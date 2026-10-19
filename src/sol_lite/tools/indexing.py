"""Exact Markdown retrieval and non-destructive, approved inbox consolidation."""

from __future__ import annotations

import asyncio
import difflib
import hashlib
import os
import re
import threading
import unicodedata
import uuid
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from pathlib import Path
from stat import S_ISLNK

from ..core.exceptions import PermissionDenied, SecurityError, ToolExecutionError
from ..permissions.scopes import READ, WRITE
from ..security.path_guard import resolve_workspace_path
from .base import ToolDefinition

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_FILES = 5000
CACHE_SIZE = 256
_IGNORE = {".git", "node_modules", ".venv", "venv", "__pycache__"}
_CACHE = OrderedDict()
_CACHE_LOCK = threading.RLock()
_APPLY_LOCK = threading.RLock()
_WRITERS = {"sol_pa", "sol_docs"}
_EOL = re.compile(r"\r\n|\n|\r")
_HEADER = re.compile(r"^ {0,3}(#{1,6}) +(.*)$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


@dataclass(frozen=True)
class Section:
    header: str
    path: tuple[str, ...]
    level: int
    start: int
    body_start: int
    own_end: int
    end: int


@dataclass(frozen=True)
class Document:
    text: str
    lines: tuple[str, ...]
    endings: tuple[str, ...]
    sections: tuple[Section, ...]
    fences: tuple[tuple[int, int], ...]
    unclosed_fence: bool
    bom: bool

    @property
    def newline(self):
        return next((ending for ending in self.endings if ending), "\n")

    @property
    def trailing_newline(self):
        return bool(self.endings and self.endings[-1])


def _physical_lines(value):
    lines, endings, position = [], [], 0
    for match in _EOL.finditer(value):
        lines.append(value[position : match.start()])
        endings.append(match[0])
        position = match.end()
    if position < len(value):
        lines.append(value[position:])
        endings.append("")
    return tuple(lines), tuple(endings)


def parse_markdown(value):
    """Parse strict UTF-8 bytes or decoded text without normalizing physical lines."""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="strict")
    if not isinstance(value, str):
        raise TypeError("Markdown must be UTF-8 bytes or text")
    lines, endings = _physical_lines(value)
    headers, fences, stack = [], [], []
    opened = None
    for index, original in enumerate(lines):
        line = original.removeprefix("\ufeff") if index == 0 else original
        fence = _FENCE.match(line)
        if opened:
            start, marker = opened
            if (
                fence
                and fence[1][0] == marker[0]
                and len(fence[1]) >= len(marker)
                and not fence[2].strip()
            ):
                fences.append((start, index + 1))
                opened = None
            continue
        if fence:
            opened = (index, fence[1])
            continue
        header = _HEADER.match(line)
        if header:
            level = len(header[1])
            title = re.sub(r"\s+#+\s*$", "", header[2]).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            path = tuple(item[1] for item in stack) + (title,)
            stack.append((level, title))
            headers.append((index, level, path, line))
    if opened:
        fences.append((opened[0], len(lines)))
    first = headers[0][0] if headers else len(lines)
    sections = [Section("(preamble)", (), 0, 0, 0, first, first)]
    subtree_ends, pending = {}, []
    for position, (start, level, _path, _header) in enumerate(headers):
        while pending and headers[pending[-1]][1] >= level:
            subtree_ends[pending.pop()] = start
        pending.append(position)
    for position, (start, level, path, header) in enumerate(headers):
        own_end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
        end = subtree_ends.get(position, len(lines))
        sections.append(Section(header, path, level, start, start + 1, own_end, end))
    return Document(
        value,
        lines,
        endings,
        tuple(sections),
        tuple(fences),
        bool(opened),
        value.startswith("\ufeff"),
    )


def _integer(value, name, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer from {lower} to {upper}")
    return value


def _search_options(args):
    query = args.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be non-empty text")
    mode, matching = args.get("mode", "text"), args.get("match", "all")
    if mode not in {"text", "regex", "header"} or matching not in {"all", "any"}:
        raise ValueError("Invalid mode or match value")
    sensitive, inbox = args.get("case_sensitive", False), args.get("include_inbox", False)
    if type(sensitive) is not bool or type(inbox) is not bool:
        raise ValueError("case_sensitive and include_inbox must be booleans")
    return {
        "query": query,
        "mode": mode,
        "match": matching,
        "case_sensitive": sensitive,
        "include_inbox": inbox,
        "context_lines": _integer(args.get("context_lines", 0), "context_lines", 0, 10),
        "max_results": _integer(args.get("max_results", 20), "max_results", 1, 100),
        "max_block_lines": _integer(args.get("max_block_lines", 80), "max_block_lines", 1, 400),
    }


def _query_matchers(options):
    query, mode = options["query"], options["mode"]
    if mode == "regex":
        try:
            compiled = re.compile(query, 0 if options["case_sensitive"] else re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"Invalid regex: {exc}") from exc
        # A conservative positive precheck is necessary for arbitrary line anchors
        # and lookarounds. A false negative would hide a real per-line match.
        complex_query = any(token in query for token in ("^", "$", "\\A", "\\Z", "\\z", "(?"))
        precheck = re.compile(r"[\s\S]*") if complex_query else compiled
        return (
            lambda line: compiled.search(line) is not None,
            lambda value: precheck.search(value) is not None,
        )
    tokens = query.split() if options["case_sensitive"] else query.casefold().split()

    def matches(line):
        value = line if options["case_sensitive"] else line.casefold()
        return (all if options["match"] == "all" else any)(token in value for token in tokens)

    if options["match"] == "all":
        pattern = "".join(r"(?=[^\r\n]*" + re.escape(token) + ")" for token in tokens)
        pattern += r"[^\r\n]*"
    else:
        pattern = "|".join(re.escape(token) for token in tokens)
    precheck = re.compile(pattern)
    return (
        matches,
        lambda value: (
            precheck.search(value if options["case_sensitive"] else value.casefold()) is not None
        ),
    )


def _render_result(path, absolute, doc, section, start, end, matched, cap):
    truncated = end - start > cap
    # Preserve at least the first actual match when a small cap consumes context.
    hits = [index for index in range(start, end) if index in matched]
    if truncated and hits and hits[0] >= start + cap:
        start = hits[0]
    end = min(end, start + cap)
    rows = [
        {"n": index + 1, "text": doc.lines[index], "match": index in matched}
        for index in range(start, end)
    ]
    verbatim = "\n".join(row["text"] for row in rows)
    longest = max((len(match[0]) for match in re.finditer(r"`+", verbatim)), default=0)
    fence = "`" * max(3, longest + 1)
    rendered = (
        f"**File Path:** {path}\n**Section Header:** {section.header}\n"
        f"**Lines:** {start + 1}-{end}\n**Verbatim Text:**\n{fence}\n{verbatim}\n{fence}"
    )
    return {
        "path": path,
        "absolute_path": absolute,
        "section_header": section.header,
        "header_path": list(section.path),
        "start_line": start + 1,
        "end_line": end,
        "truncated": truncated,
        "lines": rows,
        "verbatim": verbatim,
        "rendered": rendered,
    }


def search_documents(documents, query, **kwargs):
    """Pure search over (relative path, absolute path, Document) records."""
    options = _search_options({"query": query, **kwargs})
    matches, _ = _query_matchers(options)
    blocks = []
    total_blocks = 0

    def add_block(path, absolute, doc, section, start, end, hits):
        nonlocal total_blocks
        total_blocks += 1
        if len(blocks) < options["max_results"]:
            blocks.append(
                _render_result(
                    path, absolute, doc, section, start, end, hits, options["max_block_lines"]
                )
            )

    for path, absolute, doc in sorted(documents, key=lambda item: item[0]):
        if options["mode"] == "header":
            covered_until = -1
            hits = {section.start for section in doc.sections[1:] if matches(section.path[-1])}
            for section in doc.sections[1:]:
                if section.start in hits and section.start >= covered_until:
                    covered_until = section.end
                    add_block(path, absolute, doc, section, section.start, section.end, hits)
            continue
        hits = {index for index, line in enumerate(doc.lines) if matches(line)}
        for section in doc.sections:
            local = [index for index in range(section.start, section.own_end) if index in hits]
            spans = []
            for index in local:
                start = max(section.start, index - options["context_lines"])
                end = min(section.own_end, index + options["context_lines"] + 1)
                if spans and start <= spans[-1][1]:
                    spans[-1] = (spans[-1][0], max(end, spans[-1][1]))
                else:
                    spans.append((start, end))
            for start, end in spans:
                add_block(path, absolute, doc, section, start, end, hits)
    blocks.sort(key=lambda row: (row["path"], row["start_line"]))
    return {
        "results": blocks,
        "total_blocks": total_blocks,
        "returned": len(blocks),
    }


def _is_link(path):
    info = path.lstat()
    return S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _path_has_link(root, raw):
    current = root / raw
    while current != root:
        if _is_link(current):
            return True
        current = current.parent
    return False


def _contained_path(value, root, *, must_exist=True, no_links=False):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A non-empty workspace-relative path is required")
    raw = Path(value)
    if raw.is_absolute():
        raise ValueError("Paths must be relative to the workspace")
    result = resolve_workspace_path(value, root, must_exist=must_exist)
    if no_links and _path_has_link(root, raw):
        raise SecurityError(f"Links are not supported for consolidation: {value}")
    return result


def _walk_markdown(root, target, include_inbox):
    paths, skipped, excluded, extra = [], [], 0, 0
    excluded_root = not include_inbox and any(
        part.casefold() == "inbox" for part in target.relative_to(root).parts
    )
    stack = [(target, excluded_root)]
    while stack:
        folder, inbox = stack.pop()
        try:
            with os.scandir(folder) as scan:
                entries = sorted(scan, key=lambda item: item.name)
        except OSError as exc:
            skipped.append(
                {
                    "path": folder.relative_to(root).as_posix(),
                    "reason": "unreadable",
                    "error": str(exc),
                }
            )
            continue
        children = []
        for entry in entries:
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            try:
                if _is_link(path):
                    if not inbox:
                        skipped.append({"path": relative, "reason": "symlink"})
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if entry.name not in _IGNORE:
                        children.append(
                            (
                                path,
                                inbox or (not include_inbox and entry.name.casefold() == "inbox"),
                            )
                        )
                elif path.suffix.casefold() == ".md" and entry.is_file(follow_symlinks=False):
                    if inbox:
                        excluded += 1
                    elif len(paths) < MAX_FILES:
                        paths.append(path)
                    else:
                        extra += 1
            except OSError as exc:
                skipped.append({"path": relative, "reason": "unreadable", "error": str(exc)})
        stack.extend(reversed(children))
    if extra:
        skipped.append(
            {"path": target.relative_to(root).as_posix(), "reason": "file_limit", "count": extra}
        )
    return sorted(paths), skipped, excluded


def search_knowledge_index_sync(ctx, args):
    options = _search_options(args)
    _, precheck = _query_matchers(options)
    ctx.permission_engine.check(READ)
    root = Path(ctx.workspace_root).resolve()
    target = _contained_path(args.get("target_dir", "."), root)
    if not target.is_dir():
        raise NotADirectoryError(target)
    if _path_has_link(root, args.get("target_dir", ".")):
        return {
            "query": options["query"],
            "mode": options["mode"],
            "target_dir": args.get("target_dir", "."),
            "results": [],
            "returned": 0,
            "total_blocks": 0,
            "files_scanned": 0,
            "files_skipped": [{"path": args.get("target_dir", "."), "reason": "symlink"}],
            "inbox_files_excluded": 0,
            "complete": False,
            "notice": "No match found in 0 files. Search incomplete; absence is not established.",
        }
    paths, skipped, excluded = _walk_markdown(root, target, options["include_inbox"])
    results, scanned, total_blocks = [], 0, 0

    def collect(relative, absolute, doc):
        nonlocal total_blocks
        remaining = options["max_results"] - len(results)
        local = search_documents(
            [(relative, absolute, doc)], **{**options, "max_results": max(1, remaining)}
        )
        total_blocks += local["total_blocks"]
        if remaining > 0:
            results.extend(local["results"][:remaining])

    for path in paths:
        relative = path.relative_to(root).as_posix()
        try:
            guarded = resolve_workspace_path(relative, root, must_exist=True)
            if _is_link(path) or guarded != path:
                skipped.append({"path": relative, "reason": "symlink"})
                continue
            stat = guarded.stat()
            if stat.st_size > MAX_FILE_BYTES:
                skipped.append({"path": relative, "reason": "too_large"})
                continue
            key = (str(guarded), stat.st_mtime_ns, stat.st_size)
            with _CACHE_LOCK:
                cached = _CACHE.get(key)
                if cached is not None:
                    _CACHE.move_to_end(key)
            if cached is not None:
                scanned += 1
                if options["mode"] == "header" or precheck(cached.text):
                    collect(relative, str(guarded), cached)
                continue
            with guarded.open("rb") as stream:
                raw = stream.read(MAX_FILE_BYTES + 1)
            if len(raw) > MAX_FILE_BYTES:
                skipped.append({"path": relative, "reason": "too_large"})
                continue
            after = guarded.stat()
            if (after.st_mtime_ns, after.st_size) != (stat.st_mtime_ns, stat.st_size):
                skipped.append({"path": relative, "reason": "changed_during_read"})
                continue
            decoded = raw.decode("utf-8", errors="strict")
            scanned += 1
            if options["mode"] != "header" and not precheck(decoded):
                continue
            doc = parse_markdown(decoded)
            with _CACHE_LOCK:
                _CACHE[key] = doc
                _CACHE.move_to_end(key)
                while len(_CACHE) > CACHE_SIZE:
                    _CACHE.popitem(last=False)
            collect(relative, str(guarded), doc)
        except UnicodeError:
            skipped.append({"path": relative, "reason": "not_utf8"})
        except (OSError, SecurityError) as exc:
            skipped.append({"path": relative, "reason": "unreadable", "error": str(exc)})
    result = {"results": results, "total_blocks": total_blocks, "returned": len(results)}
    capped = result["total_blocks"] > result["returned"] or any(
        row["truncated"] for row in result["results"]
    )
    complete = not skipped and not capped
    notice = "Quote `rendered` verbatim. Do not summarise, reorder or add to it."
    if not result["results"]:
        notice = f"No match found in {scanned} files. " + notice
    if not complete:
        notice += " Search incomplete or output truncated; absence is not established."
    ctx.audit.record(
        "indexing.search",
        files_scanned=scanned,
        skipped=len(skipped),
        returned=result["returned"],
        complete=complete,
    )
    return {
        "query": options["query"],
        "mode": options["mode"],
        "target_dir": target.relative_to(root).as_posix(),
        **result,
        "files_scanned": scanned,
        "files_skipped": skipped,
        "inbox_files_excluded": excluded,
        "complete": complete,
        "notice": notice,
    }


def _normal(value):
    value = unicodedata.normalize("NFC", value).strip()
    value = re.sub(r"^[-*+]\s+", "- ", value)
    return " ".join(value.split()).casefold()


def _normal_path(section):
    return tuple(_normal(value) for value in section.path)


def _units(doc, section):
    fences = dict(doc.fences)
    result, index = [], section.body_start
    while index < section.own_end:
        end = fences.get(index, index + 1)
        lines = list(doc.lines[index:end])
        if index == 0 and lines:
            lines[0] = lines[0].removeprefix("\ufeff")
        result.append(
            {
                "start": index,
                "end": end,
                "lines": lines,
                "text": "\n".join(lines),
                "fence": index in fences,
            }
        )
        index = end
    return result


def _cells(line):
    if "|" not in line:
        return []
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def _separator(line):
    cells = _cells(line)
    return len(cells) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _table_rows(units):
    rows, run = [], []
    for unit in [*units, {"fence": True, "text": ""}]:
        if not unit["fence"] and len(_cells(unit["text"])) >= 2:
            run.append(unit)
        else:
            if len(run) >= 2 and any(_separator(item["text"]) for item in run[1:]):
                rows.extend(run)
            run = []
    return rows


def _has_table(units):
    return bool(_table_rows(units))


def _key(unit, table):
    if unit["fence"]:
        return None
    line = unit["text"].strip()
    cells = _cells(line)
    if table and len(cells) >= 2 and not _separator(line):
        return "table:" + _normal(re.sub(r"^\*\*(.+)\*\*$", r"\1", cells[0]))
    line = re.sub(r"^[-*+]\s+", "", line)
    line = re.sub(r"^\*\*([^*]+)\*\*", r"\1", line)
    match = re.match(r"^([^:=]+?)\s*[:=]\s*(.*)$", line)
    return "field:" + _normal(match[1]) if match else None


def _after_nonblank(doc, start, end):
    return next(
        (
            index + 1
            for index in range(end - 1, start - 1, -1)
            if doc.lines[index].strip().removeprefix("\ufeff")
        ),
        start,
    )


def apply_merge_text(target, insertions):
    """Pure assembly; original physical lines and their order are preserved."""
    if not isinstance(target, Document):
        target = parse_markdown(target)
    events = defaultdict(list)
    for item in insertions:
        position = item["at"]
        if not 0 <= position <= len(target.lines):
            raise ValueError("Invalid insertion position")
        events[position].append(item)
    tokens = []
    for index in range(len(target.lines) + 1):
        for insertion in sorted(events[index], key=lambda item: item.get("priority", (0, 0))):
            for line in insertion["lines"]:
                if _EOL.search(line):
                    raise ValueError("An inserted physical line contains a line terminator")
                tokens.append([line, target.newline])
        if index < len(target.lines):
            line = target.lines[index].removeprefix("\ufeff") if index == 0 else target.lines[index]
            tokens.append([line, target.endings[index]])
    for item in tokens[:-1]:
        if not item[1]:
            item[1] = target.newline
    if tokens:
        if not target.trailing_newline:
            tokens[-1][1] = ""
        elif not tokens[-1][1]:
            tokens[-1][1] = target.newline
    return ("\ufeff" if target.bom else "") + "".join(line + ending for line, ending in tokens)


def plan_merge(source, target, similarity_threshold=0.85):
    """Plan additions/conflicts without changing either input or normalizing output."""
    if (
        isinstance(similarity_threshold, bool)
        or not isinstance(similarity_threshold, (int, float))
        or not 0.5 <= similarity_threshold <= 1.0
    ):
        raise ValueError("similarity_threshold must be from 0.5 to 1.0")
    source = source if isinstance(source, Document) else parse_markdown(source)
    target = target if isinstance(target, Document) else parse_markdown(target)
    conflicts, additions, insertions, duplicates = [], [], [], []
    source_map, target_map = defaultdict(list), defaultdict(list)
    for doc, mapping in ((source, source_map), (target, target_map)):
        for section in doc.sections:
            mapping[_normal_path(section)].append(section)
    ambiguous = {
        key
        for mapping in (source_map, target_map)
        for key, value in mapping.items()
        if len(value) > 1
    }
    for path in sorted(ambiguous):
        original = (source_map.get(path) or target_map[path])[0]
        conflicts.append(
            {
                "kind": "ambiguous_header",
                "section_path": list(original.path),
                "normalized_path": list(path),
            }
        )
    if source.unclosed_fence or target.unclosed_fence:
        conflicts.append({"kind": "unclosed_fence", "section_path": []})
    covered_until = -1
    for section in source.sections:
        path = _normal_path(section)
        if section.start < covered_until or path in ambiguous:
            continue
        candidates = target_map.get(path, [])
        if not candidates:
            parent = target_map.get(path[:-1], []) if path[:-1] else []
            if parent and path[:-1] not in ambiguous:
                at = _after_nonblank(target, parent[0].body_start, parent[0].end)
                placement = "under_parent"
            else:
                at, placement = len(target.lines), "end_of_file"
            lines = list(source.lines[section.start : section.end])
            if section.start == 0 and lines:
                lines[0] = lines[0].removeprefix("\ufeff")
            while lines and not lines[-1].strip():
                lines.pop()
            if lines:
                priority = (-len(parent[0].path), 1) if placement == "under_parent" else (0, 2)
                insertions.append({"at": at, "lines": lines, "priority": priority})
                additions.append(
                    {
                        "section_path": list(section.path),
                        "placement": placement,
                        "source_lines": list(
                            range(section.start + 1, section.start + len(lines) + 1)
                        ),
                        "lines": lines,
                    }
                )
            covered_until = section.end
            continue
        other = candidates[0]
        src, dst = _units(source, section), _units(target, other)
        table = _has_table(dst)
        source_keys, target_keys = defaultdict(list), defaultdict(list)
        for units, mapping in ((src, source_keys), (dst, target_keys)):
            for unit in units:
                key = _key(unit, table)
                if key:
                    mapping[key].append(unit)
        bad_keys = {key for key, values in target_keys.items() if len(values) > 1}
        bad_keys |= {
            key
            for key, values in source_keys.items()
            if len({_normal(unit["text"]) for unit in values}) > 1
        }
        normals = {_normal(unit["text"]): unit for unit in dst if unit["text"].strip()}
        seen = set(normals)
        accepted = []
        for number, unit in enumerate(src):
            normalized = _normal(unit["text"])
            if not normalized:
                continue
            key = _key(unit, table)
            target_unit = target_keys[key][0] if key in target_keys else None
            conflict = None
            if key in bad_keys:
                conflict = "ambiguous_key"
            elif normalized in seen:
                duplicates.append(unit["text"])
                continue
            elif target_unit:
                conflict = "value_changed"
            elif key is None and len(normalized) >= 12:
                for existing, candidate in normals.items():
                    ratio = difflib.SequenceMatcher(None, normalized, existing, autojunk=False)
                    if (
                        ratio.quick_ratio() >= similarity_threshold
                        and ratio.ratio() >= similarity_threshold
                    ):
                        conflict, target_unit = "possible_edit", candidate
                        break
            if conflict:
                entry = {
                    "kind": conflict,
                    "section_path": list(section.path),
                    "source_line": unit["start"] + 1,
                    "source_text": unit["text"],
                }
                if target_unit:
                    entry.update(
                        target_line=target_unit["start"] + 1, target_text=target_unit["text"]
                    )
                conflicts.append(entry)
                continue
            at = _after_nonblank(target, other.body_start, other.own_end)
            placement = "end_of_section"
            if key and key.startswith("table:"):
                rows = _table_rows(dst)
                if rows:
                    at, placement = rows[-1]["end"], "after_table"
            accepted.append((number, unit, at, placement))
            seen.add(normalized)
        previous = None
        for number, unit, at, placement in accepted:
            lines = list(unit["lines"])
            numbers = list(range(unit["start"] + 1, unit["end"] + 1))
            if previous is not None and previous[2] == at:
                middle = src[previous[0] + 1 : number]
                if middle and all(not item["text"].strip() for item in middle):
                    blanks = [line for item in middle for line in item["lines"]]
                    lines = blanks + lines
                    numbers = [
                        index + 1 for item in middle for index in range(item["start"], item["end"])
                    ] + numbers
            priority = (-len(other.path), -1 if placement == "after_table" else 0)
            insertions.append({"at": at, "lines": lines, "priority": priority})
            additions.append(
                {
                    "section_path": list(section.path),
                    "placement": placement,
                    "source_lines": numbers,
                    "lines": lines,
                }
            )
            previous = (number, unit, at)
    status = "needs_reconciliation" if conflicts else "ready" if insertions else "no_changes"
    merged = None if conflicts else apply_merge_text(target, insertions)
    return {
        "status": status,
        "additions": additions,
        "skipped_duplicates": {"count": len(duplicates), "examples": duplicates[:20]},
        "conflicts": conflicts,
        "insertions": insertions,
        "merged_text": merged,
    }


def _merge_paths(ctx, args):
    if getattr(ctx, "agent_id", None) not in _WRITERS:
        raise PermissionDenied("Only sol_pa and sol_docs may consolidate inbox documents")
    ctx.permission_engine.check(READ)
    root = Path(ctx.workspace_root).resolve()
    source = _contained_path(args.get("source_file"), root, no_links=True)
    target = _contained_path(args.get("target_file"), root, no_links=True)
    if source == target or os.path.samefile(source, target):
        raise ValueError("Source and target must differ")
    for path in (source, target):
        if path.suffix.casefold() != ".md" or not path.is_file():
            raise ValueError("Source and target must be existing Markdown files")
    src_parts = [part.casefold() for part in source.relative_to(root).parts[:-1]]
    dst_parts = [part.casefold() for part in target.relative_to(root).parts[:-1]]
    if "inbox" not in src_parts or "inbox" in dst_parts:
        raise ValueError("Source must be inside inbox; target must be outside inbox")
    if any(part in {"_workspace", "_project"} for part in dst_parts):
        raise ValueError("Managed pack files must use workspace pack tools")
    return root, source, target


def _fresh_bytes(path):
    value = path.read_bytes()
    try:
        value.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError(f"File is not UTF-8: {path.name}") from exc
    return value


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _preview(source_bytes, target_bytes, args):
    result = plan_merge(source_bytes, target_bytes, args.get("similarity_threshold", 0.85))
    merged = result["merged_text"]
    diff = (
        []
        if merged is None
        else list(
            difflib.unified_diff(
                parse_markdown(target_bytes).lines,
                parse_markdown(merged).lines,
                fromfile=args["target_file"],
                tofile=args["target_file"] + " (merged)",
                lineterm="",
            )
        )
    )
    public = {
        key: value for key, value in result.items() if key not in {"insertions", "merged_text"}
    }
    public.update(
        source_file=args["source_file"],
        target_file=args["target_file"],
        source_sha256=_sha(source_bytes),
        target_sha256=_sha(target_bytes),
        merged_sha256=None if merged is None else _sha(merged.encode("utf-8")),
        diff="\n".join(diff[:400]),
        diff_truncated=len(diff) > 400,
        notice="Conflicts block apply. Ask the user to reconcile.",
    )
    return public, result


def consolidate_inbox_preview(ctx, args):
    _, source, target = _merge_paths(ctx, args)
    public, _ = _preview(_fresh_bytes(source), _fresh_bytes(target), args)
    ctx.audit.record(
        "indexing.consolidate_preview",
        source_file=args["source_file"],
        target_file=args["target_file"],
        status=public["status"],
        conflicts=len(public["conflicts"]),
        additions=len(public["additions"]),
    )
    return public


def _invariant(original, merged):
    before, after = parse_markdown(original), parse_markdown(merged)
    cursor = 0
    old_lines = list(before.lines)
    new_lines = list(after.lines)
    if before.bom and old_lines:
        old_lines[0] = old_lines[0].removeprefix("\ufeff")
    if after.bom and new_lines:
        new_lines[0] = new_lines[0].removeprefix("\ufeff")
    for line in old_lines:
        while cursor < len(new_lines) and new_lines[cursor] != line:
            cursor += 1
        if cursor == len(new_lines):
            raise ToolExecutionError(
                "Merge invariant failed: existing target lines changed or disappeared"
            )
        cursor += 1
    if before.bom != after.bom or before.trailing_newline != after.trailing_newline:
        raise ToolExecutionError("Merge invariant failed: BOM or trailing-newline state changed")


def consolidate_inbox_apply(ctx, args):
    for key in ("expected_source_sha256", "expected_target_sha256", "plan", "approval_id"):
        if key not in args or not isinstance(args[key], str):
            raise ValueError(f"{key} is required and must be text")
    for key in ("expected_source_sha256", "expected_target_sha256"):
        if not re.fullmatch(r"[0-9a-fA-F]{64}", args[key]):
            raise ValueError(f"{key} must be a SHA-256 digest")
    if not args["plan"].strip():
        raise ValueError("A non-empty plan is required")
    with _APPLY_LOCK:
        root, source, target = _merge_paths(ctx, args)
        source_bytes, target_bytes = _fresh_bytes(source), _fresh_bytes(target)
        public, planned = _preview(source_bytes, target_bytes, args)
        if (
            public["source_sha256"] != args["expected_source_sha256"].lower()
            or public["target_sha256"] != args["expected_target_sha256"].lower()
        ):
            raise ToolExecutionError(
                "Stale preview hashes; preview both files again. Nothing was written."
            )
        if public["status"] == "needs_reconciliation":
            return {**public, "ok": False, "applied": False}
        if public["status"] == "no_changes":
            return {**public, "applied": False, "lines_added": 0}
        clean = {key: value for key, value in args.items() if key != "approval_id"}
        ctx.permission_engine.check(
            WRITE,
            operation="consolidate_inbox_apply",
            target=str(target),
            arguments=clean,
            plan=args["plan"],
            approval_id=args["approval_id"],
            session_id=getattr(ctx, "session_id", None),
            agent_id=ctx.agent_id,
            allow_session=False,
        )
        merged = planned["merged_text"]
        _invariant(target_bytes, merged)
        # Approval may take arbitrarily long. Revalidate both paths and hashes
        # after it returns, before staging and immediately before replacement.
        _, checked_source, checked_target = _merge_paths(ctx, args)
        if (
            checked_source != source
            or checked_target != target
            or _fresh_bytes(source) != source_bytes
            or _fresh_bytes(target) != target_bytes
        ):
            raise ToolExecutionError("Files changed during approval; nothing was written")
        temporary = resolve_workspace_path(
            target.parent / ("." + target.name + "." + uuid.uuid4().hex + ".tmp"), root
        )
        created = False
        try:
            with temporary.open("xb") as stream:
                created = True
                stream.write(merged.encode("utf-8"))
                stream.flush()
                os.fsync(stream.fileno())
            _merge_paths(ctx, args)
            if _fresh_bytes(source) != source_bytes or _fresh_bytes(target) != target_bytes:
                raise ToolExecutionError("Files changed before replacement; nothing was written")
            os.replace(temporary, target)
        except OSError as exc:
            raise ToolExecutionError(
                f"Atomic consolidation failed; original target retained: {exc}"
            ) from exc
        finally:
            if created:
                temporary.unlink(missing_ok=True)
        count = sum(len(item["lines"]) for item in planned["insertions"])
        ctx.audit.record(
            "indexing.consolidate_apply",
            source_file=args["source_file"],
            target_file=args["target_file"],
            source_sha256=public["source_sha256"],
            previous_sha256=public["target_sha256"],
            new_sha256=public["merged_sha256"],
            lines_added=count,
            additions=len(public["additions"]),
        )
        return {
            **public,
            "status": "applied",
            "applied": True,
            "lines_added": count,
            "new_sha256": public["merged_sha256"],
            "notice": "Applied additions; inbox unchanged. Log this change with workspace_pack_append when a pack exists.",
        }


async def search_knowledge_index(
    query: str,
    target_dir: str = ".",
    *,
    ctx,
    mode: str = "text",
    match: str = "all",
    case_sensitive: bool = False,
    context_lines: int = 0,
    max_results: int = 20,
    max_block_lines: int = 80,
    include_inbox: bool = False,
) -> dict:
    args = {
        "query": query,
        "target_dir": target_dir,
        "mode": mode,
        "match": match,
        "case_sensitive": case_sensitive,
        "context_lines": context_lines,
        "max_results": max_results,
        "max_block_lines": max_block_lines,
        "include_inbox": include_inbox,
    }
    return await asyncio.to_thread(search_knowledge_index_sync, ctx, args)


async def consolidate_inbox_payload(
    source_file: str,
    target_file: str,
    *,
    ctx,
    apply: bool = False,
    similarity_threshold: float = 0.85,
    expected_source_sha256: str | None = None,
    expected_target_sha256: str | None = None,
    plan: str = "",
    approval_id: str | None = None,
) -> dict:
    if type(apply) is not bool:
        raise ValueError("apply must be a boolean")
    args = {
        "source_file": source_file,
        "target_file": target_file,
        "similarity_threshold": similarity_threshold,
    }
    if apply:
        args.update(
            expected_source_sha256=expected_source_sha256,
            expected_target_sha256=expected_target_sha256,
            plan=plan,
            approval_id=approval_id,
        )
    handler = consolidate_inbox_apply if apply else consolidate_inbox_preview
    return await asyncio.to_thread(handler, ctx, args)


def indexing_tools():
    search_properties = {
        "query": {"type": "string", "minLength": 1},
        "target_dir": {"type": "string", "default": "."},
        "mode": {"type": "string", "enum": ["text", "regex", "header"], "default": "text"},
        "match": {"type": "string", "enum": ["all", "any"], "default": "all"},
        "case_sensitive": {"type": "boolean", "default": False},
        "context_lines": {"type": "integer", "minimum": 0, "maximum": 10, "default": 0},
        "max_results": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
        "max_block_lines": {"type": "integer", "minimum": 1, "maximum": 400, "default": 80},
        "include_inbox": {"type": "boolean", "default": False},
    }
    merge_properties = {
        "source_file": {"type": "string"},
        "target_file": {"type": "string"},
        "similarity_threshold": {"type": "number", "minimum": 0.5, "maximum": 1.0, "default": 0.85},
    }
    approval_properties = {
        key: {"type": "string"}
        for key in ("expected_source_sha256", "expected_target_sha256", "plan", "approval_id")
    }
    definitions = [
        (
            "search_knowledge_index",
            "Find exact Markdown source text and line citations. Quote rendered verbatim; never summarise. Inbox is excluded by default.",
            search_properties,
            ["query"],
            search_knowledge_index_sync,
            False,
        ),
        (
            "consolidate_inbox_preview",
            "Preview deterministic inbox additions and conflicts without writing. Any conflict blocks apply.",
            merge_properties,
            ["source_file", "target_file"],
            consolidate_inbox_preview,
            False,
        ),
        (
            "consolidate_inbox_apply",
            "Apply a fresh conflict-free inbox preview after exact approval. Supply both preview hashes and a plan; empty approval_id requests human approval.",
            {**merge_properties, **approval_properties},
            ["source_file", "target_file", *approval_properties],
            consolidate_inbox_apply,
            True,
        ),
    ]
    return [
        ToolDefinition(
            name,
            description,
            {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
            handler,
            permissions=(READ, WRITE) if mutating else (READ,),
            risk=("MUTATING",) if mutating else ("READ_ONLY",),
            mutability=mutating,
        )
        for name, description, properties, required, handler, mutating in definitions
    ]

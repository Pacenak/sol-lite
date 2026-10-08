"""Native Ollama agent runtime with strict tool-call handling."""
from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass

from ..core.event_bus import Event
from ..core.exceptions import AgentError, ApprovalRequired, ToolExecutionError
from .repeat_guard import RepeatToolGuard
from .status import MAX_TOOL_ROUNDS, StatusTracker

PHASES = {
    "00": "WORKSPACE DISCOVERY",
    "01": "VERIFICATION / REPRODUCTION",
    "02": "ROOT CAUSE INVESTIGATION",
    "03": "FIX PLANNING",
    "04": "IMPLEMENTATION",
    "05": "VALIDATION",
    "06": "END-TO-END PROOF",
    "07": "FINAL REPORT",
}


WORKSPACE_TOOL_NAMES = {
    "inventory_workspace",
    "list_project_structure",
    "find_workspace_files",
    "read_workspace_file",
    "read_workspace_files",
    "get_workspace_file_metadata",
    "search_codebase",
    "analyze_architecture_drift",
    "repository_status",
    "repository_diff",
    "repository_log",
    "repository_branches",
    "repository_remotes",
    "repository_create_branch",
    "repository_checkout",
    "repository_stage",
    "repository_commit",
    "repository_create_bundle",
    "repository_import_bundle",
    "repository_create_patch",
    "repository_apply_patch",
    "repository_merge_import",
    "repository_set_remote",
    "repository_fetch",
    "repository_push",
    "repository_clone_remote",
    "repository_clone_local",
    "runtime_get_context",
    "execute_terminal_command",
}


WORKSPACE_EVIDENCE_PATTERNS = (
    r"\bworkspace\b",
    r"\brepository\b",
    r"\brepo\b",
    r"\bcodebase\b",
    r"\bsource\b",
    r"\bfolder\b",
    r"\bdirectory\b",
    r"\bfiles?\b",
    r"\bcontents?\b",
    r"\banaly[sz]e\b",
    r"\binspect\b",
    r"\breview\b",
    r"\baudit\b",
    r"\bdebug\b",
    r"\bunderstand\b",
    r"\btrace\b",
    r"\binvestigate\b",
    r"\bfix\b",
)


def phase_from_prompt_name(name):
    return PHASES.get(os.path.basename(name)[:2], "INTERACTIVE")


@dataclass(slots=True)
class AgentResult:
    content: str
    rounds: int
    cancelled: bool = False
    stopped_reason: str | None = None
    tool_calls: int = 0
    tool_failures: int = 0
    native_tool_calls: int = 0
    raw_tool_like_content: bool = False


class AgentRuntime:
    def __init__(
        self,
        model_manager,
        tools,
        tool_context,
        fault_log,
        status=None,
        max_tool_rounds=MAX_TOOL_ROUNDS,
        repeat_tool_threshold=3,
        status_callback=None,
        approval_callback=None,
        skill_context="",
        event_bus=None,
    ):
        self.model_manager = model_manager
        self.tools = tools
        self.tool_context = tool_context
        self.fault_log = fault_log
        self.status = status or StatusTracker()
        self.max_tool_rounds = max_tool_rounds
        self.repeat_tool_threshold = repeat_tool_threshold
        self.status_callback = status_callback
        self.approval_callback = approval_callback
        self.skill_context = skill_context
        self.event_bus = event_bus
        self._cancel_event = threading.Event()
        self._last_status_event = None

    def _emit(self, event_type, **data):
        if self.event_bus is not None:
            self.event_bus.publish(
                Event(event_type, "agent_runtime", data)
            )

    def cancel(self):
        self._cancel_event.set()
        self.status.cancel()

    @staticmethod
    def _requires_workspace_evidence(messages):
        """Determine whether the user's request requires actual workspace evidence."""
        user_text = "\n".join(
            str(message.get("content", ""))
            for message in messages
            if isinstance(message, dict)
            and message.get("role") == "user"
        )

        return any(
            re.search(pattern, user_text, re.IGNORECASE)
            for pattern in WORKSPACE_EVIDENCE_PATTERNS
        )

    @staticmethod
    def _workspace_tool_was_used(tool_names):
        return any(
            name in WORKSPACE_TOOL_NAMES
            for name in tool_names
        )

    def run(self, *, profile, messages, prompt_name=""):
        self._cancel_event.clear()
        self._last_status_event = None

        def status_update(line):
            if self.status_callback is not None:
                self.status_callback(line)

            state = self.status.state()

            if (
                state == "STALLED"
                and self._last_status_event != "STALLED"
            ):
                self._last_status_event = "STALLED"
                self._emit("agent.stalled")

        self.status.start(callback=status_update)

        self.status.begin(
            phase_from_prompt_name(prompt_name),
            "Starting agent",
        )

        self._emit(
            "agent.started",
            profile=profile,
            prompt_name=prompt_name,
        )

        guard = RepeatToolGuard(self.repeat_tool_threshold)
        current = list(messages)

        if self.skill_context:
            current[0] = dict(current[0])
            current[0]["content"] = (
                f"{current[0].get('content', '')}\n\n"
                f"{self.skill_context}"
            ).strip()

        profile_obj = self.model_manager.profile(profile)

        tool_calls_total = 0
        tool_failures = 0
        native_calls = 0
        raw_tool_like = False

        required_workspace_evidence = (
            self._requires_workspace_evidence(messages)
        )

        workspace_tools_used = set()

        try:
            for number in range(
                1,
                self.max_tool_rounds + 1,
            ):
                if self._cancel_event.is_set():
                    self._emit(
                        "agent.cancelled",
                        round=number - 1,
                    )

                    return AgentResult(
                        "",
                        number - 1,
                        True,
                        "cancelled",
                        tool_calls_total,
                        tool_failures,
                        native_calls,
                        raw_tool_like,
                    )

                self.status.set_round(number)

                self.status.touch(
                    f"Waiting for Ollama · {profile_obj.model}"
                )

                self._emit(
                    "agent.thinking",
                    round=number,
                )

                self._emit(
                    "model.waiting",
                    model=profile_obj.model,
                    round=number,
                )

                response = self.model_manager.provider.chat(
                    model=profile_obj.model,
                    messages=current,
                    tools=self.tools.ollama_schemas(),
                    temperature=profile_obj.temperature,
                    timeout=profile_obj.timeout_seconds,
                )

                message = getattr(
                    response,
                    "message",
                    None,
                )

                if message is None and isinstance(
                    response,
                    dict,
                ):
                    message = response.get("message")

                if message is None:
                    raise AgentError(
                        "Ollama returned no message object."
                    )

                content = (
                    getattr(message, "content", "")
                    or ""
                )

                calls = (
                    getattr(message, "tool_calls", None)
                    or []
                )

                self._emit(
                    "model.responded",
                    model=profile_obj.model,
                    round=number,
                    native_tool_calls=len(calls),
                    content_length=len(content),
                )

                # ---------------------------------------------------------
                # No native tool calls.
                # ---------------------------------------------------------
                if not calls:
                    raw_tool_like = (
                        self._looks_like_tool_like_content(content)
                    )

                    if raw_tool_like:
                        code = (
                            "RAW_JSON_IN_CONTENT"
                            if self._looks_like_raw_tool_json(content)
                            else "TOOL_LIKE_CONTENT"
                        )

                        self.fault_log.log(
                            category="model_safety",
                            code=code,
                            content=content,
                        )

                        self._emit(
                            "agent.failed",
                            reason="tool_call_not_native",
                            code=code,
                        )

                        self.status.finish(
                            "FAILED",
                            "Model emitted tool-like text instead of a native tool call",
                        )

                        return AgentResult(
                            content,
                            number,
                            False,
                            "tool_call_not_native",
                            tool_calls_total,
                            tool_failures,
                            native_calls,
                            True,
                        )

                    # -----------------------------------------------------
                    # Workspace evidence gate.
                    #
                    # This is deliberately enforced in the runtime rather
                    # than relying only on the prompt. A model cannot claim
                    # repository analysis without an actual native workspace
                    # tool having executed.
                    # -----------------------------------------------------
                    if (
                        required_workspace_evidence
                        and not self._workspace_tool_was_used(
                            workspace_tools_used
                        )
                    ):
                        self.fault_log.log(
                            category="agent_runtime",
                            code="WORKSPACE_EVIDENCE_REQUIRED",
                            content=content,
                        )

                        self._emit(
                            "agent.failed",
                            reason="workspace_evidence_required",
                        )

                        self.status.finish(
                            "FAILED",
                            "Workspace evidence is required before completing this task",
                        )

                        return AgentResult(
                            content,
                            number,
                            False,
                            "workspace_evidence_required",
                            tool_calls_total,
                            tool_failures,
                            native_calls,
                            False,
                        )

                    if (
                        number == 1
                        and not content.strip()
                    ):
                        self.status.finish(
                            "FAILED",
                            "Model returned no tool call and no final response",
                        )

                        self.fault_log.log(
                            category="agent_runtime",
                            code="NO_TOOL_CALL_OR_RESPONSE",
                        )

                        self._emit(
                            "agent.failed",
                            reason="no_tool_call_or_response",
                        )

                        return AgentResult(
                            "",
                            number,
                            False,
                            "no_tool_call_or_response",
                            tool_calls_total,
                            tool_failures,
                            native_calls,
                            False,
                        )

                    self.status.finish(
                        "COMPLETED",
                        "Response complete",
                    )

                    self._emit(
                        "agent.completed",
                        rounds=number,
                        tool_calls=tool_calls_total,
                    )

                    return AgentResult(
                        content,
                        number,
                        False,
                        None,
                        tool_calls_total,
                        tool_failures,
                        native_calls,
                        False,
                    )

                # ---------------------------------------------------------
                # Native structured tool calls.
                # ---------------------------------------------------------
                native_calls += len(calls)

                current.append(
                    self._assistant_message(message)
                )

                for call in calls:
                    name, args = self._normalize_tool_call(call)

                    tool_calls_total += 1

                    self._emit(
                        "tool.requested",
                        tool=name,
                        arguments=args,
                        round=number,
                    )

                    if name in WORKSPACE_TOOL_NAMES:
                        workspace_tools_used.add(name)

                    if guard.record(name, args):
                        warning = (
                            "The same tool operation has repeated "
                            "without new evidence. "
                            "Do not repeat it. Reassess the task "
                            "using existing evidence."
                        )

                        current.append(
                            {
                                "role": "user",
                                "content": warning,
                            }
                        )

                        self.fault_log.log(
                            category="agent_runtime",
                            code="NO_PROGRESS_DETECTED",
                            tool=name,
                            arguments=args,
                        )

                        self.status.touch(
                            "No progress detected; corrective instruction sent"
                        )

                        self._emit(
                            "tool.rejected",
                            tool=name,
                            reason="repeat_guard",
                        )

                        continue

                    self.status.tool_start(name)

                    self._emit(
                        "tool.started",
                        tool=name,
                        arguments=args,
                    )

                    result = None

                    try:
                        result = self.tools.execute(
                            name,
                            args,
                            self.tool_context,
                        )

                    except ApprovalRequired as exc:
                        self.status.touch(
                            f"Approval required · {name}"
                        )

                        self.fault_log.log(
                            category="permission",
                            code="APPROVAL_REQUIRED",
                            tool=name,
                            arguments=args,
                            error=str(exc),
                        )

                        approval_id = None

                        self._emit(
                            "approval.requested",
                            tool=name,
                        )

                        if (
                            self.approval_callback is not None
                            and exc.request is not None
                        ):
                            approval_id = self.approval_callback(
                                exc.request
                            )

                        if approval_id:
                            approved_args = dict(args)
                            approved_args["approval_id"] = approval_id

                            self.status.touch(
                                f"Approved · executing {name}"
                            )

                            self._emit(
                                "approval.granted",
                                tool=name,
                            )

                            try:
                                result = self.tools.execute(
                                    name,
                                    approved_args,
                                    self.tool_context,
                                )

                            except ToolExecutionError as approved_exc:
                                tool_failures += 1
                                self.status.error()

                                self.fault_log.log(
                                    category="tool",
                                    code="TOOL_EXECUTION_ERROR",
                                    tool=name,
                                    arguments=approved_args,
                                    error=str(approved_exc),
                                )

                                result = {
                                    "ok": False,
                                    "error": str(approved_exc),
                                    "tool": name,
                                }

                        else:
                            tool_failures += 1

                            self._emit(
                                "approval.denied",
                                tool=name,
                            )

                            self._emit(
                                "tool.rejected",
                                tool=name,
                                reason="approval_denied",
                            )

                            result = {
                                "ok": False,
                                "error": str(exc),
                                "approval_required": True,
                                "tool": name,
                            }

                    except ToolExecutionError as exc:
                        tool_failures += 1
                        self.status.error()

                        self.fault_log.log(
                            category="tool",
                            code="TOOL_EXECUTION_ERROR",
                            tool=name,
                            arguments=args,
                            error=str(exc),
                        )

                        result = {
                            "ok": False,
                            "error": str(exc),
                            "tool": name,
                        }

                    finally:
                        self._emit(
                            "tool.completed",
                            tool=name,
                            failed=(
                                isinstance(result, dict)
                                and result.get("ok") is False
                            ),
                        )

                        self.status.tool_complete(name)

                    current.append(
                        {
                            "role": "tool",
                            "tool_name": name,
                            "content": json.dumps(
                                result,
                                ensure_ascii=False,
                            ),
                        }
                    )

            self.status.finish(
                "FAILED",
                "Safety ceiling reached",
            )

            self._emit(
                "agent.failed",
                reason="max_tool_rounds",
                rounds=self.max_tool_rounds,
            )

            return AgentResult(
                "",
                self.max_tool_rounds,
                False,
                "max_tool_rounds",
                tool_calls_total,
                tool_failures,
                native_calls,
                raw_tool_like,
            )

        except KeyboardInterrupt:
            self.cancel()

            self._emit(
                "agent.cancelled"
            )

            return AgentResult(
                "",
                0,
                True,
                "cancelled",
                tool_calls_total,
                tool_failures,
                native_calls,
                raw_tool_like,
            )

        except Exception as exc:
            self.status.error()

            self.status.finish(
                "FAILED",
                "Agent runtime error",
            )

            self.fault_log.log(
                category="agent_runtime",
                code="AGENT_RUNTIME_ERROR",
                error=str(exc),
            )

            self._emit(
                "agent.failed",
                reason="runtime_error",
                error=str(exc),
            )

            raise

        finally:
            self.status.stop()

    @staticmethod
    def _looks_like_raw_tool_json(content):
        text = content.strip()

        if not text.startswith("{") or not text.endswith("}"):
            return False

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return False

        return (
            isinstance(parsed, dict)
            and "name" in parsed
            and "arguments" in parsed
        )

    @staticmethod
    def _looks_like_tool_like_content(content):
        text = content.strip()

        if AgentRuntime._looks_like_raw_tool_json(text):
            return True

        return bool(
            re.search(
                r"<(?:function|tool_call)\b",
                text,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _normalize_tool_call(call):
        function = getattr(
            call,
            "function",
            None,
        )

        if function is not None:
            name = getattr(
                function,
                "name",
                None,
            )
            args = getattr(
                function,
                "arguments",
                {},
            )

        elif isinstance(call, dict):
            function = call.get(
                "function",
                call,
            )

            name = function.get("name")
            args = function.get(
                "arguments",
                {},
            )

        else:
            raise AgentError(
                "Unsupported Ollama native tool-call structure."
            )

        if not isinstance(name, str) or not name:
            raise AgentError(
                "Native tool call has no valid function name."
            )

        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError as exc:
                raise AgentError(
                    f"Tool '{name}' arguments are invalid JSON."
                ) from exc

        if not isinstance(args, dict):
            raise AgentError(
                f"Tool '{name}' arguments are not an object."
            )

        return name, args

    @staticmethod
    def _assistant_message(message):
        calls = (
            getattr(message, "tool_calls", None)
            or []
        )

        normalized = [
            AgentRuntime._normalize_tool_call(call)
            for call in calls
        ]

        return {
            "role": "assistant",
            "content": getattr(
                message,
                "content",
                "",
            ) or "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": args,
                    },
                }
                for name, args in normalized
            ],
        }
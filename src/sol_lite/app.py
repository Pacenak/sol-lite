"""SOL-Lite command-line application."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

from .agents.runtime import AgentRuntime
from .agents.shell import AgentShell
from .agents.status import StatusTracker
from .bootstrap import bootstrap, load_config
from .models.health import diagnose_ollama
from .version import __version__


def build_parser():
    parser = argparse.ArgumentParser(
        prog="sol-lite",
        description=(
            "SOL-Lite local-first multi-agent assistant"
        ),
    )

    sub = parser.add_subparsers(
        dest="command"
    )

    start = sub.add_parser(
        "start",
        help="Start the interactive SOL-Lite agent shell.",
    )

    start.add_argument(
        "--agent",
        default=None,
    )

    start.add_argument(
        "--workspace",
        default=None,
    )

    start.add_argument(
        "--verbose",
        action="store_true",
    )

    sub.add_parser(
        "doctor",
        help="Run local runtime health checks.",
    )

    sub.add_parser(
        "version",
        help="Show version.",
    )

    sub.add_parser(
        "diagnose",
        help="Diagnose Ollama and configured models.",
    )

    pair = sub.add_parser("connect", help="Pair SOL-Lite with SOL-Command.")
    pair.add_argument("--command-url", required=True)
    pair.add_argument("--invite-code", required=True)
    pair.add_argument("--name", default="SOL-Lite")

    sub.add_parser("disconnect", help="Remove the saved SOL-Command credential from the OS keyring.")
    sub.add_parser("command-status", help="Check the paired SOL-Command connection.")
    sub.add_parser("sync-skills", help="Download assigned SOL skills into local pending review.")
    google_connect = sub.add_parser("google-connect", help="Connect a Google account for Gmail and Calendar.")
    google_connect.add_argument("--client-secrets", default=None, help="Google OAuth Desktop client JSON; defaults to SOL_GOOGLE_OAUTH_CLIENT_SECRETS.")
    sub.add_parser("google-disconnect", help="Remove the saved Google authorization from the OS keyring.")
    sub.add_parser("google-status", help="Check whether Google Workspace is connected.")

    battle = sub.add_parser(
        "battle-test",
        help=(
            "Run automated harness tests and optional "
            "live-agent smoke test."
        ),
    )

    battle.add_argument(
        "--live",
        action="store_true",
    )

    battle.add_argument(
        "--agent",
        default="sol_engineer",
    )

    return parser


def run_live_smoke(runtime, agent_id):
    if agent_id not in runtime.agents.names():
        raise RuntimeError(
            f"Unknown agent: {agent_id}"
        )

    agent = runtime.agents.get(
        agent_id
    )

    status = StatusTracker(
        heartbeat_interval=5,
        slow_threshold=30,
        stall_threshold=90,
    )

    lines = []

    runner = AgentRuntime(
        runtime.models,
        runtime.tools,
        runtime.tool_context,
        runtime.fault_log,
        status=status,
        status_callback=lines.append,
        event_bus=runtime.events,
    )

    system = (
        "You are being live-tested inside SOL-Lite. "
        "Use inventory_workspace exactly once, "
        "do not modify files, then report the number "
        "of files found. Native structured tool calls only. "
        "Never represent a tool invocation as ordinary text."
    )

    audit_before = (
        runtime.audit.path.read_text(
            encoding="utf-8"
        )
        if runtime.audit.path.exists()
        else ""
    )

    result = runner.run(
        profile=agent.model_profile,
        messages=[
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": (
                    "Run the live read-only workspace "
                    "inventory smoke test now."
                ),
            },
        ],
    )

    if (
        result.cancelled
        or result.stopped_reason
    ):
        raise RuntimeError(
            "Live agent stopped: "
            f"{result.stopped_reason}"
        )

    if result.native_tool_calls < 1:
        raise RuntimeError(
            "Live agent completed without a native "
            "structured tool call."
        )

    audit_text = (
        runtime.audit.path.read_text(
            encoding="utf-8"
        )
        if runtime.audit.path.exists()
        else ""
    )

    if "workspace.inventory" not in audit_text[
        len(audit_before):
    ]:
        raise RuntimeError(
            "Live agent did not produce workspace "
            "inventory evidence."
        )

    print(
        f"LIVE AGENT PASS: {agent_id}; "
        f"rounds={result.rounds}; "
        f"tool_calls={result.tool_calls}"
    )

    if result.content:
        print(result.content)


def main():
    args = build_parser().parse_args()

    if args.command == "version":
        print(
            f"SOL-Lite {__version__}"
        )
        return

    if args.command == "google-connect":
        from .credentials.manager import CredentialManager, KeyringBackend
        from .integrations.google_workspace import GoogleWorkspaceClient
        client_secrets = args.client_secrets or os.environ.get("SOL_GOOGLE_OAUTH_CLIENT_SECRETS")
        if not client_secrets:
            print("Set SOL_GOOGLE_OAUTH_CLIENT_SECRETS to the Google OAuth Desktop client JSON path.", file=sys.stderr)
            raise SystemExit(2)
        try:
            GoogleWorkspaceClient.connect(client_secrets, CredentialManager(KeyringBackend()))
        except Exception as exc:
            print(f"Google connection failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print("Google Workspace connected. SOL-Lite stores the authorization in the OS keyring.")
        return

    if args.command == "google-disconnect":
        from .credentials.manager import CredentialManager, KeyringBackend
        from .integrations.google_workspace import GoogleWorkspaceClient
        GoogleWorkspaceClient.disconnect(CredentialManager(KeyringBackend()))
        print("Removed saved Google authorization from the OS keyring.")
        return

    if args.command == "google-status":
        try:
            from .credentials.manager import CredentialManager, KeyringBackend
            from .integrations.google_workspace import GoogleWorkspaceClient
            client = GoogleWorkspaceClient.from_keyring(CredentialManager(KeyringBackend()))
        except Exception as exc:
            print(f"Google connection unavailable: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        if client is None:
            print("Google Workspace is not connected. Run 'sol-lite google-connect'.")
            raise SystemExit(1)
        print("Google authorization is saved in the OS keyring. API access is checked when a user-approved action runs.")
        return

    if args.command == "connect":
        from .integrations.sol_command import SolCommandClient
        try:
            result = SolCommandClient.pair(args.command_url, args.invite_code, name=args.name)
        except Exception as exc:
            print(f"SOL-Command connection failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print(f"Paired with SOL-Command as instance {result['instance_id']}.")
        print("Assigned sectors: " + (", ".join(result.get("sectors") or []) or "none"))
        return

    if args.command == "disconnect":
        from .integrations.sol_command import SolCommandClient
        SolCommandClient.disconnect()
        print("Removed saved SOL-Command credentials from the OS keyring.")
        return

    if args.command == "command-status":
        runtime = bootstrap(root)
        if runtime.tool_context.sol_command is None:
            print("SOL-Lite is not paired with SOL-Command.")
            raise SystemExit(1)
        try:
            status = runtime.tool_context.sol_command.status()
        except Exception as exc:
            print(f"SOL-Command unavailable: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return

    if args.command == "sync-skills":
        import re

        import yaml
        runtime = bootstrap(root)
        client = runtime.tool_context.sol_command
        if client is None:
            print("SOL-Lite is not paired with SOL-Command.", file=sys.stderr)
            raise SystemExit(1)
        try:
            payload = client.sync_pack_bodies()
        except Exception as exc:
            print(f"SOL skill sync failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        pending_root = runtime.data_root / "state" / "skills" / "pending" / "sol-command"
        pending_root.mkdir(parents=True, exist_ok=True)
        pending_root = pending_root.resolve()
        discovered = []
        for sector_id, entry in (payload.get("packs_sync") or {}).get("sectors", {}).items():
            if not isinstance(entry, dict) or not isinstance(entry.get("body"), dict):
                continue
            sector_slug = re.sub(r"[^a-z0-9._-]+", "-", str(sector_id).lower()).strip("-._")
            if not sector_slug or sector_slug != str(sector_id).lower():
                continue
            for skill in entry["body"].get("skills") or []:
                if not isinstance(skill, dict):
                    continue
                name = str(skill.get("name") or skill.get("title") or "").strip()
                slug = re.sub(r"[^a-z0-9._-]+", "-", name.lower()).strip("-._")
                if not slug:
                    continue
                description = str(skill.get("description") or skill.get("summary") or name).strip()
                if len(description) > 2000:
                    description = description[:2000]
                steps = skill.get("procedure") or skill.get("steps") or []
                body_lines = [f"# {name}", "", description, ""]
                if isinstance(steps, list):
                    body_lines.extend(f"{idx}. {str(step)[:4000]}" for idx, step in enumerate(steps[:200], 1))
                elif isinstance(steps, str):
                    body_lines.append(steps)
                refs = skill.get("references")
                if isinstance(refs, list) and refs:
                    body_lines.extend(["", "## References", ""])
                    body_lines.extend(f"- {ref!s}" for ref in refs)
                frontmatter = yaml.safe_dump({"name": slug, "description": description,
                    "source": "sol-command", "sector": str(sector_id)}, sort_keys=False).strip()
                content = f"---\n{frontmatter}\n---\n\n" + "\n".join(body_lines)
                version = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
                destination = pending_root / sector_slug / slug / version
                if not destination.resolve().is_relative_to(pending_root):
                    continue
                destination.mkdir(parents=True, exist_ok=True)
                skill_file = destination / "SKILL.md"
                if not skill_file.exists():
                    skill_file.write_text(content, encoding="utf-8")
                discovered.append(str(destination))
        print(f"Downloaded {len(discovered)} SOL skill(s) to pending review: {pending_root}")
        print("Review and install each skill with /skills discover and /skills import. Nothing was activated automatically.")
        return

    root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    if args.command == "doctor":
        runtime = bootstrap(root)

        result = runtime.health_check()

        print(
            f"SOL-Lite Doctor {__version__}"
        )
        print(
            f"  Platform: {sys.platform}"
        )
        print(
            f"  Python: {sys.version.split()[0]}"
        )
        print(
            f"  Root: {root}"
        )
        print(
            f"  Venv: {root / '.venv'}"
        )

        try:
            print(
                "  Rich: "
                f"{importlib.metadata.version('rich')}"
            )
        except importlib.metadata.PackageNotFoundError:
            result.errors.append(
                "Rich is not installed in the active "
                "Python environment."
            )

        try:
            print(
                "  PyYAML: "
                f"{importlib.metadata.version('PyYAML')}"
            )
        except importlib.metadata.PackageNotFoundError:
            result.errors.append(
                "PyYAML is not installed in the active "
                "Python environment."
            )

        install_state = (
            root
            / "data"
            / "state"
            / "install.json"
        )

        print(
            "  Install state: "
            f"{'present' if install_state.is_file() else 'missing'}"
        )

        if install_state.is_file():
            try:
                state = json.loads(
                    install_state.read_text(
                        encoding="utf-8"
                    )
                )

                print(
                    "  Installed version: "
                    f"{state.get('version', 'unknown')}"
                )
            except (
                OSError,
                json.JSONDecodeError,
            ) as exc:
                result.errors.append(
                    f"Install state is unreadable: {exc}"
                )

        config = load_config(root)

        endpoint = os.environ.get(
            "SOL_OLLAMA_URL",
            config.models.get(
                "provider",
                {},
            ).get(
                "endpoint",
                "http://127.0.0.1:11434",
            ),
        )

        print(
            f"  Ollama endpoint: {endpoint}"
        )

        if config.user_settings is not None:
            print(
                "  User settings: "
                f"{config.user_settings.path}"
            )

        if result.ok:
            for warning in result.warnings:
                print(
                    f"  WARNING: {warning}"
                )

            print(
                "SOL-Lite doctor: OK"
            )

            return

        for error in result.errors:
            print(
                f"  ERROR: {error}"
            )

        print(
            "SOL-Lite doctor: FAILED"
        )

        raise SystemExit(1)

    if args.command == "diagnose":
        config = load_config(root)

        host = os.environ.get(
            "SOL_OLLAMA_URL",
            config.models.get(
                "provider",
                {},
            ).get(
                "endpoint",
                "http://127.0.0.1:11434",
            ),
        )

        models = [
            value.get("model")
            for value in config.models.get(
                "profiles",
                {},
            ).values()
            if (
                isinstance(value, dict)
                and value.get("model")
            )
        ]

        result = diagnose_ollama(
            host,
            models,
        )

        print(
            json.dumps(
                result.data,
                indent=2,
                ensure_ascii=False,
            )
        )

        raise SystemExit(
            0 if result.ok else 1
        )

    if args.command == "start":
        runtime = bootstrap(root)
        runtime.start()

        try:
            default_agent = "sol_pa"

            if runtime.user_settings is not None:
                configured_agent = (
                    runtime.user_settings.get(
                        "general",
                        "default_agent",
                        default_agent,
                    )
                )

                if (
                    isinstance(
                        configured_agent,
                        str,
                    )
                    and configured_agent
                    in runtime.agents.names()
                ):
                    default_agent = configured_agent

            initial_agent = (
                args.agent
                if args.agent is not None
                else default_agent
            )

            shell = AgentShell(
                root=runtime.root,
                agents=runtime.agents,
                models=runtime.models,
                tools=runtime.tools,
                tool_context=runtime.tool_context,
                fault_log=runtime.fault_log,
                workspace_manager=(
                    runtime.workspace_manager
                ),
                session_manager=(
                    runtime.session_manager
                ),
                skill_manager=(
                    runtime.skill_manager
                ),
                task_manager=runtime.tasks,
                initial_agent=initial_agent,
                initial_workspace=args.workspace,
                verbose=(
                    args.verbose
                    or (
                        runtime.user_settings
                        is not None
                        and runtime.user_settings.get(
                            "display",
                            "mode",
                            "normal",
                        )
                        == "verbose"
                    )
                ),
                event_bus=runtime.events,
                settings_store=runtime.user_settings,
            )

            shell.run()

        finally:
            runtime.stop()

        return

    if args.command == "battle-test":
        commands = [
            [
                sys.executable,
                "scripts/audit-pack.py",
            ],
            [
                sys.executable,
                "scripts/preflight.py",
            ],
            [
                sys.executable,
                "-m",
                "compileall",
                "-q",
                "src",
                "tests",
            ],
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
            ],
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "src",
                "tests",
            ],
        ]

        for command in commands:
            print(
                "BATTLE:",
                " ".join(command),
            )

            completed = subprocess.run(
                command,
                cwd=root,
                check=False,
            )

            if completed.returncode:
                raise SystemExit(
                    completed.returncode
                )

        if args.live:
            run_live_smoke(
                bootstrap(root),
                args.agent,
            )

        print(
            "SOL-Lite battle test: PASS"
        )

        return

    build_parser().print_help()


if __name__ == "__main__":
    main()

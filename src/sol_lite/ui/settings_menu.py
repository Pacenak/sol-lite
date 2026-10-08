"""Interactive terminal settings menu for SOL-Lite."""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..config.user_settings import UserSettingsStore


class SettingsMenu:
    """Interactive settings editor backed by UserSettingsStore."""

    def __init__(
        self,
        *,
        store: UserSettingsStore,
        repository_config: dict[str, Any],
        console,
        display_mode_callback: Callable[[str], None] | None = None,
    ):
        self.store = store
        self.repository_config = repository_config
        self.console = console
        self.display_mode_callback = display_mode_callback

    def _effective(self) -> dict[str, Any]:
        return self.store.effective(self.repository_config)

    @staticmethod
    def _application_section(
        config: dict[str, Any],
        section: str,
    ) -> dict[str, Any]:
        """Get a section from the application YAML structure."""
        value = config.get(section, {})

        if isinstance(value, dict):
            return value

        return {}

    @staticmethod
    def _models_section(
        config: dict[str, Any],
    ) -> dict[str, Any]:
        value = config.get("models", {})
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _agents_section(
        config: dict[str, Any],
    ) -> dict[str, Any]:
        value = config.get("agents", {})
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _searxng_section(
        config: dict[str, Any],
    ) -> dict[str, Any]:
        value = config.get("searxng", {})
        return value if isinstance(value, dict) else {}

    def _repository_root_config(self) -> dict[str, Any]:
        """Build the logical application config used by the menu."""
        return {
            **self.repository_config,
            "models": self.repository_config.get("models", {}),
            "agents": self.repository_config.get("agents", {}),
            "searxng": self.repository_config.get("searxng", {}),
        }

    def _save(self) -> None:
        path = self.store.save()
        self.console.print(
            Text(
                f"Saved user settings: {path}",
                style="sol_success",
            )
        )

    def _input(
        self,
        prompt: str,
        default: str | None = None,
    ) -> str:
        suffix = (
            f" [{default}]"
            if default is not None
            else ""
        )

        try:
            answer = self.console.input(
                f"[sol_prompt]{prompt}{suffix} ❯ [/sol_prompt]"
            ).strip()
        except (EOFError, KeyboardInterrupt):
            return ""

        if not answer and default is not None:
            return default

        return answer

    def _boolean(
        self,
        prompt: str,
        current: bool,
    ) -> bool | None:
        default = "Y" if current else "N"

        answer = self._input(
            f"{prompt} [y/n]",
            default,
        ).casefold()

        if answer in {"y", "yes", "1", "true", "on"}:
            return True

        if answer in {"n", "no", "0", "false", "off"}:
            return False

        self.console.print(
            Text(
                "Enter y or n.",
                style="sol_warning",
            )
        )
        return None

    def _integer(
        self,
        prompt: str,
        current: int,
        minimum: int | None = None,
        maximum: int | None = None,
    ) -> int | None:
        answer = self._input(prompt, str(current))

        try:
            value = int(answer)
        except ValueError:
            self.console.print(
                Text(
                    "Enter a whole number.",
                    style="sol_warning",
                )
            )
            return None

        if minimum is not None and value < minimum:
            self.console.print(
                Text(
                    f"Value must be at least {minimum}.",
                    style="sol_warning",
                )
            )
            return None

        if maximum is not None and value > maximum:
            self.console.print(
                Text(
                    f"Value must not exceed {maximum}.",
                    style="sol_warning",
                )
            )
            return None

        return value

    def _float(
        self,
        prompt: str,
        current: float,
        minimum: float | None = None,
        maximum: float | None = None,
    ) -> float | None:
        answer = self._input(prompt, str(current))

        try:
            value = float(answer)
        except ValueError:
            self.console.print(
                Text(
                    "Enter a numeric value.",
                    style="sol_warning",
                )
            )
            return None

        if minimum is not None and value < minimum:
            self.console.print(
                Text(
                    f"Value must be at least {minimum}.",
                    style="sol_warning",
                )
            )
            return None

        if maximum is not None and value > maximum:
            self.console.print(
                Text(
                    f"Value must not exceed {maximum}.",
                    style="sol_warning",
                )
            )
            return None

        return value

    def _show_category(
        self,
        title: str,
        entries: list[tuple[str, str, Any]],
    ) -> None:
        table = Table(
            "Setting",
            "Value",
            "Source",
            border_style="sol_border",
            header_style="sol_core_bold",
        )

        for path, value, source in entries:
            table.add_row(
                Text(path, style="sol_identity"),
                Text(str(value), style="sol_neutral"),
                Text(source, style="sol_dim"),
            )

        self.console.print(
            Panel(
                table,
                title=Text(title, style="sol_identity"),
                border_style="sol_border",
            )
        )

    def _general(self) -> None:
        effective = self._effective()
        agents = self._agents_section(effective)

        current = self.store.get(
            "general",
            "default_agent",
            "sol_pa",
        )

        if current not in agents.get("agents", {}):
            current = "sol_pa"

        available = [
            agent_id
            for agent_id, data in agents.get("agents", {}).items()
            if isinstance(data, dict)
            and data.get("enabled", True)
        ]

        self.console.print(
            Panel(
                "General user preferences.",
                title="General",
                border_style="sol_border",
            )
        )

        self.console.print(
            "Available enabled agents: "
            + ", ".join(available)
        )

        value = self._input(
            "Default agent",
            current,
        )

        if value not in available:
            self.console.print(
                Text(
                    f"Unknown or disabled agent: {value}",
                    style="sol_error",
                )
            )
            return

        self.store.set(
            "general",
            "default_agent",
            value,
        )
        self._save()

    def _agents(self) -> None:
        effective = self._effective()
        agents_config = self._agents_section(effective)
        agents = agents_config.get("agents", {})

        if not isinstance(agents, dict):
            self.console.print(
                Text(
                    "Agent configuration is invalid.",
                    style="sol_error",
                )
            )
            return

        while True:
            table = Table(
                "#",
                "Agent",
                "Enabled",
                "Model Profile",
                border_style="sol_border",
                header_style="sol_core_bold",
            )

            records = list(agents.items())

            for index, (agent_id, data) in enumerate(records, 1):
                if not isinstance(data, dict):
                    continue

                table.add_row(
                    str(index),
                    agent_id,
                    str(bool(data.get("enabled", True))),
                    str(data.get("model_profile", "")),
                )

            table.add_row(
                "B",
                "Back",
                "",
                "",
            )

            self.console.print(table)

            answer = self._input(
                "Select agent number",
            ).casefold()

            if answer == "b":
                return

            if not answer.isdigit():
                self.console.print(
                    Text(
                        "Select a displayed agent number.",
                        style="sol_warning",
                    )
                )
                continue

            index = int(answer)

            if not 1 <= index <= len(records):
                self.console.print(
                    Text(
                        "Unknown agent selection.",
                        style="sol_warning",
                    )
                )
                continue

            agent_id, data = records[index - 1]

            if not isinstance(data, dict):
                continue

            enabled = self._boolean(
                f"Enable {agent_id}",
                bool(data.get("enabled", True)),
            )

            if enabled is None:
                continue

            self.store.set_path(
                "agents",
                ("agents", agent_id, "enabled"),
                enabled,
            )

            profile = self._input(
                "Model profile",
                str(data.get("model_profile", "engineer")),
            )

            models = self._models_section(effective)
            profiles = models.get("profiles", {})

            if profile not in profiles:
                self.console.print(
                    Text(
                        f"Unknown model profile: {profile}",
                        style="sol_warning",
                    )
                )
                continue

            self.store.set_path(
                "agents",
                ("agents", agent_id, "model_profile"),
                profile,
            )

            self._save()
            effective = self._effective()
            agents_config = self._agents_section(effective)
            agents = agents_config.get("agents", {})

    def _models(self) -> None:
        while True:
            effective = self._effective()
            models = self._models_section(effective)
            provider = models.get("provider", {})
            profiles = models.get("profiles", {})

            if not isinstance(provider, dict):
                provider = {}

            if not isinstance(profiles, dict):
                profiles = {}

            table = Table(
                "Option",
                "Current value",
                border_style="sol_border",
                header_style="sol_core_bold",
            )

            table.add_row(
                "1",
                f"Provider endpoint: {provider.get('endpoint', '')}",
            )
            table.add_row(
                "2",
                f"Provider trusted: {provider.get('trusted', False)}",
            )
            table.add_row(
                "3",
                "Edit model profile",
            )
            table.add_row(
                "B",
                "Back",
            )

            self.console.print(table)

            answer = self._input("Select option").casefold()

            if answer == "b":
                return

            if answer == "1":
                current = str(
                    self.store.get(
                        "models",
                        "provider",
                        {},
                    ).get(
                        "endpoint",
                        provider.get(
                            "endpoint",
                            "http://127.0.0.1:11434",
                        ),
                    )
                )

                value = self._input(
                    "Ollama provider endpoint",
                    current,
                )

                if not value:
                    self.console.print(
                        Text(
                            "Endpoint cannot be empty.",
                            style="sol_warning",
                        )
                    )
                    continue

                self.store.set_path(
                    "models",
                    ("provider", "endpoint"),
                    value,
                )
                self._save()
                continue

            if answer == "2":
                current = bool(
                    provider.get("trusted", False)
                )

                value = self._boolean(
                    "Trust configured provider",
                    current,
                )

                if value is None:
                    continue

                self.store.set_path(
                    "models",
                    ("provider", "trusted"),
                    value,
                )
                self._save()
                continue

            if answer == "3":
                self._model_profile_menu(profiles)
                continue

            self.console.print(
                Text(
                    "Unknown settings option.",
                    style="sol_warning",
                )
            )

    def _model_profile_menu(
        self,
        profiles: dict[str, Any],
    ) -> None:
        names = list(profiles)

        if not names:
            self.console.print(
                Text(
                    "No model profiles are configured.",
                    style="sol_warning",
                )
            )
            return

        table = Table(
            "#",
            "Profile",
            "Model",
            "Temperature",
            "Timeout",
            "Locality",
            border_style="sol_border",
            header_style="sol_core_bold",
        )

        for index, name in enumerate(names, 1):
            data = profiles[name]

            if not isinstance(data, dict):
                continue

            table.add_row(
                str(index),
                name,
                str(data.get("model", "")),
                str(data.get("temperature", "")),
                str(data.get("timeout_seconds", "")),
                str(data.get("locality", "")),
            )

        table.add_row("B", "Back", "", "", "", "")

        self.console.print(table)

        answer = self._input("Select profile").casefold()

        if answer == "b":
            return

        if not answer.isdigit():
            return

        index = int(answer)

        if not 1 <= index <= len(names):
            return

        name = names[index - 1]
        data = profiles[name]

        if not isinstance(data, dict):
            return

        model = self._input(
            "Model",
            str(data.get("model", "")),
        )

        if not model:
            self.console.print(
                Text(
                    "Model name cannot be empty.",
                    style="sol_warning",
                )
            )
            return

        temperature = self._float(
            "Temperature",
            float(data.get("temperature", 0.2)),
            0.0,
            2.0,
        )

        if temperature is None:
            return

        timeout = self._float(
            "Timeout seconds",
            float(data.get("timeout_seconds", 300)),
            1.0,
        )

        if timeout is None:
            return

        locality = self._input(
            "Locality (host/network/external/auto/any)",
            str(data.get("locality", "host")),
        ).casefold()

        if locality not in {
            "host",
            "network",
            "external",
            "auto",
            "any",
        }:
            self.console.print(
                Text(
                    "Unsupported locality.",
                    style="sol_warning",
                )
            )
            return

        self.store.set_path(
            "models",
            ("profiles", name, "model"),
            model,
        )
        self.store.set_path(
            "models",
            ("profiles", name, "temperature"),
            temperature,
        )
        self.store.set_path(
            "models",
            ("profiles", name, "timeout_seconds"),
            timeout,
        )
        self.store.set_path(
            "models",
            ("profiles", name, "locality"),
            locality,
        )

        self._save()

    def _runtime(self) -> None:
        effective = self._effective()
        runtime = self._application_section(
            effective,
            "runtime",
        )

        fields = [
            (
                "mode",
                str(runtime.get("mode", "assisted")),
            ),
            (
                "max_concurrent_agents",
                int(runtime.get("max_concurrent_agents", 4)),
            ),
            (
                "max_tool_calls_per_task",
                int(runtime.get("max_tool_calls_per_task", 40)),
            ),
            (
                "task_timeout_seconds",
                int(runtime.get("task_timeout_seconds", 900)),
            ),
            (
                "status_heartbeat_seconds",
                int(runtime.get("status_heartbeat_seconds", 1)),
            ),
            (
                "slow_threshold_seconds",
                int(runtime.get("slow_threshold_seconds", 45)),
            ),
            (
                "stall_threshold_seconds",
                int(runtime.get("stall_threshold_seconds", 90)),
            ),
        ]

        table = Table(
            "Option",
            "Setting",
            "Current value",
            border_style="sol_border",
            header_style="sol_core_bold",
        )

        for index, (name, value) in enumerate(fields, 1):
            table.add_row(
                str(index),
                name,
                str(value),
            )

        table.add_row("B", "Back", "")

        self.console.print(table)

        answer = self._input("Select option").casefold()

        if answer == "b":
            return

        if not answer.isdigit():
            return

        index = int(answer)

        if not 1 <= index <= len(fields):
            return

        name, current = fields[index - 1]

        if name == "mode":
            value = self._input(
                "Runtime mode",
                str(current),
            )

            if value not in {
                "assisted",
                "autonomous",
                "manual",
            }:
                self.console.print(
                    Text(
                        "Supported modes are assisted, autonomous and manual.",
                        style="sol_warning",
                    )
                )
                return
        else:
            value = self._integer(
                name,
                int(current),
                1,
            )

            if value is None:
                return

        self.store.set_path(
            "runtime",
            (name,),
            value,
        )
        self._save()

    def _workspace_data(self) -> None:
        effective = self._effective()

        workspace = self._application_section(
            effective,
            "workspace",
        )
        data = self._application_section(
            effective,
            "data",
        )

        table = Table(
            "Option",
            "Setting",
            "Current value",
            border_style="sol_border",
            header_style="sol_core_bold",
        )

        table.add_row(
            "1",
            "workspace.root",
            str(workspace.get("root", "")),
        )
        table.add_row(
            "2",
            "data.root",
            str(data.get("root", "")),
        )
        table.add_row(
            "3",
            "workspace.directories",
            str(workspace.get("directories", {})),
        )
        table.add_row(
            "4",
            "data.directories",
            str(data.get("directories", {})),
        )
        table.add_row("B", "Back", "")

        self.console.print(table)

        answer = self._input("Select option").casefold()

        if answer == "b":
            return

        if answer == "1":
            value = self._input(
                "Workspace root",
                str(workspace.get("root", "./workspace")),
            )
            if value:
                self.store.set_path(
                    "workspace",
                    ("root",),
                    value,
                )
                self._save()
            return

        if answer == "2":
            value = self._input(
                "Data root",
                str(data.get("root", "./data")),
            )
            if value:
                self.store.set_path(
                    "data",
                    ("root",),
                    value,
                )
                self._save()
            return

        if answer == "3":
            self.console.print(
                Text(
                    "Workspace directory mappings are repository-defined "
                    "and should normally be changed by editing the "
                    "workspace.directories settings YAML.",
                    style="sol_dim",
                )
            )
            return

        if answer == "4":
            self.console.print(
                Text(
                    "Data directory mappings are repository-defined "
                    "and should normally be changed by editing the "
                    "data.directories settings YAML.",
                    style="sol_dim",
                )
            )

    def _search(self) -> None:
        effective = self._effective()
        search = self._searxng_section(effective)

        table = Table(
            "Option",
            "Setting",
            "Current value",
            border_style="sol_border",
            header_style="sol_core_bold",
        )

        table.add_row(
            "1",
            "enabled",
            str(search.get("enabled", False)),
        )
        table.add_row(
            "2",
            "url",
            str(search.get("url", "")),
        )
        table.add_row(
            "3",
            "timeout_seconds",
            str(search.get("timeout_seconds", 15)),
        )
        table.add_row(
            "4",
            "max_results",
            str(search.get("max_results", 8)),
        )
        table.add_row(
            "5",
            "categories",
            str(search.get("categories", "general")),
        )
        table.add_row(
            "6",
            "language",
            str(search.get("language", "en")),
        )
        table.add_row(
            "7",
            "safesearch",
            str(search.get("safesearch", 1)),
        )
        table.add_row(
            "8",
            "engines",
            str(search.get("engines", "")),
        )
        table.add_row("B", "Back", "")

        self.console.print(table)

        answer = self._input("Select option").casefold()

        if answer == "b":
            return

        mapping = {
            "1": ("enabled", "bool"),
            "2": ("url", "str"),
            "3": ("timeout_seconds", "int"),
            "4": ("max_results", "int"),
            "5": ("categories", "str"),
            "6": ("language", "str"),
            "7": ("safesearch", "int"),
            "8": ("engines", "str"),
        }

        selected = mapping.get(answer)

        if selected is None:
            return

        name, kind = selected
        current = search.get(name)

        if kind == "bool":
            value = self._boolean(
                name,
                bool(current),
            )
        elif kind == "int":
            value = self._integer(
                name,
                int(current),
                0,
            )
        else:
            value = self._input(
                name,
                str(current if current is not None else ""),
            )

        if value is None:
            return

        self.store.set_path(
            "searxng",
            (name,),
            value,
        )
        self._save()

    def _integrations(self) -> None:
        effective = self._effective()

        background = self._application_section(
            effective,
            "background",
        )
        macos = self._application_section(
            effective,
            "macos",
        )
        windows = self._application_section(
            effective,
            "windows",
        )
        nas = self._application_section(
            effective,
            "nas",
        )
        bridge = self._application_section(
            effective,
            "bridge",
        )

        table = Table(
            "Option",
            "Setting",
            "Current value",
            border_style="sol_border",
            header_style="sol_core_bold",
        )

        table.add_row(
            "1",
            "background.enabled",
            str(background.get("enabled", False)),
        )
        table.add_row(
            "2",
            "background.allow_after_hours",
            str(background.get("allow_after_hours", False)),
        )
        table.add_row(
            "3",
            "macos.integrations_enabled",
            str(macos.get("integrations_enabled", False)),
        )
        table.add_row(
            "4",
            "windows.integrations_enabled",
            str(windows.get("integrations_enabled", False)),
        )
        table.add_row(
            "5",
            "nas.enabled",
            str(nas.get("enabled", False)),
        )
        table.add_row(
            "6",
            "nas.path",
            str(nas.get("path", "")),
        )
        table.add_row(
            "7",
            "bridge.enabled",
            str(bridge.get("enabled", False)),
        )
        table.add_row(
            "8",
            "bridge.listen_host",
            str(bridge.get("listen_host", "127.0.0.1")),
        )
        table.add_row(
            "9",
            "bridge.listen_port",
            str(bridge.get("listen_port", 8787)),
        )
        table.add_row("B", "Back", "")

        self.console.print(table)

        answer = self._input("Select option").casefold()

        if answer == "b":
            return

        bool_fields = {
            "1": ("background", "enabled"),
            "2": ("background", "allow_after_hours"),
            "3": ("macos", "integrations_enabled"),
            "4": ("windows", "integrations_enabled"),
            "5": ("nas", "enabled"),
            "7": ("bridge", "enabled"),
        }

        if answer in bool_fields:
            section, key = bool_fields[answer]
            section_data = self._application_section(
                effective,
                section,
            )
            value = self._boolean(
                f"{section}.{key}",
                bool(section_data.get(key, False)),
            )

            if value is None:
                return

            self.store.set_path(
                section,
                (key,),
                value,
            )
            self._save()
            return

        if answer == "6":
            value = self._input(
                "NAS path",
                str(nas.get("path", "")),
            )
            self.store.set_path(
                "nas",
                ("path",),
                value if value else None,
            )
            self._save()
            return

        if answer == "8":
            value = self._input(
                "Bridge listen host",
                str(bridge.get("listen_host", "127.0.0.1")),
            )
            if value:
                self.store.set_path(
                    "bridge",
                    ("listen_host",),
                    value,
                )
                self._save()
            return

        if answer == "9":
            value = self._integer(
                "Bridge listen port",
                int(bridge.get("listen_port", 8787)),
                1,
                65535,
            )
            if value is not None:
                self.store.set_path(
                    "bridge",
                    ("listen_port",),
                    value,
                )
                self._save()

    def _display(self) -> None:
        current = str(
            self.store.get(
                "display",
                "mode",
                "normal",
            )
        ).casefold()

        table = Table(
            "Mode",
            "Purpose",
            border_style="sol_border",
            header_style="sol_core_bold",
        )

        table.add_row(
            "normal",
            "Standard low-noise terminal display",
        )
        table.add_row(
            "verbose",
            "Expanded activity information",
        )
        table.add_row(
            "debug",
            "Detailed runtime diagnostics",
        )

        self.console.print(table)

        value = self._input(
            "Display mode",
            current,
        ).casefold()

        if value not in {"normal", "verbose", "debug"}:
            self.console.print(
                Text(
                    "Supported modes: normal, verbose, debug.",
                    style="sol_warning",
                )
            )
            return

        self.store.set(
            "display",
            "mode",
            value,
        )
        self._save()

        if self.display_mode_callback is not None:
            self.display_mode_callback(value)

    def _view(self) -> None:
        effective = self._effective()

        self.console.print(
            Panel(
                f"User settings file:\n{self.store.path}\n\n"
                f"Exists: {self.store.exists}",
                title="Settings Location",
                border_style="sol_border",
            )
        )

        overrides = self.store.settings

        if overrides:
            table = Table(
                "Section",
                "User override",
                border_style="sol_border",
                header_style="sol_core_bold",
            )

            for section, value in overrides.items():
                table.add_row(
                    section,
                    str(value),
                )

            self.console.print(
                Panel(
                    table,
                    title="User Overrides",
                    border_style="sol_border",
                )
            )
        else:
            self.console.print(
                Text(
                    "No user overrides are currently saved.",
                    style="sol_dim",
                )
            )

        self.console.print(
            Panel(
                yaml_dump(effective),
                title="Effective Configuration",
                border_style="sol_border",
            )
        )

    def _reset(self) -> None:
        self.console.print(
            Panel(
                "Resetting settings removes only user overrides. "
                "Repository configuration remains unchanged.",
                title="Reset User Settings",
                border_style="sol_warning",
            )
        )

        answer = self._input(
            "Reset all user settings? [y/n]",
            "n",
        ).casefold()

        if answer not in {"y", "yes"}:
            return

        self.store.reset()
        self._save()

        if self.display_mode_callback is not None:
            self.display_mode_callback("normal")

    def run(self) -> bool:
        """Run the menu.

        Returns True when the menu completed normally.
        """
        while True:
            table = Table(
                "Option",
                "Settings",
                border_style="sol_border",
                header_style="sol_core_bold",
            )

            table.add_row(
                "1",
                "General",
            )
            table.add_row(
                "2",
                "Agents",
            )
            table.add_row(
                "3",
                "Models & Ollama",
            )
            table.add_row(
                "4",
                "Runtime",
            )
            table.add_row(
                "5",
                "Workspace & Data",
            )
            table.add_row(
                "6",
                "Search / SearXNG",
            )
            table.add_row(
                "7",
                "Background & Integrations",
            )
            table.add_row(
                "8",
                "Terminal & Display",
            )
            table.add_row(
                "9",
                "View Configuration",
            )
            table.add_row(
                "R",
                "Reset User Settings",
            )
            table.add_row(
                "B",
                "Back",
            )

            self.console.print(
                Panel(
                    table,
                    title=Text(
                        "SOL-Lite Settings",
                        style="sol_identity",
                    ),
                    border_style="sol_border",
                )
            )

            answer = self._input(
                "Select settings category",
            ).casefold()

            try:
                if answer == "1":
                    self._general()
                elif answer == "2":
                    self._agents()
                elif answer == "3":
                    self._models()
                elif answer == "4":
                    self._runtime()
                elif answer == "5":
                    self._workspace_data()
                elif answer == "6":
                    self._search()
                elif answer == "7":
                    self._integrations()
                elif answer == "8":
                    self._display()
                elif answer == "9":
                    self._view()
                elif answer == "r":
                    self._reset()
                elif answer == "b":
                    return True
                else:
                    self.console.print(
                        Text(
                            "Unknown settings option.",
                            style="sol_warning",
                        )
                    )
            except (
                OSError,
                TypeError,
                ValueError,
            ) as exc:
                self.console.print(
                    Panel(
                        str(exc),
                        title="Settings Error",
                        border_style="sol_error",
                    )
                )


def yaml_dump(value: Any) -> str:
    """Render a mapping for the terminal without mutating it."""
    return yaml_safe_dump(value)


def yaml_safe_dump(value: Any) -> str:
    """Keep YAML rendering local to this module."""
    import yaml

    return yaml.safe_dump(
        copy.deepcopy(value),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
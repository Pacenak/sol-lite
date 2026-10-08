"""Persistent per-user SOL-Lite settings.

Repository configuration remains the source of application defaults.
User settings are stored outside the repository and are merged over the
repository configuration at startup.

Security-sensitive permission policy is deliberately excluded from this layer.
Environment variables and CLI arguments retain precedence over these settings.
"""

from __future__ import annotations

import copy
import os
import platform
import tempfile
from pathlib import Path
from typing import Any

import yaml

SUPPORTED_USER_SECTIONS = frozenset(
    {
        "general",
        "runtime",
        "workspace",
        "data",
        "logging",
        "background",
        "macos",
        "windows",
        "nas",
        "bridge",
        "models",
        "agents",
        "searxng",
        "display",
    }
)

_FORBIDDEN_USER_SECTIONS = frozenset(
    {
        "permissions",
        "security",
        "credentials",
        "secrets",
        "approvals",
        "capabilities",
    }
)


def deep_merge(
    base: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    """Return a recursive merge without mutating either input mapping."""
    result = copy.deepcopy(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)

    return result


class UserSettingsStore:
    """Load, validate, edit, save and reset user-owned settings."""

    def __init__(self, path: Path | None = None):
        self.path = (
            Path(path).expanduser().resolve()
            if path is not None
            else self.default_path()
        )
        self._settings: dict[str, Any] = {}
        self.load()

    @staticmethod
    def default_path() -> Path:
        """Return the platform-appropriate persistent settings path."""
        override = os.environ.get("SOL_LITE_SETTINGS_FILE")

        if override:
            return Path(override).expanduser().resolve()

        system = platform.system()

        if system == "Windows":
            appdata = os.environ.get("APPDATA")
            if appdata:
                return (
                    Path(appdata)
                    / "SOL-Lite"
                    / "settings.yaml"
                ).resolve()

            return (
                Path.home()
                / "AppData"
                / "Roaming"
                / "SOL-Lite"
                / "settings.yaml"
            ).resolve()

        if system == "Darwin":
            return (
                Path.home()
                / "Library"
                / "Application Support"
                / "SOL-Lite"
                / "settings.yaml"
            ).resolve()

        return (
            Path.home()
            / ".config"
            / "sol-lite"
            / "settings.yaml"
        ).resolve()

    @property
    def settings(self) -> dict[str, Any]:
        """Return a defensive copy of user overrides."""
        return copy.deepcopy(self._settings)

    @property
    def exists(self) -> bool:
        """Return whether the persistent settings file exists."""
        return self.path.is_file()

    def load(self) -> dict[str, Any]:
        """Load user settings from disk.

        A missing settings file is normal and produces an empty override
        mapping. Invalid YAML or unsupported sections are rejected.
        """
        if not self.path.is_file():
            self._settings = {}
            return self.settings

        with self.path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)

        if data is None:
            self._settings = {}
            return self.settings

        if not isinstance(data, dict):
            raise TypeError(
                f"User settings must contain a YAML mapping: {self.path}"
            )

        self._validate_sections(data)
        self._settings = copy.deepcopy(data)
        return self.settings

    def _validate_sections(
        self,
        data: dict[str, Any],
    ) -> None:
        """Validate top-level user-editable sections."""
        forbidden = sorted(
            set(data).intersection(_FORBIDDEN_USER_SECTIONS)
        )

        if forbidden:
            raise ValueError(
                "The following configuration sections cannot be changed "
                f"through user settings: {', '.join(forbidden)}"
            )

        unsupported = sorted(
            set(data).difference(SUPPORTED_USER_SECTIONS)
        )

        if unsupported:
            raise ValueError(
                "Unsupported user settings section(s): "
                f"{', '.join(unsupported)}"
            )

        for section, value in data.items():
            if not isinstance(value, dict):
                raise TypeError(
                    f"User settings section '{section}' must be a mapping."
                )

    def get(
        self,
        section: str,
        key: str | None = None,
        default: Any = None,
    ) -> Any:
        """Read a user override."""
        value = self._settings.get(section)

        if key is None:
            return copy.deepcopy(
                value if value is not None else default
            )

        if not isinstance(value, dict):
            return copy.deepcopy(default)

        return copy.deepcopy(value.get(key, default))

    def section(self, section: str) -> dict[str, Any]:
        """Return one user settings section."""
        value = self._settings.get(section, {})
        if not isinstance(value, dict):
            return {}
        return copy.deepcopy(value)

    def set(
        self,
        section: str,
        key: str,
        value: Any,
    ) -> None:
        """Set a nested user setting in memory."""
        self._validate_section_name(section)

        if not key:
            raise ValueError("A settings key is required.")

        target = self._settings.setdefault(section, {})

        if not isinstance(target, dict):
            raise TypeError(
                f"User settings section '{section}' is not a mapping."
            )

        target[key] = copy.deepcopy(value)

    def set_path(
        self,
        section: str,
        path: tuple[str, ...],
        value: Any,
    ) -> None:
        """Set a nested value using a path below a supported section."""
        self._validate_section_name(section)

        if not path:
            raise ValueError("A nested settings path is required.")

        target = self._settings.setdefault(section, {})

        if not isinstance(target, dict):
            raise TypeError(
                f"User settings section '{section}' is not a mapping."
            )

        for component in path[:-1]:
            child = target.setdefault(component, {})

            if not isinstance(child, dict):
                raise TypeError(
                    f"Cannot descend through non-mapping setting "
                    f"'{component}'."
                )

            target = child

        target[path[-1]] = copy.deepcopy(value)

    def remove(
        self,
        section: str,
        key: str | None = None,
    ) -> None:
        """Remove a setting override."""
        self._validate_section_name(section)

        if section not in self._settings:
            return

        if key is None:
            del self._settings[section]
            return

        target = self._settings[section]

        if not isinstance(target, dict):
            return

        target.pop(key, None)

        if not target:
            self._settings.pop(section, None)

    def reset(self, section: str | None = None) -> None:
        """Reset all settings or one supported section."""
        if section is None:
            self._settings = {}
            return

        self._validate_section_name(section)
        self._settings.pop(section, None)

    def save(self) -> Path:
        """Atomically save the current user settings."""
        self._validate_sections(self._settings)

        self.path.parent.mkdir(parents=True, exist_ok=True)

        payload = yaml.safe_dump(
            self._settings,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )

        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=str(self.path.parent),
            text=True,
        )

        temporary_path = Path(temporary_name)

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())

            temporary_path.replace(self.path)
        except Exception:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

        return self.path

    def effective(
        self,
        repository_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge user settings over repository configuration.

        Only supported user sections are merged. This prevents a malformed
        or manually edited settings file from introducing permission policy
        or other protected configuration into the runtime.
        """
        if not isinstance(repository_config, dict):
            raise TypeError("Repository configuration must be a mapping.")

        filtered = {
            key: value
            for key, value in self._settings.items()
            if key in SUPPORTED_USER_SECTIONS
        }

        return deep_merge(repository_config, filtered)

    def _validate_section_name(self, section: str) -> None:
        if section in _FORBIDDEN_USER_SECTIONS:
            raise ValueError(
                f"Configuration section '{section}' is protected."
            )

        if section not in SUPPORTED_USER_SECTIONS:
            raise ValueError(
                f"Unsupported user settings section: {section}"
            )
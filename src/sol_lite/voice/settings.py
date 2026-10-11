"""Voice settings stored outside the repository config."""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_VOICE = "af_bella"


def settings_path(data_root) -> Path:
    return Path(data_root) / "state" / "voice.json"


def default_settings() -> dict:
    return {
        "stt_enabled": False,
        "stt_provider": "disabled",
        "stt_model": "base",
        "stt_language": "",
        "tts_enabled": False,
        "tts_provider": "disabled",
        "tts_voice": DEFAULT_VOICE,
        "tts_speed": 1.0,
        "speak": False,
        "endpoints": {},
    }


def settings_from_probe(probe: dict) -> dict:
    """Choose local engines when they can run. Do not disable a working engine."""
    settings = default_settings()
    if probe.get("faster_whisper_import"):
        settings["stt_enabled"] = True
        settings["stt_provider"] = "local"
    if probe.get("kokoro_import") and probe.get("espeak_ok"):
        settings["tts_enabled"] = True
        settings["tts_provider"] = "local"
        settings["tts_voice"] = DEFAULT_VOICE
        settings["speak"] = True
    return settings


def load_settings(data_root) -> dict:
    path = settings_path(data_root)
    settings = default_settings()
    if not path.is_file():
        return settings
    saved = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(saved, dict):
        settings.update({key: saved[key] for key in settings if key in saved})
        if isinstance(saved.get("endpoints"), dict):
            settings["endpoints"] = saved["endpoints"]
    return settings


def save_settings(data_root, settings: dict) -> None:
    path = settings_path(data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def apply_probe_defaults(data_root, probe: dict) -> dict:
    incoming = settings_from_probe(probe)
    path = settings_path(data_root)
    if not path.is_file():
        save_settings(data_root, incoming)
        return incoming
    current = load_settings(data_root)
    if current.get("stt_provider") == "disabled" and incoming["stt_provider"] == "local":
        current["stt_provider"] = "local"
        current["stt_enabled"] = True
    if current.get("tts_provider") == "disabled" and incoming["tts_provider"] == "local":
        current["tts_provider"] = "local"
        current["tts_enabled"] = True
        current["tts_voice"] = current.get("tts_voice") or DEFAULT_VOICE
        current["speak"] = True
    save_settings(data_root, current)
    return current


def toggle_speak(data_root) -> bool:
    settings = load_settings(data_root)
    settings["speak"] = not bool(settings.get("speak"))
    if settings["speak"] and settings.get("tts_provider") == "disabled":
        settings["speak"] = False
        save_settings(data_root, settings)
        raise RuntimeError("Text-to-speech is not available. Run sol-lite voice-status.")
    save_settings(data_root, settings)
    return bool(settings["speak"])

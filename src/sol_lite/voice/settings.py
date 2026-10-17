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
        "stt_model": "small",
        "listen": True,
        "agent_voices": {},
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
    elif probe.get("platform_speech"):
        settings["tts_enabled"] = True
        settings["tts_provider"] = "platform"
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
    if current.get("tts_provider") == "disabled" and incoming["tts_provider"] in {"local", "platform"}:
        current["tts_provider"] = incoming["tts_provider"]
        current["tts_enabled"] = True
        current["tts_voice"] = current.get("tts_voice") or DEFAULT_VOICE
        # Preserve the user's spoken-reply switch during discovery.
    save_settings(data_root, current)
    return current


def ensure_voice_settings(data_root) -> dict:
    """Turn on an operating-system voice when Kokoro was saved as unavailable."""
    from .probe import probe_voice

    return apply_probe_defaults(data_root, probe_voice(data_root))


def toggle_speak(data_root) -> bool:
    before = load_settings(data_root)
    was_unavailable = before.get("tts_provider") == "disabled" or not before.get("tts_enabled")
    settings = ensure_voice_settings(data_root)
    if settings.get("tts_provider") == "disabled" or not settings.get("tts_enabled"):
        settings["speak"] = False
        save_settings(data_root, settings)
        raise RuntimeError("Text-to-speech is not available. Run sol-lite voice-status.")
    settings["speak"] = True if was_unavailable else not bool(settings.get("speak"))
    save_settings(data_root, settings)
    return bool(settings["speak"])


def set_switch(data_root, name: str, enabled: bool) -> bool:
    if name not in {"listen", "speak"}:
        raise ValueError("Unknown voice switch")
    settings = ensure_voice_settings(data_root)
    if enabled:
        prefix = "stt" if name == "listen" else "tts"
        if not settings.get(f"{prefix}_enabled"):
            raise RuntimeError("Voice engine unavailable. Run sol-lite voice-status.")
    settings[name] = enabled
    save_settings(data_root, settings)
    return enabled

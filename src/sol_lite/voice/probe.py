"""Local speech readiness. Probes do not download model weights."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _can_import(name: str) -> bool:
    try:
        __import__(name)
        return True
    except (ImportError, OSError, RuntimeError):
        return False


def _known_espeak_dirs() -> list[Path]:
    if sys.platform == "win32":
        directories = []
        for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
            root = os.environ.get(env_name)
            if root:
                directories.append(Path(root) / "eSpeak NG")
        return directories
    return [Path("/opt/homebrew/bin"), Path("/usr/local/bin")]


def ensure_espeak_on_path() -> str:
    """Return espeak-ng, including the default install directory before PATH refreshes."""
    found = shutil.which("espeak-ng") or shutil.which("espeak")
    if found:
        return found
    names = ("espeak-ng.exe", "espeak.exe") if sys.platform == "win32" else ("espeak-ng", "espeak")
    for directory in _known_espeak_dirs():
        for name in names:
            path = directory / name
            if path.is_file():
                os.environ["PATH"] = str(directory) + os.pathsep + os.environ.get("PATH", "")
                return str(path)
    return ""


def cache_dirs(data_root) -> tuple[Path, Path]:
    root = Path(data_root)
    return root / "tts" / "kokoro", root / "tts" / "hf"


def ensure_cache(data_root) -> None:
    voices, hf_home = cache_dirs(data_root)
    voices.mkdir(parents=True, exist_ok=True)
    hf_home.mkdir(parents=True, exist_ok=True)
    readme = voices / "README.md"
    if not readme.is_file():
        readme.write_text(
            "Kokoro voice cache lives here. Weights download into ../hf. Do not commit binaries.\n",
            encoding="utf-8",
        )


def apply_hf_home(data_root) -> str:
    ensure_cache(data_root)
    hf_home = str(cache_dirs(data_root)[1])
    if not (os.environ.get("HF_HOME") or "").strip():
        os.environ["HF_HOME"] = hf_home
    return os.environ.get("HF_HOME") or hf_home


def _weights_present(data_root) -> bool:
    _voices, hf_home = cache_dirs(data_root)
    return hf_home.is_dir() and any(path.is_file() for path in hf_home.rglob("*"))


def probe_voice(data_root=None) -> dict:
    espeak = ensure_espeak_on_path()
    voices = hf_home = ""
    weights = False
    if data_root is not None:
        voice_dir, hf_dir = cache_dirs(data_root)
        voices = str(voice_dir)
        hf_home = str(hf_dir)
        weights = _weights_present(data_root)
    return {
        "faster_whisper_import": _can_import("faster_whisper"),
        "kokoro_import": _can_import("kokoro"),
        "soundfile_import": _can_import("soundfile"),
        "sounddevice_import": _can_import("sounddevice"),
        "espeak_ok": bool(espeak),
        "espeak_path": espeak or "",
        "voices_dir": voices,
        "hf_home": hf_home,
        "weights_on_disk": weights,
    }


def readiness(probe: dict) -> dict:
    if probe.get("faster_whisper_import") and probe.get("weights_on_disk"):
        stt, stt_detail = "ready", ""
    elif probe.get("faster_whisper_import"):
        stt, stt_detail = "degraded", "Whisper weights are not downloaded yet"
    else:
        stt, stt_detail = "degraded", "faster-whisper is not installed"
    if probe.get("kokoro_import") and probe.get("espeak_ok") and probe.get("weights_on_disk"):
        tts, tts_detail = "ready", ""
    elif not probe.get("kokoro_import"):
        if sys.version_info >= (3, 13):
            detail = (
                "Kokoro requires Python 3.10-3.12; "
                f"this environment is Python {sys.version_info[0]}.{sys.version_info[1]}"
            )
            tts, tts_detail = "degraded", detail
        else:
            tts, tts_detail = "degraded", "kokoro is not installed"
    elif not probe.get("espeak_ok"):
        tts, tts_detail = "degraded", "espeak-ng is not on PATH"
    else:
        tts, tts_detail = "degraded", "Kokoro weights are not downloaded yet"
    return {"stt": stt, "tts": tts, "stt_detail": stt_detail, "tts_detail": tts_detail}


def voice_doctor_lines(data_root) -> list[str]:
    report = readiness(probe_voice(data_root))
    lines = []
    for label, state, detail in (
        ("Voice STT", report["stt"], report["stt_detail"]),
        ("Voice TTS", report["tts"], report["tts_detail"]),
    ):
        suffix = f" ({detail})" if detail else ""
        lines.append(f"{label}: {state}{suffix}")
    return lines

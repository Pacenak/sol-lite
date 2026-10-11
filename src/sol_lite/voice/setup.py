"""Installer helper for espeak-ng, voice settings, and model prefetch."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .probe import apply_hf_home, ensure_cache, probe_voice
from .settings import apply_probe_defaults


def ensure_espeak() -> dict:
    from .probe import ensure_espeak_on_path

    if ensure_espeak_on_path():
        return {"espeak": "present"}
    if sys.platform == "win32":
        command = [
            "winget", "install", "--id", "eSpeak-NG.eSpeak-NG", "-e",
            "--accept-package-agreements", "--accept-source-agreements",
            "--disable-interactivity",
        ]
    elif sys.platform == "darwin" and shutil.which("brew"):
        command = ["brew", "install", "espeak-ng"]
    else:
        return {"espeak": "missing", "detail": "Install espeak-ng and re-run the SOL-Lite installer."}
    try:
        subprocess.run(command, check=False)
    except OSError as exc:
        return {"espeak": "missing", "detail": str(exc)}
    if ensure_espeak_on_path():
        return {"espeak": "installed"}
    return {"espeak": "missing", "detail": "The espeak-ng installer ran, but the command is not on PATH."}


def prefetch(data_root) -> list[str]:
    """Download local voice weights. A failure is reported and does not raise."""
    errors = []
    apply_hf_home(data_root)
    try:
        from faster_whisper import WhisperModel
        WhisperModel(
            "base", device="cpu", compute_type="int8",
            download_root=str(Path(apply_hf_home(data_root)) / "whisper"),
        )
    except Exception as exc:  # noqa: BLE001 - a failed model download must not fail setup
        errors.append(f"whisper: {exc}")
    try:
        from kokoro import KPipeline
        KPipeline(lang_code="a")
    except Exception as exc:  # noqa: BLE001 - a failed model download must not fail setup
        errors.append(f"kokoro: {exc}")
    return errors


def prepare_voice(root) -> dict:
    data_root = Path(root) / "data"
    ensure_cache(data_root)
    espeak = ensure_espeak()
    probe = probe_voice(data_root)
    settings = apply_probe_defaults(data_root, probe)
    errors = []
    if probe.get("faster_whisper_import") or probe.get("kokoro_import"):
        errors = prefetch(data_root)
    return {
        "espeak": espeak,
        "stt_provider": settings.get("stt_provider"),
        "tts_provider": settings.get("tts_provider"),
        "prefetch_errors": errors,
    }


def main() -> int:
    report = prepare_voice(Path.cwd())
    print(report["espeak"])
    if report["prefetch_errors"]:
        print("Voice model prefetch needs attention:")
        for error in report["prefetch_errors"]:
            print(f"  {error}")
    else:
        print(f"Voice ready: stt={report['stt_provider']} tts={report['tts_provider']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

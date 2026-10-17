"""faster-whisper and Kokoro adapters. Imports stay inside the call that needs them."""
from __future__ import annotations

import io
import os
import tempfile
from functools import lru_cache
from pathlib import Path

from .probe import apply_hf_home
from .settings import DEFAULT_VOICE


def _speed(value) -> float:
    try:
        speed = float(value)
    except (TypeError, ValueError):
        return 1.0
    if speed <= 0:
        return 1.0
    return min(4.0, max(0.25, speed))


def _endpoint(settings: dict, provider: str) -> dict:
    endpoint_id = provider.split(":", 1)[1]
    spec = (settings.get("endpoints") or {}).get(endpoint_id)
    if not isinstance(spec, dict) or not spec.get("base_url"):
        raise RuntimeError(f"Voice endpoint {endpoint_id} is not configured")
    headers = {}
    env_name = str(spec.get("api_key_env") or "")
    if env_name:
        key = os.environ.get(env_name) or ""
        if not key:
            raise RuntimeError(f"Set {env_name} for voice endpoint {endpoint_id}")
        headers["Authorization"] = f"Bearer {key}"
    return {"id": endpoint_id, "base_url": str(spec["base_url"]).rstrip("/"), "headers": headers, "spec": spec}


def transcribe(audio: bytes, settings: dict, data_root) -> str:
    provider = str(settings.get("stt_provider") or "disabled")
    if not audio:
        return ""
    if provider == "local":
        return _transcribe_local(audio, settings, data_root)
    if provider.startswith("endpoint:"):
        return _transcribe_endpoint(audio, settings, provider)
    raise RuntimeError("Speech-to-text is disabled. Run the SOL-Lite installer or sol-lite voice-status.")


def synthesize(text: str, settings: dict, data_root) -> bytes:
    spoken = (text or "").strip()
    if not spoken:
        return b""
    provider = str(settings.get("tts_provider") or "disabled")
    if provider == "local":
        return _synthesize_local(spoken, settings, data_root)
    if provider == "platform":
        return _synthesize_platform(spoken)
    if provider.startswith("endpoint:"):
        return _synthesize_endpoint(spoken, settings, provider)
    raise RuntimeError("Text-to-speech is disabled. Run the SOL-Lite installer or sol-lite voice-status.")


def _transcribe_local(audio: bytes, settings: dict, data_root) -> str:
    try:
        import faster_whisper  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("faster-whisper is not installed. Re-run the SOL-Lite installer.") from exc
    model_name = str(settings.get("stt_model") or "small")
    try:
        import torch
        use_cuda = bool(torch.cuda.is_available())
    except (ImportError, OSError, RuntimeError):
        use_cuda = False
    device = "cuda" if use_cuda else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    download_root = str(Path(apply_hf_home(data_root)) / "whisper")
    model = _whisper_model(model_name, device, compute_type, download_root)
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            handle.write(audio)
            path = handle.name
        language = str(settings.get("stt_language") or "").strip()
        kwargs = {"language": language} if language else {}
        kwargs.update(beam_size=5, vad_filter=True, condition_on_previous_text=False)
        segments, _info = model.transcribe(path, **kwargs)
        return " ".join(segment.text.strip() for segment in segments).strip()
    finally:
        if path:
            Path(path).unlink(missing_ok=True)


def _transcribe_endpoint(audio: bytes, settings: dict, provider: str) -> str:
    import httpx

    endpoint = _endpoint(settings, provider)
    model = str(endpoint["spec"].get("stt_model") or "whisper-1")
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{endpoint['base_url']}/audio/transcriptions",
            headers=endpoint["headers"],
            data={"model": model, **({"language": settings["stt_language"]} if settings.get("stt_language") else {})},
            files={"file": ("speech.wav", audio, "audio/wav")},
        )
    if response.status_code >= 400:
        raise RuntimeError(f"Speech endpoint HTTP {response.status_code}")
    return str(response.json().get("text") or "").strip()


def _synthesize_local(text: str, settings: dict, data_root) -> bytes:
    try:
        import kokoro  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Kokoro is not installed. Re-run the SOL-Lite installer.") from exc
    apply_hf_home(data_root)
    voice = str(settings.get("tts_voice") or DEFAULT_VOICE)
    pipeline = _kokoro_pipeline(voice[:1] or "a", str(Path(data_root).resolve()))
    chunks = []
    for _graphemes, _phonemes, audio in pipeline(text, voice=voice, speed=_speed(settings.get("tts_speed"))):
        chunks.append(audio)
    if not chunks:
        raise RuntimeError("Kokoro returned no audio")
    return _wav_bytes(chunks)


def _synthesize_platform(text: str) -> bytes:
    """Speak with Windows SAPI, macOS say, or espeak-ng when Kokoro is unavailable."""
    import shutil
    import subprocess
    import sys

    with tempfile.TemporaryDirectory() as directory:
        suffix = ".aiff" if sys.platform == "darwin" else ".wav"
        path = Path(directory) / f"speech{suffix}"
        if sys.platform == "win32":
            _sapi_to_file(text, path)
        elif sys.platform == "darwin":
            subprocess.run(["say", "-o", str(path), text], check=False, timeout=30, capture_output=True)
        else:
            espeak = shutil.which("espeak-ng") or shutil.which("espeak")
            if not espeak:
                raise RuntimeError("Text-to-speech is not available. Run sol-lite voice-status.")
            subprocess.run([espeak, "-w", str(path), text], check=False, timeout=30, capture_output=True)
        if not path.is_file() or path.stat().st_size <= 44:
            raise RuntimeError("The operating system voice returned no audio")
        return path.read_bytes()


def _sapi_to_file(text: str, path: Path) -> None:
    import os
    import subprocess

    env = os.environ.copy()
    env["SOL_LITE_SPEECH_WAV"] = str(path)
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$synth.SetOutputToWaveFile($env:SOL_LITE_SPEECH_WAV); "
        "$text = [Console]::In.ReadToEnd(); "
        "if ($text) { $synth.Speak($text) }; "
        "$synth.Dispose()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        input=text,
        text=True,
        capture_output=True,
        env=env,
        timeout=30,
        check=False,
    )


def _wav_bytes(chunks) -> bytes:
    import numpy as np
    import soundfile as sf

    audio = np.concatenate(list(chunks))
    buffer = io.BytesIO()
    sf.write(buffer, audio, 24000, format="WAV")
    return buffer.getvalue()


def _synthesize_endpoint(text: str, settings: dict, provider: str) -> bytes:
    import httpx

    endpoint = _endpoint(settings, provider)
    payload = {
        "model": str(endpoint["spec"].get("tts_model") or "tts-1"),
        "input": text,
        "voice": str(settings.get("tts_voice") if settings.get("tts_voice") != DEFAULT_VOICE
                     else endpoint["spec"].get("tts_voice") or "alloy"),
        "response_format": "wav",
        "speed": _speed(settings.get("tts_speed")),
    }
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{endpoint['base_url']}/audio/speech",
            headers={**endpoint["headers"], "Content-Type": "application/json"},
            json=payload,
        )
    if response.status_code >= 400:
        raise RuntimeError(f"Speech endpoint HTTP {response.status_code}")
    return response.content


@lru_cache(maxsize=2)
def _whisper_model(model_name, device, compute_type, download_root):
    from faster_whisper import WhisperModel
    return WhisperModel(model_name, device=device, compute_type=compute_type,
                        download_root=download_root)


@lru_cache(maxsize=2)
def _kokoro_pipeline(language, data_root):
    from kokoro import KPipeline
    apply_hf_home(data_root)
    return KPipeline(lang_code=language)

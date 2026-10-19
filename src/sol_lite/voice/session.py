"""Microphone capture and spoken replies for the terminal shell."""
from __future__ import annotations

import io
import sys
from collections import deque

from .engines import synthesize, transcribe
from .settings import ensure_voice_settings


def listen(data_root, *, recorder=None, transcriber=None) -> str:
    settings = ensure_voice_settings(data_root)
    if not settings.get("listen", False):
        raise RuntimeError("Listening is off. Use /listen on.")
    if not settings.get("stt_enabled"):
        raise RuntimeError("Speech-to-text is disabled. Run the SOL-Lite installer or sol-lite voice-status.")
    audio = (recorder or record_microphone)()
    if not audio:
        return ""
    if transcriber is not None:
        return str(transcriber(audio, settings, data_root) or "").strip()
    return transcribe(audio, settings, data_root)


def speak_reply(data_root, text: str, *, agent_id=None, player=None, synthesizer=None) -> None:
    settings = ensure_voice_settings(data_root)
    if not settings.get("speak") or not settings.get("tts_enabled"):
        return
    settings = dict(settings)
    voices = settings.get("agent_voices") or {}
    if agent_id and isinstance(voices, dict) and voices.get(agent_id):
        settings["tts_voice"] = voices[agent_id]
    audio = (synthesizer or synthesize)(text, settings, data_root)
    if not audio:
        return
    (player or play_audio)(audio)


def record_microphone(max_seconds: float = 20, silence_seconds: float = 1.2, sample_rate: int = 16000) -> bytes:
    import numpy as np
    import sounddevice as sd
    import soundfile as sf

    print("Listening... press Enter to stop.")
    block = int(sample_rate * 0.1)
    frames = []
    preroll = deque(maxlen=3)
    silent = 0
    started = False
    needed = max(1, int(silence_seconds / 0.1))
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32", blocksize=block) as stream:
        for _ in range(max(1, int(max_seconds / 0.1))):
            if _enter_pressed():
                break
            data, overflow = stream.read(block)
            if overflow:
                raise RuntimeError("Microphone overflow; try another input device.")
            rms = float(np.sqrt(np.mean(np.square(data))))
            if rms > 0.015:
                if not started:
                    frames.extend(preroll)
                started = True
                silent = 0
                frames.append(data.copy())
            elif started:
                frames.append(data.copy())
                silent += 1
                if silent >= needed:
                    break
            else:
                preroll.append(data.copy())
    if not frames:
        return b""
    buffer = io.BytesIO()
    sf.write(buffer, np.concatenate(frames), sample_rate, format="WAV")
    return buffer.getvalue()


def _enter_pressed() -> bool:
    """Poll without leaving a thread blocked on the shell's next input."""
    if not sys.stdin.isatty():
        return False
    if sys.platform == "win32":
        import msvcrt
        return msvcrt.kbhit() and msvcrt.getwch() in {"\r", "\n"}
    import select
    if select.select([sys.stdin], [], [], 0)[0]:
        sys.stdin.readline()
        return True
    return False


def play_audio(audio: bytes) -> None:
    import sounddevice as sd
    import soundfile as sf

    data, rate = sf.read(io.BytesIO(audio))
    sd.play(data, rate)
    sd.wait()

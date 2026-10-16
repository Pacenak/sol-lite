"""Microphone capture and spoken replies for the terminal shell."""
from __future__ import annotations

import io
import threading

from .engines import synthesize, transcribe
from .settings import ensure_voice_settings, load_settings


def listen(data_root, *, recorder=None, transcriber=None) -> str:
    settings = load_settings(data_root)
    if not settings.get("stt_enabled"):
        raise RuntimeError("Speech-to-text is disabled. Run the SOL-Lite installer or sol-lite voice-status.")
    audio = (recorder or record_microphone)()
    if not audio:
        return ""
    if transcriber is not None:
        return str(transcriber(audio, settings, data_root) or "").strip()
    return transcribe(audio, settings, data_root)


def speak_reply(data_root, text: str, *, player=None, synthesizer=None) -> None:
    settings = ensure_voice_settings(data_root)
    if not settings.get("speak") or not settings.get("tts_enabled"):
        return
    audio = (synthesizer or synthesize)(text, settings, data_root)
    if not audio:
        return
    (player or play_audio)(audio)


def record_microphone(max_seconds: float = 20, silence_seconds: float = 1.2, sample_rate: int = 16000) -> bytes:
    import numpy as np
    import sounddevice as sd
    import soundfile as sf

    print("Listening... press Enter to stop.")
    stop = threading.Event()

    def wait_for_enter():
        try:
            input()
        except EOFError:
            pass
        stop.set()

    threading.Thread(target=wait_for_enter, daemon=True).start()
    block = int(sample_rate * 0.1)
    frames = []
    silent = 0
    started = False
    needed = max(1, int(silence_seconds / 0.1))
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32", blocksize=block) as stream:
        for _ in range(max(1, int(max_seconds / 0.1))):
            if stop.is_set() and started:
                break
            data, _overflow = stream.read(block)
            rms = float(np.sqrt(np.mean(np.square(data))))
            if rms > 0.015:
                started = True
                silent = 0
                frames.append(data.copy())
            elif started:
                frames.append(data.copy())
                silent += 1
                if silent >= needed or stop.is_set():
                    break
    if not frames:
        return b""
    buffer = io.BytesIO()
    sf.write(buffer, np.concatenate(frames), sample_rate, format="WAV")
    return buffer.getvalue()


def play_audio(audio: bytes) -> None:
    import sounddevice as sd
    import soundfile as sf

    data, rate = sf.read(io.BytesIO(audio))
    sd.play(data, rate)
    sd.wait()

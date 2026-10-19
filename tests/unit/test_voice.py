"""Voice probe, transcript handoff, and installer provisioning."""
import importlib.util
import json
from pathlib import Path

from sol_lite.voice import probe
from sol_lite.voice.probe import probe_voice, readiness
from sol_lite.voice.session import listen
from sol_lite.voice.settings import save_settings, settings_from_probe


def test_espeak_off_path_is_discovered(tmp_path, monkeypatch):
    import os

    name = "espeak-ng.exe" if probe.sys.platform == "win32" else "espeak-ng"
    binary = tmp_path / name
    binary.write_bytes(b"")
    original = os.environ.get("PATH", "")
    monkeypatch.setattr(probe, "_known_espeak_dirs", lambda: [tmp_path])
    monkeypatch.setattr(probe.shutil, "which", lambda name: None)
    try:
        found = probe.ensure_espeak_on_path()
        assert Path(found) == binary
        assert str(tmp_path) in os.environ["PATH"]
    finally:
        os.environ["PATH"] = original


def test_kokoro_missing_on_python_313_names_the_limit(monkeypatch):
    monkeypatch.setattr(probe.sys, "version_info", (3, 13, 5))
    report = readiness({"kokoro_import": False, "espeak_ok": True, "weights_on_disk": False})
    assert report["tts"] == "degraded"
    assert "3.10-3.12" in report["tts_detail"]
    assert "3.13" in report["tts_detail"]


def test_kokoro_missing_on_python_312_stays_generic(monkeypatch):
    monkeypatch.setattr(probe.sys, "version_info", (3, 12, 0))
    report = readiness({"kokoro_import": False, "espeak_ok": False, "weights_on_disk": False})
    assert report["tts_detail"] == "kokoro is not installed"


def test_missing_espeak_degrades_tts_without_raising(monkeypatch):
    monkeypatch.setattr(probe, "_can_import", lambda name: name in {"kokoro", "faster_whisper"})
    monkeypatch.setattr(probe, "ensure_espeak_on_path", lambda: "")
    monkeypatch.setattr(probe, "_platform_speech_available", lambda: False)
    report = readiness(probe_voice())
    assert report["tts"] == "degraded"
    assert "espeak-ng" in report["tts_detail"]


def test_probe_selects_local_engines_when_they_import():
    settings = settings_from_probe({
        "faster_whisper_import": True,
        "kokoro_import": True,
        "espeak_ok": True,
    })
    assert settings["stt_provider"] == "local"
    assert settings["tts_provider"] == "local"
    assert settings["stt_enabled"] is True
    assert settings["tts_enabled"] is True
    assert settings["listen"] is False
    assert settings["speak"] is False


def test_platform_discovery_keeps_voice_switches_off():
    settings = settings_from_probe({"platform_speech": True})
    assert settings["tts_provider"] == "platform"
    assert settings["listen"] is False
    assert settings["speak"] is False


def test_terminal_launch_resets_saved_switches_before_banner(tmp_path):
    import pytest

    from sol_lite.agents.shell import AgentShell
    from sol_lite.voice.settings import load_settings

    settings = settings_from_probe({"platform_speech": True})
    settings.update(listen=True, speak=True, stt_model="medium", tts_voice="am_adam")
    save_settings(tmp_path / "data", settings)
    shell = object.__new__(AgentShell)
    shell.root = tmp_path

    class BannerReached(Exception):
        pass

    def banner():
        current = load_settings(tmp_path / "data")
        assert current == {**settings, "listen": False, "speak": False}
        raise BannerReached

    shell.print_banner = banner
    with pytest.raises(BannerReached):
        shell.run()


def test_python_313_uses_the_operating_system_voice_when_kokoro_is_missing(monkeypatch):
    monkeypatch.setattr(probe.sys, "version_info", (3, 13, 5))
    report = readiness({
        "kokoro_import": False,
        "espeak_ok": False,
        "weights_on_disk": False,
        "platform_speech": True,
    })
    assert report["tts"] == "ready"
    assert "operating system voice" in report["tts_detail"]


def test_saved_disabled_voice_preserves_speak_off_when_the_operating_system_can(tmp_path, monkeypatch):
    from sol_lite.voice.session import speak_reply
    from sol_lite.voice.settings import default_settings

    save_settings(tmp_path, default_settings())
    monkeypatch.setattr(
        "sol_lite.voice.probe.probe_voice",
        lambda data_root=None: {
            "faster_whisper_import": True,
            "kokoro_import": False,
            "espeak_ok": False,
            "platform_speech": True,
            "weights_on_disk": True,
        },
    )
    played = {}
    speak_reply(
        tmp_path,
        "The sprint starts at nine.",
        player=lambda audio: played.setdefault("audio", audio),
        synthesizer=lambda text, settings, root: b"RIFFvoice",
    )
    assert played == {}


def test_windows_platform_voice_returns_a_wav(monkeypatch):
    import sys

    pytest = __import__("pytest")
    if sys.platform != "win32":
        pytest.skip("Windows speech")
    from sol_lite.voice.engines import synthesize

    audio = synthesize("hello", {"tts_provider": "platform"}, Path("."))
    assert audio[:4] == b"RIFF"
    assert len(audio) > 44


def test_listen_returns_the_transcribed_text(tmp_path):
    settings = settings_from_probe({
        "faster_whisper_import": True,
        "kokoro_import": False,
        "espeak_ok": False,
    })
    settings["listen"] = True
    save_settings(tmp_path, settings)
    heard = listen(
        tmp_path,
        recorder=lambda: b"RIFFaudio",
        transcriber=lambda audio, settings, root: "plan the sprint",
    )
    assert heard == "plan the sprint"


def test_install_requests_voice_extra_and_keeps_prefetch_errors(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[2] / "install" / "common" / "install.py"
    spec = importlib.util.spec_from_file_location("sol_lite_install", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    commands = []
    monkeypatch.setattr(module, "run", lambda command, root: commands.append(list(command)))
    monkeypatch.setattr(module, "ensure_venv", lambda root: root / "python")
    monkeypatch.setattr(
        module, "prepare_voice",
        lambda python_path, root: {"prefetch_errors": ["network down"], "exit_code": 0},
    )
    module.install(tmp_path, repair=False)
    assert any(".[dev,voice]" in " ".join(command) for command in commands)
    state = json.loads((tmp_path / "data" / "state" / "install.json").read_text(encoding="utf-8"))
    assert state["voice"]["prefetch_errors"] == ["network down"]
    assert state["application"] == "SOL-Lite"


def test_switches_stay_off_after_discovery(tmp_path, monkeypatch):
    from sol_lite.voice.settings import ensure_voice_settings, set_switch
    monkeypatch.setattr(probe, "probe_voice", lambda root: {
        "faster_whisper_import": True, "platform_speech": True})
    set_switch(tmp_path, "listen", False)
    set_switch(tmp_path, "speak", False)
    settings = ensure_voice_settings(tmp_path)
    assert settings["listen"] is False
    assert settings["speak"] is False
    called = []
    import pytest
    with pytest.raises(RuntimeError, match="Listening is off"):
        listen(tmp_path, recorder=lambda: called.append(True))
    assert called == []


def test_agent_voice_is_passed_to_synthesizer(tmp_path, monkeypatch):
    from sol_lite.voice.session import speak_reply
    settings = settings_from_probe({"platform_speech": True})
    settings["speak"] = True
    settings["agent_voices"] = {"sol_pa": "am_adam"}
    save_settings(tmp_path, settings)
    monkeypatch.setattr(probe, "probe_voice", lambda root: {})
    seen = []
    speak_reply(tmp_path, "hello", agent_id="sol_pa", player=lambda audio: None,
                synthesizer=lambda text, config, root: seen.append(config["tts_voice"]) or b"wav")
    assert seen == ["am_adam"]


def test_hosted_speech_requests_playable_wav(monkeypatch):
    import httpx

    from sol_lite.voice.engines import synthesize
    requests = []
    class Client:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, **kwargs):
            requests.append(kwargs["json"])
            return httpx.Response(200, content=b"RIFFwave")
    monkeypatch.setattr(httpx, "Client", Client)
    settings = {"tts_provider": "endpoint:test", "tts_voice": "af_bella",
                "endpoints": {"test": {"base_url": "https://example.test/v1"}}}
    assert synthesize("hello", settings, Path(".")) == b"RIFFwave"
    assert requests[0]["response_format"] == "wav"
    assert requests[0]["voice"] == "alloy"


def test_local_recognition_uses_vad_and_language(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace

    from sol_lite.voice import engines
    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False)))
    seen = {}
    class Model:
        def transcribe(self, path, **kwargs):
            seen.update(kwargs)
            return [SimpleNamespace(text=" hello Sol ")], None
    monkeypatch.setattr(engines, "_whisper_model", lambda *args: Model())
    assert engines.transcribe(b"wav", {"stt_provider": "local", "stt_language": "en"}, tmp_path) == "hello Sol"
    assert seen["vad_filter"] is True
    assert seen["language"] == "en"
    assert seen["condition_on_previous_text"] is False


def test_voice_commands_persist_switches_and_settings(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace

    from sol_lite.agents.shell import AgentShell
    from sol_lite.voice.settings import load_settings
    monkeypatch.setattr(probe, "probe_voice", lambda root: {
        "faster_whisper_import": True, "platform_speech": True})
    shell = AgentShell.__new__(AgentShell)
    shell.root = tmp_path
    shell.agents = SimpleNamespace(names=lambda: ["sol_pa"])
    for command in ["/voice off", "/listen on", "/speak on", "/voice model small",
                    "/voice language en", "/voice agent sol_pa am_adam"]:
        assert shell.handle_command(command) == "handled"
    settings = load_settings(tmp_path / "data")
    assert settings["speak"] and settings["listen"]
    assert settings["stt_language"] == "en"
    assert settings["agent_voices"]["sol_pa"] == "am_adam"
    assert shell.handle_command("/voice speed nan") == "handled"
    assert "between 0.25 and 4" in capsys.readouterr().out


def test_microphone_enter_stops_before_speech(monkeypatch):
    import sys
    from types import SimpleNamespace

    from sol_lite.voice import session
    class Stream:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, block):
            raise AssertionError("Enter must stop recording even before speech")
    monkeypatch.setitem(sys.modules, "sounddevice", SimpleNamespace(InputStream=Stream))
    monkeypatch.setattr(session, "_enter_pressed", lambda: True)
    assert session.record_microphone() == b""


def test_microphone_preserves_onset_and_stops_at_silence(monkeypatch):
    import io
    import sys
    from types import SimpleNamespace

    import numpy as np
    import soundfile as sf

    from sol_lite.voice import session
    levels = iter([0.001, 0.002, 0.1, 0, 0])
    class Stream:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, block):
            return np.full((block, 1), next(levels), dtype="float32"), False
    monkeypatch.setitem(sys.modules, "sounddevice", SimpleNamespace(InputStream=Stream))
    monkeypatch.setattr(session, "_enter_pressed", lambda: False)
    audio = session.record_microphone(silence_seconds=0.2)
    data, rate = sf.read(io.BytesIO(audio))
    assert rate == 16000
    assert len(data) == 5 * 1600
    assert 0 < data[0] < 0.01

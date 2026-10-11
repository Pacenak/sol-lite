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


def test_listen_returns_the_transcribed_text(tmp_path):
    save_settings(tmp_path, settings_from_probe({
        "faster_whisper_import": True,
        "kokoro_import": False,
        "espeak_ok": False,
    }))
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

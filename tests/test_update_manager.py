from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from hermes_ui import update_manager


class _Response:
    def __init__(self, version: str):
        self.version = version

    def raise_for_status(self):
        return None

    def json(self):
        return {"version": self.version}


def test_check_version_reports_an_available_registry_release():
    status = update_manager.check_version("0.3.96", get=lambda *args, **kwargs: _Response("0.3.97"))

    assert status.current_version == "0.3.96"
    assert status.latest_version == "0.3.97"
    assert status.update_available is True


def test_update_uses_npx_install_without_passing_settings_or_secrets():
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0)

    result = update_manager.update_to_latest(
        "0.3.96",
        get=lambda *args, **kwargs: _Response("0.3.97"),
        run=fake_run,
    )

    assert result.ok is True
    assert result.latest_version == "0.3.97"
    assert result.restart_required is True
    assert captured["command"][-2:] == ["@danhachuel/thunderbolt", "install"]
    assert "settings" not in " ".join(captured["command"]).lower()
    assert captured["kwargs"]["stdout"] is update_manager.subprocess.DEVNULL
    assert captured["kwargs"]["stderr"] is update_manager.subprocess.DEVNULL


def test_restart_current_process_reexecutes_the_same_python_command(monkeypatch):
    calls = []
    monkeypatch.setattr(update_manager.sys, "executable", "/python")
    monkeypatch.setattr(update_manager.sys, "argv", ["-m", "streamlit", "run", "app/main.py"])

    update_manager.restart_current_process(exec_fn=lambda executable, argv: calls.append((executable, argv)))

    assert calls == [("/python", ["/python", "-m", "streamlit", "run", "app/main.py"])]


def test_update_does_not_run_when_the_package_is_already_current():
    result = update_manager.update_to_latest(
        "0.3.97",
        get=lambda *args, **kwargs: _Response("0.3.97"),
        run=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("não deve instalar")),
    )

    assert result.ok is True
    assert "já está" in result.message


def test_home_is_the_only_page_that_renders_the_update_button():
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    home_controls = source.split("def render_home_update_controls() -> None:", 1)[1].split("def render_dashboard():", 1)[0]
    dashboard = source.split("def render_dashboard():", 1)[1].split("def render_blueprints():", 1)[0]

    assert 'key="home_update_version"' in home_controls
    assert source.count('key="home_update_version"') == 1
    assert 'button[kind="primary"]' in home_controls
    assert 'if current_page == "Início":\n        render_home_update_controls()' in source
    assert 'restart_current_process()' in home_controls
    assert 'update_result.ok and update_result.restart_required' in home_controls
    assert 'key="home_update_version"' not in dashboard


def test_home_update_notice_has_a_close_button_and_constrained_width():
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    home_controls = source.split("def render_home_update_controls() -> None:", 1)[1].split("def render_dashboard():", 1)[0]

    assert 'st.columns([1.45, 2.55, 3.0])' in home_controls
    assert 'st.columns([8.5, 1])' in home_controls
    assert 'key="home_update_notice_close"' in home_controls
    assert 'home_update_notice_dismissed' in home_controls
    assert 'help="Fechar este aviso"' in home_controls


def test_version_label_keeps_the_two_digit_patch_convention():
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")

    assert "def display_version(version: str)" in source
    assert 'f"{int(parts[0])}.{int(parts[1])}.{int(parts[2]):02d}"' in source
    assert "APP_VERSION_LABEL = display_version(APP_VERSION)" in source

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
    assert captured["command"][-2:] == ["@danhachuel/thunderbolt", "install"]
    assert "settings" not in " ".join(captured["command"]).lower()
    assert captured["kwargs"]["stdout"] is update_manager.subprocess.DEVNULL
    assert captured["kwargs"]["stderr"] is update_manager.subprocess.DEVNULL


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
    dashboard = source.split("def render_dashboard():", 1)[1].split("def render_blueprints():", 1)[0]

    assert 'key="home_update_version"' in dashboard
    assert source.count('key="home_update_version"') == 1
    assert 'button[kind="primary"]' in dashboard


def test_version_label_keeps_the_two_digit_patch_convention():
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")

    assert "def display_version(version: str)" in source
    assert 'f"{int(parts[0])}.{int(parts[1])}.{int(parts[2]):02d}"' in source
    assert "APP_VERSION_LABEL = display_version(APP_VERSION)" in source

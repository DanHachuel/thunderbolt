from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from integrations.session_info_health import health_check_session_info
from integrations.youtube_session_manager import (
    account_lock,
    atomic_save_credentials,
    is_yt_cm_available,
    validate_session_info,
)


def test_validate_session_info_requires_base64_like_long_value():
    assert validate_session_info("A" * 50)
    assert not validate_session_info("")
    assert not validate_session_info("A" * 49)
    assert not validate_session_info("A" * 49 + "!")


def test_yt_cm_availability_is_boolean():
    assert isinstance(is_yt_cm_available(), bool)


def test_account_lock_writes_pid_timestamp_and_cleans_up(tmp_path):
    account_dir = tmp_path / "account"
    with account_lock(account_dir, "google-1"):
        lock = account_dir / "google-1.lock"
        payload = json.loads(lock.read_text(encoding="utf-8"))
        assert payload["pid"] > 0
        assert payload["timeout_seconds"] == 300
    assert not (account_dir / "google-1.lock").exists()


def test_orphan_lock_is_replaced(tmp_path):
    account_dir = tmp_path / "account"
    account_dir.mkdir()
    lock = account_dir / "google-1.lock"
    lock.write_text(json.dumps({"pid": 99999999, "acquired_at": datetime.now(timezone.utc).isoformat(), "timeout_seconds": 300}), encoding="utf-8")
    with account_lock(account_dir, "google-1"):
        assert json.loads(lock.read_text(encoding="utf-8"))["pid"] > 0


def test_atomic_save_rotates_three_backups(tmp_path):
    destination = tmp_path / "credentials.json"
    atomic_save_credentials(destination, {"version": 1})
    atomic_save_credentials(destination, {"version": 2})
    atomic_save_credentials(destination, {"version": 3})
    atomic_save_credentials(destination, {"version": 4})
    assert json.loads(destination.read_text(encoding="utf-8"))["version"] == 4
    assert json.loads((tmp_path / "credentials.json.bak").read_text(encoding="utf-8"))["version"] == 3
    assert json.loads((tmp_path / "credentials.json.bak1").read_text(encoding="utf-8"))["version"] == 2
    assert json.loads((tmp_path / "credentials.json.bak2").read_text(encoding="utf-8"))["version"] == 1


def test_health_uses_expires_at_and_new_states():
    now = datetime(2026, 9, 4, 12, tzinfo=timezone.utc)
    account = {"id": "google-1", "label": "Conta"}
    captured = (now - timedelta(hours=1)).isoformat()
    assert health_check_session_info(account, {"sessionInfo": "x", "sessionInfoCapturedAt": captured, "expires_at": (now + timedelta(hours=7)).isoformat()}, now=now).status == "healthy"
    assert health_check_session_info(account, {"sessionInfo": "x", "sessionInfoCapturedAt": captured, "expires_at": (now + timedelta(hours=5)).isoformat()}, now=now).status == "expiring"
    assert health_check_session_info(account, {"sessionInfo": "x", "sessionInfoHealthStatus": "blocked_by_google", "sessionInfoCapturedAt": captured}, now=now).status == "blocked_by_google"
    assert health_check_session_info(account, {"sessionInfo": "x", "sessionInfoHealthStatus": "invalid_format", "sessionInfoCapturedAt": captured}, now=now).status == "invalid_format"

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from hermes_ui import domain, storage
from hermes_ui.pipeline_worker import _cascade_metadata
from integrations.session_info_health import (
    check_account_session_info_health,
    emit_session_info_health_alerts,
    health_check_session_info,
)
from integrations.youtube_direct_credentials import load_credentials_document, update_credentials_document_session_info


def _isolate_storage(tmp_path, monkeypatch):
    root = tmp_path / "storage"
    monkeypatch.setattr(storage, "STORAGE", root)
    monkeypatch.setattr(storage, "STATE", root / "state")
    monkeypatch.setattr(storage, "BLUEPRINTS", root / "blueprints")
    monkeypatch.setattr(storage, "TIKTOK_PROMPT_MASTERS", root / "tiktok" / "prompts_master")
    monkeypatch.setattr(storage, "MEDIA_DOWNLOADS", root / "downloads")
    storage.ensure_storage()
    return root


def test_atomic_write_keeps_previous_json_when_serialisation_fails(tmp_path):
    destination = tmp_path / "state.json"
    storage.atomic_write(destination, {"version": 1})
    try:
        storage.atomic_write(destination, {"bad": object()})
    except TypeError:
        pass
    assert destination.read_text(encoding="utf-8").strip().startswith("{")
    assert '"version": 1' in destination.read_text(encoding="utf-8")
    assert not list(tmp_path.glob(".state.json.*"))


def test_session_info_health_states_are_bounded_and_secret_free():
    now = datetime(2026, 8, 27, 12, tzinfo=timezone.utc)
    account = {"id": "google-1", "label": "Conta principal"}
    healthy = health_check_session_info(account, {"sessionInfo": "secret-token", "sessionInfoCapturedAt": (now - timedelta(hours=10)).isoformat()}, now=now, ttl_hours=48, alert_hours=6)
    expiring = health_check_session_info(account, {"sessionInfo": "secret-token", "sessionInfoCapturedAt": (now - timedelta(hours=43)).isoformat()}, now=now, ttl_hours=48, alert_hours=6)
    expired = health_check_session_info(account, {"sessionInfo": "secret-token", "sessionInfoCapturedAt": (now - timedelta(hours=49)).isoformat()}, now=now, ttl_hours=48, alert_hours=6)
    unknown = health_check_session_info(account, {"sessionInfo": "secret-token"}, now=now)
    assert healthy.status == "healthy"
    assert expiring.status == "expiring"
    assert expired.status == "expired"
    assert unknown.status == "unknown"
    assert "secret-token" not in str(healthy.as_dict())
    assert health_check_session_info(account, {"sessionInfo": "x", "sessionInfoCapturedAt": now.isoformat()}, now=now, ttl_hours=1).status == "healthy"
    assert health_check_session_info(account, {"sessionInfo": "x", "sessionInfoCapturedAt": (now - timedelta(hours=20)).isoformat()}, now=now, ttl_hours=1).status == "expiring"


def test_first_manual_session_info_save_records_capture_timestamp(tmp_path):
    account = {"id": "google-1", "email": "user@example.com"}
    path = update_credentials_document_session_info(tmp_path, account, "session-token")
    document = load_credentials_document(tmp_path, account, create=False)
    assert path is not None and path.exists()
    assert document["sessionInfo"] == "session-token"
    assert document["sessionInfoCapturedAt"]


def test_session_info_alert_is_deduplicated_and_redacted(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    now = datetime(2026, 8, 27, 12, tzinfo=timezone.utc)
    item = health_check_session_info(
        {"id": "google-1", "label": "Conta principal"},
        {"sessionInfo": "secret-token", "sessionInfoCapturedAt": (now - timedelta(hours=50)).isoformat()},
        now=now,
        ttl_hours=48,
    )
    first = emit_session_info_health_alerts([item], now=now)
    second = emit_session_info_health_alerts([item], now=now)
    entries = storage.read_json("notifications.json", [])
    assert len(first) == 1
    assert second == []
    assert len(entries) == 1
    assert "secret-token" not in str(entries[0])
    assert entries[0]["event_type"] == "session_info_expired"


def test_session_info_account_health_reads_persisted_document(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    account = {"id": "google-1", "email": "user@example.com"}
    update_credentials_document_session_info(tmp_path, account, "session-token")
    settings = {"youtube_batch_accounts": [account], "session_info_ttl_hours": 36, "session_info_alert_hours": 6}
    health = check_account_session_info_health(tmp_path, account, settings)
    assert health.status in {"healthy", "expiring"}
    assert health.account_id == "google-1"


def test_new_tasks_persist_cascade_contract(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    storage.write_json("channels.json", [{"id": "channel-1", "name": "Canal", "language": "pt-BR"}])
    batch = domain.create_batch("single", ["channel-1"], "Tema", 1, {})
    tasks = domain.create_tasks_for_batch(batch)
    orchestration = tasks[0]["orchestration"]
    assert orchestration["name"] == "local-cascade"
    assert orchestration["resumable"] is True
    assert orchestration["stage_order"][-1] == "upload"


def test_cascade_metadata_marks_completed_stages_without_secrets():
    current = {"stage": "video", "orchestration": {"completed_stages": ["topic", "script"], "transition_count": 2}}
    updated = _cascade_metadata(current, {"stage": "thumbnail_prompt", "state": "doing"})
    assert updated["current_stage"] == "thumbnail_prompt"
    assert updated["completed_stages"] == ["topic", "script", "video"]
    assert updated["transition_count"] == 3
    assert "token" not in str(updated).lower()


def test_internal_api_documentation_and_diagrams_exist():
    root = Path(__file__).resolve().parents[1]
    documentation = (root / "docs" / "api-internal.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "atomic_write" in documentation
    assert "SessionInfo" in documentation
    assert "local-cascade" in documentation
    assert "docs/api-internal.md" in readme
    assert all((root / "docs" / "diagrams" / name).is_file() for name in ("pipeline-cascade.mmd", "session-info-health.mmd", "atomic-json.mmd"))

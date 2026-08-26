from pathlib import Path


def _isolated_storage(tmp_path):
    from hermes_ui import storage

    storage.STORAGE = tmp_path / "storage"
    storage.STATE = storage.STORAGE / "state"
    storage.BLUEPRINTS = storage.STORAGE / "blueprints"
    storage.TIKTOK_PROMPT_MASTERS = storage.STORAGE / "tiktok" / "prompts_master"
    storage.ensure_storage()
    return storage


def test_list_logs_projects_tasks_and_notifications_with_required_fields(tmp_path):
    storage = _isolated_storage(tmp_path / "projection")
    from hermes_ui.logs import list_logs, logs_to_rows
    from hermes_ui.notifications import record_notification

    storage.write_json("tasks.json", [
        {
            "id": "video-pending",
            "state": "to_do",
            "stage": "script",
            "title": "Vídeo pendente",
            "channel_name": "Canal de teste",
            "progress": 0,
            "created_at": "2026-08-26T10:00:00+00:00",
            "updated_at": "2026-08-26T10:01:00+00:00",
        },
        {
            "id": "video-running",
            "state": "doing",
            "stage": "video",
            "title": "Vídeo em execução",
            "channel_name": "Canal de teste",
            "progress": 72,
            "created_at": "2026-08-26T10:00:00+00:00",
            "updated_at": "2026-08-26T10:02:00+00:00",
        },
        {
            "id": "video-failed",
            "state": "failed",
            "stage": "video",
            "title": "Vídeo com falha",
            "channel_name": "Canal de teste",
            "error": "Timeout do Motor",
            "created_at": "2026-08-26T10:00:00+00:00",
            "updated_at": "2026-08-26T10:03:00+00:00",
        },
    ])
    record_notification("music_completed", "Música guardada", "Faixa pronta", dedupe_key="music:one")

    records = list_logs(limit=50)
    assert {"operation", "status", "date", "time"} <= set(records[0])
    assert {item["status"] for item in records} >= {"Pendente", "Em execução", "Falha", "Concluído"}
    running = next(item for item in records if item["task_id"] == "video-running")
    assert running["operation"] == "Vídeo concluído"
    assert running["progress"] == 72
    assert "Canal de teste" in running["details"]
    failed = next(item for item in records if item["task_id"] == "video-failed")
    assert "Timeout do Motor" in failed["details"]

    rows = logs_to_rows(records)
    assert {"Operação", "Estado", "Data", "Hora"} <= set(rows[0])
    assert all(row["Data"] != "—" and row["Hora"] != "—" for row in rows)


def test_log_filters_match_operation_status_and_free_text(tmp_path):
    storage = _isolated_storage(tmp_path / "filters")
    from hermes_ui.logs import list_logs

    storage.write_json("tasks.json", [
        {
            "id": "music-running",
            "state": "doing",
            "style_wide": "music",
            "title": "Faixa em execução",
            "channel_name": "Canal musical",
            "updated_at": "2026-08-26T10:00:00+00:00",
        },
        {
            "id": "video-done",
            "state": "done",
            "title": "Vídeo pronto",
            "channel_name": "Canal de vídeo",
            "updated_at": "2026-08-26T10:01:00+00:00",
        },
    ])

    assert [item["task_id"] for item in list_logs(operation="Música concluída")] == ["music-running"]
    assert [item["task_id"] for item in list_logs(status="Em execução")] == ["music-running"]
    assert [item["task_id"] for item in list_logs(query="Canal de vídeo")] == ["video-done"]


def test_logs_page_is_between_notifications_and_api_configuration():
    root = Path(__file__).resolve().parents[1]
    source = (root / "app" / "main.py").read_text(encoding="utf-8")
    settings_start = source.index("settings_items = [")
    settings_end = source.index("]", settings_start)
    settings_block = source[settings_start:settings_end]
    assert settings_block.index('("Notificações"') < settings_block.index('("Logs"') < settings_block.index('("Configuração API"')
    assert '"Logs": render_logs' in source
    for label in ("Filtrar operações", "Operação", "Estado", "Data", "Hora", "Registo", "Origem", "Detalhes"):
        assert label in source
    assert "list_logs(operation=operation_filter, query=query, status=status_filter, limit=500)" in source

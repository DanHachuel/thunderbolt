from __future__ import annotations

import json


def test_task_platform_uses_explicit_platform(monkeypatch, tmp_path):
    from app import main

    monkeypatch.setattr(main, "read_json", lambda name, default=None: [] if name == "channels.json" else default)
    assert main.task_platform({"platform": "tiktok", "format": "wide"}) == "tiktok"
    assert main.task_platform({"platform": "youtube", "format": "portrait"}) == "youtube"


def test_task_platform_resolves_channel_for_legacy_task(monkeypatch):
    from app import main

    channels = [{"id": "tt-1", "platform": "tiktok"}, {"id": "yt-1", "platform": "youtube"}]
    monkeypatch.setattr(main, "read_json", lambda name, default=None: channels if name == "channels.json" else default)
    assert main.task_platform({"channel_id": "tt-1"}) == "tiktok"
    assert main.task_platform({"channel_id": "yt-1"}) == "youtube"


def test_automation_loader_filters_by_platform(monkeypatch):
    from app import main

    tasks = [{"id": "tt", "platform": "tiktok"}, {"id": "yt", "platform": "youtube"}]
    monkeypatch.setattr(main, "load_video_tasks_for_catalog", lambda: tasks)
    assert [task["id"] for task in main.load_automation_tasks_for_platform("tiktok")] == ["tt"]
    assert [task["id"] for task in main.load_automation_tasks_for_platform("youtube")] == ["yt"]

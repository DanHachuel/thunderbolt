from pathlib import Path

from hermes_ui import thumbnail_blueprints


def test_generic_fallback_uses_landscape_seed_by_default(tmp_path: Path):
    original = thumbnail_blueprints.BLUEPRINTS
    thumbnail_blueprints.BLUEPRINTS = tmp_path
    try:
        folder = tmp_path / "thumbnails"
        folder.mkdir()
        (folder / "Youtube_Generic_Thumbnail_Blueprint.md").write_text("16:9", encoding="utf-8")
        (folder / "Tiktok_Generic_Thumbnail_Blueprint.md").write_text("9:16", encoding="utf-8")
        result = thumbnail_blueprints.thumbnail_blueprint_for_channel({})
        assert result["id"] == "Youtube_Generic_Thumbnail_Blueprint"
    finally:
        thumbnail_blueprints.BLUEPRINTS = original


def test_generic_fallback_uses_portrait_seed_for_vertical_video(tmp_path: Path):
    original = thumbnail_blueprints.BLUEPRINTS
    thumbnail_blueprints.BLUEPRINTS = tmp_path
    try:
        folder = tmp_path / "thumbnails"
        folder.mkdir()
        (folder / "Youtube_Generic_Thumbnail_Blueprint.md").write_text("16:9", encoding="utf-8")
        (folder / "Tiktok_Generic_Thumbnail_Blueprint.md").write_text("9:16", encoding="utf-8")
        result = thumbnail_blueprints.thumbnail_blueprint_for_channel({"platform": "tiktok"}, "portrait")
        assert result["id"] == "Tiktok_Generic_Thumbnail_Blueprint"
    finally:
        thumbnail_blueprints.BLUEPRINTS = original


def test_explicit_thumbnail_blueprint_is_preserved_for_vertical_video(tmp_path: Path):
    original = thumbnail_blueprints.BLUEPRINTS
    thumbnail_blueprints.BLUEPRINTS = tmp_path
    try:
        folder = tmp_path / "thumbnails"
        folder.mkdir()
        (folder / "My_Custom_Thumbnail_Blueprint.md").write_text("custom", encoding="utf-8")
        result = thumbnail_blueprints.thumbnail_blueprint_for_channel(
            {"thumbnail_blueprint_id": "My_Custom_Thumbnail_Blueprint"}, "portrait"
        )
        assert result["id"] == "My_Custom_Thumbnail_Blueprint"
    finally:
        thumbnail_blueprints.BLUEPRINTS = original

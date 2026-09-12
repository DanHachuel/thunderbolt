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


def test_stale_horizontal_generic_is_replaced_for_vertical_task(tmp_path: Path):
    original = thumbnail_blueprints.BLUEPRINTS
    thumbnail_blueprints.BLUEPRINTS = tmp_path
    try:
        folder = tmp_path / "thumbnails"
        folder.mkdir()
        (folder / "Youtube_Generic_Thumbnail_Blueprint.md").write_text("16:9", encoding="utf-8")
        (folder / "Tiktok_Generic_Thumbnail_Blueprint.md").write_text("9:16", encoding="utf-8")
        result = thumbnail_blueprints.thumbnail_blueprint_for_task(
            {"platform": "tiktok"},
            {"format": "portrait", "thumbnail_blueprint_id": "Youtube_Generic_Thumbnail_Blueprint"},
        )
        assert result["id"] == "Tiktok_Generic_Thumbnail_Blueprint"
    finally:
        thumbnail_blueprints.BLUEPRINTS = original


def test_one_thumbnail_can_be_associated_with_multiple_script_blueprints(tmp_path: Path):
    original = thumbnail_blueprints.BLUEPRINTS
    thumbnail_blueprints.BLUEPRINTS = tmp_path
    try:
        thumbnail_blueprints.save_thumbnail_blueprint_pairs(
            "FINANCE_Thumbnail_Blueprint", ["FINANCE BRAZIL", "FINANCE ITALY", "FINANCE UK"]
        )
        pairs = thumbnail_blueprints.thumbnail_blueprint_associations()
        assert pairs["FINANCE BRAZIL"] == "FINANCE_Thumbnail_Blueprint"
        assert pairs["FINANCE ITALY"] == "FINANCE_Thumbnail_Blueprint"
        assert pairs["FINANCE UK"] == "FINANCE_Thumbnail_Blueprint"
    finally:
        thumbnail_blueprints.BLUEPRINTS = original


def test_platform_defaults_are_landscape_for_youtube_and_portrait_for_tiktok_and_instagram():
    resolver = thumbnail_blueprints.thumbnail_aspect_ratio_for_channel_task
    assert resolver({"platform": "youtube"}, {}) == "16:9"
    assert resolver({"platform": "tiktok"}, {}) == "9:16"
    assert resolver({"platform": "instagram"}, {}) == "9:16"


def test_legacy_youtube_generic_task_does_not_inherit_vertical_orientation():
    resolver = thumbnail_blueprints.thumbnail_aspect_ratio_for_channel_task
    assert resolver(
        {"platform": "youtube", "thumbnail_blueprint_id": "Youtube_Generic_Thumbnail_Blueprint"},
        {"thumbnail_blueprint_id": "Tiktok_Generic_Thumbnail_Blueprint", "format": "portrait"},
    ) == "16:9"


def test_channel_specific_thumbnail_blueprint_remains_authoritative(tmp_path: Path):
    original = thumbnail_blueprints.BLUEPRINTS
    thumbnail_blueprints.BLUEPRINTS = tmp_path
    try:
        folder = tmp_path / "thumbnails"
        folder.mkdir()
        (folder / "Custom_Thumbnail_Blueprint.md").write_text("Use a portrait 9:16 composition", encoding="utf-8")
        assert thumbnail_blueprints.thumbnail_aspect_ratio_for_channel_task(
            {"platform": "youtube", "thumbnail_blueprint_id": "Custom_Thumbnail_Blueprint"}, {}
        ) == "9:16"
    finally:
        thumbnail_blueprints.BLUEPRINTS = original


def test_finance_blueprints_use_finance_thumbnail_and_explicit_landscape_rules():
    pairs = thumbnail_blueprints.thumbnail_blueprint_associations()
    for identifier in (
        "FINANCE USA", "FINANCE AUSTRALIA", "FINANCE BRAZIL", "FINANCE CANADA", "FINANCE FRANCE",
        "FINANCE GERMANY", "FINANCE IRELAND", "FINANCE ISRAEL", "FINANCE ITALY", "FINANCE JAPAN",
        "FINANCE MEXICO", "FINANCE POLONY", "FINANCE SOUTH AFRICA", "FINANCE SOUTH COREA",
        "FINANCE SPAIN", "FINANCE UK",
    ):
        assert pairs[identifier] == "FINANCE_Thumbnail_Blueprint"
    content = thumbnail_blueprints.resolve_thumbnail_blueprint("FINANCE_Thumbnail_Blueprint")["content"]
    assert thumbnail_blueprints._explicit_blueprint_aspect_ratio(content) == "16:9"
    assert thumbnail_blueprints.thumbnail_aspect_ratio_for_channel_task(
        {"platform": "youtube"}, {"blueprint_id": "FINANCE USA"}, {"id": "FINANCE_Thumbnail_Blueprint", "content": content}
    ) == "16:9"


def test_finance_pair_lookup_accepts_separator_variants(tmp_path: Path):
    original = thumbnail_blueprints.BLUEPRINTS
    thumbnail_blueprints.BLUEPRINTS = tmp_path
    try:
        (tmp_path / "thumbnail_blueprint_pairs.json").write_text('{"FINANCE USA": "FINANCE_Thumbnail_Blueprint"}', encoding="utf-8")
        result = thumbnail_blueprints.thumbnail_blueprint_for_channel({"blueprint_id": "finance_usa"})
        assert result["id"] == "FINANCE_Thumbnail_Blueprint"
    finally:
        thumbnail_blueprints.BLUEPRINTS = original

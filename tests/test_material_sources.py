from hermes_ui.material_sources import all_material_api_keys, material_api_keys, material_source_catalog, selected_material_source, update_material_api_keys


def test_material_sources_support_multiple_keys_and_legacy_values():
    settings = {"pexels_api_keys": "old-one, old-two", "pixabay_api_keys": ["pixel-one"]}
    assert material_api_keys(settings, "pexels") == ["old-one", "old-two"]
    assert material_api_keys(settings, "pixabay") == ["pixel-one"]
    update_material_api_keys(settings, "pexels", ["new-one", "new-one", "new-two", ""])
    assert settings["material_api_keys"]["pexels"] == ["new-one", "new-two"]
    assert settings["pexels_api_keys"] == ["new-one", "new-two"]
    assert material_api_keys(settings, "pexels") == ["new-one", "new-two"]


def test_material_sources_catalog_matches_moneyprinter_style_sources():
    codes = [item["code"] for item in material_source_catalog()]
    assert codes[:3] == ["pexels", "pixabay", "coverr"]
    assert "wavespeed" in codes
    assert "loomloom" in codes
    assert "twelvelabs" in codes
    assert selected_material_source({"video_source": "pixabay"}) == "pixabay"
    assert selected_material_source({"video_source": "unknown"}) == "pexels"
    assert set(all_material_api_keys({})) == set(codes)


def test_material_sources_reject_unknown_source():
    try:
        update_material_api_keys({}, "unknown", ["key"])
    except ValueError as exc:
        assert "inválida" in str(exc)
    else:
        raise AssertionError("Uma fonte desconhecida deveria ser rejeitada")

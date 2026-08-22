import json
import os
import tempfile
from pathlib import Path



def test_display_names_are_persisted_separately_from_library_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["THUNDERBOLT_STORAGE_DIR"] = temp_dir
        from hermes_ui import storage

        storage.ensure_storage()
        blueprint = storage.BLUEPRINTS / "importados" / "example.json"
        blueprint.write_text(json.dumps({"id": "bp-example", "name": "Original Blueprint"}), encoding="utf-8")
        prompt = storage.TIKTOK_PROMPT_MASTERS / "example.md"
        prompt.write_text("# Original Prompt\n", encoding="utf-8")

        storage.set_display_name("blueprints", blueprint, "Blueprint Renomeado")
        storage.set_display_name("prompt_masters", prompt, "Prompt Renomeado")

        assert storage.get_display_name("blueprints", blueprint, "fallback") == "Blueprint Renomeado"
        assert storage.get_display_name("prompt_masters", prompt, "fallback") == "Prompt Renomeado"
        assert blueprint.name == "example.json"
        assert prompt.name == "example.md"
        saved = json.loads((storage.STATE / "display_names.json").read_text(encoding="utf-8"))
        assert saved["blueprints"]["importados/example.json"] == "Blueprint Renomeado"
        assert saved["prompt_masters"]["example.md"] == "Prompt Renomeado"

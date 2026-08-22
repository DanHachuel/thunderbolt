from __future__ import annotations

from typing import Any


MATERIAL_SOURCE_CATALOG: tuple[dict[str, str], ...] = (
    {"code": "pexels", "label": "Pexels", "description": "Banco de vídeos e imagens para materiais da pipeline.", "legacy_key": "pexels_api_keys"},
    {"code": "pixabay", "label": "Pixabay", "description": "Banco de vídeos e imagens para materiais da pipeline.", "legacy_key": "pixabay_api_keys"},
    {"code": "coverr", "label": "Coverr", "description": "Fonte de vídeos de stock com API própria.", "legacy_key": "coverr_api_keys"},
    {"code": "wavespeed", "label": "WaveSpeed AI", "description": "Geração de clips por IA; requer um serviço configurado.", "legacy_key": "wavespeed_api_keys"},
    {"code": "loomloom", "label": "LoomLoom", "description": "Fonte paga de materiais; requer confirmação no fluxo de criação.", "legacy_key": "loomloom_api_keys"},
    {"code": "twelvelabs", "label": "TwelveLabs", "description": "Ranking e análise semântica opcional dos materiais.", "legacy_key": "twelvelabs_api_keys"},
)


def _as_key_list(value: Any) -> list[str]:
    if isinstance(value, list):
        values = value
    else:
        values = str(value or "").replace("\n", ",").split(",")
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        key = str(item or "").strip()
        if key and key not in seen:
            result.append(key)
            seen.add(key)
    return result


def material_source_catalog() -> list[dict[str, str]]:
    return [dict(item) for item in MATERIAL_SOURCE_CATALOG]


def material_api_keys(settings: dict[str, Any], source: str) -> list[str]:
    code = str(source or "").strip().lower()
    saved = settings.get("material_api_keys", {})
    if isinstance(saved, dict) and code in saved:
        return _as_key_list(saved.get(code))
    legacy_key = next((item["legacy_key"] for item in MATERIAL_SOURCE_CATALOG if item["code"] == code), f"{code}_api_keys")
    return _as_key_list(settings.get(legacy_key, ""))


def all_material_api_keys(settings: dict[str, Any]) -> dict[str, list[str]]:
    return {item["code"]: material_api_keys(settings, item["code"]) for item in MATERIAL_SOURCE_CATALOG}


def update_material_api_keys(settings: dict[str, Any], source: str, keys: list[str]) -> dict[str, Any]:
    code = str(source or "").strip().lower()
    if code not in {item["code"] for item in MATERIAL_SOURCE_CATALOG}:
        raise ValueError("Fonte de materiais inválida.")
    cleaned = _as_key_list(keys)
    mapping = all_material_api_keys(settings)
    mapping[code] = cleaned
    settings["material_api_keys"] = mapping
    source_entry = next(item for item in MATERIAL_SOURCE_CATALOG if item["code"] == code)
    settings[source_entry["legacy_key"]] = cleaned
    return settings


def selected_material_source(settings: dict[str, Any]) -> str:
    source = str(settings.get("video_source") or "pexels").strip().lower()
    valid = {item["code"] for item in MATERIAL_SOURCE_CATALOG} | {"local"}
    return source if source in valid else "pexels"

from __future__ import annotations

from typing import Any
from uuid import uuid4


MATERIAL_CARDS_KEY = "material_source_cards"
MATERIAL_ACTIVE_CARD_KEY = "material_active_card_id"
DEFAULT_MATERIAL_PRIORITY = 1

MATERIAL_SOURCE_CATALOG: tuple[dict[str, str], ...] = (
    {"code": "pexels", "label": "Pexels", "description": "Banco de vídeos e imagens para materiais da pipeline.", "legacy_key": "pexels_api_keys"},
    {"code": "pixabay", "label": "Pixabay", "description": "Banco de vídeos e imagens para materiais da pipeline.", "legacy_key": "pixabay_api_keys"},
    {"code": "coverr", "label": "Coverr", "description": "Fonte de vídeos de stock com API própria.", "legacy_key": "coverr_api_keys"},
    {"code": "wavespeed", "label": "WaveSpeed AI", "description": "Geração de clips por IA; requer um serviço configurado.", "legacy_key": "wavespeed_api_keys"},
    {"code": "loomloom", "label": "LoomLoom", "description": "Fonte paga de materiais; requer confirmação no fluxo de criação.", "legacy_key": "loomloom_api_keys"},
    {"code": "twelvelabs", "label": "TwelveLabs", "description": "Ranking e análise semântica opcional dos materiais.", "legacy_key": "twelvelabs_api_keys"},
)


_SOURCE_BY_CODE = {item["code"]: item for item in MATERIAL_SOURCE_CATALOG}


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


def material_source_definition(source: Any) -> dict[str, str] | None:
    return _SOURCE_BY_CODE.get(str(source or "").strip().lower())


def _new_card(
    provider: str,
    api_key: str = "",
    *,
    card_id: str | None = None,
    priority: int = DEFAULT_MATERIAL_PRIORITY,
) -> dict[str, Any]:
    return {
        "id": card_id or f"material-{provider}-{uuid4().hex[:8]}",
        "provider": provider,
        "api_key": str(api_key or "").strip(),
        "enabled": True,
        "priority": max(1, int(priority)),
    }


def _normalise_priority(value: Any, fallback: int = DEFAULT_MATERIAL_PRIORITY) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return max(1, int(fallback or DEFAULT_MATERIAL_PRIORITY))


def normalize_material_card(card: Any, index: int = 0) -> dict[str, Any]:
    raw = card if isinstance(card, dict) else {}
    provider = str(raw.get("provider") or raw.get("source") or "pexels").strip().lower()
    if provider not in _SOURCE_BY_CODE and provider != "local":
        provider = "pexels"
    card_id = str(raw.get("id") or f"material-{provider}-{index}").strip()
    return {
        "id": card_id or f"material-{provider}-{index}",
        "provider": provider,
        "api_key": str(raw.get("api_key") or raw.get("key") or "").strip() if provider != "local" else "",
        "enabled": bool(raw.get("enabled", True)),
        "priority": _normalise_priority(raw.get("priority", index + 1), index + 1),
    }


def _ordered_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed = [(index, normalize_material_card(card, index)) for index, card in enumerate(cards)]
    indexed.sort(key=lambda pair: (pair[1].get("priority", pair[0] + 1), pair[0]))
    return [card for _index, card in indexed]


def material_source_cards(settings: dict[str, Any], *, enabled_only: bool = False) -> list[dict[str, Any]]:
    """Return material providers in stable priority order for the MoviePy queue."""
    migrated, _ = ensure_material_source_cards(settings)
    cards = [dict(item) for item in migrated.get(MATERIAL_CARDS_KEY, [])]
    if enabled_only:
        cards = [card for card in cards if card.get("enabled", True)]
    return cards


def _cards_key_mapping(cards: list[dict[str, Any]]) -> dict[str, list[str]]:
    mapping = {item["code"]: [] for item in MATERIAL_SOURCE_CATALOG}
    for index, raw_card in enumerate(cards):
        card = normalize_material_card(raw_card, index)
        provider = card["provider"]
        api_key = str(card.get("api_key") or "").strip()
        if card.get("enabled", True) and provider in mapping and api_key and api_key not in mapping[provider]:
            mapping[provider].append(api_key)
    return mapping


def _sync_legacy_material_keys(settings: dict[str, Any], mapping: dict[str, list[str]]) -> None:
    settings["material_api_keys"] = mapping
    for item in MATERIAL_SOURCE_CATALOG:
        settings[item["legacy_key"]] = list(mapping.get(item["code"], []))


def ensure_material_source_cards(settings: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Migrate legacy per-source key lists into stable independent material cards."""
    original = settings.get(MATERIAL_CARDS_KEY)
    changed = False
    if isinstance(original, list) and original:
        cards = [normalize_material_card(item, index) for index, item in enumerate(original)]
        changed = cards != original
    else:
        cards: list[dict[str, Any]] = []
        for item in MATERIAL_SOURCE_CATALOG:
            for key in material_api_keys(settings, item["code"], _ignore_cards=True):
                cards.append(
                    _new_card(
                        item["code"],
                        key,
                        card_id=f"material-{item['code']}-{len(cards)}",
                        priority=len(cards) + 1,
                    )
                )
        if not cards:
            selected = selected_material_source(settings)
            cards.append(_new_card(selected if selected in _SOURCE_BY_CODE else "pexels", card_id="material-default-0"))
        changed = True

    ordered_cards = _ordered_cards(cards)
    if ordered_cards != cards:
        changed = True
    cards = ordered_cards
    settings[MATERIAL_CARDS_KEY] = cards
    active_id = str(settings.get(MATERIAL_ACTIVE_CARD_KEY) or "").strip()
    valid_ids = {str(card["id"]) for card in cards}
    if active_id not in valid_ids:
        selected_source = selected_material_source(settings)
        matching = next((card for card in cards if card["provider"] == selected_source), None)
        active_id = str(matching["id"]) if matching else str(cards[0]["id"])
        settings[MATERIAL_ACTIVE_CARD_KEY] = active_id
        changed = True

    mapping = _cards_key_mapping(cards)
    if settings.get("material_api_keys") != mapping:
        _sync_legacy_material_keys(settings, mapping)
        changed = True
    return settings, changed


def ensure_material_source_cards_for_ui(settings: dict[str, Any]) -> list[dict[str, Any]]:
    migrated, _ = ensure_material_source_cards(settings)
    return [dict(item) for item in migrated.get(MATERIAL_CARDS_KEY, [])]


def new_material_card(provider: str, *, card_id: str | None = None) -> dict[str, Any]:
    code = str(provider or "").strip().lower()
    if code not in _SOURCE_BY_CODE:
        raise ValueError("Fonte de materiais inválida.")
    return _new_card(code, card_id=card_id)


def apply_material_source_cards_to_settings(
    settings: dict[str, Any],
    cards: list[dict[str, Any]],
    active_card_id: str = "",
) -> dict[str, Any]:
    normalized_cards = [normalize_material_card(item, index) for index, item in enumerate(cards)]
    if not normalized_cards:
        normalized_cards = [_new_card("pexels", card_id="material-default-0")]
    normalized_cards = _ordered_cards(normalized_cards)
    settings[MATERIAL_CARDS_KEY] = normalized_cards
    selected_card = next((card for card in normalized_cards if str(card["id"]) == str(active_card_id)), None)
    if selected_card is None:
        selected_card = next((card for card in normalized_cards if card.get("enabled", True)), normalized_cards[0])
    settings[MATERIAL_ACTIVE_CARD_KEY] = str(selected_card["id"])
    settings["video_source"] = str(selected_card["provider"])
    _sync_legacy_material_keys(settings, _cards_key_mapping(normalized_cards))
    return settings


def material_api_keys(settings: dict[str, Any], source: str, _ignore_cards: bool = False) -> list[str]:
    code = str(source or "").strip().lower()
    if not _ignore_cards:
        cards = settings.get(MATERIAL_CARDS_KEY)
        if isinstance(cards, list) and cards:
            return _cards_key_mapping(cards).get(code, [])
    saved = settings.get("material_api_keys", {})
    if isinstance(saved, dict) and code in saved:
        return _as_key_list(saved.get(code))
    legacy_key = _SOURCE_BY_CODE.get(code, {}).get("legacy_key", f"{code}_api_keys")
    return _as_key_list(settings.get(legacy_key, ""))


def all_material_api_keys(settings: dict[str, Any]) -> dict[str, list[str]]:
    return {item["code"]: material_api_keys(settings, item["code"]) for item in MATERIAL_SOURCE_CATALOG}


def update_material_api_keys(settings: dict[str, Any], source: str, keys: list[str]) -> dict[str, Any]:
    code = str(source or "").strip().lower()
    if code not in _SOURCE_BY_CODE:
        raise ValueError("Fonte de materiais inválida.")
    cleaned = _as_key_list(keys)
    mapping = all_material_api_keys(settings)
    mapping[code] = cleaned
    _sync_legacy_material_keys(settings, mapping)
    return settings


def selected_material_source(settings: dict[str, Any]) -> str:
    source = str(settings.get("video_source") or "pexels").strip().lower()
    valid = set(_SOURCE_BY_CODE) | {"local"}
    return source if source in valid else "pexels"

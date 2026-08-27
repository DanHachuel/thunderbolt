from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import BLUEPRINTS, atomic_write, now


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9À-ÿ]+", "-", value.strip().lower()).strip("-")
    return value or "canal"


def parse_youtube_link(url: str) -> dict[str, str]:
    value = url.strip()
    if not value:
        raise ValueError("Introduza um link do YouTube.")
    video_id = ""
    channel_ref = ""
    input_type = "channel"
    if "youtu.be/" in value:
        video_id = value.split("youtu.be/", 1)[1].split("?", 1)[0].split("/", 1)[0]
        input_type = "video"
    elif "watch?v=" in value:
        video_id = value.split("watch?v=", 1)[1].split("&", 1)[0]
        input_type = "video"
    elif "/shorts/" in value:
        video_id = value.split("/shorts/", 1)[1].split("?", 1)[0].split("/", 1)[0]
        input_type = "video"
    elif "/@" in value:
        channel_ref = value.split("/@", 1)[1].split("/", 1)[0].split("?", 1)[0]
        input_type = "channel_handle"
    elif "/channel/" in value:
        channel_ref = value.split("/channel/", 1)[1].split("/", 1)[0].split("?", 1)[0]
        input_type = "channel_id"
    else:
        channel_ref = value.rstrip("/").split("/")[-1].lstrip("@")
        input_type = "channel_handle"
    return {"original_url": value, "video_id": video_id, "channel_ref": channel_ref, "input_type": input_type}


def create_blueprint_from_link(url: str, niche: str, language: str, include_branding: bool, channel_name: str = "", blueprint_name: str = "") -> tuple[dict[str, Any], dict[str, Any] | None]:
    parsed = parse_youtube_link(url)
    base_name = channel_name.strip() or parsed["channel_ref"] or "Canal analisado"
    display_name = blueprint_name.strip() or f"Blueprint — {base_name}"
    timestamp = datetime.now(timezone.utc).isoformat()
    blueprint_id = f"bp_{uuid.uuid4().hex[:10]}"
    blueprint = {
        "id": blueprint_id,
        "name": display_name,
        "metadata": {
            "task_type": "forensic_content_blueprint",
            "source_url": parsed["original_url"],
            "input_type": parsed["input_type"],
            "video_id": parsed["video_id"],
            "channel_ref": parsed["channel_ref"],
            "target_niche": niche or "não definido",
            "language": language,
            "created_at": timestamp,
            "status": "draft_local",
        },
        "channel_profile": {
            "channel_name": base_name,
            "handle": f"@{parsed['channel_ref']}" if parsed["channel_ref"] else "",
            "description": "Preencher com dados importados do YouTube e análise forense.",
            "audience": "",
            "content_pillars": [],
        },
        "content_strategy": {
            "niche": niche or "",
            "format": "faceless",
            "publishing_frequency": "",
            "hook_patterns": [],
            "title_formulas": [],
            "script_structure": ["hook", "context", "development", "payoff", "cta"],
            "full_script_target_characters": "7000-9000",
        },
        "research": {
            "top_videos": [],
            "sample_video": {},
            "transcripts": [],
            "source_notes": [],
        },
        "branding_id": "",
        "version": 1,
    }
    branding = None
    if include_branding:
        branding = create_branding_for_blueprint(blueprint)
        blueprint["branding_id"] = branding["id"]
    return blueprint, branding


def create_branding_for_blueprint(blueprint: dict[str, Any]) -> dict[str, Any]:
    metadata = blueprint.get("metadata", {})
    channel = blueprint.get("channel_profile", {})
    name = channel.get("channel_name") or blueprint.get("name", "Canal").replace("Blueprint — ", "")
    branding = {
        "id": f"branding_{uuid.uuid4().hex[:10]}",
        "name": f"Branding — {name}",
        "blueprint_id": blueprint.get("id", ""),
        "source_url": metadata.get("source_url", ""),
        "created_at": now(),
        "status": "draft_local",
        "identity": {
            "channel_name": name,
            "handle": channel.get("handle", ""),
            "tagline": "",
            "description": channel.get("description", ""),
            "hashtags": [],
            "keywords": [],
        },
        "visual_identity": {
            "color_palette": [],
            "typography": {"primary": "", "secondary": ""},
            "profile_image_prompt": f"Logo de perfil para o canal faceless {name}, nicho {metadata.get('target_niche', '')}, visual memorável, sem texto pequeno.",
            "banner_prompt": f"Banner de YouTube para {name}, nicho {metadata.get('target_niche', '')}, composição cinematográfica, espaço seguro para texto.",
            "thumbnail_direction": "alto contraste, uma ideia visual principal, máximo quatro palavras",
        },
        "assets": {
            "profile_image": "",
            "banner": "",
            "watermark": "",
            "brand_pack_path": "",
        },
        "checklist": {
            "name_reviewed": False,
            "handle_reviewed": False,
            "description_reviewed": False,
            "profile_prompt_reviewed": False,
            "banner_prompt_reviewed": False,
            "assets_generated": False,
        },
        "version": 1,
    }
    return branding


def save_generated_blueprint(blueprint: dict[str, Any], branding: dict[str, Any] | None = None) -> tuple[Path, Path | None]:
    """Persist generated Blueprint/Branding JSON using atomic replacement."""
    BLUEPRINTS.mkdir(parents=True, exist_ok=True)
    target = BLUEPRINTS / "canais" / f"{_slug(blueprint.get('name', 'blueprint'))}-{blueprint['id']}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(target, blueprint)
    branding_path = None
    if branding:
        branding_path = BLUEPRINTS / "brandings" / f"{_slug(branding.get('name', 'branding'))}-{branding['id']}.json"
        branding_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(branding_path, branding)
    return target, branding_path


def list_branding_files() -> list[Path]:
    folder = BLUEPRINTS / "brandings"
    folder.mkdir(parents=True, exist_ok=True)
    return sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

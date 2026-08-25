"""Helpers for resuming video creation from persisted scripts and drafts."""

from __future__ import annotations

from typing import Any

VIDEO_SETTING_KEYS = (
    "video_source",
    "video_format",
    "video_concatenation_mode",
    "match_visuals_to_script_order",
    "video_transition_mode",
    "video_aspect_ratio",
    "maximum_clip_duration",
    "videos_per_run",
    "video_encoder",
)

AUDIO_SETTING_KEYS = (
    "voiceover_mode",
    "voiceover_service",
    "voice",
    "voiceover_volume",
    "voiceover_speed",
    "background_music_source",
    "background_music_volume",
)

SUBTITLE_SETTING_KEYS = (
    "enable_subtitles",
    "subtitle_font",
    "subtitle_position",
    "subtitle_color",
    "subtitle_background",
    "subtitle_background_color",
    "subtitle_rounded_background",
    "subtitle_font_size",
    "subtitle_outline",
    "subtitle_outline_width",
)

DRAFT_SETTING_SECTIONS = {
    "Configurações de vídeo": VIDEO_SETTING_KEYS,
    "Configurações de áudio": AUDIO_SETTING_KEYS,
    "Configurações de legendas": SUBTITLE_SETTING_KEYS,
}


def keyword_text(value: Any) -> str:
    """Return keywords as a stable comma-separated string."""
    if isinstance(value, (list, tuple, set)):
        values = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(values)
    return str(value or "").strip()


def markdown_body(value: Any) -> str:
    """Remove the local Markdown front matter before using a saved script as input."""
    text = str(value or "").strip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2].lstrip("\r\n")
    return text.strip()


def normalise_saved_script(record: dict[str, Any], content: str = "") -> dict[str, Any]:
    """Map a script-history record or pipeline draft to video-creation fields."""
    generation_settings = record.get("generation_settings")
    generation_settings = dict(generation_settings) if isinstance(generation_settings, dict) else {}
    title = str(record.get("title") or record.get("video_subject") or generation_settings.get("video_subject") or record.get("topic") or "").strip()
    subject = str(record.get("video_subject") or generation_settings.get("video_subject") or record.get("topic") or title).strip()
    script = str(record.get("video_script") or generation_settings.get("video_script") or "").strip() or markdown_body(content)
    keywords = keyword_text(record.get("video_keywords") or record.get("keywords") or generation_settings.get("video_keywords"))
    if not subject:
        subject = title
    return {
        **record,
        "title": title or "Roteiro sem título",
        "video_subject": subject,
        "video_script": script,
        "video_keywords": keywords,
        "generation_settings": generation_settings,
        "language": str(record.get("language") or generation_settings.get("script_language") or "pt").strip(),
        "channel_id": str(record.get("channel_id") or "").strip(),
        "blueprint_id": str(record.get("blueprint_id") or "").strip(),
    }


def missing_setting_sections(settings: dict[str, Any]) -> list[str]:
    """Return the settings sections that are incomplete in a saved record."""
    return [
        label
        for label, keys in DRAFT_SETTING_SECTIONS.items()
        if any(key not in settings for key in keys)
    ]


def setting_widget_suffixes() -> tuple[str, ...]:
    """Return the widget suffixes used by the shared video settings renderer."""
    return tuple(dict.fromkeys(key for keys in DRAFT_SETTING_SECTIONS.values() for key in keys))


def missing_content_fields(record: dict[str, Any]) -> list[str]:
    """Return the required creative fields that are absent from a saved record."""
    missing: list[str] = []
    if not str(record.get("video_subject") or "").strip():
        missing.append("Video Subject")
    if not str(record.get("video_script") or "").strip():
        missing.append("Video Script")
    if not str(record.get("video_keywords") or "").strip():
        missing.append("Video Keywords")
    return missing


__all__ = [
    "AUDIO_SETTING_KEYS",
    "DRAFT_SETTING_SECTIONS",
    "SUBTITLE_SETTING_KEYS",
    "VIDEO_SETTING_KEYS",
    "keyword_text",
    "markdown_body",
    "missing_content_fields",
    "missing_setting_sections",
    "normalise_saved_script",
    "setting_widget_suffixes",
]

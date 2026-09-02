from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlatformAsset:
    platform: str
    width: int
    height: int
    design_id: str = ""
    export_url: str = ""
    edit_url: str = ""


@dataclass
class SkillResult:
    status: str
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FeedbackItem:
    category: str
    text: str
    actionable: bool = False
    source_id: str = ""

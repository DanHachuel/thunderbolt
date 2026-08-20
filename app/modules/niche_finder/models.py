from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class DatasetInfo:
    """Metadata about a cached or uploaded Niche Finder dataset."""

    path: Path
    source: str
    rows: int
    columns: tuple[str, ...]


@dataclass
class NicheAnalysisResult:
    """Structured result returned by ``run_niche_analysis``.

    The dictionaries are intentionally DataFrame-based so the Streamlit renderer
    can display, filter and export each result without depending on Flask or HTML.
    """

    clusters: pd.DataFrame
    frequent_items: pd.DataFrame
    association_rules: pd.DataFrame
    raw_data: pd.DataFrame
    cluster_points: pd.DataFrame
    summary: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "clusters": self.clusters,
            "frequent_items": self.frequent_items,
            "association_rules": self.association_rules,
            "raw_data": self.raw_data,
            "cluster_points": self.cluster_points,
            "summary": self.summary,
        }

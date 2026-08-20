from __future__ import annotations

import ast
import json
import re
from collections import Counter
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .data_loader import DatasetError, download_kaggle_dataset, load_dataframe
from .models import NicheAnalysisResult


EMPTY_CLUSTER_COLUMNS = [
    "cluster_id",
    "palavras",
    "tamanho",
    "media_visualizacoes",
    "media_engagement",
]
EMPTY_ITEM_COLUMNS = ["itemsets", "support", "item_count"]
EMPTY_RULE_COLUMNS = ["antecedents", "consequents", "support", "confidence", "lift"]


class NicheAnalysisError(ValueError):
    """Raised when a valid dataset cannot produce a meaningful analysis."""


def _parse_tags(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    if isinstance(value, (list, tuple, set)):
        raw_items = value
    else:
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "null", "[]"}:
            return []
        raw_items: Iterable[Any]
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                try:
                    parsed = ast.literal_eval(text)
                except (ValueError, SyntaxError):
                    parsed = None
            raw_items = parsed if isinstance(parsed, (list, tuple, set)) else re.split(r"[|,]", text.strip("[]"))
        else:
            raw_items = re.split(r"[|,]", text)
    tags: list[str] = []
    for item in raw_items:
        tag = re.sub(r"\s+", " ", str(item).replace('"', "").replace("'", "")).strip().lower()
        if tag and tag not in {"nan", "none", "null"}:
            tags.append(tag)
    return list(dict.fromkeys(tags))


def _engagement_label(value: str | int | None) -> str:
    if value is None or str(value).strip().lower() in {"", "todos", "all"}:
        return "Todos"
    if isinstance(value, str) and value in {"High", "Moderate", "Low"}:
        return value
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return "Todos"
    if numeric >= 67:
        return "High"
    if numeric >= 33:
        return "Moderate"
    return "Low"


def _filter_frame(
    frame: pd.DataFrame,
    *,
    start_date: str | None,
    end_date: str | None,
    country: str | None,
    engagement: str | int | None,
    tags: Iterable[str] | None,
) -> pd.DataFrame:
    filtered = frame.copy()
    if start_date:
        filtered = filtered[filtered["publish_date"] >= str(start_date)]
    if end_date:
        filtered = filtered[filtered["publish_date"] <= str(end_date)]
    if country and str(country).strip().lower() not in {"", "todos", "all"}:
        filtered = filtered[filtered["country"].str.casefold() == str(country).strip().casefold()]

    with np.errstate(divide="ignore", invalid="ignore"):
        filtered["engagement_rate"] = np.where(
            filtered["view_count"] > 0,
            ((filtered["like_count"] + filtered["comment_count"]) / filtered["view_count"]) * 100,
            0.0,
        )
    filtered["engagement_rate"] = filtered["engagement_rate"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    label = _engagement_label(engagement)
    if label == "High":
        filtered = filtered[filtered["engagement_rate"] >= 7]
    elif label == "Moderate":
        filtered = filtered[(filtered["engagement_rate"] >= 3) & (filtered["engagement_rate"] < 7)]
    elif label == "Low":
        filtered = filtered[filtered["engagement_rate"] < 3]

    selected_tags = {str(tag).strip().casefold() for tag in (tags or []) if str(tag).strip()}
    if selected_tags:
        filtered = filtered[filtered["video_tags"].map(lambda value: bool(selected_tags.intersection(_parse_tags(value))))]
    return filtered.drop_duplicates(subset="title", keep="first").reset_index(drop=True)


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _cluster_analysis(frame: pd.DataFrame, requested_clusters: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        return _empty_frame(EMPTY_CLUSTER_COLUMNS), pd.DataFrame()
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    features = frame[["view_count", "like_count"]].clip(lower=0).astype(float)
    transformed = np.log1p(features)
    scaled = StandardScaler().fit_transform(transformed)
    n_clusters = max(1, min(int(requested_clusters), len(frame)))
    if n_clusters == 1:
        labels = np.zeros(len(frame), dtype=int)
    else:
        labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(scaled)
    points = frame.copy()
    points["cluster_id"] = labels.astype(int)
    if len(points) >= 2:
        coordinates = PCA(n_components=2, random_state=42).fit_transform(scaled)
    else:
        coordinates = np.column_stack([scaled[:, 0], np.zeros(len(points))])
    points["x"] = coordinates[:, 0]
    points["y"] = coordinates[:, 1]

    summaries: list[dict[str, Any]] = []
    for cluster_id, group in points.groupby("cluster_id", sort=True):
        counter = Counter(tag for value in group["video_tags"] for tag in _parse_tags(value))
        words = ", ".join(tag for tag, _ in counter.most_common(8))
        summaries.append(
            {
                "cluster_id": int(cluster_id),
                "palavras": words,
                "tamanho": int(len(group)),
                "media_visualizacoes": round(float(group["view_count"].mean()), 2),
                "media_engagement": round(float(group["engagement_rate"].mean()), 2),
            }
        )
    return pd.DataFrame(summaries, columns=EMPTY_CLUSTER_COLUMNS), points


def _frequent_item_analysis(frame: pd.DataFrame, min_support: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        return _empty_frame(EMPTY_ITEM_COLUMNS), _empty_frame(EMPTY_RULE_COLUMNS)
    from mlxtend.frequent_patterns import association_rules, fpgrowth

    tag_lists = frame["video_tags"].map(_parse_tags)
    tag_counts = Counter(tag for tags in tag_lists for tag in tags)
    if not tag_counts:
        return _empty_frame(EMPTY_ITEM_COLUMNS), _empty_frame(EMPTY_RULE_COLUMNS)
    frequent_tags = {tag for tag, count in tag_counts.items() if count > len(frame) * 0.5}
    tag_lists = tag_lists.map(lambda tags: [tag for tag in tags if tag not in frequent_tags])
    all_tags = sorted({tag for tags in tag_lists for tag in tags})
    if not all_tags:
        return _empty_frame(EMPTY_ITEM_COLUMNS), _empty_frame(EMPTY_RULE_COLUMNS)
    matrix = pd.DataFrame(
        [{tag: tag in tags for tag in all_tags} for tags in tag_lists],
        columns=all_tags,
    ).astype(bool)
    itemsets = fpgrowth(matrix, min_support=float(min_support), use_colnames=True, max_len=3)
    if itemsets.empty:
        return _empty_frame(EMPTY_ITEM_COLUMNS), _empty_frame(EMPTY_RULE_COLUMNS)
    itemsets = itemsets.copy()
    itemsets["item_count"] = itemsets["itemsets"].map(len)
    itemsets["itemsets"] = itemsets["itemsets"].map(lambda values: ", ".join(sorted(values)))
    itemsets = itemsets[["itemsets", "support", "item_count"]].sort_values(["support", "item_count"], ascending=[False, True]).reset_index(drop=True)

    raw_itemsets = fpgrowth(matrix, min_support=float(min_support), use_colnames=True, max_len=3)
    try:
        rules = association_rules(raw_itemsets, metric="confidence", min_threshold=0.5)
    except TypeError:  # mlxtend compatibility across versions
        rules = association_rules(raw_itemsets, num_itemsets=len(matrix), metric="confidence", min_threshold=0.5)
    if rules.empty:
        return itemsets, _empty_frame(EMPTY_RULE_COLUMNS)
    rules = rules[rules["lift"] > 1.0].copy()
    if rules.empty:
        return itemsets, _empty_frame(EMPTY_RULE_COLUMNS)
    for column in ("antecedents", "consequents"):
        rules[column] = rules[column].map(lambda values: ", ".join(sorted(values)))
    wanted = [column for column in EMPTY_RULE_COLUMNS if column in rules.columns]
    rules = rules[wanted].sort_values(["lift", "confidence"], ascending=False).reset_index(drop=True)
    return itemsets, rules


def run_niche_analysis(
    dataset_path: str | None = None,
    n_clusters: int = 5,
    min_support: float = 0.01,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    country: str | None = None,
    engagement: str | int | None = None,
    tags: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Run the adapted Niche-Finder analysis synchronously in the caller process.

    The first three parameters preserve the integration contract described in
    ``exemplo.md``. Additional keyword-only filters retain the original project's
    date, country, engagement and tag controls for the Thunderbolt UI.
    """
    if not 2 <= int(n_clusters) <= 10:
        raise NicheAnalysisError("O número de clusters deve estar entre 2 e 10.")
    if not 0.001 <= float(min_support) <= 0.5:
        raise NicheAnalysisError("O suporte mínimo deve estar entre 0,001 e 0,5.")
    path = download_kaggle_dataset() if dataset_path is None else dataset_path
    try:
        frame = load_dataframe(path)
    except DatasetError as exc:
        raise NicheAnalysisError(str(exc)) from exc
    filtered = _filter_frame(
        frame,
        start_date=start_date,
        end_date=end_date,
        country=country,
        engagement=engagement,
        tags=tags,
    )
    if filtered.empty:
        raise NicheAnalysisError("Nenhum vídeo corresponde aos filtros seleccionados.")
    clusters, points = _cluster_analysis(filtered, int(n_clusters))
    frequent_items, rules = _frequent_item_analysis(filtered, float(min_support))
    result = NicheAnalysisResult(
        clusters=clusters,
        frequent_items=frequent_items,
        association_rules=rules,
        raw_data=filtered,
        cluster_points=points,
        summary={
            "rows_input": int(len(frame)),
            "rows_filtered": int(len(filtered)),
            "cluster_count": int(len(clusters)),
            "frequent_item_count": int(len(frequent_items)),
            "association_rule_count": int(len(rules)),
            "top_tags": [str(value) for value in frequent_items["itemsets"].head(10).tolist()] if not frequent_items.empty else [],
        },
    )
    return result.as_dict()

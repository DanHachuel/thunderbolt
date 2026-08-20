from __future__ import annotations

import pandas as pd
import pytest

from app.modules.niche_finder.core import run_niche_analysis
from app.modules.niche_finder.data_loader import DatasetError, load_dataframe, save_uploaded_csv


pytestmark = pytest.mark.filterwarnings("ignore::FutureWarning")


@pytest.fixture
def niche_csv(tmp_path):
    rows = []
    tag_groups = [
        "history|facts|war",
        "history|facts|ancient",
        "history|war|documentary",
        "gaming|review|games",
        "gaming|games|console",
        "gaming|review|pc",
        "cooking|recipes|food",
        "cooking|recipes|easy",
        "cooking|food|dinner",
        "history|facts|war",
        "gaming|games|console",
        "cooking|recipes|food",
    ]
    for index, tags in enumerate(tag_groups):
        rows.append(
            {
                "title": f"Video {index}",
                "publish_date": f"2025-01-{index + 1:02d}",
                "country": "US" if index < 9 else "BR",
                "view_count": 1000 + index * 100,
                "like_count": 100 + index * 10,
                "comment_count": 10 + index,
                "video_tags": tags,
                "channel_name": f"Channel {index % 3}",
            }
        )
    path = tmp_path / "niche.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_loader_requires_core_columns(tmp_path):
    path = tmp_path / "invalid.csv"
    pd.DataFrame([{"title": "Only title"}]).to_csv(path, index=False)
    with pytest.raises(DatasetError, match="colunas"):
        load_dataframe(path)


def test_save_uploaded_csv_validates_and_persists(tmp_path, monkeypatch, niche_csv):
    from app.modules.niche_finder import data_loader

    monkeypatch.setattr(data_loader, "DATA_DIR", tmp_path / "data" / "niches")
    saved = save_uploaded_csv(niche_csv.read_bytes(), "my niche.csv")
    assert saved.exists()
    assert saved.parent.name == "uploads"
    assert load_dataframe(saved).shape[0] == 12


def test_run_niche_analysis_returns_dataframes_and_filters(niche_csv):
    pytest.importorskip("sklearn")
    pytest.importorskip("mlxtend")
    result = run_niche_analysis(
        str(niche_csv),
        n_clusters=3,
        min_support=0.1,
        start_date="2025-01-01",
        end_date="2025-01-09",
        country="US",
        engagement="Todos",
    )
    assert set(["clusters", "frequent_items", "association_rules", "raw_data", "cluster_points", "summary"]).issubset(result)
    assert isinstance(result["clusters"], pd.DataFrame)
    assert isinstance(result["frequent_items"], pd.DataFrame)
    assert isinstance(result["association_rules"], pd.DataFrame)
    assert isinstance(result["raw_data"], pd.DataFrame)
    assert len(result["raw_data"]) == 9
    assert 1 <= len(result["clusters"]) <= 3
    assert result["summary"]["rows_filtered"] == 9

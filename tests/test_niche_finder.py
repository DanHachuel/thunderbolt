from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest

from app.modules.niche_finder.core import run_niche_analysis
from app.modules.niche_finder.data_loader import DatasetError, load_dataframe


pytestmark = pytest.mark.filterwarnings("ignore::FutureWarning")


def test_niche_finder_requires_explicit_analysis_submit():
    source_path = Path(__file__).parents[1] / "app" / "main.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "render_niche_finder")
    function_source = ast.get_source_segment(source_path.read_text(encoding="utf-8"), function)

    assert function_source is not None
    assert "with st.sidebar" not in function_source
    assert 'st.form_submit_button("Analisar Nichos"' in function_source
    assert "if analyse:" in function_source
    assert "_cached_niche_download()" in function_source
    assert "run_niche_analysis(" in function_source
    assert "Nenhum dataset é descarregado e nenhuma análise é executada enquanto não clicar" in function_source



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
    with pytest.raises(DatasetError, match="colunas necessárias"):
        load_dataframe(path)


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


def _write_minimal_cached_dataset(path):
    pd.DataFrame(
        [
            {
                "title": "Cached video",
                "publish_date": "2025-01-01",
                "country": "US",
                "view_count": 100,
                "like_count": 10,
                "comment_count": 1,
                "video_tags": "cache|test",
            }
        ]
    ).to_csv(path, index=False)


def test_automatic_loader_reuses_valid_existing_cache(tmp_path, monkeypatch):
    from app.modules.niche_finder import data_loader

    data_dir = tmp_path / "storage" / "data" / "niches"
    data_dir.mkdir(parents=True)
    cached_path = data_dir / data_loader.DEFAULT_DATASET_FILENAME
    _write_minimal_cached_dataset(cached_path)
    monkeypatch.setattr(data_loader, "DATA_DIR", data_dir)
    monkeypatch.setattr(data_loader, "DEFAULT_DATASET_PATH", cached_path)

    class UnexpectedKaggleHub:
        def dataset_download(self, *args, **kwargs):
            raise AssertionError("KaggleHub não deveria ser chamado para uma cache válida")

    monkeypatch.setattr(data_loader, "kagglehub", UnexpectedKaggleHub())
    assert data_loader.download_kaggle_dataset() == cached_path


def test_automatic_loader_downloads_into_empty_temporary_directory(tmp_path, monkeypatch):
    from app.modules.niche_finder import data_loader

    data_dir = tmp_path / "storage" / "data" / "niches"
    data_dir.mkdir(parents=True)
    cached_path = data_dir / data_loader.DEFAULT_DATASET_FILENAME
    monkeypatch.setattr(data_loader, "DATA_DIR", data_dir)
    monkeypatch.setattr(data_loader, "DEFAULT_DATASET_PATH", cached_path)
    calls = []

    class FakeKaggleHub:
        def dataset_download(self, slug, *, output_dir, force_download):
            output = Path(output_dir)
            calls.append((slug, output, force_download))
            assert output.exists()
            assert list(output.iterdir()) == []
            assert force_download is True
            source = output / data_loader.DEFAULT_DATASET_FILENAME
            _write_minimal_cached_dataset(source)
            return str(output)

    from pathlib import Path

    monkeypatch.setattr(data_loader, "kagglehub", FakeKaggleHub())
    result = data_loader.download_kaggle_dataset()
    assert result == cached_path
    assert cached_path.exists()
    assert calls[0][0] == data_loader.DEFAULT_DATASET_SLUG
    assert not list(data_dir.parent.glob(".niche-kaggle-*"))


def test_niche_finder_navigation_has_kaggle_and_apify_pages():
    source_path = Path(__file__).parents[1] / "app" / "main.py"
    source = source_path.read_text(encoding="utf-8")

    assert 'niche_finder_items = [' in source
    assert '("Niche Finder Kaggle", ":material/search:", "Niche Finder Kaggle")' in source
    assert '("Niche Finder Apify", ":material/api:", "Niche Finder Apify")' in source
    assert '"Niche Finder Kaggle": render_niche_finder' in source
    assert '"Niche Finder Apify": render_niche_finder_apify' in source
    assert source.index('("Niche Finder Kaggle"') < source.index('("Niche Finder Apify"')
    assert 'st.title("Niche Finder Apify")' in source
    assert 'st.form_submit_button("Pesquisar no Apify"' in source
    assert 'Ainda não existe uma pesquisa nesta sessão' in source

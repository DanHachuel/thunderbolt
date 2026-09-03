from pathlib import Path

from app.modules.canva_skills.thumbnail_workflow import (
    CanvaThumbnailWorkflowError,
    build_search_query,
    run_thumbnail_workflow,
    select_design,
)


def test_search_query_uses_video_context_and_blueprint_niche():
    query = build_search_query("Guerra no Pacífico", "história naval", {"niche": "geopolítica"})
    assert "guerra" in query
    assert "pacífico" in query
    assert "geopolítica" in query


def test_select_design_prefers_exact_thumbnail_dimensions():
    result = select_design(
        [
            {"id": "wrong", "thumbnail": {"width": 1920, "height": 1080}},
            {"id": "exact", "thumbnail": {"width": 1280, "height": 720}},
        ],
        1280,
        720,
    )
    assert result["id"] == "exact"


def test_workflow_reads_blueprint_searches_edits_then_exports(tmp_path: Path):
    calls = []
    output = tmp_path / "thumbnail.png"

    result = run_thumbnail_workflow(
        title="A grande batalha",
        topic="história militar",
        channel={"thumbnail_blueprint_id": "Generic_Thumbnail_Blueprint"},
        width=1280,
        height=720,
        search_designs=lambda query: (calls.append(("search", query)) or [{"id": "design-1", "thumbnail": {"width": 1280, "height": 720}}]),
        edit_design=lambda design_id, changes, blueprint: (calls.append(("edit", design_id, changes["blueprint_id"])) or {"status": "committed", "design_id": design_id}),
        export_design=lambda design_id, fmt, quality, width, height: (calls.append(("export", design_id, fmt, quality, width, height)) or output),
    )
    assert result == output
    assert [call[0] for call in calls] == ["search", "edit", "export"]


def test_workflow_never_exports_without_committed_edit():
    try:
        run_thumbnail_workflow(
            title="Teste",
            topic="",
            channel={"thumbnail_blueprint_id": "Generic_Thumbnail_Blueprint"},
            search_designs=lambda query: [{"id": "design-1", "thumbnail": {"width": 1280, "height": 720}}],
            edit_design=lambda design_id, changes, blueprint: {"status": "manual_action_required", "design_id": design_id},
            export_design=lambda *args: (_ for _ in ()).throw(AssertionError("não deve exportar")),
        )
    except CanvaThumbnailWorkflowError as exc:
        assert "não foi confirmada" in str(exc)
    else:
        raise AssertionError("Era esperado bloquear a exportação sem edição confirmada")

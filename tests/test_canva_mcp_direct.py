from pathlib import Path
from unittest.mock import Mock, patch

from hermes_ui.canva_mcp_workflow import _download_url, _first_text_element, _has_richtext, _design_id, run_direct_canva_thumbnail


def test_direct_workflow_calls_search_edit_commit_formats_export_in_order(tmp_path: Path):
    client = Mock()
    client.tools.return_value = [
        {"name": "search-designs"},
        {"name": "get-design-content"},
        {"name": "start-editing-transaction"},
        {"name": "perform-editing-operations"},
        {"name": "commit-editing-transaction"},
        {"name": "get-export-formats"},
        {"name": "export-design"},
    ]
    client.call.side_effect = [
        {"structuredContent": {"items": [{"id": "D1234567890", "thumbnail": {"width": 1280, "height": 720}}]}},
        {"structuredContent": {"richtexts": [{"element_id": "text-1", "text": "old"}]}},
        {"structuredContent": {"transaction_id": "tx-1", "pages": [{"page_id": "page-1", "is_responsive": False}]}},
        {"structuredContent": {"pages": [{"page_id": "page-1", "is_responsive": False}]}},
        {"structuredContent": {"ok": True}},
        {"structuredContent": {"formats": [{"type": "png"}]}},
        {"structuredContent": {"job": {"status": "success", "urls": ["https://cdn.example/thumb.png"]}}},
    ]
    response = Mock(content=b"png", status_code=200)
    response.raise_for_status.return_value = None
    with patch("hermes_ui.canva_mcp_workflow.CanvaMCPClient") as factory, patch("hermes_ui.canva_mcp_workflow.requests.get", return_value=response):
        factory.return_value.__enter__.return_value = client
        output = tmp_path / "thumb.png"
        result = run_direct_canva_thumbnail(
            title="Título da thumbnail",
            topic="história",
            prompt="prompt",
            blueprint={"id": "HISTORIA_Thumbnail_Blueprint", "content": "rules"},
            destination=output,
            width=1280,
            height=720,
        )
    assert result == output
    assert output.read_bytes() == b"png"
    assert [call.args[0] for call in client.call.call_args_list] == [
        "search-designs", "get-design-content", "start-editing-transaction",
        "perform-editing-operations", "commit-editing-transaction",
        "get-export-formats", "export-design",
    ]
    get_content_arguments = client.call.call_args_list[1].args[1]
    assert get_content_arguments["content_types"] == ["richtexts"]


def test_direct_workflow_requires_search_result(tmp_path: Path):
    client = Mock()
    client.tools.return_value = [{"name": "search-designs"}]
    client.call.return_value = {"structuredContent": {"items": []}}
    with patch("hermes_ui.canva_mcp_workflow.CanvaMCPClient") as factory:
        factory.return_value.__enter__.return_value = client
        try:
            run_direct_canva_thumbnail(
                title="Teste", topic="", prompt="prompt",
                blueprint={"id": "bp", "content": "rules"},
                destination=tmp_path / "thumb.png", width=1280, height=720,
            )
        except Exception as exc:
            assert "não encontrou designs" in str(exc)
        else:
            raise AssertionError("O fluxo deveria falhar sem resultado de pesquisa")


def test_design_id_accepts_canva_mcp_identifier_variants():
    assert _design_id({"design_id": "D-1"}) == "D-1"
    assert _design_id({"designId": "D-2"}) == "D-2"
    assert _design_id({"design": {"id": "D-3"}}) == "D-3"


def test_text_element_accepts_canva_richtext_identifier_variants():
    assert _first_text_element({"richtexts": [{"richtext_id": "R-1", "content": "old"}]}) == "R-1"
    assert _first_text_element({"text_elements": [{"elementId": "E-2", "value": "old"}]}) == "E-2"
    assert _first_text_element({"elements": [{"id": "E-3", "type": "rich_text"}]}) == "E-3"


def test_has_richtext_matches_official_canva_transaction_shape():
    assert _has_richtext({"richtexts": [{"element_id": "E-1", "regions": []}]}) is True
    assert _has_richtext({"richtexts": [], "fills": []}) is False


def test_download_url_accepts_official_export_job_urls_shape():
    assert _download_url({"job": {"status": "success", "urls": ["https://export.canva.com/thumb.png"]}}) == "https://export.canva.com/thumb.png"


def test_direct_workflow_skips_search_result_without_id(tmp_path: Path):
    client = Mock()
    client.tools.return_value = [{"name": "search-designs"}]
    client.call.return_value = {
        "structuredContent": {"items": [{"title": "sem id"}, {"design_id": "D-456"}]}
    }
    with patch("hermes_ui.canva_mcp_workflow.CanvaMCPClient") as factory:
        factory.return_value.__enter__.return_value = client
        try:
            run_direct_canva_thumbnail(
                title="Teste", topic="", prompt="prompt",
                blueprint={"id": "bp", "content": "rules"},
                destination=tmp_path / "thumb.png", width=1280, height=720,
            )
        except Exception as exc:
            assert "não devolveu o ID do design" not in str(exc)


def test_direct_workflow_generates_editable_thumbnail_when_search_has_no_text(tmp_path: Path):
    client = Mock()
    client.tools.return_value = [
        {"name": name} for name in (
            "search-designs", "get-design-content", "generate-design",
            "create-design-from-candidate", "start-editing-transaction",
            "perform-editing-operations", "commit-editing-transaction",
            "get-export-formats", "export-design",
        )
    ]
    client.call.side_effect = [
        {"structuredContent": {"items": [{"id": "D1111111111"}]}},
        {"structuredContent": {"richtexts": []}},
        {"structuredContent": {"job": {"id": "job-1", "result": {"generated_designs": [{"candidate_id": "candidate-1"}]}}}},
        {"structuredContent": {"design_summary": {"id": "D2222222222"}}},
        {"structuredContent": {"richtexts": [{"element_id": "text-1", "text": "headline"}]}},
        {"structuredContent": {"transaction_id": "tx-1", "pages": [{"page_id": "p-1", "is_responsive": False}]}},
        {"structuredContent": {"ok": True}},
        {"structuredContent": {"ok": True}},
        {"structuredContent": {"formats": [{"type": "png"}]}},
        {"structuredContent": {"url": "https://cdn.example/generated.png"}},
    ]
    response = Mock(content=b"png", status_code=200)
    response.raise_for_status.return_value = None
    with patch("hermes_ui.canva_mcp_workflow.CanvaMCPClient") as factory, patch("hermes_ui.canva_mcp_workflow.requests.get", return_value=response):
        factory.return_value.__enter__.return_value = client
        output = tmp_path / "thumb.png"
        assert run_direct_canva_thumbnail(
            title="Título", topic="história", prompt="prompt",
            blueprint={"id": "bp", "content": "headline, dark background, icons"},
            destination=output, width=1280, height=720,
        ) == output
    generate_call = next(call for call in client.call.call_args_list if call.args[0] == "generate-design")
    assert generate_call.args[1]["design_type"] == "youtube_thumbnail"
    assert "editable headline text boxes" in generate_call.args[1]["query"]

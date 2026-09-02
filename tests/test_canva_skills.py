from unittest.mock import Mock

from app.modules.canva_skills.bulk import bulk_create_thumbnails
from app.modules.canva_skills.edit import edit_design
from app.modules.canva_skills.resize import resize_for_social_media


class SkillClient:
    def __init__(self):
        self.calls = []

    def post(self, endpoint, data=None):
        self.calls.append(("POST", endpoint, data))
        if endpoint == "autofills":
            return {"job": {"id": "auto-1"}}
        if endpoint == "designs":
            return {"design": {"id": "copy-1", "urls": {"edit_url": "https://canva/edit"}}}
        if endpoint == "exports":
            return {"job": {"id": "export-1"}}
        return {}

    def get(self, endpoint, params=None):
        self.calls.append(("GET", endpoint, params))
        if endpoint == "autofills/auto-1":
            return {"job": {"status": "success", "design": {"id": "design-1"}}}
        if endpoint == "exports/export-1":
            return {"job": {"status": "success", "urls": ["https://cdn/thumb.png"]}}
        return {}

    def export_design(self, design_id, file_type="png", quality="regular"):
        self.calls.append(("EXPORT", design_id, file_type))
        return "export-1"

    def wait_export(self, job_id):
        self.calls.append(("WAIT", job_id))
        return "https://cdn/thumb.png"


def test_bulk_create_uses_official_autofill_and_export_jobs():
    client = SkillClient()
    result = bulk_create_thumbnails("template-1", [{"titulo": "A", "texto": "B"}], client=client)
    assert result[0]["design_id"] == "design-1"
    assert ("POST", "autofills",) == client.calls[0][:2]


def test_resize_returns_platform_dimensions_and_edit_link():
    client = SkillClient()
    result = resize_for_social_media("design-1", ["youtube_thumbnail", "instagram_post"], client=client)
    assert result["youtube_thumbnail"]["width"] == 1280
    assert result["instagram_post"]["height"] == 1080
    assert result["youtube_thumbnail"]["edit_url"] == "https://canva/edit"


def test_edit_design_requires_approval_and_does_not_claim_rest_commit():
    client = Mock()
    pending = edit_design("design-1", {"texts": []}, client=client)
    assert pending["status"] == "pending_approval"
    manual = edit_design("design-1", {"texts": []}, client=client, auto_commit=True)
    assert manual["status"] == "manual_action_required"
    client.post.assert_not_called()

from __future__ import annotations

from typing import Any, Mapping

from .client import CanvaSkillsClient


def _autofill(client: CanvaSkillsClient, template_id: str, row: Mapping[str, Any], title: str) -> str:
    data = {key: value if isinstance(value, Mapping) else {"type": "text", "text": str(value)} for key, value in row.items()}
    payload = client.post("autofills", {"type": "create_from_brand_template", "brand_template_id": template_id, "data": data, "title": title[:255] or "Thunderbolt thumbnail"})
    job = payload.get("job") or payload
    job_id = str(job.get("id") or "")
    if not job_id:
        raise RuntimeError("A Canva não devolveu o job de autofill.")
    for _ in range(60):
        status_payload = client.get(f"autofills/{job_id}")
        status_job = status_payload.get("job") or status_payload
        status = str(status_job.get("status") or "").lower()
        if status == "success":
            design = status_job.get("design") or {}
            design_id = str(design.get("id") or status_job.get("design_id") or "")
            if design_id:
                return design_id
        if status == "failed":
            raise RuntimeError(f"Autofill Canva falhou: {status_job.get('error') or status_job}")
    raise RuntimeError("Autofill Canva excedeu o tempo de espera.")


def bulk_create_thumbnails(template_id: str, data: list[Mapping[str, Any]], export_format: str = "png", *, client: CanvaSkillsClient) -> list[dict[str, Any]]:
    if not template_id.strip():
        raise ValueError("É necessário indicar um Brand Template Canva.")
    results = []
    for row in data:
        design_id = _autofill(client, template_id, row, str(row.get("titulo") or row.get("title") or "Thunderbolt thumbnail"))
        job_id = client.export_design(design_id, file_type=export_format.lower())
        results.append({"design_id": design_id, "export_url": client.wait_export(job_id), "metadata": dict(row)})
    return results

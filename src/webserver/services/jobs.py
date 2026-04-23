from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from webserver.services.storage import StorageError, issue_download_url


def to_ui_job(row: Dict[str, Any]) -> Dict[str, Any]:
    sketch_key = row.get("sketch_path") or ""
    generated_key = row.get("result_path") or ""
    status = row.get("status") or "queued"
    sketch_url = _safe_signed_url(sketch_key)
    generated_url = _safe_signed_url(generated_key) if status == "completed" else ""
    return {
        "id": str(row["id"]),
        "title": row.get("title") or "Untitled Concept",
        "prompt": row.get("prompt") or "",
        "style": row.get("style") or "Cinematic",
        "sketch_name": row.get("sketch_name") or "upload.png",
        "sketch_key": sketch_key,
        "generated_key": generated_key,
        "sketch_url": sketch_url,
        "generated_url": generated_url,
        "status": status,
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "progress": _progress_for_status(status),
    }


def to_api_job(row: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "job_id": str(row["id"]),
        "title": row.get("title"),
        "prompt": row.get("prompt"),
        "style": row.get("style"),
        "status": row.get("status"),
        "created_at": _to_iso(row.get("created_at")),
        "updated_at": _to_iso(row.get("updated_at")),
    }
    if row.get("error"):
        payload["error"] = row["error"]
    if row.get("sketch_path"):
        payload["sketch_url"] = _safe_signed_url(row["sketch_path"])
    if row.get("result_path"):
        payload["result_url"] = _safe_signed_url(row["result_path"])
    return payload


def select_featured(
    items: List[Dict[str, Any]], selected_job_id: str
) -> Tuple[
    Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]
]:
    if not items:
        return None, None, None

    featured_index = 0
    for idx, item in enumerate(items):
        if item["id"] == selected_job_id:
            featured_index = idx
            break

    featured = items[featured_index]
    prev_item = items[(featured_index - 1) % len(items)]
    next_item = items[(featured_index + 1) % len(items)]
    return featured, prev_item, next_item


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _safe_signed_url(object_key: str) -> str:
    if not object_key:
        return ""
    try:
        return issue_download_url(object_key)
    except StorageError:
        return ""


def _progress_for_status(status: str) -> int:
    if status == "completed":
        return 100
    if status == "processing":
        return 55
    if status == "queued":
        return 15
    return 0

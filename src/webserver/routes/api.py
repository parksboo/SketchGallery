from __future__ import annotations

import uuid

from flask import Blueprint, current_app, jsonify, request

from webserver.services.jobs import to_api_job
from webserver.services.storage import StorageError, copy_object, issue_upload_url

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


def _repo():
    return current_app.extensions["repo"]


@api_bp.get("/health")
def health() -> tuple:
    return jsonify({"status": "ok"}), 200


@api_bp.post("/uploads/sign")
def sign_upload() -> tuple:
    payload = request.get_json(silent=True) or {}
    filename = str(payload.get("filename", "")).strip()
    purpose = str(payload.get("purpose", "sketches")).strip() or "sketches"

    if not filename:
        return jsonify({"error": "filename is required"}), 400

    try:
        signed = issue_upload_url(filename=filename, purpose=purpose)
    except StorageError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(signed), 200


@api_bp.post("/jobs")
def create_job() -> tuple:
    payload = request.get_json(silent=True) or {}
    sketch_key = str(payload.get("sketch_key", "")).strip()
    if not sketch_key:
        return jsonify({"error": "sketch_key is required"}), 400

    job_id = str(uuid.uuid4())
    title = str(payload.get("title", "Untitled Concept")).strip() or "Untitled Concept"
    prompt = str(payload.get("prompt", "No prompt yet")).strip() or "No prompt yet"
    style = str(payload.get("style", "Cinematic")).strip() or "Cinematic"
    sketch_name = str(payload.get("sketch_name", "upload.png")).strip() or "upload.png"

    result_key = f"results/{job_id}.png"
    try:
        generated = copy_object(sketch_key, result_key)
    except StorageError as exc:
        return jsonify({"error": str(exc)}), 502

    _repo().create_job(
        job_id=job_id,
        title=title,
        prompt=prompt,
        style=style,
        sketch_name=sketch_name,
        sketch_path=sketch_key,
        result_path=generated["key"],
        status="completed",
    )

    return jsonify({"job_id": job_id, "status": "completed"}), 201


@api_bp.get("/jobs/<job_id>")
def get_job(job_id: str) -> tuple:
    row = _repo().get_job(job_id)
    if not row:
        return jsonify({"error": "job not found"}), 404
    return jsonify(to_api_job(row)), 200


@api_bp.get("/jobs/<job_id>/result")
def get_result(job_id: str):
    row = _repo().get_job(job_id)
    if not row:
        return jsonify({"error": "job not found"}), 404
    if row.get("status") != "completed" or not row.get("result_path"):
        return jsonify({"error": "result is not ready"}), 409
    return jsonify({"result_url": to_api_job(row).get("result_url")}), 200


@api_bp.get("/gallery")
def get_gallery() -> tuple:
    limit = int(request.args.get("limit", "50"))
    limit = max(1, min(limit, 200))

    rows = _repo().list_completed_jobs(limit=limit)
    return jsonify({"items": [to_api_job(row) for row in rows]}), 200

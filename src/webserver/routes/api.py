from __future__ import annotations

import uuid

from flask import Blueprint, current_app, jsonify, request

from webserver.config import settings
from webserver.services.generation import GenerationDispatchError, dispatch_generation_job
from webserver.services.jobs import to_api_job
from webserver.services.storage import StorageError, delete_object, issue_upload_url

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
    default_mode = settings.default_generation_mode.strip() or "test"
    mode = str(payload.get("mode", default_mode)).strip() or default_mode

    result_key = f"results/{job_id}.png"

    _repo().create_job(
        job_id=job_id,
        title=title,
        prompt=prompt,
        style=style,
        sketch_name=sketch_name,
        sketch_path=sketch_key,
        result_path=result_key,
        status="queued",
    )

    try:
        dispatch_generation_job(
            job_id=job_id,
            sketch_key=sketch_key,
            result_key=result_key,
            title=title,
            prompt=prompt,
            style=style,
            mode =mode,
        )
        _repo().mark_processing(job_id)
    except GenerationDispatchError as exc:
        _repo().mark_failed(job_id, str(exc))
        return jsonify({"job_id": job_id, "status": "failed", "error": str(exc)}), 502

    return jsonify({"job_id": job_id, "status": "processing"}), 202


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


@api_bp.delete("/jobs/<job_id>")
def delete_job(job_id: str) -> tuple:
    row = _repo().get_job(job_id)
    if not row:
        return jsonify({"error": "job not found"}), 404

    sketch_key = str(row.get("sketch_path") or "").strip()
    result_key = str(row.get("result_path") or "").strip()

    try:
        delete_object(result_key)
        if sketch_key and sketch_key != result_key:
            delete_object(sketch_key)
    except StorageError as exc:
        return jsonify({"error": str(exc)}), 502

    _repo().delete_job(job_id)
    return jsonify({"job_id": job_id, "status": "deleted"}), 200


@api_bp.post("/internal/ray/jobs/<job_id>/result")
def ray_job_result(job_id: str) -> tuple:
    token = settings.ray_shared_token.strip()
    if token:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {token}":
            return jsonify({"error": "unauthorized"}), 401

    row = _repo().get_job(job_id)
    if not row:
        return jsonify({"error": "job not found"}), 404

    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status", "")).strip().lower()
    if status not in {"completed", "failed"}:
        return jsonify({"error": "status must be 'completed' or 'failed'"}), 400

    if status == "completed":
        result_key = str(payload.get("result_key", row.get("result_path") or "")).strip()
        if not result_key:
            return jsonify({"error": "result_key is required for completed status"}), 400
        _repo().mark_completed(job_id, result_key)
        return jsonify({"job_id": job_id, "status": "completed"}), 200

    error = str(payload.get("error", "ray generation failed")).strip() or "ray generation failed"
    _repo().mark_failed(job_id, error)
    return jsonify({"job_id": job_id, "status": "failed", "error": error}), 200

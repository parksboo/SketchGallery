from __future__ import annotations

import uuid
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from webserver.config import settings
from webserver.services.generation import GenerationDispatchError, dispatch_generation_job
from webserver.services.jobs import select_featured, to_ui_job
from webserver.services.storage import StorageError, delete_object

ui_bp = Blueprint("ui", __name__)


def _repo():
    return current_app.extensions["repo"]


def _with_toast(url: str, message: str, level: str = "success") -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["toast"] = message
    query["toast_level"] = level
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


@ui_bp.app_template_filter("human_time")
def human_time(value):
    if isinstance(value, datetime):
        return value.astimezone().strftime("%Y-%m-%d %H:%M")
    return str(value)


@ui_bp.get("/")
def home() -> str:
    rows = _repo().list_jobs(limit=5)
    jobs = [to_ui_job(row) for row in rows]
    return render_template("index.html", jobs=jobs, stats=_repo().stats())


@ui_bp.route("/create", methods=["GET", "POST"])
def create() -> str:
    form_error = None
    if request.method == "POST":
        title = request.form.get("title", "Untitled Concept").strip() or "Untitled Concept"
        prompt = request.form.get("prompt", "").strip() or "No prompt yet"
        style = request.form.get("style", "Cinematic").strip() or "Cinematic"
        sketch_key = request.form.get("sketch_key", "").strip()
        sketch_name = request.form.get("sketch_name", "upload.png").strip() or "upload.png"
        default_mode = settings.default_generation_mode.strip() or "test"
        mode = request.form.get("mode", default_mode).strip() or default_mode

        if not sketch_key:
            form_error = "Upload sketch to GCS first."
        else:
            job_id = str(uuid.uuid4())
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
                    mode=mode,
                )
                _repo().mark_processing(job_id)
            except GenerationDispatchError as exc:
                _repo().mark_failed(job_id, str(exc))
                form_error = str(exc)
                return render_template("create.html", form_error=form_error)

            return redirect(url_for("ui.job_detail", job_id=job_id))

    return render_template("create.html", form_error=form_error)


@ui_bp.get("/jobs/<job_id>")
def job_detail(job_id: str):
    row = _repo().get_job(job_id)
    if not row:
        return render_template("not_found.html", job_id=job_id), 404
    return render_template("job_detail.html", job=to_ui_job(row))


@ui_bp.get("/gallery")
def gallery() -> str:
    rows = _repo().list_completed_jobs(limit=100)
    items = [to_ui_job(row) for row in rows]

    mode = request.args.get("mode", "grid")
    selected_job_id = request.args.get("job_id", "")
    featured, prev_item, next_item = select_featured(items, selected_job_id)

    if mode not in {"grid", "museum"}:
        mode = "grid"

    return render_template(
        "gallery.html",
        items=items,
        mode=mode,
        featured=featured,
        prev_item=prev_item,
        next_item=next_item,
    )


@ui_bp.post("/jobs/<job_id>/delete")
def delete_job(job_id: str):
    row = _repo().get_job(job_id)
    if not row:
        return render_template("not_found.html", job_id=job_id), 404

    sketch_key = str(row.get("sketch_path") or "").strip()
    result_key = str(row.get("result_path") or "").strip()

    try:
        delete_object(result_key)
        if sketch_key and sketch_key != result_key:
            delete_object(sketch_key)
    except StorageError as exc:
        return render_template("job_detail.html", job=to_ui_job(row), form_error=str(exc)), 502

    _repo().delete_job(job_id)

    next_url = str(request.form.get("next", "")).strip()
    if next_url.startswith("/"):
        return redirect(_with_toast(next_url, "Artwork deleted from gallery."))
    return redirect(_with_toast(url_for("ui.gallery"), "Artwork deleted from gallery."))

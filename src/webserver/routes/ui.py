from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from webserver.services.jobs import select_featured, to_ui_job
from webserver.services.storage import DataPlaneError, copy_file, upload_endpoint

ui_bp = Blueprint("ui", __name__)


def _repo():
    return current_app.extensions["repo"]


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

        if not sketch_key:
            form_error = "Upload sketch to dataplane first."
        else:
            job_id = request.form.get("job_id", "").strip()
            if not job_id:
                form_error = "job_id is required."
                return render_template("create.html", form_error=form_error, dataplane_upload_url=upload_endpoint())
            try:
                generated = copy_file(sketch_key)
            except DataPlaneError as exc:
                form_error = str(exc)
                return render_template("create.html", form_error=form_error, dataplane_upload_url=upload_endpoint())

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
            return redirect(url_for("ui.job_detail", job_id=job_id))

    return render_template("create.html", form_error=form_error, dataplane_upload_url=upload_endpoint())


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


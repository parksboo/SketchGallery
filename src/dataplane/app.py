from __future__ import annotations

import io
import os
import shutil
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_file
from werkzeug.datastructures import FileStorage

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
DATA_ROOT = Path(os.getenv("DATAPLANE_DATA_ROOT", "/data/objects"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
PUBLIC_BASE_URL = os.getenv("DATAPLANE_PUBLIC_BASE_URL", "http://127.0.0.1:8080")
MAX_CONTENT_MB = int(os.getenv("MAX_CONTENT_MB", "20"))


def _safe_path(key: str) -> Path:
    path = (DATA_ROOT / key).resolve()
    root = DATA_ROOT.resolve()
    if root not in path.parents and path != root:
        raise ValueError("invalid file key")
    return path


def _is_png(upload: FileStorage) -> bool:
    name = (upload.filename or "").lower()
    if not name.endswith(".png"):
        return False

    pos = upload.stream.tell()
    header = upload.stream.read(8)
    upload.stream.seek(pos, io.SEEK_SET)
    return header == PNG_SIGNATURE


def _new_key(suffix: str = ".png") -> str:
    return f"{uuid.uuid4()}{suffix}"


def _public_url(key: str) -> str:
    return f"{PUBLIC_BASE_URL.rstrip('/')}/files/{key}"


def create_app() -> Flask:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_MB * 1024 * 1024

    @app.after_request
    def add_cors_headers(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    @app.route("/api/v1/files", methods=["OPTIONS"])
    @app.route("/api/v1/files/copy", methods=["OPTIONS"])
    def options() -> tuple:
        return ("", 204)

    @app.get("/health")
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200

    @app.post("/api/v1/files")
    def upload_file() -> tuple:
        if "file" not in request.files:
            return jsonify({"error": "multipart form-data field 'file' is required"}), 400

        upload = request.files["file"]
        if not upload.filename:
            return jsonify({"error": "uploaded file name is empty"}), 400
        if not _is_png(upload):
            return jsonify({"error": "only PNG files are allowed"}), 400

        key = _new_key(".png")
        target = _safe_path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        upload.save(target)

        return jsonify({"key": key, "url": _public_url(key)}), 201

    @app.post("/api/v1/files/copy")
    def copy_file() -> tuple:
        payload = request.get_json(silent=True) or {}
        source_key = str(payload.get("source_key", "")).strip()
        if not source_key:
            return jsonify({"error": "source_key is required"}), 400

        try:
            source = _safe_path(source_key)
        except ValueError:
            return jsonify({"error": "invalid source_key"}), 400
        if not source.exists():
            return jsonify({"error": "source file not found"}), 404

        target_key = str(payload.get("target_key", "")).strip() or _new_key(source.suffix or ".png")
        try:
            target = _safe_path(target_key)
        except ValueError:
            return jsonify({"error": "invalid target_key"}), 400
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

        return jsonify({"key": target_key, "url": _public_url(target_key)}), 201

    @app.get("/files/<path:key>")
    def get_file(key: str):
        try:
            file_path = _safe_path(key)
        except ValueError:
            return jsonify({"error": "invalid key"}), 400
        if not file_path.exists():
            return jsonify({"error": "file not found"}), 404
        return send_file(file_path)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=HOST, port=PORT, debug=False)

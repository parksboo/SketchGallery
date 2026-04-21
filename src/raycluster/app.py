from __future__ import annotations

import sys
from threading import Thread
from pathlib import Path

from flask import Flask, jsonify, request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from raycluster.config import settings
from raycluster.generation import GenerationError, build_generation_prompt, run_generation


def _authorized() -> bool:
    token = settings.ray_shared_token.strip()
    if not token:
        return True
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {token}"


def create_app() -> Flask:
    app = Flask(__name__)

    def _run_generation_background(
        *,
        sketch_key: str,
        result_key: str,
        callback_url: str,
        callback_token: str,
        final_prompt: str,
        mode: str,
        job_id: str,
    ) -> None:
        try:
            run_generation(
                sketch_key=sketch_key,
                result_key=result_key,
                callback_url=callback_url,
                callback_token=callback_token,
                final_prompt=final_prompt,
                mode=mode,
            )
        except GenerationError as exc:
            app.logger.error("background generation failed job_id=%s error=%s", job_id, exc)

    @app.get("/health")
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200

    @app.post("/generate")
    def generate() -> tuple:
        if not _authorized():
            return jsonify({"error": "unauthorized"}), 401

        payload = request.get_json(silent=True) or {}
        job_id = str(payload.get("job_id", "")).strip()
        sketch_key = str(payload.get("sketch_key", "")).strip()
        result_key = str(payload.get("result_key", "")).strip()
        callback_url = str(payload.get("callback_url", "")).strip()
        callback_token = str(payload.get("callback_token", "")).strip()
        prompt = str(payload.get("prompt", "")).strip()
        style = str(payload.get("style", "Cinematic")).strip() or "Cinematic"
        title = str(payload.get("title", "Untitled Artwork")).strip() or "Untitled Artwork"
        mode = str(payload.get("mode", "test")).strip() or "test"

        if not job_id:
            return jsonify({"error": "job_id is required"}), 400
        if not sketch_key:
            return jsonify({"error": "sketch_key is required"}), 400
        if not result_key:
            return jsonify({"error": "result_key is required"}), 400

        final_prompt = build_generation_prompt(
            title=title,
            user_prompt=prompt,
            style=style,
        )

        Thread(
            target=_run_generation_background,
            kwargs={
                "sketch_key": sketch_key,
                "result_key": result_key,
                "callback_url": callback_url,
                "callback_token": callback_token,
                "final_prompt": final_prompt,
                "mode": mode,
                "job_id": job_id,
            },
            daemon=True,
        ).start()

        return (
            jsonify(
                {
                    "job_id": job_id,
                    "status": "accepted",
                    "result_key": result_key,
                }
            ),
            202,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=settings.host, port=settings.port, debug=False)

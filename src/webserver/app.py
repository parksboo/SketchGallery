from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from webserver.config import settings
from webserver.repositories.postgres import PostgresRepository
from webserver.routes.api import api_bp
from webserver.routes.ui import ui_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(settings.templates_dir),
        static_folder=str(settings.static_dir),
        static_url_path="/static",
    )
    app.config["MAX_CONTENT_LENGTH"] = settings.max_content_mb * 1024 * 1024

    repo = PostgresRepository()
    repo.init_schema()
    app.extensions["repo"] = repo

    app.register_blueprint(ui_bp)
    app.register_blueprint(api_bp)

    @app.get("/health")
    def root_health() -> tuple:
        return jsonify({"status": "ok"}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=settings.host, port=settings.port, debug=False)

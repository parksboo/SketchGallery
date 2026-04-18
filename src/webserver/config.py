from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "5050"))
    max_content_mb: int = int(os.getenv("MAX_CONTENT_MB", "15"))

    project_root: Path = Path(__file__).resolve().parents[2]
    database_url: str = os.getenv("DATABASE_URL", "")
    pg_host: str = os.getenv("PGHOST", "postgres")
    pg_port: int = int(os.getenv("PGPORT", "5432"))
    pg_db: str = os.getenv("PGDATABASE", "sketchgallery")
    pg_user: str = os.getenv("PGUSER", "sketchgallery")
    pg_password: str = os.getenv("PGPASSWORD", "sketchgallery")
    dataplane_internal_url: str = os.getenv("DATAPLANE_INTERNAL_URL", "http://sketchgallery-dataplane:8080")
    dataplane_public_url: str = os.getenv("DATAPLANE_PUBLIC_URL", "http://127.0.0.1:8080")

    @property
    def templates_dir(self) -> Path:
        # Reuse existing frontend templates.
        return self.project_root / "src" / "frontend" / "templates"

    @property
    def static_dir(self) -> Path:
        # Reuse existing frontend static files.
        return self.project_root / "src" / "frontend" / "static"


settings = Settings()

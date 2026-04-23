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

    gcs_bucket: str = os.getenv("GCS_BUCKET", "")
    gcs_upload_url_expire_sec: int = int(os.getenv("GCS_UPLOAD_URL_EXPIRE_SEC", "600"))
    gcs_download_url_expire_sec: int = int(
        os.getenv("GCS_DOWNLOAD_URL_EXPIRE_SEC", "600")
    )
    ray_generation_url: str = os.getenv("RAY_GENERATION_URL", "")
    ray_request_timeout_sec: int = int(os.getenv("RAY_REQUEST_TIMEOUT_SEC", "20"))
    ray_shared_token: str = os.getenv("RAY_SHARED_TOKEN", "")
    web_public_base_url: str = os.getenv("WEB_PUBLIC_BASE_URL", "")
    default_generation_mode: str = os.getenv("DEFAULT_GENERATION_MODE", "test")

    @property
    def templates_dir(self) -> Path:
        return self.project_root / "src" / "frontend" / "templates"

    @property
    def static_dir(self) -> Path:
        return self.project_root / "src" / "frontend" / "static"


settings = Settings()

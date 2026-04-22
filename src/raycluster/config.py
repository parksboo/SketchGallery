from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    gcs_bucket: str = os.getenv("GCS_BUCKET", "")
    ray_shared_token: str = os.getenv("RAY_SHARED_TOKEN", "")
    callback_timeout_sec: int = int(os.getenv("CALLBACK_TIMEOUT_SEC", "30"))
    ray_address: str = os.getenv("RAY_ADDRESS", "")
    ray_namespace: str = os.getenv("RAY_NAMESPACE", "sketchgallery")
    ray_get_timeout_sec: int = int(os.getenv("RAY_GET_TIMEOUT_SEC", "300"))
    hf_provider: str = os.getenv("HF_PROVIDER", "replicate")
    hf_model: str = os.getenv("HF_MODEL", "black-forest-labs/FLUX.2-dev")
    hf_token_env: str = os.getenv("HF_TOKEN_ENV", "HF_TOKEN")


settings = Settings()

from __future__ import annotations

import uuid
from datetime import timedelta
from functools import lru_cache
from typing import Dict

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import storage

from webserver.config import settings


class StorageError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _client() -> storage.Client:
    try:
        return storage.Client()
    except DefaultCredentialsError as exc:
        raise StorageError(
            "GCP credentials are not configured. Set GOOGLE_APPLICATION_CREDENTIALS "
            "or use Workload Identity."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise StorageError(f"failed to initialize GCS client: {exc}") from exc


def _bucket() -> storage.Bucket:
    if not settings.gcs_bucket:
        raise StorageError("GCS_BUCKET is not configured")
    return _client().bucket(settings.gcs_bucket)


def _ensure_png_filename(filename: str) -> None:
    if not filename.lower().endswith(".png"):
        raise StorageError("only PNG files are allowed")


def issue_upload_url(filename: str, purpose: str = "sketches") -> Dict[str, str]:
    _ensure_png_filename(filename)

    purpose = purpose.strip() or "sketches"
    object_key = f"{purpose}/{uuid.uuid4()}.png"
    blob = _bucket().blob(object_key)

    try:
        upload_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=settings.gcs_upload_url_expire_sec),
            method="PUT",
            content_type="image/png",
        )
    except Exception as exc:  # noqa: BLE001
        raise StorageError(f"failed to issue signed upload url: {exc}") from exc

    return {
        "upload_url": upload_url,
        "object_key": object_key,
        "content_type": "image/png",
        "expires_in": str(settings.gcs_upload_url_expire_sec),
    }


def issue_download_url(object_key: str) -> str:
    blob = _bucket().blob(object_key)
    try:
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=settings.gcs_download_url_expire_sec),
            method="GET",
        )
    except Exception as exc:  # noqa: BLE001
        raise StorageError(f"failed to issue signed download url: {exc}") from exc


def copy_object(source_key: str, target_key: str) -> Dict[str, str]:
    bucket = _bucket()
    source_blob = bucket.blob(source_key)

    try:
        bucket.copy_blob(source_blob, bucket, target_key)
    except Exception as exc:  # noqa: BLE001
        raise StorageError(f"failed to copy GCS object: {exc}") from exc

    return {
        "key": target_key,
        "url": issue_download_url(target_key),
    }

from __future__ import annotations

from functools import lru_cache

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import storage

from raycluster.config import settings


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


def set_bucket() -> storage.Bucket:
    if not settings.gcs_bucket:
        raise StorageError("GCS_BUCKET is not configured")
    return _client().bucket(settings.gcs_bucket)


def copy_object(source_key: str, target_key: str) -> None:
    bucket = set_bucket()
    source_blob = bucket.blob(source_key)

    try:
        bucket.copy_blob(source_blob, bucket, target_key)
    except Exception as exc:  # noqa: BLE001
        raise StorageError(f"failed to copy GCS object: {exc}") from exc


def read_object_bytes(object_key: str) -> bytes:
    bucket = set_bucket()
    blob = bucket.blob(object_key)
    try:
        return blob.download_as_bytes()
    except Exception as exc:  # noqa: BLE001
        raise StorageError(f"failed to read GCS object '{object_key}': {exc}") from exc


def write_object_bytes(object_key: str, data: bytes, content_type: str = "image/png") -> None:
    bucket = set_bucket()
    blob = bucket.blob(object_key)
    try:
        blob.upload_from_string(data, content_type=content_type)
    except Exception as exc:  # noqa: BLE001
        raise StorageError(f"failed to write GCS object '{object_key}': {exc}") from exc

from __future__ import annotations

from typing import Dict

import requests

from webserver.config import settings


class DataPlaneError(RuntimeError):
    pass


def upload_endpoint() -> str:
    return f"{settings.dataplane_public_url.rstrip('/')}/api/v1/files"


def file_url(file_key: str) -> str:
    return f"{settings.dataplane_public_url.rstrip('/')}/files/{file_key}"


def copy_file(source_key: str) -> Dict[str, str]:
    url = f"{settings.dataplane_internal_url.rstrip('/')}/api/v1/files/copy"
    try:
        res = requests.post(url, json={"source_key": source_key}, timeout=10)
    except requests.RequestException as exc:  # noqa: BLE001
        raise DataPlaneError(f"failed to call dataplane copy API: {exc}") from exc

    if res.status_code >= 400:
        raise DataPlaneError(f"dataplane copy API failed with status={res.status_code}: {res.text}")

    payload = res.json()
    return {
        "key": payload["key"],
        "url": payload.get("url", file_url(payload["key"])),
    }

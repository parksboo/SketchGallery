from __future__ import annotations

import json
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from webserver.config import settings


class GenerationDispatchError(RuntimeError):
    pass


def dispatch_generation_job(
    *,
    job_id: str,
    sketch_key: str,
    result_key: str,
    title: str,
    prompt: str,
    style: str,
    mode: str,
) -> Dict[str, Any]:
    endpoint = settings.ray_generation_url.strip()
    if not endpoint:
        raise GenerationDispatchError(
            "RAY_GENERATION_URL is not configured (use external Ray cluster endpoint)"
        )

    payload = {
        "job_id": job_id,
        "sketch_key": sketch_key,
        "result_key": result_key,
        "title": title,
        "prompt": prompt,
        "style": style,
        "mode": mode,
    }

    public_base = settings.web_public_base_url.strip().rstrip("/")
    if public_base:
        payload["callback_url"] = (
            f"{public_base}/api/v1/internal/ray/jobs/{job_id}/result"
        )

    headers = {"Content-Type": "application/json"}
    if settings.ray_shared_token:
        headers["Authorization"] = f"Bearer {settings.ray_shared_token}"
        payload["callback_token"] = settings.ray_shared_token

    body = json.dumps(payload).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.ray_request_timeout_sec) as response:
            status = int(getattr(response, "status", 200))
            raw = response.read().decode("utf-8", errors="replace").strip()
            data: Dict[str, Any] = {}
            if raw:
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        data = parsed
                    else:
                        data = {"raw": parsed}
                except json.JSONDecodeError:
                    data = {"raw": raw}
            if status < 200 or status >= 300:
                raise GenerationDispatchError(
                    f"ray dispatch failed with status={status}, body={raw or '<empty>'}"
                )
            return data
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace").strip()
        raise GenerationDispatchError(
            f"ray dispatch http error status={exc.code}, body={raw or '<empty>'}"
        ) from exc
    except URLError as exc:
        raise GenerationDispatchError(
            f"ray dispatch connection error: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise GenerationDispatchError("ray dispatch timed out") from exc

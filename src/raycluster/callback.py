from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from raycluster.config import settings


class CallbackError(RuntimeError):
    pass


def send_callback(
    *,
    callback_url: str,
    callback_token: str,
    status: str,
    result_key: str = "",
    error: str = "",
) -> None:
    if not callback_url:
        raise CallbackError("callback_url is empty")

    payload: dict[str, str] = {"status": status}
    if status == "completed":
        payload["result_key"] = result_key
    if status == "failed":
        payload["error"] = error or "ray generation failed"

    token = callback_token.strip() or settings.ray_shared_token.strip()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(
        callback_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(req, timeout=settings.callback_timeout_sec) as resp:
            status_code = int(getattr(resp, "status", 200))
            if status_code < 200 or status_code >= 300:
                raw = resp.read().decode("utf-8", errors="replace")
                raise CallbackError(f"callback failed status={status_code} body={raw}")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise CallbackError(f"callback http error status={exc.code} body={raw}") from exc
    except URLError as exc:
        raise CallbackError(f"callback connection error: {exc.reason}") from exc

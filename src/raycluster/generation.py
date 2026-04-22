from __future__ import annotations

import os
from io import BytesIO
from threading import Lock

import ray
from huggingface_hub import InferenceClient
from ray.exceptions import GetTimeoutError

from raycluster.callback import CallbackError, send_callback
from raycluster.config import settings
from raycluster.storage import StorageError, copy_object, read_object_bytes, write_object_bytes


class GenerationError(RuntimeError):
    pass


_init_lock = Lock()
_ray_ready = False

_STYLE_DIRECTIVES = {
    "cinematic": (
        "cinematic composition, dramatic lighting, volumetric fog, high dynamic range, "
        "rich color grading, realistic textures, shallow depth of field"
    ),
    "fantasy matte": (
        "epic fantasy matte painting, grand environment scale, atmospheric perspective, "
        "golden-hour light, painterly yet detailed surfaces, magical ambience"
    ),
    "illustration": (
        "editorial digital illustration, clean stylized shapes, controlled outlines, "
        "harmonized palette, readable silhouette, balanced negative space"
    ),
    "retro poster": (
        "retro print poster aesthetic, limited vintage palette, halftone grain, "
        "high-contrast blocks, bold composition, subtle paper texture"
    ),
}


def build_generation_prompt(*, title: str, user_prompt: str, style: str) -> str:
    resolved_title = (title or "Untitled Artwork").strip()
    resolved_prompt = (user_prompt or "").strip()
    style_key = _normalize_style(style)
    style_directive = _STYLE_DIRECTIVES.get(
        style_key,
        "high-quality artistic rendering, coherent composition, detailed lighting and material response",
    )

    return (
        f"Title: {resolved_title}\n"
        f"Primary concept: {resolved_prompt or 'Interpret the sketch into a complete scene.'}\n"
        f"Style target: {style or 'Cinematic'}\n"
        f"Style guidance: {style_directive}\n"
        "Output requirements: preserve the sketch intent, keep strong focal hierarchy, "
        "avoid artifacts, avoid text/watermarks, final image should look gallery-ready."
    )


def _normalize_style(style: str) -> str:
    normalized = (style or "").strip().lower()
    normalized = normalized.replace("_", " ")
    return " ".join(normalized.split())


@ray.remote
def generate_image_remote(
    *,
    sketch_key: str,
    result_key: str,
    final_prompt: str,
    mode: str,
) -> dict[str, str]:
    # Placeholder generation workload.
    if mode == "test":
        copy_object(sketch_key, result_key)
    else:
        _call_api(sketch_key=sketch_key, result_key=result_key, final_prompt=final_prompt)

    return {
        "status": "completed",
        "result_key": result_key,
    }


def run_generation(
    *,
    sketch_key: str,
    result_key: str,
    callback_url: str,
    callback_token: str,
    final_prompt: str,
    mode: str,
) -> None:
    _ensure_ray_initialized()

    try:
        obj_ref = generate_image_remote.remote(
            sketch_key=sketch_key,
            result_key=result_key,
            final_prompt=final_prompt,
            mode=mode,
        )
        result = ray.get(obj_ref, timeout=settings.ray_get_timeout_sec)
        completed_key = str(result.get("result_key", result_key))

        send_callback(
            callback_url=callback_url,
            callback_token=callback_token,
            status="completed",
            result_key=completed_key,
        )
    except GetTimeoutError as exc:
        _try_failed_callback(
            callback_url=callback_url,
            callback_token=callback_token,
            error=f"ray.get timeout after {settings.ray_get_timeout_sec}s",
        )
        raise GenerationError("ray.get timed out") from exc
    except (StorageError, CallbackError, RuntimeError) as exc:
        _try_failed_callback(callback_url=callback_url, callback_token=callback_token, error=str(exc))
        raise GenerationError(str(exc)) from exc


def _ensure_ray_initialized() -> None:
    global _ray_ready

    if _ray_ready:
        return

    with _init_lock:
        if _ray_ready:
            return
        if ray.is_initialized():
            _ray_ready = True
            return

        try:
            ray.init(address=settings.ray_address, namespace=settings.ray_namespace, ignore_reinit_error=True)
        except Exception as exc:  # noqa: BLE001
            raise GenerationError(f"failed to initialize ray: {exc}") from exc
        _ray_ready = True


def _try_failed_callback(*, callback_url: str, callback_token: str, error: str) -> None:
    try:
        send_callback(
            callback_url=callback_url,
            callback_token=callback_token,
            status="failed",
            error=error,
        )
    except CallbackError:
        pass


def _call_api(*, sketch_key: str, result_key: str, final_prompt: str) -> None:
    token = os.getenv(settings.hf_token_env, "").strip()
    if not token:
        raise GenerationError(
            f"missing Hugging Face token env '{settings.hf_token_env}'. "
            "Set it in Ray runtime environment."
        )

    input_image = read_object_bytes(sketch_key)
    client = InferenceClient(
        provider=settings.hf_provider,
        api_key=token,
    )

    image = client.image_to_image(
        image = input_image,
        prompt=final_prompt,
        model=settings.hf_model,
    )

    output = BytesIO()
    image.save(output, format="PNG")
    write_object_bytes(result_key, output.getvalue(), content_type="image/png")

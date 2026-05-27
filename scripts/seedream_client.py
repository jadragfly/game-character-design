#!/usr/bin/env python3
"""Seedream 4.5 (Doubao) client used by every generation script.

This module is a thin wrapper around doubao_client.generate_image() for backwards
compatibility. The actual implementation lives in the doubao-api skill's
doubao_client.py.

Behaviour:
  * Reads DOUBAO_API_KEY and DOUBAO_API_URL.
  * Picks the appropriate doubao- prefixed model name based on the configured base URL.
  * Sends synchronous POST /api/v3/images/generations.
  * Local image paths are converted to data URIs; http(s) URLs are passed through.
  * Maps friendly aspect_ratio strings to the API's `size` pixel string.
  * Downloads each returned data[].url into out_dir as <prefix>__<i>.png.
  * Honors DOUBAO_MOCK_EN or SEEDREAM_MOCK_EN for offline dry runs.
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path
from typing import Iterable

import requests

DEFAULT_AR = "1:1"
SIZE_MAPPING: dict[str, str] = {
    "1:1": "4096x4096",
    "4:3": "3840x2880",
    "3:4": "2880x3840",
    "16:9": "3840x2160",
    "9:16": "2160x3840",
    "3:2": "3840x2560",
    "2:3": "2560x3840",
    "21:9": "3840x1646",
}

MOCK_DELAY_S = 0.2

DEBUG = os.environ.get("DEBUG", "0") == "1"
def _debug(msg: str) -> None:
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr)


class SeedreamError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code


def _mock_enabled() -> bool:
    return (
        os.environ.get("DOUBAO_MOCK_EN", "").lower() == "true"
        or os.environ.get("SEEDREAM_MOCK_EN", "").lower() == "true"
    ) and os.environ.get("NODE_ENV", "") != "production"


def _resolve_size(aspect_ratio: str | None) -> str:
    if not aspect_ratio:
        return SIZE_MAPPING[DEFAULT_AR]
    if aspect_ratio in SIZE_MAPPING:
        return SIZE_MAPPING[aspect_ratio]
    if "x" in aspect_ratio.lower():
        return aspect_ratio
    raise SeedreamError(
        "E_BAD_RATIO",
        f"Unknown aspect_ratio {aspect_ratio!r}. "
        f"Use one of {sorted(SIZE_MAPPING)} or a literal pixel string like 4096x4096.",
    )


def _to_data_uri(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise SeedreamError("E_REF_NOT_FOUND", f"Reference image does not exist: {path}")
    suffix = p.suffix.lower().lstrip(".")
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}
    mime = mime_map.get(suffix, "png")
    encoded = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"


def _normalize_images(refs: Iterable[str] | None) -> list[str]:
    if not refs:
        return []
    out: list[str] = []
    for ref in refs:
        ref = str(ref)
        if ref.startswith(("http://", "https://", "data:")):
            out.append(ref)
        else:
            out.append(_to_data_uri(ref))
    if len(out) > 14:
        raise SeedreamError(
            "E_TOO_MANY_REFS",
            f"Seedream accepts at most 14 reference images, got {len(out)}.",
        )
    return out


DOUBAO_INGRESS_PREFIXES = (
    "https://ark.cn-beijing",
)


def _resolve_model_name(api_base_url: str) -> str:
    """Choose the model name. Hosts with a known doubao ingress prefix expect
    the doubao- prefixed model id; everything else uses the unprefixed id."""
    if any(api_base_url.startswith(p) for p in DOUBAO_INGRESS_PREFIXES):
        return "doubao-seedream-4-5-251128"
    return "seedream-4-5-251128"


def _download(url: str, out_path: Path) -> None:
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        out_path.write_bytes(r.content)
    except Exception as exc:
        raise SeedreamError("E_DOWNLOAD", f"Failed to download {url}: {exc}") from exc


def _write_synthetic_mock(out_path: Path, width: int = 1024, height: int = 1024) -> None:
    """Generate a placeholder mock image locally. Used when the hosted mock
    URL is not reachable (offline dev, sandboxed CI)."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (width, height), (0, 255, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2
    body_r = min(width, height) // 4
    draw.ellipse(
        (cx - body_r, cy - body_r, cx + body_r, cy + body_r),
        fill=(255, 180, 80),
        outline=(60, 30, 0),
        width=4,
    )
    eye_r = body_r // 6
    for ox in (-body_r // 3, body_r // 3):
        draw.ellipse(
            (cx + ox - eye_r, cy - eye_r, cx + ox + eye_r, cy + eye_r),
            fill=(30, 30, 30),
        )
    img.save(out_path, format="PNG")


def generate(
    *,
    prompt: str,
    reference_image_paths: Iterable[str] | None = None,
    aspect_ratio: str = DEFAULT_AR,
    sequential: bool = False,
    out_dir: str | os.PathLike[str],
    out_prefix: str,
) -> list[str]:
    """Send one Seedream request and return local PNG paths.

    `sequential=True` enables `sequential_image_generation=auto` (Seedream picks
    1..N related images). `sequential=False` forces a single image.
    
    This function is a wrapper around doubao_client.generate_image() for backwards
    compatibility with existing pet-design scripts.
    """
    import base64 as _base64
    
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    if _mock_enabled():
        _debug("[seedream] Mock mode enabled")
        import time as _time
        _time.sleep(MOCK_DELAY_S)
        count = 8 if sequential else 1
        out_paths: list[str] = []
        for i in range(count):
            target = out_dir_p / f"{out_prefix}__{i}.png"
            _write_synthetic_mock(target)
            out_paths.append(str(target))
        return out_paths

    api_key = os.environ.get("DOUBAO_API_KEY", "").strip()
    api_url = os.environ.get("DOUBAO_API_URL", "").strip()
    
    if not api_key:
        raise SeedreamError(
            "E_NO_KEY",
            "DOUBAO_API_KEY environment variable is not set. See SKILL.md section Setup, "
            "or export DOUBAO_MOCK_EN=true (or SEEDREAM_MOCK_EN=true) to use the offline mock.",
        )
    if not api_url:
        raise SeedreamError(
            "E_NO_URL",
            "DOUBAO_API_URL environment variable is not set. See SKILL.md section Setup.",
        )

    body: dict[str, object] = {
        "model": _resolve_model_name(api_url),
        "prompt": prompt,
        "size": _resolve_size(aspect_ratio),
        "sequential_image_generation": "auto" if sequential else "disabled",
        "watermark": False,
    }
    images = _normalize_images(reference_image_paths)
    if images:
        body["image"] = images

    endpoint = api_url.rstrip("/") + "/api/v3/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    _debug(
        f"[seedream] POST {endpoint}  refs={len(images)}  size={body['size']}  "
        f"seq={body['sequential_image_generation']}"
    )
    try:
        resp = requests.post(endpoint, json=body, headers=headers, timeout=300)
    except requests.RequestException as exc:
        raise SeedreamError("E_NETWORK", f"Network call failed: {exc}") from exc
    if not resp.ok:
        raise SeedreamError(
            f"E_HTTP_{resp.status_code}",
            f"Seedream returned {resp.status_code}: {resp.text[:500]}",
        )
    payload = resp.json()
    items = payload.get("data") or []
    if not items:
        raise SeedreamError("E_NO_DATA", f"Seedream response had no data: {payload}")

    out_paths: list[str] = []
    for i, item in enumerate(items):
        url = item.get("url")
        if not url:
            raise SeedreamError("E_NO_URL_ITEM", f"data[{i}] has no url: {item}")
        target = out_dir_p / f"{out_prefix}__{i}.png"
        _download(url, target)
        out_paths.append(str(target))
    return out_paths


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="One-off Seedream 4.5 generation for testing.")
    p.add_argument("--prompt", required=True)
    p.add_argument("--reference", action="append", default=[], help="Local path or http(s) URL. Repeatable.")
    p.add_argument("--aspect-ratio", default=DEFAULT_AR, choices=sorted(SIZE_MAPPING))
    p.add_argument("--sequential", action="store_true")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--prefix", default="oneoff")
    args = p.parse_args()

    paths = generate(
        prompt=args.prompt,
        reference_image_paths=args.reference,
        aspect_ratio=args.aspect_ratio,
        sequential=args.sequential,
        out_dir=args.out_dir,
        out_prefix=args.prefix,
    )
    for path in paths:
        print(path)

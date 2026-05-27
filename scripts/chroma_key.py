#!/usr/bin/env python3
"""Replace the chroma-key background with transparency in every frame PNG.

Operates on frames/<row>_<i>.png in-place. Pixels within HSV tolerance of the
chroma_key color are made fully transparent. A 1-pixel despeckle pass removes
isolated remaining chroma pixels along the silhouette edge.
"""
from __future__ import annotations

import argparse
import colorsys
import sys
from pathlib import Path

from PIL import Image

from _common import ROW_ORDER, GAME_CHARACTER_ROWS, GAME_PLATFORMER_ROWS, load_jobs


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Make chroma-key background transparent.")
    p.add_argument("--run-dir", required=True)
    p.add_argument(
        "--row",
        default="all",
        help='Row to process, or "all".',
    )
    return p.parse_args()


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _rgb_to_hsv(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = (c / 255.0 for c in rgb)
    return colorsys.rgb_to_hsv(r, g, b)


def _key_distance_h(h: float, key_h: float) -> float:
    """Return the absolute hue distance on the [0, 1) circle."""
    d = abs(h - key_h)
    return min(d, 1.0 - d)


def _process(path: Path, key_rgb: tuple[int, int, int], tolerance: int) -> int:
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size

    key_h, key_s, key_v = _rgb_to_hsv(key_rgb)
    h_tol = tolerance / 360.0  # tolerance treated as degrees
    s_tol_min = 0.35
    v_tol_min = 0.35

    removed = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            
            ph, ps, pv = _rgb_to_hsv((r, g, b))
            hue_diff = _key_distance_h(ph, key_h)
            
            # 检测绿色背景（绿色色调 + 高饱和度）
            if hue_diff <= h_tol and ps >= s_tol_min and pv >= v_tol_min:
                pixels[x, y] = (r, g, b, 0)
                removed += 1
            # 检测白色/浅色背景 (高亮度 + 低饱和度)
            elif pv > 0.85 and ps < 0.15:
                pixels[x, y] = (r, g, b, 0)
                removed += 1
            # 检测蓝色背景 (蓝色色调 + 高饱和度 + 高亮度)
            elif hue_diff <= 0.15 and ps >= 0.4 and pv >= 0.5:
                pixels[x, y] = (r, g, b, 0)
                removed += 1
            # 检测灰色/中性色背景 (中等亮度 + 极低饱和度)
            elif pv > 0.4 and pv < 0.75 and ps < 0.1:
                pixels[x, y] = (r, g, b, 0)
                removed += 1
    
    rgba.save(path, format="PNG")
    return removed


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    jobs = load_jobs(run_dir)

    # 根据 animation_mode 选择正确的行顺序
    animation_mode = jobs.get("animation_mode", "pet")
    if animation_mode == "game":
        game_type = jobs.get("game_type", "full")
        if game_type == "platformer":
            all_rows = GAME_PLATFORMER_ROWS
        else:
            all_rows = GAME_CHARACTER_ROWS
    else:
        all_rows = ROW_ORDER

    key_rgb = _hex_to_rgb(jobs.get("chroma_key", "#00FF00"))
    tolerance = int(jobs.get("chroma_tolerance", 30))

    rows = all_rows if args.row == "all" else [args.row]
    total_removed = 0
    processed_rows = 0
    
    for row in rows:
        if row not in jobs.get("jobs", {}):
            print(f"warning: row {row!r} not in jobs, skipping")
            continue
        job = jobs["jobs"][row]
        frames = job.get("frames", [])
        
        row_removed = 0
        for i in range(8):
            path = run_dir / "frames" / f"{row}_{i}.png"
            if not path.exists():
                continue
            removed = _process(path, key_rgb, tolerance)
            row_removed += removed
            total_removed += removed
        
        if row_removed > 0:
            processed_rows += 1
            print(f"[{row}] chroma-key: removed {row_removed} pixels")
    
    print(f"chroma-key pass complete: {processed_rows} rows processed, {total_removed} pixels removed total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

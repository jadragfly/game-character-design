#!/usr/bin/env python3
"""Cut decoded outputs into 8 frames per row at exactly 192x208.

Inputs:
  decoded/<row>__raw__<i>.png   (auto mode -> 1..N separate images)
  decoded/<row>.png             (grid mode -> single image)
Outputs:
  frames/<row>_<0..7>.png       (192x208, RGBA, chroma-key still present)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from _common import CELL_H, CELL_W, ROW_ORDER, GAME_CHARACTER_ROWS, GAME_PLATFORMER_ROWS, load_jobs, save_jobs

GRID_COLS = 4
GRID_ROWS = 2
TARGET_FRAMES = 8


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Slice decoded outputs into 192x208 frames.")
    p.add_argument("--run-dir", required=True)
    p.add_argument(
        "--row",
        default="all",
        help='Row to extract, or "all" for every succeeded row.',
    )
    return p.parse_args()


def _resize_to_cell(img: Image.Image) -> Image.Image:
    """Resize the input so that it fits inside CELL_W x CELL_H, then paste
    centered onto a CELL-sized canvas filled with chroma green so empty area
    is removed by chroma_key downstream."""
    src = img.convert("RGB")
    src.thumbnail((CELL_W, CELL_H), Image.LANCZOS)
    canvas = Image.new("RGB", (CELL_W, CELL_H), (0, 255, 0))
    cx = (CELL_W - src.width) // 2
    cy = (CELL_H - src.height) // 2
    canvas.paste(src, (cx, cy))
    return canvas


def _extract_auto(decoded_paths: list[str], frames_dir: Path, row: str) -> list[Path]:
    paths = [Path(p) for p in decoded_paths]
    if len(paths) >= TARGET_FRAMES:
        chosen = paths[:TARGET_FRAMES]
    else:
        # repeat last frame to pad up to 8
        chosen = paths + [paths[-1]] * (TARGET_FRAMES - len(paths))
    out: list[Path] = []
    for i, p in enumerate(chosen):
        with Image.open(p) as im:
            cell = _resize_to_cell(im)
        target = frames_dir / f"{row}_{i}.png"
        cell.save(target, format="PNG")
        out.append(target)
    return out


def _extract_grid(decoded_path: str, frames_dir: Path, row: str) -> list[Path]:
    out: list[Path] = []
    with Image.open(decoded_path) as im:
        im_rgb = im.convert("RGB")
        cw = im_rgb.width // GRID_COLS
        ch = im_rgb.height // GRID_ROWS
        idx = 0
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                box = (c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)
                tile = im_rgb.crop(box)
                cell = _resize_to_cell(tile)
                target = frames_dir / f"{row}_{idx}.png"
                cell.save(target, format="PNG")
                out.append(target)
                idx += 1
    return out


def _extract_one(run_dir: Path, jobs: dict, row: str) -> bool:
    job = jobs["jobs"][row]
    if job["status"] != "succeeded":
        if job["status"] == "mirrored":
            print(f"[{row}] mirrored row, frames will be produced by chroma_key step.")
            return True
        print(f"[{row}] not succeeded yet (status={job['status']}). Skipping.")
        return False
    decoded = job.get("decoded")
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    if isinstance(decoded, list):
        out = _extract_auto(decoded, frames_dir, row)
    elif isinstance(decoded, str):
        out = _extract_grid(decoded, frames_dir, row)
    else:
        print(f"[{row}] no decoded output available.", file=sys.stderr)
        return False
    job["frames"] = [str(p) for p in out]
    print(f"[{row}] extracted {len(out)} frames")
    return True


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    jobs = load_jobs(run_dir)

    animation_mode = jobs.get("animation_mode", "pet")
    if animation_mode == "pet":
        all_rows = ROW_ORDER
    else:
        game_type = jobs.get("game_type", "full")
        if game_type == "platformer":
            all_rows = GAME_PLATFORMER_ROWS
        else:
            all_rows = GAME_CHARACTER_ROWS

    rows = all_rows if args.row == "all" else [args.row]
    ok = True
    for row in rows:
        if row not in jobs["jobs"]:
            print(f"error: unknown row {row!r}", file=sys.stderr)
            ok = False
            continue
        ok = _extract_one(run_dir, jobs, row) and ok
    save_jobs(run_dir, jobs)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

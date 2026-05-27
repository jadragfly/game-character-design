#!/usr/bin/env python3
"""Compose the 1536x1872 spritesheet atlas from frame PNGs.

Reads frames/<row>_<i>.png for each row (i 0..7) and pastes them into the
correct cell of an RGBA atlas. Missing frames are left transparent. Writes
final/spritesheet.png and final/spritesheet.webp.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from _common import ATLAS_H, ATLAS_W, CELL_H, CELL_W, COLS, ROW_ORDER, GAME_CHARACTER_ROWS, GAME_PLATFORMER_ROWS, load_jobs


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compose 1536x1872 atlas from frames.")
    p.add_argument("--run-dir", required=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    frames_dir = run_dir / "frames"
    final_dir = run_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)

    # 获取正确的行顺序
    jobs = load_jobs(run_dir)
    animation_mode = jobs.get("animation_mode", "pet")
    if animation_mode == "game":
        game_type = jobs.get("game_type", "full")
        if game_type == "platformer":
            row_order = GAME_PLATFORMER_ROWS
        else:
            row_order = GAME_CHARACTER_ROWS
    else:
        row_order = ROW_ORDER

    atlas = Image.new("RGBA", (ATLAS_W, ATLAS_H), (0, 0, 0, 0))
    used = 0
    missing: list[str] = []
    for row_idx, row in enumerate(row_order):
        for col in range(COLS):
            frame_path = frames_dir / f"{row}_{col}.png"
            if not frame_path.exists():
                missing.append(f"{row}_{col}")
                continue
            with Image.open(frame_path) as im:
                cell = im.convert("RGBA")
            if cell.size != (CELL_W, CELL_H):
                cell = cell.resize((CELL_W, CELL_H), Image.LANCZOS)
            atlas.paste(cell, (col * CELL_W, row_idx * CELL_H), cell)
            used += 1

    if used == 0:
        print(
            "error: no frames found. Run generate_row + extract_frames + chroma_key first.",
            file=sys.stderr,
        )
        return 1
    if missing:
        print(
            f"warning: {len(missing)} frames are missing and were left transparent: "
            f"{', '.join(missing[:8])}{'...' if len(missing) > 8 else ''}",
            file=sys.stderr,
        )

    png_path = final_dir / "spritesheet.png"
    webp_path = final_dir / "spritesheet.webp"
    atlas.save(png_path, format="PNG")
    atlas.save(webp_path, format="WEBP", lossless=True, method=6)

    print(f"wrote {png_path} ({ATLAS_W}x{ATLAS_H}, {used}/{COLS * len(row_order)} cells filled)")
    print(f"wrote {webp_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

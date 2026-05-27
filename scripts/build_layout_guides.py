#!/usr/bin/env python3
"""Regenerate the row layout guide PNGs in references/layout-guides/.

Generates guides for both pet animations and game character animations.
Each row gets two guide images:
  <row>__auto.png  -> 8 separate centered slots, side-by-side, used in
                       sequential_image_generation="auto" mode.
  <row>__grid.png  -> a 4-column x 2-row grid, used in the grid fallback mode.

The guides are pale-gray scaffolds on a green chroma-key background. They are
attached to every Seedream row request as a layout-only reference image.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

PET_ROWS = [
    "idle",
    "waving",
    "running-right",
    "running-left",
    "waiting",
    "review",
    "jumping",
    "failed",
    "happy",
]

GAME_CHARACTER_ROWS = [
    "idle",
    "walk-right",
    "walk-left",
    "jump",
    "fall",
    "crouch",
    "attack",
    "shoot",
    "hit",
    "pickup",
    "death",
]

GAME_PLATFORMER_ROWS = [
    "idle",
    "walk-right",
    "walk-left",
    "jump",
    "crouch",
    "attack",
    "pickup",
]

CHROMA_KEY = (0, 255, 0)
SLOT_FILL = (240, 240, 240)
SLOT_OUTLINE = (180, 180, 180)


def build_auto_guide(out_path: Path) -> None:
    """8 frames laid out left-to-right at 21:9-ish ratio (1024x256)."""
    img = Image.new("RGB", (1024, 256), CHROMA_KEY)
    draw = ImageDraw.Draw(img)
    cell_w = 128
    cell_h = 256
    inner_pad = 12
    for i in range(8):
        x0 = i * cell_w + inner_pad
        y0 = inner_pad
        x1 = (i + 1) * cell_w - inner_pad
        y1 = cell_h - inner_pad
        draw.rectangle([x0, y0, x1, y1], fill=SLOT_FILL, outline=SLOT_OUTLINE, width=1)
    img.save(out_path, format="PNG")


def build_grid_guide(out_path: Path) -> None:
    """4 columns x 2 rows grid at 16:9-ish (1024x576)."""
    img = Image.new("RGB", (1024, 576), CHROMA_KEY)
    draw = ImageDraw.Draw(img)
    cols, rows = 4, 2
    cell_w = 1024 // cols
    cell_h = 576 // rows
    inner_pad = 16
    for r in range(rows):
        for c in range(cols):
            x0 = c * cell_w + inner_pad
            y0 = r * cell_h + inner_pad
            x1 = (c + 1) * cell_w - inner_pad
            y1 = (r + 1) * cell_h - inner_pad
            draw.rectangle([x0, y0, x1, y1], fill=SLOT_FILL, outline=SLOT_OUTLINE, width=1)
    img.save(out_path, format="PNG")


def parse_args() -> argparse.Namespace:
    import argparse
    p = argparse.ArgumentParser(description="Build layout guide PNGs for pet and game animations.")
    p.add_argument(
        "--mode",
        default="all",
        choices=["pet", "game", "game-platformer", "all"],
        help="Which layout guides to build.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    here = Path(__file__).resolve().parent
    skill_root = here.parent

    total_guides = 0

    if args.mode in ("pet", "all"):
        target = skill_root / "references" / "layout-guides"
        target.mkdir(parents=True, exist_ok=True)
        for row in PET_ROWS:
            build_auto_guide(target / f"{row}__auto.png")
            build_grid_guide(target / f"{row}__grid.png")
        total_guides += len(PET_ROWS) * 2
        print(f"wrote {len(PET_ROWS) * 2} pet layout guides to {target}")

    if args.mode in ("game", "game-platformer", "all"):
        target = skill_root / "references" / "layout-guides" / "game"
        target.mkdir(parents=True, exist_ok=True)
        
        if args.mode in ("game", "all"):
            rows = GAME_CHARACTER_ROWS
        else:
            rows = GAME_PLATFORMER_ROWS
        
        for row in rows:
            build_auto_guide(target / f"{row}__auto.png")
            build_grid_guide(target / f"{row}__grid.png")
        total_guides += len(rows) * 2
        print(f"wrote {len(rows) * 2} game layout guides to {target}")

    print(f"total: {total_guides} layout guide files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

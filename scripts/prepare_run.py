#!/usr/bin/env python3
"""Prepare a fresh pet-design or game-character run directory: jobs.json manifest plus the
expected sub-directory layout.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from _common import (
    ROW_ORDER,
    GAME_CHARACTER_ROWS,
    GAME_PLATFORMER_ROWS,
    save_jobs,
    slugify,
)

VALID_STYLES_PET = ["codex-pixel", "anime", "animal", "original"]
VALID_STYLES_GAME = ["platformer-16bit", "platformer-indie", "platformer-chibi", "platformer-anime"]
VALID_CATEGORIES_PET = ["Anime Characters", "Animals", "Original Characters"]
VALID_CATEGORIES_GAME = ["Platform Games", "Fighting Games", "Action Adventure", "RPG", "Shooters"]

ANIMATION_MODE_CHOICES = ["pet", "game"]
GAME_TYPE_CHOICES = ["full", "platformer"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Prepare a pet-design or game-character run directory with jobs.json and layout."
    )
    p.add_argument(
        "--animation-mode",
        default="pet",
        choices=ANIMATION_MODE_CHOICES,
        help="'pet' for pet animations, 'game' for game character animations.",
    )
    p.add_argument("--character-name", required=True, help='Display name, e.g. "Mario" or "Codex".')
    p.add_argument("--description", required=True, help="One-sentence character/pet description.")
    p.add_argument(
        "--style",
        default=None,
        help="Visual style preset. Auto-selected based on animation-mode if not specified.",
    )
    p.add_argument(
        "--category",
        default=None,
        help="Category for the character. Auto-selected based on animation-mode if not specified.",
    )
    p.add_argument(
        "--reference",
        action="append",
        default=[],
        help="User reference image (local path or URL). Repeatable.",
    )
    p.add_argument(
        "--output-dir",
        required=True,
        help="Where to create the run directory (will be created).",
    )
    p.add_argument(
        "--mode",
        default="grid",
        choices=["auto", "grid"],
        help="Default per-row generation mode (overridable on each generate_row call).",
    )
    p.add_argument(
        "--chroma-key",
        default="#00FF00",
        help="Chroma key color (must match the prompt). Hex.",
    )
    p.add_argument(
        "--chroma-tolerance",
        type=int,
        default=30,
        help="HSV tolerance used by chroma_key.py (0-60).",
    )
    p.add_argument(
        "--game-type",
        default="full",
        choices=GAME_TYPE_CHOICES,
        help="Game type preset (only for animation-mode=game): 'full' includes all game actions, 'platformer' is a simplified set.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing run directory.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = Path(args.output_dir).resolve()
    if run_dir.exists() and not args.force:
        print(
            f"error: {run_dir} already exists. Use --force to overwrite, or pick a new path.",
            file=sys.stderr,
        )
        return 2
    if run_dir.exists() and args.force:
        shutil.rmtree(run_dir)

    for sub in ("decoded", "frames", "final", "qa", "qa/videos", "prompts", "references"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    user_refs: list[str] = []
    for ref in args.reference:
        ref_path = Path(ref)
        if ref_path.is_file():
            target = run_dir / "references" / ref_path.name
            shutil.copy2(ref_path, target)
            user_refs.append(str(target))
        else:
            user_refs.append(ref)

    animation_mode = args.animation_mode
    if animation_mode == "pet":
        row_order = ROW_ORDER
        valid_styles = VALID_STYLES_PET
        valid_categories = VALID_CATEGORIES_PET
        style_default = "codex-pixel"
        category_default = "Original Characters"
    else:
        if args.game_type == "platformer":
            row_order = GAME_PLATFORMER_ROWS
        else:
            row_order = GAME_CHARACTER_ROWS
        valid_styles = VALID_STYLES_GAME
        valid_categories = VALID_CATEGORIES_GAME
        style_default = "platformer-16bit"
        category_default = "Platform Games"

    style = args.style or style_default
    category = args.category or category_default

    jobs: dict[str, dict] = {
        "base": {"status": "pending", "mode": args.mode, "decoded": None, "error": None}
    }
    for row in row_order:
        entry: dict = {
            "status": "pending",
            "mode": args.mode,
            "decoded": None,
            "error": None,
        }
        if animation_mode == "game" and row in ("walk-left",):
            entry["derive_from_mirror"] = False
        jobs[row] = entry

    manifest = {
        "animation_mode": animation_mode,
        "game_type": args.game_type if animation_mode == "game" else None,
        "character_name": args.character_name,
        "slug": slugify(args.character_name),
        "description": args.description,
        "style": style,
        "category": category,
        "chroma_key": args.chroma_key,
        "chroma_tolerance": args.chroma_tolerance,
        "user_references": user_refs,
        "jobs": jobs,
    }
    save_jobs(run_dir, manifest)

    print(f"prepared run at {run_dir}")
    print(f"  animation_mode = {animation_mode}")
    print(f"  game_type       = {args.game_type if animation_mode == 'game' else 'N/A'}")
    print(f"  character_name  = {args.character_name}")
    print(f"  slug            = {manifest['slug']}")
    print(f"  style           = {style}")
    print(f"  category        = {category}")
    print(f"  rows            = {len(row_order)} actions")
    print(f"  refs            = {len(user_refs)}")
    
    if animation_mode == "pet":
        print("next: python scripts/generate_base.py --run-dir " + str(run_dir))
    else:
        print("next: python scripts/generate_base.py --run-dir " + str(run_dir))
        print(f"  game rows: {', '.join(row_order)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

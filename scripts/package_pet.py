#!/usr/bin/env python3
"""Write character.json + spritesheet.webp into final folder.

Default output: <run-dir>/final/<character.json, spritesheet.webp>.
With --output-dir, also copy to that directory.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from _common import (
    ATLAS_H, ATLAS_W, CELL_H, CELL_W, COLS,
    ROW_ORDER, GAME_CHARACTER_ROWS, GAME_PLATFORMER_ROWS,
    load_jobs, slugify
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Package character.json + spritesheet.webp.")
    p.add_argument("--run-dir", required=True)
    p.add_argument(
        "--slug",
        default=None,
        help="Character slug. Defaults to slug(character_name).",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        help="Optional. If set, also copy to that directory.",
    )
    return p.parse_args()


def build_animations(animation_mode: str, game_type: str) -> dict:
    """构建动画配置"""
    if animation_mode == "game":
        if game_type == "platformer":
            rows = GAME_PLATFORMER_ROWS
        else:
            rows = GAME_CHARACTER_ROWS
    else:
        rows = ROW_ORDER
    
    animations = {}
    row_to_anim = {
        "idle": "idle",
        "walk-right": "walk-right",
        "walk-left": "walk-left",
        "jump": "jump",
        "fall": "fall",
        "crouch": "crouch",
        "attack": "attack",
        "shoot": "shoot",
        "hit": "hit",
        "pickup": "pickup",
        "death": "death",
        "waving": "waving",
        "running-right": "run-right",
        "running-left": "run-left",
        "waiting": "wait",
        "review": "review",
        "jumping": "jump",
        "failed": "fail",
        "happy": "happy",
    }
    
    for i, row in enumerate(rows):
        anim_name = row_to_anim.get(row, row)
        num_frames = 8
        if row in ["crouch", "attack", "shoot", "hit", "pickup", "death", "failed"]:
            num_frames = 6
        
        animations[anim_name] = {
            "row": i,
            "startFrame": 0,
            "endFrame": num_frames - 1,
            "frames": num_frames,
            "loop": row not in ["crouch", "attack", "shoot", "hit", "pickup", "death", "failed"]
        }
    
    return animations


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    jobs = load_jobs(run_dir)

    spritesheet = run_dir / "final" / "spritesheet.webp"
    if not spritesheet.exists():
        print(
            f"error: {spritesheet} not found. Run compose_atlas.py first.",
            file=sys.stderr,
        )
        return 1

    animation_mode = jobs.get("animation_mode", "pet")
    game_type = jobs.get("game_type", "full")
    
    if animation_mode == "game":
        if game_type == "platformer":
            row_order = GAME_PLATFORMER_ROWS
        else:
            row_order = GAME_CHARACTER_ROWS
    else:
        row_order = ROW_ORDER
    
    slug = args.slug or slugify(jobs["character_name"])
    
    # 构建完整的 character.json
    character_json = {
        "id": slug,
        "name": jobs.get("character_name"),
        "description": jobs.get("description"),
        "style": jobs.get("style"),
        "category": jobs.get("category"),
        "spritesheetPath": "spritesheet.webp",
        "frameWidth": CELL_W,
        "frameHeight": CELL_H,
        "columns": COLS,
        "atlasWidth": ATLAS_W,
        "atlasHeight": ATLAS_H,
        "animationMode": animation_mode,
        "gameType": game_type,
        "animations": build_animations(animation_mode, game_type),
        "rows": row_order,
    }

    final_dir = run_dir / "final"
    char_path = final_dir / "character.json"
    char_path.write_text(json.dumps(character_json, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {char_path}")
    print(f"wrote {spritesheet}")

    if args.output_dir:
        target = Path(args.output_dir).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spritesheet, target / "spritesheet.webp")
        (target / "character.json").write_text(
            json.dumps(character_json, indent=2, ensure_ascii=False) + "\n"
        )
        print(f"installed character to {target}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

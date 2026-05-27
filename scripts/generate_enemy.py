#!/usr/bin/env python3
"""Generate enemy sprites with simple animations.

Enemy sprites typically need fewer animations than player characters:
- idle (8 frames)
- walk (8 frames)  
- attack (4 frames)
- death (4 frames)

This generates a smaller sprite sheet suitable for enemies.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

from _common import (
    CELL_H, CELL_W, COLS,
    load_jobs, save_jobs, slugify
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate enemy sprite with simple animations.")
    p.add_argument("--run-dir", required=True, help="Run directory from prepare_run.py")
    p.add_argument("--output-dir", required=True, help="Output directory for enemy sprites")
    p.add_argument("--enemy-name", required=True, help="Enemy character name")
    p.add_argument("--enemy-desc", required=True, help="Enemy description")
    return p.parse_args()


def get_enemy_rows() -> list[str]:
    """Get the standard enemy animation rows."""
    return ["idle", "walk", "attack", "death"]


def calculate_enemy_atlas(rows: list[str], cols: int = 4) -> tuple[int, int]:
    """Calculate atlas size for enemy sprite sheet."""
    num_rows = len(rows)
    # Use 4 columns for enemies (smaller animation)
    atlas_w = cols * CELL_W
    atlas_h = num_rows * CELL_H
    return atlas_w, atlas_h


def compose_enemy_atlas(run_dir: Path, output_path: Path, rows: list[str], cols: int = 4) -> bool:
    """Compose a smaller enemy sprite sheet from player frames."""
    frames_dir = run_dir / "frames"
    
    atlas_w, atlas_h = calculate_enemy_atlas(rows, cols)
    atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    
    # Map enemy rows to player rows
    row_mapping = {
        "idle": "idle",
        "walk": "walk-right",
        "attack": "attack",
        "death": "death",
    }
    
    frames_copied = 0
    for row_idx, enemy_row in enumerate(rows):
        player_row = row_mapping.get(enemy_row, enemy_row)
        
        # Determine number of frames
        if enemy_row in ["attack", "death"]:
            num_frames = 4
        else:
            num_frames = 8
        
        for col in range(min(cols, num_frames)):
            # Map to player frame (some rows only have 6 frames)
            player_frame = col if col < 6 else 5
            frame_path = frames_dir / f"{player_row}_{player_frame}.png"
            
            if frame_path.exists():
                with Image.open(frame_path) as im:
                    cell = im.convert("RGBA")
                
                if cell.size != (CELL_W, CELL_H):
                    cell = cell.resize((CELL_W, CELL_H), Image.LANCZOS)
                
                atlas.paste(cell, (col * CELL_W, row_idx * CELL_H), cell)
                frames_copied += 1
    
    if frames_copied == 0:
        print("error: no frames found to copy", file=sys.stderr)
        return False
    
    atlas.save(output_path.with_suffix(".png"), format="PNG")
    atlas.save(output_path.with_suffix(".webp"), format="WEBP", lossless=True, method=6)
    print(f"wrote {output_path}")
    return True


def build_enemy_config(enemy_name: str, enemy_desc: str, rows: list[str]) -> dict:
    """Build enemy character configuration."""
    animations = {}
    
    for idx, row in enumerate(rows):
        num_frames = 4 if row in ["attack", "death"] else 8
        animations[row] = {
            "row": idx,
            "startFrame": 0,
            "endFrame": num_frames - 1,
            "frames": num_frames,
            "loop": row not in ["attack", "death"]
        }
    
    # Calculate atlas dimensions (4 columns for enemies)
    atlas_w = 4 * CELL_W
    atlas_h = len(rows) * CELL_H
    
    return {
        "id": slugify(enemy_name),
        "name": enemy_name,
        "description": enemy_desc,
        "type": "enemy",
        "spritesheetPath": "spritesheet.webp",
        "frameWidth": CELL_W,
        "frameHeight": CELL_H,
        "columns": 4,
        "atlasWidth": atlas_w,
        "atlasHeight": atlas_h,
        "animations": animations,
        "rows": rows
    }


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    
    # Verify run directory exists
    if not run_dir.exists():
        print(f"error: run directory not found: {run_dir}", file=sys.stderr)
        return 1
    
    # Load jobs to verify
    jobs = load_jobs(run_dir)
    if jobs.get("animation_mode") != "game":
        print("warning: run directory is not in game mode, animations may not match")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get enemy rows
    enemy_rows = get_enemy_rows()
    
    # Compose atlas
    spritesheet_path = output_dir / "spritesheet"
    if not compose_enemy_atlas(run_dir, spritesheet_path, enemy_rows):
        return 1
    
    # Build configuration
    config = build_enemy_config(args.enemy_name, args.enemy_desc, enemy_rows)
    
    # Write config
    config_path = output_dir / "character.json"
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {config_path}")
    
    print(f"\nEnemy sprite generated successfully!")
    print(f"  Spritesheet: {spritesheet_path}.webp")
    print(f"  Config: {config_path}")
    print(f"  Animations: {', '.join(enemy_rows)}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

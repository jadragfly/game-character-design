"""Shared helpers used by every script."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROW_ORDER: list[str] = [
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

GAME_CHARACTER_ROWS: list[str] = [
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

GAME_PLATFORMER_ROWS: list[str] = [
    "idle",
    "walk-right",
    "walk-left",
    "jump",
    "crouch",
    "attack",
    "pickup",
]

def get_rows_for_mode(mode: str) -> list[str]:
    """Get row order based on animation mode: 'pet' or 'game'."""
    if mode == "game":
        return GAME_CHARACTER_ROWS
    return ROW_ORDER

ATLAS_W = 1536
ATLAS_H = 1872
CELL_W = 192
CELL_H = 208
COLS = 8
ROWS = 9


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "pet"


def skill_root() -> Path:
    """Absolute path to the pet-design/ directory (one level above scripts/)."""
    return Path(__file__).resolve().parent.parent


def load_jobs(run_dir: Path) -> dict[str, Any]:
    f = run_dir / "jobs.json"
    if not f.exists():
        raise FileNotFoundError(
            f"{f} not found. Run scripts/prepare_run.py first."
        )
    return json.loads(f.read_text())


def save_jobs(run_dir: Path, jobs: dict[str, Any]) -> None:
    f = run_dir / "jobs.json"
    tmp = f.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(jobs, indent=2, ensure_ascii=False))
    tmp.replace(f)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def compose_base_prompt(
    *,
    description: str,
    style: str,
    has_reference: bool,
) -> str:
    root = skill_root()
    style_block = read_text(root / "prompts" / "style" / f"{style}.txt")
    forbidden = read_text(root / "prompts" / "base" / "_forbidden.txt")
    template_name = "image-to-image.txt" if has_reference else "text-to-image.txt"
    template = read_text(root / "prompts" / "base" / template_name)
    return template.format(
        description=description,
        style_block=style_block,
        forbidden_block=forbidden,
    )


def compose_row_prompt(
    *,
    row: str,
    style: str,
    description: str,
    mode: str,
    animation_mode: str = "pet",
) -> str:
    root = skill_root()
    style_block = read_text(root / "prompts" / "style" / f"{style}.txt")
    
    if animation_mode == "game":
        row_prompt_path = root / "prompts" / "rows" / "game" / f"{row}.txt"
        forbidden_path = root / "prompts" / "rows" / "game" / "_forbidden.txt"
    else:
        row_prompt_path = root / "prompts" / "rows" / f"{row}.txt"
        forbidden_path = root / "prompts" / "rows" / "_forbidden.txt"
    
    action_block = read_text(row_prompt_path)
    forbidden = read_text(forbidden_path)
    
    if mode == "auto":
        layout_block = (
            "LAYOUT: Generate exactly 8 separate images, one per frame. "
            "Each image is a single isolated pose, not a grid, not a strip, not a collage. "
            "Each image has the character centered with safe padding. "
            "CRITICAL: Each frame MUST show the COMPLETE character from head to toe, "
            "no cropping, no truncation. The entire body including feet must be visible."
        )
    else:
        layout_block = (
            "LAYOUT: Generate ONE single image arranged as a 4-column by 2-row grid (8 cells). "
            "Each cell holds one frame, isolated, with safe padding inside each cell. "
            "Cells are separated by a thin gap of solid #00FF00. "
            "Read order is left to right, top row first, then bottom row. "
            "CRITICAL: Each cell MUST show the COMPLETE character from head to toe, "
            "no cropping, no truncation, no half-body. The entire body must fit within each cell."
        )
    
    if animation_mode == "game":
        identity = (
            "IDENTITY LOCK: Reference image 1 is the canonical base of the game character. "
            f"Subject: {description}. Keep the EXACT same character: same head shape, "
            "face, eyes, mouth, palette, costume, prop, outline weight, body proportions, "
            "and silhouette as in reference image 1. Do not redesign the character. "
            "Treat reference image 2 as a layout-only scaffold whose pixels MUST NOT "
            "appear in the output."
        )
    else:
        identity = (
            "IDENTITY LOCK: Reference image 1 is the canonical base of the pet. "
            f"Subject: {description}. Keep the EXACT same character: same head shape, "
            "face, eyes, mouth, palette, prop, outline weight, body proportions, "
            "and silhouette as in reference image 1. Do not redesign the pet. "
            "Treat reference image 2 as a layout-only scaffold whose pixels MUST NOT "
            "appear in the output."
        )
    
    bg = (
        "BACKGROUND: Solid pure green chroma-key background (#00FF00) covering "
        "every pixel that is not the character. No gradient, no scenery, no shadow, "
        "no ground, no vignette."
    )
    return "\n\n".join([
        layout_block,
        identity,
        action_block,
        style_block,
        bg,
        f"FORBIDDEN: {forbidden}",
    ])


def write_prompt_log(run_dir: Path, job_id: str, prompt: str) -> Path:
    out = run_dir / "prompts" / f"{job_id}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prompt, encoding="utf-8")
    return out


@dataclass
class RowSpec:
    row: str
    mode: str  # "auto" | "grid"

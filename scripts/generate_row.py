#!/usr/bin/env python3
"""Generate a single action-row for the pet or game character (or all remaining rows in order).

Two modes:
  auto -> sequential_image_generation="auto", aspect_ratio=1:1, expects 8
          separate frames returned by Seedream. Stored as
          decoded/<row>__<i>.png (i=0..7), with a manifest entry pointing
          to the directory.
  grid -> sequential_image_generation="disabled", aspect_ratio=16:9, one
          composite grid image returned. Stored as decoded/<row>.png.
          
Supports both pet animations and game character animations based on
the animation_mode in jobs.json.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import (
    ROW_ORDER,
    GAME_CHARACTER_ROWS,
    GAME_PLATFORMER_ROWS,
    compose_row_prompt,
    load_jobs,
    save_jobs,
    skill_root,
    write_prompt_log,
)

import seedream_client


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate one or all action rows (pet or game character).")
    p.add_argument("--run-dir", required=True)
    p.add_argument(
        "--row",
        required=True,
        help='Row id, or "all" to generate every pending row in order.',
    )
    p.add_argument(
        "--mode",
        default=None,
        choices=["auto", "grid"],
        help="Override mode for this call. Defaults to the per-row mode in jobs.json.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if the row is already succeeded.",
    )
    return p.parse_args()


def _generate_one(run_dir: Path, jobs: dict, row: str, mode: str | None, force: bool) -> bool:
    job = jobs["jobs"][row]
    if job["status"] == "succeeded" and not force:
        print(f"[{row}] already succeeded ({job.get('decoded')}). Use --force to redo.")
        return True

    base_canonical = run_dir / "references" / "canonical-base.png"
    if not base_canonical.exists():
        print(
            f"[{row}] error: {base_canonical} missing. Run generate_base.py first.",
            file=sys.stderr,
        )
        return False

    use_mode = mode or job.get("mode") or "auto"
    job["mode"] = use_mode

    animation_mode = jobs.get("animation_mode", "pet")
    if animation_mode == "game":
        layout_guide = (
            skill_root() / "references" / "layout-guides" / "game" / f"{row}__{use_mode}.png"
        )
    else:
        layout_guide = (
            skill_root() / "references" / "layout-guides" / f"{row}__{use_mode}.png"
        )
    if not layout_guide.exists():
        print(
            f"[{row}] error: layout guide {layout_guide} missing. "
            f"Run scripts/build_layout_guides.py.",
            file=sys.stderr,
        )
        return False

    refs = [str(base_canonical), str(layout_guide)]
    refs.extend(jobs.get("user_references") or [])

    prompt = compose_row_prompt(
        row=row,
        style=jobs["style"],
        description=jobs["description"],
        mode=use_mode,
        animation_mode=animation_mode,
    )
    write_prompt_log(run_dir, row, prompt)

    aspect = "1:1" if use_mode == "auto" else "16:9"
    sequential = use_mode == "auto"

    try:
        out_paths = seedream_client.generate(
            prompt=prompt,
            reference_image_paths=refs,
            aspect_ratio=aspect,
            sequential=sequential,
            out_dir=run_dir / "decoded",
            out_prefix=f"{row}__raw",
        )
    except seedream_client.SeedreamError as exc:
        job["status"] = "failed"
        job["error"] = str(exc)
        save_jobs(run_dir, jobs)
        print(f"[{row}] generation failed: {exc}", file=sys.stderr)
        return False

    if use_mode == "auto":
        if len(out_paths) == 0:
            job["status"] = "failed"
            job["error"] = "auto mode returned 0 frames"
            save_jobs(run_dir, jobs)
            print(f"[{row}] error: auto mode returned 0 frames", file=sys.stderr)
            return False
        if len(out_paths) != 8:
            print(
                f"[{row}] warning: auto mode returned {len(out_paths)} frames "
                f"(expected 8). extract_frames.py will resize / pad.",
                file=sys.stderr,
            )
        job["status"] = "succeeded"
        job["decoded"] = [str(p) for p in out_paths]
        job["error"] = None
    else:
        single = out_paths[0]
        target = run_dir / "decoded" / f"{row}.png"
        Path(single).rename(target)
        job["status"] = "succeeded"
        job["decoded"] = str(target)
        job["error"] = None

    save_jobs(run_dir, jobs)
    print(f"[{row}] succeeded mode={use_mode} frames={len(out_paths)}")
    return True


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    jobs = load_jobs(run_dir)

    animation_mode = jobs.get("animation_mode", "pet")
    if animation_mode == "pet":
        row_order = ROW_ORDER
        mirror_source = "running-right"
        mirror_target = "running-left"
    elif animation_mode == "game":
        game_type = jobs.get("game_type", "full")
        if game_type == "platformer":
            row_order = GAME_PLATFORMER_ROWS
        else:
            row_order = GAME_CHARACTER_ROWS
        mirror_source = "walk-right"
        mirror_target = "walk-left"
    else:
        row_order = ROW_ORDER
        mirror_source = "running-right"
        mirror_target = "running-left"

    if args.row == "all":
        ok = True
        for row in row_order:
            mirror_flag = jobs["jobs"].get(row, {}).get("derive_from_mirror")
            if mirror_flag:
                print(f"[{row}] skipped (will be mirrored from {mirror_source}).")
                continue
            ok = _generate_one(run_dir, jobs, row, args.mode, args.force) and ok
        return 0 if ok else 1

    if args.row not in jobs["jobs"]:
        print(f"error: unknown row {args.row!r}. Valid: {row_order}", file=sys.stderr)
        return 2

    success = _generate_one(run_dir, jobs, args.row, args.mode, args.force)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

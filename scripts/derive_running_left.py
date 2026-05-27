#!/usr/bin/env python3
"""Derive walk-left / running-left frames by horizontally mirroring their counterparts.

For pets: mirrors running-right into running-left
For game characters: mirrors walk-right into walk-left

This skips a Seedream call and guarantees perfect symmetry. Use only when
the source direction has no asymmetric markings, props, or text. The user must 
pass --confirm-appropriate-mirror with a one-line decision note.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

from _common import load_jobs, save_jobs


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Mirror walk-right into walk-left (game) or running-right into running-left (pet)."
    )
    p.add_argument("--run-dir", required=True)
    p.add_argument(
        "--confirm-appropriate-mirror",
        action="store_true",
        help="Required. Confirms you have visually inspected source frames "
        "and the character has no side-specific markings, prop, or text.",
    )
    p.add_argument(
        "--decision-note",
        default="symmetric character, mirror preserves identity",
        help="Recorded in jobs.json for provenance.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.confirm_appropriate_mirror:
        print(
            "error: --confirm-appropriate-mirror is required. Inspect "
            "source frames and re-run if symmetric.",
            file=sys.stderr,
        )
        return 2

    run_dir = Path(args.run_dir).resolve()
    jobs = load_jobs(run_dir)

    animation_mode = jobs.get("animation_mode", "pet")
    if animation_mode == "game":
        source_row = "walk-right"
        target_row = "walk-left"
        frame_prefix = "walk"
    else:
        source_row = "running-right"
        target_row = "running-left"
        frame_prefix = "running"

    source_job = jobs["jobs"].get(source_row, {})
    if source_job.get("status") != "succeeded":
        print(
            f"error: {source_row} has not succeeded yet, cannot mirror.",
            file=sys.stderr,
        )
        return 2

    frames_dir = run_dir / "frames"
    mirrored = 0
    for i in range(8):
        src = frames_dir / f"{frame_prefix}-right_{i}.png"
        if not src.exists():
            src_alt = frames_dir / f"{source_row}_{i}.png"
            if src_alt.exists():
                src = src_alt
            else:
                print(
                    f"error: source frame {src} (or {src_alt}) missing. "
                    f"Run extract_frames.py first.",
                    file=sys.stderr,
                )
                return 2
        dst_name = f"{frame_prefix}-left_{i}.png"
        dst = frames_dir / dst_name
        with Image.open(src) as im:
            ImageOps.mirror(im).save(dst, format="PNG")
        mirrored += 1

    jobs["jobs"][target_row]["status"] = "mirrored"
    jobs["jobs"][target_row]["derive_from_mirror"] = True
    jobs["jobs"][target_row]["mirror_note"] = args.decision_note
    jobs["jobs"][target_row]["frames"] = [
        str(frames_dir / f"{frame_prefix}-left_{i}.png") for i in range(8)
    ]
    save_jobs(run_dir, jobs)

    print(f"mirrored {mirrored} frames {source_row} -> {target_row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

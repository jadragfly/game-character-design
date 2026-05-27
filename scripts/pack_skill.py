#!/usr/bin/env python3
"""Package the pet-design skill folder into pet-design.zip for upload to
TRAE (Settings -> Rules & Skills -> Create Skill -> Upload).

The zip's root contains a single folder named pet-design/ that holds SKILL.md
at its top level, matching the TRAE skill upload format.
"""
from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache"}
EXCLUDE_SUFFIXES = {".pyc"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pack pet-design/ into a TRAE-ready skill zip.")
    p.add_argument(
        "--output",
        default=None,
        help="Output zip path. Defaults to ../pet-design.zip relative to skill folder.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    skill_dir = Path(__file__).resolve().parent.parent
    if skill_dir.name != "pet-design":
        print(
            f"error: expected to live under pet-design/, got {skill_dir}",
            file=sys.stderr,
        )
        return 2

    out_path = (
        Path(args.output).resolve()
        if args.output
        else skill_dir.parent / "pet-design.zip"
    )

    if out_path.exists():
        out_path.unlink()

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(skill_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if any(f.endswith(s) for s in EXCLUDE_SUFFIXES):
                    continue
                full = Path(root) / f
                arcname = Path("pet-design") / full.relative_to(skill_dir)
                zf.write(full, str(arcname))
    print(f"wrote {out_path}")
    print(f"  upload this zip in TRAE: Settings -> Rules & Skills -> Create Skill -> Upload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

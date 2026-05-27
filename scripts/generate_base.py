#!/usr/bin/env python3
"""Generate the canonical base portrait of the pet.

Reads jobs.json, composes a base prompt from prompts/base/{text-to-image,
image-to-image}.txt + the chosen style block + forbidden block, calls Seedream
through seedream_client.generate(...), and stores the first returned image at
both decoded/base.png and references/canonical-base.png.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from _common import compose_base_prompt, load_jobs, save_jobs, write_prompt_log

import seedream_client


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate the canonical base pet portrait.")
    p.add_argument("--run-dir", required=True)
    p.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if base.png already exists.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    jobs = load_jobs(run_dir)

    base_decoded = run_dir / "decoded" / "base.png"
    canonical = run_dir / "references" / "canonical-base.png"

    if base_decoded.exists() and not args.force:
        print(f"base already exists at {base_decoded} (use --force to regenerate)")
        return 0

    user_refs = jobs.get("user_references") or []
    has_ref = len(user_refs) > 0
    prompt = compose_base_prompt(
        description=jobs["description"],
        style=jobs["style"],
        has_reference=has_ref,
    )
    write_prompt_log(run_dir, "base", prompt)

    try:
        out_paths = seedream_client.generate(
            prompt=prompt,
            reference_image_paths=user_refs if has_ref else None,
            aspect_ratio="1:1",
            sequential=False,
            out_dir=run_dir / "decoded",
            out_prefix="base_raw",
        )
    except seedream_client.SeedreamError as exc:
        jobs["jobs"]["base"]["status"] = "failed"
        jobs["jobs"]["base"]["error"] = str(exc)
        save_jobs(run_dir, jobs)
        print(f"error: base generation failed: {exc}", file=sys.stderr)
        return 1

    chosen = Path(out_paths[0])
    shutil.copy2(chosen, base_decoded)
    shutil.copy2(chosen, canonical)

    jobs["jobs"]["base"]["status"] = "succeeded"
    jobs["jobs"]["base"]["decoded"] = str(base_decoded)
    jobs["jobs"]["base"]["error"] = None
    save_jobs(run_dir, jobs)

    print(f"wrote {base_decoded}")
    print(f"wrote {canonical}")
    print("next: python scripts/generate_row.py --run-dir " + str(run_dir) + " --row idle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

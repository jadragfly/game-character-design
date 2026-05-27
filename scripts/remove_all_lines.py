#!/usr/bin/env python3
"""Enhanced black border/line removal script for spritesheets.

This script detects and removes ALL black lines from sprites:
- Edge single pixels
- Continuous horizontal lines (full width or spanning multiple frames)
- Continuous vertical lines (full height or spanning multiple frames)
- Lines anywhere in the image (not just edges)

Usage:
    python analyze_lines.py --run-dir "D:\impotent\skills\make_game\pig-contra-game\run\pig-soldier"
    python remove_all_lines.py --run-dir "D:\impotent\skills\make_game\pig-contra-game\run\pig-soldier"
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from PIL import Image
import numpy as np


DEBUG = True


def log(msg: str) -> None:
    if DEBUG:
        print(msg)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze and remove black lines from sprites.")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--action", default="analyze", choices=["analyze", "remove"])
    p.add_argument("--threshold", type=int, default=50, help="Dark pixel threshold (0-255)")
    p.add_argument("--min-streak", type=int, default=30, help="Minimum line length to be considered a line")
    return p.parse_args()


def analyze_frame(path: Path, threshold: int = 50) -> dict:
    """Analyze a single frame for black lines."""
    with Image.open(path) as im:
        rgba = im.convert("RGBA")

    arr = np.array(rgba)
    h, w = arr.shape[:2]

    dark_mask = (arr[:, :, 0] < threshold) & (arr[:, :, 1] < threshold) & (arr[:, :, 2] < threshold)
    opaque_mask = arr[:, :, 3] > 200
    dark_opaque = dark_mask & opaque_mask

    dark_pixels = np.where(dark_opaque)
    total_dark = len(dark_pixels[0])

    if total_dark == 0:
        return {"total_dark": 0, "horizontal_lines": [], "vertical_lines": [], "summary": "No dark pixels"}

    col_counts = np.bincount(dark_pixels[1], minlength=w)
    row_counts = np.bincount(dark_pixels[0], minlength=h)

    horizontal_lines = []
    start = None
    for i in range(h):
        if row_counts[i] > 0:
            if start is None:
                start = i
        else:
            if start is not None:
                length = i - start
                if length >= 3:
                    horizontal_lines.append({"start": start, "end": i - 1, "length": length, "avg_dark": float(np.mean(row_counts[start:i]))})
                start = None

    vertical_lines = []
    start = None
    for i in range(w):
        if col_counts[i] > 0:
            if start is None:
                start = i
        else:
            if start is not None:
                length = i - start
                if length >= 3:
                    vertical_lines.append({"start": start, "end": i - 1, "length": length, "avg_dark": float(np.mean(col_counts[start:i]))})
                start = None

    return {
        "total_dark": total_dark,
        "horizontal_lines": horizontal_lines,
        "vertical_lines": vertical_lines,
        "summary": f"Dark: {total_dark}, H-lines: {len(horizontal_lines)}, V-lines: {len(vertical_lines)}"
    }


def remove_lines_from_frame(path: Path, threshold: int = 50, min_streak: int = 30) -> dict:
    """Remove all black lines from a single frame."""
    with Image.open(path) as im:
        rgba = im.convert("RGBA")

    pixels = rgba.load()
    w, h = rgba.size
    stats = {"pixels_removed": 0, "lines_removed": 0}

    dark_coords = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a > 200 and r < threshold and g < threshold and b < threshold:
                dark_coords.append((x, y))

    if not dark_coords:
        rgba.save(path, format="PNG")
        return stats

    col_counts = {}
    row_counts = {}
    for x, y in dark_coords:
        col_counts[x] = col_counts.get(x, 0) + 1
        row_counts[y] = row_counts.get(y, 0) + 1

    lines_to_remove = set()

    for col, count in col_counts.items():
        if count >= min_streak:
            lines_to_remove.add(('v', col))
            stats["lines_removed"] += 1

    for row, count in row_counts.items():
        if count >= min_streak:
            lines_to_remove.add(('h', row))
            stats["lines_removed"] += 1

    if lines_to_remove:
        removed = 0
        for line_type, pos in lines_to_remove:
            if line_type == 'v':
                for y in range(h):
                    r, g, b, a = pixels[pos, y]
                    if a > 200:
                        pixels[pos, y] = (r, g, b, 0)
                        removed += 1
            else:
                for x in range(w):
                    r, g, b, a = pixels[x, pos]
                    if a > 200:
                        pixels[x, pos] = (r, g, b, 0)
                        removed += 1
        stats["pixels_removed"] = removed

    rgba.save(path, format="PNG")
    return stats


def rebuild_spritesheet(run_dir: Path) -> None:
    """Rebuild spritesheet from processed frames."""
    frames_dir = run_dir / "frames"
    final_dir = run_dir / "final"

    rows = ["idle", "walk-right", "walk-left", "jump", "crouch", "attack", "pickup"]
    frame_size = (192, 234)
    cols = 8

    frames = {}
    for row in rows:
        frames[row] = []
        for i in range(8):
            frame_path = frames_dir / f"{row}_{i}.png"
            if frame_path.exists():
                frames[row].append(Image.open(frame_path).convert("RGBA"))

    total_height = len(rows) * frame_size[1]
    total_width = cols * frame_size[0]

    spritesheet = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))

    for row_idx, row in enumerate(rows):
        for col_idx in range(min(8, len(frames[row]))):
            x = col_idx * frame_size[0]
            y = row_idx * frame_size[1]
            spritesheet.paste(frames[row][col_idx], (x, y))

    spritesheet.save(final_dir / "spritesheet.png", format="PNG")
    log(f"Rebuilt spritesheet: {total_width}x{total_height}")


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    frames_dir = run_dir / "frames"

    if not frames_dir.exists():
        print(f"Error: frames directory not found: {frames_dir}")
        return 1

    rows = ["idle", "walk-right", "walk-left", "jump", "crouch", "attack", "pickup"]
    all_analyses = {}

    if args.action == "analyze":
        print(f"Analyzing frames in: {frames_dir}")
        print(f"Threshold: {args.threshold}, Min streak: {args.min_streak}\n")

        for row in rows:
            row_analyses = []
            for i in range(8):
                frame_path = frames_dir / f"{row}_{i}.png"
                if frame_path.exists():
                    result = analyze_frame(frame_path, args.threshold)
                    row_analyses.append(result)

            all_analyses[row] = row_analyses

            total_dark = sum(a.get("total_dark", 0) for a in row_analyses)
            h_lines = sum(len(a.get("horizontal_lines", [])) for a in row_analyses)
            v_lines = sum(len(a.get("vertical_lines", [])) for a in row_analyses)

            print(f"[{row}] frames={len(row_analyses)}, dark={total_dark}, h-lines={h_lines}, v-lines={v_lines}")

            for idx, analysis in enumerate(row_analyses):
                if analysis.get("total_dark", 0) > 0:
                    h = analysis.get("horizontal_lines", [])
                    v = analysis.get("vertical_lines", [])
                    if h or v:
                        print(f"  Frame {idx}: dark={analysis['total_dark']}")
                        for line in h[:5]:
                            print(f"    H: y={line['start']}-{line['end']}, len={line['length']}, avg={line['avg_dark']:.1f}")
                        for line in v[:5]:
                            print(f"    V: x={line['start']}-{line['end']}, len={line['length']}, avg={line['avg_dark']:.1f}")

        report_path = frames_dir.parent / "line-analysis.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(all_analyses, f, indent=2)
        print(f"\nSaved analysis to: {report_path}")

    elif args.action == "remove":
        print(f"Removing lines from frames in: {frames_dir}")
        print(f"Threshold: {args.threshold}, Min streak: {args.min_streak}\n")

        total_removed = 0
        total_lines = 0

        for row in rows:
            row_removed = 0
            row_lines = 0
            for i in range(8):
                frame_path = frames_dir / f"{row}_{i}.png"
                if frame_path.exists():
                    stats = remove_lines_from_frame(frame_path, args.threshold, args.min_streak)
                    row_removed += stats["pixels_removed"]
                    row_lines += stats["lines_removed"]
                    if stats["pixels_removed"] > 0:
                        print(f"  [{row}_{i}] removed {stats['pixels_removed']} pixels, {stats['lines_removed']} lines")

            if row_removed > 0:
                print(f"[{row}] total: {row_removed} pixels, {row_lines} lines")
                total_removed += row_removed
                total_lines += row_lines

        print(f"\nTotal: {total_removed} pixels removed, {total_lines} lines removed")

        if total_removed > 0:
            rebuild_spritesheet(run_dir)
            print("Rebuilt spritesheet.png")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

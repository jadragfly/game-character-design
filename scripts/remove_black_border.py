#!/usr/bin/env python3
"""Remove black borders from character sprites after chroma key.

Detects and removes black outline borders that may appear on character edges
due to AI generation or chroma key processing artifacts.

This script detects continuous lines (horizontal or vertical) at the edges
and removes them.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image
import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Remove black borders from character frames.")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--row", default="all", help='Row to process, or "all".')
    return p.parse_args()


def _is_dark_pixel(r: int, g: int, b: int, threshold: int = 50) -> bool:
    """Check if pixel is dark enough to be considered border."""
    return r < threshold and g < threshold and b < threshold


def _is_transparent(a: int) -> bool:
    """Check if pixel is transparent."""
    return a < 128


def _check_horizontal_line(pixels, x: int, y: int, width: int, threshold: int = 50) -> tuple[bool, int]:
    """Check if there's a continuous dark horizontal line at this position.
    
    Returns: (is_line, line_length)
    """
    length = 0
    start_x = x
    
    while x < width and _is_dark_pixel(*pixels[x, y][:3], threshold):
        length += 1
        x += 1
    
    return length >= 10, length  # 至少10个连续黑色像素才算线条


def _check_vertical_line(pixels, x: int, y: int, height: int, threshold: int = 50) -> tuple[bool, int]:
    """Check if there's a continuous dark vertical line at this position.
    
    Returns: (is_line, line_length)
    """
    length = 0
    start_y = y
    
    while y < height and _is_dark_pixel(*pixels[x, y][:3], threshold):
        length += 1
        y += 1
    
    return length >= 10, length  # 至少10个连续黑色像素才算线条


def _process_frame(path: Path, threshold: int = 50) -> dict:
    """Remove black border pixels and lines from a single frame."""
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
    
    pixels = rgba.load()
    w, h = rgba.size
    
    stats = {
        "edge_pixels_removed": 0,
        "h_lines_removed": 0,
        "v_lines_removed": 0,
        "total_removed": 0
    }
    
    edge_width = 15  # 边缘检测宽度
    
    # 1. 先移除边缘的单个黑像素
    for y in range(h):
        for x in range(min(edge_width, w // 4)):
            r, g, b, a = pixels[x, y]
            if not _is_transparent(a) and _is_dark_pixel(r, g, b, threshold):
                pixels[x, y] = (r, g, b, 0)
                stats["edge_pixels_removed"] += 1
        
        for x in range(max(w - edge_width, w * 3 // 4), w):
            r, g, b, a = pixels[x, y]
            if not _is_transparent(a) and _is_dark_pixel(r, g, b, threshold):
                pixels[x, y] = (r, g, b, 0)
                stats["edge_pixels_removed"] += 1
    
    for x in range(w):
        for y in range(min(edge_width, h // 4)):
            r, g, b, a = pixels[x, y]
            if not _is_transparent(a) and _is_dark_pixel(r, g, b, threshold):
                pixels[x, y] = (r, g, b, 0)
                stats["edge_pixels_removed"] += 1
        
        for y in range(max(h - edge_width, h * 3 // 4), h):
            r, g, b, a = pixels[x, y]
            if not _is_transparent(a) and _is_dark_pixel(r, g, b, threshold):
                pixels[x, y] = (r, g, b, 0)
                stats["edge_pixels_removed"] += 1
    
    # 2. 检测并移除横向线条（从左到右扫描边缘区域）
    for y in range(min(edge_width, h // 4)):
        x = 0
        while x < w:
            r, g, b, a = pixels[x, y]
            if not _is_transparent(a) and _is_dark_pixel(r, g, b, threshold):
                is_line, length = _check_horizontal_line(pixels, x, y, w, threshold)
                if is_line and length > w * 0.3:  # 线条超过宽度30%才移除
                    for lx in range(x, min(x + length, w)):
                        lr, lg, lb, la = pixels[lx, y]
                        if not _is_transparent(la):
                            pixels[lx, y] = (lr, lg, lb, 0)
                            stats["h_lines_removed"] += 1
                    x += length
                else:
                    x += 1
            else:
                x += 1
    
    # 3. 检测并移除横向线条（底部）
    for y in range(max(h - edge_width, h * 3 // 4), h):
        x = 0
        while x < w:
            r, g, b, a = pixels[x, y]
            if not _is_transparent(a) and _is_dark_pixel(r, g, b, threshold):
                is_line, length = _check_horizontal_line(pixels, x, y, w, threshold)
                if is_line and length > w * 0.3:
                    for lx in range(x, min(x + length, w)):
                        lr, lg, lb, la = pixels[lx, y]
                        if not _is_transparent(la):
                            pixels[lx, y] = (lr, lg, lb, 0)
                            stats["h_lines_removed"] += 1
                    x += length
                else:
                    x += 1
            else:
                x += 1
    
    # 4. 检测并移除竖向线条（从上到下扫描边缘区域）
    for x in range(min(edge_width, w // 4)):
        y = 0
        while y < h:
            r, g, b, a = pixels[x, y]
            if not _is_transparent(a) and _is_dark_pixel(r, g, b, threshold):
                is_line, length = _check_vertical_line(pixels, x, y, h, threshold)
                if is_line and length > h * 0.3:  # 线条超过高度30%才移除
                    for ly in range(y, min(y + length, h)):
                        lr, lg, lb, la = pixels[x, ly]
                        if not _is_transparent(la):
                            pixels[x, ly] = (lr, lg, lb, 0)
                            stats["v_lines_removed"] += 1
                    y += length
                else:
                    y += 1
            else:
                y += 1
    
    # 5. 检测并移除竖向线条（右侧）
    for x in range(max(w - edge_width, w * 3 // 4), w):
        y = 0
        while y < h:
            r, g, b, a = pixels[x, y]
            if not _is_transparent(a) and _is_dark_pixel(r, g, b, threshold):
                is_line, length = _check_vertical_line(pixels, x, y, h, threshold)
                if is_line and length > h * 0.3:
                    for ly in range(y, min(y + length, h)):
                        lr, lg, lb, la = pixels[x, ly]
                        if not _is_transparent(la):
                            pixels[x, ly] = (lr, lg, lb, 0)
                            stats["v_lines_removed"] += 1
                    y += length
                else:
                    y += 1
            else:
                y += 1
    
    stats["total_removed"] = (stats["edge_pixels_removed"] + 
                              stats["h_lines_removed"] + 
                              stats["v_lines_removed"])
    
    rgba.save(path, format="PNG")
    return stats


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    frames_dir = run_dir / "frames"
    
    if not frames_dir.exists():
        print(f"Error: frames directory not found: {frames_dir}")
        return 1
    
    rows = []
    if args.row == "all":
        rows = ["idle", "walk-right", "walk-left", "jump", "crouch", "attack", "pickup"]
    else:
        rows = [args.row]
    
    total_stats = {
        "edge_pixels_removed": 0,
        "h_lines_removed": 0,
        "v_lines_removed": 0,
        "total_removed": 0,
        "frames_processed": 0
    }
    
    for row in rows:
        frame_count = 0
        for i in range(8):
            frame_path = frames_dir / f"{row}_{i}.png"
            if frame_path.exists():
                stats = _process_frame(frame_path)
                total_stats["edge_pixels_removed"] += stats["edge_pixels_removed"]
                total_stats["h_lines_removed"] += stats["h_lines_removed"]
                total_stats["v_lines_removed"] += stats["v_lines_removed"]
                total_stats["total_removed"] += stats["total_removed"]
                frame_count += 1
        
        if frame_count > 0:
            print(f"[{row}] processed ({frame_count} frames)")
            print(f"       edge pixels: {total_stats['edge_pixels_removed']}, "
                  f"h_lines: {total_stats['h_lines_removed']}, "
                  f"v_lines: {total_stats['v_lines_removed']}")
    
    print(f"\nTotal: {total_stats['total_removed']} pixels removed")
    print(f"  - Edge pixels: {total_stats['edge_pixels_removed']}")
    print(f"  - Horizontal lines: {total_stats['h_lines_removed']}")
    print(f"  - Vertical lines: {total_stats['v_lines_removed']}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

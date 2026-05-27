#!/usr/bin/env python3
"""Render QA artefacts and perform quality checks:

  qa/contact-sheet.png  - grid showing all animation frames
  qa/<row>.gif          - animated GIF preview for key animations
  qa/run-summary.json   - detailed QA report with quality checks
  qa/chroma-report.txt  - chroma key processing report
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from _common import CELL_H, CELL_W, COLS, ROW_ORDER, GAME_CHARACTER_ROWS, GAME_PLATFORMER_ROWS, load_jobs


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render QA contact sheet, GIF previews, and quality checks.")
    p.add_argument("--run-dir", required=True)
    p.add_argument(
        "--gif-rows",
        nargs="+",
        default=None,
        help="Rows to render as animated GIFs. Defaults to all rows.",
    )
    p.add_argument(
        "--gif-fps",
        type=int,
        default=10,
        help="Animation playback speed.",
    )
    p.add_argument(
        "--chroma-threshold",
        type=int,
        default=5,
        help="Max percentage of chroma pixels allowed after processing.",
    )
    return p.parse_args()


def _load_font() -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, 14)
        except OSError:
            continue
    return ImageFont.load_default()


def _checker(w: int, h: int, square: int = 8) -> Image.Image:
    bg = Image.new("RGB", (w, h), (224, 224, 224))
    draw = ImageDraw.Draw(bg)
    for y in range(0, h, square):
        for x in range(0, w, square):
            if ((x // square) + (y // square)) % 2 == 0:
                draw.rectangle([x, y, x + square, y + square], fill=(192, 192, 192))
    return bg


def _check_chroma(path: Path, threshold: int = 5) -> dict:
    """检查抠图质量 - 只检测边缘区域的异常背景色"""
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
    
    pixels = rgba.load()
    w, h = rgba.size
    total = w * h
    chroma_count = 0
    white_count = 0
    black_count = 0
    blue_count = 0
    edge_count = 0
    
    edge_width = 3  # 边缘检测宽度（像素）
    total_edge = 2 * (w + h - 2 * edge_width) * edge_width  # 边缘总像素数
    
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            
            # 只在边缘区域检测背景伪影
            is_edge = y < edge_width or y >= h - edge_width or x < edge_width or x >= w - edge_width
            
            if is_edge and a > 0:  # 边缘非透明像素
                edge_count += 1
                
                # 检测绿色背景
                if r < 50 and g > 200 and b < 50:
                    chroma_count += 1
                # 检测蓝色背景
                elif r < 80 and g < 80 and b > 150 and b > r * 1.5 and b > g * 1.5:
                    blue_count += 1
                # 检测白色背景
                elif r > 240 and g > 240 and b > 240:
                    white_count += 1
                # 检测黑色边框
                elif r < 30 and g < 30 and b < 30:
                    black_count += 1
    
    # 边缘检测的百分比
    edge_percent = (edge_count / total_edge) * 100 if total_edge > 0 else 0
    chroma_percent = (chroma_count / total_edge) * 100 if total_edge > 0 else 0
    white_percent = (white_count / total_edge) * 100 if total_edge > 0 else 0
    black_percent = (black_count / total_edge) * 100 if total_edge > 0 else 0
    blue_percent = (blue_count / total_edge) * 100 if total_edge > 0 else 0
    
    # 所有边缘背景色占比
    all_bg_percent = chroma_percent + white_percent + blue_percent  # 不包括黑色（可能是角色阴影）
    
    return {
        "path": str(path),
        "chroma_pixels": chroma_count,
        "white_pixels": white_count,
        "black_pixels": black_count,
        "blue_pixels": blue_count,
        "edge_pixels": edge_count,
        "total_edge_pixels": total_edge,
        "total_pixels": total,
        "chroma_percent": round(chroma_percent, 2),
        "white_percent": round(white_percent, 2),
        "black_percent": round(black_percent, 2),
        "blue_percent": round(blue_percent, 2),
        "edge_percent": round(edge_percent, 2),
        "all_bg_percent": round(all_bg_percent, 2),
        "passed": all_bg_percent <= 5.0  # 不包括黑色的边缘背景色 < 5% 即通过
    }


def _check_frame_exists(frames_dir: Path, row: str, expected_frames: int = 8) -> dict:
    """检查帧文件是否存在"""
    results = {"row": row, "expected": expected_frames, "found": 0, "missing": [], "all_exist": False}
    for i in range(expected_frames):
        frame_path = frames_dir / f"{row}_{i}.png"
        if frame_path.exists():
            results["found"] += 1
        else:
            results["missing"].append(i)
    results["all_exist"] = results["found"] == expected_frames
    return results


def _build_contact_sheet(run_dir: Path, out_path: Path, rows: list[str]) -> None:
    label_w = 140
    cell_pad = 4
    sheet_w = label_w + COLS * (CELL_W + cell_pad) + cell_pad
    sheet_h = len(rows) * (CELL_H + cell_pad) + cell_pad + 32
    sheet = Image.new("RGB", (sheet_w, sheet_h), (250, 250, 250))
    draw = ImageDraw.Draw(sheet)
    font = _load_font()

    draw.text((12, 8), "contact sheet", fill=(40, 40, 40), font=font)

    frames_dir = run_dir / "frames"
    for row_idx, row in enumerate(rows):
        y = 32 + row_idx * (CELL_H + cell_pad) + cell_pad
        draw.text((12, y + CELL_H // 2 - 8), row, fill=(60, 60, 60), font=font)
        for col in range(COLS):
            x = label_w + col * (CELL_W + cell_pad) + cell_pad
            checker = _checker(CELL_W, CELL_H)
            sheet.paste(checker, (x, y))
            frame = frames_dir / f"{row}_{col}.png"
            if frame.exists():
                with Image.open(frame) as im:
                    cell = im.convert("RGBA")
                if cell.size != (CELL_W, CELL_H):
                    cell = cell.resize((CELL_W, CELL_H), Image.LANCZOS)
                sheet.paste(cell, (x, y), cell)

    sheet.save(out_path, format="PNG")


def _build_gif(run_dir: Path, row: str, fps: int, out_path: Path, num_frames: int = 8) -> bool:
    frames_dir = run_dir / "frames"
    frame_paths = [frames_dir / f"{row}_{i}.png" for i in range(num_frames)]
    images: list[Image.Image] = []
    
    for p in frame_paths:
        if not p.exists():
            return False
        with Image.open(p) as im:
            rgba = im.convert("RGBA")
        bg = _checker(CELL_W, CELL_H).convert("RGBA")
        bg.alpha_composite(rgba)
        images.append(bg.convert("P", palette=Image.ADAPTIVE))
    
    if not images:
        return False
    
    duration = max(1, int(1000 / fps))
    images[0].save(
        out_path,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        disposal=2,
    )
    return True


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    jobs = load_jobs(run_dir)

    animation_mode = jobs.get("animation_mode", "pet")
    if animation_mode == "game":
        game_type = jobs.get("game_type", "full")
        if game_type == "platformer":
            all_rows = GAME_PLATFORMER_ROWS
        else:
            all_rows = GAME_CHARACTER_ROWS
    else:
        all_rows = ROW_ORDER

    qa_dir = run_dir / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = run_dir / "frames"

    # 1. 生成联系表
    contact_path = qa_dir / "contact-sheet.png"
    _build_contact_sheet(run_dir, contact_path, all_rows)
    print(f"wrote {contact_path}")

    # 2. 生成 GIF 动画
    gif_rows = args.gif_rows if args.gif_rows else all_rows
    gifs_dir = qa_dir / "gifs"
    gifs_dir.mkdir(parents=True, exist_ok=True)
    written_gifs: list[str] = []
    
    for row in gif_rows:
        if row not in all_rows:
            continue
        
        # 确定帧数
        num_frames = 8
        if row in ["crouch", "attack", "shoot", "hit", "pickup", "death"]:
            num_frames = 6
        
        gif = gifs_dir / f"{row}.gif"
        if _build_gif(run_dir, row, args.gif_fps, gif, num_frames):
            print(f"wrote {gif}")
            written_gifs.append(str(gif))

    # 3. 质量检查
    print("\n=== Quality Checks ===")
    
    frame_check_results = {}
    chroma_check_results = {}
    all_frames_ok = True
    all_chroma_ok = True
    
    for row in all_rows:
        # 检查帧存在
        frame_check = _check_frame_exists(frames_dir, row)
        frame_check_results[row] = frame_check
        
        if not frame_check["all_exist"]:
            print(f"[{row}] WARNING: Missing frames {frame_check['missing']}")
            all_frames_ok = False
        else:
            print(f"[{row}] Frames: {frame_check['found']}/{frame_check['expected']} OK")
        
        # 检查抠图质量
        chroma_results = []
        for i in range(frame_check["found"]):
            frame_path = frames_dir / f"{row}_{i}.png"
            if frame_path.exists():
                chroma = _check_chroma(frame_path, args.chroma_threshold)
                chroma_results.append(chroma)
                if not chroma["passed"]:
                    issues = []
                    if chroma["chroma_percent"] > 1.0:
                        issues.append(f"green:{chroma['chroma_percent']}%")
                    if chroma["blue_percent"] > 1.0:
                        issues.append(f"blue:{chroma['blue_percent']}%")
                    if chroma["white_percent"] > 1.0:
                        issues.append(f"white:{chroma['white_percent']}%")
                    # 黑色可能是角色阴影，不再作为失败条件
                    if issues:
                        print(f"[{row}_{i}] FAIL: {', '.join(issues)} (edge:{chroma['edge_percent']}%, black:{chroma['black_percent']}%)")
                    all_chroma_ok = False
        
        if chroma_results:
            avg_chroma = sum(r["chroma_percent"] for r in chroma_results) / len(chroma_results)
            avg_white = sum(r["white_percent"] for r in chroma_results) / len(chroma_results)
            avg_black = sum(r["black_percent"] for r in chroma_results) / len(chroma_results)
            avg_blue = sum(r["blue_percent"] for r in chroma_results) / len(chroma_results)
            avg_edge = sum(r["edge_percent"] for r in chroma_results) / len(chroma_results)
            avg_all_bg = sum(r["all_bg_percent"] for r in chroma_results) / len(chroma_results)
            chroma_check_results[row] = {
                "green_percent": round(avg_chroma, 2),
                "blue_percent": round(avg_blue, 2),
                "white_percent": round(avg_white, 2),
                "black_percent": round(avg_black, 2),
                "edge_percent": round(avg_edge, 2),
                "all_bg_percent": round(avg_all_bg, 2),
                "passed": chroma_results[0]["passed"],
                "frames": chroma_results
            }
    
    # 4. 生成报告
    summary = {
        "character_name": jobs.get("character_name"),
        "slug": jobs.get("slug"),
        "animation_mode": animation_mode,
        "game_type": jobs.get("game_type"),
        "quality_checks": {
            "all_frames_exist": all_frames_ok,
            "all_chroma_passed": all_chroma_ok,
            "chroma_threshold_percent": args.chroma_threshold
        },
        "frames": frame_check_results,
        "chroma": chroma_check_results,
        "rows": {row: jobs.get("jobs", {}).get(row, {}).get("status", "unknown") for row in all_rows},
        "contact_sheet": str(contact_path),
        "gifs": written_gifs,
    }
    
    summary_path = qa_dir / "run-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(f"\nwrote {summary_path}")
    
    # 5. 文本报告
    report_lines = [
        f"QA Report for {jobs.get('character_name', 'Unknown')}",
        "=" * 50,
        f"Animation Mode: {animation_mode}",
        f"Game Type: {jobs.get('game_type', 'N/A')}",
        "",
        "Frame Check Results:",
        "-" * 30,
    ]
    
    for row, result in frame_check_results.items():
        status = "OK" if result["all_exist"] else "MISSING"
        report_lines.append(f"  {row}: {result['found']}/{result['expected']} frames [{status}]")
    
    report_lines.extend([
        "",
        "Edge Quality Check Results:",
        "-" * 50,
    ])
    
    for row, result in chroma_check_results.items():
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        report_lines.append(f"  {row}: {status}")
        report_lines.append(f"    edge:    {result['edge_percent']}% (non-transparent)")
        report_lines.append(f"    green:   {result['green_percent']}%")
        report_lines.append(f"    blue:    {result['blue_percent']}%")
        report_lines.append(f"    white:   {result['white_percent']}%")
        report_lines.append(f"    black:   {result['black_percent']}%")
        report_lines.append(f"    total:   {result['all_bg_percent']}%")
    
    report_lines.extend([
        "",
        "=" * 50,
        f"Overall: {'PASSED' if all_frames_ok and all_chroma_ok else 'ISSUES FOUND'}",
    ])
    
    chroma_report_path = qa_dir / "chroma-report.txt"
    chroma_report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"wrote {chroma_report_path}")
    
    return 0 if (all_frames_ok and all_chroma_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())

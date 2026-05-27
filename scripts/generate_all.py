#!/usr/bin/env python3
"""Generate all characters for a game project.

This script generates both player and enemy characters with distinct appearances.

Usage:
    python generate_all.py --player "Cat Soldier" --enemy "Dog Soldier" --output-dir ./run
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from slugify import slugify


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate all game characters.")
    p.add_argument("--player", required=True, help="Player character name")
    p.add_argument("--player-desc", default="", help="Player character description")
    p.add_argument("--enemy", required=True, help="Enemy character name")
    p.add_argument("--enemy-desc", default="", help="Enemy character description")
    p.add_argument("--output-dir", required=True, help="Output directory for run/")
    p.add_argument("--style", default="platformer-16bit", help="Art style")
    p.add_argument("--category", default="Action Adventure", help="Category")
    p.add_argument("--game-type", default="platformer", help="Game type")
    p.add_argument("--force", action="store_true", help="Force regenerate existing")
    return p.parse_args()


def run_script(script_name: str, args: list[str], cwd: str = None) -> int:
    """Run a script and return exit code."""
    cmd = [sys.executable, script_name] + args
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def generate_character(
    name: str,
    description: str,
    output_dir: str,
    style: str,
    category: str,
    game_type: str,
    force: bool = False
) -> tuple[str, bool]:
    """Generate a single character.

    Returns (slug, success)
    """
    slug = slugify(name)
    char_dir = Path(output_dir) / slug

    if char_dir.exists() and not force:
        print(f"  Character {slug} already exists, skipping generation")
        return slug, True

    scripts_dir = Path(__file__).parent

    print(f"\nGenerating {name} ({slug})...")

    if not char_dir.exists():
        char_dir.mkdir(parents=True)

    prepare_args = [
        "--animation-mode", "game",
        "--game-type", game_type,
        "--character-name", name,
        "--description", description,
        "--style", style,
        "--category", category,
        "--output-dir", str(char_dir)
    ]

    if run_script("prepare_run.py", prepare_args, cwd=scripts_dir) != 0:
        print(f"  Failed to prepare {name}")
        return slug, False

    generate_args = [
        "--run-dir", str(char_dir),
        "--row", "all",
        "--mode", "grid"
    ]
    if force:
        generate_args.append("--force")

    if run_script("generate_row.py", generate_args, cwd=scripts_dir) != 0:
        print(f"  Failed to generate {name}")
        return slug, False

    extract_args = ["--run-dir", str(char_dir)]
    if run_script("extract_frames.py", extract_args, cwd=scripts_dir) != 0:
        print(f"  Failed to extract frames for {name}")
        return slug, False

    chroma_args = ["--run-dir", str(char_dir)]
    if run_script("chroma_key.py", chroma_args, cwd=scripts_dir) != 0:
        print(f"  Failed to chroma key {name}")
        return slug, False

    compose_args = ["--run-dir", str(char_dir)]
    if run_script("compose_atlas.py", compose_args, cwd=scripts_dir) != 0:
        print(f"  Failed to compose atlas for {name}")
        return slug, False

    print(f"  Successfully generated {name}")
    return slug, True


def package_character(
    run_dir: str,
    slug: str,
    target_dir: str
) -> bool:
    """Package a character to assets directory."""
    scripts_dir = Path(__file__).parent
    char_dir = Path(run_dir) / slug

    if not char_dir.exists():
        print(f"  Character directory not found: {char_dir}")
        return False

    package_args = [
        "--run-dir", str(char_dir),
        "--slug", slug,
        "--output-dir", target_dir
    ]

    if run_script("package_pet.py", package_args, cwd=scripts_dir) != 0:
        print(f"  Failed to package {slug}")
        return False

    return True


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()

    print("=" * 60)
    print("Generate All Game Characters")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Player: {args.player}")
    print(f"Enemy: {args.enemy}")
    print()

    player_desc = args.player_desc or f"A brave {args.player} hero character"
    enemy_desc = args.enemy_desc or f"A fierce {args.enemy} enemy character"

    player_slug, player_ok = generate_character(
        name=args.player,
        description=player_desc,
        output_dir=str(output_dir),
        style=args.style,
        category=args.category,
        game_type=args.game_type,
        force=args.force
    )

    if not player_ok:
        print("Player generation failed!")
        return 1

    enemy_slug, enemy_ok = generate_character(
        name=args.enemy,
        description=enemy_desc,
        output_dir=str(output_dir),
        style=args.style,
        category=args.category,
        game_type=args.game_type,
        force=args.force
    )

    if not enemy_ok:
        print("Enemy generation failed!")
        return 1

    print("\n" + "=" * 60)
    print("Packaging to assets/")
    print("=" * 60)

    assets_dir = output_dir.parent / "assets" / "characters"

    print(f"\nPackaging player to {assets_dir / 'player'}...")
    if not package_character(str(output_dir), player_slug, str(assets_dir / "player")):
        return 1

    print(f"Packaging enemy to {assets_dir / 'enemy'}...")
    if not package_character(str(output_dir), enemy_slug, str(assets_dir / "enemy")):
        return 1

    print("\n" + "=" * 60)
    print("All characters generated successfully!")
    print("=" * 60)
    print(f"Player: assets/characters/player/")
    print(f"Enemy: assets/characters/enemy/")
    print()
    print("Next steps:")
    print("1. Check generated spritesheets in assets/characters/")
    print("2. Update game code to use the characters")
    print("3. Run the game to test")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

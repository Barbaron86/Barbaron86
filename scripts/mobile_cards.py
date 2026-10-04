"""Render a separate mobile glass card around the full annual snake animation.

The existing Snake workflow CLI is retained. Streak's mobile assets are now
generated directly from its statistics by generate_streak.py.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from activity_cards import write_svg
from glass_snake import wrap_snake


def mobile_snake(svg: str, theme_name: str) -> str:
    """Keep all annual cells and keyframes, using a uniform nested SVG viewport."""
    return wrap_snake(svg, theme_name, mobile=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("snake",))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--theme", choices=("light", "dark"), required=True)
    args = parser.parse_args()
    source = args.input.read_text(encoding="utf-8")
    write_svg(mobile_snake(source, args.theme), args.output)


if __name__ == "__main__":
    main()

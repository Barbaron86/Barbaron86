"""Fit the existing desktop Streak and Snake SVGs into 600 × 224 mobile cards.

Keep desktop geometry, SVG metadata, contribution details and snake animation.
Do not construct an alternative mobile dashboard from a subset of the data.
"""
from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from glass_snake import wrap_snake

SVG_NS = "{http://www.w3.org/2000/svg}"
MOBILE_WIDTH = 600
MOBILE_HEIGHT = 224
TAGLINE = re.compile(r"<text\b[^>]*>\s*Every day counts\s*</text>\s*")


def fit_desktop_svg(svg: str, original_width: int, original_height: int) -> str:
    """Resize the SVG viewport; retain all existing child nodes and coordinates.

    A non-uniform viewport fit is intentional: the whole desktop card fills
    600 × 224 without clipping any of the metrics or the contribution grid.
    """
    root = ET.fromstring(svg)
    if root.tag != f"{SVG_NS}svg":
        raise ValueError("Expected an SVG root")
    if (root.get("width"), root.get("height")) != (
        str(original_width), str(original_height)
    ):
        raise ValueError("Unexpected desktop card dimensions")

    def resize(match: re.Match[str]) -> str:
        tag = match.group(0)
        tag = re.sub(r'\bwidth="[^"]+"', f'width="{MOBILE_WIDTH}"', tag, count=1)
        tag = re.sub(r'\bheight="[^"]+"', f'height="{MOBILE_HEIGHT}"', tag, count=1)
        if 'preserveAspectRatio="' in tag:
            tag = re.sub(
                r'\bpreserveAspectRatio="[^"]+"',
                'preserveAspectRatio="none"', tag, count=1,
            )
        else:
            tag = tag[:-1] + ' preserveAspectRatio="none">'
        return tag

    result = re.sub(r"<svg\b[^>]*>", resize, svg, count=1)
    ET.fromstring(result)
    return result if result.endswith("\n") else result + "\n"


def mobile_streak(svg: str, theme_name: str) -> str:
    """Preserve all desktop Streak statistics and remove the old tagline."""
    if theme_name not in ("light", "dark"):
        raise ValueError(f"Unsupported Streak theme: {theme_name}")
    svg = TAGLINE.sub("", svg)
    return fit_desktop_svg(svg, original_width=940, original_height=258)


def mobile_snake(svg: str, theme_name: str) -> str:
    """Apply the *desktop* Liquid Glass styling and keep all snake keyframes."""
    styled = wrap_snake(svg, theme_name)
    if "@keyframes" not in styled:
        raise ValueError("Missing original snake animation")
    return fit_desktop_svg(styled, original_width=880, original_height=235)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("streak", "snake"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--theme", choices=("light", "dark"), required=True)
    args = parser.parse_args()
    source = args.input.read_text(encoding="utf-8")
    svg = (mobile_streak if args.kind == "streak" else mobile_snake)(
        source, args.theme
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()

"""Create mobile 600x224 Streak and Snake cards from the normal generated SVGs.

Desktop cards remain untouched. Snake animation and all contribution weeks survive.
"""
from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

from generate_streak import THEMES
from glass_snake import THEMES as SNAKE_THEMES

SVG_NS = "{http://www.w3.org/2000/svg}"


def mobile_streak(svg: str, theme_name: str) -> str:
    """Read already calculated desktop statistics and lay them out for mobile."""
    root = ET.fromstring(svg)
    if root.get("width") != "940" or root.get("height") != "258":
        raise ValueError("Unexpected desktop Streak dimensions")
    values = {}
    positions = {
        "current": ("144", "123"),
        "range": ("144", "174"),
        "total": ("396", "105"),
        "longest": ("608", "105"),
        "year": ("819", "105"),
        "active": ("396", "207"),
    }
    for name, (x, y) in positions.items():
        found = [el for el in root.iter(f"{SVG_NS}text")
                 if el.get("x") == x and el.get("y") == y]
        if len(found) != 1:
            raise ValueError(f"Missing Streak field: {name}")
        values[name] = escape("".join(found[0].itertext()).strip().split(" days")[0])
    theme = THEMES[theme_name]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="224" viewBox="0 0 600 224" role="img" aria-label="Mobile GitHub Streak statistics">
<defs>
<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{theme["BG_START"]}"/><stop offset="1" stop-color="{theme["BG_END"]}"/></linearGradient>
<linearGradient id="accent" x1="0" y1="1" x2="1" y2="0"><stop stop-color="{theme["BLUE"]}"/><stop offset=".55" stop-color="{theme["PURPLE"]}"/><stop offset="1" stop-color="{theme["PINK"]}"/></linearGradient>
<linearGradient id="mountain" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{theme["BLUE"]}" stop-opacity=".22"/><stop offset="1" stop-color="{theme["PURPLE"]}" stop-opacity=".02"/></linearGradient>
<clipPath id="round"><rect x="1" y="1" width="598" height="222" rx="23"/></clipPath>
</defs>
<rect x="1" y="1" width="598" height="222" rx="23" fill="url(#panel)" stroke="{theme["BORDER"]}" stroke-width="1.5"/>
<g clip-path="url(#round)">
<path d="M0 220 44 171 90 216 146 185 193 224 269 197 350 224 427 183 507 221 560 193 600 221V224H0Z" fill="url(#mountain)"/>
<path d="M2 2H598" stroke="{theme["HIGHLIGHT"]}" stroke-opacity=".4"/>
<rect x="14" y="15" width="238" height="193" rx="18" fill="{theme["GLASS"]}" fill-opacity="{theme["GLASS_OPACITY"]}" stroke="{theme["INNER_BORDER"]}"/>
<rect x="14" y="15" width="238" height="3" rx="1.5" fill="url(#accent)"/>
<path d="M426 64V197M274 124H577" stroke="{theme["DIVIDER"]}" stroke-opacity="{theme["DIVIDER_OPACITY"]}"/>
</g>
<g font-family="Segoe UI,Arial,sans-serif">
<text x="30" y="42" fill="{theme["MUTED"]}" font-size="17" font-weight="700" letter-spacing="1">GITHUB STREAK</text>
<circle cx="232" cy="36" r="4" fill="{theme["PINK"]}"/>
<text x="133" y="125" text-anchor="middle" fill="{theme["PRIMARY"]}" font-size="75" font-weight="750">{values["current"]}</text>
<text x="133" y="151" text-anchor="middle" fill="{theme["PURPLE"]}" font-size="14" font-weight="700">CURRENT STREAK · DAYS</text>
<text x="133" y="173" text-anchor="middle" fill="{theme["MUTED"]}" font-size="10">{values["range"]}</text>
<rect x="48" y="188" width="168" height="5" rx="2.5" fill="{theme["TRACK"]}"/>
<rect x="48" y="188" width="168" height="5" rx="2.5" fill="url(#accent)"/>
<text x="33" y="207" fill="{theme["MUTED"]}" font-size="10">Every day counts</text>
<text x="347" y="77" text-anchor="middle" fill="{theme["MUTED"]}" font-size="12">TOTAL</text>
<text x="347" y="111" text-anchor="middle" fill="{theme["PRIMARY"]}" font-size="30" font-weight="700">{values["total"]}</text>
<text x="499" y="77" text-anchor="middle" fill="{theme["MUTED"]}" font-size="12">LONGEST</text>
<text x="499" y="111" text-anchor="middle" fill="{theme["PURPLE"]}" font-size="30" font-weight="700">{values["longest"]}</text>
<text x="347" y="153" text-anchor="middle" fill="{theme["MUTED"]}" font-size="12">THIS YEAR</text>
<text x="347" y="188" text-anchor="middle" fill="{theme["BLUE"]}" font-size="28" font-weight="700">{values["year"]}</text>
<text x="499" y="153" text-anchor="middle" fill="{theme["MUTED"]}" font-size="12">ACTIVE DAYS</text>
<text x="499" y="188" text-anchor="middle" fill="{theme["PRIMARY"]}" font-size="28" font-weight="700">{values["active"]}</text>
</g></svg>
'''


def mobile_snake(svg: str, theme_name: str) -> str:
    """Use original animation, enlarging the grid vertically for the mobile card."""
    ET.fromstring(svg)
    if 'id="glass-snake-bg"' in svg:
        raise ValueError("Mobile Snake must be generated from the raw snk SVG")
    if "</style>" not in svg:
        raise ValueError("Missing snake animation stylesheet")
    theme = SNAKE_THEMES[theme_name]
    panel = f'''<defs>
<linearGradient id="mobile-panel" x1="0" y1="0" x2="1" y2="1">
<stop stop-color="{theme["start"]}"/><stop offset="1" stop-color="{theme["end"]}"/>
</linearGradient>
<linearGradient id="mobile-mountain" x1="0" y1="0" x2="0" y2="1">
<stop stop-color="{theme["blue"]}" stop-opacity=".2"/>
<stop offset="1" stop-color="{theme["glow"]}" stop-opacity=".02"/>
</linearGradient>
<clipPath id="mobile-panel-clip"><rect x="1" y="1" width="598" height="222" rx="23"/></clipPath>
<clipPath id="mobile-grid-clip"><rect x="15" y="57" width="571" height="148"/></clipPath>
</defs>
<g id="glass-snake-mobile">
<rect x="1" y="1" width="598" height="222" rx="23" fill="url(#mobile-panel)" stroke="{theme["border"]}" stroke-width="1.5"/>
<g clip-path="url(#mobile-panel-clip)">
<path d="M1 219 54 186 101 219 182 192 241 224 338 195 418 224 518 189 599 218V224H1Z" fill="url(#mobile-mountain)"/>
<path d="M2 2H598" stroke="{theme["glass"]}" stroke-opacity=".4"/>
</g>
<text x="25" y="36" fill="{theme["text"]}" font-family="Segoe UI,Arial,sans-serif" font-size="21" font-weight="700">CONTRIBUTION SNAKE</text>
<text x="575" y="36" text-anchor="end" fill="{theme["muted"]}" font-family="Segoe UI,Arial,sans-serif" font-size="11">GitHub activity</text>
</g><g clip-path="url(#mobile-grid-clip)"><g transform="translate(17 58) scale(.67 .94)">'''
    svg = re.sub(
        r"<svg\b[^>]*>",
        lambda m: re.sub(
            r'viewBox="[^"]+"', 'viewBox="0 0 600 224"',
            re.sub(r'height="[^"]+"', 'height="224"',
                   re.sub(r'width="[^"]+"', 'width="600"', m.group(0)))),
        svg, count=1,
    )
    svg = svg.replace("</style>", "</style>" + panel, 1)
    svg = svg.replace("</svg>", "</g></g></svg>", 1)
    ET.fromstring(svg)
    return svg if svg.endswith("\n") else svg + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("streak", "snake"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--theme", choices=("light", "dark"), required=True)
    args = parser.parse_args()
    content = args.input.read_text(encoding="utf-8")
    result = (mobile_streak if args.kind == "streak" else mobile_snake)(content, args.theme)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")


if __name__ == "__main__":
    main()

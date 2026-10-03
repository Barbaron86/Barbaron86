"""Add a lightweight Liquid Glass panel to the animated Platane/snk SVG.

Retain original snake animation and contribution geometry.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
import xml.etree.ElementTree as ET

THEMES = {
    "dark": {"start": "#101c39", "end": "#1d122e", "border": "#6a64bd", "text": "#f0f6fc", "muted": "#a7badb", "glow": "#a855f7", "blue": "#258bff", "glass": "#f0f6fc"},
    "light": {"start": "#edf5ff", "end": "#faeafa", "border": "#a5b7e2", "text": "#162644", "muted": "#54647e", "glow": "#ca68dc", "blue": "#3e8def", "glass": "#ffffff"},
}


def wrap_snake(content: str, theme_name: str) -> str:
    """Add background and headings, without modifying CSS keyframes."""
    ET.fromstring(content)
    if 'id="glass-snake-bg"' in content:
        raise ValueError("Input is already glass-styled")
    theme = THEMES[theme_name]
    if not re.search(r"<svg\b[^>]*>", content):
        raise ValueError("Expected snk SVG root")
    if "</style>" not in content:
        raise ValueError("Expected snk stylesheet; do not replace animations")
    header = f'''<defs>
  <linearGradient id="glass-snake-gradient" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{theme['start']}"/><stop offset="1" stop-color="{theme['end']}"/></linearGradient>
  <linearGradient id="glass-snake-mountain" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{theme['blue']}" stop-opacity=".19"/><stop offset="1" stop-color="{theme['glow']}" stop-opacity=".015"/></linearGradient>
  <clipPath id="glass-snake-clip"><rect x="-15" y="-55" width="878" height="232" rx="17"/></clipPath>
</defs>'''
    panel = f'''<g id="glass-snake-bg">
<rect x="-15" y="-55" width="878" height="232" rx="17" fill="url(#glass-snake-gradient)" stroke="{theme['border']}" stroke-width="1.4"/>
<g clip-path="url(#glass-snake-clip)">
<path d="M-15 170 66 124 113 167 209 135 277 167 405 137 524 175 653 128 754 168 863 139V177H-15Z" fill="url(#glass-snake-mountain)"/>
<path d="M-15-54H863" stroke="{theme['glass']}" stroke-opacity=".4"/>
</g>
<text x="15" y="-35" fill="{theme['text']}" font-family="Segoe UI,Arial,sans-serif" font-size="14" font-weight="700" letter-spacing="1">CONTRIBUTION SNAKE</text>
<text x="850" y="-35" text-anchor="end" fill="{theme['muted']}" font-family="Segoe UI,Arial,sans-serif" font-size="11">GitHub activity</text>
</g>'''
    content = re.sub(r"<svg\b[^>]*>", lambda match: re.sub(r'viewBox="[^"]+"', 'viewBox="-16 -56 880 235"', re.sub(r'height="[^"]+"', 'height="235"', match.group(0))), content, count=1)
    content = content.replace("</style>", "</style>" + header + panel, 1)
    ET.fromstring(content)
    return content if content.endswith("\n") else content + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--theme", choices=tuple(THEMES), required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(wrap_snake(args.input.read_text(encoding="utf-8"), args.theme), encoding="utf-8")


if __name__ == "__main__":
    main()

"""Frame the complete Platane/snk animation without changing its geometry."""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from activity_cards import SVG_NS, glass_frame, validate_svg, write_svg

SVG_START = re.compile(r"<svg\b[^>]*>")


def _animation_viewport(content: str, width: int, height: int, padding: int) -> str:
    """Change only viewport placement; keep the source viewBox and body intact."""
    def position(match: re.Match[str]) -> str:
        tag = match.group()
        attributes = {
            "id": "snake-animation", "x": str(padding), "y": "44",
            "width": str(width - 2 * padding), "height": str(height - 60),
            "preserveAspectRatio": "xMidYMid meet",
        }
        for name, value in attributes.items():
            pattern = rf'''(?<=\s){name}\s*=\s*(["']).*?\1'''
            replacement = f'{name}="{value}"'
            if re.search(pattern, tag):
                tag = re.sub(pattern, lambda _: replacement, tag, count=1)
            else:
                tag = tag[:-1] + f" {replacement}>"
        return tag

    return SVG_START.sub(position, content, count=1)


def wrap_snake(content: str, theme_name: str, *, mobile: bool = False) -> str:
    """Give the annual grid its own card and uniformly fit the original animation."""
    validate_svg(content)
    root = ET.fromstring(content)
    if (root.find('.//*[@id="snake-animation"]') is not None
            or root.find('.//*[@id="glass-snake-bg"]') is not None
            or root.get("id") == "snake-animation"):
        raise ValueError("Input is already glass-styled")
    stylesheet = root.find(f"{{{SVG_NS}}}style")
    if stylesheet is None:
        raise ValueError("Expected the snk stylesheet and contribution grid")
    opening = SVG_START.search(content)
    if opening is None:
        raise ValueError("Expected an SVG root")

    width, height = (600, 224) if mobile else (880, 235)
    original_description = root.find(f"{{{SVG_NS}}}desc")
    attribution = "" if original_description is None else "".join(original_description.itertext())
    animation = _animation_viewport(content[opening.start():], width, height, 28 if mobile else 16)
    # snk already defines each cell's initial contribution fill outside keyframes.
    # Keep those rules; hide moving elements when motion is unavailable or reduced.
    motion_supported = ""
    if "@keyframes" in (stylesheet.text or ""):
        motion_supported = '''@supports (animation-name: snk) {
  #snake-animation .s, #snake-animation .u { visibility: visible; }
}'''
    rendered = f'''<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="snake-title snake-description">
<title id="snake-title">GitHub contribution snake</title>
<desc id="snake-description">Annual GitHub contribution grid. Color intensity represents contribution levels; the snake consumes active cells. The complete original animation is fitted uniformly without cropping. With reduced motion, the original activity grid remains visible. {escape(attribution)}</desc>
{glass_frame(width, height, theme_name)}
<g id="snake-light-arc" transform="translate({(width - 600) / 2:g} 0)" fill="none" stroke="url(#activity-accent)">
  <path d="M105 33C185 15 213 44 294 29S404 16 495 32" stroke-width="2" stroke-opacity="{'.36' if theme_name == 'dark' else '.27'}"/>
  <path d="M140 33C228 19 284 41 368 28S431 22 461 30" stroke-width="1" stroke-opacity=".15"/>
</g>
<style>
#snake-animation .s, #snake-animation .u {{ visibility: hidden; }}
{motion_supported}
@media (prefers-reduced-motion: reduce) {{
  #snake-animation .c, #snake-animation .s, #snake-animation .u {{ animation: none !important; }}
  #snake-animation .s, #snake-animation .u {{ visibility: hidden; }}
}}
</style>
{animation}
</svg>
'''
    validate_svg(rendered)
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--theme", choices=("light", "dark"), required=True)
    args = parser.parse_args()
    content = wrap_snake(args.input.read_text(encoding="utf-8"), args.theme)
    write_svg(content, args.output)


if __name__ == "__main__":
    main()

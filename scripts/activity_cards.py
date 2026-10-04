"""Shared Liquid Glass surfaces and safe output for GitHub activity cards."""
from __future__ import annotations

import math
import os
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"

THEMES = {
    "dark": {
        "BG_START": "#08243e", "BG_MIDDLE": "#0d1117", "BG_END": "#21132e",
        "BLUE": "#4aa7ff", "PURPLE": "#bb83ff", "PINK": "#fa6cbd",
        "CORNER": "#8deaff", "CORNER_OPACITY": "0.65",
        "GLASS": "#ffffff", "GLASS_OPACITY": "0.065",
        "INNER_BORDER": "#514b86", "DIVIDER": "#8ea9ea",
        "DIVIDER_OPACITY": "0.22", "PRIMARY": "#f0f6fc",
        "MUTED": "#a8b5d6", "TRACK": "#273351",
        "HALO_OPACITY": "0.32", "GLASS_START": "0.09",
        "GLASS_END": "0.01", "MOUNTAIN_OPACITY": "0.32",
        "HIGHLIGHT_OPACITY": "0.12",
    },
    "light": {
        "BG_START": "#e6f5ff", "BG_MIDDLE": "#ffffff", "BG_END": "#fbedfa",
        "BLUE": "#2473db", "PURPLE": "#8655c6", "PINK": "#e53d87",
        "CORNER": "#2473db", "CORNER_OPACITY": "0.85",
        "GLASS": "#ffffff", "GLASS_OPACITY": "0.7",
        "INNER_BORDER": "#b2badd", "DIVIDER": "#809de0",
        "DIVIDER_OPACITY": "0.22", "PRIMARY": "#142542",
        "MUTED": "#536682", "TRACK": "#cfdaed",
        "HALO_OPACITY": "0.16", "GLASS_START": "0.65",
        "GLASS_END": "0.22", "MOUNTAIN_OPACITY": "0.22",
        "HIGHLIGHT_OPACITY": "0.65",
    },
}


def theme_colors(theme_name: str) -> dict[str, str]:
    """Return the activity palette, rejecting unsupported themes explicitly."""
    try:
        return THEMES[theme_name]
    except KeyError as error:
        raise ValueError(f"Unsupported activity theme: {theme_name}") from error


def fitted_size(value: object, maximum: float, available: float) -> str:
    """Keep normal values at full size and reserve room for unusually long ones."""
    size = min(maximum, available / max(len(str(value)) * 0.62, 1))
    return f"{size:.2f}"


def glass_frame(width: int, height: int, theme_name: str) -> str:
    """Use the coding cards' corner and two mountain paths at activity sizes."""
    t = theme_colors(theme_name)
    return f'''<defs>
  <linearGradient id="activity-background" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{t['BG_START']}"/><stop offset=".55" stop-color="{t['BG_MIDDLE']}"/><stop offset="1" stop-color="{t['BG_END']}"/></linearGradient>
  <linearGradient id="activity-border" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{t['CORNER']}"/><stop offset=".3" stop-color="{t['BLUE']}" stop-opacity=".5"/><stop offset=".68" stop-color="{t['PURPLE']}" stop-opacity=".65"/><stop offset="1" stop-color="{t['PINK']}"/></linearGradient>
  <linearGradient id="activity-accent"><stop stop-color="{t['BLUE']}"/><stop offset=".58" stop-color="{t['PURPLE']}"/><stop offset="1" stop-color="{t['PINK']}"/></linearGradient>
  <radialGradient id="activity-halo"><stop stop-color="{t['BLUE']}" stop-opacity="{t['HALO_OPACITY']}"/><stop offset="1" stop-color="{t['BLUE']}" stop-opacity="0"/></radialGradient>
  <radialGradient id="activity-violet"><stop stop-color="{t['PURPLE']}" stop-opacity=".18"/><stop offset="1" stop-color="{t['PURPLE']}" stop-opacity="0"/></radialGradient>
  <linearGradient id="activity-glass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ffffff" stop-opacity="{t['GLASS_START']}"/><stop offset=".5" stop-color="#ffffff" stop-opacity="{t['GLASS_END']}"/><stop offset="1" stop-color="{t['PINK']}" stop-opacity=".04"/></linearGradient>
  <linearGradient id="activity-mountain" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{t['BLUE']}" stop-opacity="{t['MOUNTAIN_OPACITY']}"/><stop offset="1" stop-color="{t['PURPLE']}" stop-opacity=".025"/></linearGradient>
  <linearGradient id="activity-ridge"><stop stop-color="{t['BLUE']}" stop-opacity=".18"/><stop offset="1" stop-color="{t['PINK']}" stop-opacity=".06"/></linearGradient>
  <clipPath id="activity-card"><rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="23"/></clipPath>
</defs>
<g clip-path="url(#activity-card)">
  <rect width="{width}" height="{height}" fill="url(#activity-background)"/>
  <ellipse cx="30" cy="12" rx="{205 * width / 600:g}" ry="125" fill="url(#activity-halo)"/>
  <ellipse cx="{width - 38}" cy="5" rx="{220 * width / 600:g}" ry="150" fill="url(#activity-violet)"/>
  <rect x="8" y="8" width="{width - 16}" height="{height - 16}" rx="20" fill="url(#activity-glass)"/>
  <g transform="scale({width / 600:g} {height / 224:g})">
    <path d="M0 178L30 148Q36 142 42 150L68 187L87 179L139 215L205 193L277 224H0Z" fill="url(#activity-mountain)"/>
    <path d="M0 214L72 182L118 215L170 224L245 191L322 224L394 207L496 224H0Z" fill="url(#activity-ridge)"/>
    <path d="M0 178L30 148Q36 142 42 150L68 187M170 224L245 191L322 224" fill="none" stroke="{t['BLUE']}" stroke-opacity=".22"/>
  </g>
  <path d="M22 14H{width - 23}" stroke="#ffffff" stroke-opacity="{t['HIGHLIGHT_OPACITY']}"/>
</g>
<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="23" fill="none" stroke="url(#activity-border)" stroke-width="1.5"/>
<path id="brand-corner" d="M4 45V25Q4 4 25 4H65" fill="none" stroke="{t['CORNER']}" stroke-opacity="{t['CORNER_OPACITY']}" stroke-width="2"/>
'''


def validate_svg(content: str) -> None:
    """Reject incomplete or invalid SVGs before any destination is touched."""
    root = ET.fromstring(content)
    if root.tag != f"{{{SVG_NS}}}svg" or re.search(r"\{\{[A-Z_]+\}\}", content):
        raise ValueError("Expected a complete SVG document")
    try:
        viewport = [float(value) for value in root.attrib["viewBox"].split()]
    except (KeyError, ValueError) as error:
        raise ValueError("SVG has no valid viewport") from error
    if (len(viewport) != 4 or not all(map(math.isfinite, viewport))
            or viewport[2] <= 0 or viewport[3] <= 0):
        raise ValueError("SVG viewport dimensions must be positive and finite")


def write_svg(content: str, path: Path) -> None:
    """Validate, then atomically replace one generated asset on the same volume."""
    validate_svg(content)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content.rstrip() + "\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

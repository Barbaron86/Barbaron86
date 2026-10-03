"""Deterministic, self-contained glass/gradient SVG rendering."""

from pathlib import Path
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

THEMES = {
    "dark": {"bg": "#0D1117", "text": "#F0F6FC", "muted": "#A5B4CF", "line": "#8EA9EA", "track": "#25324D", "panel": "#13182C", "white": "#FFFFFF", "green": "#00D68F", "yellow": "#FFB800", "red": "#FF586D"},
    "light": {"bg": "#FFFFFF", "text": "#0B1530", "muted": "#405B8B", "line": "#809DE0", "track": "#DAE5F4", "panel": "#FFFFFF", "white": "#FFFFFF", "green": "#00875A", "yellow": "#A36300", "red": "#D62243"},
}

# Source: Simple Icons, CC0; see docs/coding-practice.md. Invert the square
# silhouette in a mask to expose the original circular Codewars mark.
CODEWARS_PATH = ET.parse(Path(__file__).resolve().parents[1] / "assets" / "codewars-logo.svg").getroot().find("{http://www.w3.org/2000/svg}path").attrib["d"]


def label(x: float, y: float, value: object, theme: dict[str, str], *, size: float = 16,
          color: str | None = None, weight: int = 400, anchor: str = "start") -> str:
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color or theme["text"]}" '
            f'font-family="Segoe UI,Arial,sans-serif" font-size="{size}" '
            f'font-weight="{weight}">{escape(str(value))}</text>')


def fitted_size(value: str, maximum: float, available: float) -> float:
    return round(min(maximum, available / max(len(value) * 0.62, 1)), 2)


def svg_start(platform: str, username: str, variant: str, description: str) -> str:
    theme = THEMES[variant]
    dark = variant == "dark"
    cw = platform == "Codewars"
    left = "#FF4269" if cw else "#259BFF"
    right = "#FF8C78" if cw else "#C971EC"
    sky = "#A855F7" if cw else "#1555C3"
    a, b = (("#241729", "#10152B") if cw else ("#08243E", "#11122B")) if dark else (("#FFF1F6", "#EDF4FF") if cw else ("#E6F5FF", "#F6F0FF"))
    title = f"{platform} statistics for {username}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="224" viewBox="0 0 600 224" role="img" aria-labelledby="title desc" aria-label={quoteattr(title)}>
<title id="title">{escape(title)}</title>
<desc id="desc">{escape(description)}</desc>
<defs>
  <linearGradient id="background" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{a}"/><stop offset=".55" stop-color="{theme['bg']}"/><stop offset="1" stop-color="{b}"/></linearGradient>
  <linearGradient id="border" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{'#95E8FF' if not cw else '#EBA5D7'}"/><stop offset=".3" stop-color="{left}" stop-opacity=".5"/><stop offset=".68" stop-color="{sky}" stop-opacity=".65"/><stop offset="1" stop-color="{right}"/></linearGradient>
  <radialGradient id="halo"><stop stop-color="{left}" stop-opacity="{'.4' if dark else '.18'}"/><stop offset="1" stop-color="{left}" stop-opacity="0"/></radialGradient>
  <radialGradient id="violet"><stop stop-color="{sky}" stop-opacity="{'.24' if dark else '.1'}"/><stop offset="1" stop-color="{sky}" stop-opacity="0"/></radialGradient>
  <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#FFFFFF" stop-opacity="{'.09' if dark else '.65'}"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity="{'.01' if dark else '.22'}"/><stop offset="1" stop-color="{right}" stop-opacity=".04"/></linearGradient>
  <linearGradient id="mountain" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{left}" stop-opacity="{'.32' if dark else '.22'}"/><stop offset="1" stop-color="{left}" stop-opacity=".025"/></linearGradient>
  <linearGradient id="ridge" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{left}" stop-opacity=".18"/><stop offset="1" stop-color="{right}" stop-opacity=".06"/></linearGradient>
  <clipPath id="card"><rect x="1" y="1" width="598" height="222" rx="23"/></clipPath>
</defs>
<g clip-path="url(#card)">
  <rect width="600" height="224" fill="url(#background)"/>
  <ellipse cx="30" cy="12" rx="205" ry="125" fill="url(#halo)"/>
  <ellipse cx="562" cy="5" rx="220" ry="150" fill="url(#violet)"/>
  <rect x="8" y="8" width="584" height="208" rx="20" fill="url(#glass)"/>
  <path d="M0 178L30 148Q36 142 42 150L68 187L87 179L139 215L205 193L277 224H0Z" fill="url(#mountain)"/>
  <path d="M0 214L72 182L118 215L170 224L245 191L322 224L394 207L496 224H0Z" fill="url(#ridge)"/>
  <path d="M0 178L30 148Q36 142 42 150L68 187M170 224L245 191L322 224" fill="none" stroke="{left}" stroke-opacity="{'.28' if dark else '.15'}"/>
  <path d="M22 14H577" stroke="#FFFFFF" stroke-opacity="{'.12' if dark else '.65'}"/>
</g>
<rect x="1" y="1" width="598" height="222" rx="23" fill="none" stroke="url(#border)" stroke-width="1.5"/>
<path d="M4 45V25Q4 4 25 4H65" fill="none" stroke="{'#8DEAFF' if not cw else '#F799C8'}" stroke-opacity=".55" stroke-width="2"/>
'''


def leetcode_logo(theme: dict[str, str]) -> str:
    return (f'<g transform="translate(33 27)" fill="none" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M36 6L18 24M27 20L45 37M26 58L40 44" stroke="#FFB21D" stroke-width="7"/>'
            f'<path d="M36 2L5 33Q0 38 5 43L25 63" stroke="{theme["text"]}" stroke-width="7"/>'
            '<path d="M20 37H50" stroke="#93A2B8" stroke-width="7"/></g>')


def codewars_logo() -> str:
    return (f'<defs><mask id="cw-mark" maskUnits="userSpaceOnUse" x="0" y="0" width="24" height="24">'
            f'<rect width="24" height="24" fill="white"/><path d="{CODEWARS_PATH}" fill="black"/></mask></defs>'
            '<g transform="translate(32 27) scale(2.6)"><circle cx="12" cy="12" r="11" '
            'fill="#F53550" mask="url(#cw-mark)"/></g>')


def make_leetcode_svg(username: str, counts: dict[str, int], variant: str) -> str:
    theme = THEMES[variant]
    total = f'{counts["All"]:,}'
    description = f'{counts["All"]} problems solved. Easy: {counts["Easy"]}. Medium: {counts["Medium"]}. Hard: {counts["Hard"]}. Bars show each difficulty as a share of all solved problems.'
    svg = svg_start("LeetCode", username, variant, description) + leetcode_logo(theme)
    svg += label(103, 52, "LeetCode", theme, size=30, weight=700)
    svg += label(103, 78, "Problems Solved", theme, size=17, color=theme["muted"])
    svg += label(139, 169, total, theme, size=fitted_size(total, 76, 236), weight=750, anchor="middle")
    svg += label(139, 196, "solved", theme, size=19, color=theme["muted"], anchor="middle")
    svg += f'<path d="M282 83V195" stroke="{theme["line"]}" stroke-opacity=".42"/>'
    for difficulty, y, gradient, bright in (("Easy", 110, "green", "#36E3A2"), ("Medium", 150, "yellow", "#FFD45C"), ("Hard", 190, "red", "#FF7380")):
        name = difficulty.lower()
        color = theme[gradient]
        fill = {"green": "#00CA85", "yellow": "#FFAC0A", "red": "#FF3B54"}[gradient]
        svg += f'<defs><linearGradient id="{name}-bar"><stop stop-color="{fill}"/><stop offset="1" stop-color="{bright}"/></linearGradient></defs>'
        svg += f'<circle cx="307" cy="{y - 6}" r="8" fill="{fill}"/>'
        svg += label(325, y, difficulty, theme, size=16)
        svg += f'<rect x="394" y="{y - 18}" width="120" height="17" rx="8.5" fill="{theme["track"]}" fill-opacity=".8"/>'
        width = round(120 * counts[difficulty] / counts["All"], 3) if counts["All"] else 0
        if width:
            svg += f'<rect id="{name}-fill" x="394" y="{y - 18}" width="{width}" height="17" rx="8.5" fill="url(#{name}-bar)"/>'
        value = f'{counts[difficulty]:,}'
        svg += label(574, y + 1, value, theme, size=fitted_size(value, 21, 55), color=color, weight=700, anchor="end")
    return svg + "</svg>\n"


def metric_icon(kind: str, y: int, theme: dict[str, str]) -> str:
    content = {
        "kata": '<path d="M1 19V11H5V19M9 19V5L13 2V19M17 19V9H21V19" fill="currentColor" stroke="none"/>',
        "honor": '<path d="M6 3H18V9Q18 16 12 16Q6 16 6 9ZM6 5H2V8Q2 12 7 12M18 5H22V8Q22 12 17 12M12 16V21M7 22H17"/>',
        "python": '<path d="M7 4L1 12L7 20M17 4L23 12L17 20M14 2L10 22"/>',
    }[kind]
    return f'<g transform="translate(327 {y})" color="{theme["muted"]}" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round">{content}</g>'


def make_codewars_svg(username: str, stats: dict, variant: str) -> str:
    theme = THEMES[variant]
    overall = stats["ranks"]["overall"]["name"]
    python_rank = (stats["ranks"].get("languages") or {}).get("python", {}).get("name", "—")
    completed, honor = stats["codeChallenges"]["totalCompleted"], stats["honor"]
    description = f'Overall rank: {overall}. Kata Completed: {completed}. Honor: {honor}. Python Rank: {python_rank}.'
    svg = svg_start("Codewars", username, variant, description) + codewars_logo()
    svg += label(104, 52, "Codewars", theme, size=30, weight=700)
    svg += label(104, 78, "Overall Rank", theme, size=17, color=theme["muted"])
    svg += '<defs><linearGradient id="rank" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#FF626D"/><stop offset="1" stop-color="#ED1D43"/></linearGradient></defs>'
    svg += label(42, 169, overall, theme, size=fitted_size(overall, 64, 240), weight=750, color="url(#rank)")
    svg += f'<path d="M299 53V188" stroke="{theme["line"]}" stroke-opacity=".3"/>'
    svg += f'<rect x="316" y="27" width="264" height="173" rx="18" fill="{theme["panel"]}" fill-opacity="{.42 if variant == "dark" else .65}" stroke="{theme["line"]}" stroke-opacity=".13"/>'
    for name, value, icon, y in (("Kata Completed", f"{completed:,}", "kata", 69), ("Honor", f"{honor:,}", "honor", 122), ("Python Rank", python_rank, "python", 175)):
        svg += metric_icon(icon, y - 19, theme)
        svg += label(363, y - 1, name, theme, size=15, color=theme["muted"])
        svg += label(565, y, value, theme, size=fitted_size(str(value), 21, 82), weight=700, anchor="end")
        if y != 175:
            svg += f'<path d="M331 {y + 18}H565" stroke="{theme["line"]}" stroke-opacity=".15"/>'
    return svg + "</svg>\n"

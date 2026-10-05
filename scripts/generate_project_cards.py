"""Generate the static Liquid Glass project cards with Python's standard library.

Run: python scripts/generate_project_cards.py
Edit assets/projects/projects.json, run this command, then commit the data, SVGs and README.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
BEGIN = '<!-- BEGIN MY PROJECTS -->'
END = '<!-- END MY PROJECTS -->'


@dataclass(frozen=True)
class Project:
    slug: str
    name: str
    category: str
    description: str
    desktop: tuple[str, ...]
    mobile: tuple[str, ...]
    featured: bool = False
    art: str = 'ui'
    secondary_label: str | None = None
    secondary_url: str | None = None


def load_projects(path: Path) -> tuple[Project, ...]:
    entries = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(entries, list) or not entries:
        raise ValueError('projects.json must contain a nonempty list')
    projects = tuple(Project(**{**row, 'desktop': tuple(row['desktop']),
                                'mobile': tuple(row['mobile'])}) for row in entries)
    if len({p.slug for p in projects}) != len(projects):
        raise ValueError('Project slugs must be unique')
    filenames = [f'header-{layout}.svg' for layout in ('desktop', 'tablet', 'mobile')]
    for p in projects:
        for layout in ('desktop', 'tablet', 'mobile'):
            filenames.extend((f'{p.slug}-{layout}.svg', f'{p.slug}-repository-{layout}.svg',
                              f'{p.slug}-secondary-{layout}.svg'))
    if len(set(filenames)) != len(filenames):
        raise ValueError('Project slugs cause generated filename collisions; choose a different slug')
    for p in projects:
        if not re.fullmatch(r'[a-z][a-z0-9-]*', p.slug):
            raise ValueError(f'Invalid asset slug: {p.slug}')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', p.name):
            raise ValueError(f'Invalid GitHub repository name: {p.name}')
        if not p.category or not p.description or not p.desktop or not p.mobile:
            raise ValueError(f'Missing project content: {p.name}')
        if len(p.mobile) > 7 or not set(p.mobile).issubset(p.desktop):
            raise ValueError(f'Mobile stack must contain at most seven desktop technologies: {p.name}')
        if any(not isinstance(label, str) or not label for label in p.desktop):
            raise ValueError(f'Invalid technology label: {p.name}')
        if p.art not in ('api', 'load', 'ui') or not isinstance(p.featured, bool):
            raise ValueError(f'Invalid art or featured value: {p.name}')
        if (p.secondary_label is None) != (p.secondary_url is None):
            raise ValueError(f'Secondary action requires both label and URL: {p.name}')
        if p.secondary_label is not None:
            if (not isinstance(p.secondary_label, str) or not p.secondary_label.strip()
                    or not isinstance(p.secondary_url, str)
                    or any(c.isspace() for c in p.secondary_url)):
                raise ValueError(f'Invalid secondary action: {p.name}')
            target = urlsplit(p.secondary_url)
            if target.scheme != 'https' or not target.hostname:
                raise ValueError(f'Secondary action requires an HTTPS URL: {p.name}')
    if sum(p.featured for p in projects) > 1:
        raise ValueError('Only one project may be featured')
    return projects


PROJECTS = load_projects(ROOT / 'assets' / 'projects' / 'projects.json')


@dataclass(frozen=True)
class Layout:
    card_width: int
    card_height: int
    body_height: int
    padding: int
    header_height: int
    gap: int

    @property
    def board_width(self) -> int:
        return self.card_width + 2 * self.padding

    @property
    def board_height(self) -> int:
        return self.header_height + len(PROJECTS) * self.card_height + (len(PROJECTS) - 1) * self.gap + self.padding


LAYOUTS = {
    'desktop': Layout(900, 346, 292, 20, 178, 14),
    'tablet': Layout(568, 414, 360, 16, 180, 12),
    'mobile': Layout(360, 398, 344, 16, 246, 12),
}

# The profile sidebar appears at 768px, reducing the README by about 288px.
# A narrow README still needs the compact layout on a small portrait tablet.
MOBILE_MEDIA = '(max-width: 480px), (min-width: 768px) and (max-width: 820px)'
TABLET_MEDIA = '(max-width: 1280px)'
# GitHub caps the desktop README near 846px. Whole CSS pixel widths keep
# Chrome from rounding the body and independently linked footer differently.
DESKTOP_DISPLAY_WIDTH = 846

# Stroke, text and translucent fill, shared by every tool in a category.
CATEGORY_COLORS = {
    'languages': ('#4388e3', '#baddff', '#1a3c70'),
    'testing': ('#329967', '#adf7c7', '#16422c'),
    'api': ('#24a7b1', '#93f2f1', '#12434b'),
    'data': ('#cda14d', '#f5e0a8', '#49381c'),
    'infrastructure': ('#6376d8', '#d4d9ff', '#262b62'),
    'monitoring': ('#bd7245', '#ffd4b7', '#4b2c22'),
    'quality': ('#a17bdd', '#e8d1ff', '#382650'),
}
NEUTRAL_COLORS = ('#647688', '#e0e9f7', '#29384c')
FONT = 'Segoe UI,Arial,sans-serif'


def load_technology_categories(path: Path) -> dict[str, str]:
    categories = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(categories, dict):
        raise ValueError('technologies.json must map technology labels to category names')
    for label, category in categories.items():
        if (not isinstance(label, str) or not label or not isinstance(category, str)
                or category not in CATEGORY_COLORS):
            raise ValueError(f'Invalid technology category for {label}: {category}')
    return categories


TECHNOLOGY_CATEGORIES = load_technology_categories(ROOT / 'assets' / 'projects' / 'technologies.json')


def text_width(value: str, size: float) -> float:
    """Conservative system-font advance estimate for deterministic wrapping."""
    narrow, wide = "ilIjtfr.,:;!|' ", 'MWmw@%&'
    return sum(.31 if c in narrow else .86 if c in wide else .60 for c in value) * size


def fit_size(value: str, width: float, preferred: float, minimum: float) -> float:
    size = min(preferred, width / text_width(value, 1))
    if size < minimum:
        raise ValueError(f'Heading is too long; shorten it: {value}')
    return size


def wrap_text(value: str, width: float, size: float) -> list[str]:
    lines: list[str] = []
    line = ''
    for word in value.split():
        if text_width(word, size) > width:
            raise ValueError(f'Word does not fit the card: {word}')
        candidate = f'{line} {word}' if line else word
        if text_width(candidate, size) <= width:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def text(value: str, x: float, y: float, size: float, color: str = '#e0e8f6',
         weight: int = 400) -> str:
    return (f'<text x="{x:g}" y="{y:g}" font-family="{FONT}" font-size="{size:g}" '
            f'font-weight="{weight}" fill="{color}">{escape(value)}</text>')


def start_svg(prefix: str, width: int, height: int, title: str, description: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{prefix}-title {prefix}-desc">
<title id="{prefix}-title">{escape(title)}</title>
<desc id="{prefix}-desc">{escape(description)}</desc>
<defs>
  <linearGradient id="{prefix}-bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#18283e"/><stop offset=".45" stop-color="#091723"/><stop offset="1" stop-color="#162347"/></linearGradient>
  <linearGradient id="{prefix}-edge" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#cabfff"/><stop offset=".35" stop-color="#5387bd"/><stop offset=".75" stop-color="#809fef"/><stop offset="1" stop-color="#d3ceff"/></linearGradient>
  <linearGradient id="{prefix}-glass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#d7e4ff" stop-opacity=".42"/><stop offset=".3" stop-color="#839bfc" stop-opacity=".13"/><stop offset=".7" stop-color="#608bd0" stop-opacity=".06"/><stop offset="1" stop-color="#9797ff" stop-opacity=".30"/></linearGradient>
  <linearGradient id="{prefix}-blue" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#a4eeff"/><stop offset=".5" stop-color="#54abff"/><stop offset="1" stop-color="#8079ff"/></linearGradient>
  <linearGradient id="{prefix}-violet" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#8facff"/><stop offset=".55" stop-color="#7962d9"/><stop offset="1" stop-color="#342955"/></linearGradient>
  <radialGradient id="{prefix}-halo"><stop stop-color="#54baff" stop-opacity=".9"/><stop offset=".38" stop-color="#4785f2" stop-opacity=".48"/><stop offset="1" stop-color="#527aff" stop-opacity="0"/></radialGradient>
  <radialGradient id="{prefix}-purple"><stop stop-color="#ac86ff" stop-opacity=".7"/><stop offset=".45" stop-color="#7958d9" stop-opacity=".32"/><stop offset="1" stop-color="#634ec3" stop-opacity="0"/></radialGradient>
  <linearGradient id="{prefix}-wave" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#b7a5ff" stop-opacity=".9"/><stop offset=".35" stop-color="#8461f0" stop-opacity=".55"/><stop offset="1" stop-color="#5758cb" stop-opacity=".02"/></linearGradient>
  <filter id="{prefix}-glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="4"/></filter>
  <clipPath id="{prefix}-clip"><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="22"/></clipPath>
  <clipPath id="{prefix}-art-clip"><rect width="226" height="266" rx="17"/></clipPath>
</defs>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="22" fill="url(#{prefix}-bg)" stroke="url(#{prefix}-edge)"/>
<g aria-hidden="true" clip-path="url(#{prefix}-clip)"><ellipse cx="{width}" cy="{height*.76:g}" rx="{width*.42:g}" ry="{height*.85:g}" fill="url(#{prefix}-halo)" opacity=".65"/><ellipse cx="0" cy="{height}" rx="{width*.32:g}" ry="{height*.86:g}" fill="url(#{prefix}-purple)" opacity=".65"/><ellipse cx="{width*.72:g}" cy="0" rx="{width*.3:g}" ry="{height*.8:g}" fill="url(#{prefix}-purple)" opacity=".32"/><path d="M24 2H{width-24}" stroke="#f0efff" stroke-opacity=".44"/><path d="M8 24Q8 8 24 8H{width*.45:g}" fill="none" stroke="#c4d8ff" stroke-opacity=".18" stroke-width="3" stroke-linecap="round" filter="url(#{prefix}-glow)"/></g>
'''


def cube(prefix: str, x: float, y: float, scale: float = 1, opacity: float = 1) -> str:
    return f'''<g transform="translate({x:g} {y:g}) scale({scale:g})" opacity="{opacity:g}" stroke="#b7d9ff" stroke-width="1.3" stroke-linejoin="round">
<path d="M0 24 40 0 80 24 40 48Z" fill="url(#{prefix}-blue)" fill-opacity=".62"/>
<path d="M0 24 40 48V92L0 68Z" fill="url(#{prefix}-blue)" fill-opacity=".28"/>
<path d="M40 48 80 24V68L40 92Z" fill="url(#{prefix}-violet)" fill-opacity=".75"/>
<path d="M4 28 36 47V80L4 63Z" fill="#91c9ff" fill-opacity=".13" stroke="none"/>
<path d="M0 24 40 48 80 24M40 48V92" fill="none" stroke="#ddf4ff"/>
</g>'''


def icon(prefix: str, slug: str, x: int, y: int, size: int) -> str:
    result = f'<g aria-hidden="true" transform="translate({x} {y}) scale({size/80:g})"><rect x="1" y="1" width="78" height="78" rx="18" fill="url(#{prefix}-glass)" stroke="#8298d6"/><ellipse cx="40" cy="44" rx="32" ry="30" fill="url(#{prefix}-halo)"/>'
    if slug == 'api':
        result += f'<g filter="url(#{prefix}-glow)">{cube(prefix, 20, 18, .5)}</g>' + cube(prefix, 20, 18, .5)
    elif slug == 'load':
        result += f'''<path d="M17 60A29 29 0 1 1 63 60" fill="none" stroke="url(#{prefix}-blue)" stroke-width="4"/>
<path d="M20 48 25 46M23 29 28 32M40 20V26M57 29 52 32M60 48 55 46" stroke="#a3c7ff" stroke-width="3" stroke-linecap="round"/>
<path d="M40 47 54 31" stroke="#7eaaff" stroke-width="4" stroke-linecap="round"/><circle cx="40" cy="47" r="5" fill="#9ac9ff"/>'''
    else:
        result += f'''<rect x="18" y="20" width="44" height="32" rx="3" fill="#278afb" opacity=".4" filter="url(#{prefix}-glow)"/>
<rect x="18" y="20" width="44" height="32" rx="3" fill="#142d52" stroke="url(#{prefix}-blue)" stroke-width="3"/>
<path d="M40 54V63M29 65H51" stroke="#76baff" stroke-width="4" stroke-linecap="round"/>'''
    return result + '</g>'


def illustration(prefix: str, slug: str, x: int = 653, y: int = 20, scale: float = 1) -> str:
    result = f'<g aria-hidden="true" transform="translate({x} {y}) scale({scale:g})"><rect width="226" height="266" rx="17" fill="url(#{prefix}-glass)" stroke="#7395da" stroke-opacity=".45"/><g clip-path="url(#{prefix}-art-clip)">'
    result += f'<ellipse cx="226" cy="266" rx="210" ry="230" fill="url(#{prefix}-halo)" opacity=".8"/><ellipse cx="30" cy="0" rx="190" ry="190" fill="url(#{prefix}-purple)" opacity=".45"/>'
    if slug == 'api':
        result += '<g stroke="#4b80b9" stroke-width=".6" opacity=".3">'
        for offset in range(-80, 200, 35):
            result += f'<path d="M{offset} 150 226 {263-offset/2:g}M0 {130+offset/2:g} 226 {17+offset/2:g}"/>'
        result += '</g>'
        result += f'<path d="M18 209 112 159 206 209 112 258Z" fill="#79aaff" fill-opacity=".10" stroke="#679dff" stroke-opacity=".65"/>'
        result += f'<g opacity=".7" filter="url(#{prefix}-glow)">{cube(prefix, 60, 60, 1.3)}</g>'
        for y, opacity in [(124, .32), (92, .55), (60, 1)]:
            result += cube(prefix, 60, y, 1.3, opacity)
    elif slug == 'load':
        result += '<g stroke="#6c7ad9" stroke-dasharray="2 5" opacity=".35">'
        for x in (35, 82, 130, 177):
            result += f'<path d="M{x} 40V226"/>'
        result += '</g>'
        curve = 'M15 192C35 164 38 117 67 139S99 197 116 129 145 53 164 70 177 112 211 58'
        result += f'<path d="{curve}L211 246H15Z" fill="url(#{prefix}-wave)"/>'
        result += f'<path d="{curve}" fill="none" stroke="#b69aff" stroke-width="5" filter="url(#{prefix}-glow)"/>'
        result += f'<path d="{curve}" fill="none" stroke="#bfa4ff" stroke-width="1.8"/>'
        result += '<path d="M15 213C35 192 52 175 75 198S106 213 130 159 169 147 211 153" fill="none" stroke="#5989e4" stroke-opacity=".6"/>'
    else:
        for x, y, opacity in [(41, 36, .32), (29, 55, .55), (17, 74, .9)]:
            result += f'<g transform="translate({x} {y}) skewY(15)" opacity="{opacity}"><rect width="154" height="148" rx="9" fill="url(#{prefix}-blue)" fill-opacity=".23" stroke="#b3c8ff"/><rect width="154" height="148" rx="9" fill="url(#{prefix}-glass)"/><path d="M1 25H153" stroke="#a8c8ff" stroke-opacity=".6"/>'
            result += '<circle cx="12" cy="13" r="3" fill="#cc9df9"/><circle cx="23" cy="13" r="3" fill="#8abaff"/><circle cx="34" cy="13" r="3" fill="#99def0"/>'
            result += '<rect x="13" y="39" width="24" height="92" rx="4" fill="#4b70bd" opacity=".45"/><rect x="49" y="39" width="91" height="40" rx="4" fill="#6695e4" opacity=".45"/><path d="M49 94H137M49 106H128M49 118H137M49 130H105" stroke="#739dde" stroke-width="4" stroke-linecap="round"/></g>'
    return result + '</g></g>'


def featured(x: int, y: int) -> str:
    return (f'<g transform="translate({x} {y})"><rect width="94" height="24" rx="12" fill="#305593" stroke="#82acfa"/>'
            '<path d="m13 5 2 4 5 .7-3.5 3.4.8 4.9L13 16l-4.3 2.3.8-4.9L6 9.7l5-.7Z" fill="#e0e5ff"/>'
            + text('Featured', 26, 16.5, 12, '#f1f6ff', 600) + '</g>')


def badges(prefix: str, technologies: tuple[str, ...], x: int, y: int, width: int, bottom: int,
           size: int = 15, height: int = 28, leading: int = 34) -> str:
    result = '<g aria-label="Technology stack">'
    current_x, current_y = float(x), y
    for technology in technologies:
        pill_width = round(text_width(technology, size) + 24)
        if pill_width > width:
            raise ValueError(f'Technology pill does not fit: {technology}')
        if current_x + pill_width > x + width:
            current_x, current_y = float(x), current_y + leading
        if current_y + height > bottom:
            raise ValueError('Technology stack exceeds the card; use fewer or shorter labels')
        stroke, color, fill = CATEGORY_COLORS.get(TECHNOLOGY_CATEGORIES.get(technology), NEUTRAL_COLORS)
        result += f'<g transform="translate({current_x:g} {current_y})"><rect width="{pill_width}" height="{height}" rx="{height/2:g}" fill="{fill}" fill-opacity=".65" stroke="{stroke}"/><rect width="{pill_width}" height="{height}" rx="{height/2:g}" fill="url(#{prefix}-glass)"/>'
        result += '<path d="M13 2H' + str(pill_width - 13) + '" stroke="#ffffff" stroke-opacity=".15"/>'
        result += text(technology, 12, (height + size) / 2 - 2.5, size, color) + '</g>'
        current_x += pill_width + 8
    return result + '</g>'


def repository_icon(x: int, y: int, size: int = 20) -> str:
    # Local vector silhouette; no font glyph or external logo dependency.
    return f'''<g transform="translate({x} {y}) scale({size/24:g})" fill="#f0f5ff"><path d="M12 1a11 11 0 0 0-3.5 21.4c.5.1.7-.2.7-.5v-2c-2.8.6-3.4-1.2-3.4-1.2-.5-1.2-1.2-1.5-1.2-1.5-1-.7.1-.7.1-.7 1.1.1 1.7 1.1 1.7 1.1 1 1.6 2.5 1.1 3 .8.1-.7.4-1.1.7-1.4-2.3-.3-4.7-1.2-4.7-5a4 4 0 0 1 1-2.8c-.1-.3-.4-1.3.1-2.7 0 0 .9-.3 2.9 1.1a10 10 0 0 1 5.2 0C16.6 6.2 17.5 6.5 17.5 6.5c.5 1.4.2 2.4.1 2.7a4 4 0 0 1 1 2.8c0 3.8-2.4 4.7-4.7 5 .4.3.7.9.7 1.8v3.1c0 .3.2.6.7.5A11 11 0 0 0 12 1Z"/></g>'''


def render_card(project: Project, layout: str) -> str:
    mobile = layout == 'mobile'
    prefix = f'project-{project.slug}-{layout}'
    metrics = LAYOUTS[layout]
    width, height, body_height = metrics.card_width, metrics.card_height, metrics.body_height
    technologies = project.mobile if mobile else project.desktop
    if mobile and len(technologies) > 7:
        raise ValueError('Mobile cards support at most seven technologies')
    result = start_svg(prefix, width, height, project.name + ' — ' + project.category,
                       project.description + ' Technologies: ' + ', '.join(technologies) + '.')
    if layout == 'tablet':
        # SVG image media queries see the displayed image width. Keep typography
        # and artwork restrained as this composition grows inside the README.
        result += '''<style>.tablet-profile{display:none}.tablet-compact{display:inline}
@media(min-width:560px){.tablet-compact{display:none}.tablet-medium{display:inline}}
@media(min-width:700px){.tablet-medium{display:none}.tablet-wide{display:inline}}</style>'''
        for profile, icon_size, title_size, description_size, badge_size in (
                ('compact', 72, 27, 22, 18), ('medium', 64, 25, 20, 16),
                ('wide', 56, 23, 17, 14)):
            result += f'<g class="tablet-profile tablet-{profile}">'
            result += icon(prefix, project.art, 20, 24, icon_size)
            name_size = fit_size(project.name, 320 if project.featured else 440, title_size, 20)
            result += text(project.name, 108, 53, name_size, '#f3f6ff', 650)
            result += text(project.category, 108, 81, fit_size(project.category, 440, 17, 14), '#9ccaff')
            if project.featured:
                featured_x = 108 + text_width(project.name, name_size) + 14
                result += f'<g transform="translate({featured_x:g} 32) scale(1.15)">' + featured(0, 0) + '</g>'
            description_top = 104
            # Align the art with the first line's visible cap height, rather
            # than the alphabetic baseline or the font's extra ascent space.
            description_y = description_top + round(description_size * .76)
            result += illustration(prefix, project.art, 420, description_top, .5)
            lines = wrap_text(project.description, 352, description_size)
            if description_y + (len(lines) - 1) * 24 > 254:
                raise ValueError(f'Description exceeds tablet layout: {project.name}')
            for index, line in enumerate(lines):
                result += text(line, 24, description_y + 24 * index, description_size)
            result += badges(prefix, technologies, 24, 270, 520, body_height - 16,
                             badge_size, 32, 40)
            result += '</g>'
        return result + render_footer(project, 'repository', layout) + render_footer(project, 'secondary', layout) + '\n</svg>\n'
    if mobile:
        result += icon(prefix, project.art, 20, 24, 58)
        name_size = fit_size(project.name, 171 if project.featured else 249, 20, 15)
        result += text(project.name, 91, 45, name_size, '#f3f6ff', 650)
        result += text(project.category, 91, 68, fit_size(project.category, 249, 13, 11), '#9ccaff')
        if project.featured:
            result += '<g transform="translate(272 28) scale(.73)">' + featured(0, 0) + '</g>'
        description_x, description_y, available, size, leading = 20, 105, 320, 17, 23
        badge_x, badge_y, badge_width = 20, 228, 320
    else:
        result += icon(prefix, project.art, 24, 28, 80)
        name_size = fit_size(project.name, 281 if project.featured else 498, 28, 20)
        result += text(project.name, 132, 57, name_size, '#f3f6ff', 650)
        result += text(project.category, 132, 85, fit_size(project.category, 498, 18, 14), '#9ccaff')
        if project.featured:
            result += featured(423, 36)
        result += illustration(prefix, project.art)
        description_x, description_y, available, size, leading = 132, 118, 498, 22, 24
        badge_x, badge_y, badge_width = 132, 210, 496
    lines = wrap_text(project.description, available, size)
    if description_y + (len(lines) - 1) * leading > badge_y - 16:
        raise ValueError(f'Description exceeds {layout} layout: {project.name}')
    for index, line in enumerate(lines):
        result += text(line, description_x, description_y + leading * index, size)
    result += badges(prefix, technologies, badge_x, badge_y, badge_width, body_height - 16)
    return result + render_footer(project, 'repository', layout) + render_footer(project, 'secondary', layout) + '\n</svg>\n'


def footer_split(layout: str) -> int:
    """Use a whole SVG pixel inside the button gap as the link boundary."""
    metrics = LAYOUTS[layout]
    left = {'mobile': 20, 'tablet': 24, 'desktop': 132}[layout]
    source_width = 8 + 28 + text_width('Source code', 15) + 34
    gap = {'mobile': 8, 'tablet': 12, 'desktop': 16}[layout]
    return round(metrics.padding + left + source_width + gap / 2)


def render_footer(project: Project, action: str, layout: str) -> str:
    """Draw an action on the card's existing surface, without another frame."""
    metrics = LAYOUTS[layout]
    width, top = metrics.card_width, metrics.body_height
    prefix = f'project-{project.slug}-{layout}'
    label = 'Source code' if action == 'repository' else project.secondary_label
    if label is None:
        return ''
    result = f'<g aria-label="{escape(label, quote=True)}">'
    source_x = {'mobile': 20, 'tablet': 24, 'desktop': 132}[layout] + 8
    source_width = 8 + 28 + text_width('Source code', 15) + 34
    gap = {'mobile': 8, 'tablet': 12, 'desktop': 16}[layout]
    x = source_x if action == 'repository' else source_x + source_width + gap
    y = top + 33
    icon_gap = 28 if action == 'repository' else 26
    trailing = 34 if action == 'repository' else 16
    size = fit_size(label, width - x - icon_gap - trailing - 12, 15, 12)
    advance = text_width(label, size)
    button_width = 8 + icon_gap + advance + trailing
    result += (f'<rect x="{x-8:g}" y="{top+8}" width="{button_width:g}" height="38" rx="14" '
               f'fill="url(#{prefix}-glass)" stroke="#829cda" stroke-opacity=".6"/>')
    if action == 'repository':
        result += repository_icon(x, y - 17, 21)
        result += text(label, x + 28, y, size, '#d2e5ff')
        arrow = x + 28 + advance + 7
        result += f'<path d="M{arrow} {y-5}h12m-5-5 5 5-5 5" fill="none" stroke="#c5dfff" stroke-width="1.5"/>'
    else:
        result += f'<path d="M{x+3} {y-19}h10l5 5v18H{x+3}Zm10 0v5h5M{x+7} {y-9}h7M{x+7} {y-4}h7" fill="none" stroke="#d2e5ff" stroke-width="1.5" stroke-linejoin="round"/>'
        result += text(label, x + 26, y, size, '#d2e5ff')
    return result + '</g>'


def svg_content(source: str, surface: bool = True) -> str:
    """Extract drawing commands when embedding an SVG in the shared scene."""
    content = source[source.index('<defs>'):source.rindex('</svg>')]
    if not surface:
        # The header belongs to the outer panel, without a second card frame.
        defs_end = content.index('</defs>') + len('</defs>')
        background_end = content.index('</g>', defs_end) + len('</g>')
        content = content[:defs_end] + content[background_end:]
    return content


def render_board(layout: str) -> str:
    """Draw every contour once, before making any independently linked crops."""
    metrics = LAYOUTS[layout]
    result = start_svg(f'projects-board-{layout}', metrics.board_width, metrics.board_height,
                       'My Projects', 'QA automation and performance testing projects.')
    result += f'<g transform="translate({metrics.padding} {metrics.padding})">' + svg_content(render_header(layout), surface=False) + '</g>'
    for index, project in enumerate(PROJECTS):
        y = metrics.header_height + index * (metrics.card_height + metrics.gap)
        result += f'<g transform="translate({metrics.padding} {y})">' + svg_content(render_card(project, layout)) + '</g>'
    return result + '\n</svg>\n'


def board_slice(source: str, layout: str, viewport: tuple[int, int, int, int],
                title: str, description: str) -> str:
    """Crop the same scene; prevent per-image aspect-ratio letterboxing."""
    x, y, width, height = viewport
    prefix = f'projects-board-{layout}'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="{x} {y} {width} {height}" preserveAspectRatio="none" role="img" '
            f'aria-labelledby="{prefix}-title {prefix}-desc">\n'
            f'<title id="{prefix}-title">{escape(title)}</title>\n'
            f'<desc id="{prefix}-desc">{escape(description)}</desc>\n'
            + svg_content(source) + '\n</svg>\n')


def render_assets() -> dict[str, str]:
    assets = {}
    for layout, metrics in LAYOUTS.items():
        width = metrics.board_width
        split = footer_split(layout)
        board = render_board(layout)
        assets[f'header-{layout}.svg'] = board_slice(
            board, layout, (0, 0, width, metrics.header_height), 'My Projects', 'View all repositories.')
        for index, project in enumerate(PROJECTS):
            y = metrics.header_height + index * (metrics.card_height + metrics.gap)
            start = y - (metrics.gap if index else 0)
            assets[f'{project.slug}-{layout}.svg'] = board_slice(
                board, layout, (0, start, width, y + metrics.body_height - start),
                project.name + ' — ' + project.category, project.description)
            footer_height = metrics.card_height - metrics.body_height
            if index == len(PROJECTS) - 1:
                footer_height += metrics.padding
            for action in ('repository', 'secondary'):
                offset = 0 if action == 'repository' else split
                slice_width = split if action == 'repository' else width - split
                assets[f'{project.slug}-{action}-{layout}.svg'] = board_slice(
                    board, layout, (offset, y + metrics.body_height, slice_width, footer_height),
                    'Source code' if action == 'repository' else project.secondary_label or 'Project footer',
                    f'Navigation for {project.name}.')
    return assets


def render_header(layout: str) -> str:
    mobile = layout == 'mobile'
    tablet = layout == 'tablet'
    width = LAYOUTS[layout].card_width
    height = {'mobile': 218, 'tablet': 152, 'desktop': 150}[layout]
    prefix = 'projects-header-' + layout
    caption = 'A collection of QA automation and performance testing projects with real-world scenarios, modern tools and CI/CD.'
    result = start_svg(prefix, width, height, 'My Projects', caption + ' View all repositories.')
    x, y, size = (20, 20, 48) if mobile or tablet else (24, 25, 58)
    result += f'<g aria-hidden="true" transform="translate({x} {y})"><rect width="{size}" height="{size}" rx="14" fill="url(#{prefix}-glass)" stroke="#8996c8"/>'
    for dx, dy in ((0, 0), (15, 0), (0, 15), (15, 15)):
        result += f'<rect x="{size/2-12+dx:g}" y="{size/2-12+dy:g}" width="10" height="10" rx="1.5" fill="none" stroke="#a9bcff" stroke-width="2"/>'
    result += '</g>'
    result += (f'<text x="{84 if mobile or tablet else 100}" y="{54 if mobile or tablet else 66}" '
               f'font-family="{FONT}" font-size="{29 if mobile or tablet else 36}" font-weight="700" '
               'fill="#f3f6ff">My <tspan fill="#82a8ff">Projects</tspan></text>')
    if tablet:
        lines = wrap_text(caption, 520, 16.5)
        for index, line in enumerate(lines):
            result += text(line, 20, 95 + 23 * index, 16.5, '#b2c2de')
        button_x, button_y = 320, 25
    elif mobile:
        lines = wrap_text(caption, 320, 14.5)
        for index, line in enumerate(lines):
            result += text(line, 20, 95 + 21 * index, 14.5, '#b2c2de')
        button_x, button_y = 20, 164
    else:
        lines = wrap_text(caption, 535, 15.5)
        for index, line in enumerate(lines):
            result += text(line, 100, 100 + 22 * index, 15.5, '#b2c2de')
        button_x, button_y = 648, 39
    result += f'<g transform="translate({button_x} {button_y})"><rect width="228" height="38" rx="19" fill="url(#{prefix}-glass)" stroke="#6888d6"/>'
    result += repository_icon(12, 9, 20) + text('View all repositories', 42, 24, 13.5, '#f2f6ff', 500)
    result += '<path d="m211 13 5 6-5 6" fill="none" stroke="#c9dcff" stroke-width="1.6" stroke-linecap="round"/></g>'
    return result + '\n</svg>\n'


def render_readme() -> str:
    body_widths = dict.fromkeys(LAYOUTS, '100%')
    body_widths['desktop'] = str(DESKTOP_DISPLAY_WIDTH)

    def picture(stem: str, alternative: str, widths: dict[str, str] | None = None) -> str:
        widths = widths or body_widths
        return (f'<picture><source media="{MOBILE_MEDIA}" srcset="assets/projects/{stem}-mobile.svg" width="{widths["mobile"]}" />'
                   f'<source media="{TABLET_MEDIA}" srcset="assets/projects/{stem}-tablet.svg" width="{widths["tablet"]}" />'
                   f'<img src="assets/projects/{stem}-desktop.svg" width="{widths["desktop"]}" align="top" '
                   f'alt="{escape(alternative, quote=True)}" /></picture>')

    def link(url: str, stem: str, alternative: str, widths: dict[str, str] | None = None) -> str:
        return f'<a href="{escape(url, quote=True)}">{picture(stem, alternative, widths)}</a>'

    fractions = {layout: footer_split(layout) / metrics.board_width * 100 for layout, metrics in LAYOUTS.items()}
    widths = {layout: f'{fraction:.8f}%' for layout, fraction in fractions.items()}
    remaining = {layout: f'{100-fraction:.8f}%' for layout, fraction in fractions.items()}
    desktop_split = round(DESKTOP_DISPLAY_WIDTH * fractions['desktop'] / 100)
    widths['desktop'] = str(desktop_split)
    remaining['desktop'] = str(DESKTOP_DISPLAY_WIDTH - desktop_split)

    caption = ('My Projects. A collection of QA automation and performance testing projects '
               'with real-world scenarios, modern tools and CI/CD. View all repositories.')
    rows = ['<p align="center">',
            '  ' + link('https://github.com/search?q=user%3ABarbaron86&type=repositories', 'header', caption) + '<br />']
    for index, project in enumerate(PROJECTS):
        repo = f'https://github.com/Barbaron86/{project.name}'
        alternative = project.name + ' — ' + project.category + '. '
        if project.featured:
            alternative += 'Featured project. '
        alternative += project.description + ' Technologies: ' + ', '.join(project.desktop) + '.'
        # An anchor without href keeps GitHub from adding an image-file link.
        rows.append('  <a>' + picture(project.slug, alternative) + '</a><br />')
        footer = link(repo, project.slug + '-repository', 'Source code', widths)
        if project.secondary_url is not None:
            footer += link(project.secondary_url, project.slug + '-secondary', project.secondary_label, remaining)
        else:
            footer += '<a>' + picture(project.slug + '-secondary', '', remaining) + '</a>'
        rows.append('  ' + footer + ('<br />' if index < len(PROJECTS) - 1 else ''))
    return '\n'.join(rows + ['</p>'])


def generate(output: Path, readme: Path | None = None) -> None:
    assets = render_assets()
    updated_readme = None
    if readme is not None:
        current = readme.read_text(encoding='utf-8')
        if current.count(BEGIN) != 1 or current.count(END) != 1:
            raise ValueError('README must contain one pair of MY PROJECTS markers')
        before, remainder = current.split(BEGIN, 1)
        _, after = remainder.split(END, 1)
        updated_readme = before + BEGIN + '\n' + render_readme() + '\n' + END + after
    # Validate every image before replacing any generated assets.
    for value in assets.values():
        ET.fromstring(value)
    output.mkdir(parents=True, exist_ok=True)
    for filename, value in assets.items():
        path = output / filename
        if not path.exists() or path.read_text(encoding='utf-8') != value:
            path.write_text(value, encoding='utf-8', newline='\n')
    if updated_readme is not None and updated_readme != current:
        readme.write_text(updated_readme, encoding='utf-8', newline='\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='SVG output directory; skips README unless --readme is set')
    parser.add_argument('--readme', type=Path, help='README containing MY PROJECTS markers')
    args = parser.parse_args()
    output = args.output or ROOT / 'assets' / 'projects'
    readme = args.readme or (ROOT / 'README.md' if args.output is None else None)
    generate(output, readme)


if __name__ == '__main__':
    main()

"""Generate the static Liquid Glass project cards with Python's standard library.

Run: python scripts/generate_project_cards.py
Edit PROJECTS to update copy or stacks, then commit the regenerated assets.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Project:
    slug: str
    name: str
    category: str
    description: str
    desktop: tuple[str, ...]
    mobile: tuple[str, ...]
    featured: bool = False


PROJECTS = (
    Project(
        'isolation', 'isolation-api-tests', 'Isolated API & Integration Testing',
        'An API testing framework with custom FastAPI mocks for service isolation. '
        'Tests real HTTP/gRPC interactions, Kafka events and PostgreSQL data.',
        ('Python', 'Pytest', 'FastAPI', 'HTTPX', 'gRPC', 'Kafka', 'PostgreSQL', 'Docker', 'Allure'),
        ('Python', 'Pytest', 'FastAPI', 'gRPC', 'Kafka', 'PostgreSQL', 'Docker'),
        featured=True,
    ),
    Project(
        'performance', 'performance-tests', 'Performance & Load Testing',
        'A Locust-based load testing framework with decoupled HTTP/gRPC clients, '
        'automated test data seeding, Prometheus/Grafana monitoring and CI/CD reporting.',
        ('Python', 'Locust', 'gRPC', 'HTTPX', 'Docker', 'Prometheus', 'Grafana'),
        ('Python', 'Locust', 'gRPC', 'HTTPX', 'Docker', 'Prometheus', 'Grafana'),
    ),
    Project(
        'ui', 'autotest-ui', 'UI Test Automation',
        'A Playwright-based UI testing framework with Page Object architecture, '
        'parallel cross-browser execution, reusable authentication state, Allure reporting and CI/CD.',
        ('Python', 'Playwright', 'Pytest', 'pytest-xdist', 'Pydantic', 'Poetry', 'Allure', 'Ruff', 'Mypy'),
        ('Python', 'Playwright', 'Pytest', 'pytest-xdist', 'Allure', 'Ruff', 'Mypy'),
    ),
)

# Stroke, text and translucent fill of each technology pill.
COLORS = {
    'Python': ('#4388e3', '#baddff', '#1a3c70'),
    'Pytest': ('#566576', '#e0e7ef', '#2c3a4b'),
    'FastAPI': ('#249e92', '#a0f6e4', '#123f41'),
    'HTTPX': ('#647688', '#e0e9f7', '#29384c'),
    'gRPC': ('#24a7b1', '#93f2f1', '#12434b'),
    'Kafka': ('#7761cf', '#dbccff', '#312258'),
    'PostgreSQL': ('#4982d1', '#bedcff', '#1b365a'),
    'Docker': ('#329ac9', '#b4eeff', '#133d59'),
    'Allure': ('#329967', '#adf7c7', '#16422c'),
    'Locust': ('#329967', '#adf7c7', '#16422c'),
    'Prometheus': ('#bd7245', '#ffd4b7', '#4b2c22'),
    'Grafana': ('#bd7245', '#ffd4b7', '#4b2c22'),
    'Playwright': ('#329967', '#adf7c7', '#16422c'),
    'pytest-xdist': ('#566576', '#e0e7ef', '#2c3a4b'),
    'Pydantic': ('#b56190', '#ffcae4', '#492540'),
    'Poetry': ('#7761cf', '#dbccff', '#312258'),
    'Ruff': ('#7761cf', '#dbccff', '#312258'),
    'Mypy': ('#6376d8', '#d4d9ff', '#262b62'),
}
FONT = 'Segoe UI,Arial,sans-serif'
NS = '{http://www.w3.org/2000/svg}'


def text_width(value: str, size: float) -> float:
    """Conservative system-font advance estimate for deterministic wrapping."""
    narrow, wide = "ilIjtfr.,:;!|' ", 'MWmw@%&'
    return sum(.31 if c in narrow else .86 if c in wide else .60 for c in value) * size


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


def start_svg(prefix: str, width: int, height: int, title: str, description: str,
              viewport: tuple[int, int, int, int] | None = None) -> str:
    # The body and two navigation images share one continuous glass surface.
    vx, vy, vw, vh = viewport or (0, 0, width, height)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{vw}" height="{vh}" viewBox="{vx} {vy} {vw} {vh}" role="img" aria-labelledby="{prefix}-title {prefix}-desc">
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
    if slug == 'isolation':
        result += f'<g filter="url(#{prefix}-glow)">{cube(prefix, 20, 18, .5)}</g>' + cube(prefix, 20, 18, .5)
    elif slug == 'performance':
        result += f'''<path d="M17 60A29 29 0 1 1 63 60" fill="none" stroke="url(#{prefix}-blue)" stroke-width="4"/>
<path d="M20 48 25 46M23 29 28 32M40 20V26M57 29 52 32M60 48 55 46" stroke="#a3c7ff" stroke-width="3" stroke-linecap="round"/>
<path d="M40 47 54 31" stroke="#7eaaff" stroke-width="4" stroke-linecap="round"/><circle cx="40" cy="47" r="5" fill="#9ac9ff"/>'''
    else:
        result += f'''<rect x="18" y="20" width="44" height="32" rx="3" fill="#278afb" opacity=".4" filter="url(#{prefix}-glow)"/>
<rect x="18" y="20" width="44" height="32" rx="3" fill="#142d52" stroke="url(#{prefix}-blue)" stroke-width="3"/>
<path d="M40 54V63M29 65H51" stroke="#76baff" stroke-width="4" stroke-linecap="round"/>'''
    return result + '</g>'


def illustration(prefix: str, slug: str) -> str:
    result = f'<g aria-hidden="true" transform="translate(653 20)"><rect width="226" height="266" rx="17" fill="url(#{prefix}-glass)" stroke="#7395da" stroke-opacity=".45"/><g clip-path="url(#{prefix}-art-clip)">'
    result += f'<ellipse cx="226" cy="266" rx="210" ry="230" fill="url(#{prefix}-halo)" opacity=".8"/><ellipse cx="30" cy="0" rx="190" ry="190" fill="url(#{prefix}-purple)" opacity=".45"/>'
    if slug == 'isolation':
        result += '<g stroke="#4b80b9" stroke-width=".6" opacity=".3">'
        for offset in range(-80, 200, 35):
            result += f'<path d="M{offset} 150 226 {263-offset/2:g}M0 {130+offset/2:g} 226 {17+offset/2:g}"/>'
        result += '</g>'
        result += f'<path d="M18 209 112 159 206 209 112 258Z" fill="#79aaff" fill-opacity=".10" stroke="#679dff" stroke-opacity=".65"/>'
        result += f'<g opacity=".7" filter="url(#{prefix}-glow)">{cube(prefix, 60, 60, 1.3)}</g>'
        for y, opacity in [(124, .32), (92, .55), (60, 1)]:
            result += cube(prefix, 60, y, 1.3, opacity)
    elif slug == 'performance':
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
    result += '<rect x="183" y="12" width="30" height="30" rx="10" fill="#8b9fea" fill-opacity=".15" stroke="#9eaff0" stroke-opacity=".45"/><path d="M193 32 204 21M193 21H204V32" fill="none" stroke="#e1eaff" stroke-width="1.8" stroke-linecap="round"/>'
    return result + '</g></g>'


def featured(x: int, y: int) -> str:
    return (f'<g transform="translate({x} {y})"><rect width="94" height="24" rx="12" fill="#305593" stroke="#82acfa"/>'
            '<path d="m13 5 2 4 5 .7-3.5 3.4.8 4.9L13 16l-4.3 2.3.8-4.9L6 9.7l5-.7Z" fill="#e0e5ff"/>'
            + text('Featured', 26, 16.5, 12, '#f1f6ff', 600) + '</g>')


def badges(prefix: str, technologies: tuple[str, ...], x: int, y: int, width: int) -> str:
    result = '<g aria-label="Technology stack">'
    current_x, current_y = float(x), y
    for technology in technologies:
        pill_width = round(text_width(technology, 15) + 24)
        if pill_width > width:
            raise ValueError(f'Technology pill does not fit: {technology}')
        if current_x + pill_width > x + width:
            current_x, current_y = float(x), current_y + 34
        stroke, color, fill = COLORS[technology]
        result += f'<g transform="translate({current_x:g} {current_y})"><rect width="{pill_width}" height="28" rx="14" fill="{fill}" fill-opacity=".65" stroke="{stroke}"/><rect width="{pill_width}" height="28" rx="14" fill="url(#{prefix}-glass)"/>'
        result += '<path d="M13 2H' + str(pill_width - 13) + '" stroke="#ffffff" stroke-opacity=".15"/>'
        result += text(technology, 12, 19, 15, color) + '</g>'
        current_x += pill_width + 8
    return result + '</g>'


def repository_icon(x: int, y: int, size: int = 20) -> str:
    # Local vector silhouette; no font glyph or external logo dependency.
    return f'''<g transform="translate({x} {y}) scale({size/24:g})" fill="#f0f5ff"><path d="M12 1a11 11 0 0 0-3.5 21.4c.5.1.7-.2.7-.5v-2c-2.8.6-3.4-1.2-3.4-1.2-.5-1.2-1.2-1.5-1.2-1.5-1-.7.1-.7.1-.7 1.1.1 1.7 1.1 1.7 1.1 1 1.6 2.5 1.1 3 .8.1-.7.4-1.1.7-1.4-2.3-.3-4.7-1.2-4.7-5a4 4 0 0 1 1-2.8c-.1-.3-.4-1.3.1-2.7 0 0 .9-.3 2.9 1.1a10 10 0 0 1 5.2 0C16.6 6.2 17.5 6.5 17.5 6.5c.5 1.4.2 2.4.1 2.7a4 4 0 0 1 1 2.8c0 3.8-2.4 4.7-4.7 5 .4.3.7.9.7 1.8v3.1c0 .3.2.6.7.5A11 11 0 0 0 12 1Z"/></g>'''


def render_card(project: Project, mobile: bool) -> str:
    layout = 'mobile' if mobile else 'desktop'
    prefix = f'project-{project.slug}-{layout}'
    width, height, body_height = (360, 428, 374) if mobile else (900, 346, 292)
    technologies = project.mobile if mobile else project.desktop
    if mobile and len(technologies) > 7:
        raise ValueError('Mobile cards support at most seven technologies')
    result = start_svg(prefix, width, height, project.name + ' — ' + project.category,
                       project.description + ' Technologies: ' + ', '.join(technologies) + '. Open the project repository.',
                       viewport=(0, 0, width, body_height))
    if mobile:
        result += icon(prefix, project.slug, 20, 24, 58)
        result += text(project.name, 91, 45, 22, '#f3f6ff', 650)
        result += text(project.category, 91, 68, 13, '#9ccaff')
        if project.featured:
            result += featured(91, 85)
        description_x, description_y, available, size, leading = 20, 136, 320, 17, 23
        badge_x, badge_y, badge_width = 20, 258, 320
    else:
        result += icon(prefix, project.slug, 24, 28, 80)
        result += text(project.name, 132, 57, 28, '#f3f6ff', 650)
        result += text(project.category, 132, 85, 18, '#9ccaff')
        if project.featured:
            result += featured(423, 36)
        result += illustration(prefix, project.slug)
        description_x, description_y, available, size, leading = 132, 121, 498, 18, 25
        badge_x, badge_y, badge_width = 132, 210, 496
    lines = wrap_text(project.description, available, size)
    if description_y + (len(lines) - 1) * leading > badge_y - 16:
        raise ValueError(f'Description exceeds {layout} layout: {project.name}')
    for index, line in enumerate(lines):
        result += text(line, description_x, description_y + leading * index, size)
    result += badges(prefix, technologies, badge_x, badge_y, badge_width)
    return result + '\n</svg>\n'


def render_footer(action: str, mobile: bool) -> str:
    """Two equal image slices make independent HTML links on one glass footer."""
    layout = 'mobile' if mobile else 'desktop'
    width, height, top = (360, 428, 374) if mobile else (900, 346, 292)
    half = width // 2
    offset = 0 if action == 'repository' else half
    prefix = f'projects-{action}-{layout}'
    label = action.capitalize()
    result = start_svg(prefix, width, height, label, f'Open project {action}.',
                       viewport=(offset, top, half, height - top))
    x = (20 if mobile else 132) if action == 'repository' else offset + (12 if mobile else 18)
    y = top + 33
    if action == 'repository':
        result += repository_icon(x, y - 17, 21)
        result += text(label, x + 28, y, 15, '#d2e5ff')
        arrow = x + 117
        result += f'<path d="M{arrow} {y-5}h12m-5-5 5 5-5 5" fill="none" stroke="#c5dfff" stroke-width="1.5"/>'
    else:
        result += f'<path d="M{x+3} {y-19}h10l5 5v18H{x+3}Zm10 0v5h5M{x+7} {y-9}h7M{x+7} {y-4}h7" fill="none" stroke="#d2e5ff" stroke-width="1.5" stroke-linejoin="round"/>'
        result += text(label, x + 26, y, 15, '#d2e5ff')
    return result + '\n</svg>\n'


def render_header(mobile: bool) -> str:
    width, height = (360, 218) if mobile else (900, 150)
    prefix = 'projects-header-' + ('mobile' if mobile else 'desktop')
    caption = 'A collection of QA automation and performance testing projects with real-world scenarios, modern tools and CI/CD.'
    result = start_svg(prefix, width, height, 'My Projects', caption + ' View all repositories.')
    x, y, size = (20, 20, 48) if mobile else (24, 25, 58)
    result += f'<g aria-hidden="true" transform="translate({x} {y})"><rect width="{size}" height="{size}" rx="14" fill="url(#{prefix}-glass)" stroke="#8996c8"/>'
    for dx, dy in ((0, 0), (15, 0), (0, 15), (15, 15)):
        result += f'<rect x="{size/2-12+dx:g}" y="{size/2-12+dy:g}" width="10" height="10" rx="1.5" fill="none" stroke="#a9bcff" stroke-width="2"/>'
    result += '</g>'
    result += (f'<text x="{84 if mobile else 100}" y="{54 if mobile else 66}" '
               f'font-family="{FONT}" font-size="{29 if mobile else 36}" font-weight="700" '
               'fill="#f3f6ff">My <tspan fill="#82a8ff">Projects</tspan></text>')
    if mobile:
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


def generate(output: Path) -> None:
    assets = {}
    for mobile in (False, True):
        layout = 'mobile' if mobile else 'desktop'
        for project in PROJECTS:
            assets[f'{project.slug}-{layout}.svg'] = render_card(project, mobile)
        assets[f'header-{layout}.svg'] = render_header(mobile)
        for action in ('repository', 'documentation'):
            assets[f'{action}-{layout}.svg'] = render_footer(action, mobile)
    # Validate every image before replacing any generated assets.
    for value in assets.values():
        ET.fromstring(value)
    output.mkdir(parents=True, exist_ok=True)
    for filename, value in assets.items():
        path = output / filename
        if not path.exists() or path.read_text(encoding='utf-8') != value:
            path.write_text(value, encoding='utf-8', newline='\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'assets' / 'projects')
    args = parser.parse_args()
    generate(args.output)


if __name__ == '__main__':
    main()

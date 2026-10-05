# Updating My Projects

Edit [projects.json](../assets/projects/projects.json), then run from the repository root:

```sh
python scripts/generate_project_cards.py
```

The command regenerates mobile, tablet, and desktop layouts, all linked navigation slices, and the README block between `MY PROJECTS` markers. The outer panel height, project order, spacing, and final rounded corners follow the list automatically. Other README sections are preserved.

To add a project, append one object:

```json
{
  "slug": "new-project",
  "name": "new-project",
  "category": "QA Tooling",
  "description": "A short description of the project and its testing approach.",
  "desktop": ["Python", "Pytest", "NewTool"],
  "mobile": ["Python", "Pytest", "NewTool"],
  "art": "ui"
}
```

- `slug` is a unique lowercase asset filename prefix; keep it stable when renaming a repository.
- `name` is the repository name under `Barbaron86`. The Source code button's repository link is generated automatically.
- `secondary_label` and `secondary_url` optionally add a second button for a distinct project resource. Supply both fields together and use an HTTPS URL; omit both to show only Source code.
- `mobile` must be a subset of `desktop` with at most seven technologies.
- `art` selects a reusable illustration: `api` (cubes), `load` (chart), or `ui` (windows, also the default).
- `featured` is optional and defaults to `false`; at most one project may be featured.
- New technology labels get a neutral glass badge automatically. Assign their category in `technologies.json` to use the shared category color.

Commit `projects.json`, the regenerated SVGs, and `README.md` together. No workflow or generator changes are needed to add a project that fits an existing layout. Reorder the list to change display order.

Content is wrapped and validated before files are written. If a long name, description, or badge exceeds the layout, shorten its text; the generator reports the problem rather than cropping it silently.

## Navigation

Project content and illustrations are decorative; the two footer buttons provide explicit navigation. Source code opens the repository. The optional second button opens a distinct project resource, rather than repeating the repository README.

```json
"secondary_label": "Test report",
"secondary_url": "https://example.com/report/"
```

Current resources are the API architecture diagram, the latest published Locust report, and the UI project's Allure report. The report links use their stable `/latest/` and `/main/` entries.

The generator draws a complete board once per layout, including the outer surface, each card's frame, and both buttons. `board_slice()` crops that same scene for the header, card bodies, and two independently linked footer images. The footer boundary is a whole SVG pixel inside the button gap. Image dimensions and `viewBox` extents are identical integers; `preserveAspectRatio="none"` on the crops prevents separate aspect-ratio letterboxing after browser subpixel rounding.

Mobile and tablet HTML widths use each crop's exact fraction of the board. Desktop displays the header and bodies at 846 CSS pixels, with footer widths of 288 and 558 pixels. These whole widths preserve the same proportions and add up exactly, avoiding Chrome's separate rounding of fractional body and footer widths that can produce a one-pixel step in the border. The SVG assets remain unchanged.

Buttons remain left aligned with gaps of 8, 12, and 16 SVG units in mobile, tablet, and desktop layouts. Their rendered spacing scales with the board. Each footer image retains its own HTML link. When a project has no secondary action, the right slice displays only the background and has no link. Body images use anchors without `href` to suppress GitHub's automatic links to image files.

## Responsive layouts

`picture` selects the composition, and the matching `source`/`img` width keeps the footer proportions synchronized with the body. The image itself does not contain navigation handlers. No JavaScript, inline README styles, positioning overlays, or presentation tables are required.

The breakpoints account for the profile sidebar, which appears at a viewport width of 768px and reduces the README's available width. Measurements of the current profile showed 518px of content at a 600px viewport, 398px at 768px, and a maximum of 846px at 1280–1440px. The capped GitHub profile container prevents enlargement on wider desktop screens.

| Viewport | Composition | Board width |
| --- | --- | --- |
| Up to 480px | Mobile | 392 SVG units |
| 481–767px | Tablet | 600 SVG units |
| 768–820px, with the sidebar | Mobile | 392 SVG units |
| 821–1280px | Tablet | 600 SVG units |
| Above 1280px | Desktop | 940 SVG units, displayed at 846px |

The narrow portrait-tablet range deliberately uses the compact composition because its actual content width is similar to a phone's. In particular, 800px and 801px select the same layout. Desktop starts above 1280 CSS pixels, where the profile container can accommodate its fixed 846px display width. Browser zoom reduces the CSS viewport, so a laptop can switch to the taller tablet composition at 125% zoom while retaining its existing mobile rules.

Tablet cards have their own text wrapping, full technology stack, and smaller illustrations aligned with the visible top of the first description line. The Featured badge sits next to the project title. Media queries inside the SVG select compact, medium, and wide content at displayed body-image widths of 560px and 700px. They keep typography and icons restrained as the tablet composition grows. The compact profile is the default; minimum-width overrides cover fractional widths without gaps, including browser zoom. These styles are inside the SVG assets, not CSS attached to the README.

Mobile retains its configured subset of at most seven technologies. Desktop retains the horizontal illustration on the right and uses 22-unit description text to remain readable at its lower switching boundary. If GitHub changes the profile's sidebar or container widths, remeasure the available content before changing `MOBILE_MEDIA` and `TABLET_MEDIA`.

## Technology categories

[technologies.json](../assets/projects/technologies.json) maps tool names to their primary role. Every tool in the same category uses the same border, text, and translucent fill colors in both layouts.

| Category | Border accent | Current tools |
| --- | --- | --- |
| `languages` | Blue `#4388E3` | Python |
| `testing` | Green `#329967` | Pytest, pytest-xdist, Playwright, Locust, Allure |
| `api` | Cyan `#24A7B1` | FastAPI, HTTPX, gRPC |
| `data` | Amber `#CDA14D` | Kafka, PostgreSQL, Pydantic |
| `infrastructure` | Indigo `#6376D8` | Docker, Poetry |
| `monitoring` | Orange `#BD7245` | Prometheus, Grafana, Loguru |
| `quality` | Purple `#A17BDD` | Ruff, Mypy |

Pydantic belongs to data because it validates data schemas. Poetry belongs to infrastructure because it manages project dependencies and environments. Categories describe a primary role, not a tool's branding.

For example, add `"NewTool": "testing"` to `technologies.json` and run the same generation command to give that tool the testing color. No generator edits are required. Unclassified tools remain neutral gray; misspelled category names stop generation before files are written. Commit the mapping with regenerated SVGs when changing it.

## Preview generation

For generation into a temporary folder without updating the profile:

```sh
python scripts/generate_project_cards.py --output /path/to/preview
```

Add `--readme /path/to/README.md` to update a separate README containing the same markers.

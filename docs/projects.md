# Updating My Projects

Edit [projects.json](../assets/projects/projects.json), then run from the repository root:

```sh
python scripts/generate_project_cards.py
```

The command regenerates both layouts, all linked navigation slices, and the README block between `MY PROJECTS` markers. The outer panel height, project order, spacing, and final rounded corners follow the list automatically. Other README sections are preserved.

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

Current resources are the API architecture diagram, an example Locust report, and the UI project's Allure report. The Locust link identifies a particular example run; update its URL to feature a different run. The UI report's `/main/` entry redirects to its published report.

Every layout keeps two equal footer slices to preserve the shared outer panel. When a project has no secondary action, the right slice displays only the background and has no link. Body images use anchors without `href` to suppress GitHub's automatic links to image files.

## Technology categories

[technologies.json](../assets/projects/technologies.json) maps tool names to their primary role. Every tool in the same category uses the same border, text, and translucent fill colors in both layouts.

| Category | Border accent | Current tools |
| --- | --- | --- |
| `languages` | Blue `#4388E3` | Python |
| `testing` | Green `#329967` | Pytest, pytest-xdist, Playwright, Locust, Allure |
| `api` | Cyan `#24A7B1` | FastAPI, HTTPX, gRPC |
| `data` | Amber `#CDA14D` | Kafka, PostgreSQL, Pydantic |
| `infrastructure` | Indigo `#6376D8` | Docker, Poetry |
| `monitoring` | Orange `#BD7245` | Prometheus, Grafana |
| `quality` | Purple `#A17BDD` | Ruff, Mypy |

Pydantic belongs to data because it validates data schemas. Poetry belongs to infrastructure because it manages project dependencies and environments. Categories describe a primary role, not a tool's branding.

For example, add `"NewTool": "testing"` to `technologies.json` and run the same generation command to give that tool the testing color. No generator edits are required. Unclassified tools remain neutral gray; misspelled category names stop generation before files are written. Commit the mapping with regenerated SVGs when changing it.

## Preview generation

For generation into a temporary folder without updating the profile:

```sh
python scripts/generate_project_cards.py --output /path/to/preview
```

Add `--readme /path/to/README.md` to update a separate README containing the same markers.

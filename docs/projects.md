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
- `name` is the repository name under `Barbaron86`. Repository and documentation links are generated automatically; documentation targets `blob/main/README.md`.
- `mobile` must be a subset of `desktop` with at most seven technologies.
- `art` selects a reusable illustration: `api` (cubes), `load` (chart), or `ui` (windows, also the default).
- `featured` is optional and defaults to `false`; at most one project may be featured.
- New technology labels get a neutral glass badge automatically; adding a color is optional.

Commit `projects.json`, the regenerated SVGs, and `README.md` together. No workflow or generator changes are needed to add a project that fits an existing layout. Reorder the list to change display order.

Content is wrapped and validated before files are written. If a long name, description, or badge exceeds the layout, shorten its text; the generator reports the problem rather than cropping it silently.

For generation into a temporary folder without updating the profile:

```sh
python scripts/generate_project_cards.py --output /path/to/preview
```

Add `--readme /path/to/README.md` to update a separate README containing the same markers.

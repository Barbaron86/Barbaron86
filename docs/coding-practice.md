# Coding Practice cards

The profile uses four self-contained 600 × 224 SVG cards in `output`.
LeetCode bars show the share of solved tasks at each difficulty, including
empty bars when no tasks are solved. Codewars displays the current overall
and Python ranks, completed kata and Honor directly from the public API.
Neither platform's failures prevent refreshing the other platform.

## Configuration and activation

In **Settings → Secrets and variables → Actions → Variables**, set:

| Repository variable | Confirmed public account |
| --- | --- |
| `LEETCODE_USERNAME` | `barbaron86` |
| `CODEWARS_USERNAME` | `Barbaron86` |

No cookies, platform passwords or personal tokens are needed. The publisher
uses the job-scoped `GITHUB_TOKEN`. After the PR is merged by the owner,
**Refresh Coding Practice** runs daily at `47 3 * * *` (06:47 Moscow time).
GitHub may delay scheduled runs. It also supports **Run workflow**; use
`source_ref: main` for normal updates. A reviewed feature ref is available
for pre-merge validation when the workflow is registered on the default branch.

The schedule always checks out `main`. Generation runs with read-only
repository permissions; only the publication job has `contents: write`.
Generation records `git rev-parse HEAD` as an output. Publication checks out
that exact SHA and verifies it before using the generated artifact.
The workflow shares `profile-assets` concurrency with Snake and Streak.
Publication clones the newest `output`, overlays only complete successful
theme pairs, skips identical files and retries non-force pushes up to three
times. Existing Snake/Streak files and a failed platform's cards are preserved.

The final report job fails visibly if any API refresh failed, even when
valid cards from the other platform were successfully published. The
generation job summary identifies the affected source and diagnostic.
When both sources fail, there is no publication.

## Local use and validation

Python 3.12+ and Git are the only runtime requirements:

```sh
python -m compileall -q scripts
python scripts/update_coding_stats.py --leetcode barbaron86 --codewars Barbaron86 --output dist
python scripts/publish_coding_stats.py --assets dist --repo .
```

The last command writes to the remote `output` branch. Review generated
files first. Use a fresh generation directory before publishing so it
contains only the current successful platforms. Local generation can also
update an existing directory; invalid requests retain its last good cards.

The generator exits 1 on partial/full failure and 0 on complete success.
During development, 31 offline unit and local Git integration tests passed.
At the owner's explicit request, their source and the separate PR CI workflow
were removed. They are not ongoing CI checks. The refresh workflow checks Python
syntax before generation; this does not replace behavioral testing.

## Sources and rendering

- [LeetCode profile](https://leetcode.com/u/barbaron86/): public GraphQL `matchedUser.username` and `submitStatsGlobal.acSubmissionNum` at `https://leetcode.com/graphql/`.
- [Codewars user API](https://dev.codewars.com/#get-user): username, `ranks.overall.name`, `ranks.languages.python.name`, `honor`, `codeChallenges.totalCompleted`.
- Codewars vector source: [Simple Icons](https://github.com/simple-icons/simple-icons/blob/develop/icons/codewars.svg), distributed under [CC0](https://github.com/simple-icons/simple-icons/blob/develop/LICENSE.md). A local SVG mask extracts the circular mark; rendered cards embed its vector data. Brand names identify the linked public profiles.
- LeetCode mark: inline vector strokes in `scripts/coding_cards.py`.

Gradients, translucent panels, clipped mountain shapes and system fonts
produce the glass effect without JavaScript, external resources,
`foreignObject` or unsupported backdrop filters. SVG content is deterministic;
there is no per-run date or random decoration.

README uses linked `picture` elements with dark/light media sources.
Each card is displayed at 400 px; GitHub's image max-width permits wrapping
and shrinking on narrow screens. Verify the rendered GitHub README after
publication as well as the source SVGs.

"""Generate self-hosted LeetCode and Codewars SVG cards from public stats."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

LEETCODE_QUERY = """
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
    submitStatsGlobal { acSubmissionNum { difficulty count } }
  }
}
"""
THEMES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "text": "#e6edf3", "muted": "#8b949e", "track": "#21262d"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#1f2328", "muted": "#59636e", "track": "#eaeef2"},
}


def get_json(url: str, payload: dict | None = None) -> dict:
    """Fetch a public JSON API with a timeout; raise on HTTP and API errors."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"User-Agent": "Barbaron86-GitHub-Profile/1.0", "Accept": "application/json"}
    if body is not None:
        headers.update({"Content-Type": "application/json", "Referer": "https://leetcode.com/"})
    request = Request(url, data=body, headers=headers, method="POST" if body else "GET")
    try:
        with urlopen(request, timeout=20) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"Cannot fetch {url}: {error}") from error
    if not isinstance(result, dict) or result.get("errors"):
        raise ValueError(f"Unexpected API response from {url}: {str(result)[:300]}")
    return result


def leetcode_stats(username: str) -> dict[str, int]:
    response = get_json("https://leetcode.com/graphql/", {"query": LEETCODE_QUERY, "variables": {"username": username}})
    user = response.get("data", {}).get("matchedUser")
    if not user:
        raise ValueError(f"LeetCode user not found: {username}")
    counts = {entry["difficulty"]: int(entry["count"]) for entry in user["submitStatsGlobal"]["acSubmissionNum"]}
    if not all(key in counts for key in ("All", "Easy", "Medium", "Hard")):
        raise ValueError("Missing LeetCode difficulty counts")
    return counts


def codewars_stats(username: str) -> dict:
    response = get_json(f"https://www.codewars.com/api/v1/users/{quote(username, safe='')}")
    if not response.get("username") or not response.get("ranks", {}).get("overall"):
        raise ValueError(f"Codewars user not found or stats unavailable: {username}")
    return response


def svg_start(theme: dict[str, str], title: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="468" height="224" viewBox="0 0 468 224" '
            f'role="img" aria-label="{escape(title)}">'
            f'<rect x="0.5" y="0.5" width="467" height="223" rx="15" fill="{theme["bg"]}" '
            f'stroke="{theme["border"]}"/>')


def label(x: int, y: int, value: object, theme: dict[str, str], *, size: int = 14,
          color: str | None = None, weight: int = 400, anchor: str = "start") -> str:
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color or theme["text"]}" '
            f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" '
            f'font-size="{size}" font-weight="{weight}">{escape(str(value))}</text>')


def card_header(name: str, username: str, theme: dict[str, str], accent: str) -> str:
    return (f'<rect x="28" y="25" width="4" height="25" rx="2" fill="{accent}"/>'
            + label(44, 44, name, theme, size=20, weight=700)
            + label(440, 43, f"@{username}", theme, size=11, color=theme["muted"], anchor="end"))


def footer(theme: dict[str, str], updated: str) -> str:
    return (f'<path d="M28 190H440" stroke="{theme["border"]}"/>'
            + label(28, 210, f"UPDATED {updated} UTC", theme, size=10, color=theme["muted"]) + "</svg>\n")


def make_leetcode_svg(username: str, counts: dict[str, int], variant: str, updated: str) -> str:
    theme = THEMES[variant]
    svg = svg_start(theme, f"LeetCode statistics for {username}") + card_header("LeetCode", username, theme, "#ffa116")
    svg += label(28, 117, counts["All"], theme, size=55, weight=750)
    svg += label(30, 144, "PROBLEMS SOLVED", theme, size=11, color=theme["muted"], weight=600)
    colors = {"Easy": "#2db89b", "Medium": "#d6a01d", "Hard": "#e56670"}
    for difficulty, y in (("Easy", 87), ("Medium", 122), ("Hard", 157)):
        svg += label(220, y, difficulty.upper(), theme, size=11, color=colors[difficulty], weight=700)
        svg += label(436, y, counts[difficulty], theme, size=13, weight=650, anchor="end")
        svg += f'<rect x="220" y="{y + 8}" width="216" height="6" rx="3" fill="{theme["track"]}"/>'
        width = round(216 * counts[difficulty] / max(counts["All"], 1), 2)
        if width:
            svg += f'<rect x="220" y="{y + 8}" width="{width}" height="6" rx="3" fill="{colors[difficulty]}"/>'
    return svg + footer(theme, updated)


def make_codewars_svg(username: str, stats: dict, variant: str, updated: str) -> str:
    theme = THEMES[variant]
    ranks = stats["ranks"]
    overall = ranks["overall"]["name"]
    python_rank = ranks.get("languages", {}).get("python", {}).get("name", "—")
    svg = svg_start(theme, f"Codewars statistics for {username}") + card_header("Codewars", username, theme, "#bb432c")
    svg += label(28, 121, overall, theme, size=43, weight=750)
    svg += label(30, 145, "OVERALL RANK", theme, size=11, color=theme["muted"], weight=600)
    for name, value, y in (("KATA COMPLETED", stats["codeChallenges"]["totalCompleted"], 91),
                            ("HONOR", stats["honor"], 126), ("PYTHON RANK", python_rank, 161)):
        svg += label(220, y, name, theme, size=11, color=theme["muted"], weight=600)
        svg += label(436, y, value, theme, size=17, weight=700, anchor="end")
    return svg + footer(theme, updated)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leetcode", default=os.getenv("LEETCODE_USERNAME", ""))
    parser.add_argument("--codewars", default=os.getenv("CODEWARS_USERNAME", ""))
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    if not args.leetcode.strip() or not args.codewars.strip():
        parser.error("Set LEETCODE_USERNAME and CODEWARS_USERNAME repository variables")

    leetcode = leetcode_stats(args.leetcode.strip())
    codewars = codewars_stats(args.codewars.strip())
    updated = datetime.now(timezone.utc).strftime("%d %b %Y")
    args.output.mkdir(parents=True, exist_ok=True)
    for variant in THEMES:
        (args.output / f"leetcode-{variant}.svg").write_text(
            make_leetcode_svg(args.leetcode, leetcode, variant, updated), encoding="utf-8")
        (args.output / f"codewars-{variant}.svg").write_text(
            make_codewars_svg(args.codewars, codewars, variant, updated), encoding="utf-8")
    print(f"Generated 4 coding stats SVGs in {args.output}")


if __name__ == "__main__":
    main()

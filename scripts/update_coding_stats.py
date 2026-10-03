"""Generate independently updated, self-hosted LeetCode and Codewars cards."""

from __future__ import annotations

import argparse
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from coding_cards import THEMES, make_codewars_svg, make_leetcode_svg

LEETCODE_QUERY = """
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
    username
    submitStatsGlobal { acSubmissionNum { difficulty count } }
  }
}
"""
MAX_ATTEMPTS = 3


def get_json(url: str, payload: dict | None = None) -> dict:
    """Retry transient HTTP/transport errors, never bypass platform protection."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"User-Agent": "Barbaron86-GitHub-Profile/1.0", "Accept": "application/json"}
    if body is not None:
        headers.update({"Content-Type": "application/json", "Referer": "https://leetcode.com/"})
    request = Request(url, data=body, headers=headers, method="POST" if body is not None else "GET")
    for attempt in range(MAX_ATTEMPTS):
        try:
            with urlopen(request, timeout=20) as response:
                result = json.load(response)
        except HTTPError as error:
            retryable = error.code in (408, 429, 500, 502, 503, 504)
            error.close()
            if not retryable or attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError(f"Cannot fetch {url}: HTTP {error.code} ({attempt + 1} attempts)") from error
        except (URLError, TimeoutError, ConnectionError, OSError, HTTPException) as error:
            if attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError(f"Cannot fetch {url} after {MAX_ATTEMPTS} attempts: {error}") from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError(f"Invalid JSON response from {url}") from error
        else:
            if not isinstance(result, dict):
                raise ValueError(f"Expected JSON object from {url}")
            if result.get("errors") or result.get("success") is False:
                raise ValueError(f"API error from {url}: {str(result.get('errors') or result.get('reason'))[:200]}")
            return result
        sleep(2 ** attempt)
    raise RuntimeError("HTTP retry budget exhausted")


def object_field(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Missing or invalid object: {context}")
    return value


def count_field(value: object, context: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{context} must be a nonnegative integer")
    return value


def check_identity(value: object, username: str, platform: str) -> None:
    if not isinstance(value, str) or value.casefold() != username.casefold():
        raise ValueError(f"{platform} response does not match requested user {username}")


def leetcode_stats(username: str) -> dict[str, int]:
    response = get_json("https://leetcode.com/graphql/", {"query": LEETCODE_QUERY, "variables": {"username": username}})
    user = object_field(response.get("data"), "LeetCode data").get("matchedUser")
    if user is None:
        raise ValueError(f"LeetCode user not found: {username}")
    user = object_field(user, "LeetCode matchedUser")
    check_identity(user.get("username"), username, "LeetCode")
    entries = object_field(user.get("submitStatsGlobal"), "submitStatsGlobal").get("acSubmissionNum")
    if not isinstance(entries, list):
        raise ValueError("Missing LeetCode acSubmissionNum list")
    counts = {}
    for raw_entry in entries:
        entry = object_field(raw_entry, "LeetCode difficulty")
        name = entry.get("difficulty")
        if name not in ("All", "Easy", "Medium", "Hard") or name in counts:
            raise ValueError("Unknown or duplicate LeetCode difficulty")
        counts[name] = count_field(entry.get("count"), f"LeetCode {name}")
    if set(counts) != {"All", "Easy", "Medium", "Hard"}:
        raise ValueError("Missing LeetCode difficulty counts")
    if counts["All"] != counts["Easy"] + counts["Medium"] + counts["Hard"]:
        raise ValueError("LeetCode total is inconsistent with difficulty counts")
    return counts


def rank_name(value: object, context: str) -> str:
    name = object_field(value, context).get("name")
    if not isinstance(name, str) or re.fullmatch(r"[1-8] (?:kyu|dan)", name) is None:
        raise ValueError(f"Invalid Codewars rank: {context}")
    return name


def codewars_stats(username: str) -> dict:
    response = get_json(f"https://www.codewars.com/api/v1/users/{quote(username, safe='')}")
    check_identity(response.get("username"), username, "Codewars")
    ranks = object_field(response.get("ranks"), "Codewars ranks")
    overall = rank_name(ranks.get("overall"), "overall")
    languages = ranks.get("languages")
    languages = {} if languages is None else object_field(languages, "Codewars languages")
    python = languages.get("python")
    python_name = rank_name(python, "python") if python is not None else "—"
    challenges = object_field(response.get("codeChallenges"), "Codewars codeChallenges")
    return {
        "username": response["username"],
        "honor": count_field(response.get("honor"), "Codewars honor"),
        "ranks": {"overall": {"name": overall}, "languages": {"python": {"name": python_name}}},
        "codeChallenges": {"totalCompleted": count_field(challenges.get("totalCompleted"), "Codewars totalCompleted")},
    }


def save_pair(output: Path, cards: dict[str, str]) -> bool:
    """Validate/stage both themes before replacing; roll back on write failure."""
    for svg in cards.values():
        root = ET.fromstring(svg)
        if root.tag != "{http://www.w3.org/2000/svg}svg":
            raise ValueError("Rendered image is not SVG")
    output.mkdir(parents=True, exist_ok=True)
    originals = {name: (output / name).read_bytes() if (output / name).exists() else None for name in cards}
    encoded = {name: svg.encode("utf-8") for name, svg in cards.items()}
    changed = [name for name in cards if originals[name] != encoded[name]]
    if not changed:
        return False
    with tempfile.TemporaryDirectory(prefix=".coding-", dir=output) as stage:
        stage = Path(stage)
        for name in changed:
            (stage / name).write_bytes(encoded[name])
        replaced = []
        try:
            for name in changed:
                (stage / name).replace(output / name)
                replaced.append(name)
        except OSError:
            for name in reversed(replaced):
                if originals[name] is None:
                    (output / name).unlink(missing_ok=True)
                else:
                    (stage / name).write_bytes(originals[name])
                    (stage / name).replace(output / name)
            raise
    return True


def update_cards(leetcode: str, codewars: str, output: Path) -> dict[str, str]:
    results = {}
    for platform, username, fetch, render in (
        ("leetcode", leetcode, leetcode_stats, make_leetcode_svg),
        ("codewars", codewars, codewars_stats, make_codewars_svg),
    ):
        try:
            username = username.strip()
            if not username:
                raise ValueError(f"Set {platform.upper()}_USERNAME repository variable or --{platform}")
            data = fetch(username)
            cards = {f"{platform}-{variant}.svg": render(username, data, variant) for variant in THEMES}
            results[platform] = "updated" if save_pair(output, cards) else "unchanged"
        except (ValueError, RuntimeError, OSError, ET.ParseError) as error:
            results[platform] = f"error: {error}"
        print(f"{platform}: {results[platform]}", file=sys.stderr if results[platform].startswith("error:") else sys.stdout)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leetcode", default=os.getenv("LEETCODE_USERNAME", ""))
    parser.add_argument("--codewars", default=os.getenv("CODEWARS_USERNAME", ""))
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args(argv)
    results = update_cards(args.leetcode, args.codewars, args.output)
    has_assets = any(not result.startswith("error:") for result in results.values())
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as report:
            report.write(f"has_assets={'true' if has_assets else 'false'}\n")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as report:
            report.write("### Coding Practice refresh\n\n")
            for platform, result in results.items():
                safe_result = result.replace("`", "'").replace("\n", " ").replace("\r", " ")
                report.write(f"- **{platform}**: `{safe_result}`\n")
            report.write("\nFailed platforms retain their last published images.\n")
    return 1 if any(result.startswith("error:") for result in results.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())

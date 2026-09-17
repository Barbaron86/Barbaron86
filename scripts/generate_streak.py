from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

HTTP_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2
MAX_RETRY_DELAY_SECONDS = 60
RETRYABLE_HTTP_CODES = {429, 502, 503, 504}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = PROJECT_ROOT / "assets" / "streak-template.svg"
OUTPUT_PATH = PROJECT_ROOT / "dist" / "streak.svg"

PLACEHOLDER_PATTERN = re.compile(r"\{\{[A-Z_]+\}\}")

MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

ContributionMap = dict[date, int]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StreakPeriod:
    start: date | None
    end: date | None
    days: int


@dataclass(frozen=True)
class StreakStats:
    total_contributions: int
    first_contribution: date | None
    current: StreakPeriod
    longest: StreakPeriod
    current_year_contributions: int
    active_days: int
    best_day_date: date | None
    best_day_count: int


def _retry_delay(attempt: int, retry_after: str | None = None) -> int:
    """Return delay before the next HTTP retry."""
    if retry_after and retry_after.isdigit():
        return min(int(retry_after), MAX_RETRY_DELAY_SECONDS)
    return RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))


def _is_retryable_http_error(error: HTTPError) -> bool:
    if error.code in RETRYABLE_HTTP_CODES:
        return True
    # GitHub may use 403 for a temporary secondary rate limit.
    if error.code == 403 and error.headers.get("Retry-After"):
        return True
    return False


def github_graphql(
    token: str, query: str, variables: dict[str, object],
) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode()

    for attempt in range(1, MAX_RETRIES + 1):
        request = Request(
            GITHUB_GRAPHQL_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "Barbaron86-GitHub-Streak",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                body = response.read().decode("utf-8")

        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")

            if not _is_retryable_http_error(error) or attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"GitHub API returned HTTP {error.code}: {body}"
                ) from error

            delay = _retry_delay(
                attempt, retry_after=error.headers.get("Retry-After"),
            )
            logger.warning(
                "GitHub API returned HTTP %d. "
                "Retrying attempt %d/%d in %d seconds.",
                error.code, attempt + 1, MAX_RETRIES, delay,
            )
            time.sleep(delay)
            continue

        except (URLError, TimeoutError) as error:
            if attempt == MAX_RETRIES:
                reason = getattr(error, "reason", str(error))
                raise RuntimeError(
                    f"Could not connect to GitHub API: {reason}"
                ) from error

            delay = _retry_delay(attempt)
            logger.warning(
                "GitHub API connection failed. "
                "Retrying attempt %d/%d in %d seconds.",
                attempt + 1, MAX_RETRIES, delay,
            )
            time.sleep(delay)
            continue

        try:
            result = json.loads(body)
        except json.JSONDecodeError as error:
            raise RuntimeError("GitHub API returned invalid JSON") from error

        if result.get("errors"):
            raise RuntimeError(f"GitHub GraphQL error: {result['errors']}")

        data = result.get("data")
        if data is None:
            raise RuntimeError(
                "GitHub GraphQL response does not contain data"
            )

        return data

    raise RuntimeError(
        "GitHub GraphQL request failed after all retry attempts"
    )


def get_account_created_year(token: str, username: str) -> int:
    """Return the year when the GitHub account was created."""
    query = """
    query AccountInfo($login: String!) {
      user(login: $login) {
        createdAt
      }
    }
    """

    data = github_graphql(token=token, query=query, variables={"login": username})
    user = data.get("user")

    if user is None:
        raise RuntimeError(f"GitHub user '{username}' was not found")

    # Python 3.12 natively understands the trailing "Z".
    created_at = datetime.fromisoformat(user["createdAt"])
    return created_at.year


def get_contributions_for_year(
    token: str, username: str, year: int,
) -> ContributionMap:
    """Fetch the GitHub contribution calendar for one year."""
    query = """
    query Contributions(
      $login: String!,
      $from: DateTime!,
      $to: DateTime!
    ) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """

    data = github_graphql(
        token=token,
        query=query,
        variables={
            "login": username,
            "from": f"{year}-01-01T00:00:00Z",
            "to": f"{year}-12-31T23:59:59Z",
        },
    )

    user = data.get("user")
    if user is None:
        raise RuntimeError(f"GitHub user '{username}' was not found")

    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    contributions: ContributionMap = {}

    for week in weeks:
        for day in week["contributionDays"]:
            d = date.fromisoformat(day["date"])
            contributions[d] = int(day["contributionCount"])

    return contributions


def get_all_contributions(
    token: str, username: str, today: date,
) -> ContributionMap:
    """Fetch all available contribution-calendar data for the user."""
    first_year = get_account_created_year(token=token, username=username)
    contributions: ContributionMap = {}

    for year in range(first_year, today.year + 1):
        logger.info("Fetching GitHub contributions for %d", year)
        year_data = get_contributions_for_year(
            token=token, username=username, year=year,
        )
        contributions.update(year_data)

    return {d: c for d, c in contributions.items() if d <= today}


def _active_contributions(contributions: ContributionMap) -> ContributionMap:
    """Return only dates that contain at least one contribution."""
    return {d: c for d, c in contributions.items() if c > 0}


def calculate_current_streak(
    contributions: ContributionMap, today: date,
) -> StreakPeriod:
    """Calculate the currently active daily streak."""
    end = today

    # Today must not break the current streak while the day
    # is still in progress and has no contributions yet.
    if contributions.get(today, 0) == 0:
        end = today - timedelta(days=1)

    if contributions.get(end, 0) == 0:
        return StreakPeriod(start=None, end=None, days=0)

    start = end
    while contributions.get(start - timedelta(days=1), 0) > 0:
        start -= timedelta(days=1)

    return StreakPeriod(start=start, end=end, days=(end - start).days + 1)


def calculate_longest_streak(contributions: ContributionMap) -> StreakPeriod:
    """Calculate the longest consecutive sequence of active days.

    Assumes contributions are pre-filtered to not exceed today.
    """
    active_dates = sorted(_active_contributions(contributions))

    if not active_dates:
        return StreakPeriod(start=None, end=None, days=0)

    current_start = current_end = active_dates[0]
    current_days = 1
    longest = StreakPeriod(start=current_start, end=current_end, days=1)

    for d in active_dates[1:]:
        if d - current_end == timedelta(days=1):
            current_end = d
            current_days += 1
        else:
            current_start = current_end = d
            current_days = 1

        if current_days > longest.days:
            longest = StreakPeriod(
                start=current_start, end=current_end, days=current_days,
            )

    return longest


def calculate_first_contribution(contributions: ContributionMap) -> date | None:
    """Return the first date containing a contribution."""
    active = _active_contributions(contributions)
    if not active:
        return None
    return min(active)


def calculate_current_year_contributions(
    contributions: ContributionMap, current_year: int,
) -> int:
    """Return the number of contributions in the current year."""
    return sum(
        count for d, count in contributions.items()
        if d.year == current_year
    )


def calculate_active_days(
    contributions: ContributionMap, current_year: int,
) -> int:
    """Return active-day count for the current year."""
    return sum(
        1 for d, count in contributions.items()
        if d.year == current_year and count > 0
    )


def calculate_best_day(contributions: ContributionMap) -> tuple[date | None, int]:
    """Return the date with the highest contribution count.

    When tied, the latest date wins.
    """
    active = _active_contributions(contributions)
    if not active:
        return None, 0

    best_date, best_count = max(
        active.items(), key=lambda item: (item[1], item[0]),
    )
    return best_date, best_count


def calculate_stats(contributions: ContributionMap, today: date) -> StreakStats:
    """Calculate all statistics displayed on the SVG card."""
    best_day_date, best_day_count = calculate_best_day(contributions)

    return StreakStats(
        total_contributions=sum(contributions.values()),
        first_contribution=calculate_first_contribution(contributions),
        current=calculate_current_streak(contributions, today),
        longest=calculate_longest_streak(contributions),
        current_year_contributions=calculate_current_year_contributions(
            contributions, today.year,
        ),
        active_days=calculate_active_days(contributions, today.year),
        best_day_date=best_day_date,
        best_day_count=best_day_count,
    )


def format_date(value: date | None) -> str:
    """Format a date using deterministic English month names."""
    if value is None:
        return "\u2014"
    return f"{MONTHS[value.month - 1]} {value.day}, {value.year}"


def format_period(period: StreakPeriod) -> str:
    """Format a streak period for SVG display."""
    if period.start is None or period.end is None:
        return "\u2014"
    if period.start == period.end:
        return format_date(period.start)
    return f"{format_date(period.start)} \u2014 {format_date(period.end)}"


def render_svg(stats: StreakStats, username: str, current_year: int) -> str:
    """Render statistics into the SVG template."""
    if not TEMPLATE_PATH.exists():
        raise RuntimeError(f"SVG template not found: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    raw_replacements = {
        "{{USERNAME}}": username,
        "{{TOTAL}}": str(stats.total_contributions),
        "{{FIRST_CONTRIBUTION}}": format_date(stats.first_contribution),
        "{{CURRENT}}": str(stats.current.days),
        "{{CURRENT_RANGE}}": format_period(stats.current),
        "{{LONGEST}}": str(stats.longest.days),
        "{{LONGEST_RANGE}}": format_period(stats.longest),
        "{{THIS_YEAR}}": str(stats.current_year_contributions),
        "{{CURRENT_YEAR}}": str(current_year),
        "{{ACTIVE_DAYS}}": str(stats.active_days),
        "{{BEST_DAY_COUNT}}": str(stats.best_day_count),
        "{{BEST_DAY_DATE}}": format_date(stats.best_day_date),
    }

    for placeholder, raw_value in raw_replacements.items():
        if placeholder not in template:
            raise RuntimeError(
                f"SVG template is missing placeholder {placeholder}"
            )
        template = template.replace(placeholder, escape(raw_value))

    remaining = sorted(set(PLACEHOLDER_PATTERN.findall(template)))
    if remaining:
        raise RuntimeError(f"Unsubstituted SVG placeholders: {remaining}")

    return template


def save_svg(svg: str) -> None:
    """Write the generated SVG to the dist directory."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not svg.endswith("\n"):
        svg += "\n"

    OUTPUT_PATH.write_text(svg, encoding="utf-8")


def configure_logging() -> None:
    """Configure console logging for GitHub Actions."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def main() -> None:
    """Generate the GitHub streak SVG."""
    token = os.environ.get("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_USERNAME")

    if not token:
        raise RuntimeError("Environment variable GITHUB_TOKEN is required")
    if not username:
        raise RuntimeError("Environment variable GITHUB_USERNAME is required")

    today = datetime.now(timezone.utc).date()
    logger.info("Generating GitHub streak for %s", username)

    contributions = get_all_contributions(token=token, username=username, today=today)
    if not contributions:
        raise RuntimeError("GitHub returned no contribution calendar data")

    stats = calculate_stats(contributions, today)
    svg = render_svg(stats, username, today.year)
    save_svg(svg)

    logger.info(
        "Streak SVG generated successfully: %s\n"
        "  Total contributions: %d\n"
        "  First contribution:  %s\n"
        "  Current streak:      %d days\n"
        "  Longest streak:      %d days\n"
        "  Contributions %d:    %d\n"
        "  Active days %d:      %d\n"
        "  Best day:            %d contributions (%s)",
        OUTPUT_PATH,
        stats.total_contributions,
        format_date(stats.first_contribution),
        stats.current.days,
        stats.longest.days,
        today.year, stats.current_year_contributions,
        today.year, stats.active_days,
        stats.best_day_count, format_date(stats.best_day_date),
    )


if __name__ == "__main__":
    configure_logging()

    try:
        main()
    except Exception:
        logger.exception("GitHub streak generation failed")
        sys.exit(1)

"""Overlay valid coding cards onto the latest output branch without force push."""

from __future__ import annotations

import argparse
import base64
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from time import sleep
import xml.etree.ElementTree as ET

ASSET_NAMES = {f"{platform}-{theme}.svg" for platform in ("leetcode", "codewars") for theme in ("dark", "light")}


def run_git(directory: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    # Only Actions needs explicit auth. Keep the provided token in environment,
    # never in command arguments, remote URLs, temporary files or log output.
    if environment.get("GITHUB_TOKEN"):
        index = int(environment.get("GIT_CONFIG_COUNT", "0"))
        environment["GIT_CONFIG_COUNT"] = str(index + 1)
        environment[f"GIT_CONFIG_KEY_{index}"] = "http.https://github.com/.extraheader"
        credential = base64.b64encode(f"x-access-token:{environment['GITHUB_TOKEN']}".encode()).decode()
        environment[f"GIT_CONFIG_VALUE_{index}"] = f"AUTHORIZATION: basic {credential}"
    result = subprocess.run(["git", "-C", str(directory), *arguments], capture_output=True, text=True, env=environment)
    if check and result.returncode:
        raise RuntimeError(f"Git {arguments[0]} failed: {result.stderr.strip()}")
    return result


def validate_assets(directory: Path) -> list[Path]:
    files = sorted(directory.glob("*.svg"))
    names = {path.name for path in files}
    if names - ASSET_NAMES:
        raise ValueError(f"Unexpected assets: {', '.join(sorted(names - ASSET_NAMES))}")
    for platform in ("leetcode", "codewars"):
        pair = {f"{platform}-dark.svg", f"{platform}-light.svg"}
        if names & pair and not pair <= names:
            raise ValueError(f"Incomplete {platform} theme pair")
    for path in files:
        if path.is_symlink() or path.stat().st_size > 1_000_000:
            raise ValueError(f"Invalid SVG asset: {path.name}")
        root = ET.fromstring(path.read_bytes())
        if root.tag != "{http://www.w3.org/2000/svg}svg" or root.attrib.get("viewBox") != "0 0 600 224" or root.attrib.get("role") != "img":
            raise ValueError(f"Invalid SVG root/dimensions/accessibility: {path.name}")
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] in ("script", "foreignObject", "image", "style"):
                raise ValueError(f"SVG contains unsupported content: {path.name}")
            for attribute, value in element.attrib.items():
                if attribute.rsplit("}", 1)[-1].startswith("on") or (attribute.rsplit("}", 1)[-1] == "href" and not value.startswith("#")) or ("url(" in value and not value.startswith("url(#")):
                    raise ValueError(f"SVG contains active/external content: {path.name}")
    return files


def publish_assets(assets: Path, repo: Path, attempts: int = 3) -> bool:
    files = validate_assets(assets)
    if not files:
        print("No new cards; published assets retained.")
        return False
    if not 1 <= attempts <= 5:
        raise ValueError("Publication attempts must be between 1 and 5")
    remote = run_git(repo, "remote", "get-url", "origin").stdout.strip()
    for attempt in range(attempts):
        # Start from the newest remote tree every time. A rejected push leaves
        # the remote unchanged; discarding this temporary clone loses no work.
        with tempfile.TemporaryDirectory(prefix="coding-publish-") as temporary:
            checkout = Path(temporary) / "output"
            run_git(repo, "clone", "--quiet", "--no-checkout", remote, str(checkout))
            exists = run_git(checkout, "show-ref", "--verify", "--quiet", "refs/remotes/origin/output", check=False).returncode == 0
            if exists:
                run_git(checkout, "checkout", "-b", "output", "origin/output")
            else:
                # Unborn branch in an unpopulated checkout: no main files leak
                # into the first asset commit, no orphan checkout cleanup needed.
                run_git(checkout, "symbolic-ref", "HEAD", "refs/heads/output")
            run_git(checkout, "config", "user.name", "github-actions[bot]")
            run_git(checkout, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
            for file in files:
                shutil.copyfile(file, checkout / file.name)
            run_git(checkout, "add", "--", *(file.name for file in files))
            changed = run_git(checkout, "diff", "--cached", "--quiet", check=False)
            if changed.returncode == 0:
                print("Coding cards are already up to date; no commit created.")
                return False
            if changed.returncode != 1:
                raise RuntimeError("Cannot compare generated coding cards")
            run_git(checkout, "commit", "-m", "chore: refresh coding practice cards")
            pushed = run_git(checkout, "push", "origin", "HEAD:refs/heads/output", check=False)
            if pushed.returncode == 0:
                print(f"Published {len(files)} cards to output.")
                return True
            print(f"Publication attempt {attempt + 1}/{attempts} rejected: {pushed.stderr.strip()}")
        if attempt < attempts - 1:
            sleep(2 ** attempt)
    raise RuntimeError(f"Cannot publish coding cards after {attempts} attempts; output retained")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, default=Path("dist"))
    parser.add_argument("--repo", type=Path, default=Path("."))
    args = parser.parse_args()
    publish_assets(args.assets.resolve(), args.repo.resolve())


if __name__ == "__main__":
    main()

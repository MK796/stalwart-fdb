#!/usr/bin/env python3
"""Select stable Stalwart releases that publish the FoundationDB binary."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

API_URL = "https://api.github.com/repos/stalwartlabs/stalwart/releases?per_page=100"
REQUIRED_ASSET = "stalwart-foundationdb-x86_64-unknown-linux-gnu.tar.gz"
TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def github_get_json(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "mk796-stalwart-fdb-builder",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def parse_version(tag: str) -> tuple[int, int, int] | None:
    match = TAG_RE.fullmatch(tag)
    return tuple(int(part) for part in match.groups()) if match else None


def stable_tags(data: object) -> list[str]:
    if not isinstance(data, list):
        raise RuntimeError("Unexpected GitHub releases response")

    releases: list[tuple[tuple[int, int, int], str]] = []
    for release in data:
        if not isinstance(release, dict):
            continue
        if release.get("draft") or release.get("prerelease"):
            continue

        tag = release.get("tag_name")
        version = parse_version(tag) if isinstance(tag, str) else None
        if version is None:
            continue

        assets = release.get("assets")
        asset_names = {
            asset.get("name")
            for asset in (assets if isinstance(assets, list) else [])
            if isinstance(asset, dict)
        }
        if REQUIRED_ASSET not in asset_names:
            continue
        releases.append((version, tag))

    releases.sort(reverse=True)
    if not releases:
        raise RuntimeError("No stable Stalwart release with a FoundationDB binary found")
    return [tag for _, tag in releases]


def major_minor_tag(tag: str) -> str:
    version = parse_version(tag)
    if version is None:
        raise ValueError(f"Not a stable Stalwart tag: {tag}")
    return f"v{version[0]}.{version[1]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--releases-file", type=Path)
    parser.add_argument("--print-latest", action="store_true")
    parser.add_argument("--print-major-minor", metavar="TAG")
    parser.add_argument("--validate", metavar="TAG")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.print_major_minor:
        print(major_minor_tag(args.print_major_minor))
        return 0

    if args.releases_file:
        data = json.loads(args.releases_file.read_text(encoding="utf-8"))
    else:
        data = github_get_json(API_URL)
    tags = stable_tags(data)

    if args.validate:
        if args.validate not in tags:
            raise RuntimeError(
                f"{args.validate} is not a stable Stalwart release with {REQUIRED_ASSET}"
            )
        print(args.validate)
    elif args.json:
        print(json.dumps({"latest": tags[0], "tags": tags}, sort_keys=True))
    else:
        print(tags[0] if args.print_latest else "\n".join(tags))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)

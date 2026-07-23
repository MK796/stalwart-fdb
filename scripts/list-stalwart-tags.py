#!/usr/bin/env python3
"""Select stable upstream Stalwart tags."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request

TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
API_URL = "https://api.github.com/repos/stalwartlabs/stalwart/tags?per_page=100"


def github_get_json(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "mk796-stalwart-fdb-builder",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def parse_version(tag: str) -> tuple[int, int, int] | None:
    match = TAG_RE.match(tag)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def stable_tags() -> list[str]:
    data = github_get_json(API_URL)
    if not isinstance(data, list):
        raise RuntimeError("Unexpected GitHub tags response")

    tags: list[tuple[tuple[int, int, int], str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        version = parse_version(name)
        if version is None:
            continue
        tags.append((version, name))

    tags.sort(reverse=True)
    if not tags:
        raise RuntimeError("No stable semver Stalwart tags found")
    return [name for _, name in tags]


def major_minor_tag(tag: str) -> str:
    version = parse_version(tag)
    if version is None:
        raise ValueError(f"Not a stable Stalwart tag: {tag}")
    return f"v{version[0]}.{version[1]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--print-latest", action="store_true")
    parser.add_argument("--print-major-minor", metavar="TAG")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.print_major_minor:
        print(major_minor_tag(args.print_major_minor))
        return 0

    tags = stable_tags()
    if args.json:
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

#!/usr/bin/env python3
"""Select the newest explicitly non-AVX FoundationDB client release."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

API_URL = "https://api.github.com/repos/apple/foundationdb/releases?per_page=100"
SERIES_RE = re.compile(r"^\d+\.\d+$")
NON_AVX_RE = re.compile(
    r"\bwithout\s+avx\b|\bnon[-\s]?avx\b|\bno\s+avx\b|\bnot\b.{0,40}\bavx\b",
    re.IGNORECASE,
)
AVX_RE = re.compile(r"\bavx\b", re.IGNORECASE)
REQUIRED_ASSETS = {"libfdb_c.x86_64.so", "libfdb_c.x86_64.so.sha256"}


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


def version_key(version: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in version.split("."))


def classify_release(body: str) -> str:
    if NON_AVX_RE.search(body):
        return "non-avx"
    if AVX_RE.search(body):
        return "avx"
    return "unknown"


def release_assets(release: dict[str, object]) -> set[str]:
    assets = release.get("assets")
    return {
        asset.get("name")
        for asset in (assets if isinstance(assets, list) else [])
        if isinstance(asset, dict) and isinstance(asset.get("name"), str)
    }


def matching_releases(data: object, series: str) -> dict[str, dict[str, object]]:
    if not SERIES_RE.fullmatch(series):
        raise ValueError(f"Invalid FoundationDB series: {series}")
    if not isinstance(data, list):
        raise RuntimeError("Unexpected GitHub releases response")

    version_re = re.compile(rf"^{re.escape(series)}\.\d+$")
    matches: dict[str, dict[str, object]] = {}
    for release in data:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        tag = release.get("tag_name")
        if isinstance(tag, str) and version_re.fullmatch(tag):
            matches[tag] = release
    if not matches:
        raise RuntimeError(f"No FoundationDB {series}.x releases found")
    return matches


def validate_non_avx(version: str, release: dict[str, object]) -> None:
    body = release.get("body")
    classification = classify_release(body if isinstance(body, str) else "")
    if classification != "non-avx":
        raise RuntimeError(f"FoundationDB {version} is classified as {classification}")

    missing = REQUIRED_ASSETS - release_assets(release)
    if missing:
        raise RuntimeError(
            f"FoundationDB {version} is missing required assets: {', '.join(sorted(missing))}"
        )


def select_version(
    data: object, series: str, requested: str | None = None
) -> tuple[str, str]:
    releases = matching_releases(data, series)

    if requested:
        if requested not in releases:
            raise RuntimeError(
                f"Requested FoundationDB {requested} is not a published {series}.x release"
            )
        validate_non_avx(requested, releases[requested])
        return requested, f"requested {requested} is explicitly non-AVX"

    skipped: list[str] = []
    for version in sorted(releases, key=version_key, reverse=True):
        release = releases[version]
        body = release.get("body")
        classification = classify_release(body if isinstance(body, str) else "")
        if classification == "unknown":
            raise RuntimeError(
                f"FoundationDB {version} release notes do not state whether AVX is enabled"
            )
        if classification == "avx":
            skipped.append(version)
            continue

        validate_non_avx(version, release)
        reason = f"selected newest non-AVX FoundationDB {series} release {version}"
        if skipped:
            reason += f"; skipped AVX releases: {', '.join(skipped)}"
        return version, reason

    raise RuntimeError(f"All discovered FoundationDB {series}.x releases are AVX-enabled")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series", required=True)
    parser.add_argument("--releases-file", type=Path)
    parser.add_argument("--requested-version")
    parser.add_argument("--print-version", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.releases_file:
        data = json.loads(args.releases_file.read_text(encoding="utf-8"))
    else:
        data = github_get_json(API_URL)
    version, reason = select_version(data, args.series, args.requested_version)

    if args.json:
        print(json.dumps({"version": version, "reason": reason}, sort_keys=True))
    elif args.print_version:
        print(version)
    else:
        print(f"{version} {reason}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)

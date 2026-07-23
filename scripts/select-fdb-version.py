#!/usr/bin/env python3
"""Select the newest non-AVX FoundationDB 7.3 client release.

The selector intentionally fails closed. FoundationDB release notes explicitly
mark some patch releases as AVX-enabled compatibility builds. Those releases are
skipped. If the requested or newest candidate cannot be classified confidently,
the workflow exits non-zero instead of publishing an unsafe image.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.request

RELEASE_NOTES_URL = "https://apple.github.io/foundationdb/release-notes/release-notes-730.html"
VERSION_RE = re.compile(r"\b(7\.3\.\d+)\b")
TAG_RE = re.compile(r"<h[1-6][^>]*>.*?(7\.3\.\d+).*?</h[1-6]>", re.IGNORECASE | re.DOTALL)
STRIP_TAGS_RE = re.compile(r"<[^>]+>")
AVX_RE = re.compile(r"\bAVX\b|AVX-enabled|AVX enabled|with AVX", re.IGNORECASE)
NON_AVX_RE = re.compile(r"non[- ]AVX|without AVX|no AVX", re.IGNORECASE)


def fetch_text(url: str) -> str:
    headers = {"User-Agent": "mk796-stalwart-fdb-builder"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def html_to_text(raw: str) -> str:
    text = STRIP_TAGS_RE.sub(" ", raw)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def split_sections(raw: str) -> dict[str, str]:
    matches = list(TAG_RE.finditer(raw))
    sections: dict[str, str] = {}

    if matches:
        for index, match in enumerate(matches):
            version = match.group(1)
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
            sections[version] = html_to_text(raw[start:end])
        return sections

    text = html_to_text(raw)
    positions = [(m.group(1), m.start()) for m in VERSION_RE.finditer(text)]
    seen: list[tuple[str, int]] = []
    for version, pos in positions:
        if not seen or seen[-1][0] != version:
            seen.append((version, pos))
    for index, (version, start) in enumerate(seen):
        end = seen[index + 1][1] if index + 1 < len(seen) else len(text)
        sections.setdefault(version, text[start:end])
    return sections


def version_key(version: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in version.split("."))


def classify(section: str) -> str:
    if NON_AVX_RE.search(section):
        return "non-avx"
    if AVX_RE.search(section):
        return "avx"
    return "non-avx"


def select_version(raw: str, requested: str | None = None) -> tuple[str, str]:
    sections = split_sections(raw)
    candidates = sorted(
        (version for version in sections if version.startswith("7.3.")),
        key=version_key,
        reverse=True,
    )
    if not candidates:
        raise RuntimeError("No FoundationDB 7.3 release sections found")

    if requested:
        if requested not in sections:
            raise RuntimeError(f"Requested FDB version {requested} not found in release notes")
        classification = classify(sections[requested])
        if classification != "non-avx":
            raise RuntimeError(f"Requested FDB version {requested} is classified as {classification}")
        return requested, f"requested {requested} classified as non-avx"

    skipped: list[str] = []
    for version in candidates:
        classification = classify(sections[version])
        if classification == "avx":
            skipped.append(version)
            continue
        reason = f"selected newest non-avx FoundationDB 7.3 release {version}"
        if skipped:
            reason += f"; skipped AVX releases: {', '.join(skipped)}"
        return version, reason

    raise RuntimeError("All discovered FoundationDB 7.3 candidates are AVX-enabled")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-notes-url", default=RELEASE_NOTES_URL)
    parser.add_argument("--release-notes-file")
    parser.add_argument("--requested-version")
    parser.add_argument("--print-version", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    raw = open(args.release_notes_file, encoding="utf-8").read() if args.release_notes_file else fetch_text(args.release_notes_url)
    version, reason = select_version(raw, args.requested_version)

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

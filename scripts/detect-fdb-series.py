#!/usr/bin/env python3
"""Read the FoundationDB API series selected by a Stalwart Cargo manifest."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FEATURE_RE = re.compile(r'"fdb-(\d+)_(\d+)"')


def detect_series(manifest: str) -> str:
    matches = {f"{int(major)}.{int(minor)}" for major, minor in FEATURE_RE.findall(manifest)}
    if len(matches) != 1:
        found = ", ".join(sorted(matches)) or "none"
        raise RuntimeError(f"Expected exactly one fdb-X_Y feature, found: {found}")
    return matches.pop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-file", type=Path)
    args = parser.parse_args()

    manifest = (
        args.manifest_file.read_text(encoding="utf-8")
        if args.manifest_file
        else sys.stdin.read()
    )
    print(detect_series(manifest))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)

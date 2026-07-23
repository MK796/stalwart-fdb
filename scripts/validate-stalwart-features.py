#!/usr/bin/env python3
"""Validate that an upstream Stalwart manifest exposes required build features."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

REQUIRED_FEATURES = ("foundationdb", "s3", "zenoh", "enterprise")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    manifest = tomllib.loads(args.manifest.read_text(encoding="utf-8"))
    features = manifest.get("features")
    if not isinstance(features, dict):
        raise RuntimeError(f"{args.manifest} does not define a [features] table")

    missing = [feature for feature in REQUIRED_FEATURES if feature not in features]
    if missing:
        raise RuntimeError(f"Missing required Stalwart features: {', '.join(missing)}")

    print(" ".join(REQUIRED_FEATURES))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)

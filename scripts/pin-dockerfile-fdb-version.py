#!/usr/bin/env python3
"""Patch upstream Dockerfile.fdb to use one exact FoundationDB version."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


def patch_dockerfile(path: pathlib.Path, fdb_version: str) -> None:
    text = path.read_text(encoding="utf-8")
    if "ARG FDB_VERSION_RANGE" not in text:
        raise RuntimeError("Dockerfile does not contain ARG FDB_VERSION_RANGE")
    if "--arg RANGE" not in text:
        raise RuntimeError("Dockerfile does not contain expected RANGE jq argument")

    text = text.replace('ARG FDB_VERSION_RANGE="7.4"', f'ARG FDB_VERSION="{fdb_version}"')
    text = text.replace('--arg RANGE "${FDB_VERSION_RANGE}"', '--arg VERSION "${FDB_VERSION}"')
    text = text.replace('select(.tag_name | startswith($RANGE + "."))', 'select(.tag_name == $VERSION)')

    if "FDB_VERSION_RANGE" in text:
        raise RuntimeError("FDB_VERSION_RANGE still present after patch")
    if not re.search(r"select\(\.tag_name == \$VERSION\)", text):
        raise RuntimeError("Exact FDB_VERSION selection was not applied")

    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dockerfile", type=pathlib.Path)
    parser.add_argument("fdb_version")
    args = parser.parse_args()

    if not re.fullmatch(r"7\.3\.\d+", args.fdb_version):
        raise RuntimeError(f"Only FoundationDB 7.3.x versions are accepted, got {args.fdb_version}")

    patch_dockerfile(args.dockerfile, args.fdb_version)
    print(f"Pinned {args.dockerfile} to FoundationDB {args.fdb_version}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)

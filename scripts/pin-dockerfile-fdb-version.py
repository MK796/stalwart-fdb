#!/usr/bin/env python3
"""Patch upstream Dockerfile.fdb for an exact FDB version and matching Cargo features."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


def replace_once(text: str, old: str, new: str, description: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {description}, found {count}")
    return text.replace(old, new, 1)


def replace_regex_once(text: str, pattern: str, replacement: str, description: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {description}, found {count}")
    return updated


def patch_dockerfile(path: pathlib.Path, fdb_version: str) -> None:
    text = path.read_text(encoding="utf-8")

    build_matches = list(
        re.finditer(
            r'^RUN cargo build (?P<arguments>.+) --release$',
            text,
            flags=re.MULTILINE,
        )
    )
    if len(build_matches) != 1:
        raise RuntimeError(
            f"Expected exactly one final cargo build command, found {len(build_matches)}"
        )

    build_arguments = build_matches[0].group("arguments").strip()
    for required_argument in ("-p stalwart", "--no-default-features", "--features"):
        if required_argument not in build_arguments:
            raise RuntimeError(
                f"Final cargo build command is missing {required_argument!r}"
            )

    text = replace_regex_once(
        text,
        r'^ARG FDB_VERSION_RANGE="[^"]+"$',
        f'ARG FDB_VERSION="{fdb_version}"',
        "FDB_VERSION_RANGE argument",
    )
    text = replace_once(
        text,
        '--arg RANGE "${FDB_VERSION_RANGE}"',
        '--arg VERSION "${FDB_VERSION}"',
        "FoundationDB RANGE jq argument",
    )
    text = replace_once(
        text,
        'select(.tag_name | startswith($RANGE + "."))',
        'select(.tag_name == $VERSION)',
        "FoundationDB release range selector",
    )

    chef_command = "RUN cargo chef cook --release --recipe-path recipe.json"
    text = replace_once(
        text,
        chef_command,
        f"{chef_command} {build_arguments}",
        "cargo chef cook command",
    )

    if "FDB_VERSION_RANGE" in text:
        raise RuntimeError("FDB_VERSION_RANGE still present after patch")
    if not re.search(r"select\(\.tag_name == \$VERSION\)", text):
        raise RuntimeError("Exact FDB_VERSION selection was not applied")
    if f"{chef_command} {build_arguments}" not in text:
        raise RuntimeError("Cargo chef command does not match final build arguments")

    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dockerfile", type=pathlib.Path)
    parser.add_argument("fdb_version")
    args = parser.parse_args()

    if not re.fullmatch(r"7\.3\.\d+", args.fdb_version):
        raise RuntimeError(
            f"Only FoundationDB 7.3.x versions are accepted, got {args.fdb_version}"
        )

    patch_dockerfile(args.dockerfile, args.fdb_version)
    print(f"Pinned {args.dockerfile} to FoundationDB {args.fdb_version}")
    print("Aligned cargo chef cook with the final Stalwart build arguments")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)

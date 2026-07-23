#!/usr/bin/env bash
set -Eeuo pipefail

source_dir="${1:?Usage: build-stalwart.sh UPSTREAM_SOURCE_DIR}"
features="foundationdb s3 zenoh enterprise"

(
  cd "${source_dir}"
  cargo build \
    --locked \
    --release \
    --timings \
    -p stalwart \
    --no-default-features \
    --features "${features}"
) &
build_pid=$!

while kill -0 "${build_pid}" 2>/dev/null; do
  sleep 60
  if kill -0 "${build_pid}" 2>/dev/null; then
    printf 'Stalwart source build is still running at %s\n' "$(date -u +%FT%TZ)"
  fi
done

if wait "${build_pid}"; then
  echo "Stalwart source build completed."
else
  status=$?
  echo "Stalwart source build failed with exit code ${status}." >&2
  exit "${status}"
fi

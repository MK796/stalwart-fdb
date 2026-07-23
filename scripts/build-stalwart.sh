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
started_at=$(date +%s)

while kill -0 "${build_pid}" 2>/dev/null; do
  sleep 60
  if kill -0 "${build_pid}" 2>/dev/null; then
    now=$(date +%s)
    printf '\n=== Stalwart build heartbeat: %s, elapsed %dm %02ds ===\n' \
      "$(date -u +%FT%TZ)" \
      "$(((now - started_at) / 60))" \
      "$(((now - started_at) % 60))"
    printf '%s\n' 'Top compiler/linker processes:'
    ps -eo pid,ppid,etimes,pcpu,pmem,rss,stat,comm,args --sort=-pcpu |
      sed -n '1,12p'
    printf '%s\n' 'Runner memory:'
    free -h
    printf 'Cargo target size: '
    du -sh "${source_dir}/target" 2>/dev/null || echo 'not created yet'
    printf '%s\n\n' '=== End build heartbeat ==='
  fi
done

if wait "${build_pid}"; then
  echo "Stalwart source build completed."
else
  status=$?
  echo "Stalwart source build failed with exit code ${status}." >&2
  exit "${status}"
fi

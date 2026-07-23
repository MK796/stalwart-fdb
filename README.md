# stalwart-fdb

Build upstream Stalwart Docker images with FoundationDB client support.

This repository does not vendor or fork Stalwart source code. The GitHub Actions workflow checks upstream `stalwartlabs/stalwart` tags, checks FoundationDB 7.3 release notes for the newest non-AVX client release, builds upstream Stalwart with upstream `Dockerfile.fdb`, and publishes the resulting image to GHCR.

## Image

```text
ghcr.io/mk796/stalwart-fdb
```

Example tags:

```text
v0.16.14-fdb7.3.78
v0.16-fdb7.3.78
latest-fdb7.3.78
latest
```

`latest` means the newest stable upstream Stalwart tag built with the newest automatically selected non-AVX FoundationDB 7.3 client release.

## AVX Safety

FoundationDB occasionally publishes AVX-enabled patch releases. Those builds do not run on older CPUs such as Intel Xeon X5690.

The workflow fails closed:

- AVX-marked FoundationDB releases are skipped.
- Ambiguous release-note sections fail the workflow.
- The selected FDB version is included in every versioned image tag.

## Manual Run

Use GitHub Actions -> `Build Stalwart FDB Image` -> `Run workflow`.

Optional inputs:

- `stalwart_version`: exact upstream Stalwart tag, for example `v0.16.14`
- `fdb_version`: exact FoundationDB version override, only accepted if release notes classify it as non-AVX

## Compose Example

```yaml
services:
  ms-stalwart:
    image: ghcr.io/mk796/stalwart-fdb:latest
```

For reproducible deployments prefer a pinned tag:

```yaml
image: ghcr.io/mk796/stalwart-fdb:v0.16.14-fdb7.3.78
```

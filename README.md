# stalwart-fdb

Packages the official FoundationDB-enabled Stalwart release binary as a small Docker image.

This repository does **not** compile, patch, or fork Stalwart. Every six hours, GitHub Actions:

1. finds the newest stable Stalwart release containing the Linux x86_64 FoundationDB binary;
2. verifies that binary with Stalwart's GitHub build attestation;
3. reads the release tag's Cargo manifest to determine the required FDB API series;
4. selects the newest release in that series whose official FoundationDB release notes explicitly say it is non-AVX;
5. verifies `libfdb_c.so` against Apple's published SHA-256 checksum and packages both files using Stalwart's upstream runtime layout.

## Image

```text
ghcr.io/mk796/stalwart-fdb
```

Example tags for Stalwart `v0.16.14`, which requires FDB API `7.4`:

```text
v0.16.14-fdb7.4.4
v0.16-fdb7.4.4
latest-fdb7.4.4
latest
```

The immutable full tag is always published. Moving `vMAJOR.MINOR`, `latest-fdbVERSION`, and `latest` aliases are updated only for the newest automatically selected combination.

The image currently targets `linux/amd64`.

## FoundationDB Cluster Version

Use the FDB version encoded in the image tag for the FoundationDB servers as well. For example:

```yaml
image: foundationdb/foundationdb:7.4.4
```

FoundationDB `7.4.4` is a pre-release, but its official release notes explicitly state that it was compiled **without AVX instructions**. Newer AVX-enabled patches such as `7.4.5` and `7.4.6` are skipped automatically.

## Manual Run

Use GitHub Actions -> `Build Stalwart FDB Image` -> `Run workflow`.

Optional inputs:

- `stalwart_version`: exact stable upstream tag containing the FDB binary
- `fdb_version`: exact release from that Stalwart tag's required API series; accepted only when the official release notes explicitly classify it as non-AVX

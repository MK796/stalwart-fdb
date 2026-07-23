# stalwart-fdb

Builds the unmodified stable Stalwart source with FoundationDB, S3 and embedded
Zenoh peer-to-peer coordination, then publishes a multi-platform Docker image.

Every six hours, GitHub Actions:

1. selects the newest stable Stalwart release and resolves its exact commit;
2. verifies that the release exposes the `foundationdb`, `s3`, `zenoh` and
   `enterprise` Cargo features;
3. detects the FoundationDB API series required by that Stalwart release;
4. selects the newest FoundationDB release in that series whose official
   release notes explicitly classify the x86_64 build as non-AVX;
5. verifies the official FoundationDB headers and client libraries for x86_64
   and aarch64 using Apple's SHA-256 files;
6. compiles Stalwart natively on x86_64 and aarch64 GitHub runners;
7. tests both platform images before publishing one multi-platform manifest.

The upstream Stalwart source is not patched or forked.

## Image

```text
ghcr.io/mk796/stalwart-fdb
```

Example tags for Stalwart `v0.16.14` with FoundationDB `7.4.4`:

```text
v0.16.14-fdb7.4.4-p2p
v0.16-fdb7.4.4-p2p
latest-fdb7.4.4-p2p
latest
```

The complete version tag is immutable. Moving aliases are updated only for the
newest automatically selected Stalwart and FoundationDB combination. Existing
pre-P2P tags are not overwritten.

Published platforms:

```text
linux/amd64
linux/arm64
```

Each platform image contains the matching `libfdb_c.so` and the same Stalwart
feature set:

```text
foundationdb,s3,zenoh,enterprise
```

Zenoh runs inside each Stalwart process. A peer-to-peer deployment therefore
does not need a separate Zenoh, NATS, Redis or Kafka service.

## FoundationDB Cluster Version

Use the FDB version encoded in the image tag for the FoundationDB servers too:

```yaml
image: foundationdb/foundationdb:7.4.4
```

The non-AVX requirement applies to x86_64. Both platform images use client
artifacts from the same FoundationDB release.

## Manual Run

Use GitHub Actions -> `Build Stalwart FDB-P2P Image` -> `Run workflow`.

Optional inputs:

- `stalwart_version`: exact stable upstream tag
- `fdb_version`: exact release from the required FDB API series; accepted only
  when the official release notes classify its x86_64 build as non-AVX

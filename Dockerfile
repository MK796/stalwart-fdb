# syntax=docker/dockerfile:1

FROM debian:trixie-slim

ARG STALWART_VERSION
ARG STALWART_COMMIT
ARG STALWART_FEATURES
ARG FDB_VERSION
ARG TARGETARCH

LABEL org.opencontainers.image.title="stalwart-fdb" \
      org.opencontainers.image.description="Stalwart with FoundationDB, S3 and embedded Zenoh P2P coordination" \
      org.opencontainers.image.source="https://github.com/MK796/stalwart-fdb" \
      org.opencontainers.image.vendor="MK796" \
      org.opencontainers.image.version="${STALWART_VERSION}-fdb${FDB_VERSION}-p2p" \
      org.mk796.stalwart.upstream="${STALWART_VERSION}" \
      org.mk796.stalwart.commit="${STALWART_COMMIT}" \
      org.mk796.stalwart.features="${STALWART_FEATURES}" \
      org.mk796.foundationdb.version="${FDB_VERSION}" \
      org.mk796.foundationdb.avx="disabled" \
      org.mk796.image.architecture="${TARGETARCH}"

COPY --chmod=0755 dist/stalwart /usr/local/bin/stalwart
COPY --chmod=0644 dist/libfdb_c.so /usr/lib/libfdb_c.so

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -yq --no-install-recommends ca-certificates curl libcap2-bin && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -r -g 2000 stalwart && \
    useradd -r -u 2000 -g 2000 -s /usr/sbin/nologin -M stalwart && \
    mkdir -p /etc/stalwart /var/lib/stalwart && \
    chown stalwart:stalwart /etc/stalwart /var/lib/stalwart && \
    setcap 'cap_net_bind_service=+ep' /usr/local/bin/stalwart

USER stalwart
WORKDIR /var/lib/stalwart
VOLUME ["/etc/stalwart", "/var/lib/stalwart"]
EXPOSE 443 25 110 587 465 143 993 995 4190 8080
ENV STALWART_HEALTHCHECK_URL=https://127.0.0.1:443/healthz/live
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsSk -H "X-Forwarded-For: 127.0.0.1" "$STALWART_HEALTHCHECK_URL" || curl -fsS -H "X-Forwarded-For: 127.0.0.1" http://127.0.0.1:8080/healthz/live || exit 1
ENTRYPOINT ["/usr/local/bin/stalwart"]
CMD ["--config", "/etc/stalwart/config.json"]

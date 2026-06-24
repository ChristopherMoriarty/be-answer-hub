FROM minio/mc:RELEASE.2025-04-16T18-13-26Z AS mc

FROM minio/minio:RELEASE.2025-04-22T22-12-26Z

COPY --from=mc /usr/bin/mc /usr/bin/mc
COPY scripts/minio-entrypoint.sh /usr/local/bin/minio-entrypoint.sh
RUN chmod +x /usr/local/bin/minio-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/minio-entrypoint.sh"]

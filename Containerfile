FROM docker.io/library/python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /platform
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Bake the DuckDB extensions into the image so a run never downloads anything
RUN d=/root/.duckdb/extensions/v2.0.1/linux_amd64 && mkdir -p $d && \
    for e in httpfs iceberg avro; do \
      curl -fsS https://extensions.duckdb.org/v2.0.1/linux_amd64/$e.duckdb_extension.gz \
        | gunzip > $d/$e.duckdb_extension; \
    done
COPY pipeline pipeline
COPY transform transform
CMD ["pipeline/job.sh"]

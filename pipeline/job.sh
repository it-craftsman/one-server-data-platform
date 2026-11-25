#!/usr/bin/env bash
# Runs inside the pipeline container: load new raw files, rebuild marts and the page.
set -euo pipefail
cd "$PLATFORM_ROOT"
mkdir -p data/serving

for month in "$@"; do
  raw="data/raw/yellow_tripdata_${month}.parquet"
  marker="data/raw/.loaded-${month}"
  if [[ -f "$raw" && ( ! -f "$marker" || "$raw" -nt "$marker" ) ]]; then
    python pipeline/ingest.py "$month"
    touch "$marker"
  fi
done

metadata=$(python -c "
from pipeline.ingest import catalog
print(catalog().load_table('raw.yellow_trips').metadata_location)")

dbt build --project-dir transform --profiles-dir transform \
  --vars "{trips_metadata: '$metadata'}"
python pipeline/report.py

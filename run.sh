#!/usr/bin/env bash
# Entry point for cron: fetch raw files on the host, then run the job container.
set -euo pipefail
cd "$(dirname "$0")"

months=("$@")
if [[ ${#months[@]} -eq 0 ]]; then
  # TLC publishes with a lag of a few months, so look back four
  for i in 1 2 3 4; do
    months+=("$(date -d "$(date +%Y-%m-01) -$i month" +%Y-%m)")
  done
fi

for month in "${months[@]}"; do
  pipeline/fetch.sh "$month"
done

podman-compose --profile jobs run --rm -T --no-deps pipeline \
  pipeline/job.sh "${months[@]}"

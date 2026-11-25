#!/usr/bin/env bash
# Download one month of TLC yellow taxi data; resume on errors, refuse truncated files.
set -euo pipefail
month="$1"
dir="$(dirname "$0")/../data/raw"
url="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_${month}.parquet"
out="$dir/yellow_tripdata_${month}.parquet"
mkdir -p "$dir"

headers=$(curl -sI "$url")
if ! grep -q "^HTTP/[0-9.]* 200" <<<"$headers"; then
  echo "$month: not published yet" >&2
  exit 0
fi
expected=$(awk 'tolower($1)=="content-length:" {print $2}' <<<"$headers" | tr -d '\r')
[[ -f "$out" && $(stat -c %s "$out") == "$expected" ]] && exit 0

curl -sS --fail --retry 8 --retry-all-errors --retry-delay 5 -C - -o "$out" "$url"
if [[ $(stat -c %s "$out") != "$expected" ]]; then
  echo "$month: truncated download" >&2
  exit 1
fi

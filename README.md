# One-server data platform

A complete, small data platform that runs on one machine: Polars loads raw files into Apache Iceberg tables, dbt on DuckDB builds the marts, and a static page shows the dashboard. It uses a year of NYC yellow taxi trips as test data.

This is the code behind the article [LINK: Medium article].

## What's inside

- `compose.yaml` with three services: PostgreSQL 17 as the Iceberg catalog, Caddy serving the dashboard page, and the pipeline job (behind the `jobs` profile).
- `Containerfile` for the pipeline image. The DuckDB extensions are downloaded at build time, so a run downloads nothing.
- `run.sh`, the entry point for cron. It fetches raw files on the host and then starts the job container.
- `pipeline/fetch.sh` downloads one month from the TLC host, resumes broken transfers and fails on truncated files.
- `pipeline/ingest.py` loads one month into the Iceberg table `raw.yellow_trips`, partitioned by month. Rerunning a month replaces that month.
- `pipeline/job.sh` runs inside the container: ingest new months, `dbt build`, render the page.
- `transform/` is the dbt project (one staging view, four tables, six tests).
- `pipeline/report.py` writes `site/index.html` with three Vega-Lite charts.

## Prerequisites

- Linux with Podman and podman-compose (tested with Podman 5.4.2 and podman-compose 1.3.0)
- `curl`, `flock` and GNU `date` on the host
- About 2 GB of free memory and a few GB of disk for one year of data

## Quick start

```bash
git clone https://github.com/it-craftsman/one-server-data-platform.git
cd one-server-data-platform
cp .env.example .env            # then set CATALOG_PASSWORD to a real value
podman-compose up -d catalog site
podman-compose --profile jobs build pipeline
./run.sh 2026-06 2026-07        # load two months
```

Open http://localhost:8080 for the dashboard.

`./run.sh` without arguments looks back four months from today. That is what the nightly cron job uses.

## How the monthly download works

TLC publishes each month with a delay of about two months. For each month, `fetch.sh` sends a HEAD request first. A month that isn't published yet is skipped with a message. A file that is already complete (same size as the `Content-Length` header) is not downloaded again. Broken transfers resume with `curl -C -`, and a size mismatch at the end fails the run.

Inside the container, a marker file per month (`data/raw/.loaded-YYYY-MM`) decides whether a month gets loaded again. A month is loaded when the marker is missing or the raw file is newer than the marker.

## Scheduling

Copy `scripts/crontab.example` into your crontab and adjust the path:

```bash
15 3 * * * cd /opt/platform && flock -n /tmp/platform.lock ./run.sh >> /var/log/platform.log 2>&1
```

To test a schedule without touching the system crontab, you can use [supercronic](https://github.com/aptible/supercronic). Download the binary for your platform from its releases page, make it executable and run `supercronic scripts/crontab.example` in the foreground.

## Measured numbers

Measured on a shared virtual machine with 8 vCPUs, 15 GiB of RAM (about 2 GiB free at the time) and a virtual disk, with DuckDB capped at 1.5 GB. Your hardware will give different numbers.

- 12 months (August 2025 to July 2026), 47,106,693 rows, 770 MB of raw Parquet
- Full backfill from raw files to the finished page: 35.4 seconds
- Loading one month: 1.2 to 1.8 seconds
- `dbt build`: 4.18 seconds
- Nightly run without new data: 10.3 to 13.0 seconds
- Revenue per month straight from the Iceberg table: 0.19 seconds

## Known limits

- A DuckDB file accepts one read-write process or several read-only processes, not both. A BI tool holding the marts open makes the nightly build fail. The static page avoids this.
- One machine, no failover. Back up with `pg_dump` of the catalog plus a copy of `data/warehouse`. The Iceberg metadata stores absolute paths, so restore to the same path.
- No access control beyond file permissions. No table roles, no column masking, no query audit.
- Memory limits the size before the disk does. A median per day and pickup zone ran out of memory at 1.5 GB, which is why the daily table uses an average.
- PyIceberg 0.12.0 only expires snapshots. Old data files stay on disk, and nothing compacts small files.
- The SQL catalog works for one engine. Once Trino or Spark need the same tables, move to a REST catalog such as Apache Polaris.

## Data

NYC Taxi and Limousine Commission trip record data: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page. `transform/seeds/taxi_zone_lookup.csv` is the TLC taxi zone lookup table.

## License

MIT, see `LICENSE`.

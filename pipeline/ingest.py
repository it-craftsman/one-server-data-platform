"""Load one month of NYC yellow taxi trips into an Iceberg table.

Usage: python ingest.py 2026-07
Re-running a month replaces that month and nothing else.
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import polars as pl
from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.expressions import And, GreaterThanOrEqual, LessThan
from pyiceberg.transforms import MonthTransform

ROOT = Path(os.environ["PLATFORM_ROOT"])
RAW = ROOT / "data" / "raw"
WAREHOUSE = ROOT / "data" / "warehouse"


def catalog() -> SqlCatalog:
    WAREHOUSE.mkdir(parents=True, exist_ok=True)
    return SqlCatalog(
        "platform",
        uri=os.environ["CATALOG_URI"],
        warehouse=f"file://{WAREHOUSE}",
    )


def month_bounds(month: str) -> tuple[datetime, datetime]:
    start = datetime.fromisoformat(f"{month}-01")
    end = datetime(start.year + start.month // 12, start.month % 12 + 1, 1)
    return start, end


def read_month(month: str, start: datetime, end: datetime) -> pl.DataFrame:
    return (
        pl.scan_parquet(RAW / f"yellow_tripdata_{month}.parquet")
        .select(
            pl.col("VendorID").cast(pl.Int32).alias("vendor_id"),
            pl.col("tpep_pickup_datetime").alias("pickup_at"),
            pl.col("tpep_dropoff_datetime").alias("dropoff_at"),
            pl.col("passenger_count").cast(pl.Int32),
            pl.col("trip_distance").cast(pl.Float64),
            pl.col("PULocationID").cast(pl.Int32).alias("pickup_zone_id"),
            pl.col("DOLocationID").cast(pl.Int32).alias("dropoff_zone_id"),
            pl.col("payment_type").cast(pl.Int32),
            pl.col("fare_amount").cast(pl.Float64),
            pl.col("tip_amount").cast(pl.Float64),
            pl.col("total_amount").cast(pl.Float64),
            pl.col("cbd_congestion_fee").cast(pl.Float64),
        )
        # every file has a few trips dated outside its month; keep the month only
        .filter(pl.col("pickup_at").is_between(start, end, closed="left"))
        .collect()
    )


def main(month: str) -> None:
    t0 = time.perf_counter()
    start, end = month_bounds(month)
    trips = read_month(month, start, end).to_arrow()

    cat = catalog()
    cat.create_namespace_if_not_exists("raw")
    if not cat.table_exists("raw.yellow_trips"):
        table = cat.create_table("raw.yellow_trips", schema=trips.schema)
        with table.update_spec() as spec:
            spec.add_field("pickup_at", MonthTransform(), "pickup_month")
    table = cat.load_table("raw.yellow_trips")

    # delete the month and append it again in one transaction
    table.overwrite(
        trips,
        overwrite_filter=And(
            GreaterThanOrEqual("pickup_at", start.isoformat()),
            LessThan("pickup_at", end.isoformat()),
        ),
    )
    print(f"{month}: {trips.num_rows:,} rows in {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1])

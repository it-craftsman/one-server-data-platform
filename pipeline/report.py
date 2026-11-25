"""Render the marts into one static HTML page. Any web server can serve it."""
import json
import os
from pathlib import Path

import duckdb

ROOT = Path(os.environ["PLATFORM_ROOT"])
OUT = ROOT / "site" / "index.html"

con = duckdb.connect(str(ROOT / "data" / "serving" / "marts.duckdb"), read_only=True)


def rows(sql: str) -> list[dict]:
    cur = con.execute(sql)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


charts = {
    "Trips per month": (
        rows("select strftime(month, '%Y-%m') as month, trips from mart_monthly"),
        {"mark": "bar", "encoding": {
            "x": {"field": "month", "type": "ordinal"},
            "y": {"field": "trips", "type": "quantitative"}}},
    ),
    "Trips by hour and weekday": (
        rows("select weekday, hour, trips from mart_hourly"),
        {"mark": "rect", "encoding": {
            "x": {"field": "hour", "type": "ordinal"},
            "y": {"field": "weekday", "type": "ordinal"},
            "color": {"field": "trips", "type": "quantitative"}}},
    ),
    "Top 10 pickup zones by revenue": (
        rows("""select zone, sum(revenue) as revenue from fct_daily_zone
                where zone is not null group by zone order by revenue desc limit 10"""),
        {"mark": "bar", "encoding": {
            "y": {"field": "zone", "type": "nominal", "sort": "-x"},
            "x": {"field": "revenue", "type": "quantitative"}}},
    ),
}

blocks = []
for i, (title, (data, spec)) in enumerate(charts.items()):
    spec = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": title, "width": 640, "data": {"values": data}, **spec}
    blocks.append(f'<div id="c{i}"></div><script>vegaEmbed("#c{i}", {json.dumps(spec, default=str)});</script>')

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(
    "<!doctype html><meta charset='utf-8'><title>NYC taxi</title>"
    "<script src='https://cdn.jsdelivr.net/npm/vega@5'></script>"
    "<script src='https://cdn.jsdelivr.net/npm/vega-lite@5'></script>"
    "<script src='https://cdn.jsdelivr.net/npm/vega-embed@6'></script>"
    + "".join(blocks)
)
print(f"wrote {OUT}")

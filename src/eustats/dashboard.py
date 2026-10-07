"""Static HTML dashboard: one NUTS 2 map per indicator and national time series."""

from __future__ import annotations

import html
import json
from pathlib import Path

import duckdb
import plotly.express as px

# Member States shown in the time-series charts next to the EU27 aggregate.
FOCUS_COUNTRIES = ("IT", "DE", "FR", "ES", "PL")


def build_dashboard(warehouse: Path, geojson_path: Path) -> str:
    geojson = json.loads(geojson_path.read_text(encoding="utf-8"))
    with duckdb.connect(str(warehouse), read_only=True) as con:
        indicators = con.execute(
            "select indicator_id, label, unit, dataset_code "
            "from staging.stg_config__indicators order by indicator_id"
        ).fetchall()
        latest = con.execute("select * from marts.mart_nuts2_latest").df()
        series = con.execute(
            "select f.indicator_id, f.geo, coalesce(g.geo_label, f.geo) as geo_label, "
            "f.time_period, f.obs_value "
            "from marts.fct_indicator_values as f "
            "inner join marts.dim_geo as g using (geo) "
            "where f.geo_level = 'eu_aggregate' or f.geo in ?",
            [list(FOCUS_COUNTRIES)],
        ).df()

    sections = []
    for index, (indicator_id, label, unit, dataset_code) in enumerate(indicators):
        regional = latest[latest["indicator_id"] == indicator_id]
        year = int(regional["time_period"].max())
        current = regional[regional["time_period"] == year]
        lagging = len(regional) - len(current)
        figure_map = px.choropleth(
            current,
            geojson=geojson,
            featureidkey="properties.NUTS_ID",
            locations="geo",
            color="obs_value",
            hover_name="geo_label",
            hover_data={"geo": True, "obs_value": ":,.1f", "obs_flag": True},
            color_continuous_scale="Viridis",
            # Clip the colour scale to the 5th-95th percentiles so a few extreme
            # regions (e.g. Luxembourg, Dublin) do not flatten the rest of the map.
            range_color=tuple(current["obs_value"].quantile([0.05, 0.95])),
            labels={"obs_value": ""},
        )
        # Frame continental Europe; outermost regions stay in the data but off-screen.
        figure_map.update_geos(
            visible=False,
            projection_type="mercator",
            lataxis_range=[34, 71],
            lonaxis_range=[-12, 35],
        )
        figure_map.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, height=520)

        trend = series[series["indicator_id"] == indicator_id].sort_values("time_period")
        figure_trend = px.line(
            trend,
            x="time_period",
            y="obs_value",
            color="geo_label",
            markers=True,
            labels={"time_period": "Year", "obs_value": unit, "geo_label": ""},
        )
        figure_trend.update_layout(margin={"l": 0, "r": 0, "t": 10, "b": 0}, height=360)

        note = f" {lagging} regions have no {year} value yet and are not shown." if lagging else ""
        sections.append(
            f"<section><h2>{html.escape(label)}</h2>"
            f"<p class='meta'>{html.escape(unit)} · NUTS 2 regions, {year} · "
            f"source: Eurostat <code>{dataset_code}</code>. Colour scale clipped to the "
            f"5th-95th percentiles; outermost regions are outside the frame."
            f"{html.escape(note)}</p>"
            # The first chart loads plotly.js (version matched to the Python package).
            + figure_map.to_html(full_html=False, include_plotlyjs="cdn" if index == 0 else False)
            + "<h3>EU27 and selected Member States</h3>"
            + figure_trend.to_html(full_html=False, include_plotlyjs=False)
            + "</section>"
        )

    return PAGE_TEMPLATE.format(sections="\n".join(sections))


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EU regional statistics</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 1100px; margin: 0 auto;
         padding: 16px; color: #1f2933; background: #ffffff; }}
  h1 {{ margin-bottom: 4px; }}
  section {{ border-top: 1px solid #d9e2ec; padding-top: 16px; margin-top: 24px; }}
  .meta {{ color: #52606d; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>EU regional statistics</h1>
<p class="meta">Built by eu-stats-pipeline from Eurostat data. See the data quality report
and the methodology note in the repository for validation results and caveats.</p>
{sections}
</body>
</html>
"""


def write_dashboard(warehouse: Path, geojson_path: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_dashboard(warehouse, geojson_path), encoding="utf-8")

"""Quality report structured along the ESS quality dimensions.

Inputs are the warehouse built by dbt and dbt's run_results.json, so the report
always describes the exact data and validation run that produced the outputs.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pandas as pd

DATABROWSER_URL = "https://ec.europa.eu/eurostat/databrowser/view/{code}/default/table?lang=en"


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_None._\n"
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    divider = "|" + "|".join("---" for _ in frame.columns) + "|"
    rows = [
        "| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |"
        for row in frame.itertuples(index=False)
    ]
    return "\n".join([header, divider, *rows]) + "\n"


def _test_results(run_results_path: Path) -> pd.DataFrame:
    results = json.loads(run_results_path.read_text(encoding="utf-8"))["results"]
    rows = [
        {
            "check": r["unique_id"].split(".")[2],
            "status": r["status"],
            "rows_flagged": r.get("failures") or 0,
        }
        for r in results
        if r["unique_id"].startswith("test.")
    ]
    frame = pd.DataFrame(rows)
    status_order = {"error": 0, "fail": 1, "warn": 2, "pass": 3}
    frame["order"] = frame["status"].map(status_order)
    return frame.sort_values(["order", "check"]).drop(columns="order").reset_index(drop=True)


def _query(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.execute(sql).df()


def build_report(warehouse: Path, run_results_path: Path) -> str:
    tests = _test_results(run_results_path)
    with duckdb.connect(str(warehouse), read_only=True) as con:
        sources = _query(
            con,
            """
            select m.file, m.dataset_code, m.rows, left(m.sha256, 12) as sha256_prefix,
                   m.retrieved_at, m.offline_fixture
            from raw.manifest as m order by m.file
            """,
        )
        indicators = _query(
            con,
            """
            select c.indicator_id, c.dataset_code, c.label, c.unit,
                   min(f.time_period) as first_year, max(f.time_period) as last_year,
                   count(distinct f.geo) filter (where f.geo_level = 'country') as countries,
                   count(distinct f.geo) filter (
                       where f.geo_level = 'nuts2' and f.in_gisco_nuts2024
                   ) as nuts2_regions
            from marts.fct_indicator_values as f
            inner join staging.stg_config__indicators as c using (indicator_id)
            group by all order by c.indicator_id
            """,
        )
        timeliness = _query(
            con,
            """
            select indicator_id,
                   max(time_period) as latest_reference_year,
                   strftime(max(source_last_update), '%Y-%m-%d') as eurostat_last_update,
                   year(current_date) - max(time_period) as years_since_reference
            from marts.fct_indicator_values
            where obs_value is not null
            group by indicator_id order by indicator_id
            """,
        )
        accuracy = _query(
            con,
            """
            select indicator_id,
                   count(*) as observations,
                   round(100.0 * count(*) filter (where obs_value is null) / count(*), 1)
                       as pct_missing,
                   round(100.0 * count(*) filter (where is_estimated) / count(*), 1)
                       as pct_estimated,
                   round(100.0 * count(*) filter (where is_provisional) / count(*), 1)
                       as pct_provisional,
                   round(100.0 * count(*) filter (where is_low_reliability) / count(*), 1)
                       as pct_low_reliability,
                   round(100.0 * count(*) filter (where has_break) / count(*), 1)
                       as pct_series_break
            from marts.fct_indicator_values group by indicator_id order by indicator_id
            """,
        )
        completeness = _query(
            con,
            """
            with eu_regions as (
                select n.nuts_id from staging.stg_gisco__nuts2 as n
                inner join reference.eu27_countries as eu on eu.country_code = n.country_code
            ),
            latest as (
                select indicator_id, max(time_period) as latest_year
                from marts.fct_indicator_values
                where geo_level = 'nuts2' and obs_value is not null
                group by indicator_id
            )
            select l.indicator_id, l.latest_year,
                   count(distinct f.geo) as regions_with_value,
                   (select count(*) from eu_regions) as eu_nuts2_regions,
                   round(100.0 * count(distinct f.geo) / (select count(*) from eu_regions), 1)
                       as pct_complete
            from latest as l
            left join marts.fct_indicator_values as f
                on f.indicator_id = l.indicator_id and f.time_period = l.latest_year
               and f.obs_value is not null
               and f.geo in (select nuts_id from eu_regions)
            group by l.indicator_id, l.latest_year order by l.indicator_id
            """,
        )
        nuts_versions = _query(
            con, "select * from quality.assert_nuts2_codes_in_gisco_2024 order by geo"
        )
        plausibility = _query(
            con,
            """
            select indicator_id, geo, previous_period || '-' || time_period as years,
                   previous_value, obs_value,
                   case when indicator_id = 'unemployment_rate'
                        then printf('%+.1f pp', change)
                        else printf('%+.1f %%', 100 * change) end as change,
                   coalesce(obs_flag, '') as flag
            from quality.assert_no_extreme_year_on_year_changes
            order by indicator_id, geo, years
            """,
        )
        coherence_failures = _query(
            con, "select * from quality.assert_regional_population_matches_national"
        )

    failed = tests[tests["status"].isin(["fail", "error"])]
    warned = tests[tests["status"] == "warn"]
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    sources["dataset_code"] = sources["dataset_code"].map(
        lambda code: f"[{code}]({DATABROWSER_URL.format(code=code)})" if ":" not in code else code
    )

    lines = [
        "# Data quality report",
        "",
        f"Generated {generated_at} by `eustats report`. "
        "Structure follows the quality dimensions of the European Statistical System (ESS).",
        "",
        f"**Validation summary:** {len(tests)} checks, {len(failed)} failed, "
        f"{len(warned)} warnings for manual review.",
        "",
        "## Sources and lineage",
        "",
        "Every raw file is recorded in `data/raw/manifest.json` with its source URL, "
        "retrieval time and SHA-256 checksum.",
        "",
        _markdown_table(sources),
        "## 1. Relevance",
        "",
        "Indicators, coverage of the EU27 Member States and NUTS 2024 level-2 regions.",
        "",
        _markdown_table(indicators),
        "## 2. Accuracy and reliability",
        "",
        "Share of observations by Eurostat status flag (combined flags count for each component).",
        "",
        _markdown_table(accuracy),
        "Completeness of the latest year with regional data, against all NUTS 2024 level-2 "
        "regions of the EU27:",
        "",
        _markdown_table(completeness),
        "Validation checks (dbt tests):",
        "",
        _markdown_table(tests),
        "## 3. Timeliness and punctuality",
        "",
        _markdown_table(timeliness),
        "Regional accounts and labour-market statistics are published with a lag of one to "
        "two years after the reference year.",
        "",
        "## 4. Coherence and comparability",
        "",
        "**Regional vs national population.** The sum of NUTS 2024 level-2 populations is "
        "checked against the national total for every country and year.",
        "",
        "All countries and years are within tolerance.\n"
        if coherence_failures.empty
        else _markdown_table(coherence_failures),
        "**NUTS versions.** Regions with recent data but no NUTS 2024 geometry. These are "
        "codes from an older NUTS version: they are kept in `fct_indicator_values` but "
        "excluded from maps and from the coherence check, to avoid double counting.",
        "",
        _markdown_table(nuts_versions),
        "## 5. Plausibility review",
        "",
        "Year-on-year changes above the review thresholds (population ±5 %, GDP per "
        "inhabitant ±25 %, unemployment ±5 percentage points). A flag `b` marks a break "
        "in series declared by Eurostat; unflagged rows should be checked against the "
        "source metadata.",
        "",
        _markdown_table(plausibility),
        "## 6. Accessibility and clarity",
        "",
        "- Source tables: Eurostat data browser links in the lineage table above.",
        "- Column definitions: [data dictionary](data-dictionary.md).",
        "- Methods: [methodology note](methodology.md).",
        "",
    ]
    return "\n".join(lines)


def write_report(warehouse: Path, run_results_path: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(warehouse, run_results_path), encoding="utf-8")

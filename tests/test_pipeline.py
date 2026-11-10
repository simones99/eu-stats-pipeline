"""End-to-end run on the offline fixtures (Italy, the Netherlands, Portugal, Poland).

The fixtures are a subset of real Eurostat data chosen because they exercise the
checks: the Netherlands and Portugal carry NUTS 2021 codes next to NUTS 2024 ones,
and Poland has a declared break in series after the 2021 census.
"""

import re

import duckdb
import pytest

from eustats.cli import Paths, main


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    out = tmp_path_factory.mktemp("run")
    assert main(["run", "--offline", "--out", str(out)]) == 0
    return Paths(out)


def test_all_outputs_are_written(run):
    for path in (
        run.docs / "quality-report.md",
        run.docs / "data-dictionary.md",
        run.site / "index.html",
        run.raw_dir / "manifest.json",
    ):
        assert path.stat().st_size > 0


def test_non_regional_units_are_excluded(run):
    with duckdb.connect(str(run.warehouse), read_only=True) as con:
        leaked = con.execute(
            "select count(*) from marts.fct_indicator_values "
            "where geo_level in ('nuts1', 'nuts2') and (geo like '__Z%' or geo like '__X%')"
        ).fetchone()[0]
    assert leaked == 0


def test_older_nuts_codes_are_kept_but_flagged(run):
    with duckdb.connect(str(run.warehouse), read_only=True) as con:
        old_codes = {
            row[0]
            for row in con.execute(
                "select distinct geo from marts.fct_indicator_values "
                "where geo_level = 'nuts2' and not in_gisco_nuts2024"
            ).fetchall()
        }
        mapped = con.execute(
            "select count(*) from marts.mart_nuts2_latest where geo in ('PT17', 'NL33')"
        ).fetchone()[0]
    assert {"PT17", "NL33"} <= old_codes
    assert mapped == 0


def test_report_lists_coherence_result_and_census_break(run):
    report = (run.docs / "quality-report.md").read_text()
    assert "0 failed" in report
    assert "All countries and years are within tolerance." in report
    assert "| population | PL91 | 2020-2021 |" in report


def test_new_indicators_reach_the_regional_mart(run):
    with duckdb.connect(str(run.warehouse), read_only=True) as con:
        mapped = {
            row[0]
            for row in con.execute(
                "select indicator_id from marts.mart_nuts2_latest where geo = 'ITC4'"
            ).fetchall()
        }
    assert {"gdp_pps_pct_eu27", "population_density"} <= mapped


def test_nuts3_units_are_classified_and_left_out_of_the_fact_table(run):
    with duckdb.connect(str(run.warehouse), read_only=True) as con:
        level = con.execute("select geo_level from marts.dim_geo where geo = 'ITC4C'").fetchone()
        in_fact = con.execute(
            "select count(*) from marts.fct_indicator_values where length(geo) = 5"
        ).fetchone()[0]
    assert level == ("nuts3",)
    assert in_fact == 0


def test_dashboard_has_one_section_per_dashboard_indicator(run):
    page = (run.site / "index.html").read_text()
    assert re.findall(r"<h2>(.*?)</h2>", page) == [
        "GDP per inhabitant, EU27 = 100",
        "Population density",
        "Unemployment rate, 15-74 years",
    ]


def test_dashboard_sections_link_to_the_eurostat_dataset(run):
    page = (run.site / "index.html").read_text()
    assert "https://ec.europa.eu/eurostat/databrowser/view/demo_r_d3dens/default/table" in page


def test_dashboard_footer_gives_sources_and_copyright(run):
    footer = re.search(r"<footer>.*</footer>", (run.site / "index.html").read_text(), re.S)
    assert footer, "the page has no footer"
    text = footer.group(0)
    assert "© European Union" in text
    assert "© EuroGeographics for the administrative boundaries" in text
    assert "https://github.com/simones99/eu-stats-pipeline" in text
    assert "docs/quality-report.md" in text
    assert "docs/methodology.md" in text
    assert re.search(r"Data retrieved on \d{4}-\d{2}-\d{2}", text)


def test_density_map_is_described_as_log_scaled(run):
    page = (run.site / "index.html").read_text()
    density = page.split("<h2>Population density</h2>")[1].split("</p>")[0]
    assert "Logarithmic colour scale" in density

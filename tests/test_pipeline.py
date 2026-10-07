"""End-to-end run on the offline fixtures (Italy, the Netherlands, Portugal, Poland).

The fixtures are a subset of real Eurostat data chosen because they exercise the
checks: the Netherlands and Portugal carry NUTS 2021 codes next to NUTS 2024 ones,
and Poland has a declared break in series after the 2021 census.
"""

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

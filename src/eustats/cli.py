"""Command line entry point: `eustats run` executes the whole pipeline."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from eustats.dashboard import write_dashboard
from eustats.dictionary import write_dictionary
from eustats.ingest import ingest
from eustats.load import load
from eustats.quality import write_report

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "datasets.yml"
DBT_DIR = ROOT / "dbt"
FIXTURES = ROOT / "tests" / "fixtures"


@dataclass(frozen=True)
class Paths:
    """Where one pipeline run writes its files (the repository root by default)."""

    out: Path

    @property
    def raw_dir(self) -> Path:
        return self.out / "data" / "raw"

    @property
    def warehouse(self) -> Path:
        return self.out / "data" / "warehouse.duckdb"

    @property
    def dbt_target(self) -> Path:
        return self.out / "dbt" / "target"

    @property
    def docs(self) -> Path:
        return self.out / "docs"

    @property
    def site(self) -> Path:
        return self.out / "site"


def run_dbt(paths: Paths) -> int:
    env = {**os.environ, "EUSTATS_WAREHOUSE": str(paths.warehouse)}
    dbt = Path(sys.executable).with_name("dbt")
    command = [
        str(dbt),
        "build",
        "--project-dir",
        str(DBT_DIR),
        "--profiles-dir",
        str(DBT_DIR),
        "--target-path",
        str(paths.dbt_target),
    ]
    return subprocess.run(command, env=env, cwd=ROOT, check=False).returncode


def report(paths: Paths) -> None:
    write_report(
        paths.warehouse, paths.dbt_target / "run_results.json", paths.docs / "quality-report.md"
    )
    write_dictionary(
        paths.dbt_target / "manifest.json", paths.warehouse, paths.docs / "data-dictionary.md"
    )
    write_dashboard(
        paths.warehouse, paths.raw_dir / "nuts2_2024.geojson", paths.site / "index.html"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eustats", description=__doc__)
    parser.add_argument("step", choices=["ingest", "load", "build", "report", "run"])
    parser.add_argument(
        "--offline",
        action="store_true",
        help="use the sample files in tests/fixtures instead of the Eurostat API",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT,
        help="directory for data, docs and site outputs (default: repository root)",
    )
    args = parser.parse_args(argv)
    paths = Paths(args.out.resolve())

    if args.step in ("ingest", "run"):
        ingest(paths.raw_dir, CONFIG, offline_dir=FIXTURES if args.offline else None)
    if args.step in ("load", "run"):
        load(paths.raw_dir, CONFIG, paths.warehouse)
    if args.step in ("build", "run"):
        # dbt exits with 1 when a check fails; warnings do not fail the build.
        if run_dbt(paths) != 0:
            print("dbt build failed: see the failing checks above.", file=sys.stderr)
            return 1
    if args.step in ("report", "run"):
        report(paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

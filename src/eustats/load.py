"""Load the raw files into the `raw` schema of the DuckDB warehouse.

The raw layer keeps every column as text, exactly as delivered by Eurostat.
Typing, renaming and filtering happen in the dbt staging models.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from eustats.config import load_config


def load(raw_dir: Path, config_path: Path, warehouse: Path) -> None:
    config = load_config(config_path)
    warehouse.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(warehouse)) as con:
        con.execute("create schema if not exists raw")

        for dataset in config.datasets:
            con.execute(
                f"create or replace table raw.{dataset.id} as "
                "select * from read_csv(?, header = true, all_varchar = true)",
                [str(raw_dir / f"{dataset.id}.csv")],
            )

        for codelist in ("geo_codelist", "obs_flag_codelist"):
            con.execute(
                f"create or replace table raw.{codelist} as "
                "select * from read_csv(?, header = true, all_varchar = true)",
                [str(raw_dir / f"{codelist}.csv")],
            )

        features = json.loads((raw_dir / "nuts2_2024.geojson").read_text(encoding="utf-8"))
        nuts_rows = [
            (
                feature["properties"]["NUTS_ID"],
                feature["properties"]["CNTR_CODE"],
                feature["properties"]["NAME_LATN"],
            )
            for feature in features["features"]
        ]
        con.execute(
            "create or replace table raw.gisco_nuts2 "
            "(nuts_id varchar, country_code varchar, name_latn varchar)"
        )
        con.executemany("insert into raw.gisco_nuts2 values (?, ?, ?)", nuts_rows)

        con.execute(
            "create or replace table raw.dataset_config "
            "(indicator_id varchar, dataset_code varchar, label varchar, unit varchar, "
            "valid_min double, valid_max double, on_dashboard boolean, map_midpoint double, "
            "map_log_scale boolean)"
        )
        con.executemany(
            "insert into raw.dataset_config values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    d.id,
                    d.code,
                    d.label,
                    d.unit,
                    d.valid_range[0],
                    d.valid_range[1],
                    d.dashboard,
                    d.map_midpoint,
                    d.map_log_scale,
                )
                for d in config.datasets
            ],
        )

        manifest = json.loads((raw_dir / "manifest.json").read_text(encoding="utf-8"))
        con.execute(
            "create or replace table raw.manifest "
            "(file varchar, dataset_code varchar, source_url varchar, retrieved_at varchar, "
            "offline_fixture boolean, sha256 varchar, rows bigint)"
        )
        con.executemany(
            "insert into raw.manifest values (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    e["file"],
                    e["dataset_code"],
                    e["source_url"],
                    e["retrieved_at"],
                    e["offline_fixture"],
                    e["sha256"],
                    e["rows"],
                )
                for e in manifest["files"]
            ],
        )

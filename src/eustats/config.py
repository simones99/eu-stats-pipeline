"""Typed access to config/datasets.yml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Dataset:
    id: str
    code: str
    key: str
    label: str
    unit: str
    valid_range: tuple[float, float]
    dashboard: bool = True
    map_midpoint: float | None = None
    map_log_scale: bool = False


@dataclass(frozen=True)
class Config:
    start_period: int
    datasets: tuple[Dataset, ...]


def load_config(path: Path) -> Config:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    datasets = tuple(
        Dataset(
            id=item["id"],
            code=item["code"],
            key=item["key"],
            label=item["label"],
            unit=item["unit"],
            valid_range=(float(item["valid_range"][0]), float(item["valid_range"][1])),
            dashboard=bool(item.get("dashboard", True)),
            map_midpoint=(
                float(item["map_midpoint"]) if item.get("map_midpoint") is not None else None
            ),
            map_log_scale=bool(item.get("map_log_scale", False)),
        )
        for item in raw["datasets"]
    )
    return Config(start_period=int(raw["start_period"]), datasets=datasets)

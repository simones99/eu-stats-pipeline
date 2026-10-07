"""Download Eurostat datasets (SDMX-CSV) and the GEO codelist, recording lineage.

Every raw file is written to data/raw/ and described in data/raw/manifest.json
with its source URL, retrieval time, SHA-256 checksum and row count, so any
figure in the outputs can be traced back to the exact file it came from.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

import requests

from eustats.config import Dataset, load_config

SDMX_BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1"
GISCO_NUTS2_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_60M_2024_4326_LEVL_2.geojson"
)
TIMEOUT_SECONDS = 180

SDMX_NS = {
    "s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def dataset_url(dataset: Dataset, start_period: int) -> str:
    return (
        f"{SDMX_BASE}/data/{dataset.code}/{dataset.key}?format=SDMX-CSV&startPeriod={start_period}"
    )


# Codelists stored next to the data: output file name -> Eurostat codelist id.
CODELISTS = {"geo_codelist.csv": "GEO", "obs_flag_codelist.csv": "OBS_FLAG"}


def codelist_url(codelist_id: str) -> str:
    return f"{SDMX_BASE}/codelist/ESTAT/{codelist_id}"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_data_rows(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def parse_codelist(xml_text: str) -> list[tuple[str, str]]:
    """Return (code, English label) pairs from an SDMX-ML 2.1 codelist."""
    root = ET.fromstring(xml_text)
    rows = []
    for code in root.iter(f"{{{SDMX_NS['s']}}}Code"):
        label = next(
            (name.text for name in code.findall("c:Name", SDMX_NS) if name.get(XML_LANG) == "en"),
            None,
        )
        rows.append((code.get("id"), label or ""))
    return rows


def write_codelist_csv(rows: list[tuple[str, str]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["code", "label"])
        writer.writerows(rows)


def _download(url: str, path: Path) -> None:
    response = requests.get(url, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    path.write_bytes(response.content)


def _entry(
    path: Path, dataset_code: str, url: str, retrieved_at: str, offline_dir: Path | None
) -> dict:
    return {
        "file": path.name,
        "dataset_code": dataset_code,
        "source_url": url,
        "retrieved_at": retrieved_at,
        "offline_fixture": offline_dir is not None,
        "sha256": sha256_of(path),
        "rows": count_data_rows(path) if path.suffix == ".csv" else None,
    }


def ingest(raw_dir: Path, config_path: Path, offline_dir: Path | None = None) -> dict:
    """Fetch every configured dataset into raw_dir and write manifest.json.

    With offline_dir set, files are copied from that folder instead of the API
    (used by CI and tests so the pipeline runs without network access).
    """
    config = load_config(config_path)
    raw_dir.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(UTC).isoformat(timespec="seconds")
    entries = []

    sources = [
        (f"{d.id}.csv", dataset_url(d, config.start_period), d.code) for d in config.datasets
    ]
    for filename, url, code in sources:
        target = raw_dir / filename
        if offline_dir:
            shutil.copyfile(offline_dir / filename, target)
        else:
            _download(url, target)
        entries.append(_entry(target, code, url, retrieved_at, offline_dir))

    for filename, codelist_id in CODELISTS.items():
        target = raw_dir / filename
        url = codelist_url(codelist_id)
        if offline_dir:
            shutil.copyfile(offline_dir / filename, target)
        else:
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            write_codelist_csv(parse_codelist(response.text), target)
        entries.append(_entry(target, f"ESTAT:{codelist_id}", url, retrieved_at, offline_dir))

    nuts_target = raw_dir / "nuts2_2024.geojson"
    if offline_dir:
        shutil.copyfile(offline_dir / "nuts2_2024.geojson", nuts_target)
    else:
        _download(GISCO_NUTS2_URL, nuts_target)
    entries.append(
        _entry(nuts_target, "GISCO:NUTS_2024_LEVL_2", GISCO_NUTS2_URL, retrieved_at, offline_dir)
    )

    manifest = {"start_period": config.start_period, "files": entries}
    (raw_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

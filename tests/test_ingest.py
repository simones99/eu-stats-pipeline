import json
from pathlib import Path

from eustats.config import load_config
from eustats.ingest import dataset_url, ingest, parse_codelist, sha256_of

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "datasets.yml"
FIXTURES = ROOT / "tests" / "fixtures"

CODELIST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<m:Structure xmlns:m="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
             xmlns:s="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
             xmlns:c="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
  <m:Structures><s:Codelists><s:Codelist id="GEO" agencyID="ESTAT" version="1.0">
    <s:Code id="ITH3">
      <c:Name xml:lang="de">Venetien</c:Name><c:Name xml:lang="en">Veneto</c:Name>
    </s:Code>
    <s:Code id="EL"><c:Name xml:lang="en">Greece</c:Name></s:Code>
    <s:Code id="XX"><c:Name xml:lang="fr">Inconnu</c:Name></s:Code>
  </s:Codelist></s:Codelists></m:Structures>
</m:Structure>"""


def test_dataset_url_uses_sdmx_key_and_start_period():
    dataset = load_config(CONFIG).datasets[0]
    url = dataset_url(dataset, 2015)
    assert url.endswith(f"/data/{dataset.code}/{dataset.key}?format=SDMX-CSV&startPeriod=2015")


def test_parse_codelist_keeps_english_label_and_codes_without_one():
    assert parse_codelist(CODELIST_XML) == [("ITH3", "Veneto"), ("EL", "Greece"), ("XX", "")]


def test_offline_ingest_writes_manifest_with_checksums(tmp_path):
    manifest = ingest(tmp_path, CONFIG, offline_dir=FIXTURES)

    written = json.loads((tmp_path / "manifest.json").read_text())
    assert written == manifest
    files = {entry["file"]: entry for entry in manifest["files"]}
    assert set(files) == {
        "gdp_pps_per_inhabitant.csv",
        "population.csv",
        "unemployment_rate.csv",
        "geo_codelist.csv",
        "obs_flag_codelist.csv",
        "nuts2_2024.geojson",
    }
    for name, entry in files.items():
        assert entry["sha256"] == sha256_of(tmp_path / name)
        assert entry["offline_fixture"] is True
    population_lines = (FIXTURES / "population.csv").read_text().splitlines()
    assert files["population.csv"]["rows"] == len(population_lines) - 1
    assert files["nuts2_2024.geojson"]["rows"] is None

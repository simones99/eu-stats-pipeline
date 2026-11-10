from pathlib import Path

from eustats.config import load_config

CONFIG = Path(__file__).resolve().parents[1] / "config" / "datasets.yml"


def _datasets():
    return {dataset.id: dataset for dataset in load_config(CONFIG).datasets}


def test_indicators_are_on_the_dashboard_unless_switched_off():
    datasets = _datasets()
    on_dashboard = {name for name, dataset in datasets.items() if dataset.dashboard}
    assert on_dashboard == {"gdp_pps_pct_eu27", "population_density", "unemployment_rate"}


def test_only_the_eu27_index_has_a_map_midpoint():
    datasets = _datasets()
    assert datasets["gdp_pps_pct_eu27"].map_midpoint == 100
    assert datasets["unemployment_rate"].map_midpoint is None


def test_only_density_is_mapped_on_a_log_scale():
    log_scaled = {name for name, dataset in _datasets().items() if dataset.map_log_scale}
    assert log_scaled == {"population_density"}

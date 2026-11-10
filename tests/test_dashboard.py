import pandas as pd
import pytest

from eustats.dashboard import DIVERGING_SCALE, SEQUENTIAL_SCALE, log_ticks, map_colours

VALUES = pd.Series([float(v) for v in range(40, 241)])  # 5th pct = 50, 95th pct = 230


def test_map_colours_clip_to_the_5th_and_95th_percentiles():
    scale, colour_range = map_colours(VALUES, midpoint=None)
    assert scale == SEQUENTIAL_SCALE
    assert colour_range == pytest.approx((50, 230))


def test_map_colours_with_a_midpoint_are_diverging_and_centred_on_it():
    scale, colour_range = map_colours(VALUES, midpoint=100)
    assert scale == DIVERGING_SCALE
    # The wider side (100 -> 230) sets both sides, so 100 sits at the neutral colour.
    assert colour_range == pytest.approx((-30, 230))


def test_log_ticks_are_round_values_inside_the_range():
    assert log_ticks(25, 1300) == [30, 100, 300, 1000]


def test_log_ticks_cover_fractions_and_thousands():
    assert log_ticks(0.5, 3500) == [1, 3, 10, 30, 100, 300, 1000, 3000]

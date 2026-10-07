"""Shared fixtures: the real BepInEx exports in data/cache."""

from pathlib import Path

import pytest

from fm_advisor.ingestion import load_squad, merge_squads

DATA = Path(__file__).parent.parent / "data" / "cache"


@pytest.fixture(scope="session")
def real_attr_result():
    return load_squad(DATA / "moneyball_export_20260811_093123.csv")


@pytest.fixture(scope="session")
def real_perf_result():
    return load_squad(DATA / "moneyball_export_20260811_093025.csv")


@pytest.fixture(scope="session")
def real_merged(real_attr_result, real_perf_result):
    merged, _ = merge_squads(real_attr_result, real_perf_result)
    return merged

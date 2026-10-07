"""Shared fixtures: exports in the combined single-file view."""

from pathlib import Path

import pytest

from fm_advisor.ingestion import load_squad

ROOT = Path(__file__).parent.parent
SAMPLE_EXPORT = ROOT / "data" / "samples" / "combined_view_sample.csv"
FIXTURE_SQUAD = Path(__file__).parent / "_fixtures" / "squad_combined.csv"


@pytest.fixture(scope="session")
def sample_result():
    """The real one-player export that defines the view's columns."""
    return load_squad(SAMPLE_EXPORT)


@pytest.fixture(scope="session")
def squad_result():
    """An 11-player squad in the same view (the sample row plus made-up players)."""
    return load_squad(FIXTURE_SQUAD)


@pytest.fixture(scope="session")
def squad(squad_result):
    return squad_result.players

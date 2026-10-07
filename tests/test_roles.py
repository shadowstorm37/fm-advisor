"""Tests for the FM26 role library in fm_advisor.scoring.roles."""

import pytest

from fm_advisor.ingestion import ATTRIBUTE_NAMES
from fm_advisor.role_catalogue import POSITIONS, ROLE_CATALOGUE, Phase
from fm_advisor.scoring import ROLE_LIBRARY, evaluate_role, role_key, roles_at
from fm_advisor.scoring.roles import KEY_WEIGHT, SUPPORT_WEIGHT, _tiered


def test_library_has_one_definition_per_phase_and_code():
    assert len(ROLE_LIBRARY) == 72


def test_every_catalogue_role_is_scoreable_at_its_position():
    for entry in ROLE_CATALOGUE:
        role = ROLE_LIBRARY[role_key(entry.phase, entry.code)]
        assert entry.position in role.eligible_positions, entry
        assert role.display_name == f"{entry.name} ({entry.phase.value})"


def test_every_position_has_roles_in_both_phases():
    for position in POSITIONS:
        assert roles_at(position, Phase.IP), position
        assert roles_at(position, Phase.OOP), position


def test_roles_only_use_real_attributes():
    for role in ROLE_LIBRARY.values():
        unknown = set(role.attribute_weights) - set(ATTRIBUTE_NAMES)
        assert not unknown, (role.key, unknown)


def test_roles_only_use_stats_the_export_carries(sample_result):
    exported = set(sample_result.players[0].stats)
    for role in ROLE_LIBRARY.values():
        unknown = {s.name for s in role.stat_weights} - exported
        assert not unknown, (role.key, unknown)


def test_key_attributes_count_double():
    weights = _tiered(("Passing", "Vision"), ("Composure",), "example")
    assert weights["Passing"] == pytest.approx(weights["Composure"] * KEY_WEIGHT / SUPPORT_WEIGHT)
    assert sum(weights.values()) == pytest.approx(1.0)


def test_listing_a_name_twice_is_rejected():
    with pytest.raises(ValueError):
        _tiered(("Passing",), ("Passing",), "example")


def test_possession_lost_is_scored_lower_is_better():
    stats = {s.name: s for s in ROLE_LIBRARY["ip_bcb"].stat_weights}
    assert stats["Possession Lost per 90"].higher_is_better is False
    assert stats["Pass Completion Percentage"].higher_is_better is True


def test_out_of_possession_keeper_roles_are_attribute_only():
    for key in ("oop_gk", "oop_sk", "oop_lhk"):
        assert ROLE_LIBRARY[key].stat_weights == ()


def test_every_role_scores_a_loaded_squad(squad):
    for role in ROLE_LIBRARY.values():
        for result in evaluate_role(squad, role):
            assert 0.0 <= result.role_score <= 100.0

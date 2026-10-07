"""Tests for fm_advisor.role_catalogue."""

from collections import Counter

from fm_advisor.ingestion import load_squad
from fm_advisor.role_catalogue import (
    POSITIONS,
    ROLE_CATALOGUE,
    Phase,
    find_roles,
    role_names,
    roles_for,
)


def test_catalogue_size_and_positions():
    assert len(ROLE_CATALOGUE) == 112
    assert set(POSITIONS) == {
        "GK", "DC", "DR", "DL", "WBR", "WBL", "DM", "MC", "MR", "ML", "AMC", "AMR", "AML", "ST",
    }


def test_every_position_has_roles_in_both_phases():
    for position in POSITIONS:
        assert roles_for(position, Phase.IP), position
        assert roles_for(position, Phase.OOP), position


def test_position_phase_code_is_unique():
    keys = Counter((r.position, r.phase, r.code) for r in ROLE_CATALOGUE)
    assert [k for k, n in keys.items() if n > 1] == []


def test_left_and_right_sides_share_the_same_roles():
    for right, left in (("DR", "DL"), ("WBR", "WBL"), ("MR", "ML"), ("AMR", "AML")):
        assert [(r.code, r.name, r.phase) for r in roles_for(right)] == [
            (r.code, r.name, r.phase) for r in roles_for(left)
        ]


def test_wide_midfielder_code_differs_by_phase():
    assert [r.phase for r in find_roles("WM", ["ML"])] == [Phase.IP]
    assert [r.phase for r in find_roles("WMF", ["ML"])] == [Phase.OOP]


def test_code_resolves_to_a_single_role():
    matches = find_roles("BCB", ["DC"])
    assert [(r.name, r.phase) for r in matches] == [("Ball-Playing Centre-Back", Phase.IP)]


def test_code_shared_across_phases_returns_both():
    assert [r.phase for r in find_roles("CB", ["DC"])] == [Phase.IP, Phase.OOP]
    assert role_names("CB", ["DC"]) == ["Centre-Back"]
    assert role_names("PWB", ["WBR"]) == ["Playmaking Wing-Back", "Pressing Wing-Back"]


def test_code_is_resolved_only_at_the_given_positions():
    assert role_names("AM", ["MC"]) == ["Attacking Midfielder"]
    assert find_roles("BCB", ["ST"]) == []
    assert find_roles("bcb ", ["DC"]) != []   # case and stray spaces tolerated


def test_sample_export_best_role_is_known(sample_result):
    ross = sample_result.players[0]
    assert role_names(ross.best_role, ross.best_positions) == ["Ball-Playing Centre-Back"]


def test_unknown_best_role_raises_a_load_warning(tmp_path):
    path = tmp_path / "bad_role.csv"
    path.write_text("Player;Best Pos;Best Role\nSolo;D (C);XYZ\n", encoding="utf-8")
    result = load_squad(path)
    assert result.warnings == ["Best Role 'XYZ' for Solo is not an FM26 role at DC."]

"""Tests for fm_advisor.squad (Phase 2)."""

import json
from datetime import date

import pytest

from fm_advisor.ingestion import Player
from fm_advisor.role_catalogue import POSITIONS, Phase
from fm_advisor.scoring import RoleDefinition
from fm_advisor.squad import (
    audit_contracts,
    build_depth_chart,
    build_squad_report,
)
from fm_advisor.squad.depth_chart import (
    CRITICAL_WEAKNESS,
    DEPTH_CONCERN,
    HEALTHY,
    NO_COVERAGE,
)

from helpers import TEST_CD_ROLE

ROLES = [TEST_CD_ROLE]

STRONG_CB = dict(positions=["DC"], attributes={"Tackling": 18, "Heading": 17, "Positioning": 16, "Strength": 16})
WEAK_CB = dict(positions=["DC"], attributes={"Tackling": 6, "Heading": 5, "Positioning": 6, "Strength": 7})
BACKUP_CB = dict(positions=["DC"], attributes={"Tackling": 12, "Heading": 11, "Positioning": 12, "Strength": 12})


def _cd_depth(players):
    return build_depth_chart(players, roles=ROLES)[0]


def test_no_coverage_when_nobody_plays_the_position():
    depth = _cd_depth([Player(name="Striker Only", positions=["ST"], attributes={"Finishing": 15})])
    assert depth.status == NO_COVERAGE
    assert depth.quality_count == 0
    assert depth.no_data_count == 0


def test_critical_weakness_with_one_strong_player_and_no_backup():
    depth = _cd_depth([Player(name="Ace", **STRONG_CB)])
    assert depth.status == CRITICAL_WEAKNESS
    assert depth.quality_count == 1


def test_depth_concern_with_one_quality_and_one_backup():
    depth = _cd_depth([Player(name="Ace", **STRONG_CB), Player(name="Squad Player", **BACKUP_CB)])
    assert depth.status == DEPTH_CONCERN
    assert depth.quality_count == 1
    assert depth.backup_count == 1


def test_healthy_with_two_quality_players():
    depth = _cd_depth([Player(name="Ace", **STRONG_CB), Player(name="Ace 2", **STRONG_CB)])
    assert depth.status == HEALTHY
    assert depth.quality_count == 2


def test_no_data_player_is_neither_a_weakness_nor_coverage():
    # eligible, zero attributes, zero stats
    depth = _cd_depth([Player(name="Blank Slate", positions=["DC"])])
    assert depth.status == NO_COVERAGE          # not Critical Weakness
    assert depth.no_data_count == 1
    assert depth.entries[0].tier == "no_data"
    assert depth.entries[0].score is None       # not 0.0


def _one_attribute_role(key, attribute, phase, positions=("DC",)):
    return RoleDefinition(
        key=key, display_name=key, attribute_weights={attribute: 1.0},
        eligible_positions=positions, phase=phase,
    )


def test_position_score_averages_best_role_in_each_phase():
    roles = [
        _one_attribute_role("ip_pass", "Passing", Phase.IP),
        _one_attribute_role("ip_dribble", "Dribbling", Phase.IP),
        _one_attribute_role("oop_tackle", "Tackling", Phase.OOP),
    ]
    # Passing 20 -> 100, Dribbling 1 -> 0, Tackling 1 -> 0.
    player = Player(name="Passer", positions=["DC"], attributes={"Passing": 20, "Dribbling": 1, "Tackling": 1})
    entry = build_depth_chart([player], roles=roles)[0].entries[0]

    assert [(f.phase, f.role_key, f.role_score) for f in entry.best_roles] == [
        ("IP", "ip_pass", 100.0),
        ("OOP", "oop_tackle", 0.0),
    ]
    assert entry.score == 50.0
    assert entry.tier == "backup"


def test_entries_are_ranked_and_marked_natural_or_not():
    players = [
        Player(name="Fill-In", positions=["DC", "DM"], best_positions=["DM"], attributes=BACKUP_CB["attributes"]),
        Player(name="Natural", best_positions=["DC"], **STRONG_CB),
    ]
    depth = _cd_depth(players)
    assert [(e.player_name, e.natural) for e in depth.entries] == [("Natural", True), ("Fill-In", False)]


def test_full_library_covers_every_position(squad):
    chart = build_depth_chart(squad)
    assert [d.position for d in chart] == list(POSITIONS)

    by_position = {d.position: d for d in chart}
    assert by_position["WBL"].status == NO_COVERAGE   # nobody in the fixture squad plays there

    # A player appears at every position they can play, natural only at their best.
    winger_spots = {
        d.position: e.natural
        for d in chart for e in d.entries if e.player_name == "Fixture Winger"
    }
    assert winger_spots == {"MR": False, "ML": False, "AMR": True, "AML": False}

    # With the full library every scored player has one IP and one OOP role.
    for depth in chart:
        for entry in depth.entries:
            assert [f.phase for f in entry.best_roles] == ["IP", "OOP"]
            assert entry.score == pytest.approx(sum(f.role_score for f in entry.best_roles) / 2, abs=0.05)


def test_contract_audit_flags_starting_caliber_player_expiring_soon():
    players = [
        Player(name="Star", contract_expiry=date(2027, 1, 1), **STRONG_CB),   # ~5 months out
        Player(name="Weak Link", contract_expiry=date(2026, 9, 1), **WEAK_CB),  # expires soon but not starting-caliber
        Player(name="Safe Star", contract_expiry=date(2030, 1, 1), **STRONG_CB),  # starting-caliber, contract fine
        Player(name="Mystery Star", positions=["DC"], attributes=STRONG_CB["attributes"]),  # no contract data at all
    ]
    result = audit_contracts(players, roles=ROLES, reference=date(2026, 8, 11))
    assert [f.player_name for f in result.flags] == ["Star"]
    assert result.flags[0].months_until_expiry == 5
    assert result.flags[0].positions == ["DC"]
    # unknown contract is tracked separately, not flagged as urgent
    assert result.unknown_contract_players == ["Mystery Star"]


def test_contract_audit_flags_a_player_once_across_positions():
    roles = [
        _one_attribute_role("cb", "Tackling", None, positions=("DC",)),
        _one_attribute_role("dm", "Tackling", None, positions=("DM",)),
    ]
    player = Player(
        name="Versatile", positions=["DC", "DM"], attributes={"Tackling": 18},
        contract_expiry=date(2026, 12, 1),
    )
    result = audit_contracts([player], roles=roles, reference=date(2026, 8, 11))
    assert len(result.flags) == 1
    assert result.flags[0].positions == ["DC", "DM"]


def test_loaded_squad_report_is_json_serializable(squad):
    report = build_squad_report(squad, roles=ROLES)
    assert report["squad_size"] == len(squad)
    assert [d["position"] for d in report["depth_chart"]] == ["DC"]
    assert isinstance(json.dumps(report), str)

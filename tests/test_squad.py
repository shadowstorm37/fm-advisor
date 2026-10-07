"""Tests for fm_advisor.squad (Phase 2)."""

import json
from datetime import date

from fm_advisor.ingestion import Player
from fm_advisor.scoring import CENTRAL_DEFENDER_DEFEND
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

ROLES = [CENTRAL_DEFENDER_DEFEND]

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
    assert depth.entries[0].role_score is None  # not 0.0


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
    # unknown contract is tracked separately, not flagged as urgent
    assert result.unknown_contract_players == ["Mystery Star"]


def test_real_squad_report_is_json_serializable(real_merged):
    report = build_squad_report(real_merged, roles=ROLES)
    assert report["squad_size"] == len(real_merged)
    assert len(report["depth_chart"]) == len(ROLES)
    assert isinstance(json.dumps(report), str)

"""Tests for fm_advisor.scoring (Task 1.3)."""

from fm_advisor.ingestion import Player
from fm_advisor.scoring import (
    ADVANCED_FORWARD_ATTACK,
    CENTRAL_DEFENDER_DEFEND,
    compute_attribute_score,
    evaluate_role,
)

CB_STATS = (
    "Tackle Completion Percentage",
    "Headers Won Percentage",
    "Interceptions per 90",
    "Possession Lost per 90",
)


def _cb(name, attributes=None, stats=None):
    return Player(
        name=name,
        positions=["DC"],
        attributes=attributes or {},
        stats=dict(zip(CB_STATS, stats)) if stats else {},
    )


TEST_CB = _cb("Test CB", {"Tackling": 16, "Heading": 15, "Positioning": 15, "Strength": 14})
LEVEL_ATTRS = {"Tackling": 10, "Heading": 10, "Positioning": 10, "Strength": 10}


def test_attribute_score_matches_spec_formula():
    # spec formula, unscaled: 16*0.3 + 15*0.3 + 15*0.2 + 14*0.2 = 15.1
    raw = 16 * 0.3 + 15 * 0.3 + 15 * 0.2 + 14 * 0.2
    expected_0_100 = (raw - 1) / 19 * 100
    assert round(compute_attribute_score(TEST_CB, CENTRAL_DEFENDER_DEFEND), 4) == round(expected_0_100, 4)


def test_attribute_only_player_falls_back_to_attribute_score():
    result = evaluate_role([TEST_CB], CENTRAL_DEFENDER_DEFEND)
    assert len(result) == 1
    assert result[0].stat_score is None
    assert result[0].role_score == result[0].attribute_score


def test_stats_only_player_falls_back_to_stat_score():
    stats_only = _cb("Stats Only CB", stats=(80.0, 70.0, 2.0, 2.0))
    result = evaluate_role([stats_only], CENTRAL_DEFENDER_DEFEND)
    assert result[0].attribute_score is None             # not 0.0
    assert result[0].role_score == result[0].stat_score  # not dragged to 0


def test_stat_percentiles_follow_squad_spread_including_inverted_stats():
    a = _cb("A", LEVEL_ATTRS, stats=(90.0, 80.0, 3.0, 1.0))
    b = _cb("B", LEVEL_ATTRS, stats=(50.0, 40.0, 1.0, 5.0))
    results = evaluate_role([a, b], CENTRAL_DEFENDER_DEFEND)
    assert results[0].player.name == "A"   # same attributes -> stats break the tie
    assert results[0].stat_score > 90
    assert results[1].stat_score < 10      # more possession lost is penalised


def test_loaded_squad_results_sorted_descending(squad):
    scores = [r.role_score for r in evaluate_role(squad, CENTRAL_DEFENDER_DEFEND)]
    assert scores == sorted(scores, reverse=True)
    # AF-Attack must also evaluate cleanly against a loaded squad.
    evaluate_role(squad, ADVANCED_FORWARD_ATTACK)

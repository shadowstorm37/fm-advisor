"""Tests for fm_advisor.tactics (Phase 3 structured-output schema)."""

import pytest
from pydantic import ValidationError

from fm_advisor.tactics import InPossession, OutOfPossession, TacticalPlan, Transitions

VALID_PLAN = {
    "in_possession": {
        "build_up_strategy": "Play Through Press",
        "goal_kicks": "Short",
        "gk_distribution_speed": "Balanced",
        "gk_distribution_target": "Centre-Backs",
        "time_wasting": "Standard",
        "passing_directness": "Shorter",
        "tempo": "Higher",
        "creative_freedom": "More Expressive",
        "supporting_runs": "Both Flanks Balanced",
        "progress_through": "Middle",
        "pass_reception": "Pass to Feet",
        "attacking_width": "Standard",
        "dribbling": "Balanced",
        "patience": "Work Ball Into Box",
        "shots_from_distance": "Discouraged",
        "crossing_style": "Low Crosses",
        "play_for_set_pieces": "Keep ball in play",
    },
    "out_of_possession": {
        "defensive_line": "Lower",
        "line_of_engagement": "Middle Block",
        "pressing_traps": "Trap Outside",
        "cross_engagement": "Stop Crosses",
        "defensive_width": "Narrow",
        "tackling": "Stay on Feet",
        "short_gk_distribution_response": False,
    },
    "transitions": {
        "attacking_transition": "Counter-Attack",
        "defensive_transition": "Regroup",
    },
    "tactical_reasoning": "Their forwards are quicker than our centre-backs.",
}


def test_valid_plan_round_trips():
    plan = TacticalPlan.model_validate(VALID_PLAN)
    assert plan.model_dump(mode="json") == VALID_PLAN


def test_instruction_counts_match_spec():
    assert len(InPossession.model_fields) == 17
    assert len(OutOfPossession.model_fields) == 7
    assert len(Transitions.model_fields) == 2


def test_option_outside_enum_is_rejected():
    bad = {**VALID_PLAN, "transitions": {**VALID_PLAN["transitions"], "attacking_transition": "Gegenpress"}}
    with pytest.raises(ValidationError):
        TacticalPlan.model_validate(bad)


def test_unknown_instruction_is_rejected():
    bad = {**VALID_PLAN, "transitions": {**VALID_PLAN["transitions"], "offside_trap": "Yes"}}
    with pytest.raises(ValidationError):
        TacticalPlan.model_validate(bad)

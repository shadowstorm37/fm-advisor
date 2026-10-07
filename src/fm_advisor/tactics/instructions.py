"""
FM26 tactical instruction schema (Phase 3, Task 3.2).

Every enum mirrors one FM26 team instruction and its exact in-game option
labels. `TacticalPlan` is the structured-output contract handed to the LLM:
it can only pick from these options, so an invalid instruction can never
reach the UI.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


# --- In possession -----------------------------------------------------------

class BuildUpStrategy(StrEnum):
    BYPASS_PRESS = "Bypass Press"
    PLAY_THROUGH_PRESS = "Play Through Press"
    BALANCED = "Balanced"


class GoalKicks(StrEnum):
    SHORT = "Short"
    LONG = "Long"
    MIXED = "Mixed"


class GKDistributionSpeed(StrEnum):
    DISTRIBUTE_QUICKLY = "Distribute Quickly"
    BALANCED = "Balanced"
    SLOW_PACE_DOWN = "Slow Pace Down"


class GKDistributionTarget(StrEnum):
    CENTRE_BACKS = "Centre-Backs"
    FULL_BACKS = "Full-Backs"
    FLANKS = "Flanks"
    PLAYMAKERS = "Playmakers"
    TARGET_AREA_MAN = "Target Area/Man"


class TimeWasting(StrEnum):
    LESS_OFTEN = "Less Often"
    STANDARD = "Standard"
    MORE_OFTEN = "More Often"


class PassingDirectness(StrEnum):
    MUCH_SHORTER = "Much Shorter"
    SHORTER = "Shorter"
    STANDARD = "Standard"
    MORE_DIRECT = "More Direct"
    MUCH_MORE_DIRECT = "Much More Direct"


class Tempo(StrEnum):
    MUCH_LOWER = "Much Lower"
    LOWER = "Lower"
    STANDARD = "Standard"
    HIGHER = "Higher"
    MUCH_HIGHER = "Much Higher"


class CreativeFreedom(StrEnum):
    BE_MORE_DISCIPLINED = "Be More Disciplined"
    MORE_EXPRESSIVE = "More Expressive"


class SupportingRuns(StrEnum):
    LEFT = "Left"
    RIGHT = "Right"
    BOTH_FLANKS_BALANCED = "Both Flanks Balanced"


class ProgressThrough(StrEnum):
    BALANCED = "Balanced"
    MIDDLE = "Middle"
    LEFT = "Left"
    RIGHT = "Right"
    BOTH_FLANKS = "Both Flanks"


class PassReception(StrEnum):
    PASS_INTO_SPACE = "Pass into Space"
    BALANCED = "Balanced"
    PASS_TO_FEET = "Pass to Feet"


class AttackingWidth(StrEnum):
    MUCH_NARROWER = "Much Narrower"
    NARROWER = "Narrower"
    STANDARD = "Standard"
    WIDER = "Wider"
    MUCH_WIDER = "Much Wider"


class Dribbling(StrEnum):
    ENCOURAGED = "Encouraged"
    BALANCED = "Balanced"
    DISCOURAGED = "Discouraged"


class Patience(StrEnum):
    WORK_BALL_INTO_BOX = "Work Ball Into Box"
    STANDARD = "Standard"
    HIT_EARLY_CROSSES = "Hit Early Crosses"


class ShotsFromDistance(StrEnum):
    ENCOURAGED = "Encouraged"
    BALANCED = "Balanced"
    DISCOURAGED = "Discouraged"


class CrossingStyle(StrEnum):
    LOW_CROSSES = "Low Crosses"
    WHIPPED_CROSSES = "Whipped Crosses"
    FLOATED_CROSSES = "Floated Crosses"
    BALANCED = "Balanced"


class PlayForSetPieces(StrEnum):
    PLAY_FOR_SET_PIECES = "Play for Set Pieces"
    KEEP_BALL_IN_PLAY = "Keep ball in play"


# --- Out of possession -------------------------------------------------------

class DefensiveLine(StrEnum):
    MUCH_HIGHER = "Much Higher"
    HIGHER = "Higher"
    STANDARD = "Standard"
    LOWER = "Lower"
    MUCH_LOWER = "Much Lower"


class LineOfEngagement(StrEnum):
    HIGH_PRESS = "High Press"
    MIDDLE_BLOCK = "Middle Block"
    LOW_BLOCK = "Low Block"


class PressingTraps(StrEnum):
    TRAP_OUTSIDE = "Trap Outside"
    STANDARD = "Standard"
    TRAP_INSIDE = "Trap Inside"


class CrossEngagement(StrEnum):
    INVITE_CROSSES = "Invite Crosses"
    STOP_CROSSES = "Stop Crosses"
    STANDARD = "Standard"


class DefensiveWidth(StrEnum):
    STANDARD = "Standard"
    NARROW = "Narrow"
    WIDE = "Wide"


class Tackling(StrEnum):
    GET_STUCK_IN = "Get Stuck In"
    STANDARD = "Standard"
    STAY_ON_FEET = "Stay on Feet"


# --- Transitions -------------------------------------------------------------

class AttackingTransition(StrEnum):
    COUNTER_ATTACK = "Counter-Attack"
    STANDARD = "Standard"
    HOLD_SHAPE = "Hold Shape"


class DefensiveTransition(StrEnum):
    COUNTER_PRESS = "Counter-Press"
    REGROUP = "Regroup"
    STANDARD = "Standard"


# --- Structured output models ------------------------------------------------

class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InPossession(_Strict):
    build_up_strategy: BuildUpStrategy
    goal_kicks: GoalKicks
    gk_distribution_speed: GKDistributionSpeed
    gk_distribution_target: GKDistributionTarget
    time_wasting: TimeWasting
    passing_directness: PassingDirectness
    tempo: Tempo
    creative_freedom: CreativeFreedom
    supporting_runs: SupportingRuns
    progress_through: ProgressThrough
    pass_reception: PassReception
    attacking_width: AttackingWidth
    dribbling: Dribbling
    patience: Patience
    shots_from_distance: ShotsFromDistance
    crossing_style: CrossingStyle
    play_for_set_pieces: PlayForSetPieces


class OutOfPossession(_Strict):
    defensive_line: DefensiveLine
    line_of_engagement: LineOfEngagement
    pressing_traps: PressingTraps
    cross_engagement: CrossEngagement
    defensive_width: DefensiveWidth
    tackling: Tackling
    short_gk_distribution_response: bool


class Transitions(_Strict):
    attacking_transition: AttackingTransition
    defensive_transition: DefensiveTransition


class TacticalPlan(_Strict):
    """The complete LLM response: one choice per instruction plus the why."""
    in_possession: InPossession
    out_of_possession: OutOfPossession
    transitions: Transitions
    tactical_reasoning: str = Field(
        description="Plain-language justification citing the matchup figures provided."
    )

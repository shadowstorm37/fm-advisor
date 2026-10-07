"""
Role definitions for the Task 1.3 matrix evaluator.

Each RoleDefinition pairs the attribute weights spec'd in the project prompt
with a small set of *relevant* performance stats from the combined export,
so a role score can be blended: rated ability (what a player is capable of)
adjusted by observed output (what they've actually done on the pitch).

Starting scope (per current decision): two roles, to prove the scoring math
generalizes across a defensive and an attacking position before expanding to
the full FM26 role list.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StatWeight:
    """
    A performance stat's contribution to a role's stat-based score.

    `higher_is_better=False` flips the normalization (e.g. Possession Lost per
    90 — a lower rate is the good outcome).
    """
    name: str
    weight: float
    higher_is_better: bool = True


@dataclass(frozen=True)
class RoleDefinition:
    """
    A single FM26 tactical role.

    attribute_weights : canonical attribute name -> weight. Must sum to 1.0
                         so the weighted average lands on the 1-20 scale
                         before being rescaled to 0-100.
    stat_weights       : relevant performance stats and their contribution
                          to the stat-based half of the blended score.
    eligible_positions : canonical position tokens (from Player.positions)
                          a player must hold at least one of to be scored
                          for this role at all.
    stat_blend         : fraction of the final score contributed by stats
                          (0.0 = attributes only, matching the original
                          spec; 1.0 = stats only). Only applied when the
                          player actually has stats data — falls back to
                          pure attribute score otherwise.
    """
    key: str
    display_name: str
    attribute_weights: dict[str, float]
    eligible_positions: tuple[str, ...]
    stat_weights: tuple[StatWeight, ...] = field(default_factory=tuple)
    stat_blend: float = 0.35

    def __post_init__(self) -> None:
        total = round(sum(self.attribute_weights.values()), 6)
        if total != 1.0:
            raise ValueError(
                f"{self.key}: attribute_weights must sum to 1.0, got {total}"
            )
        if not (0.0 <= self.stat_blend <= 1.0):
            raise ValueError(f"{self.key}: stat_blend must be in [0, 1]")


# --- Central Defender - Defend ------------------------------------------
# Attribute weights taken directly from the project spec's worked example.
CENTRAL_DEFENDER_DEFEND = RoleDefinition(
    key="cd_defend",
    display_name="Central Defender (Defend)",
    attribute_weights={
        "Tackling": 0.3,
        "Heading": 0.3,
        "Positioning": 0.2,
        "Strength": 0.2,
    },
    eligible_positions=("DC",),
    stat_weights=(
        StatWeight("Tackle Completion Percentage", weight=0.4),
        StatWeight("Headers Won Percentage", weight=0.35),
        StatWeight("Interceptions per 90", weight=0.15),
        StatWeight("Possession Lost per 90", weight=0.10, higher_is_better=False),
    ),
    stat_blend=0.35,
)

# --- Advanced Forward - Attack -------------------------------------------
# A second, structurally different role (attacking output vs. defensive duels)
# to confirm the evaluator generalizes rather than being CD-shaped by accident.
ADVANCED_FORWARD_ATTACK = RoleDefinition(
    key="af_attack",
    display_name="Advanced Forward (Attack)",
    attribute_weights={
        "Finishing": 0.30,
        "Off The Ball": 0.20,
        "Acceleration": 0.15,
        "Pace": 0.15,
        "Composure": 0.10,
        "Dribbling": 0.10,
    },
    eligible_positions=("ST",),
    stat_weights=(
        StatWeight("Goals per 90 minutes", weight=0.40),
        StatWeight("xG/90", weight=0.30),
        StatWeight("Conv %", weight=0.20),
        StatWeight("Shots on Target Percentage", weight=0.10),
    ),
    stat_blend=0.35,
)

ROLE_LIBRARY: dict[str, RoleDefinition] = {
    r.key: r for r in (CENTRAL_DEFENDER_DEFEND, ADVANCED_FORWARD_ATTACK)
}
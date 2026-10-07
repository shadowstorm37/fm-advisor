"""
Task 1.3 — mathematical matrix evaluator.

Turns each player's raw attributes (and, where available, performance stats)
into a single 0-100 role score, and ranks the squad by it. All deterministic:
no AI involved anywhere in this module, per the project's "data integrity
over AI guesswork" constraint.

Scoring shape
-------------
attribute_score : weighted average of the role's rated attributes (1-20),
                   rescaled to 0-100. This alone reproduces the spec's worked
                   example exactly (CD-Defend formula -> /20 -> *5).

stat_score       : each relevant performance stat is converted to a 0-100
                    percentile *relative to the current squad* (min-max
                    normalized across whichever players in the squad actually
                    have that stat), then combined by the role's stat weights.
                    Squad-relative because raw per-90 rates have no fixed
                    "good" scale on their own — "0.6 xA/90" only means
                    something next to the rest of the squad's numbers.

role_score       : blended attribute_score and stat_score per the role's
                    `stat_blend`. A player with no performance data
                    (attribute-only export) still gets a full score — it just
                    falls back to 100% attribute-based, so nobody is penalised
                    for missing data rather than for actually being worse.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from fm_advisor.ingestion import Player

from .roles import RoleDefinition, StatWeight


@dataclass
class RoleScoreResult:
    """One player's score breakdown for one role."""
    player: Player
    attribute_score: Optional[float]   # 0-100, None if player has no attribute data at all
    stat_score: Optional[float]        # 0-100, None if no usable stats
    role_score: float                  # 0-100, final blended score
    eligible: bool                     # holds at least one of the role's positions


def compute_attribute_score(player: Player, role: RoleDefinition) -> float:
    """Weighted average of the role's rated attributes, rescaled 1-20 -> 0-100."""
    weighted_sum = sum(
        player.attr(attr_name) * weight
        for attr_name, weight in role.attribute_weights.items()
    )
    # weights sum to 1.0 (enforced in RoleDefinition), so weighted_sum is on
    # the native 1-20 scale; rescale linearly so 1 -> 0 and 20 -> 100.
    return max(0.0, min(100.0, (weighted_sum - 1) / 19 * 100))


def _squad_stat_percentiles(
    players: list[Player], stat: StatWeight
) -> dict[str, float]:
    """
    Min-max normalize one stat across every player in `players` that has it,
    keyed by player name. Missing values are simply excluded, not defaulted
    to zero, so a blank cell never masquerades as "worst in the squad."
    """
    values = {p.name: p.stat(stat.name) for p in players if p.stat(stat.name) is not None}
    if not values:
        return {}
    lo, hi = min(values.values()), max(values.values())
    if hi == lo:
        # Every player identical on this stat: no discriminating signal,
        # score everyone at the midpoint rather than dividing by zero.
        return {name: 50.0 for name in values}
    percentiles = {}
    for name, value in values.items():
        pct = (value - lo) / (hi - lo) * 100
        if not stat.higher_is_better:
            pct = 100 - pct
        percentiles[name] = pct
    return percentiles


def compute_stat_score(
    player: Player,
    role: RoleDefinition,
    squad_percentiles: dict[str, dict[str, float]],
) -> Optional[float]:
    """
    Weighted blend of the role's stat percentiles for this player.

    Returns None if the player has none of the role's relevant stats at all
    (e.g. an attribute-only export with no performance data), so
    the caller can fall back to a pure attribute score rather than guessing.
    """
    contributions: list[tuple[float, float]] = []  # (percentile, weight)
    for stat in role.stat_weights:
        pct = squad_percentiles.get(stat.name, {}).get(player.name)
        if pct is not None:
            contributions.append((pct, stat.weight))
    if not contributions:
        return None
    total_weight = sum(w for _, w in contributions)
    return sum(pct * w for pct, w in contributions) / total_weight


def evaluate_role(
    players: list[Player],
    role: RoleDefinition,
    only_eligible: bool = True,
) -> list[RoleScoreResult]:
    """
    Score every player in `players` against `role`, sorted best-to-worst.

    only_eligible=True (default) restricts results to players who hold at
    least one of the role's eligible_positions — set False to see how
    every player would grade out regardless of what position they play.
    """
    # Precompute squad-relative percentiles once per stat (not once per player).
    squad_percentiles = {
        stat.name: _squad_stat_percentiles(players, stat) for stat in role.stat_weights
    }

    results: list[RoleScoreResult] = []
    for player in players:
        eligible = any(pos in player.positions for pos in role.eligible_positions)
        if only_eligible and not eligible:
            continue

        # A player loaded from a stats-only export has no real ratings —
        # every attribute silently defaulted to the baseline (1), which would
        # score as 0.0 and unfairly tank the blend. Treat that as "no
        # attribute data" (None) rather than "worst possible attributes."
        has_real_attributes = player.has_attributes()
        attr_score = compute_attribute_score(player, role) if has_real_attributes else None
        stat_score = compute_stat_score(player, role, squad_percentiles)

        if attr_score is None and stat_score is None:
            role_score = 0.0
        elif attr_score is None:
            role_score = stat_score
        elif stat_score is None:
            role_score = attr_score
        else:
            role_score = (1 - role.stat_blend) * attr_score + role.stat_blend * stat_score

        results.append(RoleScoreResult(
            player=player,
            attribute_score=round(attr_score, 1) if attr_score is not None else None,
            stat_score=round(stat_score, 1) if stat_score is not None else None,
            role_score=round(role_score, 1),
            eligible=eligible,
        ))

    results.sort(key=lambda r: r.role_score, reverse=True)
    return results


def role_results_to_frame(results: list[RoleScoreResult]) -> pd.DataFrame:
    """Flatten RoleScoreResults into a DataFrame for display / export."""
    if not results:
        return pd.DataFrame(
            columns=["name", "attribute_score", "stat_score", "role_score", "eligible"]
        )
    return pd.DataFrame.from_records([
        {
            "name": r.player.name,
            "attribute_score": r.attribute_score,
            "stat_score": r.stat_score,
            "role_score": r.role_score,
            "eligible": r.eligible,
        }
        for r in results
    ]).set_index("name")
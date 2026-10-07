"""
Phase 2 — structural depth charting.

Groups the squad by position and flags thin spots. Entirely deterministic —
built on top of the Phase 1.3 `evaluate_role()` matrix, no AI involved.

Every player who can play a position is scored on each role the position
offers. Their position score is the average of their best in-possession role
and their best out-of-possession role there, so a player has to be useful in
both phases to count as starting-caliber.

A player who can play a position but has no attribute *or* stat data at all
gets `role_score == 0.0` from the evaluator (its documented "nobody to
blend" fallback). Counting that 0.0 as "this player is bad at the position"
would fabricate a judgement from an absence of data, so those players are
tracked separately as `no_data_count` and excluded from the quality/depth
counts that drive the status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fm_advisor.ingestion import Player
from fm_advisor.role_catalogue import POSITIONS
from fm_advisor.scoring import ROLE_LIBRARY, RoleDefinition, RoleScoreResult, evaluate_role

# A position score at/above this counts the player as starting-caliber there.
DEFAULT_QUALITY_THRESHOLD = 60.0
# A position score at/above this (but below quality) counts as usable squad depth.
DEFAULT_BACKUP_THRESHOLD = 45.0

CRITICAL_WEAKNESS = "Critical Weakness"
NO_COVERAGE = "No Coverage"
DEPTH_CONCERN = "Depth Concern"
HEALTHY = "Healthy"


@dataclass
class RoleFit:
    """A player's best role in one phase at one position."""
    phase: Optional[str]   # "IP" / "OOP"; None for a role outside the catalogue
    role_key: str
    role_name: str
    role_score: float


@dataclass
class PositionDepthEntry:
    """One player's contribution to a position's depth."""
    player_name: str
    natural: bool            # the position is one of the player's best positions
    score: Optional[float]   # mean of best_roles' scores; None if the player has no data at all
    tier: str                # "quality" | "backup" | "below_backup" | "no_data"
    best_roles: list[RoleFit] = field(default_factory=list)


@dataclass
class PositionDepth:
    """Depth assessment for a single position."""
    position: str
    status: str
    quality_count: int
    backup_count: int
    no_data_count: int
    entries: list[PositionDepthEntry] = field(default_factory=list)


def _tier(score: float, quality_threshold: float, backup_threshold: float) -> str:
    if score >= quality_threshold:
        return "quality"
    if score >= backup_threshold:
        return "backup"
    return "below_backup"


def _entry(
    player: Player,
    position: str,
    results: list[tuple[RoleDefinition, RoleScoreResult]],
    quality_threshold: float,
    backup_threshold: float,
) -> PositionDepthEntry:
    natural = position in player.best_positions
    has_data = any(
        r.attribute_score is not None or r.stat_score is not None for _, r in results
    )
    if not has_data:
        return PositionDepthEntry(player.name, natural, None, "no_data")

    # Best role per phase, in the order the phases first appear.
    best: dict[Optional[str], tuple[RoleDefinition, RoleScoreResult]] = {}
    for role, result in results:
        phase = role.phase.value if role.phase is not None else None
        if phase not in best or result.role_score > best[phase][1].role_score:
            best[phase] = (role, result)

    best_roles = [
        RoleFit(phase, role.key, role.display_name, result.role_score)
        for phase, (role, result) in best.items()
    ]
    score = round(sum(fit.role_score for fit in best_roles) / len(best_roles), 1)
    return PositionDepthEntry(
        player.name, natural, score, _tier(score, quality_threshold, backup_threshold), best_roles
    )


def _status_for(quality_count: int, backup_count: int, eligible_with_data: int) -> str:
    if eligible_with_data == 0:
        # Either nobody plays this position at all, or everyone who does has
        # no scoreable data yet — neither is "the players here are weak", so
        # this is surfaced distinctly rather than as a Critical Weakness.
        return NO_COVERAGE
    if quality_count >= 2:
        return HEALTHY
    if quality_count + backup_count >= 2:
        return DEPTH_CONCERN
    return CRITICAL_WEAKNESS


def build_depth_chart(
    players: list[Player],
    roles: Optional[list[RoleDefinition]] = None,
    quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
    backup_threshold: float = DEFAULT_BACKUP_THRESHOLD,
) -> list[PositionDepth]:
    """
    Assess squad depth for each position covered by `roles` (defaults to the
    full ROLE_LIBRARY, i.e. every FM26 position). A position is "Healthy" with
    >=2 quality-tier players, "Depth Concern" with fewer than 2 quality but
    >=2 counting backup-tier too, "Critical Weakness" with fewer than 2 total,
    and "No Coverage" if nobody who can play there has any scoreable data.
    """
    role_list = roles if roles is not None else list(ROLE_LIBRARY.values())

    # Score each role once, then share the results across its positions.
    results_by_role: dict[str, dict[int, RoleScoreResult]] = {
        role.key: {id(r.player): r for r in evaluate_role(players, role, only_eligible=True)}
        for role in role_list
    }

    covered = {pos for role in role_list for pos in role.eligible_positions}
    positions = [p for p in POSITIONS if p in covered] + sorted(covered - set(POSITIONS))

    chart: list[PositionDepth] = []
    for position in positions:
        roles_here = [role for role in role_list if position in role.eligible_positions]
        entries = [
            _entry(
                player,
                position,
                [(role, results_by_role[role.key][id(player)]) for role in roles_here],
                quality_threshold,
                backup_threshold,
            )
            for player in players
            if position in player.positions
        ]
        entries.sort(key=lambda e: (e.score is None, -(e.score or 0.0)))

        quality_count = sum(1 for e in entries if e.tier == "quality")
        backup_count = sum(1 for e in entries if e.tier == "backup")
        no_data_count = sum(1 for e in entries if e.tier == "no_data")

        chart.append(PositionDepth(
            position=position,
            status=_status_for(quality_count, backup_count, len(entries) - no_data_count),
            quality_count=quality_count,
            backup_count=backup_count,
            no_data_count=no_data_count,
            entries=entries,
        ))

    return chart

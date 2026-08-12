"""
Phase 2 — structural depth charting.

Groups the squad by role (each role implies the position(s) it covers) and
flags thin spots. Entirely deterministic — built on top of the Phase 1.3
`evaluate_role()` matrix, no AI involved.

A player who is eligible for a role but has no attribute *or* stat data at
all gets `role_score == 0.0` from the evaluator (its documented "nobody to
blend" fallback). Counting that 0.0 as "this player is bad at the role"
would fabricate a judgement from an absence of data, so those players are
tracked separately as `no_data_count` / `no_data_players` and excluded from
the quality/depth counts that drive the status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fm_advisor.ingestion import Player
from fm_advisor.scoring import ROLE_LIBRARY, RoleDefinition, RoleScoreResult, evaluate_role

# A role_score at/above this counts the player as starting-caliber for the role.
DEFAULT_QUALITY_THRESHOLD = 60.0
# A role_score at/above this (but below quality) counts as usable squad depth.
DEFAULT_BACKUP_THRESHOLD = 45.0

CRITICAL_WEAKNESS = "Critical Weakness"
NO_COVERAGE = "No Coverage"
DEPTH_CONCERN = "Depth Concern"
HEALTHY = "Healthy"


@dataclass
class PositionDepthEntry:
    """One eligible player's contribution to a role's depth."""
    player_name: str
    role_score: Optional[float]  # None if the player has no attribute/stat data at all
    tier: str  # "quality" | "backup" | "below_backup" | "no_data"


@dataclass
class PositionDepth:
    """Depth assessment for a single role (and the position(s) it covers)."""
    role_key: str
    role_display_name: str
    status: str
    quality_count: int
    backup_count: int
    no_data_count: int
    entries: list[PositionDepthEntry] = field(default_factory=list)


def _classify(
    results: list[RoleScoreResult],
    quality_threshold: float,
    backup_threshold: float,
) -> list[PositionDepthEntry]:
    entries: list[PositionDepthEntry] = []
    for r in results:
        has_data = r.attribute_score is not None or r.stat_score is not None
        if not has_data:
            entries.append(PositionDepthEntry(r.player.name, None, "no_data"))
        elif r.role_score >= quality_threshold:
            entries.append(PositionDepthEntry(r.player.name, r.role_score, "quality"))
        elif r.role_score >= backup_threshold:
            entries.append(PositionDepthEntry(r.player.name, r.role_score, "backup"))
        else:
            entries.append(PositionDepthEntry(r.player.name, r.role_score, "below_backup"))
    return entries


def _status_for(quality_count: int, backup_count: int, eligible_with_data: int) -> str:
    if eligible_with_data == 0:
        # Either nobody plays this role at all, or everyone who does has no
        # scoreable data yet — neither is "the players here are weak", so
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
    Assess squad depth for each role in `roles` (defaults to the full
    ROLE_LIBRARY). A role is "Healthy" with >=2 quality-tier players,
    "Depth Concern" with fewer than 2 quality but >=2 counting backup-tier
    too, "Critical Weakness" with fewer than 2 total, and "No Coverage" if
    nobody eligible has any scoreable data at all.
    """
    role_list = roles if roles is not None else list(ROLE_LIBRARY.values())

    chart: list[PositionDepth] = []
    for role in role_list:
        results = evaluate_role(players, role, only_eligible=True)
        entries = _classify(results, quality_threshold, backup_threshold)

        quality_count = sum(1 for e in entries if e.tier == "quality")
        backup_count = sum(1 for e in entries if e.tier == "backup")
        no_data_count = sum(1 for e in entries if e.tier == "no_data")
        eligible_with_data = len(entries) - no_data_count

        chart.append(PositionDepth(
            role_key=role.key,
            role_display_name=role.display_name,
            status=_status_for(quality_count, backup_count, eligible_with_data),
            quality_count=quality_count,
            backup_count=backup_count,
            no_data_count=no_data_count,
            entries=entries,
        ))

    return chart

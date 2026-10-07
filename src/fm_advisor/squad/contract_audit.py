"""
Phase 2 — contract expiry auditing.

Flags starting-caliber players (position score at/above the depth chart's
"quality" threshold at one or more positions) whose contract runs out soon.
Deterministic, built on the depth chart.

A player with no parsed `contract_expiry` (blank/unrecognised export field)
is *not* flagged — `months_until_contract_expiry()` returns None for them,
and treating "unknown" as "urgent" would be exactly the fabricated-baseline
mistake this project explicitly avoids elsewhere. They're still reported
separately (`unknown_contract_count` / `unknown_contract_players`) so the
gap in data is visible rather than silently dropped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from fm_advisor.ingestion import Player
from fm_advisor.scoring import RoleDefinition

from .depth_chart import DEFAULT_QUALITY_THRESHOLD, PositionDepth, build_depth_chart

DEFAULT_WARNING_MONTHS = 12


@dataclass
class ContractFlag:
    """A starting-caliber player whose contract expires soon."""
    player_name: str
    positions: list[str]     # every position where they are starting-caliber
    best_score: float        # their highest position score among those
    contract_expiry: Optional[date]
    months_until_expiry: int


@dataclass
class ContractAuditResult:
    flags: list[ContractFlag] = field(default_factory=list)
    unknown_contract_count: int = 0
    unknown_contract_players: list[str] = field(default_factory=list)


def audit_contracts(
    players: list[Player],
    roles: Optional[list[RoleDefinition]] = None,
    quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
    warning_months: int = DEFAULT_WARNING_MONTHS,
    reference: Optional[date] = None,
    depth_chart: Optional[list[PositionDepth]] = None,
) -> ContractAuditResult:
    """
    Flag every starting-caliber player whose contract expires within
    `warning_months`, once per player. Pass `depth_chart` to reuse one already
    built with the same thresholds; otherwise it is built from `roles`.
    """
    if depth_chart is None:
        depth_chart = build_depth_chart(players, roles=roles, quality_threshold=quality_threshold)

    # player name -> [(position, score)] for every position they start at
    starting: dict[str, list[tuple[str, float]]] = {}
    for depth in depth_chart:
        for entry in depth.entries:
            if entry.tier == "quality":
                starting.setdefault(entry.player_name, []).append((depth.position, entry.score))

    flags: list[ContractFlag] = []
    unknown: list[str] = []
    for player in players:
        spots = starting.get(player.name)
        if not spots:
            continue

        months = player.months_until_contract_expiry(reference)
        if months is None:
            unknown.append(player.name)
            continue

        if months < warning_months:
            flags.append(ContractFlag(
                player_name=player.name,
                positions=[position for position, _ in spots],
                best_score=max(score for _, score in spots),
                contract_expiry=player.contract_expiry,
                months_until_expiry=months,
            ))

    flags.sort(key=lambda f: f.months_until_expiry)
    return ContractAuditResult(
        flags=flags,
        unknown_contract_count=len(unknown),
        unknown_contract_players=sorted(unknown),
    )

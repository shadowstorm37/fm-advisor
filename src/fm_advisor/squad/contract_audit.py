"""
Phase 2 — contract expiry auditing.

Flags starting-caliber players (role_score at/above the depth chart's
"quality" threshold for at least one role they're eligible for) whose
contract runs out soon. Deterministic, built on `evaluate_role()`.

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
from fm_advisor.scoring import ROLE_LIBRARY, RoleDefinition, evaluate_role

from .depth_chart import DEFAULT_QUALITY_THRESHOLD

DEFAULT_WARNING_MONTHS = 12


@dataclass
class ContractFlag:
    """A starting-caliber player whose contract expires soon."""
    player_name: str
    role_key: str
    role_display_name: str
    role_score: float
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
) -> ContractAuditResult:
    """
    Scan every role for starting-caliber players (role_score >=
    quality_threshold) and flag the ones whose contract expires within
    `warning_months`. A player can appear once per qualifying role.
    """
    role_list = roles if roles is not None else list(ROLE_LIBRARY.values())

    flags: list[ContractFlag] = []
    seen_unknown: set[str] = set()

    for role in role_list:
        results = evaluate_role(players, role, only_eligible=True)
        for r in results:
            if r.role_score < quality_threshold:
                continue

            months = r.player.months_until_contract_expiry(reference)
            if months is None:
                seen_unknown.add(r.player.name)
                continue

            if months < warning_months:
                flags.append(ContractFlag(
                    player_name=r.player.name,
                    role_key=role.key,
                    role_display_name=role.display_name,
                    role_score=r.role_score,
                    contract_expiry=r.player.contract_expiry,
                    months_until_expiry=months,
                ))

    flags.sort(key=lambda f: f.months_until_expiry)
    return ContractAuditResult(
        flags=flags,
        unknown_contract_count=len(seen_unknown),
        unknown_contract_players=sorted(seen_unknown),
    )

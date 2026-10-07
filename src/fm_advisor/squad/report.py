"""
Phase 2 deliverable — combine the depth chart and contract audit into one
JSON-serializable package. Still zero AI budget spent: everything here is a
reshape of `depth_chart.py` / `contract_audit.py` output.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Optional

from fm_advisor.ingestion import Player
from fm_advisor.scoring import RoleDefinition

from .contract_audit import DEFAULT_WARNING_MONTHS, audit_contracts
from .depth_chart import (
    DEFAULT_BACKUP_THRESHOLD,
    DEFAULT_QUALITY_THRESHOLD,
    build_depth_chart,
)


def _json_safe(value):
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    return value


def build_squad_report(
    players: list[Player],
    game_date: date,
    roles: Optional[list[RoleDefinition]] = None,
    quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
    backup_threshold: float = DEFAULT_BACKUP_THRESHOLD,
    warning_months: int = DEFAULT_WARNING_MONTHS,
) -> dict:
    """
    Build the combined Phase 2 report: squad depth by position plus contract
    urgency flags for starting-caliber players, measured from `game_date`
    (the date in the save, which no export carries). Returns a plain dict of
    JSON-safe primitives (dates become ISO strings) ready for
    `json.dumps()` or the FastAPI layer.
    """
    depth_chart = build_depth_chart(
        players, roles=roles, quality_threshold=quality_threshold, backup_threshold=backup_threshold
    )
    contract_result = audit_contracts(
        players,
        reference=game_date,
        warning_months=warning_months,
        depth_chart=depth_chart,
    )

    return {
        "squad_size": len(players),
        "game_date": game_date.isoformat(),
        "thresholds": {
            "quality": quality_threshold,
            "backup": backup_threshold,
            "contract_warning_months": warning_months,
        },
        "depth_chart": [_json_safe(asdict(p)) for p in depth_chart],
        "contract_flags": [_json_safe(asdict(f)) for f in contract_result.flags],
        "unknown_contract_count": contract_result.unknown_contract_count,
        "unknown_contract_players": contract_result.unknown_contract_players,
    }

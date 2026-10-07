"""
Phase 4.2 — recruitment mapping.

Cross-references a large scouted-player export against the roles the Phase 2
report flags as "Critical Weakness", ranking candidates by role score per
pound of transfer value. Deterministic, like everything upstream of the LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fm_advisor.ingestion import Player


@dataclass
class TransferSuggestion:
    player_name: str
    role_key: str
    role_score: float
    transfer_value_high: Optional[float]
    value_ratio: Optional[float]   # role_score per £1M; None if value unknown


def shortlist_for_weaknesses(
    report: dict,
    scouted: list[Player],
    per_role: int = 5,
) -> list[TransferSuggestion]:
    """Top `per_role` scouted candidates for each critically weak role in `report`."""
    raise NotImplementedError("Phase 4.2: recruitment shortlist")

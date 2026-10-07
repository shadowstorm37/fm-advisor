"""
fm26_ingest - Phase 1 ingestion engine for the FM26 Tactical & Recruitment Advisor.

Public API:
    load_squad(path)        -> LoadResult (players + numeric frame + diagnostics)
    Player                  -> validated per-player schema
    squad_to_frame(players) -> wide numeric DataFrame for the math layer
"""

from .cleaning import (
    clean_attribute,
    clean_money_range,
    clean_number,
    clean_percentage,
    clean_stat,
    clean_wage,
    parse_age,
    parse_contract_date,
    parse_positions,
)
from .ingestion import (
    ColumnMap,
    LoadResult,
    load_squad,
    read_raw_frame,
    resolve_columns,
    squad_to_frame,
)
from .models import ATTRIBUTE_NAMES, STATUS_FLAG_LABELS, Player, normalize_header

__all__ = [
    "load_squad",
    "LoadResult",
    "ColumnMap",
    "read_raw_frame",
    "resolve_columns",
    "squad_to_frame",
    "Player",
    "ATTRIBUTE_NAMES",
    "STATUS_FLAG_LABELS",
    "normalize_header",
    "clean_attribute",
    "clean_number",
    "clean_percentage",
    "clean_money_range",
    "clean_stat",
    "clean_wage",
    "parse_age",
    "parse_positions",
    "parse_contract_date",
]

__version__ = "0.1.0"
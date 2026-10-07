"""
Structured player schema + column alias registry (Task 1.2).

The BepInEx export view is user-configurable, so column headers vary between
setups. Rather than hard-code positions in the file, we normalise each header
and resolve it against two disjoint alias registries:

  * ATTRIBUTE_ALIASES - the ~48 FM attributes (full name + FMRTE 3-letter code)
  * PROFILE_ALIASES   - identity / contract metadata

Anything unrecognised is preserved untouched in Player.extra so no data is lost.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


def normalize_header(header: str) -> str:
    """Lower-case and strip everything but alphanumerics for robust matching."""
    return re.sub(r"[^a-z0-9]", "", str(header).strip().lower())


# Canonical attribute name -> every header spelling we accept.
# Canonical names use FM's full attribute names so the Phase 1.3 role formulas
# (e.g. Tackling * 0.3 + Heading * 0.3 ...) read naturally.
_ATTRIBUTE_SPELLINGS: dict[str, tuple[str, ...]] = {
    # Technical
    "Corners": ("cor",),
    "Crossing": ("cro",),
    "Dribbling": ("dri",),
    "Finishing": ("fin",),
    "First Touch": ("fir", "firsttouch"),
    "Free Kick Taking": ("fre", "freekicks", "freekicktaking"),
    "Heading": ("hea",),
    "Long Shots": ("lon", "longshots"),
    "Long Throws": ("lth", "longthrows"),
    "Marking": ("mar",),
    "Passing": ("pas",),
    "Penalty Taking": ("pen", "penalties", "penaltytaking"),
    "Tackling": ("tck", "tak"),
    "Technique": ("tec", "tech"),
    # Mental
    "Aggression": ("agg",),
    "Anticipation": ("ant",),
    "Bravery": ("bra",),
    "Composure": ("cmp",),
    "Concentration": ("cnt", "con"),
    "Decisions": ("dec",),
    "Determination": ("det",),
    "Flair": ("fla",),
    "Leadership": ("ldr", "lead"),
    "Off The Ball": ("otb", "offtheball"),
    "Positioning": ("pos",),
    "Teamwork": ("tea", "team"),
    "Vision": ("vis",),
    "Work Rate": ("wor", "workrate"),
    # Physical
    "Acceleration": ("acc",),
    "Agility": ("agi",),
    "Balance": ("bal",),
    "Jumping Reach": ("jum", "jumping", "jumpingreach"),
    "Natural Fitness": ("nat", "naturalfitness"),
    "Pace": ("pac",),
    "Stamina": ("sta",),
    "Strength": ("str",),
    # Goalkeeping
    "Aerial Reach": ("aer", "aerialreach"),
    "Command Of Area": ("cmd", "commandofarea"),
    "Communication": ("com", "comm"),
    "Eccentricity": ("ecc",),
    "Handling": ("han",),
    "Kicking": ("kic",),
    "One On Ones": ("1v1", "oneonones", "1on1s"),
    "Punching": ("pun", "punchingtendency"),
    "Reflexes": ("ref",),
    "Rushing Out": ("tro", "rushingout", "rushingouttendency"),
    "Throwing": ("thr",),
}

# Profile fields. NOTE: aliases here are deliberately kept disjoint from the
# attribute codes above (e.g. "nat" is Natural Fitness, so nationality only
# accepts "nation"/"nationality"; "pos" is Positioning, so the position column
# only accepts "position"/"positions").
_PROFILE_SPELLINGS: dict[str, tuple[str, ...]] = {
    "name": ("name", "player", "playername", "fullname"),
    "age": ("age",),
    "position_raw": ("position", "positions", "playablepositions"),
    "best_position_raw": ("bestpos", "bestposition"),
    "best_role": ("bestrole",),
    "playing_time": ("playingtime",),
    "club": ("club", "team", "currentclub"),
    "nationality": ("nationality", "nation", "nat1"),
    "contract_expiry_raw": (
        "expires", "expiry", "expirydate",
        "contract", "contractexpiry", "contractexpires", "contractexpiration",
    ),
    "division": ("division", "league", "competition"),
    "based_in": ("basedin", "country"),
    "status_raw": ("inf", "info", "status"),
    "transfer_value_raw": ("transfervalue", "value", "marketvalue"),
    "minutes": ("minutes", "mins", "minutesplayed"),
    "wage_raw": ("wage", "wages", "salary"),
}

# The "Inf" column's short codes.
STATUS_FLAG_LABELS: dict[str, str] = {
    "Wnt": "Wanted (transfer/wage listed)",
    "Inj": "Injured",
    "Yth": "Youth prospect",
    "Loa": "Out on loan",
    "ESC": "Release clause active",
}


def _build_lookup(spellings: dict[str, tuple[str, ...]], include_key: bool) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, aliases in spellings.items():
        if include_key:
            lookup[normalize_header(canonical)] = canonical
        for alias in aliases:
            lookup[normalize_header(alias)] = canonical
    return lookup


# normalized-header -> canonical-name
ATTRIBUTE_LOOKUP = _build_lookup(_ATTRIBUTE_SPELLINGS, include_key=True)
PROFILE_LOOKUP = _build_lookup(_PROFILE_SPELLINGS, include_key=False)

# All canonical attribute names, in a stable order (useful for DataFrame cols).
ATTRIBUTE_NAMES: tuple[str, ...] = tuple(_ATTRIBUTE_SPELLINGS.keys())


class Player(BaseModel):
    """A single cleaned, validated squad member."""

    model_config = ConfigDict(extra="forbid")

    name: str
    age: Optional[int] = None
    positions: list[str] = Field(default_factory=list)        # everywhere they can play
    position_raw: Optional[str] = None
    best_positions: list[str] = Field(default_factory=list)   # their natural spot
    best_position_raw: Optional[str] = None
    best_role: Optional[str] = None
    playing_time: Optional[str] = None                        # squad status, e.g. "Regular Starter"
    contract_expiry: Optional[date] = None
    contract_expiry_raw: Optional[str] = None
    wage_raw: Optional[str] = None
    wage_weekly: Optional[float] = None
    club: Optional[str] = None
    nationality: Optional[str] = None
    division: Optional[str] = None
    based_in: Optional[str] = None

    # Attribute (1-20 ability) view
    attributes: dict[str, int] = Field(default_factory=dict)

    # Status, value and performance output
    status_raw: Optional[str] = None
    status_flags: list[str] = Field(default_factory=list)
    transfer_value_raw: Optional[str] = None
    transfer_value_low: Optional[float] = None
    transfer_value_high: Optional[float] = None
    minutes: Optional[int] = None
    stats: dict[str, float] = Field(default_factory=dict)

    # Any column we could not map (transfer value, personality, morale, ...).
    extra: dict[str, str] = Field(default_factory=dict)

    def attr(self, name: str, default: int = 1) -> int:
        """Fetch an attribute by canonical name with a safe default."""
        return self.attributes.get(name, default)

    def stat(self, name: str, default: Optional[float] = None) -> Optional[float]:
        """Fetch a performance stat by its export column name."""
        return self.stats.get(name, default)

    def months_until_contract_expiry(self, reference: Optional[date] = None) -> Optional[int]:
        """Whole months from `reference` (default today) to contract expiry."""
        if self.contract_expiry is None:
            return None
        ref = reference or date.today()
        return (self.contract_expiry.year - ref.year) * 12 + (
            self.contract_expiry.month - ref.month
        )

    def is_goalkeeper(self) -> bool:
        return "GK" in self.positions

    def has_attributes(self) -> bool:
        return bool(self.attributes)

    def has_stats(self) -> bool:
        return bool(self.stats)
"""
Role definitions for the Task 1.3 matrix evaluator.

Each RoleDefinition pairs attribute weights with a small set of *relevant*
performance stats from the combined export, so a role score can be blended:
rated ability (what a player is capable of) adjusted by observed output (what
they've actually done on the pitch).

The library covers every role in `role_catalogue` — one definition per phase
and code, shared by every position that offers it (Winger in possession is
the same definition at M (R) and AM (L)).

DRAFT WEIGHTS: the game does not publish which attributes drive each role, so
the lists in `_DRAFT` are a football-sense first pass, not FM26's own numbers.
Each role names its "key" attributes and stats, which count double, and its
"support" ones, which count once. Edit the lists freely; weights are
normalised from them automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fm_advisor.role_catalogue import ROLE_CATALOGUE, Phase

KEY_WEIGHT = 2.0
SUPPORT_WEIGHT = 1.0

# Stats where a lower figure is the good outcome.
LOWER_IS_BETTER = frozenset({"Possession Lost per 90"})


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
    code / phase       : the role's FM26 catalogue code and phase; None for
                          an ad-hoc role that is not in the catalogue.
    """
    key: str
    display_name: str
    attribute_weights: dict[str, float]
    eligible_positions: tuple[str, ...]
    stat_weights: tuple[StatWeight, ...] = field(default_factory=tuple)
    stat_blend: float = 0.35
    code: Optional[str] = None
    phase: Optional[Phase] = None

    def __post_init__(self) -> None:
        total = round(sum(self.attribute_weights.values()), 6)
        if total != 1.0:
            raise ValueError(
                f"{self.key}: attribute_weights must sum to 1.0, got {total}"
            )
        if not (0.0 <= self.stat_blend <= 1.0):
            raise ValueError(f"{self.key}: stat_blend must be in [0, 1]")


@dataclass(frozen=True)
class _Draft:
    key: tuple[str, ...]
    support: tuple[str, ...]
    stats_key: tuple[str, ...] = ()
    stats_support: tuple[str, ...] = ()


def _d(key: str, support: str, stats_key: str = "", stats_support: str = "") -> _Draft:
    """Build a draft from comma-separated name lists."""
    split = lambda text: tuple(part.strip() for part in text.split(",") if part.strip())
    return _Draft(split(key), split(support), split(stats_key), split(stats_support))


IP, OOP = Phase.IP, Phase.OOP

# Stat bundles shared by several out-of-possession roles.
_PRESSING = ("Pres C/90, Possession Won per 90", "Pres A/90, Tackles Completed per 90, Dist/90")
_TRACKING = ("Tackles Completed per 90, Possession Won per 90, Dist/90", "Interceptions per 90, Tackle Completion Percentage")
_SCREENING = ("Interceptions per 90, Blk/90", "Possession Won per 90, Tackle Completion Percentage")

_DRAFT: dict[tuple[Phase, str], _Draft] = {
    # --- Goalkeeper ----------------------------------------------------------
    # In possession a keeper is judged on distribution; shot-stopping lives in
    # the out-of-possession roles. The export has no save stats, so the OOP
    # keeper roles are scored on attributes alone.
    (IP, "GK"): _d(
        "Kicking, Throwing, Decisions",
        "First Touch, Passing, Composure, Concentration",
        "Pass Completion Percentage", "Passes Completed per 90"),
    (IP, "BGK"): _d(
        "Passing, First Touch, Kicking, Composure",
        "Vision, Throwing, Decisions, Technique",
        "Pass Completion Percentage, Progressive Passes per 90", "Passes Completed per 90"),
    (IP, "NGK"): _d(
        "Kicking, Throwing",
        "Decisions, Concentration, Composure"),
    (OOP, "GK"): _d(
        "Reflexes, Handling, One On Ones, Positioning, Aerial Reach",
        "Command Of Area, Communication, Concentration, Agility, Anticipation"),
    (OOP, "SK"): _d(
        "Rushing Out, One On Ones, Anticipation, Reflexes, Acceleration",
        "Handling, Positioning, Decisions, Pace, Composure, Command Of Area"),
    (OOP, "LHK"): _d(
        "Reflexes, Handling, Positioning, Aerial Reach, Command Of Area",
        "Communication, Concentration, Agility, Jumping Reach, One On Ones"),

    # --- Centre-back ---------------------------------------------------------
    (IP, "CB"): _d(
        "Passing, Composure, Decisions, First Touch",
        "Positioning, Anticipation, Concentration, Technique",
        "Pass Completion Percentage", "Passes Completed per 90, Possession Lost per 90"),
    (IP, "ACB"): _d(
        "Passing, Dribbling, Composure, First Touch, Decisions",
        "Technique, Vision, Pace, Acceleration, Anticipation",
        "Progressive Passes per 90, Dribbles per 90", "Pass Completion Percentage, Possession Lost per 90"),
    (IP, "BCB"): _d(
        "Passing, Vision, Composure, Technique, First Touch",
        "Decisions, Anticipation, Concentration",
        "Progressive Passes per 90, Pass Completion Percentage",
        "Passes Completed per 90, Key Passes per 90, Possession Lost per 90"),
    (IP, "NCB"): _d(
        "Heading, Strength, Bravery, Concentration, Positioning",
        "Jumping Reach, Decisions, Tackling",
        "Clearances per 90, Possession Lost per 90", "Headers Won Percentage"),
    (OOP, "CB"): _d(
        "Tackling, Marking, Positioning, Heading, Jumping Reach, Strength",
        "Anticipation, Concentration, Bravery, Decisions, Pace",
        "Tackle Completion Percentage, Headers Won Percentage, Interceptions per 90",
        "Clearances per 90, Blk/90"),
    (OOP, "SCB"): _d(
        "Tackling, Aggression, Bravery, Anticipation, Strength, Heading",
        "Marking, Positioning, Jumping Reach, Decisions, Acceleration",
        "Tackles Completed per 90, Possession Won per 90, Headers Won Percentage",
        "Tackle Completion Percentage, Interceptions per 90"),
    (OOP, "CCB"): _d(
        "Positioning, Anticipation, Pace, Acceleration, Concentration, Marking",
        "Tackling, Decisions, Composure, Heading",
        "Interceptions per 90, Clearances per 90", "Blk/90, Tackle Completion Percentage"),
    (OOP, "WCB"): _d(
        "Tackling, Marking, Positioning, Pace, Acceleration, Stamina",
        "Heading, Strength, Anticipation, Agility, Work Rate",
        "Tackle Completion Percentage, Interceptions per 90",
        "Headers Won Percentage, Tackles Completed per 90, Dist/90"),
    (OOP, "SWD"): _d(
        "Tackling, Aggression, Bravery, Anticipation, Pace, Acceleration",
        "Marking, Strength, Stamina, Positioning, Agility",
        "Tackles Completed per 90, Possession Won per 90",
        "Tackle Completion Percentage, Interceptions per 90, Dist/90"),
    (OOP, "CWD"): _d(
        "Positioning, Anticipation, Pace, Acceleration, Concentration, Marking",
        "Tackling, Stamina, Agility, Decisions",
        "Interceptions per 90, Clearances per 90", "Blk/90, Tackle Completion Percentage, Dist/90"),

    # --- Full-back and wing-back ---------------------------------------------
    (IP, "FB"): _d(
        "Passing, Crossing, First Touch, Decisions, Teamwork",
        "Technique, Stamina, Pace, Composure",
        "Pass Completion Percentage, Crosses Completed per 90",
        "Progressive Passes per 90, Possession Lost per 90"),
    (IP, "WB"): _d(
        "Crossing, Dribbling, Pace, Acceleration, Stamina, Off The Ball",
        "Technique, First Touch, Passing, Work Rate",
        "Crosses Completed per 90, Dribbles per 90",
        "Crosses Completed Ratio, xA/90, Progressive Passes per 90"),
    (IP, "AWB"): _d(
        "Crossing, Dribbling, Off The Ball, Pace, Acceleration, Stamina",
        "Technique, Flair, First Touch, Work Rate, Anticipation",
        "Crosses Completed per 90, xA/90, Dribbles per 90",
        "Chances Created per 90, Key Passes per 90"),
    (IP, "IWB"): _d(
        "Passing, First Touch, Decisions, Composure, Technique, Vision",
        "Teamwork, Anticipation, Off The Ball, Agility",
        "Pass Completion Percentage, Progressive Passes per 90",
        "Passes Completed per 90, Key Passes per 90, Possession Lost per 90"),
    (IP, "IFB"): _d(
        "Passing, Composure, Decisions, Positioning, First Touch",
        "Concentration, Anticipation, Technique, Strength",
        "Pass Completion Percentage", "Passes Completed per 90, Possession Lost per 90"),
    (IP, "PWB"): _d(
        "Passing, Vision, Technique, First Touch, Crossing, Decisions",
        "Dribbling, Composure, Off The Ball, Flair",
        "Key Passes per 90, Chances Created per 90, Progressive Passes per 90",
        "xA/90, Pass Completion Percentage"),
    (OOP, "FB"): _d(
        "Tackling, Marking, Positioning, Pace, Concentration",
        "Anticipation, Acceleration, Stamina, Teamwork, Decisions",
        "Tackle Completion Percentage, Interceptions per 90", "Tackles Completed per 90, Blk/90"),
    (OOP, "PFB"): _d(
        "Tackling, Aggression, Work Rate, Stamina, Acceleration, Anticipation",
        "Pace, Bravery, Marking, Teamwork",
        *_PRESSING),
    (OOP, "HFB"): _d(
        "Positioning, Marking, Concentration, Tackling, Decisions",
        "Anticipation, Strength, Heading, Teamwork",
        "Tackle Completion Percentage, Interceptions per 90, Clearances per 90", "Blk/90"),
    (OOP, "WB"): _d(
        "Tackling, Marking, Positioning, Stamina, Pace, Work Rate",
        "Anticipation, Acceleration, Concentration, Teamwork",
        "Tackle Completion Percentage, Interceptions per 90", "Tackles Completed per 90, Dist/90"),
    (OOP, "PWB"): _d(
        "Tackling, Aggression, Work Rate, Stamina, Acceleration, Anticipation",
        "Pace, Bravery, Marking, Teamwork",
        *_PRESSING),
    (OOP, "HWB"): _d(
        "Positioning, Marking, Concentration, Tackling, Stamina",
        "Anticipation, Decisions, Teamwork, Strength",
        "Tackle Completion Percentage, Interceptions per 90, Clearances per 90", "Blk/90"),

    # --- Defensive midfield --------------------------------------------------
    (IP, "DM"): _d(
        "Passing, First Touch, Decisions, Composure, Teamwork",
        "Positioning, Concentration, Technique, Anticipation",
        "Pass Completion Percentage, Passes Completed per 90",
        "Possession Lost per 90, Progressive Passes per 90"),
    (IP, "DLP"): _d(
        "Passing, Vision, Technique, First Touch, Composure, Decisions",
        "Anticipation, Teamwork, Balance",
        "Progressive Passes per 90, Pass Completion Percentage, Key Passes per 90",
        "Passes Completed per 90, Chances Created per 90"),
    (IP, "BBM"): _d(
        "Stamina, Work Rate, Off The Ball, Passing, Teamwork",
        "Dribbling, First Touch, Long Shots, Finishing, Acceleration, Decisions",
        "Dist/90, Progressive Passes per 90",
        "Shot/90, xG/90, Dribbles per 90, Pass Completion Percentage"),
    (IP, "HB"): _d(
        "Positioning, Passing, Composure, Decisions, Concentration",
        "First Touch, Anticipation, Teamwork, Strength",
        "Pass Completion Percentage", "Passes Completed per 90, Possession Lost per 90"),
    (IP, "BBP"): _d(
        "Passing, Vision, Stamina, Work Rate, Technique, Off The Ball",
        "First Touch, Decisions, Dribbling, Composure",
        "Progressive Passes per 90, Key Passes per 90, Dist/90",
        "Chances Created per 90, Pass Completion Percentage"),
    (OOP, "DM"): _d(
        "Tackling, Positioning, Anticipation, Marking, Concentration, Teamwork",
        "Work Rate, Stamina, Strength, Decisions",
        "Interceptions per 90, Tackle Completion Percentage, Possession Won per 90",
        "Tackles Completed per 90"),
    (OOP, "DDM"): _d(
        "Positioning, Marking, Heading, Concentration, Tackling",
        "Jumping Reach, Strength, Anticipation, Decisions",
        "Interceptions per 90, Clearances per 90, Headers Won Percentage",
        "Tackle Completion Percentage, Blk/90"),
    (OOP, "SDM"): _d(
        "Positioning, Anticipation, Concentration, Decisions, Tackling",
        "Marking, Teamwork, Composure, Strength",
        *_SCREENING),

    # --- Central midfield ----------------------------------------------------
    (IP, "CM"): _d(
        "Passing, First Touch, Decisions, Teamwork, Technique",
        "Vision, Off The Ball, Composure, Stamina",
        "Pass Completion Percentage, Progressive Passes per 90",
        "Passes Completed per 90, Key Passes per 90, Possession Lost per 90"),
    (IP, "AM"): _d(
        "Off The Ball, Passing, Technique, First Touch, Vision, Decisions",
        "Long Shots, Finishing, Dribbling, Composure, Anticipation, Flair",
        "Key Passes per 90, Chances Created per 90, xA/90",
        "xG/90, Shot/90, Dribbles per 90"),
    (IP, "AP"): _d(
        "Passing, Vision, Technique, First Touch, Composure, Decisions",
        "Flair, Dribbling, Off The Ball, Anticipation, Agility",
        "Key Passes per 90, Chances Created per 90, xA/90",
        "Progressive Passes per 90, Pass Completion Percentage"),
    (IP, "CHM"): _d(
        "Off The Ball, Stamina, Work Rate, Acceleration, Dribbling, Passing",
        "First Touch, Technique, Crossing, Anticipation, Pace",
        "Dribbles per 90, Progressive Passes per 90, Dist/90",
        "xA/90, Crosses Completed per 90, Key Passes per 90"),
    (IP, "MPM"): _d(
        "Passing, Vision, Technique, First Touch, Composure, Decisions",
        "Teamwork, Anticipation, Balance, Off The Ball",
        "Progressive Passes per 90, Passes Completed per 90, Pass Completion Percentage",
        "Key Passes per 90, Chances Created per 90"),
    (OOP, "CM"): _d(
        "Tackling, Positioning, Work Rate, Teamwork, Stamina",
        "Anticipation, Marking, Concentration, Decisions",
        "Possession Won per 90, Tackle Completion Percentage",
        "Interceptions per 90, Tackles Completed per 90, Dist/90"),
    (OOP, "PCM"): _d(
        "Work Rate, Stamina, Aggression, Tackling, Anticipation, Acceleration",
        "Teamwork, Bravery, Pace, Determination",
        *_PRESSING),
    (OOP, "SCM"): _d(
        "Positioning, Anticipation, Concentration, Tackling, Decisions",
        "Marking, Teamwork, Strength, Composure",
        *_SCREENING),

    # --- Wide midfield -------------------------------------------------------
    (IP, "WM"): _d(
        "Passing, Crossing, Teamwork, Work Rate, Decisions, First Touch",
        "Stamina, Technique, Off The Ball, Dribbling",
        "Crosses Completed per 90, Pass Completion Percentage",
        "Key Passes per 90, Progressive Passes per 90"),
    (IP, "W"): _d(
        "Crossing, Dribbling, Pace, Acceleration, Technique",
        "Agility, Off The Ball, First Touch, Flair, Stamina",
        "Dribbles per 90, Crosses Completed per 90, xA/90",
        "Crosses Completed Ratio, Chances Created per 90"),
    (IP, "PW"): _d(
        "Passing, Vision, Technique, First Touch, Dribbling, Decisions",
        "Composure, Flair, Crossing, Off The Ball, Agility",
        "Key Passes per 90, Chances Created per 90, xA/90",
        "Progressive Passes per 90, Dribbles per 90"),
    (IP, "IW"): _d(
        "Dribbling, Technique, Acceleration, Agility, Passing, Off The Ball",
        "First Touch, Long Shots, Vision, Pace, Composure, Flair",
        "Dribbles per 90, Key Passes per 90", "Shot/90, xG/90, xA/90"),
    (OOP, "WMF"): _d(
        "Work Rate, Teamwork, Positioning, Tackling, Stamina",
        "Marking, Anticipation, Concentration, Decisions",
        "Possession Won per 90, Tackle Completion Percentage",
        "Interceptions per 90, Dist/90"),
    (OOP, "TWM"): _d(
        "Work Rate, Stamina, Tackling, Marking, Teamwork, Pace",
        "Positioning, Anticipation, Acceleration, Concentration",
        *_TRACKING),
    (OOP, "OWM"): _d(
        "Pace, Acceleration, Off The Ball, Anticipation",
        "Dribbling, First Touch, Composure, Balance",
        "Dribbles per 90", "Goals per 90 minutes, xA/90"),

    # --- Attacking midfield (centre) -----------------------------------------
    (IP, "FR"): _d(
        "Flair, Technique, Dribbling, Vision, Off The Ball, First Touch",
        "Passing, Composure, Anticipation, Agility, Long Shots, Finishing",
        "Chances Created per 90, Dribbles per 90, xA/90",
        "xG/90, Key Passes per 90, Shot/90"),
    (IP, "SS"): _d(
        "Finishing, Off The Ball, Composure, Anticipation, Acceleration, First Touch",
        "Dribbling, Technique, Pace, Decisions, Long Shots",
        "xG/90, Goals per 90 minutes, Shot/90",
        "Conv %, Shots on Target Percentage, xA/90"),
    (OOP, "AM"): _d(
        "Work Rate, Teamwork, Positioning, Anticipation, Stamina",
        "Tackling, Decisions, Concentration, Acceleration",
        "Possession Won per 90, Pres C/90", "Pres A/90, Interceptions per 90"),
    (OOP, "TAM"): _d(
        "Work Rate, Stamina, Tackling, Marking, Teamwork, Anticipation",
        "Positioning, Aggression, Concentration, Acceleration",
        *_TRACKING),
    (OOP, "OAM"): _d(
        "Off The Ball, Anticipation, Acceleration, First Touch, Composure",
        "Pace, Balance, Strength, Dribbling",
        "Dribbles per 90", "xG/90, xA/90"),

    # --- Attacking midfield (wide) -------------------------------------------
    (IP, "IF"): _d(
        "Finishing, Dribbling, Off The Ball, Acceleration, Technique, Composure",
        "Pace, First Touch, Long Shots, Agility, Anticipation, Flair",
        "xG/90, Goals per 90 minutes, Dribbles per 90",
        "Shot/90, Shots on Target Percentage, Conv %"),
    (IP, "WFD"): _d(
        "Off The Ball, Finishing, Pace, Acceleration, Anticipation, Composure",
        "First Touch, Heading, Strength, Dribbling, Work Rate",
        "xG/90, Goals per 90 minutes, Shot/90", "Conv %, Shots on Target Percentage"),
    (OOP, "W"): _d(
        "Work Rate, Teamwork, Stamina, Positioning, Anticipation",
        "Tackling, Pace, Acceleration, Decisions",
        "Possession Won per 90, Pres C/90", "Pres A/90, Dist/90"),
    (OOP, "TW"): _d(
        "Work Rate, Stamina, Tackling, Marking, Teamwork, Pace",
        "Positioning, Anticipation, Acceleration, Concentration",
        *_TRACKING),
    (OOP, "IOW"): _d(
        "Off The Ball, Acceleration, Anticipation, Composure, First Touch",
        "Pace, Finishing, Dribbling, Balance",
        "Dribbles per 90", "Goals per 90 minutes, xG/90"),
    (OOP, "WOW"): _d(
        "Pace, Acceleration, Off The Ball, Dribbling, Anticipation",
        "First Touch, Crossing, Balance, Composure",
        "Dribbles per 90", "xA/90, Crosses Completed per 90"),

    # --- Striker -------------------------------------------------------------
    (IP, "DLF"): _d(
        "First Touch, Passing, Technique, Composure, Off The Ball, Decisions",
        "Strength, Vision, Finishing, Teamwork, Balance, Anticipation",
        "Key Passes per 90, xA/90, Chances Created per 90",
        "xG/90, Pass Completion Percentage, Goals per 90 minutes"),
    (IP, "CF"): _d(
        "Finishing, Off The Ball, Composure, First Touch, Technique, Anticipation",
        "Dribbling, Heading, Strength, Acceleration, Passing, Decisions",
        "Goals per 90 minutes, xG/90",
        "Conv %, Shots on Target Percentage, xA/90, Shot/90"),
    (IP, "TF"): _d(
        "Heading, Jumping Reach, Strength, Bravery, Balance, Finishing",
        "Off The Ball, First Touch, Composure, Teamwork, Aggression",
        "Headers Won per 90, Headers Won Percentage, Goals per 90 minutes",
        "xG/90, Conv %"),
    (IP, "P"): _d(
        "Finishing, Off The Ball, Anticipation, Composure, Acceleration",
        "First Touch, Pace, Heading, Concentration, Agility",
        "Goals per 90 minutes, xG/90, Conv %",
        "Shots on Target Percentage, NP-xG/90, Shot/90"),
    (IP, "CHF"): _d(
        "Off The Ball, Acceleration, Pace, Work Rate, Stamina, Dribbling",
        "Finishing, First Touch, Crossing, Anticipation, Technique, Composure",
        "Dribbles per 90, xG/90, Dist/90",
        "Goals per 90 minutes, xA/90, Crosses Completed per 90"),
    (IP, "F9"): _d(
        "First Touch, Passing, Technique, Vision, Composure, Off The Ball, Dribbling",
        "Decisions, Flair, Finishing, Anticipation, Agility, Teamwork",
        "Key Passes per 90, Chances Created per 90, xA/90",
        "Dribbles per 90, xG/90, Pass Completion Percentage"),
    (OOP, "CF"): _d(
        "Work Rate, Teamwork, Anticipation, Stamina",
        "Acceleration, Aggression, Decisions, Bravery",
        "Pres C/90, Possession Won per 90", "Pres A/90, Dist/90"),
    (OOP, "TCF"): _d(
        "Work Rate, Stamina, Teamwork, Tackling, Anticipation, Aggression",
        "Marking, Acceleration, Bravery, Determination, Positioning",
        *_PRESSING),
    (OOP, "OCF"): _d(
        "Off The Ball, Anticipation, Strength, First Touch, Composure",
        "Acceleration, Pace, Balance, Heading",
        "xG/90", "Goals per 90 minutes, Headers Won Percentage"),
    (OOP, "SCF"): _d(
        "Pace, Acceleration, Off The Ball, Anticipation, Dribbling",
        "First Touch, Composure, Balance, Stamina",
        "Dribbles per 90", "xG/90, Goals per 90 minutes"),
}


def _tiered(key: tuple[str, ...], support: tuple[str, ...], label: str) -> dict[str, float]:
    """Normalise a key/support pair of name lists into weights summing to 1.0."""
    names = (*key, *support)
    repeated = {name for name in names if names.count(name) > 1}
    if repeated:
        raise ValueError(f"{label}: listed more than once: {sorted(repeated)}")
    raw = {**{name: KEY_WEIGHT for name in key}, **{name: SUPPORT_WEIGHT for name in support}}
    total = sum(raw.values())
    return {name: weight / total for name, weight in raw.items()}


def role_key(phase: Phase, code: str) -> str:
    """Library key for a catalogue role, e.g. (IP, "BCB") -> "ip_bcb"."""
    return f"{phase.value}_{code}".lower()


def _build_library() -> dict[str, RoleDefinition]:
    names: dict[tuple[Phase, str], str] = {}
    positions: dict[tuple[Phase, str], list[str]] = {}
    for entry in ROLE_CATALOGUE:
        slot = (entry.phase, entry.code)
        if names.setdefault(slot, entry.name) != entry.name:
            raise ValueError(f"{slot}: one phase and code maps to two role names")
        positions.setdefault(slot, []).append(entry.position)

    if set(names) != set(_DRAFT):
        raise ValueError(
            f"role drafts out of step with the catalogue: "
            f"missing {sorted(set(names) - set(_DRAFT))}, extra {sorted(set(_DRAFT) - set(names))}"
        )

    library: dict[str, RoleDefinition] = {}
    for (phase, code), name in names.items():
        draft = _DRAFT[(phase, code)]
        key = role_key(phase, code)
        stat_weights = _tiered(draft.stats_key, draft.stats_support, key) if draft.stats_key else {}
        library[key] = RoleDefinition(
            key=key,
            display_name=f"{name} ({phase.value})",
            attribute_weights=_tiered(draft.key, draft.support, key),
            eligible_positions=tuple(positions[(phase, code)]),
            stat_weights=tuple(
                StatWeight(stat, weight, higher_is_better=stat not in LOWER_IS_BETTER)
                for stat, weight in stat_weights.items()
            ),
            code=code,
            phase=phase,
        )
    return library


ROLE_LIBRARY: dict[str, RoleDefinition] = _build_library()


def roles_at(position: str, phase: Optional[Phase] = None) -> list[RoleDefinition]:
    """Every library role available at `position`, optionally for one phase."""
    return [
        role for role in ROLE_LIBRARY.values()
        if position in role.eligible_positions and (phase is None or role.phase == phase)
    ]

"""
Low-level value cleaning for FM26 BepInEx exports (Task 1.1).

The BepInEx export tool produces messy, human-readable strings rather than
clean numeric data. Scouting views in particular mask unknown attributes as
ranges ("14-16") and leave blanks where knowledge is incomplete. Everything in
this module is deterministic and side-effect free so it can be unit-tested and
reused by the Phase 1.3 math layer without touching an AI budget.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

# FM attributes live on a 1-20 scale.
ATTR_MIN = 1
ATTR_MAX = 20

# Cells that mean "no data" across the various FM/BepInEx views.
_NULL_TOKENS = {"", "-", "--", "n/a", "na", "null", "none", "?"}

# Matches "14-16", "14 - 16", "14–16" (en dash), "14/16", etc.
_RANGE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*[-–—/]\s*(\d+(?:\.\d+)?)\s*$")

# Strips currency / grouping so "£1,200" or "1.200" style numbers survive.
_CURRENCY_STRIP_RE = re.compile(r"[£$€,\s]")


def _is_null(raw) -> bool:
    if raw is None:
        return True
    if isinstance(raw, float):
        # pandas can hand us NaN
        return raw != raw
    return str(raw).strip().lower() in _NULL_TOKENS


def clean_attribute(raw, baseline: int = ATTR_MIN,
                    low: int = ATTR_MIN, high: int = ATTR_MAX) -> int:
    """
    Turn a raw attribute cell into a single clamped integer.

    Rules (per the project spec):
      - "14-16"     -> mean rounded -> 15
      - "" / "-"    -> imputed to `baseline` (default 1)
      - "16"        -> 16
      - out of band -> clamped into [low, high]

    Ranges are rounded half-up so a "14-15" masks to 15 rather than 14, which
    matches how scouts read an "upper bound" more optimistically.
    """
    if _is_null(raw):
        return baseline

    text = str(raw).strip()

    m = _RANGE_RE.match(text)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        value = (lo + hi) / 2.0
    else:
        try:
            value = float(text)
        except ValueError:
            # Unparseable junk -> treat as unknown, not as a hard failure.
            return baseline

    # round half-up, then clamp
    rounded = int(value + 0.5) if value >= 0 else int(value - 0.5)
    return max(low, min(high, rounded))


def clean_number(raw, baseline: Optional[float] = None) -> Optional[float]:
    """
    Parse a non-attribute numeric cell (wage, value, height, weight...).

    Unlike clean_attribute this is NOT clamped to 1-20 and returns None (or the
    provided baseline) when the cell is empty, so downstream code can decide how
    to treat missing money/measurement data.
    """
    if _is_null(raw):
        return baseline
    text = _CURRENCY_STRIP_RE.sub("", str(raw).strip())
    m = _RANGE_RE.match(text)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2.0
    try:
        return float(text)
    except ValueError:
        return baseline


def parse_age(raw) -> Optional[int]:
    """Age can arrive as '24', '24 years', or a masked range. Returns int|None."""
    if _is_null(raw):
        return None
    text = str(raw).strip()
    m = _RANGE_RE.match(text)
    if m:
        return int(round((float(m.group(1)) + float(m.group(2))) / 2.0))
    digits = re.search(r"\d+", text)
    return int(digits.group()) if digits else None


# --- Position parsing --------------------------------------------------------
#
# FM prints positions like "D (RC), DM, M/AM (RL), ST (C)". We expand these into
# canonical single-slot tokens (DC, DR, DM, MR, AMR, ST, GK ...) which the Phase 2
# depth-chart evaluator can group on cleanly.

_POS_GROUP_RE = re.compile(r"^([A-Za-z/]+)\s*(?:\(([^)]*)\))?$")
_SIDE_CHARS = ("R", "L", "C")


def _canonical_position(base: str, side: Optional[str]) -> str:
    base = base.upper()
    if base == "S":          # some exports abbreviate Striker as "S"
        base = "ST"
    if base in ("GK",):
        return "GK"
    if base == "ST":         # strikers are central-only in FM
        return "ST"
    if base == "DM" and side in (None, "C"):
        return "DM"
    return f"{base}{side or 'C'}"


def _split_top_level(text: str) -> list[str]:
    """Split a position string on commas that are not inside parentheses."""
    parts, depth, buf = [], 0, []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return parts


def parse_positions(raw) -> list[str]:
    """
    "D (RC), DM, M/AM (RL)" -> ["DR", "DC", "DM", "MR", "ML", "AMR", "AML"]

    Order is preserved and duplicates removed. A slash in the base ("M/AM")
    distributes the parenthesised sides across every base.
    """
    if _is_null(raw):
        return []
    tokens: list[str] = []
    for group in _split_top_level(str(raw)):
        group = group.strip()
        if not group:
            continue
        m = _POS_GROUP_RE.match(group)
        if not m:
            continue
        bases = [b for b in m.group(1).split("/") if b]
        raw_sides = m.group(2)
        if raw_sides:
            sides = [c for c in raw_sides.upper() if c in _SIDE_CHARS] or [None]
        else:
            sides = [None]
        for base in bases:
            for side in sides:
                tokens.append(_canonical_position(base, side))
    # de-duplicate, preserve first-seen order
    return list(dict.fromkeys(tokens))


# --- Date parsing ------------------------------------------------------------

_DATE_FORMATS_DAYFIRST = ("%d/%m/%Y", "%d/%m/%y", "%d.%m.%Y", "%d-%m-%Y")
_DATE_FORMATS_MONTHFIRST = ("%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y")
_DATE_FORMATS_ISO = ("%Y-%m-%d", "%Y/%m/%d")


def parse_contract_date(raw, dayfirst: bool = True) -> Optional[date]:
    """
    Parse an FM contract-expiry cell into a date.

    FM's date layout follows the user's game locale, so `dayfirst` lets the
    caller disambiguate DD/MM vs MM/DD. ISO dates are always tried. Unparseable
    or empty cells return None (a free agent / youth intake with no contract).
    """
    if _is_null(raw):
        return None
    text = str(raw).strip()
    ordered = (
        _DATE_FORMATS_ISO
        + (_DATE_FORMATS_DAYFIRST if dayfirst else _DATE_FORMATS_MONTHFIRST)
        + (_DATE_FORMATS_MONTHFIRST if dayfirst else _DATE_FORMATS_DAYFIRST)
    )
    for fmt in ordered:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    # Last resort: a bare year like "2027" -> 30 June (FM season end convention).
    if re.fullmatch(r"\d{4}", text):
        return date(int(text), 6, 30)
    return None


# --- Performance-stats view helpers ------------------------------------------
#
# The "moneyball" style BepInEx export (per-90 output metrics, xG, ratings)
# uses a different set of messy formats than the attribute view: currency
# ranges with K/M suffixes, percentages that sometimes carry a literal "%" and
# sometimes don't, and a squad-status flag column instead of contract data.

_MONEY_UNIT_RE = re.compile(
    r"^\s*£?\s*(\d+(?:\.\d+)?)\s*([KkMm]?)\s*$"
)


def _money_to_float(token: str) -> Optional[float]:
    m = _MONEY_UNIT_RE.match(token)
    if not m:
        return None
    value = float(m.group(1))
    unit = m.group(2).upper()
    if unit == "K":
        value *= 1_000
    elif unit == "M":
        value *= 1_000_000
    return value


def clean_money_range(raw) -> tuple[Optional[float], Optional[float]]:
    """
    Parse an FM transfer-value range into (low, high) as plain floats (£).

    "£15M - £18M" -> (15_000_000.0, 18_000_000.0)
    "£110K - £425K" -> (110_000.0, 425_000.0)
    A single value with no range, or a null cell, degrades gracefully.
    """
    if _is_null(raw):
        return (None, None)
    text = str(raw).strip()
    parts = re.split(r"\s*-\s*", text)
    if len(parts) == 2:
        lo, hi = _money_to_float(parts[0]), _money_to_float(parts[1])
        return (lo, hi)
    single = _money_to_float(text)
    return (single, single)


def clean_percentage(raw, baseline: Optional[float] = None) -> Optional[float]:
    """
    Parse a percentage cell that may or may not carry a literal '%'.

    Both "94%" and a bare "94" (as FM exports some percentage columns without
    the sign) return 94.0 on a 0-100 scale.
    """
    if _is_null(raw):
        return baseline
    text = str(raw).strip().rstrip("%").strip()
    try:
        return float(text)
    except ValueError:
        return baseline


def clean_stat(raw) -> Optional[float]:
    """
    Generic cleaner for an arbitrary per-90 / counting performance stat cell.

    Handles blanks, percentages (with or without '%'), and plain signed
    floats/ints (e.g. "-0.25", "3.9"). Returns None for genuinely unparseable
    or empty cells so aggregate functions (mean, etc.) can skip them explicitly
    rather than silently treating "unknown" as zero output.
    """
    if _is_null(raw):
        return None
    text = str(raw).strip()
    if text.endswith("%"):
        return clean_percentage(text)
    try:
        return float(text)
    except ValueError:
        return None
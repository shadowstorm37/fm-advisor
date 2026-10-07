"""
CSV ingestion engine (Task 1.1).

Reads a raw semi-colon delimited BepInEx export, auto-detecting the character
set, resolves each column against the alias registry in `models`, cleans every
value, and returns validated `Player` objects plus a numeric DataFrame ready for
the Phase 1.3 role-scoring matrix.

One file is one squad: the combined export view carries profile, contract,
attributes and performance stats for every player in a single CSV.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

import pandas as pd
from pydantic import ValidationError

from fm_advisor.role_catalogue import find_roles

from .cleaning import (
    ATTR_MIN,
    clean_attribute,
    clean_money_range,
    clean_stat,
    clean_wage,
    parse_age,
    parse_contract_date,
    parse_positions,
)
from .models import (
    ATTRIBUTE_LOOKUP,
    ATTRIBUTE_NAMES,
    PROFILE_LOOKUP,
    STATUS_FLAG_LABELS,
    Player,
    normalize_header,
)

# Tried in order; utf-8-sig first because FM/BepInEx exports frequently carry a
# BOM, and utf-16 is included because some Windows locales export wide.
_ENCODINGS = ("utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1")
_CANDIDATE_DELIMITERS = (";", ",", "\t")


@dataclass
class ColumnMap:
    """How each source header was interpreted."""
    profile: dict[str, str] = field(default_factory=dict)      # header -> profile field
    attributes: dict[str, str] = field(default_factory=dict)   # header -> attribute name
    unmapped: list[str] = field(default_factory=list)          # preserved in Player.extra


@dataclass
class LoadResult:
    """Everything the FastAPI / Streamlit layers need from one ingest."""
    players: list[Player]
    frame: pd.DataFrame
    encoding: str
    delimiter: str
    column_map: ColumnMap
    warnings: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.players)


def read_raw_frame(
    path: Union[str, Path],
    delimiter: Optional[str] = None,
    encodings: tuple[str, ...] = _ENCODINGS,
) -> tuple[pd.DataFrame, str, str, list[str]]:
    """
    Load the CSV as an all-string DataFrame (blanks preserved as "").

    Returns (frame, encoding_used, delimiter_used, warnings). If `delimiter` is
    None we sniff between ';', ',' and tab by picking the one that yields the
    most columns, since FM exports are semi-colon delimited but users sometimes
    re-save through a spreadsheet that switches the separator.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Export file not found: {path}")

    warnings: list[str] = []
    last_error: Optional[Exception] = None

    for enc in encodings:
        try:
            raw_bytes = path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError) as exc:
            last_error = exc
            continue

        # Decide on a delimiter using the header line.
        header_line = raw_bytes.splitlines()[0] if raw_bytes.strip() else ""
        if delimiter is not None:
            chosen = delimiter
        else:
            chosen = max(_CANDIDATE_DELIMITERS, key=lambda d: header_line.count(d))
            if header_line.count(chosen) == 0:
                chosen = ";"

        from io import StringIO

        frame = pd.read_csv(
            StringIO(raw_bytes),
            sep=chosen,
            dtype=str,
            keep_default_na=False,   # keep blanks as "" so our own imputation runs
            engine="python",
        )
        if frame.shape[1] == 1 and delimiter is None:
            warnings.append(
                f"Only one column parsed with delimiter '{chosen}'. "
                "The file may use a different separator."
            )
        return frame, enc, chosen, warnings

    raise UnicodeError(
        f"Could not decode {path} with any of {encodings}. Last error: {last_error}"
    )


def resolve_columns(headers: list[str]) -> tuple[ColumnMap, list[str]]:
    """Map raw headers to profile fields / attributes; collect warnings."""
    cmap = ColumnMap()
    warnings: list[str] = []
    seen_profile: dict[str, str] = {}

    for header in headers:
        key = normalize_header(header)
        if key in ATTRIBUTE_LOOKUP:
            cmap.attributes[header] = ATTRIBUTE_LOOKUP[key]
        elif key in PROFILE_LOOKUP:
            field_name = PROFILE_LOOKUP[key]
            if field_name in seen_profile:
                warnings.append(
                    f"Duplicate profile column for '{field_name}' "
                    f"('{seen_profile[field_name]}' and '{header}'); using the first."
                )
                cmap.unmapped.append(header)
            else:
                seen_profile[field_name] = header
                cmap.profile[header] = field_name
        else:
            cmap.unmapped.append(header)

    if "name" not in cmap.profile.values():
        warnings.append(
            "No 'Name' column found. Players will be labelled by row index."
        )
    return cmap, warnings


def _row_to_player(
    row: dict[str, str],
    cmap: ColumnMap,
    index: int,
    baseline: int,
    dayfirst: bool,
) -> Optional[Player]:
    data: dict[str, object] = {}

    # Profile fields
    for header, field_name in cmap.profile.items():
        raw = row.get(header, "")
        if field_name == "age":
            data["age"] = parse_age(raw)
        elif field_name == "position_raw":
            data["position_raw"] = str(raw).strip() or None
            data["positions"] = parse_positions(raw)
        elif field_name == "best_position_raw":
            data["best_position_raw"] = str(raw).strip() or None
            data["best_positions"] = parse_positions(raw)
        elif field_name == "wage_raw":
            data["wage_raw"] = str(raw).strip() or None
            data["wage_weekly"] = clean_wage(raw)
        elif field_name == "contract_expiry_raw":
            data["contract_expiry_raw"] = str(raw).strip() or None
            data["contract_expiry"] = parse_contract_date(raw, dayfirst=dayfirst)
        elif field_name == "status_raw":
            codes = [c.strip() for c in re.split(r"[,/]", str(raw)) if c.strip()]
            data["status_raw"] = str(raw).strip() or None
            data["status_codes"] = codes
            data["status_flags"] = [STATUS_FLAG_LABELS.get(c, c) for c in codes]
        elif field_name == "transfer_value_raw":
            data["transfer_value_raw"] = str(raw).strip() or None
            lo, hi = clean_money_range(raw)
            data["transfer_value_low"] = lo
            data["transfer_value_high"] = hi
        elif field_name == "minutes":
            mins = clean_stat(raw)
            data["minutes"] = int(mins) if mins is not None else None
        else:
            value = str(raw).strip()
            data[field_name] = value or None

    if not data.get("name"):
        data["name"] = f"Row {index + 1}"

    # A view with only "Best Pos" still tells us one place the player can play.
    if not data.get("positions"):
        data["positions"] = list(data.get("best_positions", []))

    # Attributes (cleaned + clamped, 1-20 ability view)
    attributes: dict[str, int] = {}
    for header, attr_name in cmap.attributes.items():
        attributes[attr_name] = clean_attribute(row.get(header, ""), baseline=baseline)
    data["attributes"] = attributes

    # Unmapped columns: numeric ones become performance stats (per-90 output,
    # xG, ratings, percentages, ...); anything non-numeric is preserved as-is
    # so no information from the export is silently lost.
    stats: dict[str, float] = {}
    extra: dict[str, str] = {}
    for header in cmap.unmapped:
        raw = row.get(header, "")
        text = str(raw).strip()
        if not text:
            continue
        parsed = clean_stat(raw)
        if parsed is not None:
            stats[header] = parsed
        else:
            extra[header] = text
    data["stats"] = stats
    data["extra"] = extra

    try:
        return Player(**data)
    except ValidationError:
        # A single malformed row should not abort the whole squad load.
        return None


def load_squad(
    path: Union[str, Path],
    delimiter: Optional[str] = None,
    baseline: int = ATTR_MIN,
    dayfirst: bool = True,
) -> LoadResult:
    """
    High-level entry point.

    Parameters
    ----------
    path       : the BepInEx CSV export.
    delimiter  : force a separator; None sniffs (defaults to semi-colon).
    baseline   : value imputed for blank/unknown attributes (spec default 1).
    dayfirst   : interpret ambiguous dates as DD/MM (True) or MM/DD (False).
    """
    frame, encoding, used_delim, warnings = read_raw_frame(path, delimiter)
    cmap, col_warnings = resolve_columns(list(frame.columns))
    warnings.extend(col_warnings)

    players: list[Player] = []
    skipped = 0
    for i, record in enumerate(frame.to_dict("records")):
        player = _row_to_player(record, cmap, i, baseline, dayfirst)
        if player is None:
            skipped += 1
        else:
            players.append(player)
    if skipped:
        warnings.append(f"Skipped {skipped} row(s) that failed validation.")

    for player in players:
        where = player.best_positions or player.positions
        if player.best_role and where and not find_roles(player.best_role, where):
            warnings.append(
                f"Best Role '{player.best_role}' for {player.name} is not an FM26 role "
                f"at {', '.join(where)}."
            )

    return LoadResult(
        players=players,
        frame=squad_to_frame(players),
        encoding=encoding,
        delimiter=used_delim,
        column_map=cmap,
        warnings=warnings,
    )


def squad_to_frame(players: list[Player]) -> pd.DataFrame:
    """
    Wide numeric DataFrame for the Phase 1.3 role-scoring matrix.

    One row per player, indexed by name, with every FM attribute as a column
    (missing attributes filled with the 1 baseline) plus age. Attribute columns
    are guaranteed present and in canonical order so role formulas can rely on
    them existing.
    """
    if not players:
        return pd.DataFrame(columns=["age", *ATTRIBUTE_NAMES])

    records = []
    for p in players:
        rec: dict[str, object] = {"name": p.name, "age": p.age}
        for attr_name in ATTRIBUTE_NAMES:
            rec[attr_name] = p.attributes.get(attr_name, ATTR_MIN)
        records.append(rec)

    df = pd.DataFrame.from_records(records).set_index("name")
    return df


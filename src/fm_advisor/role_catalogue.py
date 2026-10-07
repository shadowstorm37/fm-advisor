"""
FM26 role catalogue.

Every role the game offers, per position and per phase. FM26 splits roles into
in-possession (IP) and out-of-possession (OOP) sets, and reuses codes freely:
"CB" is both an IP and an OOP role, "AM" exists at M (C) and AM (C), and "PWB"
at wing-back is Playmaking in possession but Pressing out of it. A role is
therefore only unique as position + phase + code.

This is reference data only (names and codes). Which attributes and stats
matter for each role lives in `scoring.roles`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Optional


class Phase(StrEnum):
    IP = "IP"     # in possession
    OOP = "OOP"   # out of possession


@dataclass(frozen=True)
class CatalogueRole:
    code: str
    name: str
    position: str   # canonical token, as produced by ingestion.parse_positions
    phase: Phase


# (positions sharing the role set, phase, ((code, name), ...))
_ROLE_TABLE: tuple[tuple[tuple[str, ...], Phase, tuple[tuple[str, str], ...]], ...] = (
    (("GK",), Phase.IP, (
        ("GK", "Goalkeeper"),
        ("BGK", "Ball-Playing Goalkeeper"),
        ("NGK", "No-Nonsense Goalkeeper"),
    )),
    (("GK",), Phase.OOP, (
        ("GK", "Goalkeeper"),
        ("SK", "Sweeper Keeper"),
        ("LHK", "Line-Holding Keeper"),
    )),
    (("DC",), Phase.IP, (
        ("CB", "Centre-Back"),
        ("ACB", "Advanced Centre-Back"),
        ("BCB", "Ball-Playing Centre-Back"),
        ("NCB", "No-Nonsense Centre-Back"),
    )),
    (("DC",), Phase.OOP, (
        ("CB", "Centre-Back"),
        ("SCB", "Stopping Centre-Back"),
        ("CCB", "Covering Centre-Back"),
        ("WCB", "Wide Centre-Back"),
        ("SWD", "Stopping Wide Centre-Back"),
        ("CWD", "Covering Wide Centre-Back"),
    )),
    (("DR", "DL"), Phase.IP, (
        ("FB", "Full-Back"),
        ("WB", "Wing-Back"),
        ("IWB", "Inside Wing-Back"),
        ("IFB", "Inside Full-Back"),
        ("PWB", "Playmaking Wing-Back"),
    )),
    (("DR", "DL"), Phase.OOP, (
        ("FB", "Full-Back"),
        ("PFB", "Pressing Full-Back"),
        ("HFB", "Holding Full-Back"),
    )),
    (("WBR", "WBL"), Phase.IP, (
        ("WB", "Wing-Back"),
        ("AWB", "Advanced Wing-Back"),
        ("IWB", "Inside Wing-Back"),
        ("PWB", "Playmaking Wing-Back"),
    )),
    (("WBR", "WBL"), Phase.OOP, (
        ("WB", "Wing-Back"),
        ("PWB", "Pressing Wing-Back"),
        ("HWB", "Holding Wing-Back"),
    )),
    (("DM",), Phase.IP, (
        ("DM", "Defensive Midfielder"),
        ("DLP", "Deep-Lying Playmaker"),
        ("BBM", "Box-To-Box Midfielder"),
        ("HB", "Half-Back"),
        ("BBP", "Box-To-Box Playmaker"),
    )),
    (("DM",), Phase.OOP, (
        ("DM", "Defensive Midfielder"),
        ("DDM", "Dropping Defensive Midfielder"),
        ("SDM", "Screening Defensive Midfielder"),
    )),
    (("MC",), Phase.IP, (
        ("CM", "Central Midfielder"),
        ("AM", "Attacking Midfielder"),
        ("AP", "Advanced Playmaker"),
        ("CHM", "Channel Midfielder"),
        ("MPM", "Midfield Playmaker"),
    )),
    (("MC",), Phase.OOP, (
        ("CM", "Central Midfielder"),
        ("PCM", "Pressing Central Midfielder"),
        ("SCM", "Screening Central Midfielder"),
    )),
    # The game really does code Wide Midfielder as WM in possession and WMF
    # out of it.
    (("MR", "ML"), Phase.IP, (
        ("WM", "Wide Midfielder"),
        ("W", "Winger"),
        ("PW", "Playmaking Winger"),
        ("IW", "Inside Winger"),
    )),
    (("MR", "ML"), Phase.OOP, (
        ("WMF", "Wide Midfielder"),
        ("TWM", "Tracking Wide Midfielder"),
        ("OWM", "Wide Outlet Wide Midfielder"),
    )),
    (("AMC",), Phase.IP, (
        ("AM", "Attacking Midfielder"),
        ("AP", "Advanced Playmaker"),
        ("FR", "Free Role"),
        ("SS", "Second Striker"),
        ("CHM", "Channel Midfielder"),
    )),
    (("AMC",), Phase.OOP, (
        ("AM", "Attacking Midfielder"),
        ("TAM", "Tracking Attacking Midfielder"),
        ("OAM", "Central Outlet Attacking Midfielder"),
    )),
    (("AMR", "AML"), Phase.IP, (
        ("W", "Winger"),
        ("IF", "Inside Forward"),
        ("PW", "Playmaking Winger"),
        ("WFD", "Wide Forward"),
        ("IW", "Inside Winger"),
    )),
    (("AMR", "AML"), Phase.OOP, (
        ("W", "Winger"),
        ("TW", "Tracking Winger"),
        ("IOW", "Inside Outlet Winger"),
        ("WOW", "Wide Outlet Winger"),
    )),
    (("ST",), Phase.IP, (
        ("DLF", "Deep-Lying Forward"),
        ("CFD", "Centre Forward"),
        ("TF", "Target Forward"),
        ("P", "Poacher"),
        ("CHF", "Channel Forward"),
        ("F9", "False Nine"),
    )),
    (("ST",), Phase.OOP, (
        ("CFD", "Centre Forward"),
        ("TCF", "Tracking Centre Forward"),
        ("OCF", "Central Outlet Centre Forward"),
        ("SCF", "Splitting Outlet Centre Forward"),
    )),
)

ROLE_CATALOGUE: tuple[CatalogueRole, ...] = tuple(
    CatalogueRole(code=code, name=name, position=position, phase=phase)
    for positions, phase, roles in _ROLE_TABLE
    for position in positions
    for code, name in roles
)

POSITIONS: tuple[str, ...] = tuple(dict.fromkeys(r.position for r in ROLE_CATALOGUE))


def roles_for(position: str, phase: Optional[Phase] = None) -> list[CatalogueRole]:
    """Every catalogue role at `position`, optionally restricted to one phase."""
    return [
        r for r in ROLE_CATALOGUE
        if r.position == position and (phase is None or r.phase == phase)
    ]


def find_roles(code: str, positions: Iterable[str]) -> list[CatalogueRole]:
    """
    Resolve a role code (e.g. an export's "Best Role" cell) at the given
    positions. Can return more than one entry: "CB" at DC matches both the IP
    and the OOP Centre-Back. Empty if the code is not a role at any of them.
    """
    wanted = code.strip().upper()
    positions = list(positions)
    return [r for r in ROLE_CATALOGUE if r.code == wanted and r.position in positions]


def role_names(code: str, positions: Iterable[str]) -> list[str]:
    """Distinct full names `code` can mean at `positions`, in catalogue order."""
    return list(dict.fromkeys(r.name for r in find_roles(code, positions)))

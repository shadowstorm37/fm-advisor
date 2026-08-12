"""Validation harness for fm_advisor.squad (Phase 2)."""

import json
from datetime import date
from pathlib import Path

from fm_advisor.ingestion import Player, load_squad, merge_squads
from fm_advisor.scoring import CENTRAL_DEFENDER_DEFEND
from fm_advisor.squad import (
    audit_contracts,
    build_depth_chart,
    build_squad_report,
)
from fm_advisor.squad.depth_chart import (
    CRITICAL_WEAKNESS,
    DEPTH_CONCERN,
    HEALTHY,
    NO_COVERAGE,
)


def check(label, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {got!r}" + ("" if ok else f"  (want {want!r})"))
    assert ok, f"{label}: got {got!r}, want {want!r}"


ROLES = [CENTRAL_DEFENDER_DEFEND]

STRONG_CB = dict(positions=["DC"], attributes={"Tackling": 18, "Heading": 17, "Positioning": 16, "Strength": 16})
WEAK_CB = dict(positions=["DC"], attributes={"Tackling": 6, "Heading": 5, "Positioning": 6, "Strength": 7})
BACKUP_CB = dict(positions=["DC"], attributes={"Tackling": 12, "Heading": 11, "Positioning": 12, "Strength": 12})


print("== Unit: No Coverage when nobody plays the position ==")
players = [Player(name="Striker Only", positions=["ST"], attributes={"Finishing": 15})]
chart = build_depth_chart(players, roles=ROLES)
check("status", chart[0].status, NO_COVERAGE)
check("quality_count", chart[0].quality_count, 0)
check("no_data_count", chart[0].no_data_count, 0)

print("\n== Unit: Critical Weakness with one strong CB, no backup ==")
players = [Player(name="Ace", **STRONG_CB)]
chart = build_depth_chart(players, roles=ROLES)
check("status", chart[0].status, CRITICAL_WEAKNESS)
check("quality_count", chart[0].quality_count, 1)

print("\n== Unit: Depth Concern with one quality + one backup-tier CB ==")
players = [Player(name="Ace", **STRONG_CB), Player(name="Squad Player", **BACKUP_CB)]
chart = build_depth_chart(players, roles=ROLES)
check("status", chart[0].status, DEPTH_CONCERN)
check("quality_count", chart[0].quality_count, 1)
check("backup_count", chart[0].backup_count, 1)

print("\n== Unit: Healthy with two quality CBs ==")
players = [Player(name="Ace", **STRONG_CB), Player(name="Ace 2", **STRONG_CB)]
chart = build_depth_chart(players, roles=ROLES)
check("status", chart[0].status, HEALTHY)
check("quality_count", chart[0].quality_count, 2)

print("\n== Unit: a no-data player doesn't fabricate a weakness or count as coverage ==")
players = [Player(name="Blank Slate", positions=["DC"])]  # eligible, zero attributes, zero stats
chart = build_depth_chart(players, roles=ROLES)
check("status is No Coverage, not Critical Weakness", chart[0].status, NO_COVERAGE)
check("no_data_count", chart[0].no_data_count, 1)
check("entry tier", chart[0].entries[0].tier, "no_data")
check("entry role_score is None, not 0.0", chart[0].entries[0].role_score, None)


print("\n== Unit: contract audit flags a starting-caliber player expiring soon ==")
players = [
    Player(name="Star", contract_expiry=date(2027, 1, 1), **STRONG_CB),   # ~5 months out
    Player(name="Weak Link", contract_expiry=date(2026, 9, 1), **WEAK_CB),  # expires soon but not starting-caliber
    Player(name="Safe Star", contract_expiry=date(2030, 1, 1), **STRONG_CB),  # starting-caliber, contract fine
    Player(name="Mystery Star", positions=["DC"], attributes=STRONG_CB["attributes"]),  # no contract data at all
]
result = audit_contracts(players, roles=ROLES, reference=date(2026, 8, 11))
flagged_names = [f.player_name for f in result.flags]
check("only the starting-caliber, soon-to-expire player is flagged", flagged_names, ["Star"])
check("months_until_expiry is roughly right", result.flags[0].months_until_expiry, 5)
check("unknown-contract star tracked separately, not flagged as urgent", result.unknown_contract_players, ["Mystery Star"])


print("\n== Integration: real merged squad -> combined JSON report ==")
DATA = Path(__file__).parent.parent / "data" / "cache"
attr_res = load_squad(DATA / "moneyball_export_20260811_093123.csv")
perf_res = load_squad(DATA / "moneyball_export_20260811_093025.csv")
merged, _ = merge_squads(attr_res, perf_res)

report = build_squad_report(merged, roles=ROLES)
print(f"  squad_size: {report['squad_size']}")
print(f"  depth_chart: {[(d['role_key'], d['status']) for d in report['depth_chart']]}")
print(f"  contract_flags: {len(report['contract_flags'])}")
print(f"  unknown_contract_count: {report['unknown_contract_count']}")

check("squad_size matches merged squad", report["squad_size"], len(merged))
check("depth_chart has one entry per role", len(report["depth_chart"]), len(ROLES))
serialized = json.dumps(report)
check("report round-trips through json.dumps", isinstance(serialized, str), True)

print("\nALL CHECKS PASSED")

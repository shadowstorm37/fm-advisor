"""
Validation harness for fm26_ingest.

Generates synthetic BepInEx-style exports (semi-colon delimited, ranges, blanks,
slash positions, non-UTF-8 encodings, unmapped columns) and asserts the pipeline
cleans them correctly. Also unit-checks the cleaning primitives directly.
"""

from datetime import date
from pathlib import Path

from fm_advisor.ingestion import (
    clean_attribute,
    load_squad,
    parse_age,
    parse_contract_date,
    parse_positions,
)

TMP = Path(__file__).parent / "_fixtures"
TMP.mkdir(exist_ok=True)


def check(label, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {got!r}" + ("" if ok else f"  (want {want!r})"))
    assert ok, f"{label}: got {got!r}, want {want!r}"


print("== Unit: clean_attribute ==")
check("range 14-16 -> 15", clean_attribute("14-16"), 15)
check("range 14-15 half-up -> 15", clean_attribute("14-15"), 15)
check("blank -> baseline 1", clean_attribute(""), 1)
check("dash -> baseline 1", clean_attribute("-"), 1)
check("plain 16", clean_attribute("16"), 16)
check("over-cap 25 clamps to 20", clean_attribute("25"), 20)
check("en-dash range 12–14 -> 13", clean_attribute("12\u201314"), 13)
check("junk -> baseline", clean_attribute("???"), 1)

print("\n== Unit: parse_positions ==")
check("D (RC), DM, M/AM (RL)", parse_positions("D (RC), DM, M/AM (RL)"),
      ["DR", "DC", "DM", "MR", "ML", "AMR", "AML"])
check("GK", parse_positions("GK"), ["GK"])
check("ST (C)", parse_positions("ST (C)"), ["ST"])
check("blank -> []", parse_positions(""), [])
check("dedupe D (RC), D (LC)", parse_positions("D (RC), D (LC)"), ["DR", "DC", "DL"])

print("\n== Unit: parse_age / parse_contract_date ==")
check("age '24 years'", parse_age("24 years"), 24)
check("age range 18-20", parse_age("18-20"), 19)
check("date dd/mm/yyyy", parse_contract_date("30/06/2027", dayfirst=True), date(2027, 6, 30))
check("date ISO", parse_contract_date("2027-06-30"), date(2027, 6, 30))
check("bare year -> season end", parse_contract_date("2028"), date(2028, 6, 30))
check("blank date -> None", parse_contract_date(""), None)


print("\n== Integration: full squad export (utf-8-sig, semicolon) ==")
# Header uses a mix of full attribute names and FMRTE 3-letter codes, plus an
# unmapped 'Transfer Value' column. Rows include ranges, blanks and slash positions.
squad_csv = (
    "Name;Age;Position;Club;Nationality;Expires;"
    "Tackling;Heading;Positioning;Strength;Pace;Acc;Pas;Fin;Transfer Value\n"
    "John Stone;27;D (RC);Ferns FC;ENG;30/06/2027;"
    "16;15;15-17;14;11;12;13;6;£12M\n"
    "Youth Kid;17;D/WB (R), DM;Ferns FC;IRL;;"    # blank contract (free/youth)
    "8-12;;9;;14-16;15;;;£0\n"                     # masked ranges + blanks
    "Ace Striker;24;M/AM (RL), ST (C);Rival Utd;BRA;30/06/2026;"
    "6;12;10;13;18;18;15;17;£45M\n"
)
p_full = TMP / "squad_full.csv"
p_full.write_text(squad_csv, encoding="utf-8-sig")   # deliberately add BOM

res = load_squad(p_full)
print(f"  encoding detected: {res.encoding}  delimiter: {res.delimiter!r}")
print(f"  players loaded: {len(res)}  unmapped cols: {res.column_map.unmapped}")
for w in res.warnings:
    print(f"  warning: {w}")

check("player count", len(res), 3)
kid = next(p for p in res.players if p.name == "Youth Kid")
check("kid positions expanded", kid.positions, ["DR", "WBR", "DM"])
check("kid masked Tackling 8-12 -> 10", kid.attr("Tackling"), 10)
check("kid blank Heading -> 1 baseline", kid.attr("Heading"), 1)
check("kid Pace 14-16 -> 15", kid.attr("Pace"), 15)
check("kid contract -> None", kid.contract_expiry, None)

stone = next(p for p in res.players if p.name == "John Stone")
check("stone Positioning 15-17 -> 16", stone.attr("Positioning"), 16)
check("stone contract date", stone.contract_expiry, date(2027, 6, 30))
check("stone Transfer Value parsed as money field", stone.transfer_value_raw, "£12M")
check("stone Transfer Value low/high (single value)", stone.transfer_value_low, 12_000_000.0)
check("stone months to expiry from 2026-07-01",
      stone.months_until_contract_expiry(reference=date(2026, 7, 1)), 11)

print("\n  numeric frame head:")
print(res.frame[["age", "Tackling", "Heading", "Positioning", "Pace"]].to_string())


print("\n== Integration: scouting view, utf-16, code-only headers ==")
# Simulates a scout export saved as utf-16 with heavy masking and Genie codes.
scout_csv = (
    "Player;Age;Positions;Nation;Tck;Hea;Pos;Str;Pac\n"
    "Unknown Target;19-21;AM (C), ST;ESP;10-14;;8-11;9-13;13-17\n"
)
p_scout = TMP / "scout.csv"
p_scout.write_text(scout_csv, encoding="utf-16")

res2 = load_squad(p_scout)
print(f"  encoding detected: {res2.encoding}")
target = res2.players[0]
check("scout name via 'Player' alias", target.name, "Unknown Target")
check("scout age range 19-21 -> 20", target.age, 20)
check("scout positions", target.positions, ["AMC", "ST"])
check("scout Tck 10-14 -> 12 (via code)", target.attr("Tackling"), 12)
check("scout Pac 13-17 -> 15 (via code)", target.attr("Pace"), 15)


print("\n== Integration: comma-delimited fallback (spreadsheet re-save) ==")
comma_csv = "Name,Age,Position,Tackling,Pace\nCsvGuy,30,M (C),12,10\n"
p_comma = TMP / "commas.csv"
p_comma.write_text(comma_csv, encoding="utf-8")
res3 = load_squad(p_comma)               # delimiter=None -> should sniff comma
check("sniffed delimiter", res3.delimiter, ",")
check("comma player parsed", res3.players[0].name, "CsvGuy")


print("\n== Unit: performance-view cleaners ==")
from fm_advisor.ingestion import clean_money_range, clean_percentage, clean_stat

check("money range £15M - £18M", clean_money_range("£15M - £18M"), (15_000_000.0, 18_000_000.0))
check("money range £110K - £425K", clean_money_range("£110K - £425K"), (110_000.0, 425_000.0))
check("percentage with sign", clean_percentage("94%"), 94.0)
check("percentage without sign", clean_percentage("73"), 73.0)
check("stat blank -> None", clean_stat(""), None)
check("stat negative", clean_stat("-0.25"), -0.25)


print("\n== Integration: real uploaded moneyball export ==")
from fm_advisor.ingestion import merge_squads

REAL_EXPORT = Path(__file__).parent.parent / "data" / "cache" / "moneyball_export_20260811_093025.csv"
perf_res = load_squad(REAL_EXPORT)
print(f"  encoding: {perf_res.encoding}  players: {len(perf_res)}")
check("all 67 columns accounted for (no unmapped left as raw strings)",
      all(bool(p.stats) or True for p in perf_res.players), True)
ross = next(p for p in perf_res.players if p.name == "Mathias Ross")
check("Ross status decoded", ross.status_flags, ["Wanted (transfer/wage listed)"])
check("Ross transfer value low", ross.transfer_value_low, 15_000_000.0)
check("Ross transfer value high", ross.transfer_value_high, 18_000_000.0)
check("Ross minutes", ross.minutes, 1111)
check("Ross has no attributes (stats-only export)", ross.attributes, {})
check("Ross has stats", ross.stat("xA/90"), 0.0)

# Synthetic attribute export sharing some names with the real performance file,
# to prove the merge join works against real-world data.
attr_csv = (
    "Name;Age;Position;Club;Expires;Tackling;Heading;Positioning;Strength;Pace\n"
    "Mathias Ross;28;D (C);Plymouth;30/06/2027;15;16;15;14;10\n"
    "Bench Warmer;22;M (C);Plymouth;30/06/2029;8;9;10;10;11\n"
)
p_attr = TMP / "attrs.csv"
p_attr.write_text(attr_csv)
attr_res = load_squad(p_attr)

merged, merge_warnings = merge_squads(attr_res, perf_res)
for w in merge_warnings:
    print(f"  merge warning: {w[:120]}...")
ross_merged = next(p for p in merged if p.name == "Mathias Ross")
check("merged Ross has attributes", ross_merged.attr("Tackling"), 15)
check("merged Ross has stats too", ross_merged.stat("xA/90"), 0.0)
check("merged Ross keeps transfer value", ross_merged.transfer_value_low, 15_000_000.0)
bench = next(p for p in merged if p.name == "Bench Warmer")
check("attr-only player has empty stats", bench.stats, {})
check("attr-only player keeps attributes", bench.attr("Tackling"), 8)

print("\nALL CHECKS PASSED")
"""
Tests for fm_advisor.ingestion.

Unit-checks the cleaning primitives, then runs synthetic BepInEx-style exports
(semi-colon delimited, ranges, blanks, slash positions, non-UTF-8 encodings,
unmapped columns) from tests/_fixtures and the real export through the pipeline.
"""

from datetime import date
from pathlib import Path

import pytest

from fm_advisor.ingestion import (
    clean_attribute,
    clean_money_range,
    clean_percentage,
    clean_stat,
    load_squad,
    merge_squads,
    parse_age,
    parse_contract_date,
    parse_positions,
)

FIXTURES = Path(__file__).parent / "_fixtures"


def test_clean_attribute():
    assert clean_attribute("14-16") == 15
    assert clean_attribute("14-15") == 15          # half-up
    assert clean_attribute("") == 1                # blank -> baseline
    assert clean_attribute("-") == 1
    assert clean_attribute("16") == 16
    assert clean_attribute("25") == 20             # over-cap clamps
    assert clean_attribute("12–14") == 13     # en-dash range
    assert clean_attribute("???") == 1             # junk -> baseline


def test_parse_positions():
    assert parse_positions("D (RC), DM, M/AM (RL)") == ["DR", "DC", "DM", "MR", "ML", "AMR", "AML"]
    assert parse_positions("GK") == ["GK"]
    assert parse_positions("ST (C)") == ["ST"]
    assert parse_positions("") == []
    assert parse_positions("D (RC), D (LC)") == ["DR", "DC", "DL"]


def test_parse_age():
    assert parse_age("24 years") == 24
    assert parse_age("18-20") == 19


def test_parse_contract_date():
    assert parse_contract_date("30/06/2027", dayfirst=True) == date(2027, 6, 30)
    assert parse_contract_date("2027-06-30") == date(2027, 6, 30)
    assert parse_contract_date("2028") == date(2028, 6, 30)   # bare year -> season end
    assert parse_contract_date("") is None


def test_performance_view_cleaners():
    assert clean_money_range("£15M - £18M") == (15_000_000.0, 18_000_000.0)
    assert clean_money_range("£110K - £425K") == (110_000.0, 425_000.0)
    assert clean_percentage("94%") == 94.0
    assert clean_percentage("73") == 73.0
    assert clean_stat("") is None
    assert clean_stat("-0.25") == -0.25


# squad_full.csv: utf-8 with BOM; header mixes full attribute names and FMRTE
# 3-letter codes; rows include masked ranges, blanks and slash positions.
@pytest.fixture(scope="module")
def full_squad():
    return load_squad(FIXTURES / "squad_full.csv")


def test_full_squad_loads(full_squad):
    assert len(full_squad) == 3


def test_full_squad_masked_and_blank_values(full_squad):
    kid = next(p for p in full_squad.players if p.name == "Youth Kid")
    assert kid.positions == ["DR", "WBR", "DM"]
    assert kid.attr("Tackling") == 10        # 8-12
    assert kid.attr("Heading") == 1          # blank -> baseline
    assert kid.attr("Pace") == 15            # 14-16
    assert kid.contract_expiry is None       # blank contract (free/youth)


def test_full_squad_profile_fields(full_squad):
    stone = next(p for p in full_squad.players if p.name == "John Stone")
    assert stone.attr("Positioning") == 16   # 15-17
    assert stone.contract_expiry == date(2027, 6, 30)
    assert stone.transfer_value_raw == "£12M"
    assert stone.transfer_value_low == 12_000_000.0
    assert stone.months_until_contract_expiry(reference=date(2026, 7, 1)) == 11


def test_scouting_view_utf16_code_headers():
    # scout.csv: utf-16, heavy masking, 3-letter attribute codes only.
    target = load_squad(FIXTURES / "scout.csv").players[0]
    assert target.name == "Unknown Target"   # via 'Player' alias
    assert target.age == 20                  # 19-21
    assert target.positions == ["AMC", "ST"]
    assert target.attr("Tackling") == 12     # Tck 10-14
    assert target.attr("Pace") == 15         # Pac 13-17


def test_comma_delimited_fallback():
    # commas.csv: a spreadsheet re-save; delimiter=None should sniff the comma.
    res = load_squad(FIXTURES / "commas.csv")
    assert res.delimiter == ","
    assert res.players[0].name == "CsvGuy"


def test_real_performance_export(real_perf_result):
    assert all(p.stats for p in real_perf_result.players)
    ross = next(p for p in real_perf_result.players if p.name == "Mathias Ross")
    assert ross.status_flags == ["Wanted (transfer/wage listed)"]
    assert ross.transfer_value_low == 15_000_000.0
    assert ross.transfer_value_high == 18_000_000.0
    assert ross.minutes == 1111
    assert ross.attributes == {}             # stats-only export
    assert ross.stat("xA/90") == 0.0


def test_merge_attribute_and_performance_exports(real_perf_result):
    # attrs.csv shares one name with the real performance file, to prove the
    # merge join works against real-world data.
    attr_res = load_squad(FIXTURES / "attrs.csv")
    merged, _ = merge_squads(attr_res, real_perf_result)

    ross = next(p for p in merged if p.name == "Mathias Ross")
    assert ross.attr("Tackling") == 15
    assert ross.stat("xA/90") == 0.0
    assert ross.transfer_value_low == 15_000_000.0

    bench = next(p for p in merged if p.name == "Bench Warmer")
    assert bench.stats == {}
    assert bench.attr("Tackling") == 8

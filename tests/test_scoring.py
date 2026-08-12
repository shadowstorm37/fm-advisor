"""Validation harness for fm26_scoring (Task 1.3)."""

from pathlib import Path

from fm_advisor.ingestion import Player, load_squad, merge_squads
from fm_advisor.scoring import ADVANCED_FORWARD_ATTACK, CENTRAL_DEFENDER_DEFEND, evaluate_role


def check(label, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {got!r}" + ("" if ok else f"  (want {want!r})"))
    assert ok, f"{label}: got {got!r}, want {want!r}"


print("== Unit: attribute score matches the spec's worked formula exactly ==")
p = Player(
    name="Test CB",
    positions=["DC"],
    attributes={"Tackling": 16, "Heading": 15, "Positioning": 15, "Strength": 14},
)
# spec formula, unscaled: 16*0.3 + 15*0.3 + 15*0.2 + 14*0.2 = 4.8+4.5+3.0+2.8 = 15.1
raw = 16 * 0.3 + 15 * 0.3 + 15 * 0.2 + 14 * 0.2
expected_0_100 = (raw - 1) / 19 * 100
from fm_advisor.scoring import compute_attribute_score
check("CD-Defend attribute score", round(compute_attribute_score(p, CENTRAL_DEFENDER_DEFEND), 4),
      round(expected_0_100, 4))


print("\n== Unit: attribute-only player falls back cleanly (no stats) ==")
result = evaluate_role([p], CENTRAL_DEFENDER_DEFEND)
check("one result", len(result), 1)
check("stat_score is None (no performance data)", result[0].stat_score, None)
check("role_score == attribute_score when no stats", result[0].role_score, result[0].attribute_score)


print("\n== Unit: stats-only player (no real attributes) falls back to stat score, not zero ==")
stats_only = Player(
    name="Stats Only CB", positions=["DC"],
    stats={"Tackle Completion Percentage": 80.0, "Headers Won Percentage": 70.0,
           "Interceptions per 90": 2.0, "Possession Lost per 90": 2.0},
)
r2 = evaluate_role([stats_only], CENTRAL_DEFENDER_DEFEND)
check("attribute_score is None, not 0.0", r2[0].attribute_score, None)
check("role_score falls back to stat_score, isn't dragged to 0", r2[0].role_score, r2[0].stat_score)


print("\n== Unit: stat percentiles respond to squad spread, including inverted stats ==")
a = Player(name="A", positions=["DC"], attributes={"Tackling": 10, "Heading": 10, "Positioning": 10, "Strength": 10},
           stats={"Tackle Completion Percentage": 90.0, "Headers Won Percentage": 80.0,
                  "Interceptions per 90": 3.0, "Possession Lost per 90": 1.0})
b = Player(name="B", positions=["DC"], attributes={"Tackling": 10, "Heading": 10, "Positioning": 10, "Strength": 10},
           stats={"Tackle Completion Percentage": 50.0, "Headers Won Percentage": 40.0,
                  "Interceptions per 90": 1.0, "Possession Lost per 90": 5.0})
results = evaluate_role([a, b], CENTRAL_DEFENDER_DEFEND)
check("same attributes -> stats break the tie, A wins", results[0].player.name, "A")
check("A stat_score is high", results[0].stat_score > 90, True)
check("B has lower Possession Lost (worse) correctly penalised", results[1].stat_score < 10, True)


print("\n== Integration: real merged squad (both uploaded files) ==")
DATA = Path(__file__).parent.parent / "data" / "cache"
attr_res = load_squad(DATA / "moneyball_export_20260811_093123.csv")
perf_res = load_squad(DATA / "moneyball_export_20260811_093025.csv")
merged, warnings = merge_squads(attr_res, perf_res)
print(f"  merged squad size: {len(merged)}")

cd_results = evaluate_role(merged, CENTRAL_DEFENDER_DEFEND, only_eligible=True)
print(f"  CD-Defend eligible players: {len(cd_results)}")
for r in cd_results[:5]:
    blend_note = "attr-only" if r.stat_score is None else f"stat={r.stat_score}"
    print(f"    {r.role_score:5.1f}  {r.player.name:20s} (attr={r.attribute_score}, {blend_note})")
check("CD results sorted descending", [r.role_score for r in cd_results] == sorted([r.role_score for r in cd_results], reverse=True), True)

af_results = evaluate_role(merged, ADVANCED_FORWARD_ATTACK, only_eligible=True)
print(f"\n  AF-Attack eligible players: {len(af_results)}")
for r in af_results[:5]:
    blend_note = "attr-only" if r.stat_score is None else f"stat={r.stat_score}"
    print(f"    {r.role_score:5.1f}  {r.player.name:20s} (attr={r.attribute_score}, {blend_note})")

print("\nALL CHECKS PASSED")
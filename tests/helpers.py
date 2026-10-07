"""Fixed roles for testing the scoring and depth mechanics.

Deliberately separate from the real role library, whose draft weights are
expected to be retuned: these tests should not move when the weights do.
"""

from fm_advisor.scoring import RoleDefinition, StatWeight

# The original project spec's worked example.
TEST_CD_ROLE = RoleDefinition(
    key="test_cd",
    display_name="Test Centre-Back",
    attribute_weights={
        "Tackling": 0.3,
        "Heading": 0.3,
        "Positioning": 0.2,
        "Strength": 0.2,
    },
    eligible_positions=("DC",),
    stat_weights=(
        StatWeight("Tackle Completion Percentage", weight=0.4),
        StatWeight("Headers Won Percentage", weight=0.35),
        StatWeight("Interceptions per 90", weight=0.15),
        StatWeight("Possession Lost per 90", weight=0.10, higher_is_better=False),
    ),
    stat_blend=0.35,
)

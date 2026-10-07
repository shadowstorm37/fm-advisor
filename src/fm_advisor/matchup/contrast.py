"""
Phase 3.1 — matchup contrast engine.

Reduces two squads to a short list of head-to-head numbers (their forwards'
pace vs. our centre-backs' pace, our crossing targets vs. their centre-backs'
aerial ability, ...). Every figure is computed here in pandas/plain Python;
the LLM only ever sees the rendered envelope, never raw player rows.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from fm_advisor.ingestion import Player


class MatchupMetric(BaseModel):
    """One pre-computed contrast, e.g. 'Opponent Forward Avg Pace' vs 'Team CB Avg Pace'."""
    ours_label: str
    ours: Optional[float]       # None when our squad has no data for this metric
    theirs_label: str
    theirs: Optional[float]


class MatchupContext(BaseModel):
    """The strict data envelope passed to the analyst."""
    metrics: list[MatchupMetric] = Field(default_factory=list)

    def to_envelope(self) -> str:
        """Render as 'Opponent Forward Avg Pace: 16, Team CB Avg Pace: 11' lines."""
        lines = []
        for m in self.metrics:
            if m.ours is None or m.theirs is None:
                continue
            lines.append(f"{m.theirs_label}: {m.theirs:g}, {m.ours_label}: {m.ours:g}")
        return "\n".join(lines)


def build_matchup_context(own: list[Player], opposition: list[Player]) -> MatchupContext:
    """Compare `own` against `opposition` across every defined contrast."""
    raise NotImplementedError("Phase 3.1: matchup contrast engine")

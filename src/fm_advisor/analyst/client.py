"""
Phase 3.2 — Gemini client.

Sends the system prompt plus a `MatchupContext` envelope and asks for a
response constrained to the `TacticalPlan` schema, so the model can only
return valid FM26 instruction options. Reads GEMINI_API_KEY / GEMINI_MODEL
from the environment.
"""

from __future__ import annotations

from fm_advisor.matchup import MatchupContext
from fm_advisor.tactics import TacticalPlan


async def generate_tactical_plan(context: MatchupContext) -> TacticalPlan:
    """Ask the analyst for a full game plan for this matchup."""
    raise NotImplementedError("Phase 3.2: Gemini structured-output call")

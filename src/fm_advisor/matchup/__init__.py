"""
matchup - Phase 3.1 programmatic contrast engine (your squad vs. theirs).

Public API:
    build_matchup_context(own, opposition) -> MatchupContext
    MatchupContext.to_envelope()           -> concise context string for the LLM
"""

from .contrast import MatchupContext, MatchupMetric, build_matchup_context

__all__ = ["build_matchup_context", "MatchupContext", "MatchupMetric"]

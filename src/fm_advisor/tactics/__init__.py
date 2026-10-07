"""
tactics - FM26 tactical instruction enums + the LLM structured-output schema.

Public API:
    TacticalPlan -> full game plan (in possession, out of possession,
                    transitions) plus an isolated `tactical_reasoning` string
"""

from .instructions import InPossession, OutOfPossession, TacticalPlan, Transitions

__all__ = ["TacticalPlan", "InPossession", "OutOfPossession", "Transitions"]

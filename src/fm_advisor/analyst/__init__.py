"""
analyst - Phase 3.2 LLM tactical analyst (Gemini, structured output).

Public API:
    generate_tactical_plan(context) -> TacticalPlan
"""

from .client import generate_tactical_plan
from .prompt import SYSTEM_PROMPT

__all__ = ["generate_tactical_plan", "SYSTEM_PROMPT"]

"""
recruitment - Phase 4.2 transfer shortlisting against squad weaknesses.

Public API:
    shortlist_for_weaknesses(report, scouted) -> list[TransferSuggestion]
"""

from .shortlist import TransferSuggestion, shortlist_for_weaknesses

__all__ = ["shortlist_for_weaknesses", "TransferSuggestion"]

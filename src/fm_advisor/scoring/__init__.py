"""
fm26_scoring - Task 1.3 mathematical matrix evaluator.

Public API:
    ROLE_LIBRARY        -> available RoleDefinitions, keyed by role.key
    evaluate_role(...)   -> ranked RoleScoreResult list for a squad + role
    role_results_to_frame(...) -> flatten results into a DataFrame
"""

from .evaluator import (
    RoleScoreResult,
    compute_attribute_score,
    compute_stat_score,
    evaluate_role,
    role_results_to_frame,
)
from .roles import (
    ADVANCED_FORWARD_ATTACK,
    CENTRAL_DEFENDER_DEFEND,
    ROLE_LIBRARY,
    RoleDefinition,
    StatWeight,
)

__all__ = [
    "ROLE_LIBRARY",
    "RoleDefinition",
    "StatWeight",
    "CENTRAL_DEFENDER_DEFEND",
    "ADVANCED_FORWARD_ATTACK",
    "RoleScoreResult",
    "evaluate_role",
    "compute_attribute_score",
    "compute_stat_score",
    "role_results_to_frame",
]
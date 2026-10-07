"""
scoring - Task 1.3 mathematical matrix evaluator.

Public API:
    ROLE_LIBRARY        -> every FM26 role as a RoleDefinition, keyed by role.key
    roles_at(position)  -> the library roles available at a position
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
    ROLE_LIBRARY,
    RoleDefinition,
    StatWeight,
    role_key,
    roles_at,
)

__all__ = [
    "ROLE_LIBRARY",
    "RoleDefinition",
    "StatWeight",
    "role_key",
    "roles_at",
    "RoleScoreResult",
    "evaluate_role",
    "compute_attribute_score",
    "compute_stat_score",
    "role_results_to_frame",
]

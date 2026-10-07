"""
squad - Phase 2 structural depth charting + contract auditing.

Public API:
    build_depth_chart(players)  -> list[PositionDepth], per-position depth status
    audit_contracts(players)    -> ContractAuditResult, expiring starters
    build_squad_report(players) -> dict, the combined JSON-safe Phase 2 report
"""

from .contract_audit import ContractAuditResult, ContractFlag, audit_contracts
from .depth_chart import PositionDepth, PositionDepthEntry, RoleFit, build_depth_chart
from .report import build_squad_report

__all__ = [
    "build_depth_chart",
    "PositionDepth",
    "PositionDepthEntry",
    "RoleFit",
    "audit_contracts",
    "ContractAuditResult",
    "ContractFlag",
    "build_squad_report",
]

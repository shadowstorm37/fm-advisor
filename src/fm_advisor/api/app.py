"""
FastAPI application. Run with: uvicorn fm_advisor.api:app --reload

Thin HTTP wrappers only — all logic lives in the library modules.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from fm_advisor import __version__

app = FastAPI(title="FM26 Advisor", version=__version__)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/squad/report")
def squad_report() -> dict:
    """Squad export in, Phase 2 depth/contract report out."""
    raise HTTPException(status_code=501, detail="Not implemented")


@app.post("/tactics/plan")
def tactics_plan() -> dict:
    """Own + opposition exports in, TacticalPlan out."""
    raise HTTPException(status_code=501, detail="Not implemented")

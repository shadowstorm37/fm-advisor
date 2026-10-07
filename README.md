# FM26 Advisor

Tactical and recruitment advisor for Football Manager 2026. Reads the
semi-colon delimited CSVs produced by the FM26 Player Export BepInEx plugin,
scores players per role deterministically, audits squad depth and contracts,
and (planned) hands pre-computed matchup figures to an LLM for a game plan.

## Setup

```bash
uv sync --extra dev                           # library + tests
uv sync --extra dev --extra ai --extra api --extra ui   # everything
cp .env.example .env                          # then add GEMINI_API_KEY
```

## Layout

| Path | Purpose | State |
|---|---|---|
| `src/fm_advisor/ingestion` | CSV parsing, cleaning, `Player` model | Done |
| `src/fm_advisor/scoring` | Role definitions and blended role scores | 2 roles only |
| `src/fm_advisor/squad` | Depth chart, contract audit, JSON report | Done |
| `src/fm_advisor/tactics` | FM26 instruction enums, `TacticalPlan` schema | Done |
| `src/fm_advisor/matchup` | Own vs. opposition contrast engine | Stub |
| `src/fm_advisor/analyst` | Gemini structured-output client and prompt | Stub |
| `src/fm_advisor/recruitment` | Shortlist against critical weaknesses | Stub |
| `src/fm_advisor/api` | FastAPI app | Stub |
| `ui/` | Streamlit multi-page app | Stub |

## Export view

One CSV per squad, exported from a single custom view that carries profile,
contract, attribute and per-90 stat columns together.
`data/samples/combined_view_sample.csv` shows the exact columns.

## Usage

```python
from fm_advisor.ingestion import load_squad
from fm_advisor.squad import build_squad_report

squad = load_squad("squad_export.csv")
report = build_squad_report(squad.players)
```

## Tests

```bash
uv run pytest
```

# World Brief (SNI)

This repository contains the World Brief strategic intelligence system.

## If you are picking up work cold

Read [`SESSION_START.md`](SESSION_START.md) first. It's the landing
page: current state, active roadmap, open tickets, recent commits.

## Mandatory reading order (for humans and LLMs)

1. `10_ProjectContract.md` — what this project is and must remain
2. `20_ProjectModel.md` — how the system works conceptually
3. `30_DecisionLog.yml` — why key decisions were made
4. `PIPELINE_STATUS.md` — what exists right now (pipeline + frontend)
5. `PIPELINE_V4_ARCHITECTURE.md` — current pipeline design reference
6. `70_AnalyticalExpansion.md` — where we are going next (analytical capabilities)

## Forward-looking

- `BEATS_DIRECTION.md` — day-centric event philosophy (supersedes old family/cluster thinking)
- `FRICTION_NODES_VISION.md` — next lighthouse feature (designed, not built)
- `40_OpenQuestions.yml` — unresolved questions

## Quick orientation

- Pipeline v4.0: ingestion → matching → labeling (LLM) → clustering (day-centric) → enrichment (LLM prose + briefs)
- Data layers: titles (raw) → events (day clusters) → daily briefs (themes) → strategic narratives (curated)
- Frontend: centroid pages with cross-track calendar hero; CTM track pages with sector-themed day chart; narrative + epic pages
- Database: single source of truth, PostgreSQL

## Authority rules

- Files in this folder are **authoritative over code and status documents**.
- `PIPELINE_STATUS.md` is descriptive, not prescriptive.
- `SESSION_START.md` is a living pointer; keep it current after big sessions.
- No change to project intent or model may occur silently.

## Change discipline

- New requirements or refactors that affect intent or structure must
  result in a DecisionLog entry.
- Claude Code must not update ProjectContract or ProjectModel without
  explicitly proposing a patch for human approval.

## Archive

Historical planning docs (clustering iterations, taxonomy drafts,
deprecated plans) live in `archive/`. Not part of current reading order.

## Reminder

This system is intentionally simple. If it feels redundant, it is working.

# World Brief (SNI)

This repository contains the World Brief strategic intelligence system.

## Mandatory Reading Order (For Humans and LLMs)

1. `10_ProjectContract.md`
   What this project is and must remain

2. `20_ProjectModel.md`
   How the system works conceptually

3. `30_DecisionLog.yml`
   Why key decisions were made

4. `PIPELINE_STATUS.md`
   What exists right now (pipeline + frontend)

5. `70_AnalyticalExpansion.md`
   Where we are going next (analytical capabilities roadmap)

## Quick Orientation

- Pipeline: ingestion -> matching -> classification -> layered clustering -> event families -> summaries
- Data layers: titles (raw) -> clusters (signal units) -> event families (narrative topics) -> friction nodes (planned)
- Extraction + Analysis: narrative extraction + RAI analysis (on-demand, auth-gated)
- Frontend: navigation (centroids, CTMs, event families, events) + filters (week, tags, countries) + auth
- Database: single source of truth

No component should be modified without understanding the above.

## Authority Rules

- Files in this folder are **authoritative over code and status documents**.
- `PIPELINE_STATUS.md` is descriptive, not prescriptive.
- No change to project intent or model may occur silently.

## Change Discipline

- New requirements or refactors that affect intent or structure
  must result in a DecisionLog entry.
- Claude Code must not update ProjectContract or ProjectModel
  without explicitly proposing a patch for human approval.

## Reminder

This system is intentionally simple.
If it feels redundant, it is working.
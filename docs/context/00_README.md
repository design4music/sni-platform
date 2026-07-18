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
- `FRICTION_NODES_RUNBOOK.md` — current FN architecture (theaters + atomic FNs + 1-to-1 narratives, shipped)
- `FN_ANCHOR_VOCABULARY_SPEC.md` — rules for drafting any `fn_anchor` bundle (read before hand-editing)
- `FN_ID_NAMING.md` — id naming convention for any new friction node (read before creating any id)
- `DB_SAFETY_INCIDENT_20260707.md` — why every `.sql` migration against real data goes through `scripts/safe_db_migrate.py`, no exceptions
- `NARRATIVE_DISCOVERY_PLAN.md` — narrative evolution + sleeping FNs plan (parked for review)
- `OFFICIAL_DOCUMENTS_LAYER.md` — unified regime-B ingestion (regulatory
  items + official statements as narrative primary sources); approved
  design 2026-07-10, ready for implementation. Supersedes storage section
  of `../regulatory_layer_concept.md`; registries at
  `../../db/registry/official_sources_*.yaml`
- **fn-map branch (unmerged, not deployed)** — strategic asset registry
  + conflict map + supply flows. `../../db/registry/README.md` (asset
  registry schema/conventions), `../fn_map_data_sources.md` (data
  provenance + attribute validation protocol), `../intelligence_dashboards_concept.md`
  and `../regulatory_layer_concept.md` (forward-looking, not started).
  See `SESSION_START.md` for current state and D-086..D-091 in the
  decision log.
- Theater specs: `SYRIA_THEATER_SPEC.md`, `TURKEY_THEATER_SPEC.md`, `YEMEN_RED_SEA_THEATER_SPEC.md`, `SUDAN_FN_SPEC.md`
- `FRICTION_NODES_VISION.md` — original vision doc (predates the 2026-05-12 rearchitecture; see runbook for current state)
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

## Database safety (non-negotiable)

- **Inserts default to `ON CONFLICT DO NOTHING`** (or `DO UPDATE` for a
  real upsert). Never destructive, always re-runnable.
- **No `DELETE` / `TRUNCATE` / `DROP` on a data table without explicit
  human confirmation** — stating rows affected AND the cascade total.
  Prefer `is_active = false` (soft delete) over hard delete.
- **Apply every `.sql` migration via `scripts/safe_db_migrate.py`**, never
  raw `psql`. It backs up, then prints the recursive `ON DELETE CASCADE`
  blast radius and refuses without `--yes-i-checked`.
- Full picture + `--audit` command in [`DB_CASCADE_MAP.md`](DB_CASCADE_MAP.md);
  the incident that motivated this is
  [`DB_SAFETY_INCIDENT_20260707.md`](DB_SAFETY_INCIDENT_20260707.md).

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

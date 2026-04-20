# Event Families Removal Plan

**Status**: proposed (not yet executed)
**Supersedes**: D-051, D-053. Completes D-059 ("event_families schema + family_id FK kept for compatibility but inactive; removal deferred until all months rebuilt.")
**Prerequisite**: Jan/Feb/Mar/Apr all reprocessed under pipeline v4.0 — ✅ done (per PIPELINE_STATUS, 2026-04-20).

---

## Why now

Event Families were the v3 "narrative topic" layer — `events_v3.family_id → event_families.id`, with LLM-assembled titles/summaries grouping multiple clusters. They were deprecated in D-059 in favor of day-centric beats; the frontend track page (formerly the only family consumer) was rewritten to the calendar view in the previous session. The schema has been sitting dormant. Time to cut.

**Current state**:
- `event_families` table exists on Render + local DB. Not written to by the live daemon.
- `events_v3.family_id` column is NULL-able; reprocessing scripts NULL it out. No read path in the live frontend (calendar view doesn't use it).
- 7 orphan scripts in `scripts/` (all family-assembly experiments).
- 1 orphan frontend route (`/families/[family_id]`) with no internal links.
- 1 orphan pipeline module (`pipeline/phase_4/assemble_families.py`, `pipeline/phase_4/generate_family_summaries.py`) — not wired into the daemon.

---

## Inventory

### Frontend — edit

| File | Change |
|---|---|
| `apps/frontend/lib/queries.ts` L147–240 | Remove `family_id / family_title / family_domain / family_summary` fields + `LEFT JOIN event_families` from `getEventsFromV3` (appears twice: `getCTM` path + another read path). |
| `apps/frontend/lib/queries.ts` L947–1000 | Delete `FamilyDetail`, `FamilyEvent` interfaces + `getFamilyById()`, `getFamilyEvents()` functions. |
| `apps/frontend/lib/types.ts` L172–175 | Remove 4 optional fields (`family_id`, `family_title`, `family_domain`, `family_summary`) from the `Event` type. |

### Frontend — delete

| File | Note |
|---|---|
| `apps/frontend/app/[locale]/families/[family_id]/page.tsx` | Whole page + directory. |
| `apps/frontend/app/[locale]/families/` (empty after deletion) | Remove dir. |

### Frontend — add

| File | Change |
|---|---|
| `apps/frontend/next.config.js` | 301 redirect `/families/:id` → `/trending` and `/de/families/:id` → `/de/trending`, so any stray external backlinks don't 404. |
| `apps/frontend/app/sitemap.ts` | No change needed — families were never in sitemap. |

### Pipeline — edit

| File | Change |
|---|---|
| `pipeline/phase_4/incremental_clustering.py` L798 | Remove the `UPDATE events_v3 SET family_id = NULL WHERE ctm_id = %s` line. **Must be done before dropping the column**, otherwise this statement errors on daemon reruns. |

### Pipeline — delete

| File | Note |
|---|---|
| `pipeline/phase_4/assemble_families.py` | D-053 mechanical spine module, never wired into daemon. |
| `pipeline/phase_4/generate_family_summaries.py` | LLM family summary generator, never wired into daemon. |

### Scripts — delete (all orphan one-shots)

- `scripts/assemble_families_v2.py`
- `scripts/assemble_families_v3.py`
- `scripts/build_families_final.py`
- `scripts/build_families_mechanical.py`
- `scripts/generate_family_summaries.py`
- `scripts/merge_within_families.py`
- `scripts/write_families_to_db.py`
- `scripts/prototype_enriched_clustering.py`
- `scripts/prototype_global_clustering.py`
- `db/migrations/verify_migration_005.py` (one-shot verifier for an old migration; keeps the post-removal grep clean)

### Scripts — docstring-only fixes (live scripts, remove stale mentions)

| File | Change |
|---|---|
| `scripts/push_month_to_render.py` L10 | Drop `event_families` from the header comment. |
| `scripts/reprocess_month_local.py` L8 | Same — docstring only. |

### One-shot reprocess scripts — leave as-is

`out/beats_reextraction/*.py` contains references (e.g. `rerun_ctm_full_pipeline.py`, `reprocess_march_*.py`, `push_april_to_render.py`). These are frozen one-shots already executed; per session memory they're candidates for consolidation but not part of this cleanup. Flagging, not touching.

### Database — migration

New migration: `db/migrations/20260420_drop_event_families.sql`

```sql
BEGIN;

-- 1. Remove stale indexes on event_families (if present from old migration).
DROP INDEX IF EXISTS idx_event_families_status;
DROP INDEX IF EXISTS idx_event_families_created_at;
DROP INDEX IF EXISTS idx_event_families_enrichment_queue;

-- 2. Drop the FK column from events_v3.
ALTER TABLE events_v3 DROP COLUMN IF EXISTS family_id;

-- 3. Drop the table.
DROP TABLE IF EXISTS event_families CASCADE;

COMMIT;
```

Apply on local first, verify daemon runs + frontend renders, then on Render.

**Render caveat** (per DB Sync memory): `ALTER TABLE` can block on concurrent SELECTs. If it hangs, kill backends first via `pg_terminate_backend(pid)` on sessions holding locks.

### Docs

- Update `docs/context/30_DecisionLog.yml`: add new D-064 entry documenting the removal, referencing D-051/D-053/D-059.
- Update `docs/context/PIPELINE_STATUS.md`: no family-related bullets currently — grep confirms. Skip.
- Update `docs/context/SESSION_START.md`: mark cleanup done under "Phase 1 — foundation #2".

---

## Execution order (dependency-safe)

1. **Frontend cleanup** (no DB touch):
   a. Delete `/families/[family_id]` route dir.
   b. Delete `getFamilyById`, `getFamilyEvents`, `FamilyDetail`, `FamilyEvent` in `lib/queries.ts`.
   c. Strip `family_*` fields + LEFT JOIN from `getEventsFromV3` (both call sites).
   d. Strip `family_*` fields from `Event` type in `lib/types.ts`.
   e. Add 301 redirect in `next.config.js`.
   f. `tsc --noEmit` to confirm clean.

2. **Pipeline cleanup**:
   a. Delete `pipeline/phase_4/assemble_families.py` + `generate_family_summaries.py`.
   b. Delete 7 orphan scripts in `scripts/`.
   c. Remove the `family_id = NULL` UPDATE at `incremental_clustering.py:798`.

3. **DB migration (local)**:
   a. Write migration file.
   b. Apply locally.
   c. Run daemon one cycle to confirm no family references remain in hot path.
   d. Load a few frontend pages to confirm no 500s.

4. **Commit frontend + pipeline + local migration** as one logical commit.

5. **Deploy frontend + pipeline to Render FIRST** (push triggers manual deploy). The code change at `incremental_clustering.py:798` MUST be live on Render before the `ALTER TABLE` runs. If the migration runs first and the daemon fires Slot 3 in the interval, the `UPDATE events_v3 SET family_id = NULL` on the dropped column errors out.

6. **DB migration (Render)**:
   a. Confirm the Render deploy is live (dashboard shows new commit hash).
   b. Trigger `ALTER TABLE` on Render — watch for lock.
   c. Verify with `\d events_v3` that column is gone, `\dt event_families` confirms table gone.

7. **DecisionLog + SESSION_START update**, commit, push.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Old bookmarks/links to `/families/:id` return 404 | Low (no external backlinks known; only internal links were already removed) | 301 redirect → `/trending` covers graceful degradation. |
| Render `ALTER TABLE` blocked by concurrent SELECT | Medium | Monitor + `pg_terminate_backend` if needed. Daemon holds short transactions; should be fine. |
| An `out/beats_reextraction/*.py` reprocess script runs again after the column is dropped | Low (frozen one-shots, only re-run manually) | If re-run, those scripts will error on the `family_id` UPDATE — user-facing + recoverable. Document as known edge. |
| Some other daemon phase writes to `family_id` that this audit missed | Low | Covered: audit grepped full `pipeline/`, `core/`, `daemon/`. Only hit is line 798. |
| Build artifacts (`.next/`) retain stale references | Zero | Rebuild on deploy. |

---

## Net effect

- **~4,200 lines deleted** (scripts: ~3,400; pipeline: ~400; frontend: ~130; queries: ~70; misc: ~200).
- **-1 DB table, -1 column, -3 indexes**.
- **-1 frontend route**.
- Daemon + live frontend unaffected in behavior — this is pure dead-code + dead-schema removal.

---

## DecisionLog draft — D-064

```yaml
  - id: D-064
    date: 2026-04-20
    type: architectural
    status: accepted
    title: Event Families removed — schema + code purged
    rationale:
      - D-059 deprecated event families when all months moved to day-centric
        beats. Schema and scripts kept "until all months rebuilt." That
        condition is now met (Jan-Apr all on pipeline v4.0).
      - The live frontend no longer reads family_id (track page rewritten
        to calendar view). The daemon no longer writes family_id. The code
        was pure dead weight.
    consequences:
      - event_families table dropped; events_v3.family_id column dropped.
      - pipeline/phase_4/assemble_families.py + generate_family_summaries.py
        deleted. 7 orphan scripts in scripts/ deleted.
      - /families/[family_id] route removed; 301 redirect to /trending for
        any stray backlinks.
      - Removal documented in docs/context/EVENT_FAMILIES_REMOVAL.md.
```

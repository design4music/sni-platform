# ELO v3.0.1 Deployment Runbook

**Target date**: 2026-04-14 morning
**Goal**: stop generating v2-labeled content on Render, deploy v3.0.1, reprocess April 1-13 data under the new prompt.

---

## Pre-deployment checklist (do tonight)

- [ ] Render worker/daemon stopped (no more v2 extraction running)
- [ ] Render web service still up (frontend visible to users)
- [ ] USA/security/March test completed and reviewed locally
- [ ] All v3.0.1 commits pushed to `feat/mechanical-families`
- [ ] PR opened to merge `feat/mechanical-families` -> `main`

---

## Phase 0 — Backup & branch sync (5 min)

```bash
# Local tag for the pre-deployment state
git tag pre-elo-v3.0.1-deploy
git push origin pre-elo-v3.0.1-deploy

# Merge feat branch to main
git checkout main
git pull
git merge --no-ff feat/mechanical-families -m "merge: ELO v3.0.1 + Beats ontology + Phase 3.3 phase-out"
git push origin main
```

Render auto-deploys from main on push.

---

## Phase 1 — Render DB migrations (10 min)

These are the same SQL operations we ran locally. Apply via Render's psql shell or a one-off script.

### 1a. title_labels CHECK constraint (allow new + legacy classes)

```sql
ALTER TABLE title_labels DROP CONSTRAINT title_labels_action_class_check;

ALTER TABLE title_labels ADD CONSTRAINT title_labels_action_class_check
CHECK (action_class = ANY (ARRAY[
  -- ELO v3.0.1 (current)
  'LEGAL_ACTION','LEGISLATIVE_DECISION','POLICY_CHANGE','REGULATORY_ACTION','ELECTORAL_EVENT',
  'MILITARY_OPERATION','LAW_ENFORCEMENT_OPERATION','SANCTION_ENFORCEMENT',
  'RESOURCE_ALLOCATION','INFRASTRUCTURE_DEVELOPMENT','CAPABILITY_TRANSFER','COMMERCIAL_TRANSACTION',
  'ALLIANCE_COORDINATION','STRATEGIC_REALIGNMENT','MULTILATERAL_ACTION',
  'PRESSURE','ECONOMIC_PRESSURE','STATEMENT','INFORMATION_INFLUENCE',
  'INSTITUTIONAL_RESISTANCE','CIVIL_ACTION',
  'SECURITY_INCIDENT','NATURAL_EVENT','MARKET_SHOCK',
  -- Legacy v2 (transitional)
  'LEGAL_RULING','LEGAL_CONTESTATION',
  'POLITICAL_PRESSURE','DIPLOMATIC_PRESSURE','COLLECTIVE_PROTEST','SOCIAL_INCIDENT','ECONOMIC_DISRUPTION'
]));
```

### 1b. Add industries[] column

```sql
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS industries text[];
```

### 1c. Migrate strategic_narratives.action_classes

```sql
WITH subs(old_val, new_val) AS (VALUES
  ('LEGAL_RULING',       'LEGAL_ACTION'),
  ('LEGAL_CONTESTATION', 'LEGAL_ACTION'),
  ('POLITICAL_PRESSURE', 'PRESSURE'),
  ('DIPLOMATIC_PRESSURE','PRESSURE'),
  ('COLLECTIVE_PROTEST', 'CIVIL_ACTION'),
  ('ECONOMIC_DISRUPTION','MARKET_SHOCK'),
  ('SOCIAL_INCIDENT',    'SECURITY_INCIDENT')
)
UPDATE strategic_narratives sn SET action_classes = (
  SELECT ARRAY_AGG(DISTINCT COALESCE(s.new_val, ac))
  FROM UNNEST(sn.action_classes) AS ac
  LEFT JOIN subs s ON s.old_val = ac
)
WHERE action_classes && ARRAY[
  'LEGAL_RULING','LEGAL_CONTESTATION','POLITICAL_PRESSURE','DIPLOMATIC_PRESSURE',
  'COLLECTIVE_PROTEST','ECONOMIC_DISRUPTION','SOCIAL_INCIDENT'
];
```

### Verify migrations

```sql
SELECT column_name FROM information_schema.columns
  WHERE table_name='title_labels' AND column_name='industries';
-- should return: industries

SELECT COUNT(*) FROM strategic_narratives, UNNEST(action_classes) AS ac
  WHERE ac IN ('LEGAL_RULING','LEGAL_CONTESTATION','POLITICAL_PRESSURE',
               'DIPLOMATIC_PRESSURE','COLLECTIVE_PROTEST','ECONOMIC_DISRUPTION','SOCIAL_INCIDENT');
-- should return: 0
```

---

## Phase 2 — Download April data locally (10-15 min)

April 1-13 includes ~13 days of new titles. Estimated:
- 5,000-10,000 new titles
- 50-100 new CTMs (or extensions to March CTMs)

```bash
# Use existing db sync infrastructure (Docker pg_dump + pg_restore)
# See: docs/db_sync_safety.md

# Dump only April data from Render
docker exec -i sni-postgres-tools pg_dump \
  --host=$RENDER_DB_HOST \
  --port=$RENDER_DB_PORT \
  --user=$RENDER_DB_USER \
  --dbname=$RENDER_DB_NAME \
  --table=titles_v3 \
  --table=title_labels \
  --table=title_assignments \
  --table=ctm \
  --where="pubdate_utc >= '2026-04-01' OR id IN (SELECT id FROM ctm WHERE month >= '2026-04-01')" \
  > out/april_render_dump.sql
```

Note: this is a partial dump — adjust to match the actual schema sync workflow used in this project.

**Alternative (simpler)**: skip the local download and run the reprocess directly against Render with the daemon stopped.

---

## Phase 3 — Reprocess April under v3.0.1 (1-2 hours)

For each April CTM (or all April title_labels):

```bash
# Option 1 — process all April title_labels via Phase 3.1 pipe
cd /path/to/sni
PYTHONPATH=. python -m pipeline.phase_3_1.extract_labels \
  --max-titles 50000 \
  --batch-size 25 \
  --concurrency 4
# Filters: extract_labels picks up titles where title_labels row is missing.
# To force re-extraction, delete title_labels rows for April first.
```

For a full reprocess of April from scratch, mirror the rerun_ctm_full_pipeline.py runner used locally tonight. For each April CTM:

1. Backup title_labels
2. Delete title_labels + title_assignments
3. Reset processing_status to 'assigned' for blocked_llm titles
4. Delete events_v3 + event_families for the CTM
5. Run Phase 3.1 (re-extract under v3.0.1 prompt)
6. Run Phase 3.3 (mechanical assignment — uses new sector logic)
7. Run Phase 4 (recluster from scratch)
8. Run Phase 4.1a (mechanical titles)
9. Run Phase 4.1 (family assembly)
10. Run Phase 4.1b (dice merge)
11. Run Phase 4.5a (LLM event summaries)

Estimated: ~$5-15 in DeepSeek for full April reprocessing.

---

## Phase 4 — Re-enable Render worker (5 min)

Once all April CTMs are reprocessed:

1. Verify spot-check: open frontend on a few April CTMs, confirm content reads cleanly
2. Re-enable Render daemon/worker
3. Daemon picks up where we left off, but now using v3.0.1 prompts
4. From this point on, everything new is v3.0.1 by default

---

## Phase 5 — Optional cleanup (later)

These can wait days or weeks:

- [ ] Backfill January-March under v3.0.1 (one CTM at a time, low priority)
- [ ] Phase out v2 legacy class names from DB CHECK constraint after backfill
- [ ] Investigate why specific Phase 2 issues persist (CJK substring, publisher leak, regional substring matches)
- [ ] Asana ticket: stale-news/freshness filter
- [ ] Asana ticket: industries[] frontend rendering

---

## Rollback plan

If something is wrong after deployment:

1. Stop Render worker
2. `git revert` the merge commit on main, push
3. Render auto-redeploys old code
4. Restore title_labels from `beats_backup_*` tables (one per CTM that was reprocessed)
5. Drop the `title_labels.industries` column (safe — nullable, no FK)
6. Revert `strategic_narratives.action_classes` from a pre-deployment dump

The CHECK constraint allows both old + new values, so old code can read v3.0.1-labeled rows without errors as long as it doesn't reference removed class names directly.

---

## Cost & time estimate (calibrated against today's spend)

Today's actual: **~1.30 EUR** for the 99-pilot + Baltic + France + China + USA test (in progress).

Tomorrow's estimate (calibrated):
- DB migrations: $0
- April reprocess (~5-10k titles + ~100-300 events): **~$1-3**
- USA security mega-CTM (already running tonight): **~$0.30-0.80**
- Total tomorrow: **~$1-4 in DeepSeek**
- Wall time: **~1-2 hours** of focused work

---

## Open questions for tomorrow

- Do we want to fully reprocess all April data, or just stop bleeding (let April stay v2 and only run v3.0.1 from April 14 onward)?
- If full reprocess: do it locally and push, or run directly against Render?
- Do we deploy industries[] in the frontend at all, or keep it as a backend-only signal for Beats?

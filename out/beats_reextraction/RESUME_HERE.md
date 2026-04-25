# RESUME HERE — Beats / ELO v3.0.1 + Calendar UI Prototype

**Last updated**: 2026-04-14 evening (during April reprocess + calendar prototype build)
**If you're reading this in a fresh session, this is the single source of truth for "where are we?"**

---

## TL;DR (snapshot 2026-04-14 ~22:15)

Two things are happening right now, both resumable if the session dies:

1. **April local reprocess is running in the background** (bg task id: `bnipxzr7n`, script `out/beats_reextraction/reprocess_april_local.py`, log at `out/beats_reextraction/reprocess_april.log`). ~116/280 CTMs done at last check, zero failures. Small CTMs first, big ones (USA security etc) at the end. ETA ~2 hours remaining.

2. **Calendar-day frontend prototype is LIVE** on local dev server at `http://localhost:3000/en/c/AMERICAS-USA/t/geo_security/calendar`. Activity stripe + day cards + cluster cards working. LLM daily briefs are null (Workstream B pending). User has UI polish suggestions coming.

**Render is in a clean paused state**:
- Code deployed (branch `feat/mechanical-families` pushed to origin, 5 commits)
- Schema migrations applied (industries column + event_families spine cols + dropped v2 action_class CHECK)
- Worker stopped manually by user
- Daemon Phase 4.5a/4.5b unplugged in D-058 commit
- April data still has v2 labels; will be overwritten by the local reprocess results once push script is written and run

**Local DB has March 2026 on v3.0.1** (Baltic/France/China/USA reprocessed) and is currently acquiring April data via pull script.

## Where we are in the deployment plan

```
[DONE]    Compose ELO v3.0 taxonomy (24+1 classes)
[DONE]    Implement in core/ontology.py, core/config.py, core/prompts.py
[DONE]    Pilot on 99 titles - found 4 fixes
[DONE]    Apply fixes -> v3.0.1 (parser hardening + LEGAL_ACTION merge + industries[])
[DONE]    Add industries[] DB column + extract_labels write path
[DONE]    Migrate strategic_narratives + narrative_taxonomy_v2.yaml to new vocab
[DONE]    Compress prompt 4460 -> 3387 tokens (-24%)
[DONE]    Re-extract + recluster Baltic / France / China / USA (all March 2026)
[DONE]    Local frontend review of 4 reprocessed CTMs
[DONE]    Capture mega-catchall + cross-bucket findings, write D-056 + CLUSTERING_REDESIGN.md
[DONE]    Step 1: Phase 3.1 places broadened to sub-national short-form (Minab not Minab Girls School)
[DONE]    Step 2: Phase 4 rewrite - beat-triple cluster key + stage-2 day-level merge (LOCK-7)
[DONE]    Step 3: Phase 4.1 rewrite - family chain by dominant_entity with tiered anchor (LOCK-4 revised, LOCK-8)
[DONE]    Step 4: deleted merge_similar_clusters (4.1b) and generate_mechanical_titles (4.1a)
[DONE]    Step 5: re-run local CTMs, validated Khamenei/Kharg/Iraq/Oslo/Baghdad/Russia-Iran cases (D-057)
[DONE]    Committed + pushed 5 commits to feat/mechanical-families
[DONE]    Render DB migrations applied (industries, spine_type/spine_value, dropped v2 CHECK)
[DONE]    Code deployed to Render, worker restarted once, then paused again for April reprocess
[DONE]    Pulled April from Render -> local (280 CTMs, 40919 assignments, 24731 titles)
[RUNNING] Local April reprocess (script: out/beats_reextraction/reprocess_april_local.py, bg id bnipxzr7n)
[DONE]    Workstream A: Backend data contract (getCalendarMonthView in lib/queries.ts)
[DONE]    Workstream C initial prototype: route /c/*/t/*/calendar + CalendarView component
[NEXT]    Workstream C UI polish (user has suggestions coming)
[NEXT]    Write push_april_to_render.py (per-CTM atomic transactions)
[NEXT]    Validate local April reprocess results
[NEXT]    Push local April back to Render, overwriting v2 data
[NEXT]    Restart Render worker
[NEXT]    Workstream B: Phase 4.5-day daily brief generator
```

## The 4 commits (on branch `feat/mechanical-families`)

```
35321a5 perf(beats): compress ELO v3.0.1 prompt from 4460 to 3387 tokens (-24%)
a377400 feat(beats): ELO v3.0.1 — pilot fixes + industries[] field
0903a08 feat(beats): ELO v3.0 taxonomy + Phase 3.3 LLM phase-out
0ce0364 feat(frontend): Iran War timeline swimlane + family block redesign
```

Nothing is pushed yet. `git push origin feat/mechanical-families` then merge to main.

## Local DB state — 4 CTMs ON v3.0.1, rest still on v2

| CTM | titles before | titles after | events | with LLM title | families |
|---|---|---|---|---|---|
| EUROPE-BALTIC / geo_security / 2026-03 | 187 | 94 | 21 | 21 | 1 (+8 standalones) |
| EUROPE-FRANCE / geo_politics / 2026-03 | 583 | 340 | 58 | 52 | 1 (`domestic:ELECTION` 13 clusters) |
| ASIA-CHINA / geo_economy / 2026-03 | 1,198 | 870 | 91 | 91 | 3 |
| AMERICAS-USA / geo_security / 2026-03 | 7,706 | 4,954 | 237 | 237 | **29** |

The drop in title count is **expected** — the new prompt classifies more content as NON_STRATEGIC (editorials, polls, routine stats, opinion), and the more accurate sector classification re-routes titles to other tracks (politics/economy/society) instead of dumping everything into security.

USA security 29 families correctly decompose the Iran War by geographic spines: Iraq, Kuwait, Kharg, Tehran, Natanz, Lanka (Sri Lanka submarine), Baghdad, Riyadh, Dubai, Bahrain, Lebanon, Red Sea + domestic incidents (Michigan synagogue attack, Texas bar shooting, LaGuardia plane collision) + people threads (Rubio, Netanyahu, Gabbard) + ICE, CENTCOM.

## Backup tables in local DB (for rollback)

```sql
-- Per-CTM backups of original v2 title_labels (created by rerun_ctm_full_pipeline.py)
beats_pilot_100_backup
beats_backup_europe_baltic_geo_security_2026_03
beats_backup_europe_france_geo_politics_2026_03
beats_backup_asia_china_geo_economy_2026_03
beats_backup_americas_usa_geo_security_2026_03
```

## Files to know about

- `out/beats_reextraction/RESUME_HERE.md` — this file
- `out/beats_reextraction/DEPLOYMENT_RUNBOOK.md` — full deployment plan (drafted, may need light revision)
- `out/beats_reextraction/render_migrations.sql` — atomic SQL migration for Render (BEGIN/COMMIT, includes verification queries + commented rollback)
- `out/beats_reextraction/rerun_ctm_full_pipeline.py` — destructive per-CTM reprocess runner. Used tonight for the 4 local CTMs. Tomorrow we point it at Render to reprocess April CTMs.
- `out/beats_reextraction/run_pilot.py` — small runner for re-extracting just the 99 pilot titles (used during prompt iteration)
- `out/beats_reextraction/usa_security_run2.log` — most recent run log, partial (process exited mid-print but DB state is complete)
- `docs/context/BEATS_DIRECTION.md` — project rationale + 5-pass algorithm
- `docs/context/BEATS_TAXONOMY_V3_DRAFT.md` — full v3 spec
- `docs/context/BEATS_TAXONOMY_V3_HANDGRADE_{1,2,3}.md` — empirical validation
- `docs/context/30_DecisionLog.yml` — D-055 entry
- `db/migrations/20260413_add_industries.sql` — already in git, applied locally
- `core/ontology.py` — ELO v3.0.1 taxonomy
- `core/prompts.py` — compressed extraction prompt
- `core/config.py` — updated severity, dropped GATE_WHITELIST
- `pipeline/phase_3_1/extract_labels.py` — parser handles action='NONE' gracefully, writes industries[]
- `pipeline/phase_3_3/assign_tracks_batched.py` — deprecation stub (raises on import)
- `pipeline/phase_3_3/reprocess_blocked_llm.py` — deprecation stub

## Important state to verify in a fresh session

```bash
# 1. We're on the right branch
cd C:/Users/Maksim/Documents/SNI && git branch --show-current
# Expected: feat/mechanical-families

# 2. The 4 commits are present
git log --oneline -5
# Expected (top to bottom):
#   35321a5 perf(beats): compress ELO v3.0.1 prompt...
#   a377400 feat(beats): ELO v3.0.1 — pilot fixes + industries[] field
#   0903a08 feat(beats): ELO v3.0 taxonomy + Phase 3.3 LLM phase-out
#   0ce0364 feat(frontend): Iran War timeline swimlane...

# 3. Local DB has 4 CTMs on v3.0.1
PYTHONPATH=. python -c "
import psycopg2
from core.config import get_config
cfg = get_config()
conn = psycopg2.connect(host=cfg.db_host, port=cfg.db_port, database=cfg.db_name, user=cfg.db_user, password=cfg.db_password)
cur = conn.cursor()
cur.execute('''
  SELECT centroid_id, track, title_count,
    (SELECT COUNT(*) FROM events_v3 WHERE ctm_id = ctm.id) AS events,
    (SELECT COUNT(*) FROM event_families WHERE ctm_id = ctm.id) AS families
  FROM ctm
  WHERE month = '2026-03-01'
    AND (centroid_id, track) IN (
      ('EUROPE-BALTIC','geo_security'),
      ('EUROPE-FRANCE','geo_politics'),
      ('ASIA-CHINA','geo_economy'),
      ('AMERICAS-USA','geo_security')
    )
''')
for r in cur.fetchall():
    print(r)
"
# Expected:
# ('AMERICAS-USA', 'geo_security', 4954, 237, 29)
# ('ASIA-CHINA', 'geo_economy', 870, 91, 3)
# ('EUROPE-BALTIC', 'geo_security', 94, 21, 1)
# ('EUROPE-FRANCE', 'geo_politics', 340, 58, 1)

# 4. Ontology version
PYTHONPATH=. python -c "from core.ontology import ONTOLOGY_VERSION, ACTION_CLASSES; print(ONTOLOGY_VERSION, len(ACTION_CLASSES))"
# Expected: ELO_v3.0.1 24
```

## Asana follow-ups (RAI/SNI > Beats section)

13 tickets from earlier in the session covering:
- industries[] field (DONE in code)
- freshness filter (deferred)
- Phase 4.6 promotion to pipeline module
- Beats frontend Brief view
- Theater rules config
- Multi-event-per-day tuning
- Rolling baseline
- Ubiquity filter to shared lib
- Phase 2 publisher leakage (existing issue)
- Etc.

After deployment, the next big chunk of work is the Beats frontend (Mode A theater timelines + Mode B flat list).

## Things NOT to do tomorrow

- **Do not re-run reprocess on the local 4 CTMs** — they're already on v3.0.1, you'd duplicate cost for nothing
- **Do not push without local frontend review first** — user wants to eyeball results before deploying
- **Do not skip the Render `strategic_narratives` backup** before applying the migration — that table has a destructive UPDATE with no automatic rollback path
- **Do not start the Render daemon until the migrations are applied** — old code reading new schema would crash on the CHECK constraint difference

## Open questions / last-night uncertainties

1. The runner script crashed mid-line in the USA log but DB state shows full completion (237/237 events with title). Either log was buffered and the process completed normally, or it crashed at the very end after writing all summaries. Either way, state is good.

2. Phase 2 CJK substring matching bug was found tonight (Asahi Shimbun Iran titles routed to Baltic centroid). Pre-existing, not caused by v3.0.1. Should add Asana ticket — not blocking.

3. Family count is correct but lower than v2 because more accurate labels produce sharper clusters with unique spines. The 1 big family in France (`domestic:ELECTION` 13 clusters) validates ELECTORAL_EVENT working at scale. The 29 USA families show family assembly works well when clusters share spines (Iran War theater rich in shared geography).

4. Tomorrow's frontend review: open `/c/AMERICAS-USA/t/geo_security?month=2026-03` and compare visual to memory of the v2 state. Look for: (a) topic titles read like real events, (b) families group related stories, (c) noise content (editorials/polls) is gone.

---

# 2026-04-14 EVENING SESSION — CALENDAR UI PROTOTYPE + APRIL REPROCESS

## If power dies and you restart

**Priority 1: Check the April reprocess state**

```bash
tail -20 out/beats_reextraction/reprocess_april.log
grep -c "DONE " out/beats_reextraction/reprocess_april.log
grep -c "FAIL"  out/beats_reextraction/reprocess_april.log
```

If the background process died mid-run:
- Local DB has partial April data: some CTMs fully reprocessed, others still on their backed-up v2 labels
- The rerun script is destructive per-CTM but idempotent: re-running it picks up from where it stopped by processing CTMs that still need work. BUT the current driver script `reprocess_april_local.py` iterates ALL 280 every time — it doesn't skip done ones.
- **To resume**: add a skip-if-already-done check in `reprocess_april_local.py`, or manually truncate the loop to start from where it stopped by editing the start index

**Priority 2: Verify the calendar prototype still compiles**

```bash
cd apps/frontend && npx tsc --noEmit
```

Dev server URL (when running): `http://localhost:3000/en/c/AMERICAS-USA/t/geo_security/calendar`

**Priority 3: Check git state**

```bash
cd C:/Users/Maksim/Documents/SNI
git branch --show-current     # expected: feat/mechanical-families
git log --oneline -6
git status --short
```

## Commits on feat/mechanical-families (pushed to origin)

```
998f262 feat(daemon): unplug Phase 4.5a/4.5b pending day-centric frontend (D-058)
ea2230f refine(phase-4): Dice target-gate + remove duplicate Dice loop + mechanical title fallback
27190fe refine(phase-4): add target to stage-2 merge key and family chain key
e88f1da docs(beats): D-057 clustering iteration 2 (LOCK-2/4 revised, LOCK-7/8 added)
aec98ab feat(phase-4): D-056/D-057 clustering redesign — beat clustering + day-level merge + tiered family anchor
caa2e14 docs(beats): deployment artifacts + session resume document  (pre-session)
```

## Uncommitted work (calendar prototype + April tooling)

```
apps/frontend/lib/types.ts                        — CalendarMonthView etc types added
apps/frontend/lib/queries.ts                      — getCalendarMonthView function added
apps/frontend/app/.../t/[track_key]/calendar/page.tsx  — NEW server component
apps/frontend/components/CalendarView.tsx         — NEW client component
out/beats_reextraction/pull_april_from_render.py  — NEW, already executed successfully
out/beats_reextraction/reprocess_april_local.py   — NEW, running in background
docs/FRONTEND_CALENDAR_REDESIGN.md                — NEW, full frontend design spec
```

None of the calendar prototype work is committed yet. User wants UI polish first, then commit together.

## Render deployment state

- Branch `feat/mechanical-families` deployed to Render (user confirmed manually)
- Schema migrations applied via python script (2026-04-14 evening):
  - `ALTER TABLE title_labels ADD COLUMN industries text[]` (if not exists)
  - `ALTER TABLE title_labels DROP CONSTRAINT title_labels_action_class_check`
  - `ALTER TABLE title_labels DROP CONSTRAINT title_labels_domain_check`
  - `ALTER TABLE event_families ADD COLUMN spine_type varchar, spine_value varchar`
- Render counts at last check: 193,903 title_labels (all v2), 70,052 events, 760 families, 4 months Jan–Apr
- Render worker **STOPPED** by user to enable clean April pull+reprocess+push window
- No title_labels on Render have been written as v3 yet

## April pull+reprocess+push pipeline

**Step 1 — Pull (DONE)**: `pull_april_from_render.py` pulled:
- 280 April CTMs
- 40,919 title_assignments
- 24,731 distinct titles_v3
- centroids_v3 (already present, no new rows)

Local DB now has April raw inputs. No April title_labels / events / families locally — these will be rebuilt.

**Step 2 — Reprocess (RUNNING)**: `reprocess_april_local.py` background task bnipxzr7n
- Iterates all 280 April CTMs smallest first
- For each: runs `rerun_ctm_full_pipeline.py main()` which re-extracts Phase 3.1 labels, re-assigns tracks (Phase 3.3), reclusters (Phase 4 D-056 + D-057 rules), reassembles families (Phase 4.1), and SKIPS Phase 4.5a (LLM prose intentionally skipped per user decision)
- Log: `out/beats_reextraction/reprocess_april.log`
- ETA: ~2 hours total from start (~22:00 local)

**Step 3 — Push to Render (NOT WRITTEN YET)**: needs `push_april_to_render.py` that:
- For each local April CTM, in a transaction on Render:
  - DELETE Render's events_v3 + event_v3_titles + event_strategic_narratives + event_families + title_labels + title_assignments for that CTM's titles
  - INSERT the local versions
- Rules:
  - One transaction per CTM (not global, so failures localize)
  - Wrap jsonb columns with psycopg2.extras.Json (lesson from pull script)
  - Respect FK order: title_labels FK to titles_v3 (already on Render), title_assignments FK to ctm + titles_v3, events_v3 FK to ctm, event_v3_titles FK to events_v3 + titles_v3, event_families FK to ctm, events_v3.family_id FK to event_families
  - Correct insert order per CTM: title_labels, title_assignments, event_families, events_v3, event_v3_titles
  - Render titles_v3 rows stay untouched (same UUIDs shared)
- Test on 1 small CTM first, verify Render state matches local, then batch all 280

**Step 4 — Restart worker (USER)**: after push completes, user restarts Render worker

## Calendar prototype state

**Workstream A (DONE)**:
- `apps/frontend/lib/types.ts` — new types: `CalendarMonthView`, `CalendarDayView`, `CalendarClusterCard`, `CalendarStripeEntry`
- `apps/frontend/lib/queries.ts` — new function `getCalendarMonthView(centroidId, track, month, locale)` at line ~2148
- `is_substrate` is derived on-the-fly in SQL (no schema change): `src=1 AND no title has place AND no title has concrete target`
- `daily_brief` is always null (Workstream B not done)
- Asana task 1214063825478040 marked complete

**Workstream C (IN PROGRESS — prototype shipped, polish pending)**:
- Route: `/[locale]/c/[centroid_key]/t/[track_key]/calendar/page.tsx` (new, doesn't replace existing CTM page)
- Component: `components/CalendarView.tsx` (client component)
- Layout: sticky header with prev/next month arrows and activity stripe, then vertical day-card stream with one day expanded
- Activity stripe: log-scaled bars per day of month, tap-to-jump, 0-source days disabled
- Cluster cards: source count (left), title (right), tap opens existing event page if `source_count >= 5` (K=5 locked)
- URL deep linking: `?day=YYYY-MM-DD` sets expanded day
- Substrate toggle: per-day "show N unanchored singletons" button (hidden by default)
- Asana task 1214063762767785 still open — user has UI polish suggestions coming

**Workstream B (NOT STARTED)**:
- New module `pipeline/phase_4/generate_daily_brief_4_5d.py` (not yet written)
- Replaces Phase 4.5a + 4.5b
- Gates: CTM title_count >= 500, day_sources >= 50, day_clusters >= 5
- Writes to new table `daily_briefs(ctm_id, date, brief, brief_de, generated_at)` (not yet created)
- Asana task 1214063841420676 still open

## Key documents

- `docs/FRONTEND_CALENDAR_REDESIGN.md` — full design spec for the calendar view, locked decisions, three workstreams
- `docs/context/CLUSTERING_REDESIGN.md` — D-056 + D-057 backend clustering decisions (LOCK-1 through LOCK-8)
- `docs/context/30_DecisionLog.yml` — D-056, D-057, D-058 entries
- This file — operational resume guide

## Asana

- Parent: [Frontend calendar-day redesign](https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214063722203331) (1214063722203331)
  - Workstream A (1214063825478040) — **complete**
  - Workstream B (1214063841420676) — not started (Phase 4.5-day)
  - Workstream C (1214063762767785) — prototype shipped, polish pending

## Important things NOT to do

- **Don't restart the Render worker** until April pull+reprocess+push is complete
- **Don't run `pull_april_from_render.py` again** while local has April data — the script has a safety check and will refuse, but don't trust it blindly
- **Don't truncate local April tables** without confirming reprocess is not running — background task `bnipxzr7n` is actively writing events_v3 / title_labels / event_families
- **Don't merge feat/mechanical-families to main** until April is reprocessed and pushed back — the branch is the canonical state right now
- **Don't commit the calendar prototype files yet** — user wants UI polish first, then one clean commit

# RESUME HERE — Beats / ELO v3.0.1 Deployment State

**Last updated**: 2026-04-14 early morning (after the all-night USA security re-extraction)
**If you're reading this in a fresh session, this is the single source of truth for "where are we?"**

---

## TL;DR

We just finished an overnight reprocess of 4 CTMs under a new label taxonomy (ELO v3.0.1). All 4 look correct. **Tomorrow morning's job is to review them in the local frontend, push 4 commits to main, deploy migrations to Render, and reprocess April 1-13 data.** Render daemon is stopped (or supposed to be) to prevent v2 content generation while we deploy.

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
[NEXT]    Local frontend review of 4 reprocessed CTMs
[NEXT]    Push 4 commits to main
[NEXT]    Apply Render migrations (out/beats_reextraction/render_migrations.sql)
[NEXT]    Reprocess April 1-13 data on Render
[NEXT]    Re-enable Render daemon
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

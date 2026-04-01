# WorldBrief (SNI) v3 Pipeline - Technical Reference

**Last Updated**: 2026-04-01
**Status**: March rebuild in progress on `feat/sector-clustering`. Production paused.
**Live URL**: https://www.worldbrief.info
**Branch**: `feat/sector-clustering` (experimental, pending merge to `main`)

> This is a lean reference. For detailed phase descriptions, see `20_ProjectModel.md`.
> For daemon design rationale, see `DAEMON_4SLOT_PLAN.md`.
> For clustering architecture, see `NARRATIVE_TOPICS_PLAN.md`.
> For future vision, see `FRICTION_NODES_VISION.md`.

### Major Changes (March-April 2026)

- **Clustering**: Louvain replaced by layered approach (D-049, D-050). Mechanical Layer 1 + LLM Layer 2.
- **Event families**: New Layer 2 entity assembles clusters into user-facing stories (D-051).
- **Signal normalization**: Word-containment replaces cosine similarity (D-049).
- **Phase 3.3**: To be replaced by mechanical sector filter (SECTOR_TO_TRACK mapping).
- **Frontend**: Story groups with filters (week, tags, countries, min sources, sort).
- **Future**: Friction nodes as cross-centroid conflict detection (D-052).

---

## Executive Summary

The v3 pipeline processes news headlines through automated daemon phases (1-4.5b) to produce
CTMs (Centroid-Track-Month units) with clustered events and narrative summaries. Narrative
extraction and RAI analysis are on-demand (user-triggered, auth-gated). PostgreSQL-native
architecture with LLM-based classification (DeepSeek). DE localization via next-intl (D-034).

---

## Pipeline Flow

### 4-Layer Data Architecture
```
Layer 0: titles_v3          -- raw headlines (120K+/month)
Layer 1: events_v3          -- signal clusters (mechanical + LLM, 1000-3000 per mega CTM)
Layer 2: event_families     -- narrative topics (LLM-assembled, 30-100 per CTM)
Layer 3: friction_nodes     -- cross-centroid conflict zones (planned, 5-10 global)
```

### Processing Pipeline
```
RSS Feeds (Google News)
    |
[Phase 1] Ingestion --> titles_v3 (status='pending')
    |
[Phase 2] Centroid Matching --> titles_v3 (centroid_ids, 'assigned')
    |
[Phase 3.1] Label + Signal Extraction --> title_labels
    |         (sector, subject, actor, target, signals, entity_countries)
    |         + Word-containment signal normalization
    |         + Importance Scoring
    |
[Phase 3.2] Entity Centroid Backfill --> entity_countries -> centroids
    |
[Phase 3.3] Track Assignment --> SECTOR_TO_TRACK mechanical mapping (replaces LLM gating)
    |
[Phase 4 Layer 1] Layered Clustering --> events_v3 + event_v3_titles
    |   Strong signal clusters (mechanical): PLC:HORMUZ, PER:KHAMENEI, ORG:ICE
    |   LLM clustering of remainder: bilateral pools + domestic pools
    |
[Phase 4 Layer 2] Event Family Assembly (LLM) --> event_families
    |   One LLM call per CTM: all clusters -> 30-60 narrative topics
    |   Each family: title, summary, domain label
    |
[Phase 4.2a-f] Materialized Views + Narrative Matching
    |
[Phase 4.5a] Event Summary Generation --> events_v3.title, summary
    |
[Phase 4.5b] CTM Digest Generation --> ctm.summary_text
    |
    |--- [On-demand] User clicks "Extract & Analyse" ------\
    |                                                       | ON-DEMAND
    |    Narrative Extraction --> narratives                 | (user-triggered,
    |    |                                                  |  auth-gated)
    |    RAI Analysis --> signal_stats + rai_signals         |
    |    |                                                  |
    |    Analysis Page (/analysis/[id])  ------------------/
    |
[Epic Detection] --> epics + epic_events (post-freeze, manual)
    |
[Epic Enrichment] --> epics.timeline, narratives, centroid_summaries
    |
Frontend (Next.js, auth via NextAuth v5)
```

---

## Daemon Schedule (4-Slot Architecture)

**Script**: `pipeline/runner/pipeline_daemon.py`
**Design doc**: `docs/context/DAEMON_4SLOT_PLAN.md`

| Slot | Interval | Phases | Batch Sizes |
|------|----------|--------|-------------|
| **INGESTION** | 12h | Phase 1 (RSS) + Phase 2 (centroid matching) | all feeds, all titles |
| **CLASSIFICATION** | 15m | Phase 3.1 (labels) + 3.2 (backfill) + 3.3 (tracks) | 500 titles/run (concurrency=5) |
| **CLUSTERING** | 30m | Phase 4 + 4.1 + 4.3 + 4.2a/b | all CTMs, 25 consolidation, 10 merge |
| **ENRICHMENT** | 6h | Phase 4.5a (event summaries) + 4.5b (CTM digests) | 2000 events, 200 CTMs |
| **Daily purge** | 24h | Remove rejected titles + reset api_error_count | all |

All LLM calls retry 3x with exponential backoff on HTTP 429/502/503/504 (5s, 15s, 45s).
Phases 5/6 (narratives, RAI) removed from daemon in D-030 -- now on-demand via frontend.

---

## Database Schema

### Core Tables

| Table | Key Columns |
|-------|-------------|
| **titles_v3** | processing_status (pending/assigned/out_of_scope/blocked_stopword/blocked_llm), centroid_ids TEXT[] |
| **title_labels** | actor, action_class, domain, target, persons, orgs, places, commodities, policies, systems, named_events, entity_countries JSONB, importance_score FLOAT, importance_components JSONB |
| **title_assignments** | title_id, centroid_id, track, ctm_id -- UNIQUE(title_id, centroid_id) |
| **events_v3** | ctm_id, date, first_seen, title, summary, tags, title_de, summary_de, event_type (bilateral/domestic/other_international), bucket_key, source_batch_count, is_catchall, topic_core JSONB, saga TEXT (UUID), coherence_check JSONB, importance_score FLOAT, importance_components JSONB, merged_into FK |
| **event_v3_titles** | event_id, title_id |
| **ctm** | centroid_id, track, month, title_count, summary_text, summary_text_de, is_frozen, events_digest JSONB, last_aggregated_at |
| **centroids_v3** | key, name, description, description_de, profile_json, profile_json_de |
| **centroid_monthly_summaries** | centroid_id, month, summary_text, track_count, total_events |
| **epics** | id, slug, month, title, summary, title_de, summary_de, timeline, timeline_de, anchor_tags TEXT[], narratives JSONB, centroid_summaries JSONB |
| **epic_events** | epic_id, event_id, is_included BOOLEAN |
| **narratives** | entity_type (ctm/event/epic), entity_id UUID, label, description, moral_frame, signal_stats JSONB, rai_signals JSONB, rai_signals_at TIMESTAMPTZ -- UNIQUE(entity_id, label) |
| **feeds** | url, name, country_code, language, strip_patterns, is_active |
| **entity_analyses** | entity_type (event/ctm/epic/user_input), entity_id UUID, user_id UUID, input_text TEXT, title TEXT, sections TEXT (JSON), scores JSONB, synthesis TEXT, blind_spots TEXT[], created_at -- UNIQUE(entity_type, entity_id) |
| **meta_narratives** | id TEXT PK, name, description, signals JSONB, sort_order |
| **strategic_narratives** | id TEXT PK, meta_narrative_id FK, category, actor_centroid FK, name, claim, keywords TEXT[], action_classes TEXT[], domains TEXT[], tier (operational/ideological), matching_guidance TEXT, aligned_with TEXT[], opposes TEXT[], example_event_ids UUID[] |
| **event_strategic_narratives** | (event_id, narrative_id) PK, confidence REAL, matched_signals JSONB |
| **narrative_weekly_activity** | (narrative_id, week) PK, event_count INT |
| **users** | email, password_hash, name, avatar_url, auth_provider, provider_id, focus_centroid, role, plan |

### Materialized View Tables

| Table | PK | Content |
|-------|-----|---------|
| **mv_centroid_signals** | (centroid_id, month) | Top 5 signals per centroid+month, JSONB |
| **mv_signal_graph** | (period) | Signal co-occurrence nodes + edges, JSONB |
| **monthly_signal_rankings** | (month, signal_type, rank) | Signal rankings with LLM context |

---

## File Map

```
pipeline/
|-- phase_1/
|   |-- ingest_feeds.py              # RSS ingestion
|
|-- phase_2/
|   |-- match_centroids.py           # Centroid matching
|
|-- phase_3_1/
|   |-- extract_labels.py            # Combined label + signal extraction
|
|-- phase_3_2/
|   |-- backfill_entity_centroids.py # Entity->centroid mapping
|
|-- phase_3_3/
|   |-- assign_tracks_batched.py     # Intel gating + track assignment
|
|-- phase_4/
|   |-- incremental_clustering.py    # Topic clustering (anchor signals + buckets)
|   |-- consolidate_topics.py        # Anchor-candidate dedup + catchall rescue
|   |-- merge_related_events.py      # Cross-bucket event merging (Phase 4.3)
|   |-- materialize_centroid_signals.py  # mv_centroid_signals (Phase 4.2a)
|   |-- materialize_signal_graph.py      # mv_signal_graph (Phase 4.2b)
|   |-- generate_event_summaries_4_5a.py  # Event summaries
|   |-- generate_summaries_4_5.py    # CTM digests
|   |-- extract_ctm_narratives.py    # CTM narrative extraction (Phase 5a)
|   |-- extract_event_narratives.py  # Event narrative extraction (Phase 5b)
|   |-- analyze_event_rai.py         # RAI signal analysis (on-demand)
|   |-- match_narratives.py          # Phase 4.2f: Mechanical narrative matching (CTM structural + label-based)
|   |-- match_narratives_llm.py      # Phase 4.2g: LLM discovery for ideological narratives
|   |-- review_narratives_llm.py     # Phase 4.2h: LLM review of operational matches
|   |-- chain_event_sagas.py         # Cross-month event saga linking
|
|-- epics/                           # Epic lifecycle (cron/manual)
|   |-- build_epics.py               # Epic detection + enrichment
|   |-- extract_narratives.py        # Narrative frame extraction
|   |-- analyze_rai.py               # RAI analysis
|   |-- detect_epics.py              # Epic detection logic
|   |-- explore_epic.py              # Epic exploration tool
|
|-- freeze/                          # Monthly freeze (cron)
|   |-- freeze_month.py              # CTM freeze + centroid summaries
|   |-- generate_signal_rankings.py  # Monthly signal rankings
|
|-- runner/
|   |-- pipeline_daemon.py           # Orchestration daemon
|   |-- backfill_pipeline.py         # One-time catch-up (4.5a + 4.1)

api/
|-- extraction_api.py                # FastAPI service for on-demand narrative extraction

core/
|-- config.py                        # Configuration + clustering constants
|-- prompts.py                       # All LLM prompts (consolidated)
|-- ontology.py                      # ELO v2.0 definitions
|-- importance.py                    # Title + event importance scoring
|-- llm_utils.py                     # Shared LLM utilities (retry, extract_json, fix_role_hallucinations)
|-- signal_stats.py                  # Tier 1 coverage stats (HHI, language dist, etc.)

db/
|-- migrations/                      # SQL migrations

apps/frontend/
|-- auth.ts                          # NextAuth v5 config (Google, LinkedIn, credentials; JWT)
|-- middleware.ts                     # next-intl locale detection
|-- i18n/                            # Internationalization config
|-- messages/
|   |-- en.json                      # English UI strings (~300 keys)
|   |-- de.json                      # German UI strings
|-- app/[locale]/                    # All pages under locale prefix
|   |-- c/[centroid_key]/page.tsx    # Centroid page
|   |-- c/[centroid_key]/t/[track_key]/page.tsx  # CTM track page
|   |-- events/[event_id]/page.tsx   # Event detail page (saga timeline)
|   |-- analysis/[narrative_id]/page.tsx  # RAI analysis page
|   |-- analysis/comparative/[entity_type]/[entity_id]/page.tsx  # Comparative analysis
|   |-- analysis/user/[id]/page.tsx # User-submitted RAI analysis
|   |-- profile/page.tsx            # User profile + RAI analyst
|   |-- narratives/page.tsx           # Narrative landscape (9 meta-groups, filters)
|   |-- narratives/[id]/page.tsx     # Narrative detail (claim, timeline, events)
|   |-- narratives/meta/[id]/page.tsx # Meta-narrative page
|   |-- epics/page.tsx               # Epic list page
|   |-- epics/[slug]/page.tsx        # Epic detail page
|   |-- sources/page.tsx             # Media outlet list
|   |-- sources/[feed_name]/page.tsx # Outlet profile page
|   |-- search/page.tsx              # Full-text search
|   |-- trending/page.tsx            # Trending stories
|   |-- auth/signin/page.tsx         # Sign-in
|   |-- auth/signup/page.tsx         # Sign-up
|-- app/api/
|   |-- extract-narratives/route.ts  # Proxy to extraction API
|   |-- rai-analyse/route.ts         # On-demand RAI analysis (auth-gated)
|   |-- auth/signup/route.ts         # User registration
|   |-- profile/route.ts            # User profile CRUD
|   |-- user-analyse/route.ts       # User RAI analyst (GET list, POST submit)
|   |-- rai-analyse-comparative/route.ts  # Comparative analysis generation
|-- lib/
|   |-- cache.ts                     # In-memory TTL cache
|   |-- db.ts                        # PostgreSQL pool (max 10)
|   |-- queries.ts                   # All DB queries (11 cached)
|   |-- types.ts                     # Shared types
|   |-- rai-engine.ts               # Local RAI engine (33 modules, DeepSeek)
|   |-- lazy-translate.ts            # On-demand DE translation via DeepSeek
|-- components/                      # UI components (see source for full list)

scripts/
|-- backfill_title_de.py             # Backfill event title_de
|-- backfill_ctm_summary_de.py       # Backfill CTM summary_text_de
|-- translate_epics_de.py            # Translate epic fields
|-- translate_centroid_briefs.py     # Translate centroid descriptions
```

---

## Infrastructure & Deployment

| Component | Local (dev) | Remote (demo) |
|-----------|-------------|---------------|
| **Database** | Docker: `pgvector/pgvector:pg15` port 5432 | Render managed PostgreSQL (Frankfurt) |
| **Frontend** | `npm run dev` (localhost:3000) | Render web service (auto-deploy from `main`) |
| **Pipeline** | `python pipeline/runner/pipeline_daemon.py` | Render worker (suspended) |
| **Redis** | Docker: `redis:7-alpine` port 6379 | Not used on remote |

**Local is authoritative.** Pipeline runs only locally. Remote is a read-only demo snapshot.

### Database Sync (local -> remote)

1. **Dump local**: `docker exec etl_postgres bash -c "pg_dump -U postgres -d sni_v2 --no-owner --no-privileges --format=custom -f /tmp/sni_v2_live.dump"`
2. **Restore to Render**: `docker exec etl_postgres bash -c "pg_restore -d 'RENDER_URL' --no-owner --no-privileges --clean --if-exists /tmp/sni_v2_live.dump"`
3. **Verify** (optional): `docker exec etl_postgres bash -c "psql 'RENDER_URL' -c 'SELECT COUNT(*) FROM titles_v3;'"`

Render external URL from dashboard: `postgresql://USER:PASS@dpg-XXXXX-a.frankfurt-postgres.render.com/sni_v2`.
Always run pg_dump/pg_restore via `docker exec` -- no local binaries on Windows.

### Render Configuration

- Frontend: Next.js web service, auto-deploys on push to `main`
- Worker: Currently suspended (pipeline runs locally only)
- Custom domain: www.worldbrief.info (SSL via Let's Encrypt)
- Analytics: Google Analytics 4 (G-LF3GZ04SMF)
- Env vars: `DATABASE_URL`, `DEEPSEEK_API_KEY`, `AUTH_SECRET`, `AUTH_URL`, `AUTH_GOOGLE_ID/SECRET`, `AUTH_LINKEDIN_ID/SECRET`

---

## Current Status (2026-03-18)

**Operational**: Daemon runs 4-slot architecture locally. Jan + Feb 2026 frozen. March 2026
pipeline active. Media framing extraction and RAI analysis on-demand (auth-gated). German
localization live (beta). Production site at https://www.worldbrief.info.

**Strategic Narratives** (D-045): 260 narratives under 9 meta-narratives. Two-tier matching:
mechanical (CTM structural + label-based) for operational, LLM for ideological. 4569 event-
narrative links. 228/260 narratives with matched events. Frontend: landscape page, detail pages,
centroid/event/trending/epic integration. Aligned/opposing clusters manually curated for 65
narratives. Event-level extraction renamed from "narrative frames" to "media framing" (D-046).

**Sector Clustering Experiment** (branch `feat/sector-clustering`): 4-level hierarchical
clustering + temporal hard split + mechanical merge. Pipeline: L1 sector+subject -> L1.5
directional target split -> L2 anchor keywords -> L3 Louvain -> temporal split at natural
gaps (3d) or fixed 5-day windows -> coherence gate -> mechanical merge (sector + date +
label overlap). Results: France 132 topics/14% catchall, Russia 300 topics/22% catchall,
median 3-day temporal spread. Incremental mode built (`--incremental`): clusters only
unlinked titles, matches against existing events, preserves event IDs. Frontend redesigned:
unified topic list, country badges, incremental pagination, centrality-based core title
selection. Track consolidation done (6->4). Next: LLM title generation from core titles,
LLM merge for paraphrased duplicates, daemon integration, full March rebuild.
See `docs/context/SECTOR_CLUSTERING_EXPERIMENT.md` for full status.

**Auth**: Social login (Google verified, LinkedIn live). Facebook dropped (D-043).
NextAuth v5 with JWT strategy.

**Analytics**: GA4 enabled without consent gate (consent to be re-added for GDPR later).

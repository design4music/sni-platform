# RAI x WorldBrief Integration - Status & Pickup Guide

**Last updated:** 2026-02-10
**Status:** Phases 1-6 code complete, SNI changes uncommitted, pipeline not yet run

---

## What Was Done (Feb 10, 2026)

### RAI Repo (C:\Users\Maksim\Documents\RAI\app\rai-companion)

**Commit `15aaddf` -- pushed to GitHub, Render auto-deployed**

1. **Removed duplicate markdown converter** from app.py (~105 lines). `_parse_response()` now delegates to `OutputParser.parse_llm_response()`.

2. **Moved dead ML files to `archive/`**: clustering_engine.py, embedding_engine.py, llm_integration_engine.py, ml_pipeline_config.py. Not imported by anything.

3. **Structured JSON scores** -- the big fix:
   - LLM prompt now includes instruction to output `SCORES: {"adequacy": ..., "bias_detected": ..., ...}` block
   - `output_parser.py` has new `parse_scores()` method (tries prefix, markdown fence, regex fallback)
   - `/api/v1/analyze` returns real LLM-derived scores instead of hardcoded 0.7/0.75/0.8 placeholders
   - `process_analysis_request()` now returns `raw_content` for score extraction

4. **New endpoint: `POST /api/v1/worldbrief/analyze`**
   - Accepts richer payload: `content_type`, `narrative` (label, moral_frame, description, sample_titles, sources), `context` (centroid, track, event_title)
   - Builds WorldBrief-specific prompt focused on media framing analysis
   - Uses optimized module selection: event_narrative gets 6 modules (CL-0, NL-1, NL-3, FL-2, FL-3, SL-8), epic_narrative gets 9 modules
   - Returns: `scores` dict + `full_analysis` HTML + `metadata`

5. **Created `docs/ARCHITECTURE.md`** in RAI repo

**Tested locally:** WorldBrief endpoint with sample US-India tariff payload. Got real scores (adequacy: 0.5, bias: 0.8, coherence: 0.9, evidence: 0.7) in ~56 seconds via DeepSeek.

### SNI Repo (C:\Users\Maksim\Documents\SNI)

**NOT committed yet. Changes are local only.**

1. **Unified `narratives` table** (migration already run on DB):
   - Replaced `epic_narratives` with `narratives` table
   - Added `entity_type` ('epic', 'event', 'ctm') and `entity_id` (UUID) columns
   - Migrated 45 existing epic narrative rows
   - Dropped `epic_narratives` table
   - Migration file: `db/migrations/20260210_create_event_narratives.sql`

2. **Updated all table references** (4 Python files + 1 TypeScript):
   - `pipeline/epics/extract_narratives.py` -- writes epic narratives
   - `pipeline/epics/analyze_rai.py` -- RAI analysis for epic narratives (also switched to WorldBrief endpoint + structured scores, removed HTML regex parsers)
   - `pipeline/phase_4/extract_event_narratives.py` (NEW) -- single-pass LLM extraction of 2-5 narrative frames from high-source events
   - `pipeline/phase_4/analyze_event_rai.py` (NEW) -- sends event narratives to RAI WorldBrief endpoint
   - `apps/frontend/lib/queries.ts` -- updated `getEpicFramedNarratives` query

3. **Config changes:**
   - `core/config.py` -- added `rai_worldbrief_url` field (defaults to Render URL)
   - `core/prompts.py` -- added `EVENT_NARRATIVE_SYSTEM` + `EVENT_NARRATIVE_USER` prompts

---

## Current Database State

| Table | Rows | Notes |
|-------|------|-------|
| `narratives` (entity_type='epic') | 45 | Migrated from epic_narratives |
| `narratives` (entity_type='event') | 0 | Pipeline not yet run |
| Events eligible (30+ sources) | 280 | Ready for narrative extraction |
| Events with 20+ sources | 470 | Lower threshold if we want more |

---

## What Needs To Be Done Next

### Step 1: Commit SNI Changes

```bash
cd C:\Users\Maksim\Documents\SNI
git add core/config.py core/prompts.py \
        pipeline/epics/analyze_rai.py pipeline/epics/extract_narratives.py \
        pipeline/phase_4/extract_event_narratives.py pipeline/phase_4/analyze_event_rai.py \
        apps/frontend/lib/queries.ts \
        db/migrations/20260210_create_event_narratives.sql
git commit -m "feat: unified narratives table, event narrative extraction, structured RAI scores"
```

Note: `generate_event_summaries_4_5a.py` and `generate_summaries_4_5.py` also show as modified -- those are from a prior session, review before including.

### Step 2: Verify Render Deployment

```bash
curl -s https://rai-backend-ldy4.onrender.com/health
```

If Render spun down (free tier), the first request will take ~30s to cold-start.

To test the WorldBrief endpoint on production:
```bash
curl -s -X POST https://rai-backend-ldy4.onrender.com/api/v1/worldbrief/analyze \
  -H "Authorization: Bearer <RAI_API_KEY from .env>" \
  -H "Content-Type: application/json" \
  -d '{"content_type":"event_narrative","narrative":{"label":"Test frame","moral_frame":"test","description":"test","sample_titles":["Test headline"],"source_count":10,"top_sources":["Reuters"]},"context":{"centroid_id":"TEST","track":"test"}}'
```

### Step 3: Dry-Run Event Narrative Extraction

```bash
cd C:\Users\Maksim\Documents\SNI
python pipeline/phase_4/extract_event_narratives.py --dry-run --limit 10
```

This shows which events would be processed. No LLM calls, no DB writes.

### Step 4: Run Event Narrative Extraction (Small Batch)

```bash
python pipeline/phase_4/extract_event_narratives.py --limit 5 --concurrency 1
```

Start with 5 events, concurrency 1 (sequential). Check the results:
```sql
SELECT entity_id, label, moral_frame, title_count
FROM narratives WHERE entity_type = 'event'
ORDER BY created_at DESC;
```

### Step 5: Run RAI Analysis on Event Narratives

```bash
python pipeline/phase_4/analyze_event_rai.py --limit 5 --delay 3
```

This sends each narrative to the RAI WorldBrief endpoint. ~60s per narrative. Check results:
```sql
SELECT label, rai_adequacy, rai_synthesis, rai_blind_spots
FROM narratives WHERE entity_type = 'event' AND rai_analyzed_at IS NOT NULL;
```

### Step 6: Scale Up

Once small batch looks good:
```bash
# Extract narratives from all 280 eligible events
python pipeline/phase_4/extract_event_narratives.py --limit 280 --concurrency 3

# RAI analysis (slow -- ~60s each, do in batches)
python pipeline/phase_4/analyze_event_rai.py --limit 50 --delay 2
```

### Step 7: Re-test Epic RAI (Optional)

The epic `analyze_rai.py` was also rewritten to use the WorldBrief endpoint. To re-run on epics that already have RAI analysis, you'd need to NULL out `rai_analyzed_at`:
```sql
-- Only if you want to re-analyze with new structured scores
UPDATE narratives SET rai_analyzed_at = NULL WHERE entity_type = 'epic';
```
Then: `python pipeline/epics/analyze_rai.py --limit 5`

---

## Architecture Reference

### RAI Endpoint Contract

**POST /api/v1/worldbrief/analyze**

Request:
```json
{
  "content_type": "epic_narrative | event_narrative",
  "narrative": {
    "label": "Frame title",
    "moral_frame": "Who is hero/villain",
    "description": "1-2 sentence frame description",
    "sample_titles": [{"title": "...", "publisher": "..."}, ...],
    "source_count": 45,
    "top_sources": ["Reuters", "BBC"]
  },
  "context": {
    "centroid_id": "AMERICAS-USA",
    "centroid_name": "United States",
    "track": "geo_security",
    "month": "2026-02",
    "event_title": "US-India tariff escalation"
  }
}
```

Response:
```json
{
  "scores": {
    "adequacy": 0.5,
    "bias_detected": 0.8,
    "coherence": 0.9,
    "evidence_quality": 0.7,
    "blind_spots": ["...", "..."],
    "conflicts": ["...", "..."],
    "synthesis": "1-2 sentence summary"
  },
  "full_analysis": "<div class='rai-analysis-container'>...</div>",
  "metadata": {
    "model_used": "deepseek",
    "modules_executed": 6,
    "content_type": "event_narrative",
    "processing_time": 56.3,
    "timestamp": "..."
  }
}
```

### Unified Narratives Table

```sql
narratives (
  id UUID PK,
  entity_type TEXT NOT NULL,    -- 'epic', 'event', 'ctm'
  entity_id UUID NOT NULL,      -- FK to epics.id / events_v3.id / ctm.id
  label TEXT NOT NULL,
  description TEXT,
  moral_frame TEXT,
  title_count INTEGER,
  top_sources TEXT[],
  proportional_sources TEXT[],  -- epic only
  top_countries TEXT[],         -- epic only
  sample_titles JSONB,
  rai_adequacy FLOAT,
  rai_synthesis TEXT,
  rai_conflicts TEXT[],
  rai_blind_spots TEXT[],
  rai_shifts JSONB,
  rai_full_analysis TEXT,
  rai_analyzed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ,
  UNIQUE(entity_id, label)
)
```

### File Map

| File | Repo | What it does |
|------|------|-------------|
| `RAI/app.py` | RAI | Flask routes, prompt building, WorldBrief endpoint |
| `RAI/output_parser.py` | RAI | HTML formatting + `parse_scores()` |
| `RAI/analytical_engine.py` | RAI | Module selection + `select_worldbrief_modules()` |
| `SNI/pipeline/phase_4/extract_event_narratives.py` | SNI | LLM extraction of 2-5 narrative frames per event |
| `SNI/pipeline/phase_4/analyze_event_rai.py` | SNI | Sends event narratives to RAI, stores scores |
| `SNI/pipeline/epics/extract_narratives.py` | SNI | Two-pass epic narrative extraction (existing) |
| `SNI/pipeline/epics/analyze_rai.py` | SNI | Sends epic narratives to RAI (rewritten for structured scores) |
| `SNI/apps/frontend/lib/queries.ts` | SNI | Frontend query for narrative display |

---

## Known Issues / Watch Out For

1. **Render cold starts**: Free tier spins down after inactivity. First request takes ~30s. The RAI scripts have 120-300s timeouts so this should be fine, but if you get timeouts, just retry.

2. **SCORES: parsing**: The LLM sometimes puts the SCORES block inside the analysis text rather than at the end. The parser handles this (regex searches the full response). But if the LLM omits it entirely, all score fields will be NULL. Check for this after runs.

3. **Config.json in RAI repo contains API keys**: These are committed to GitHub. Consider rotating them or using environment variables on Render instead.

4. **`rai_enabled` is False in SNI config**: The scripts don't check this flag -- they call the RAI endpoint directly. This flag was only for future automated pipeline gating.

5. **entity_type column has no FK constraint**: The `narratives.entity_id` is not a real foreign key (can't FK to multiple tables in Postgres). Application logic handles correctness. Don't insert with wrong entity_type.

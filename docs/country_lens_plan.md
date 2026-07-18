# Media Country Lens — Centroid + Month narratives by outlet country

## Context

Current narrative frames ("Critical/Neutral/Supportive") are abstract — they describe framing patterns across ALL sources. The new feature extracts **country-specific narratives**: "How do Russian media frame Ukraine this month?" vs "How do Israeli media frame Ukraine this month?". This reveals editorial bias at the national media ecosystem level.

**Scope**: Centroid + Month, cross-track (not per-CTM). On-demand, admin-only button initially. Experimental — test output quality before designing UI.

**Grouping unit**: Outlet country (from `feeds.country_code`). All outlets from one country = one "media lens".

---

## Implementation Plan

### Step 1: Country Lens extraction script

**New file**: `pipeline/phase_4/extract_country_lens.py`

**Logic**:
1. Accept `centroid_id`, `month` (YYYY-MM), `country_code` (e.g. "RU", "US", "IL")
2. Query all titles for that centroid+month from outlets of that country:
   ```sql
   SELECT t.title_display, t.publisher_name, t.pubdate_utc, t.detected_language
   FROM titles_v3 t
   JOIN title_assignments ta ON ta.title_id = t.id
   JOIN feeds f ON f.id = t.feed_id
   WHERE ta.centroid_id = $1
     AND t.pubdate_utc >= ($2 || '-01')::date
     AND t.pubdate_utc < (($2 || '-01')::date + interval '1 month')
     AND f.country_code = $3
   ```
3. If < 10 titles — skip (insufficient data), return `{skipped: true, reason: "insufficient", count: N}`
4. Sample up to 150 titles (time-stratified, round-robin by publisher within each day)
5. Send to LLM with a new prompt:
   - System: "You are a media-framing analyst specializing in national media ecosystems."
   - User prompt includes: centroid label, month, country name, sampled titles with `[publisher] [date] headline`
   - Ask for 2-4 narrative frames that characterize how THIS COUNTRY'S media covers this centroid
   - Each frame: label, description (2-3 sentences), stance (how this framing positions the country's interests), key publishers within the country that push this frame
6. Parse response, store in `country_lens` table

**Reuse**: `sample_titles()` from `extract_event_narratives.py` (time-stratified sampling), `call_llm_sync()` from `core/llm_utils.py`

### Step 2: Database table

**New file**: `db/migrations/20260307_create_country_lens.sql`

```sql
CREATE TABLE country_lens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centroid_id TEXT NOT NULL REFERENCES centroids_v3(id),
    month DATE NOT NULL,
    country_code TEXT NOT NULL,
    title_count INTEGER NOT NULL,
    frames JSONB NOT NULL,
    -- frames: [{label, description, stance, title_count, key_publishers}]
    raw_response TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(centroid_id, month, country_code)
);

CREATE INDEX idx_country_lens_centroid_month ON country_lens(centroid_id, month);
```

### Step 3: CLI entry point

Same script (`extract_country_lens.py`) with `main()` + argparse:
- `--centroid EUROPE-UKRAINE --month 2026-03 --country RU` — single extraction
- `--centroid EUROPE-UKRAINE --month 2026-03 --top N` — auto-detect top N countries by title count for this centroid+month, extract all
- `--centroid EUROPE-UKRAINE --month 2026-03 --all` — all countries with >= 10 titles
- Prints results to stdout for quick review

### Step 4: Admin API endpoint (on-demand)

**New file**: `apps/frontend/app/api/country-lens/route.ts`

- POST `{centroid_id, month, country_code?}`
- If `country_code` provided: extract for that country
- If not: find top 5 countries by title count, extract all
- Auth-gated (session check)
- Calls extraction script via the existing FastAPI extraction service pattern

**Update**: `api/extraction_api.py` — add `/country-lens` endpoint that imports and calls the extraction function.

### Step 5: Simple results page (admin-only, minimal)

**New file**: `apps/frontend/app/[locale]/c/[centroid_key]/lens/page.tsx`

- URL: `/c/EUROPE-UKRAINE/lens?month=2026-03`
- Shows country flags + country name for each extracted lens
- Under each country: 2-4 narrative frame cards (label + description + stance + key publishers)
- Side-by-side comparison layout (grid of country columns)
- "Extract" button to trigger on-demand extraction for missing countries
- No public nav link initially — accessed directly by URL

---

## Files to create/modify

| File | Action |
|------|--------|
| `db/migrations/20260307_create_country_lens.sql` | CREATE |
| `pipeline/phase_4/extract_country_lens.py` | CREATE |
| `api/extraction_api.py` | ADD `/country-lens` endpoint |
| `apps/frontend/app/api/country-lens/route.ts` | CREATE (proxy to FastAPI) |
| `apps/frontend/app/[locale]/c/[centroid_key]/lens/page.tsx` | CREATE (results page) |
| `apps/frontend/lib/queries.ts` | ADD `getCountryLens()` query |
| `apps/frontend/lib/types.ts` | ADD `CountryLens` type |

---

## Key decisions

- **JSONB frames column** (not separate rows per frame) — keeps it simple, one row per centroid+month+country
- **Minimum 10 titles** to extract — below that, narrative detection is unreliable
- **2-4 frames per country** — fewer than general narratives (3-5) because single-country coverage is narrower
- **Cross-track by design** — query joins on centroid_id only, no track filter
- **No DE translation initially** — experimental phase, English only

---

## Verification

1. Run migration on local DB
2. Test CLI: `python -m pipeline.phase_4.extract_country_lens --centroid EUROPE-UKRAINE --month 2026-03 --top 3`
3. Verify `country_lens` table has rows with valid JSONB frames
4. Test API endpoint via curl
5. Visit `/c/EUROPE-UKRAINE/lens?month=2026-03` and verify display

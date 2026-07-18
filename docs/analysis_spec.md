# WorldBrief Data Analysis Spec

**For:** Claude Code analysis session (separate window)
**Context:** WorldBrief is a news intelligence platform. Pipeline ingests RSS titles, classifies them by country/topic, clusters into events, generates summaries. Goal: identify what computed content would be most interesting to paid users.

## Database Access

```bash
cd C:\Users\Maksim\Documents\SNI
# All queries via: python -c "import psycopg2; from core.config import config; ..."
# Or: node -e "const { Pool } = require('pg'); ..."
# Config loads from .env automatically
```

## Key Tables

| Table | What | Key columns |
|-------|------|-------------|
| `titles_v3` | Raw news titles (~100k+) | `id`, `title_display`, `publisher_name`, `detected_language`, `centroid_ids[]`, `processing_status`, `pubdate_utc`, `created_at` |
| `title_labels` | LLM-extracted labels per title | `title_id`, `actor`, `action_class`, `domain`, `persons[]`, `orgs[]`, `places[]`, `commodities[]`, `policies[]`, `systems[]`, `named_events[]` |
| `title_assignments` | Title -> centroid + track mapping | `title_id`, `centroid_id`, `track`, `ctm_id` |
| `centroids_v3` | Countries/entities (~85 active) | `id`, `label`, `class` (geo/thematic/non-state), `iso_codes[]`, `primary_theater`, `is_active` |
| `ctm` | Centroid-Track-Month buckets | `id`, `centroid_id`, `track`, `month`, `title_count`, `summary_text`, `is_frozen` |
| `events_v3` | Clustered events within CTMs | `id`, `ctm_id`, `title`, `summary`, `source_batch_count`, `date`, `is_catchall`, `bucket_key` |
| `narratives` | Extracted narrative frames | `id`, `entity_type` (epic/event/ctm), `entity_id`, `title`, `narrative_text`, `signal_stats` (JSONB), `rai_signals` (JSONB) |
| `track_configs` | Track definitions | `id`, `track_key` (geo_politics/geo_economy/geo_security), `label` |
| `feeds` | RSS feed sources | `id`, `name`, `url`, `language`, `is_active` |

## Tracks (3 per country)

- `geo_politics` -- governance, elections, legislation, protests
- `geo_economy` -- trade, markets, sanctions, infrastructure
- `geo_security` -- military, conflict, defense, terrorism

## Analysis Tasks

### 1. Content Richness Map
Which countries/entities have the richest content? Rank by:
- Title count (last 30 days)
- Event count (non-catchall)
- Source diversity (distinct publishers)
- Language diversity
- Summary coverage (% events with prose summaries)
- Narrative coverage (has extracted narratives?)

**Output:** Top 20 richest centroids, bottom 20 (thin coverage). This tells us where the product is strongest.

### 2. Signal Network Analysis
The `title_labels` table has extracted persons, orgs, places, commodities, policies per title. Analyze:
- Most mentioned persons globally (top 50) + which countries they appear in
- Most mentioned orgs (top 50) + cross-country reach
- Person-org co-occurrence: who appears with which organizations?
- Cross-country signal overlap: which persons/orgs bridge multiple centroids?

**Why:** Cross-country signal networks are premium content. "TRUMP appears in 45 countries' coverage" or "IMF mentioned across 30 countries" -- this is the kind of computed insight users would pay for.

### 3. Event Scale Distribution
- Distribution of events by source_batch_count (how many titles per event?)
- What % of events are "big stories" (50+ sources)?
- What are the biggest events right now (most sources)?
- How many events are catchall vs real topics?

**Why:** Big stories with many sources are high-value. The biggest events could power a "Top Stories" feature.

### 4. Temporal Patterns
- Title ingestion volume by day of week
- Which countries have the most consistent coverage?
- Staleness: how many CTMs haven't had new titles in 7+ days?
- Event lifecycle: average time from first_seen to last title added

### 5. Track Balance
- Per centroid: how balanced are the 3 tracks? (some countries may be 90% security, 5% economy, 5% politics)
- Which tracks are underpopulated globally?
- Track balance could inform editorial gaps

### 6. Bilateral Coverage
Events have a `bucket_key` for bilateral relationships (e.g., "US-China", "Russia-Ukraine").
- What are the most active bilateral pairs?
- Which bilateral relationships have the most events?
- Any "hidden" bilateral activity (countries that co-occur in titles but don't have explicit bilateral events)?

### 7. Publisher Landscape
- Top 50 publishers by title count
- Publisher diversity per country (are some countries single-source?)
- Language distribution of titles
- Any publishers dominating specific tracks?

## Output Format

Write results as markdown with tables and key insights. Save to `out/analysis_*.md`. Focus on actionable findings -- what could become paid features, where content is weak, what's most interesting to users.

## Paid Feature Ideas to Evaluate

Based on the data, assess feasibility of:
1. **Global Signal Tracker** -- track a person/org across all countries (e.g., "Where is Elon Musk in the news?")
2. **Top Stories ranking** -- events ranked by source count, updated daily
3. **Bilateral Dashboard** -- interactive relationship maps
4. **Country Risk Score** -- computed from signal density in security track
5. **Trend Detection** -- new persons/orgs appearing for the first time in a country
6. **Cross-Country Narrative Comparison** -- same event, different country perspectives

Don't just query -- interpret. What patterns would surprise a geopolitics analyst? What would they pay $10/month for?

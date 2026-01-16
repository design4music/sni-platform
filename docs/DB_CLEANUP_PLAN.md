# Database Cleanup Plan for Production Deployment

## Overview

The current `sni_v2` database contains legacy tables from previous pipeline iterations. For production deployment, we need a clean database schema containing only the tables actively used by the current pipeline and frontend.

## Minimal Required Tables for Production

### Core Pipeline Tables

1. **titles_v3** - Raw RSS feed items
   - Stores all ingested articles from RSS feeds
   - Referenced by: Phase 2, Phase 3, Phase 4
   - Required columns: id, title, url, published_at, feed_id, language_code, processing_status, etc.

2. **taxonomy_v3** - Centroid keyword definitions
   - Contains keywords/aliases for each centroid
   - Referenced by: Phase 2 (centroid matching)
   - Required columns: centroid_id, term, language_code, type (keyword/alias)

3. **centroids_v3** - Geographic and thematic centroids
   - Master list of all centroids (countries, regions, themes, non-state actors)
   - Referenced by: Phase 2, Phase 3, Frontend
   - Required columns: id, label, type, primary_theater, description, iso_code

4. **track_configs** - Track definitions and prompts
   - Defines strategic tracks (geo_politics, geo_security, etc.)
   - Referenced by: Phase 3
   - Required columns: track_key, label, description, gating_prompt, assignment_prompt

5. **ctm** - Centroid-Track-Month aggregations
   - Stores events digest and summaries for each centroid/track/month combination
   - Referenced by: Phase 4, Frontend
   - Required columns: id, centroid_id, track, month, title_count, events_digest, summary_text, is_frozen

6. **rss_feeds** - RSS feed sources
   - List of all monitored RSS feeds
   - Referenced by: Phase 1
   - Required columns: id, name, url, country_code, language_code, is_active

### Join/Support Tables

7. **title_centroids** - Many-to-many: titles to centroids
   - Links titles to their assigned centroids (multi-centroid support)
   - Required columns: title_id, centroid_id

8. **title_tracks** - Many-to-many: titles to tracks
   - Links titles to their assigned tracks within centroids
   - Required columns: title_id, centroid_id, track

## Legacy Tables to Remove

The following tables are from previous pipeline iterations and are NOT used by the current system:

- `titles` (old v1/v2 schema)
- `enriched_facts` / `event_frames` (old Phase 3/4)
- `framed_narratives` (deprecated framing phase)
- `entity_*` tables (old entity extraction)
- `neo4j_*` tables (deprecated graph database integration)
- Any other tables not listed in "Required Tables" above

## Recommended Approach

### Option 1: Clean Migration (Recommended)

**Pros:** Clean start, no legacy baggage, easier to maintain
**Cons:** Requires re-running pipeline to populate data

**Steps:**
1. Create new database: `worldbrief_production`
2. Apply clean migrations from scratch (schema only)
3. Migrate essential reference data:
   - `centroids_v3` (master centroid list)
   - `taxonomy_v3` (keywords/aliases)
   - `track_configs` (track definitions)
   - `rss_feeds` (active feeds list)
4. Run pipeline to populate `titles_v3` and `ctm`
5. Verify frontend displays correctly
6. Update `.env` to point to new database

### Option 2: In-Place Cleanup

**Pros:** Preserves existing title/CTM data
**Cons:** Risk of missing dependencies, harder to verify completeness

**Steps:**
1. Backup current database: `pg_dump sni_v2 > backup_$(date +%Y%m%d).sql`
2. Create list of tables to keep (see Required Tables above)
3. Generate DROP TABLE statements for all other tables
4. Review and execute DROP statements
5. Verify pipeline and frontend still work

## Database User Permissions

For production deployment, create least-privileged database users:

### Pipeline User (Read/Write)
```sql
CREATE USER pipeline_writer WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON titles_v3, title_centroids, title_tracks, ctm TO pipeline_writer;
GRANT SELECT ON centroids_v3, taxonomy_v3, track_configs, rss_feeds TO pipeline_writer;
```

### Frontend User (Read-Only)
```sql
CREATE USER frontend_reader WITH PASSWORD 'secure_password';
GRANT SELECT ON centroids_v3, ctm, titles_v3, title_centroids, title_tracks, rss_feeds TO frontend_reader;
```

### Admin User (Full Access)
```sql
-- Use existing postgres user or create dedicated admin
CREATE USER worldbrief_admin WITH PASSWORD 'secure_password' CREATEDB;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO worldbrief_admin;
```

## Migration Scripts Location

Clean migration scripts should be created in:
```
/db/migrations/production/
  01_create_tables.sql
  02_create_indexes.sql
  03_create_users.sql
  04_seed_reference_data.sql
```

## Verification Checklist

After cleanup/migration:
- [ ] Pipeline Phase 1 can ingest new titles
- [ ] Pipeline Phase 2 can match titles to centroids
- [ ] Pipeline Phase 3 can assign tracks
- [ ] Pipeline Phase 4 can generate events digest and summaries
- [ ] Frontend home page displays centroids
- [ ] Frontend centroid pages show CTMs
- [ ] Frontend CTM pages show events and summaries
- [ ] No broken foreign key constraints
- [ ] All active RSS feeds are present

## Next Steps

1. **Manual Review Required:** Max to review this plan and decide on Option 1 vs Option 2
2. **Backup:** Create full backup before any destructive operations
3. **Testing:** Test chosen approach on local copy first
4. **Documentation:** Document final schema in `/docs/DATABASE_SCHEMA.md`

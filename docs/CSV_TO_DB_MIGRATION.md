# CSV → Database Migration: Strategic Vocabulary Loading

## Overview

Migration from CSV-based entity vocabulary loading to database-backed system using the `data_entities` table.

**Status**: Ready for testing
**Date**: 2025-10-15

---

## What Changed

### Before (CSV-based)
```
strategic_gate.py
    ↓
taxonomy_extractor.py
    ↓
vocab_loader.py (reads CSV files)
    ↓
data/actors.csv (~50 entities)
data/go_people.csv (~30 entities)
data/stop_culture.csv
```

### After (Database-backed)
```
strategic_gate.py (simplified - no config validation)
    ↓
taxonomy_extractor.py (uses vocab_loader_db)
    ↓
vocab_loader_db.py (queries data_entities table)
    ↓
PostgreSQL: data_entities table
    - COUNTRY entities (enriched with Wikidata)
    - PERSON entities (enriched with Wikidata)
    - ORG entities (enriched with Wikidata)
    - CAPITAL entities (enriched with Wikidata)
    - Multilingual aliases in JSONB
```

---

## Files Modified

### 1. **apps/filter/vocab_loader_db.py** (NEW)
- Database-backed vocabulary loader
- Same interface as `vocab_loader.py`
- Queries `data_entities` table by entity_type
- Flattens JSONB aliases across all languages
- Falls back to CSV for `stop_culture` (not migrated yet)

**Key Functions:**
- `load_actor_aliases()` → Loads COUNTRY, ORG, CAPITAL entities
- `load_go_people_aliases()` → Loads PERSON entities
- `load_stop_culture_phrases()` → Falls back to CSV loader
- `_load_entities_by_type()` → Core DB query logic

### 2. **apps/filter/taxonomy_extractor.py** (MODIFIED)
- Factory function `create_multi_vocab_taxonomy_extractor()` now imports from `vocab_loader_db`
- Removed config path dependencies
- No other changes - maintains same interface

**Changes:**
```python
# Before
from apps.filter.vocab_loader import load_actor_aliases, ...
go_actors = load_actor_aliases(config.actors_csv_path)

# After
from apps.filter.vocab_loader_db import load_actor_aliases, ...
go_actors = load_actor_aliases()  # No path needed
```

### 3. **apps/filter/strategic_gate.py** (MODIFIED)
- Removed `_validate_config()` method
- Removed config path validation
- Removed unused `get_config()` import
- Simplified initialization

**Changes:**
```python
# Before
def __init__(self):
    self.config = get_config()
    self._validate_config()
    self._taxonomy_extractor = create_multi_vocab_taxonomy_extractor()

# After
def __init__(self):
    self._taxonomy_extractor = create_multi_vocab_taxonomy_extractor()
```

### 4. **apps/filter/test_db_migration.py** (NEW)
- Comprehensive test script
- Validates DB loader functionality
- Compares CSV vs DB output (when both available)
- Tests strategic gate integration
- Provides migration validation report

---

## Data Migration Status

### Migrated to `data_entities` table:
- ✅ **COUNTRY** entities - From Wikidata + actors.csv
- ✅ **CAPITAL** entities - From Wikidata
- ✅ **ORG** entities - From Wikidata
- ✅ **PERSON** entities - From go_people.csv + Wikidata enrichment

### Not yet migrated:
- ⏳ **stop_culture.csv** - Still loaded from CSV (uses legacy loader)
- ⏳ **go_taxonomy.csv** - Not yet defined (returns empty dict)

---

## Benefits of Database-Backed System

### 1. **Scalability**
- CSV parsing on every gate initialization → Single DB query
- No file I/O bottleneck
- Query optimization via indexes
- Prepared statement caching

### 2. **Multilingual Enrichment**
- CSV: Limited to manually entered aliases
- DB: Wikidata-enriched with 10+ languages per entity
- JSONB storage: Efficient language-specific querying

### 3. **Maintainability**
- CSV: Manual editing, prone to format errors
- DB: Structured schema with constraints
- Easy bulk updates via SQL or import scripts

### 4. **Flexibility**
- Add new entity types without code changes
- Filter by metadata (wikidata_qid, domains_hint, country_entity_id)
- Future: Real-time entity updates, version control

### 5. **Performance**
- GIN indexes on aliases for fast substring matching
- Full-text search capability on names
- Reduced memory footprint (query on demand vs loading entire CSV)

---

## Testing the Migration

### 1. Validate Database is Populated
```bash
python apps/filter/vocab_loader_db.py
```
Expected output:
```
Database-backed Vocabulary Validation
========================================
Database accessible: True
Actor entities: ~250
Go people entities: ~30
Total actor aliases: ~1500+
...
All vocabularies loaded successfully from database!
```

### 2. Run Comprehensive Migration Test
```bash
python apps/filter/test_db_migration.py
```

This will:
- Test DB loader independently
- Test CSV loader (if available)
- Compare outputs (if both available)
- Test strategic gate integration
- Provide pass/fail summary

### 3. Run P2 Strategic Filtering
```bash
# Your existing P2 pipeline script should work unchanged
python apps/filter/run_phase2.py  # or whatever your entry point is
```

---

## Rollback Plan

If issues arise, rollback is simple:

**Option 1: Revert single file**
```bash
# Revert taxonomy_extractor.py to use CSV loader
git checkout HEAD~1 apps/filter/taxonomy_extractor.py
```

**Option 2: Feature flag (add to config.py)**
```python
USE_DB_VOCAB_LOADER = False  # Toggle to False for CSV loader
```

Then in `taxonomy_extractor.py`:
```python
if get_config().USE_DB_VOCAB_LOADER:
    from apps.filter.vocab_loader_db import ...
else:
    from apps.filter.vocab_loader import ...
```

---

## Future Enhancements

### 1. Migrate stop_culture to DB
- Add `STOP_CULTURE` entity_type to `data_entities`
- Import from stop_culture.csv
- Remove CSV fallback in `vocab_loader_db.py`

### 2. Add Domain-Based Matching
- Use `domains_hint` field for publisher-based entity detection
- E.g., "whitehouse.gov" → automatically tag as "US" entity

### 3. Entity Relationships
- Link PERSON → COUNTRY via `country_entity_id`
- Link COUNTRY → CAPITAL via `capital_entity_id`
- Enable relationship-based filtering

### 4. Real-Time Updates
- API endpoint to add/update entities
- Trigger extractor pattern rebuild on entity changes
- Version tracking for entity changes

### 5. Performance Optimization
- Cache loaded vocabularies in memory (Redis/in-process)
- Lazy loading for infrequently used entity types
- Compiled regex pattern caching

---

## Troubleshooting

### Error: "data_entities table not found"
**Solution:** Run the migration:
```bash
psql -U postgres -d sni_v2 -f db/migrations/20251014_create_data_entities.sql
```

### Error: "No entities loaded from database"
**Solution:** Populate the table:
```bash
python apps/data/import_wikidata.py
python apps/data/import_csv_persons.py
```

### Error: "stop_culture.csv not found"
**Solution:** This is expected - stop_culture is still CSV-based. Ensure `data/stop_culture.csv` exists.

### Strategic gate returns unexpected results
**Solution:**
1. Check entity counts: `python apps/filter/vocab_loader_db.py`
2. Compare with CSV: `python apps/filter/test_db_migration.py`
3. Verify data_entities content: `SELECT * FROM data_entities LIMIT 10;`

---

## Code References

- **vocab_loader_db.py**: apps/filter/vocab_loader_db.py:1-250
- **taxonomy_extractor.py**: apps/filter/taxonomy_extractor.py:238-259
- **strategic_gate.py**: apps/filter/strategic_gate.py:33-41
- **test_db_migration.py**: apps/filter/test_db_migration.py:1-200

---

## Validation Checklist

Before deploying to production:

- [ ] Database `data_entities` table exists
- [ ] Table populated with entities (run `python apps/filter/vocab_loader_db.py`)
- [ ] Migration test passes (run `python apps/filter/test_db_migration.py`)
- [ ] Strategic gate test passes with sample titles
- [ ] P2 pipeline runs without errors
- [ ] Entity counts match or exceed CSV baseline
- [ ] Performance benchmarks acceptable

---

## Questions?

Check the codebase:
- Database schema: `db/migrations/20251014_create_data_entities.sql`
- Import scripts: `apps/data/import_wikidata.py`, `apps/data/import_csv_persons.py`
- Legacy CSV loader: `apps/filter/vocab_loader.py` (kept for reference)

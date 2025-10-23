# SNI-v2 Active Pipeline Code Map

## Pipeline Runner

**Main Orchestrator:**
- `run_pipeline.py` - Main pipeline orchestrator (P1→P2→P4→P5, P3 runs as separate worker)

---

## Phase 1: RSS Ingestion

**Entry Point:**
- `apps/ingest/run_ingestion.py` - CLI entry point

**Core Logic:**
- `apps/ingest/rss_fetcher.py` - RSS feed fetching
- `apps/ingest/feeds_repo.py` - Feed management

**Dependencies:**
- `data/*.csv` - RSS feed sources (if file-based)
- Database: `titles` table

---

## Phase 2: Strategic Filtering + Entity Enrichment

**Entry Point:**
- `apps/filter/run_enhanced_gate.py` - CLI entry point

**Core Logic:**
- `apps/filter/entity_enrichment.py` - Main orchestrator
- `apps/filter/taxonomy_extractor.py` - Static GO/STOP list matching
- `apps/filter/country_enrichment.py` - Auto-add countries via iso_code
- `apps/filter/vocab_loader_db.py` - Database vocabulary loader
- `apps/filter/enhanced_p2_filter.py` - LLM strategic review
- `apps/filter/strategic_gate.py` - Legacy gate logic
- `apps/filter/title_processor_helpers.py` - Helper functions

**Dependencies:**
- Database: `data_entities` table
- Database: `taxonomy_terms` table
- Neo4j: Network intelligence (optional)
- Database: `titles` table (updates `gate_keep`, `entities`)

---

## Phase 3: Event Family Generation

**Entry Point:**
- `apps/generate/incident_processor.py` - Incident-based MAP/REDUCE (NEW)
  - CLI: Run directly as Python module

**Core Logic:**
- `apps/generate/map_classifier.py` - MAP: Incident clustering
- `apps/generate/reduce_assembler.py` - REDUCE: Incident analysis → EF
- `apps/generate/seed_validator.py` - P3.5a: Seed validation
- `apps/generate/thematic_validator.py` - P3.5b: Cross-batch assignment
- `apps/generate/ef_merger.py` - P3.5c: Interpretive merging
- `apps/generate/ef_splitter.py` - P3.5d: Interpretive splitting
- `apps/generate/p35_pipeline.py` - P3.5 orchestration
- `apps/generate/theater_inference.py` - Theater inference
- `apps/generate/ef_key.py` - EF key generation (SHA256 theater+type)

**Supporting:**
- `apps/generate/database.py` - Database operations for EF/FN
- `apps/generate/models.py` - EventFamily, FramedNarrative models
- `apps/generate/mapreduce_models.py` - MAP/REDUCE models
- `apps/generate/mapreduce_prompts.py` - LLM prompts

**Dependencies:**
- `data/event_types.csv` - 11 event type enums
- `data/theaters.csv` - 16 theater enums
- Database: `titles` table (reads), `event_families` table (writes)

---

## Phase 4: Event Family Enrichment

**Entry Point:**
- `apps/enrich/cli.py` - CLI entry point (command: `enrich-queue`)

**Core Logic:**
- `apps/enrich/processor.py` - EF enrichment processor
- `apps/enrich/centroid_matcher.py` - Centroid matching
- `apps/enrich/models.py` - Enrichment models

**Dependencies:**
- Database: `event_families` table (status='seed' → 'active')

---

## Phase 5: Framed Narratives

**Entry Point:**
- `apps/generate/run_framing.py` - CLI entry point (command: `process`)

**Core Logic:**
- `apps/generate/framing_processor.py` - Framed narrative generation

**Dependencies:**
- Database: `event_families` table (status='active')
- Database: `framed_narratives` table (writes)

---

## Phase 6: RAI Analysis (Manual Only)

**Entry Point:**
- `apps/generate/run_rai.py` - CLI entry point (command: `process`)

**Core Logic:**
- `apps/generate/rai_processor.py` - RAI analysis

**Dependencies:**
- RAI Service: `render.com:rai-backend`
- Database: `framed_narratives` table (updates `rai_analysis`)

---

## Core Infrastructure

**Configuration:**
- `core/config.py` - All configuration (SNIConfig class)
- `.env` - Environment variables

**Database:**
- `core/database.py` - Database session management
- `core/llm_client.py` - DeepSeek LLM integration
- `core/neo4j_sync.py` - Neo4j network intelligence (optional)

**Data Files:**
- `data/event_types.csv` - Event type enums
- `data/theaters.csv` - Theater enums
- `data/actors.csv` - Strategic actors (legacy?)
- `data/go_people.csv` - GO list: People
- `data/stop_culture.csv` - STOP list: Culture
- `data/go_taxonomy.csv` - GO list: Taxonomy

---

## Database Tables

**Primary Tables:**
- `titles` - News titles (19k records currently)
- `event_families` - Event Families
- `framed_narratives` - Framed narratives
- `data_entities` - Strategic actors & entities
- `taxonomy_terms` - GO/STOP lists

**Support Tables:**
- `feeds` - RSS feed sources (if DB-based)

---

## Utility Scripts (Not in Pipeline)

**Data Import:**
- `apps/data/import_csv_actors.py` - Import actors from CSV
- `apps/data/import_csv_persons.py` - Import persons from CSV
- `apps/data/import_wikidata.py` - Import from Wikidata

**Migrations:**
- `db/migrations/*.sql` - Database migrations
- Various `run_migration*.py` scripts

**Legacy/Archive:**
- `apps/filter/test_db_migration.py` - Test script
- `run_phase2_batch.py` - Legacy Phase 2 runner
- `run_phase2_test.py` - Legacy Phase 2 test

---

## Pipeline Execution Flows

### Current Flow (run_pipeline.py):
```
P1 (Ingest) → P2 (Filter) → [P3 skipped - separate worker] → P4 (Enrich) → P5 (Framing) → P6 (RAI)
```

### Phase 3 Background Worker (Separate):
```
P3 (Generate): Incident clustering → Analysis → P3.5a Validation → P3.5b Assignment → P3.5c Merge → P3.5d Split
```

### Manual Execution:
```bash
# Full pipeline
python run_pipeline.py run

# Individual phases
python run_pipeline.py phase1
python run_pipeline.py phase2
python run_pipeline.py phase3
python run_pipeline.py phase4
python run_pipeline.py phase5

# Daemon mode
python run_pipeline.py run --daemon --interval 360  # Every 6 hours
```

---

## Issues/Notes for Reorganization

1. **Inconsistent naming:**
   - `run_ingestion.py` vs `run_enhanced_gate.py` vs `run_framing.py`
   - Should standardize to `run_<phase>.py`

2. **Legacy files still present:**
   - `apps/filter/strategic_gate.py` (legacy?)
   - `run_phase2_*.py` (old runners)

3. **Phase 3 confusion:**
   - `incident_processor.py` is the active implementation
   - `mapreduce_processor.py` referenced in run_pipeline.py but doesn't exist?
   - Need to clarify which is active

4. **Data import scripts:**
   - In `apps/data/` but not part of pipeline
   - Should these be in `scripts/` or separate `tools/` directory?

5. **Missing:**
   - Phase 3 CLI entry point (currently runs as Python module directly)
   - Clear separation of "pipeline" vs "utilities" vs "data management"

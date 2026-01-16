 Phase 2 Bucketless Processing Architecture Plan

  Current State Analysis

  - Ingestion: Google News feeds → titles table ✅ Working
  - CLUST-1: Strategic filtering → gate_keep = true ✅ Working
  - CLUST-2: Creates buckets table → ❌ To be eliminated
  - GEN-1: Buckets → Event Families → ❌ Needs rework for direct title processing

  Target Architecture

  Core Processing Flow

  Google News → titles → [CLUST-1 Enhanced] → [GEN-1 Direct] → Event Families
                  ↓
          titles.entities populated with:
          - actors (countries/orgs from CSV)
          - people (politicians from CSV)
          - stop_words (lifestyle filter from CSV)
          - centroids (LLM-generated)

  Required Scripts & Components

  1. Enhanced CLUST-1 (apps/clust1/)

  Purpose: Strategic filtering + entity extraction into titles.entities

  Scripts needed:
  - run_enhanced_gate.py - Main orchestrator
  - entity_extractor.py - CSV vocabulary matching
  - vocab_loader.py - Load 3 CSV files (actors, people, stop_words)

  Changes to titles table schema:
  -- Already done in Phase 2 migration:
  ALTER TABLE titles ADD COLUMN entities jsonb;

  Entities structure:
  {
    "actors": ["Russia", "NATO", "Israel"],
    "people": ["Putin", "Biden", "Macron"],
    "stop_words": ["sports", "entertainment"],
    "centroid": "Ukraine conflict diplomatic response"
  }

  2. Direct GEN-1 Processing (apps/gen1/)

  Purpose: titles.entities → Event Families (no buckets)

  Scripts needed:
  - run_direct_gen1.py - Main processor
  - title_grouper.py - Group titles by entity similarity
  - centroid_generator.py - LLM-generated centroids for titles
  - ef_assembler.py - Create Event Families from title groups

  3. Supporting Infrastructure

  Migration Scripts (db/migrations/):
  - phase2_populate_entities.py - Backfill existing titles with entities
  - phase2_cleanup_buckets.py - Remove bucket tables (after testing)

  Vocabulary Management (data/):
  - actors.csv - Countries, organizations
  - go_people.csv - Politicians, public figures
  - stop_culture.csv - Lifestyle/sports terms
  - update_vocabs.py - Vocabulary maintenance script (future, we do it manually)

  Testing Scripts:
  ALWAYS place testing scripts into Tests/ Folder!
  - test_clust1_enhanced.py - Test entity extraction
  - test_direct_gen1.py - Test bucketless Event Family creation
  - validate_phase2.py - End-to-end validation

  Implementation Phases

  Phase 2A: Enhanced CLUST-1

  1. Vocabulary Management
    - Open data/ directory with 3 CSV files
    - Open apps/clust1/vocab_loader.py to load vocabularies
    - Find entity_extractor.py for CSV matching in apps/clust1/taxonomy_extractor.py also see apps/clust2/actor_sets.py
  2. Enhanced Gate Processing
    - Modify CLUST-1, CLUST-2 to populate titles.entities
    - Strategic filtering + entity extraction in one pass
    - Backfill existing titles with entities

///////////// make a big pause here to review results /////////////////

  Phase 2B: Direct GEN-1

  3. Title Grouping Logic
    - Group titles by entity similarity (no buckets)
    - Use titles.entities for fast LLM preprocessing
    - Generate centroids for ongoing narrative themes
  4. Event Family Assembly
    - LLM processes title groups directly
    - Create Event Families and Framed Narratives
    - Assign titles to Event Families via titles.event_family_id

  Phase 2C: Testing & Cleanup

  5. Validation & Testing
    - End-to-end pipeline testing
    - Performance comparison vs bucket-based approach
    - Data quality validation
  6. Cleanup
    - Drop bucket tables after successful testing
    - Remove unused columns from titles table
    - Update documentation

  Key Benefits of This Architecture

  1. Simplified Data Flow: titles → entities → Event Families (no intermediate buckets)
  2. Faster Processing: LLM works with pre-extracted entities instead of raw text
  3. Better Grouping: Entity-based similarity more accurate than text similarity
  4. Scalable: Direct title processing scales better than bucket management
  5. Flexible: Easy to add new vocabularies or entity types

  Critical Dependencies

  - Vocabulary Files: Need 3 CSV files with current taxonomies
  - Entity Extraction Logic: Efficient matching against CSV vocabularies
  - LLM Prompt Engineering: Adapt prompts for entity-based processing
  - Database Performance: Ensure titles.entities queries are optimized
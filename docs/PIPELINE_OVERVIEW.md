# SNI-v2 Pipeline Overview

**Orchestrator:** `run_pipeline.py` - Runs phases in sequence with timeout protection and checkpoint/resume

## Phase 1: Ingest (apps/ingest/)
**Script:** `run_ingestion.py`

Fetch headlines from RSS feeds and store them in the database. Uses conditional GET requests with ETag caching to avoid re-fetching unchanged content. Extracts publisher information, detects language, normalizes title text with Unicode NFKC, and generates content hashes for deduplication. Each title enters the pipeline with `processing_status = 'pending'`.

## Phase 2: Strategic Gate (apps/filter/)
**Script:** `run_enhanced_gate.py`

Filter titles to identify strategically significant content. Uses static taxonomy matching first (countries, organizations, strategic keywords), then falls back to LLM review for ambiguous titles. Extracts actor entities and populates the `titles.entities` column. Parallel processing with controlled concurrency. Strategic titles get `gate_keep = true` and move forward; non-strategic titles are filtered out. All LLM interactions handled by `core/llm_client.py`.

## Phase 3: Event Family Generation (apps/generate/)
**Background worker** - Runs independently

Group related strategic titles into Event Families (ongoing sagas). Uses triple-key matching: same actors + same theater + same event type = one Event Family. Designed for cross-language consolidation and anti-fragmentation. Absorbs repeated incidents into existing patterns rather than creating duplicate families. Outputs Event Families with canonical summaries.

## Phase 4: Enrichment (apps/enrich/)
**Script:** `processor.py`

Add strategic context to Event Families. Extracts canonical actors with roles, identifies temporal patterns and magnitude baselines, assesses policy status, and matches to narrative centroids. Enhances summaries with comparable precedents and abnormality assessment. Creates enrichment records stored as JSON sidecars in the database.

## Phase 5: Framed Narrative (Future)
**Not yet implemented**

Analyze how different media outlets frame the same Event Family. Identify distinct narratives with supporting evidence from headlines. Track evaluative and causal framing patterns across sources.

---

**Key Components:**
- `core/llm_client.py` - All LLM prompts and interactions in one place
- `core/config.py` - Centralized configuration with environment variable overrides
- `core/checkpoint.py` - Checkpoint/resume system for reliability
- `apps/filter/title_processor_helpers.py` - Shared title processing utilities

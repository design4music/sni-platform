# SNI-v2 Pipeline Flow & Architecture

*Updated: September 23, 2025 - Production-Ready Timeout Mitigation Implementation*

# Project Vision (SNI / SNE)

**Goal.** Turn raw multi-source news into a small set of long-lived, strategic **Event Families (EFs)** and their **Framed Narratives (FNs)**—so analysts see the big stories, not a flood of one-offs.

**What the platform does (end-to-end).**

* **Ingest** new items from configured RSS feeds; dedupe; store titles.
* **Strategic gate** each title: extract geopolitical actors, drop non-strategic items via stop-lists; mark "strategic".
* **Generate EFs (Incident-First)** via hybrid processing: Incident clustering → Analysis → Single-title EF seeds for orphans. Achieves 100% strategic coverage with optimal incident grouping.
* **Merge EFs (Cross-batch)** across batches using ef_key matching: consolidate families that share **theater + event_type**; reunite lost siblings.
* **Generate FNs** per EF: surface 1–3 dominant frames with headline-level evidence (UUIDs).
* **Continuous upkeep (cron)**: periodically re-scan previously created EFs and **merge newly created with historical** ones to keep families long-lived and coherent.

**Principles.**

* **Incident-first processing:** Identify strategic incidents first, then classify them - prevents EF fragmentation
* **100% strategic coverage:** Every strategic title becomes either part of incident cluster or single-title EF seed
* **Anti-fragmentation:** Cross-batch ef_key merging reunites lost siblings; early signals preserved for epic events
* **Strategic scope only:** diplomacy, military, economy, domestic politics, tech/regulation; exclude sports/celebrity/local crime.
* **Evidence discipline:** all FN claims cite actual title UUIDs.

**Outputs.**

* A compact set of active **Event Families** (by **theater** and **event_type**), each with linked titles.
* **100% strategic title coverage** - no strategic content left unprocessed
* **Framed Narratives** per EF showing how media position the same saga.

**Run mode.**

* One orchestrated script can execute the full cycle; individual phases are callable for ops/testing.

## Architecture Overview

The SNI (Strategic Narrative Intelligence) system operates a **hybrid incident-first pipeline** that transforms raw RSS feeds into strategic Event Families with zero fragmentation. The system emphasizes **semantic incident clustering** before classification to ensure related events stay together.

### Core Data Flow
```
RSS Sources → Ingestion → Strategic Gating → Entity Extraction → Incident-First EF Generation
```

## Pipeline Components

### 1. RSS Ingestion (P1)
**Entry Point:** `python -m apps.ingest.run_ingestion`
**Purpose:** Collect news articles from 137+ configured RSS feeds
**Input:** RSS feed URLs from `feeds` table
**Output:** New records in `titles` table with `processing_status='pending'`

**Features:**
- Google News RSS aggregation across strategic sources
- Content deduplication via hashing
- Multi-language support (English, Arabic, French, etc.)
- Automatic publisher domain extraction
- **Resumable batch processing** with checkpoint-based recovery
- **Feed-based cursor** tracking via `last_feed_id`

**Timeout Mitigation:**
- `--batch` flag for configurable feed batch size (default: 500)
- `--resume` flag to continue from last checkpoint
- Checkpoint tracking: `logs/checkpoints/p1_ingest.json`
- Atomic checkpoint updates with temp file operations
- Cron-compatible with `flock` and `timeout` protection

**Performance:**
- Standard: ~2,000-5,000 titles ingested per run (varies by news cycle)
- Batch mode: 137+ feeds processed in batches with checkpoint resume capability

### 2. Enhanced Strategic Gate + Entity Processing (P2)
**Entry Point:** `python -m apps.filter.run_enhanced_gate`
**Purpose:** Combined strategic filtering and entity extraction in one pass
**Input:** Titles with `processing_status='pending'`
**Output:** Updates `gate_keep`, `gate_reason`, `entities`, `gate_score`, `gate_actor_hit`

**Strategic Filtering Logic:**
- Actor matching against `actors.csv` (countries, organizations, leaders)
- People matching against `go_people.csv` (strategic individuals)
- Content filtering via `stop_culture.csv` (excludes sports, entertainment)
- Strategic hit rate: ~10-30% depending on news cycle

**Entity Extraction:**
- Real-time actor extraction during gating
- JSON storage in `titles.entities` field with proper serialization
- Version tracking for extraction evolution
- Actor canonicalization (e.g., "Putin" → "RU")

**Timeout Mitigation:**
- `--batch` flag for configurable title batch size (default: 1000)
- `--resume` flag to continue from last checkpoint
- Checkpoint tracking: `logs/checkpoints/p2_filter.json`
- **Title-based cursor** tracking via `last_title_id`
- Idempotent processing with duplicate protection
- Cron-compatible with `flock` and `timeout` protection

**Execution:**
```bash
# Standard processing
python -m apps.filter.run_enhanced_gate --hours 24 --max-titles 1000

# Batch processing with resume capability
python -m apps.filter.run_enhanced_gate --batch 1000 --resume
```

### 3. Hybrid Incident-First Event Family Generation (P3)
**Entry Point:** `python -m apps.generate.incident_processor`
**Purpose:** Incident-first EF generation with 100% strategic title coverage
**Input:** Strategic titles where `event_family_id IS NULL`
**Output:** Creates `event_families` records with zero fragmentation

**Background Worker Architecture:**
- **Continuous processing** via `--background` flag (systemd service)
- **No batch/resume needed** - designed as persistent worker
- Automatic batch size management (configurable max_titles parameter)
- Built-in error recovery and retry logic
- Single worker instance prevents concurrency conflicts

#### Hybrid Incident-First Architecture
- **MAP Phase:** Semantic incident clustering via LLM analysis
  - Identifies strategic incidents across title batches (100 per batch)
  - Groups related titles by: temporal proximity, causal relationships, strategic coherence
  - Examples: "Charlie Kirk Assassination and Aftermath", "Poland-Russia Border Incident"
- **REDUCE Phase:** Incident analysis and EF generation
  - Analyzes each incident cluster → (theater, event_type) + EF content
  - Generates chronological event timelines within incidents
  - Same logic handles both multi-title and single-title clusters
- **Orphan Processing:** Single-title EF seeds for unclustered strategic content
  - Detects titles not belonging to incidents
  - Creates single-title EF seeds for early signals and isolated events
  - Uses same REDUCE logic for consistency
- **Cross-Batch Merging:** ef_key matching reunites lost siblings
  - Merges incidents with same ef_key (theater + event_type hash)
  - Lost siblings from different batches automatically reunite
  - Preserves early signals as seeds for future epic events

#### Performance Characteristics
- **Coverage:** 100% strategic title processing (incidents + singles)
- **Throughput:** 50 titles → 20 EFs (16 incidents + 4 single-title EFs)
- **Merging:** Cross-batch incident merging via ef_key matching
- **Quality:** Semantic incident clustering prevents fragmentation
- **API Optimization:** Parallel processing with configurable concurrency

#### Production Configuration
```python
# Optimized settings (core/config.py)
map_concurrency: int = 8        # Parallel incident clustering
reduce_concurrency: int = 12    # Parallel incident analysis
map_batch_size: int = 100       # Titles per clustering call
llm_max_tokens_generic: int = 8000   # Near DeepSeek 8K limit
```

**Execution:**
```bash
# One-time processing up to N titles
python -m apps.generate.incident_processor 500

# Background worker mode (production systemd service)
python -m apps.generate.incident_processor 1000 --background
```

#### Problem Solved: EF Fragmentation
**Before (Event-First):**
- Poland drone incident → 5 headlines → 3 separate EFs (fragmented)
- Lost siblings across batches → no reunification
- Early signals → missed or ignored
- 42% strategic titles unclustered

**After (Incident-First + Hybrid):**
- Poland drone incident → 5 headlines → 1 EF (clustered)
- Cross-batch merging via ef_key → siblings reunite
- Single-title EF seeds → early signals preserved
- 100% strategic coverage

### 4. Anti-Fragmentation Philosophy

**Core Principle:** Fight political information fragmentation by:
- **Incident-first clustering:** Identify strategic incidents before classification
- **Semantic coherence:** Group related events by narrative threads, not just keywords
- **Cross-batch discovery:** ef_key merging reunites lost siblings across processing batches
- **Early signal preservation:** Single-title EF seeds capture emerging strategic trends
- **Time-flexible coherence:** Events can span hours to weeks within incidents

**Quality Metrics:**
- 100% strategic title coverage (incident clusters + single-title EF seeds)
- Cross-batch incident merging success (ef_key matching)
- Zero EF fragmentation for related strategic events
- High semantic clustering quality via LLM incident identification

## Timeout Mitigation Strategy

### Production Architecture
The SNI pipeline implements a comprehensive timeout mitigation strategy with phase-specific approaches:

**Phase-Specific Strategies:**
- **P1 Ingest & P2 Filter:** Resumable batch processing with checkpoint recovery
- **P3 Generate:** Background systemd worker with continuous processing
- **P4 Enrich:** Resumable batch processing with checkpoint recovery

**Core Features:**
- **Checkpoint-based Resume:** All phases (P1, P2, P4) support `--resume` flag
- **Configurable Batch Sizes:** `--batch` parameter for processing control
- **Atomic Operations:** Checkpoint updates with temp file operations
- **Idempotent Processing:** Safe to rerun without data corruption
- **Lock Protection:** `flock` prevents concurrent execution
- **Timeout Guards:** `timeout` command protects against hanging processes

**Cron Configuration:**
- **P1 & P2 & P4:** 12-hour intervals with batch processing and resume capability
- **P3:** Continuous systemd background service
- See `docs/cron_setup.md` for complete production deployment guide

## Complete Pipeline Execution

### Unified Pipeline Orchestrator (Development)
**Entry Point:** `python run_pipeline.py`
**Purpose:** Single command execution for development and testing

```bash
# Complete pipeline (P1, P2, P4 only - P3 runs as background service)
python run_pipeline.py run

# Individual phases with timeout mitigation
python run_pipeline.py phase1 --batch 500 --resume     # RSS ingestion
python run_pipeline.py phase2 --batch 1000 --resume    # Strategic filtering
python run_pipeline.py phase4 --batch 50 --resume      # EF enrichment

# Note: P3 Generate runs as background systemd service, not via pipeline orchestrator

# Pipeline status monitoring
python run_pipeline.py status
```

### Production Cron Schedule
```bash
# P1 Ingest - Every 12 hours with timeout protection
0 6,18 * * * cd /path/to/SNI && timeout 30m flock -n /tmp/p1_ingest.lock python apps/ingest/run_ingestion.py --batch 500 --resume

# P2 Filter - Every 12 hours, 30 min after P1
30 6,18 * * * cd /path/to/SNI && timeout 15m flock -n /tmp/p2_filter.lock python apps/filter/run_enhanced_gate.py --batch 1000 --resume

# P4 Enrich - Every 12 hours, 30 min after P2
0 7,19 * * * cd /path/to/SNI && timeout 45m flock -n /tmp/p4_enrich.lock python apps/enrich/cli.py enrich-queue --batch 50 --resume

# P3 Generate - Continuous systemd background service (no cron needed)
# sudo systemctl enable sni-p3-generate.service
```

### Manual Processing (Development/Testing)
```bash
# 1. Ingest latest news with batch processing
python -m apps.ingest.run_ingestion --batch 500 --resume

# 2. Enhanced gating with batch processing
python -m apps.filter.run_enhanced_gate --batch 1000 --resume

# 3. Start background EF generation worker
python -m apps.generate.incident_processor 1000 --background

# 4. EF Enrichment with batch processing
python -m apps.enrich.cli enrich-queue --batch 50 --resume
```

### Performance Benchmarks (With Timeout Mitigation)
- **P1 RSS Ingestion:** ~3-5 minutes for 137 feeds
  - Batch mode: Configurable feed batch size with checkpoint resume
  - Timeout protection: 30-minute limit with automatic recovery
- **P2 Enhanced Gating:** ~30-60 seconds for 1,000 titles
  - Batch mode: Configurable title batch size with checkpoint resume
  - Timeout protection: 15-minute limit with automatic recovery
- **P3 Incident-First Processing:** ~3-4 minutes for 50 titles → 20 EFs (100% coverage)
  - Background worker: Continuous processing with automatic restart
  - MAP Phase: ~1.5 minutes for incident clustering
  - REDUCE Phase: ~1.5 minutes for incident analysis + orphan processing
  - Cross-batch merging: Real-time via ef_key matching
- **P4 EF Enrichment:** ~8.4s per EF (426 EFs/hour, 93.1% success rate)
  - Batch mode: Configurable EF batch size with checkpoint resume
  - Timeout protection: 45-minute limit with automatic recovery
  - Strategic context extraction with 6-field minimal payload
  - JSON sidecar storage (no database changes)
  - Cost: ~$0.021 per EF (~150 tokens @ $0.14/1K)
- **Coverage:** 100% strategic titles processed (no orphans left behind)
- **Reliability:** All phases resumable, idempotent, and timeout-protected

### Current System Status (Production-Ready Timeout Mitigation)
- **Architecture:** Incident-first hybrid processing with timeout mitigation successfully implemented
- **Coverage:** 100% strategic title processing (incidents + single-title EF seeds)
- **Anti-fragmentation:** Zero related event splitting via semantic clustering
- **Cross-batch merging:** Automatic sibling reunification via ef_key matching
- **Timeout Mitigation:** All phases resumable with checkpoint recovery
- **Production Ready:** Stable processing with comprehensive timeout protection and automatic recovery
- **Operational Mode:** P1/P2/P4 on 12-hour cron cycles, P3 as continuous systemd background service

## Database Schema

### Core Tables
- **`titles`**: Individual news articles with strategic metadata
- **`feeds`**: RSS source configuration (137 active feeds)
- **`event_families`**: Consolidated strategic events (incidents + single-title seeds)
- **`framed_narratives`**: Multi-perspective event analysis

### Key Fields
- `titles.gate_keep`: Strategic relevance flag
- `titles.entities`: JSON actor extraction results
- `titles.event_family_id`: Direct EF assignment (100% for strategic titles)
- `event_families.source_title_ids`: UUID array of constituent titles
- `event_families.ef_key`: Theater + event_type hash for cross-batch merging
- `framed_narratives.supporting_title_ids`: Evidence title references

## System Architecture Decisions

### Incident-First vs Event-First Processing
**Decision:** Incident-first semantic clustering before classification
**Rationale:** Event-first caused EF fragmentation - related events split across multiple EFs
**Result:** Zero fragmentation, 100% strategic coverage, cross-batch sibling reunification

### Hybrid Processing vs Pure Clustering
**Decision:** Hybrid approach with single-title EF seeds for orphans
**Rationale:** Not every strategic title belongs to multi-title incidents
**Result:** 100% strategic coverage while preserving incident quality

### ef_key Cross-Batch Merging vs Session-Only Processing
**Decision:** ef_key (theater + event_type hash) for cross-batch merging
**Rationale:** Lost siblings need reunification across processing sessions
**Result:** Poland drone incidents merged despite being in different batches

### Semantic LLM Clustering vs Rule-Based Grouping
**Decision:** LLM semantic incident clustering in MAP phase
**Rationale:** Rule-based grouping missed narrative coherence and causal relationships
**Result:** High-quality incident identification with strategic coherence

## File Organization

### Active Components
- `run_pipeline.py` - **Unified pipeline orchestrator with incident-first integration**
- `apps/ingest/run_ingestion.py` - RSS ingestion
- `apps/filter/run_enhanced_gate.py` - Strategic gating + entities
- `apps/generate/incident_processor.py` - **Incident-first EF generation (primary system)**
- `apps/generate/map_classifier.py` - Semantic incident clustering (MAP phase)
- `apps/generate/reduce_assembler.py` - Incident analysis + EF generation (REDUCE phase)
- `apps/generate/mapreduce_models.py` - Incident clustering data models
- `apps/generate/mapreduce_prompts.py` - Incident clustering + analysis prompts
- `apps/generate/llm_client.py` - LLM client with retry logic
- `apps/generate/database.py` - Database operations with ef_key merging
- `apps/generate/models.py` - Core EventFamily model
- `apps/generate/ef_key.py` - EF key generation for cross-batch merging
- `apps/enrich/` - **EF strategic context enrichment system**
  - `apps/enrich/cli.py` - Enrichment command-line interface
  - `apps/enrich/processor.py` - Core enrichment processing with queue management
  - `apps/enrich/models.py` - 6-field enrichment payload data models
  - `apps/enrich/prompts.py` - Micro-prompt templates for bounded LLM calls
- `data/*.csv` - Strategic vocabularies (actors, people, taxonomy)
- `data/enrichments/` - JSON sidecar enrichment storage

### Legacy Components (REMOVED)
- ~~`apps/generate/mapreduce_processor.py`~~ - **REMOVED: Legacy event-first processor**
- Legacy compatibility functions in `mapreduce_prompts.py` - **REMOVED**

### Configuration
- `core/config.py` - Centralized system configuration
- `HYBRID_INCIDENT_ARCHITECTURE.md` - Detailed architecture documentation
- `.claude/settings.local.json` - Claude Code integration
- `CLAUDE.md` - Project instructions
- `README.md` - Project overview

#### Key Configuration Settings (With Timeout Mitigation)
```python
# Incident-First Configuration (core/config.py)
map_concurrency: int = 8                    # Parallel incident clustering
reduce_concurrency: int = 12                # Parallel incident analysis
map_batch_size: int = 100                   # Titles per clustering call
llm_max_tokens_generic: int = 8000          # Near DeepSeek 8K limit
llm_timeout_seconds: int = 180              # Individual LLM call timeout

# EF Enrichment Configuration
enrichment_enabled: bool = True             # Enable/disable enrichment processing
daily_enrichment_cap: int = 100             # Daily enrichment limit
enrichment_max_tokens: int = 200            # Bounded token limit for micro-prompts
enrichment_temperature: float = 0.0         # Deterministic LLM responses

# Timeout Mitigation Configuration
# P1 Ingest Batch Settings
p1_default_batch_size: int = 500            # Default feed batch size
p1_checkpoint_file: str = "logs/checkpoints/p1_ingest.json"

# P2 Filter Batch Settings
p2_default_batch_size: int = 1000           # Default title batch size
p2_checkpoint_file: str = "logs/checkpoints/p2_filter.json"

# P3 Generate Background Worker Settings
p3_background_max_titles: int = 1000        # Max titles per background cycle
p3_restart_on_error: bool = True            # Systemd auto-restart

# P4 Enrich Batch Settings
p4_default_batch_size: int = 50             # Default EF batch size
p4_checkpoint_file: str = "logs/checkpoints/p4_enrich.json"

# Production Cron Timeouts
p1_timeout_minutes: int = 30                # RSS ingestion timeout
p2_timeout_minutes: int = 15                # Strategic filtering timeout
p4_timeout_minutes: int = 45                # EF enrichment timeout
```

**Performance Characteristics:**
- Incident-first processing: 50 titles → 20 EFs in ~3-4 minutes
- 100% strategic title coverage (no orphans)
- Cross-batch incident merging via ef_key matching
- Semantic clustering prevents EF fragmentation
- EF enrichment: 8.4s per EF, 93.1% success rate, 426 EFs/hour capacity

## Quality Assurance

### Strategic Content Focus
- **Included:** Diplomacy, military operations, economic policy, domestic politics, tech regulation
- **Excluded:** Sports, entertainment, weather, local crime, celebrity news
- **Filtering:** Automated via CSV stop list AND LLM prompt for non-strategic content that leaked through

### Incident-First Prompt Engineering
- **Incident Clustering:** Semantic incident identification with temporal and causal analysis
- **Incident Analysis:** Theater + event_type classification with chronological event extraction
- **Cross-Merging:** ef_key matching for automatic sibling reunification
- **Coverage Guarantee:** Single-title EF seeds for orphaned strategic content

### Data Quality Metrics
- **100% Coverage:** All strategic titles assigned to EFs (incidents + singles)
- **Zero Fragmentation:** Related events stay together via semantic clustering
- **Cross-batch Merging:** Lost siblings automatically reunited via ef_key
- **UUID Integrity:** All title references use actual UUIDs (not array indices)
- **Confidence Tracking:** LLM confidence scores for all generated content

## Troubleshooting

### Common Issues
1. **Import Path Errors:** Always use `python -m apps.module.script` format
2. **Context Length Limits:** Batch sizes optimized for LLM token limits (~131k)
3. **Database Connectivity:** Check PostgreSQL connection in `core/config.py`
4. **Unicode Encoding:** Windows console encoding issues with international feeds

### Health Checks
```bash
# Check recent ingestion
python -c "from apps.generate.database import get_gen1_database; import asyncio; print(asyncio.run(get_gen1_database().get_processing_stats()))"

# Check strategic title coverage
python -c "from core.database import get_db_session; from sqlalchemy import text; with get_db_session() as s: print(f'Strategic: {s.execute(text(\"SELECT COUNT(*) FROM titles WHERE gate_keep = true\")).scalar()}'); print(f'Assigned: {s.execute(text(\"SELECT COUNT(*) FROM titles WHERE event_family_id IS NOT NULL\")).scalar()}')"

# Check Event Family generation status
python -c "from apps.generate.database import get_gen1_database; import asyncio; db = get_gen1_database(); efs = asyncio.run(db.get_event_families(limit=5)); print(f'{len(efs)} recent Event Families')"
```

## Development Workflow

### Testing Incident-First Processing
```bash
# Test incident-first with small batch
python -m apps.generate.incident_processor 50

# Test with background processing
python -m apps.generate.incident_processor 200 --background

# Check processing results and coverage
python investigate_unclustered_simple.py

# Check specific EF counts and merging
python debug_ef_key_merging.py
```

### Code Quality Standards
- **No Unicode/Emoji:** Code files contain only ASCII characters
- **UUID References:** Always use actual title IDs, never array indices
- **Error Handling:** Comprehensive exception handling with meaningful messages
- **Documentation:** Inline docstrings for all major functions
- **Database connection** Always use PostgreSQL connection in `core/config.py`

---

*This pipeline documentation reflects the current Incident-First Hybrid Architecture with production-ready timeout mitigation, 100% strategic coverage, and zero fragmentation, successfully implemented and tested on September 23, 2025.*
# SNI-v2 Pipeline Flow & Architecture

*Updated: September 15, 2025 - Multi-Pass GEN-1 Architecture*

## Architecture Overview

The SNI (Strategic Narrative Intelligence) system operates a **sequential processing pipeline** that transforms raw RSS feeds into strategic Event Families and Framed Narratives. The system emphasizes **anti-fragmentation** through intelligent content consolidation.

### Core Data Flow
```
RSS Sources → Ingestion → Strategic Gating → Entity Extraction → Multi-Pass Event Family Generation
```

## Pipeline Components

### 1. RSS Ingestion
**Entry Point:** `python -m apps.ingest.run_ingestion`  
**Purpose:** Collect news articles from 137+ configured RSS feeds  
**Input:** RSS feed URLs from `feeds` table  
**Output:** New records in `titles` table with `processing_status='pending'`

**Features:**
- Google News RSS aggregation across strategic sources
- Content deduplication via hashing
- Multi-language support (English, Arabic, French, etc.)
- Automatic publisher domain extraction

**Performance:** ~2,000-5,000 titles ingested per run (varies by news cycle)

### 2. Enhanced Strategic Gate + Entity Processing
**Entry Point:** `python -m apps.clust1.run_enhanced_gate`  
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
- JSON storage in `titles.entities` field
- Version tracking for extraction evolution
- Actor canonicalization (e.g., "Putin" → "RU")

**Execution:**
```bash
python -m apps.clust1.run_enhanced_gate --hours 24 --max-titles 1000
```

### 3. Multi-Pass Event Family Generation (GEN-1)
**Entry Point:** `python -m apps.gen1.multipass_processor`  
**Purpose:** Intelligent Event Family assembly with anti-fragmentation focus  
**Input:** Strategic titles where `event_family_id IS NULL`  
**Output:** Creates `event_families` and `framed_narratives` records

#### Pass 1: Sequential EF Assembly
- **Strategy:** Process titles in large sequential batches (1,000 per batch)
- **Focus:** Basic Event Family creation with essential metadata
- **LLM Processing:** Content-driven EF generation (not artificially limited)
- **Performance:** 40x faster than entity-based batching
- **Anti-fragmentation:** Prefers coherent, comprehensive Event Families

**Execution:**
```bash
python -m apps.gen1.multipass_processor pass1 [max_titles]
```

#### Pass 2: Cross-Merging & Narrative Generation
- **Strategy:** Analyze existing Event Families for merge opportunities
- **Focus:** Fight information fragmentation through intelligent consolidation
- **LLM Analysis:** Cross-EF comparison for strategic coherence
- **Narrative Generation:** Multi-perspective Framed Narrative analysis
- **Quality:** Evidence-based framing with textual citations

**Execution:**
```bash
python -m apps.gen1.multipass_processor pass2 [max_event_families]
```

### 4. Anti-Fragmentation Philosophy

**Core Principle:** Fight political information fragmentation by:
- Creating fewer, more comprehensive Event Families
- Intelligent merging of related strategic events
- Actor canonicalization across languages and sources
- Time-flexible coherence (events can span weeks/months)

**Quality Metrics:**
- High LLM confidence scores (typically 0.85-0.95)
- Evidence-based Framed Narratives with exact quote citations
- Strategic focus (excludes sports, entertainment, local news)

## Complete Pipeline Execution

### Sequential Processing Order
```bash
# 1. Ingest latest news (137 feeds)
python -m apps.ingest.run_ingestion

# 2. Enhanced gating + entity extraction (combined)
python -m apps.clust1.run_enhanced_gate --hours 2

# 3. Multi-pass Event Family generation
python -m apps.gen1.multipass_processor pass1   # Basic EF assembly
python -m apps.gen1.multipass_processor pass2   # Cross-merging + narratives
```

### Performance Benchmarks
- **RSS Ingestion:** ~3-5 minutes for 137 feeds
- **Enhanced Gating:** ~30-60 seconds for 1,000 titles
- **Pass 1 (Sequential):** ~15-20 minutes for 7,500 titles (8 batches)
- **Pass 2 (Cross-merge):** ~5-10 minutes for 45 Event Families

### Current System Status
- **Event Families Generated:** 45 (from 7,491 strategic titles)
- **Average Confidence:** 0.91 (very high quality)
- **Framed Narratives:** 0 (Pass 2 implementation ready)
- **Anti-fragmentation Success:** Comprehensive EFs covering major strategic events

## Database Schema

### Core Tables
- **`titles`**: Individual news articles with strategic metadata
- **`feeds`**: RSS source configuration (137 active feeds)
- **`event_families`**: Consolidated strategic events
- **`framed_narratives`**: Multi-perspective event analysis

### Key Fields
- `titles.gate_keep`: Strategic relevance flag
- `titles.entities`: JSON actor extraction results
- `titles.event_family_id`: Direct EF assignment
- `event_families.source_title_ids`: UUID array of constituent titles
- `framed_narratives.supporting_title_ids`: Evidence title references

## System Architecture Decisions

### Sequential vs Entity-Based Batching
**Decision:** Sequential batching (40x performance improvement)  
**Rationale:** Entity-based batching created too many small, inefficient batches  
**Result:** 7,491 titles processed in 8 large batches instead of 54+ small ones

### Multi-Pass vs Single-Pass Processing
**Decision:** Two-pass architecture (Pass 1: Assembly, Pass 2: Cross-merging)  
**Rationale:** Anti-fragmentation requires cross-batch analysis for merging  
**Result:** Higher quality, fewer fragmented Event Families

### Direct Title Processing vs Bucket Clustering
**Decision:** Direct title processing (bucketless architecture)  
**Rationale:** Bucket clustering was inefficient and didn't improve quality  
**Result:** Simplified pipeline with better performance and maintainability

## File Organization

### Active Components
- `apps/ingest/run_ingestion.py` - RSS ingestion
- `apps/clust1/run_enhanced_gate.py` - Strategic gating + entities
- `apps/gen1/multipass_processor.py` - Multi-pass EF generation
- `apps/gen1/llm_client.py` - LLM prompt management
- `apps/gen1/database.py` - Database operations
- `data/*.csv` - Strategic vocabularies (actors, people, taxonomy)

### Archived/Legacy Components (prefixed with ~)
- `~*.py` - Deprecated bucket-based architecture
- `tests/root/test_*.py` - Moved test files
- `~phase2_design.md` - Legacy design documents

### Configuration
- `.claude/settings.local.json` - Claude Code integration
- `CLAUDE.md` - Project instructions
- `README.md` - Project overview

## Quality Assurance

### Strategic Content Focus
- **Included:** Diplomacy, military operations, economic policy, domestic politics, tech regulation
- **Excluded:** Sports, entertainment, weather, local crime, celebrity news
- **Filtering:** Automated via CSV vocabularies + manual stop lists

### LLM Prompt Engineering
- **Event Family Assembly:** Strategic semantic grouping with actor canonicalization  
- **Cross-Merging:** Anti-fragmentation analysis with high confidence thresholds
- **Framed Narratives:** Evidence-based framing analysis with exact quote requirements

### Data Quality Metrics
- **UUID Integrity:** All title references use actual UUIDs (not array indices)
- **Confidence Tracking:** LLM confidence scores for all generated content
- **Evidence Requirements:** All narratives must cite specific headline evidence

## Troubleshooting

### Common Issues
1. **Import Path Errors:** Always use `python -m apps.module.script` format
2. **Context Length Limits:** Batch sizes optimized for LLM token limits (~131k)
3. **Database Connectivity:** Check PostgreSQL connection in `core/config.py`
4. **Unicode Encoding:** Windows console encoding issues with international feeds

### Health Checks
```bash
# Check recent ingestion
python -c "from apps.gen1.database import get_gen1_database; import asyncio; print(asyncio.run(get_gen1_database().get_processing_stats()))"

# Check strategic title counts
python -c "from core.database import get_db_session; from sqlalchemy import text; with get_db_session() as s: print(f'Strategic: {s.execute(text(\"SELECT COUNT(*) FROM titles WHERE gate_keep = true\")).scalar()}')"

# Check Event Family generation status
python -c "from apps.gen1.database import get_gen1_database; import asyncio; db = get_gen1_database(); efs = asyncio.run(db.get_event_families(limit=5)); print(f'{len(efs)} recent Event Families')"
```

## Development Workflow

### Testing Multi-Pass Processing
```bash
# Test small batch Pass 1
python -m apps.gen1.multipass_processor pass1 100 --dry-run

# Test Pass 2 with limited EFs  
python -m apps.gen1.multipass_processor pass2 5 --dry-run

# Check processing results
python -c "from apps.gen1.database import get_gen1_database; import asyncio; print(asyncio.run(get_gen1_database().get_processing_stats()))"
```

### Code Quality Standards
- **No Unicode/Emoji:** Code files contain only ASCII characters
- **UUID References:** Always use actual title IDs, never array indices
- **Error Handling:** Comprehensive exception handling with meaningful messages
- **Documentation:** Inline docstrings for all major functions

---

*This pipeline documentation reflects the current multi-pass, anti-fragmentation architecture successfully implemented and tested on September 15, 2025.*
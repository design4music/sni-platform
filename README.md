# SNI-v2: Strategic Narrative Intelligence with Incident-First Architecture

A production-ready system that transforms multilingual news headlines into comprehensive Event Families using semantic incident clustering and hybrid processing.

## 🎯 Core Concept

- **Input**: Strategic news headlines from 137+ RSS feeds
- **Processing**: Incident-first semantic clustering → Classification → EF generation
- **Output**: Comprehensive Event Families with 100% strategic coverage
- **Philosophy**: Prevent EF fragmentation through semantic incident clustering before classification
- **Coverage**: Zero strategic titles left unprocessed (incidents + single-title EF seeds)

## 🚀 Architecture Overview

### Hybrid Incident-First Pipeline
```
RSS Ingestion → Strategic Gating → Incident Clustering → EF Generation → Cross-Batch Merging
```

**Key Innovation**: Semantic incident clustering **before** classification prevents EF fragmentation and ensures related events stay together.

### Core Benefits
- ✅ **Zero EF Fragmentation**: Related events cluster together (Poland drone incident → 1 EF, not 3)
- ✅ **100% Strategic Coverage**: Every strategic title becomes part of an EF (incidents + singles)
- ✅ **Cross-Batch Merging**: Lost siblings reunite via ef_key matching across processing sessions
- ✅ **Early Signal Preservation**: Single-title EF seeds capture emerging strategic trends

## 🛠️ Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- DeepSeek API access (configured in `core/config.py`)

### Production Pipeline Execution
```bash
# Complete pipeline (recommended)
python run_pipeline.py run

# Individual phases
python run_pipeline.py phase1 --max-feeds 137    # RSS ingestion
python run_pipeline.py phase2 --hours 24         # Strategic filtering
python run_pipeline.py phase3 --max-titles 500   # Incident-first EF generation

# Check pipeline status
python run_pipeline.py status
```

### Manual Processing
```bash
# 1. Ingest latest news
python -m apps.ingest.run_ingestion

# 2. Strategic gating + entity extraction
python -m apps.filter.run_enhanced_gate --hours 24

# 3. Incident-first Event Family generation
python -m apps.generate.incident_processor 500
```

## 📋 Current Architecture

### Active Processing Components
```
apps/
├── ingest/
│   └── run_ingestion.py           # RSS ingestion from 137 feeds
├── filter/
│   └── run_enhanced_gate.py       # Strategic filtering + entity extraction
└── generate/
    ├── incident_processor.py      # PRIMARY: Incident-first EF generation
    ├── map_classifier.py          # Semantic incident clustering (MAP)
    ├── reduce_assembler.py        # Incident analysis + EF generation (REDUCE)
    ├── mapreduce_models.py        # Incident clustering data models
    ├── mapreduce_prompts.py       # LLM prompts for clustering + analysis
    ├── database.py               # Database operations with ef_key merging
    ├── models.py                 # Core EventFamily model
    └── ef_key.py                 # Cross-batch merging via theater + event_type
```

### Core Configuration
```python
# core/config.py - Production settings
map_concurrency: int = 8                    # Parallel incident clustering
reduce_concurrency: int = 12                # Parallel incident analysis
map_batch_size: int = 100                   # Titles per clustering call
llm_max_tokens_generic: int = 8000          # Near DeepSeek 8K limit
llm_timeout_seconds: int = 180              # Individual LLM call timeout
```

## 🔄 Processing Pipeline Details

### 1. RSS Ingestion
- **Sources**: 137 strategic RSS feeds (Google News aggregation)
- **Deduplication**: Content hashing prevents duplicates
- **Multilingual**: English, Arabic, French, German, Russian, Chinese
- **Performance**: ~2,000-5,000 titles per run

### 2. Strategic Gating + Entity Extraction
- **Actor Matching**: `actors.csv` (countries, organizations, leaders)
- **People Matching**: `go_people.csv` (strategic individuals)
- **Content Filtering**: `stop_culture.csv` (excludes sports, entertainment)
- **Hit Rate**: ~10-30% strategic content
- **Real-time Entities**: JSON storage in `titles.entities`

### 3. Incident-First Event Family Generation

#### MAP Phase: Semantic Incident Clustering
- **LLM Analysis**: DeepSeek identifies strategic incidents across title batches
- **Clustering Criteria**:
  - Temporal proximity (48-hour windows)
  - Causal relationships (action → reaction → consequence)
  - Strategic coherence (unified narrative threads)
- **Examples**: "Charlie Kirk Assassination and Aftermath", "Poland-Russia Border Incident"

#### REDUCE Phase: Incident Analysis + EF Generation
- **Incident Analysis**: LLM analyzes clusters → (theater, event_type) + EF content
- **Timeline Generation**: Chronological event sequences within incidents
- **ef_key Creation**: theater + event_type hash for cross-batch merging
- **Handles Both**: Multi-title incidents + single-title clusters

#### Hybrid Orphan Processing
- **Orphan Detection**: Identifies strategic titles not belonging to incidents
- **Single-Title EF Seeds**: Creates EF seeds for isolated strategic content
- **Early Signals**: Preserves emerging trends for future epic events
- **Same Logic**: Uses identical REDUCE pipeline for consistency

#### Cross-Batch Merging
- **ef_key Matching**: Automatic merging of incidents with same theater + event_type
- **Lost Sibling Reunification**: Related events from different batches automatically merge
- **Database Integration**: Real-time merging during processing

## 🗄️ Database Schema

### Core Tables
- **`titles`**: Individual news articles with strategic metadata
- **`feeds`**: RSS source configuration (137 active feeds)
- **`event_families`**: Consolidated strategic events (incidents + single-title seeds)
- **`framed_narratives`**: Multi-perspective event analysis (future phase)

### Key Fields
- `titles.gate_keep`: Strategic relevance flag
- `titles.entities`: JSON actor extraction results
- `titles.event_family_id`: Direct EF assignment (100% for strategic titles)
- `event_families.source_title_ids`: UUID array of constituent titles
- `event_families.ef_key`: Theater + event_type hash for cross-batch merging
- `event_families.events`: JSONB chronological timeline within incidents

## 📊 Performance Metrics

### Production Benchmarks
- **RSS Ingestion**: ~3-5 minutes for 137 feeds
- **Strategic Gating**: ~30-60 seconds for 1,000 titles
- **Incident Processing**: ~3-4 minutes for 50 titles → 20 EFs
  - MAP Phase: ~1.5 minutes (incident clustering)
  - REDUCE Phase: ~1.5 minutes (analysis + orphan processing)
  - Cross-batch merging: Real-time via ef_key

### Quality Metrics
- **Coverage**: 100% strategic titles processed (no orphans)
- **Fragmentation**: Zero related event splitting
- **Merging Success**: Automatic sibling reunification across batches
- **Confidence**: High LLM confidence scores (0.85-0.95)

### Example Results (50-title test)
- **16 incident clusters** → 16 multi-title/single-title EFs
- **4 orphaned titles** → 4 single-title EF seeds
- **Total**: 20 EFs with 100% strategic coverage
- **Cross-batch merging**: Poland/Ukraine incidents merged via ef_key

## 🔧 Configuration & Setup

### Environment Configuration
```bash
# Database (core/config.py)
DATABASE_URL=postgresql://user:pass@localhost:5432/sni_v2

# LLM Configuration
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your_api_key

# Processing Limits
map_concurrency=8          # Parallel incident clustering
reduce_concurrency=12      # Parallel incident analysis
map_batch_size=100         # Titles per clustering batch
```

### Strategic Vocabularies
- `data/actors.csv`: Strategic actors (countries, organizations)
- `data/go_people.csv`: Strategic individuals
- `data/stop_culture.csv`: Non-strategic content filters

## 🧪 Testing & Validation

### Test Incident Processing
```bash
# Small batch test
python -m apps.generate.incident_processor 50

# Background processing
python -m apps.generate.incident_processor 200 --background

# Check coverage and results
python investigate_unclustered_simple.py

# Debug ef_key merging
python debug_ef_key_merging.py
```

### Health Checks
```bash
# Strategic title coverage
python -c "from core.database import get_db_session; from sqlalchemy import text; with get_db_session() as s: print(f'Strategic: {s.execute(text(\"SELECT COUNT(*) FROM titles WHERE gate_keep = true\")).scalar()}'); print(f'Assigned: {s.execute(text(\"SELECT COUNT(*) FROM titles WHERE event_family_id IS NOT NULL\")).scalar()}')"

# Recent EF generation
python -c "from apps.generate.database import get_gen1_database; import asyncio; db = get_gen1_database(); efs = asyncio.run(db.get_event_families(limit=5)); print(f'{len(efs)} recent Event Families')"
```

## 🛡️ Quality Assurance

### Strategic Content Focus
- **Included**: Diplomacy, military operations, economic policy, domestic politics, tech regulation
- **Excluded**: Sports, entertainment, weather, local crime, celebrity news
- **Filtering**: Automated via CSV stop lists + LLM strategic validation

### Anti-Fragmentation Measures
- **Incident-First**: Semantic clustering before classification prevents splitting
- **Cross-Batch Merging**: ef_key matching reunites lost siblings
- **Comprehensive Coverage**: Single-title EF seeds preserve early signals
- **Time-Flexible**: Events can span hours to weeks within incidents

## 📚 Documentation

- **`PIPELINE_FLOW.md`**: Complete pipeline documentation with performance benchmarks
- **`HYBRID_INCIDENT_ARCHITECTURE.md`**: Detailed technical architecture
- **Database Schema**: See `db/migrations/` for current schema
- **API Documentation**: Future FastAPI integration planned

## 🔮 Future Phases

### Next: Intelligent EF Enrichment
- **LLM Mini-Research**: Background research on key actors
- **Historical Context**: Precedent analysis for strategic implications
- **Regional Impact**: Geographic and political consequence assessment
- **Strategic Intelligence**: Transform EF seeds into comprehensive intel products

### Planned Features
- **Framed Narratives**: Multi-perspective analysis of each EF
- **Strategic Arcs**: Cross-EF pattern detection
- **Real-time API**: FastAPI endpoints for live access
- **Dashboard Interface**: Web UI for analyst access

## 🛠️ Troubleshooting

### Common Issues
1. **Import Paths**: Always use `python -m apps.module.script` format
2. **Database Connection**: Check PostgreSQL settings in `core/config.py`
3. **LLM Timeouts**: Adjust `llm_timeout_seconds` for slower API responses
4. **Unicode Issues**: Windows console encoding with international feeds

### Performance Tuning
- **Concurrency**: Adjust `map_concurrency` and `reduce_concurrency` for your hardware
- **Batch Size**: Modify `map_batch_size` based on LLM context limits
- **Timeout**: Increase `llm_timeout_seconds` for complex incident clustering

---

**Current Status**: Production-ready Incident-First Hybrid Architecture with 100% strategic coverage and zero fragmentation, successfully implemented September 19, 2025.
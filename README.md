# SNI-v2: Strategic Narrative Intelligence with Incident-First Architecture

A production-ready system that transforms multilingual news headlines into comprehensive Event Families using semantic incident clustering and hybrid processing.

---

## ⚠️ **DEVELOPMENT PRINCIPLE: MINIMAL, FOCUSED IMPLEMENTATION**

**THIS IS A HARD RULE - NOT A SUGGESTION**

### Code Philosophy
- **Write ONLY what is needed NOW** - Not what might be needed later
- **No "just in case" features** - No premature abstractions
- **No overengineering** - Resist the urge to add complexity because you can
- **50 lines > 200 lines** - Shorter, focused code is always better
- **If unsure, go simpler** - When in doubt, choose the minimal approach

### Examples of What NOT to Do
- ❌ Adding wrapper methods that just call existing methods
- ❌ Implementing features for future steps before they're needed
- ❌ Creating elaborate class hierarchies when a simple function works
- ❌ Writing extensive docstrings when the code is self-explanatory
- ❌ Adding singleton patterns, factory patterns, etc. unless absolutely necessary

### What TO Do Instead
- ✅ Implement exactly what the current step requires
- ✅ Use the simplest approach that works
- ✅ Add features incrementally when actually needed
- ✅ Keep functions and classes focused on one job
- ✅ Ask "Can this be simpler?" before writing

**Remember**: This project values working code over perfect code. Ship minimal, iterate if needed.

---

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

# Phase Timeouts (in minutes) - prevents pipeline blocking
phase_1_timeout_minutes: int = 10           # RSS ingestion: 137 feeds
phase_2_timeout_minutes: int = 5            # Strategic filtering: 1000 titles
phase_3_timeout_minutes: int = 15           # EF generation: 500 titles
phase_4_timeout_minutes: int = 30           # Enrichment: 100 EFs with LLM
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

# Pipeline Timeouts (prevents blocking on long operations)
PHASE_1_TIMEOUT_MINUTES=10    # RSS ingestion timeout
PHASE_2_TIMEOUT_MINUTES=5     # Strategic filtering timeout
PHASE_3_TIMEOUT_MINUTES=15    # EF generation timeout
PHASE_4_TIMEOUT_MINUTES=30    # Enrichment timeout
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

## 🔧 Development Guidelines

### Session Start Checklist
**ALWAYS run these commands at the start of any development session:**
```bash
# 1. Check current git state (prevents conflicts)
git status
git log --oneline -5

# 2. Verify database connection
python -c "from core.database import get_db_session; print('✅ Database connected')"

# 3. Check background processes
ps aux | grep python  # Linux/Mac
tasklist | findstr python  # Windows
```

### Git Workflow Lessons Learned

#### ⚠️ Critical: Always Check Git State First
**Problem**: When conversations get summarized and continued, it's easy to lose track of actual git state vs. conceptual progress.

**Solution**: Before any git operation, check the actual state:
```bash
git status                    # Check for uncommitted changes
git log --oneline -5          # See recent commits
git fetch origin             # Check remote state
git log --oneline origin/main -3  # See remote commits
```

#### Git Conflict Resolution Strategy
1. **Identify the conflict source**: `git log --oneline origin/main -5` vs `git log --oneline HEAD -5`
2. **For solo development**: Use `git push --force-with-lease` when you're the only developer
3. **Never use**: `git checkout --ours .` blindly - always examine conflicts first
4. **When rebasing fails**: `git rebase --abort` and assess the situation

#### Commit Message Standards
```
FEATURE: Brief description (50 chars max)

- Detailed change 1
- Detailed change 2
- Performance impact if any

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Code Organization Principles

#### Module Import Standards
- Always use: `python -m apps.module.script` format
- Never use: relative imports in scripts
- Path handling: Add project root to sys.path in standalone scripts

#### Development Safety Rules
1. **Database migrations**: Always backup before schema changes
2. **Background processes**: Check running processes before starting new ones
3. **Configuration changes**: Test in development environment first
4. **Large refactors**: Create feature branches for complex changes
5. **Architectural changes**: ALWAYS discuss approach with alternatives, pros/cons before implementation

### Performance Monitoring

#### Key Metrics to Track
```bash
# Processing speed
python -c "from apps.generate.database import get_gen1_database; import asyncio; print('EF processing rate:', 'X EFs/hour')"

# Coverage verification
python -c "from core.database import get_db_session; from sqlalchemy import text; with get_db_session() as s: strategic = s.execute(text('SELECT COUNT(*) FROM titles WHERE gate_keep = true')).scalar(); assigned = s.execute(text('SELECT COUNT(*) FROM titles WHERE event_family_id IS NOT NULL')).scalar(); print(f'Coverage: {assigned}/{strategic} ({assigned/strategic*100:.1f}%)')"

# Database health
python -c "from core.database import get_db_session; from sqlalchemy import text; with get_db_session() as s: print(f'Active EFs: {s.execute(text(\"SELECT COUNT(*) FROM event_families WHERE status = \'active\'\")).scalar()}')"
```

### Troubleshooting Quick Reference

#### Common Issues & Solutions
- **Git conflicts after context switch**: Check git state first, force-push if solo dev
- **Import errors**: Use `python -m apps.module.script` format
- **Background process conflicts**: Kill existing processes before starting new ones
- **Database connection issues**: Verify PostgreSQL service and config.py settings
- **LLM timeouts**: Increase timeout values in config.py, check API key validity

#### Emergency Recovery
```bash
# Reset to last known good state
git reflog                    # Find good commit
git reset --hard <commit>     # Reset to good state
git push --force-with-lease   # Update remote (SOLO DEV ONLY)

# Clear all background processes
pkill -f "python.*apps"      # Linux/Mac
taskkill /F /IM python.exe    # Windows (careful!)
```

---

**Current Status**: Production-ready Incident-First Hybrid Architecture with 100% strategic coverage and zero fragmentation. EF Context Enhancement system implemented September 22, 2025.
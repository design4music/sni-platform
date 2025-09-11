# SNI-v2: Headlines-Only Multilingual Narrative Intelligence

A lean, multilingual system that turns news headlines into Events, Framed Narratives, and Strategic Arcs.

## 🎯 Core Concept

- **Input**: Headlines only (no scraping)
- **Output**: Events with competing narrative framings
- **Philosophy**: Expose how meaning is manufactured, don't average viewpoints
- **Approach**: Deterministic clustering + targeted LLM generation

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- psql command-line tool

### One-Command Setup

```bash
cd SNI-v2
python scripts/run_setup.py
```

This will:
1. Install Python dependencies
2. Create the SNI database
3. Set up database tables
4. Download required NLP models
5. Verify everything works

### Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.template .env
# Edit .env with your database credentials

# 3. Create database and tables
python scripts/setup_database.py

# 4. Download spaCy models
python -m spacy download en_core_web_sm

# 5. Test setup
python scripts/test_setup.py
```

## 📋 Project Structure

```
SNI-v2/
├── apps/                   # Core processing pipeline
│   ├── ingest/            # RSS fetch & normalize
│   ├── clust1/            # Bucketing & guardrails  
│   ├── gen1/              # Prompts & LLM calls
│   ├── merge/             # Cross-feed reconciliation
│   └── arc/               # Cross-event patterns
├── core/                   # Core utilities
│   ├── config.py          # Configuration management
│   ├── database.py        # Database connections
│   └── models.py          # SQLAlchemy models  
├── api/                   # FastAPI endpoints
├── db/                    # Database management
│   ├── migrations/        # Schema migrations
│   ├── seeds/            # Sample data
│   └── schema.sql        # Database schema
├── scripts/               # Setup & utility scripts
│   ├── run_setup.py      # One-command setup
│   └── setup_database.py # Database setup
├── tests/                 # Test suite
├── docs/                  # Context & specifications
└── data/                  # Configuration files
```

## 🔧 Configuration

Key settings in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/sni_v2

# Languages (Phase 1)
PRIMARY_LANGUAGE=en
SUPPORTED_LANGUAGES=en,es,fr,de,ru,zh

# LLM (for generation phase)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# Processing
MAX_BUCKET_SIZE=100
COSINE_THRESHOLD_BUCKET=0.60
```

## 🗄️ Database Schema

Core tables following Context Document specifications:

- **feeds**: RSS feed configurations
- **titles**: Headlines with multilingual processing
- **buckets**: Pre-LLM clustering groups
- **events**: Neutral event descriptions
- **narratives**: Competing storylines for events
- **arcs**: Cross-event patterns

## 🌍 Multilingual Support

**Phase 1 Languages**:
- English (primary)
- Spanish, French, German (full support)
- Russian, Chinese (strategic coverage)

**NLP Models**:
- Embeddings: `all-MiniLM-L6-v2` (100+ languages)
- NER: spaCy models per language
- Language detection: `langdetect`

## 🔄 Processing Pipeline

Following Context Document workflow:

1. **CLUST Phase** (Deterministic)
   - Ingest & normalize headlines
   - Strategic gate filtering
   - Actor-set bucketing (24-48h windows)
   - De-duplication

2. **GEN Phase** (LLM)
   - Bucket → Event + Narratives
   - Competing framings analysis
   - Lexicon marker extraction

3. **MERGE Phase** (Cross-batch)
   - Auto-merge same events
   - Narrative continuity

4. **ARC Phase** (Optional)
   - Pattern detection
   - Cross-event linking

## 🎛️ API Endpoints

```bash
# Start API server
python api/main.py

# Endpoints (once implemented)
GET  /titles                # List strategic titles
GET  /events                # List events with narratives
GET  /arcs                  # List structural arcs
POST /ingestion/run         # Trigger ingestion
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Test specific components
pytest tests/test_ingestion.py
pytest tests/test_multilingual.py

# Test setup
python scripts/test_setup.py
```

## 📊 Monitoring

```bash
# Database stats
python -c "from core.database import get_database_stats; print(get_database_stats())"

# Check recent activity
python scripts/check_status.py
```

## 🛠️ Development

### Process Rules - Better Development Workflow

Follow these rules to prevent rushing into implementation without proper planning:

1. **Architecture First**: Always create a comprehensive architectural plan before building
   - Document the plan in `docs/tickets/` for review
   - Break complex features into phases and steps
   - Get architectural approval before implementation

2. **Check Existing Software Landscape**: Before building anything new, audit what already exists
   - Review existing apps, core modules, and utilities
   - Check for similar patterns or components that can be reused
   - Map how new work fits into the existing codebase architecture

3. **Complete Functional Blocks**: Build complete, testable functional units rather than incremental pieces
   - Finish entire features or phases before moving to the next
   - Include proper error handling and logging
   - Test end-to-end functionality

4. **Stay Strategic**: Focus on high-level architectural decisions rather than getting lost in technical details
   - Prioritize system design over implementation specifics
   - Maintain awareness of how components interact
   - Document design decisions and trade-offs

### Adding New Languages

1. Install spaCy model: `python -m spacy download {lang}_core_news_sm`
2. Add language code to `SUPPORTED_LANGUAGES` in `.env`
3. Update language configs in `data/language_configs.json`

### Adding New Feeds

```python
from ingestion.feed_manager import add_feed

add_feed(
    name="Example News",
    url="https://example.com/rss",
    language_code="en",
    country_code="US"
)
```

## 📈 Performance

**Target Scale (MVP)**:
- 10,000 headlines backfill
- 500 headlines/day processing
- 6 languages support
- <2s average bucket processing

## 🔒 Security

- No sensitive data in configs
- Parameterized SQL queries
- Input validation for all endpoints
- Structured logging without secrets

## 🤝 Contributing

1. Follow Context Document specifications
2. Maintain multilingual compatibility
3. Add tests for new features
4. Use black/isort for code formatting

## 📚 Documentation

- **Context Document**: Full system specifications
- **API Docs**: Auto-generated FastAPI docs at `/docs`
- **Database Schema**: See `scripts/schema.sql`

## 🆘 Troubleshooting

**Database Connection Failed**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U postgres -d sni_v2
```

**Missing spaCy Models**:
```bash
python -m spacy download en_core_web_sm
```

**Import Errors**:
```bash
# Ensure you're in the project root
cd SNI-v2
export PYTHONPATH=$(pwd)
```

---

Built following the SNI Headlines-Only Context Document specifications.
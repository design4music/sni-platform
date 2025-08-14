# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Strategic Narrative Intelligence (SNI) Platform

The SNI platform aggregates global news, detects strategic narratives, and processes them through advanced ML pipelines.

## Project Overview

The SNI platform is a comprehensive news intelligence system with:
- **Multi-source ingestion**: RSS feeds, APIs, web scrapers
- **Advanced NLP**: Keyword extraction, canonicalization, clustering
- **Strategic analysis**: Narrative detection and thematic grouping
- **Production-ready**: Docker containerization, monitoring, error handling

## Architecture

```
News Sources → ETL Pipeline → Keyword Processing → ML Clustering → API/Frontend
     ↓              ↓              ↓              ↓           ↓
   RSS/API      Ingestion    Canonicalization  CLUST-1    FastAPI
   Scrapers     Filtering     Normalization    Clustering  React UI
```

## Key Technologies

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL with pgvector
- **Data Processing**: Pandas, NumPy, sentence-transformers
- **ML/NLP**: spaCy, scikit-learn, YAKE, KeyBERT
- **Task Queue**: Celery with Redis
- **Deployment**: Docker, monitoring with Prometheus

## Project Structure

```
SNI/
├── etl_pipeline/           # Core ETL processing
│   ├── keywords/          # Keyword extraction & canonicalization
│   ├── clustering/        # CLUST-1 clustering system
│   └── requirements.txt   # Python dependencies
├── scripts/               # Utility scripts
├── database_migrations/   # SQL schema migrations
├── data/                 # Configuration files
│   └── keyword_synonyms.yml  # Canonicalization rules
└── tests/                # Test suites
```

## Critical Files & Components

### Keyword Processing System
- `etl_pipeline/keywords/canonicalizer.py`: Advanced keyword normalization
- `etl_pipeline/keywords/update_keyword_canon_from_db.py`: Nightly batch processing
- `data/keyword_synonyms.yml`: Canonicalization rules and synonyms

### Clustering System
- `etl_pipeline/clustering/clust1_taxonomy_graph.py`: 4-stage clustering pipeline
- Uses canonical vocabulary for improved clustering quality

### Database Schema
- `database_migrations/`: SQL migrations for schema changes
- Key tables: `articles`, `keyword_canon_map`, `article_core_keywords`
- Materialized views: `shared_keywords_300h`, `article_core_keywords`

## Development Workflow

### Common Commands
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r etl_pipeline/requirements.txt

# Database operations
psql narrative_intelligence
alembic upgrade head

# Run ETL pipeline
python scripts/regenerate_keywords.py
python etl_pipeline/keywords/update_keyword_canon_from_db.py

# Run clustering
python etl_pipeline/clustering/clust1_taxonomy_graph.py

# Testing
pytest tests/
```

### Code Standards
- **CRITICAL: NO Unicode symbols or emoji**: Windows encoding issues cause 'charmap' codec errors - use plain ASCII only
- **English-only MVP**: Current focus on English content for consistency
- **Database types**: Use `float()` wrapper for NumPy types before DB insertion
- **Error handling**: Comprehensive logging with structured output
- **SQL patterns**: Use CTEs for complex queries, avoid DISTINCT in window functions

## Key Configuration Files

### `data/keyword_synonyms.yml`
Central configuration for keyword canonicalization:
- `synonyms`: Country/entity mappings (us → united states)
- `persons`: Person name variants (trump → donald trump)  
- `concept_clusters`: Thematic groupings (negotiations, tariffs)
- `stop_words`: Terms to filter out
- `normalization`: Text processing rules

### Database Configuration
- PostgreSQL with pgvector extension required
- Connection pooling for performance
- Materialized views for efficient keyword access

## ML Pipeline: CLUST-1 System

**SOLIDIFIED PIPELINE (v1.0)**
- **Default Mode**: STRICT (quality-focused, precision over coverage)
- **Triads**: DISABLED by default (--use_triads 0)
- **Recall Mode**: DISABLED by default (use --profile recall to enable)

**Strict Mode Configuration:**
- Cosine thresholds: seed/densify=0.86, orphan=0.89
- Consolidation: cos=0.90, wj=0.55, time=0.50
- Hub tokens: Top-12 most frequent terms filtered out
- Min shared keywords: 2 for clustering

**4-stage clustering pipeline:**
1. **Seed**: Identify high-overlap keyword pairs (triads OFF)
2. **Densify**: Build dense clusters from seeds with strict thresholds
3. **Consolidate**: Merge overlapping clusters with multiple criteria
4. **Persist**: Save to database with metadata

**Performance Targets (Strict Mode):**
- Strategic filtering: 35-45% (current: ~41%)
- Clustering success: 35-55% (current: ~34%)
- Quality over quantity approach

Uses canonicalized vocabulary from `article_core_keywords` table.

## Canonicalization System

Advanced keyword normalization with:
- **Title stripping**: "President Trump" → "donald trump"
- **Acronym expansion**: "U.S." → "united states" 
- **Demonym conversion**: "russian" → "russia" (standalone only)
- **Punctuation normalization**: Consistent hyphenation/spacing

## Common Issues & Solutions

### Unicode Encoding
**Problem**: 'charmap' codec errors on Windows
**Solution**: NEVER use Unicode symbols, emoji, or special characters - use plain ASCII only. This is a project-wide rule due to repeated encoding issues.

### Database Types  
**Problem**: NumPy float64 insertion errors
**Solution**: Wrap with `float()` before database insertion

### SQL Window Functions
**Problem**: "DISTINCT is not implemented for window functions"
**Solution**: Use CTEs to calculate distinct counts separately

### Character Classes in Regex
**Problem**: "bad character range" errors
**Solution**: Order character classes correctly: `[^\w\s/-]` not `[^\w\s-/]`

## Testing Strategy

- Unit tests for individual components
- Integration tests for pipeline flows
- Database tests with transaction rollback
- Performance tests for large datasets

## Deployment Notes

- Docker containerization available
- Environment variables for configuration
- Monitoring with Prometheus metrics
- Structured logging throughout

## Working with This Codebase

### When Adding Features
1. Check existing patterns in similar modules
2. Follow the canonicalization → clustering → API flow
3. Update tests and documentation
4. Ensure English-only compatibility for MVP

### When Debugging
1. Check logs for structured error messages
2. Verify database connections and migrations
3. Test with small datasets first
4. Use materialized views for performance

### When Modifying Keywords/Clustering
1. Test with `update_keyword_canon_from_db.py` first
2. Check impact on CLUST-1 clustering quality
3. Update `keyword_synonyms.yml` if needed
4. Verify database materialized view updates

## Performance Considerations

- Use batch processing for large datasets
- Leverage database indexes and materialized views  
- Monitor memory usage with large numpy arrays
- Consider parallel processing for independent operations

## Security & Data Handling

- No sensitive data in configuration files
- Parameterized SQL queries throughout
- Input validation for all user data
- Structured logging without exposing internals

This guide should help Claude Code instances quickly understand and work effectively within the SNI platform architecture.
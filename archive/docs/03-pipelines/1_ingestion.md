# SNI Articles Ingestion - Technical Reference

**Document**: Strategic Narrative Intelligence - Articles Ingestion Technical Reference  
**Last Updated**: 2025-08-30  
**Version**: 2.0  
**Status**: Production Ready  
**Pipeline Step**: Step 1 of 12

## Overview

The Articles Ingestion system is the entry point of the SNI pipeline, responsible for collecting articles from multiple sources including RSS feeds, XML sitemaps, and API endpoints. The system implements incremental processing, deduplication, quality filtering, and progressive content enhancement.

**Supported Source Types:**
- **RSS/Atom Feeds**: Standard syndication formats (31 active feeds)
- **XML Sitemaps**: Crawl news sitemaps for article discovery (1 active feed)  
- **API Sources**: Direct integration with news providers (ready for implementation)

---

## Ingestion Scripts

### Core Ingestion Scripts

#### `rss_ingestion.py` (Root-level)
**Purpose**: Main ingestion orchestrator and entry point for RSS/sitemap processing  
**Function**: Coordinates the entire ingestion process with comprehensive error handling
```bash
# Usage
python rss_ingestion.py --incremental          # Recommended: only new articles
python rss_ingestion.py --window-hours 72     # Last 72 hours
python rss_ingestion.py --limit 100           # Max articles per feed
python rss_ingestion.py --feeds 1,5,12        # Specific feed IDs only
```

**Key Features:**
- Feed configuration loading from database
- Incremental vs full refresh modes
- Feed-specific rate limiting and timeout handling
- Comprehensive logging and error recovery
- Integration with both RSS and XML sitemap handlers

#### `etl_pipeline/ingestion/rss_handler.py`
**Purpose**: Core RSS feed processing logic with quality filtering  
**Function**: Handles RSS/Atom parsing, article extraction, and quality validation
```python
# Main classes
RSSFeedHandler      # Standard RSS feed processing
BaseFeedHandler     # Abstract base for feed handlers
```

**Processing Logic:**
- RSS/Atom feed parsing with feedparser
- Article metadata extraction (title, URL, content, published_at)
- Content quality validation (length, language, HTML cleanup)
- Source attribution cleaning and normalization
- Database persistence with deduplication

#### `etl_pipeline/ingestion/fetch_fulltext.py`
**Purpose**: Progressive full-text enhancement system  
**Function**: Upgrades RSS snippets to full article content via web scraping
```bash
# Usage  
python etl_pipeline/ingestion/fetch_fulltext.py --window 24    # Last 24h
python etl_pipeline/ingestion/fetch_fulltext.py --window 0     # All pending
```

**Enhancement Process:**
- Identifies articles needing full-text enhancement (< 300 words)
- Uses learned extraction profiles for website-specific optimization  
- Implements Trafilatura with intelligent fallbacks
- Handles rate limiting and retry logic
- Updates processing_status from PENDING to COMPLETED/FAILED

#### `unified_ingestion.py`
**Purpose**: Alternative unified ingestion interface  
**Function**: Simplified entry point for unified RSS/sitemap/API processing
```bash
# Usage
python unified_ingestion.py                   # Process all active feeds
```

**Features:**
- Single interface for all source types
- Automatic source type detection
- Simplified configuration and execution

### Supporting Scripts

#### `etl_pipeline/core/tasks/ingestion_tasks.py`  
**Purpose**: Task-based ingestion system for async processing  
**Function**: Celery-compatible task definitions for distributed ingestion

#### `etl_pipeline/ingestion/rss_ingestion.py` (ETL Module)
**Purpose**: ETL-specific RSS ingestion logic  
**Function**: Core RSS processing implementation used by main orchestrator

---

## Database Tables

### Primary Tables

#### `news_feeds`
**Purpose**: Store feed configuration and metadata  
**Schema**:
```sql
id                    UUID PRIMARY KEY
name                  VARCHAR(255)           # Human-readable feed name
url                   TEXT                   # Feed URL (RSS/sitemap/API endpoint)
feed_type             feed_type_enum         # RSS, xml_sitemap, api, scraper
language              language_code_enum     # EN, RU, DE, FR
country_code          VARCHAR(2)             # ISO country code
is_active             BOOLEAN DEFAULT true   # Feed enabled status
priority              INTEGER DEFAULT 1      # 1=high, 5=low priority
fetch_interval_minutes INTEGER DEFAULT 60    # Minutes between fetches
reliability_score     FLOAT DEFAULT 0.5      # Feed quality score (0.0-1.0)
last_fetched_at       TIMESTAMP             # Last successful fetch
created_at            TIMESTAMP DEFAULT NOW()
updated_at            TIMESTAMP DEFAULT NOW()
```

**Current Data:**
- **31 RSS feeds**: Active RSS/Atom feeds from various news sources
- **1 XML sitemap feed**: Sitemap-based article discovery
- **0 API feeds**: Ready for future API integrations

#### `articles`
**Purpose**: Store all ingested articles with metadata  
**Schema**:
```sql
id                    UUID PRIMARY KEY
feed_id               UUID REFERENCES news_feeds(id)
url                   TEXT UNIQUE            # Article URL (deduplication key)
title                 TEXT                   # Article headline
content               TEXT                   # Article content (snippet or full-text)
summary               TEXT                   # Article summary/description
author                TEXT                   # Author name
published_at          TIMESTAMP              # Original publication time
language              language_code_enum     # Detected article language
word_count            INTEGER                # Content word count
processing_status     processing_status_enum # PENDING, COMPLETED, FAILED, etc.
ingestion_source      TEXT                   # Source attribution metadata
metadata              JSONB                  # Additional structured metadata
content_hash          TEXT                   # Content deduplication hash
created_at            TIMESTAMP DEFAULT NOW()
updated_at            TIMESTAMP DEFAULT NOW()
```

**Processing Status Flow:**
1. **PENDING**: Newly ingested, awaiting full-text enhancement
2. **COMPLETED**: Full-text enhanced, ready for keyword extraction
3. **FAILED**: Enhancement failed, may retry later
4. **FILTERED_OUT**: Removed due to quality filters
5. **DUPLICATE**: Identified as duplicate content

#### `article_extraction_profiles`
**Purpose**: Store learned extraction patterns for websites  
**Schema**:
```sql
domain                TEXT PRIMARY KEY       # Website domain (e.g., 'cnn.com')
profile_name          TEXT                   # Human-readable profile name
extraction_config     JSONB                  # Trafilatura/extraction settings
success_rate          FLOAT                  # Historical success rate
last_updated          TIMESTAMP              # Profile last modified
sample_urls           TEXT[]                 # Sample URLs for testing
```

**Purpose**: Enables website-specific optimization for full-text extraction

### Supporting Tables

#### `feed_fetch_log`
**Purpose**: Track feed fetch attempts and results  
**Schema**:
```sql
id                    UUID PRIMARY KEY
feed_id               UUID REFERENCES news_feeds(id)
fetch_started_at      TIMESTAMP
fetch_completed_at    TIMESTAMP
articles_found        INTEGER                # Articles discovered in feed
articles_new          INTEGER                # New articles added
articles_duplicates   INTEGER                # Duplicate articles skipped
articles_errors       INTEGER                # Articles with processing errors
status                TEXT                   # SUCCESS, FAILED, PARTIAL
error_message         TEXT                   # Error details if failed
```

---

## General Flow & Conditions

### Incremental Processing Flow

1. **Feed Discovery**
   ```sql
   SELECT * FROM news_feeds WHERE is_active = true ORDER BY priority ASC
   ```

2. **Last Fetch Check**  
   ```sql
   SELECT last_fetched_at FROM news_feeds WHERE id = ?
   ```

3. **Article Processing**
   - Fetch RSS/sitemap content
   - Parse articles newer than `last_fetched_at`
   - Apply quality filters (length, language, content type)
   - Check for duplicates via URL and content_hash
   - Insert new articles with `processing_status = 'PENDING'`

4. **Feed Update**
   ```sql
   UPDATE news_feeds SET last_fetched_at = NOW(), updated_at = NOW() WHERE id = ?
   ```

### Quality Filtering Conditions

#### Content Quality Filters
- **Minimum Length**: Articles must have content or meaningful description
- **Language Detection**: Must match expected feed language (EN/RU/DE/FR)
- **Content Type**: Must be text-based news content, not media/gallery
- **HTML Cleanup**: Strip HTML tags, normalize whitespace, remove boilerplate

#### Deduplication Logic
- **URL-based**: Exact URL match prevents duplicates
- **Content-based**: Generate hash of cleaned content for near-duplicate detection
- **Title similarity**: Compare cleaned titles for potential duplicates

#### Source Attribution Cleaning
Dynamic cleaning of source attributions from titles and content:
```python
# Examples:
"Story zerohedge.com" → "Story"
"News - The Washington Post" → "News" 
"Reuters Sitemap Sitemap" → "Reuters"
```

### Progressive Enhancement Flow

1. **Enhancement Candidate Selection**
   ```sql
   SELECT * FROM articles 
   WHERE processing_status = 'PENDING' 
     AND (word_count < 300 OR word_count IS NULL)
     AND created_at > NOW() - INTERVAL '24 hours'
   ```

2. **Full-text Extraction**
   - Apply learned extraction profiles if available
   - Use Trafilatura with intelligent fallbacks
   - Validate extracted content quality
   - Update `content`, `word_count`, and `processing_status`

3. **Auto Mode Logic**
   - **≥300 words**: Mark as COMPLETED, ready for full keyword extraction
   - **50-299 words**: Mark as COMPLETED, suitable for short-mode extraction
   - **<50 words**: Mark as FILTERED_OUT, insufficient content

---

## Configuration & Settings

### Feed-level Configuration
- **Rate Limiting**: Configurable delays between requests (default: 1-2 seconds)
- **Timeout Settings**: Connection and read timeouts (default: 30 seconds)
- **Retry Logic**: Failed requests retry with exponential backoff
- **User-Agent Rotation**: Multiple browser user-agents to avoid blocking

### Content Processing
- **HTML Cleanup**: BeautifulSoup with aggressive boilerplate removal
- **Character Encoding**: UTF-8 normalization with fallback handling
- **Content Filtering**: Remove cookie notices, subscription prompts, ads
- **Language Detection**: langdetect library with confidence thresholds

### Database Settings
- **Connection Pooling**: 10 concurrent connections per process
- **Batch Processing**: Insert/update articles in batches of 50-100
- **Transaction Management**: Atomic operations with rollback on errors
- **Index Optimization**: URL and content_hash indexes for fast deduplication

---

## Error Handling & Recovery

### Network Errors
- **Connection Timeouts**: Retry with exponential backoff (1s, 2s, 4s)
- **HTTP Errors**: Log and skip problematic feeds temporarily
- **SSL/TLS Issues**: Fallback to HTTP where appropriate
- **Rate Limiting**: Respect 429 responses with proper delays

### Content Errors  
- **Parse Failures**: Log malformed RSS/XML, attempt graceful degradation
- **Encoding Issues**: Multiple encoding detection attempts
- **Invalid URLs**: Validate and sanitize before processing
- **Empty Content**: Mark as FILTERED_OUT, don't retry

### Database Errors
- **Constraint Violations**: Handle duplicate URLs gracefully  
- **Connection Loss**: Implement connection pooling with auto-recovery
- **Transaction Deadlocks**: Retry with jittered delays
- **Disk Space**: Monitor and alert on storage issues

---

## Monitoring & Metrics

### Key Performance Indicators
- **Articles/Hour**: Ingestion rate across all sources
- **Success Rate**: % of feeds successfully processed  
- **Enhancement Rate**: % of articles successfully enhanced to full-text
- **Duplicate Rate**: % of articles identified as duplicates
- **Error Rate**: % of articles failing quality filters or processing

### Operational Monitoring
- **Feed Health**: Track feeds failing consecutively
- **Content Quality**: Monitor word count distributions
- **Processing Delays**: Identify bottlenecks in enhancement pipeline
- **Database Performance**: Query execution times and connection usage

---

## Future Enhancements

### Planned Improvements
1. **API Source Integration**: Direct API integration for major news providers
2. **Real-time Processing**: WebSocket/SSE for immediate article processing
3. **Advanced Deduplication**: Semantic similarity-based duplicate detection
4. **Content Classification**: Automatic topic/category assignment during ingestion
5. **Quality Scoring**: ML-based content quality assessment
6. **Source Reliability**: Dynamic feed reliability scoring based on performance

### Technical Debt
1. **Code Consolidation**: Merge duplicate ingestion logic across modules
2. **Configuration Management**: Centralized feed configuration system
3. **Testing Coverage**: Comprehensive integration tests for all source types
4. **Documentation**: API documentation for ingestion endpoints
5. **Performance Optimization**: Async/await throughout ingestion pipeline

---

*This technical reference provides comprehensive implementation details for the SNI Articles Ingestion system. For operational procedures and troubleshooting, refer to the ops documentation.*
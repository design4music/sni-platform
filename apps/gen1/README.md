# GEN-1: Event Family Assembly System

GEN-1 is the Event Family assembly and Framed Narrative generation system for the Strategic Narrative Intelligence (SNI) platform. It transforms CLUST-2 buckets (actor-grouped headlines) into coherent Event Families and identifies how different outlets frame these events.

## Core Concepts

### Event Family (EF)
A coherent real-world news happening/episode from multiple titles sharing the same concrete event:
- **Actors**: Specific people, organizations, countries involved  
- **Time**: Clear temporal boundaries (may span days/weeks)
- **Geography**: Optional location context
- **Coherence**: Feels like "the same story"

### Framed Narrative (FN)
Stanceful rendering showing how outlets frame/position an Event Family:
- **Evidence-based**: Must cite specific headline evidence
- **Evaluative**: Clear stance (supportive, critical, neutral, etc.)
- **Language**: Key phrases that signal framing
- **Prevalence**: How dominant this framing is

## System Architecture

```
CLUST-2 Buckets → GEN-1 → Event Families + Framed Narratives
                     ↓
               LLM Intelligence + Cross-Bucket Merging
```

### Key Components

1. **Models** (`models.py`): Pydantic data models for Event Families and Framed Narratives
2. **LLM Client** (`llm_client.py`): Specialized LLM interactions with expert prompting
3. **Database** (`database.py`): Database operations for reading buckets and writing results
4. **Processor** (`processor.py`): Core orchestration logic with validation
5. **Validation** (`validation.py`): Quality control and metrics
6. **CLI Runner** (`run_gen1.py`): Command-line interface

## Key Features

### Cross-Bucket Intelligence
- **Buckets as Hints**: CLUST-2 buckets are processing hints only
- **Free Merging**: LLM can pull titles across buckets or exclude within buckets
- **Smart Boundaries**: Focus on coherent events, not rigid bucket boundaries

### Quality Controls
- **Confidence Scoring**: LLM confidence in event coherence
- **Evidence Requirements**: Framed Narratives must cite supporting headlines
- **Validation Pipeline**: Automatic quality checks and recommendations
- **Processing Metrics**: Success rates, quality scores, error tracking

### Production Features
- **Database Integration**: Reads from CLUST-2, writes normalized records
- **Batch Processing**: Handles large volumes with LLM context management
- **Error Handling**: Robust error recovery and logging
- **Monitoring**: Processing statistics and quality metrics

## Installation and Setup

### 1. Database Schema Setup

Create the required database tables:

```bash
cd C:\Users\Maksim\Documents\SNI
PYTHONPATH=. python apps/gen1/setup_schema.py create
```

Verify the schema:
```bash
PYTHONPATH=. python apps/gen1/setup_schema.py verify
```

### 2. Configuration

GEN-1 uses the existing SNI configuration in `core/config.py`. Ensure these are set:

- **Database**: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **LLM**: `DEEPSEEK_API_KEY` (or other LLM provider keys)
- **Processing**: `PROCESSING_WINDOW_HOURS` (default: 72)

### 3. Prerequisites

Ensure the following are available:
- CLUST-2 has created buckets and bucket_members tables
- Strategic titles have been processed (gate_keep = true)
- LLM service is accessible

## Usage

### Basic Processing

Process recent buckets into Event Families:

```bash
cd C:\Users\Maksim\Documents\SNI
PYTHONPATH=. python apps/gen1/run_gen1.py
```

### Advanced Options

```bash
# Process last 48 hours with minimum 3 titles per bucket
PYTHONPATH=. python apps/gen1/run_gen1.py --hours 48 --min-size 3

# Dry run (don't save to database)
PYTHONPATH=. python apps/gen1/run_gen1.py --dry-run

# Process maximum 20 buckets
PYTHONPATH=. python apps/gen1/run_gen1.py --max-buckets 20

# Show processing summary
PYTHONPATH=. python apps/gen1/run_gen1.py --summary

# Verbose logging
PYTHONPATH=. python apps/gen1/run_gen1.py --verbose

# Check system readiness
PYTHONPATH=. python apps/gen1/run_gen1.py --check
```

### Environment Variables

Control processing with environment variables:

```bash
# Processing window
export PROCESSING_WINDOW_HOURS=96

# LLM configuration  
export DEEPSEEK_API_KEY=your_key_here
export LLM_PROVIDER=deepseek
export MAX_TOKENS_PER_REQUEST=4000
```

## Database Schema

### Event Families Table

```sql
CREATE TABLE event_families (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    key_actors TEXT[],
    event_type TEXT NOT NULL,
    geography TEXT,
    event_start TIMESTAMP WITH TIME ZONE NOT NULL,
    event_end TIMESTAMP WITH TIME ZONE,
    source_bucket_ids TEXT[],
    source_title_ids TEXT[],
    confidence_score DECIMAL(3,2),
    coherence_reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Framed Narratives Table

```sql
CREATE TABLE framed_narratives (
    id UUID PRIMARY KEY,
    event_family_id UUID REFERENCES event_families(id),
    frame_type TEXT NOT NULL,
    frame_description TEXT NOT NULL,
    stance_summary TEXT NOT NULL,
    supporting_headlines TEXT[],
    supporting_title_ids TEXT[],
    key_language TEXT[],
    prevalence_score DECIMAL(3,2),
    evidence_quality DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Processing Flow

### Phase 1: Bucket Loading
1. Query CLUST-2 buckets from the last N hours
2. Filter by minimum bucket size
3. Order by processing priority (newest first, largest first, etc.)
4. Load associated titles and metadata

### Phase 2: Event Family Assembly
1. Group buckets into processing batches (manage LLM context)
2. Send bucket contexts to LLM with assembly instructions
3. LLM identifies coherent Event Families across/within buckets
4. Create EventFamily objects with metadata and confidence scores

### Phase 3: Framed Narrative Generation
1. For each Event Family, gather title contexts
2. Send to LLM with framing analysis instructions
3. LLM identifies distinct framing approaches
4. Create FramedNarrative objects with evidence and scores

### Phase 4: Validation and Quality Control
1. Validate Event Families (confidence, coherence, completeness)
2. Validate Framed Narratives (evidence, stance clarity, language)
3. Generate quality metrics and recommendations
4. Flag low-quality results for review

### Phase 5: Database Storage
1. Save Event Families with normalized schema
2. Save Framed Narratives linked to Event Families
3. Update processing statistics and metrics
4. Log results for monitoring and analysis

## LLM Prompting Strategy

### Event Family Assembly
- **System Prompt**: Expert news analyst identifying coherent events
- **Context**: Multiple buckets with actor sets and titles
- **Instructions**: Buckets are hints only, focus on coherent happenings
- **Output**: JSON with Event Families, reasoning, and confidence

### Framed Narrative Generation
- **System Prompt**: Expert in media framing analysis
- **Context**: Event Family details and associated headlines
- **Instructions**: Identify distinct framings with specific evidence
- **Output**: JSON with Framed Narratives and analysis

## Quality Metrics

### Event Family Quality
- **Confidence Score**: LLM confidence in event coherence (0.0-1.0)
- **Coherence Reason**: Detailed explanation of why titles form coherent event
- **Actor Relevance**: Key actors are specific and relevant
- **Time Coherence**: Event boundaries make temporal sense

### Framed Narrative Quality
- **Evidence Quality**: Supporting headlines clearly demonstrate framing (0.0-1.0)
- **Prevalence Score**: How dominant this framing is among sources (0.0-1.0)
- **Stance Clarity**: Frame description is specific and evaluative
- **Language Precision**: Key phrases accurately capture framing signals

### Processing Quality
- **Success Rate**: Percentage of buckets successfully processed
- **Validation Rate**: Percentage of results passing quality checks
- **Processing Speed**: Time per bucket/title
- **Error Tracking**: Types and frequency of processing errors

## Integration with SNI Pipeline

### Upstream Dependencies
- **Ingestion**: Feeds must be ingested and processed
- **CLUST-1**: Strategic gate must filter relevant titles
- **CLUST-2**: Actor sets must be extracted and buckets created

### Downstream Consumers
- **Analytics**: Event Families provide structured event data
- **API**: Framed Narratives expose media framing insights
- **Dashboards**: Processing metrics inform system health
- **Research**: Quality Event Families enable narrative analysis

## Monitoring and Operations

### Processing Logs
- **File Logs**: Detailed processing logs in `logs/gen1_YYYYMMDD.log`
- **Console Logs**: Real-time processing status and results
- **Error Logs**: Failures, warnings, and quality issues

### Key Metrics to Monitor
- **Processing Volume**: Buckets and titles processed per hour/day
- **Quality Scores**: Average confidence and evidence quality
- **Error Rates**: Failed processing and validation failures
- **LLM Performance**: Response times and token usage

### Operational Commands

```bash
# Check system health
PYTHONPATH=. python apps/gen1/run_gen1.py --check

# Get processing summary
PYTHONPATH=. python apps/gen1/run_gen1.py --summary

# Validate recent processing
PYTHONPATH=. python apps/gen1/setup_schema.py verify
```

## Troubleshooting

### Common Issues

1. **No buckets found**: Ensure CLUST-2 is running and creating buckets
2. **LLM errors**: Check API keys and service availability
3. **Database errors**: Verify schema exists and connection works
4. **Low quality scores**: Review LLM prompts and validation thresholds

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```bash
PYTHONPATH=. python apps/gen1/run_gen1.py --verbose --dry-run
```

### Schema Management

```bash
# Drop and recreate schema (WARNING: deletes all data)
PYTHONPATH=. python apps/gen1/setup_schema.py drop --force
PYTHONPATH=. python apps/gen1/setup_schema.py create
```

## Development

### Testing Changes

```bash
# Test with dry run
PYTHONPATH=. python apps/gen1/run_gen1.py --dry-run --max-buckets 5

# Test schema changes
PYTHONPATH=. python apps/gen1/setup_schema.py verify
```

### Adding New Features

1. Update data models in `models.py`
2. Modify LLM prompts in `llm_client.py` 
3. Update database operations in `database.py`
4. Add validation rules in `validation.py`
5. Test with `--dry-run` mode

### Performance Optimization

- **Batch Size**: Adjust `max_buckets_per_batch` for LLM context limits
- **Processing Windows**: Tune `PROCESSING_WINDOW_HOURS` for relevance vs. volume
- **Quality Thresholds**: Balance quality vs. quantity in validation rules

---

**GEN-1** transforms raw news buckets into structured Event Families and insightful Framed Narratives, providing the foundation for sophisticated narrative intelligence analysis.
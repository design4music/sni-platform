# SNI v3 Pipeline Daemon

Production daemon running Phases 1-4 on configurable intervals.

## Usage

```bash
python pipeline/runner/pipeline_daemon.py
```

Press Ctrl+C to stop gracefully.

## Pipeline Phases

**Phase 1: RSS Ingestion** (every 1 hour)
- Fetches new titles from active feeds

**Phase 2: Centroid Matching** (every 5 minutes)  
- Matches titles to centroids

**Phase 3: Track Assignment** (every 10 minutes)
- Assigns tracks, creates/updates CTMs

**Phase 4.1: Events Digest** (every 1 hour)
- Extracts events from titles (with batching + consolidation)

**Phase 4.2: Summary Generation** (every 1 hour)
- Generates summaries from events
- Monitors word counts

## How Updates Work

As new titles arrive daily:
- `ctm.title_count` increments
- `ctm.events_digest` regenerated from all titles
- `ctm.summary_text` rewritten from current events

The system handles accumulation through:
- Event consolidation (reduces redundancy)
- LLM prompt (enforces 150-250 word limit)
- Hard token cap (500 tokens max)

## Testing

Run for several consecutive days to assess:
- Do summaries stay under 250 words as events accumulate?
- At what point does quality degrade?
- Which CTMs grow fastest?

This data will inform whether current architecture works or if CTW (weekly) is needed.

## Configuration

Settings in `core/config.py` (thresholds, concurrency, batch sizes).
Intervals in `pipeline_daemon.py` (phase timing).

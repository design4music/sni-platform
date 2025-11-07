# SNI v3 Pipeline Daemon

Orchestrates the complete v3 pipeline with intelligent scheduling and queue monitoring.

## Architecture

### Pipeline Phases

1. **Phase 1: RSS Ingestion** (1 hour interval)
   - Fetches RSS feeds from Google News
   - Inserts into `titles_v3` with `processing_status='pending'`

2. **Phase 2: Centroid Matching** (5 minute interval)
   - Fast mechanical matching (theater → systemic → macro)
   - Assigns `centroid_ids`, sets `processing_status='assigned'`
   - Processes 500 titles per run

3. **Phase 3: Track Assignment** (10 minute interval)
   - LLM-based track classification
   - Creates CTMs (centroid+track+month)
   - Processes 100 CTMs per run

4. **Phase 4: Enrichment** (1 hour interval)
   - 4.1: Events digest extraction
   - 4.2: Narrative summary generation
   - Processes 50 CTMs per run
   - Lower priority (can wait)

### Key Features

- **Adaptive Scheduling**: Checks queue depths, skips phases with no work
- **Graceful Shutdown**: Handles SIGINT/SIGTERM cleanly
- **Retry Logic**: 3 attempts with exponential backoff
- **Queue Monitoring**: Real-time visibility into pipeline health
- **Sequential Execution**: Simple, predictable, debuggable

## Running the Daemon

### Development

```bash
# Run directly
python v3/runner/pipeline_daemon.py

# Monitor logs
tail -f logs/pipeline.log
```

### Production (systemd)

```bash
# Install service
sudo cp v3/runner/sni-v3-pipeline.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start/stop service
sudo systemctl start sni-v3-pipeline
sudo systemctl stop sni-v3-pipeline
sudo systemctl restart sni-v3-pipeline

# Enable on boot
sudo systemctl enable sni-v3-pipeline

# Check status
sudo systemctl status sni-v3-pipeline

# View logs
sudo journalctl -u sni-v3-pipeline -f
```

## Configuration

Edit intervals and batch sizes in `pipeline_daemon.py`:

```python
# Intervals (seconds)
self.phase1_interval = 3600  # RSS feeds
self.phase2_interval = 300   # Centroid matching
self.phase3_interval = 600   # Track assignment
self.phase4_interval = 3600  # Enrichment

# Batch sizes
self.phase2_batch_size = 500  # Titles
self.phase3_batch_size = 100  # CTMs
self.phase4_batch_size = 50   # CTMs
```

## Monitoring

### Queue Status

Each cycle displays current queue depths:
```
Queue Status:
  Pending titles (Phase 2):    1,234
  Titles need track (Phase 3): 567
  CTMs need events (Phase 4.1): 89
  CTMs need summary (Phase 4.2): 45
```

### Performance Metrics

Monitor via logs:
- Cycle duration
- Phase execution time
- Success/failure rates
- Retry attempts

### Database Queries

```sql
-- Phase 2 queue
SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'pending';

-- Phase 3 queue
SELECT COUNT(*) FROM titles_v3
WHERE processing_status = 'assigned' AND track IS NULL;

-- Phase 4.1 queue
SELECT COUNT(*) FROM ctm
WHERE title_count > 0 AND events_digest = '[]'::jsonb;

-- Phase 4.2 queue
SELECT COUNT(*) FROM ctm
WHERE jsonb_array_length(events_digest) > 0 AND summary_text IS NULL;
```

## Scaling Considerations

### Current Design (v1)
- Sequential execution
- Single daemon instance
- Fixed batch sizes

### Future Enhancements (v2+)
- Parallel phase execution (Phase 2-4 can run concurrently)
- Multiple daemon instances with work distribution
- Dynamic batch sizing based on queue depth
- Prometheus metrics endpoint
- Health check HTTP endpoint
- Configuration reload without restart

### When to Scale

**Indicators:**
- Phase 2 queue > 10,000 titles (add concurrent matchers)
- Phase 3 queue > 1,000 CTMs (increase LLM concurrency)
- Phase 4 queue > 500 CTMs (run Phase 4 more frequently)

**Bottlenecks:**
- Phase 1: RSS feed fetch time (can parallelize feeds)
- Phase 2: Fast, unlikely bottleneck
- Phase 3: LLM API limits (increase batch size or frequency)
- Phase 4: LLM API limits (increase batch size or frequency)

## Troubleshooting

### Daemon won't start
- Check database connectivity: `psql -U postgres -d sni`
- Verify .env file exists and has correct credentials
- Check Python dependencies: `pip install -r requirements.txt`

### Phase failing repeatedly
- Check logs for specific error
- Verify API keys (Deepseek) in .env
- Check database schema matches v3 expectations
- Manually run phase script to isolate issue

### Queue backing up
- Increase batch size for bottleneck phase
- Decrease interval for bottleneck phase
- Check for errors in phase execution
- Consider scaling (multiple daemon instances)

### Graceful shutdown not working
- Check signal handling (SIGTERM should work)
- Force kill only as last resort: `kill -9 <pid>`
- Review logs for shutdown errors

## Manual Phase Execution

If daemon is stopped, run phases manually:

```bash
# Phase 1
python v3/phase_1/ingest_feeds.py --max-feeds 10

# Phase 2
python v3/phase_2/match_centroids.py --max-titles 500

# Phase 3
python v3/phase_3/assign_tracks.py --max-ctms 100

# Phase 4.1
python v3/phase_4/generate_events_digest.py --max-ctms 50

# Phase 4.2
python v3/phase_4/generate_summaries.py --max-ctms 50
```

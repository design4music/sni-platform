# RAI (Risk Assessment Intelligence) Integration

## Overview

Phase 6 adds external RAI analysis to Framed Narratives. Each FN (along with its parent Event Family context) is sent to https://r-a-i.org/analyst.html for analysis, and results are stored back in the database.

## Architecture

```
Pipeline Flow:
Phase 5 (Framing) → Phase 6 (RAI Analysis)
                     ↓
                 External RAI Service (HTTP POST)
                     ↓
                 Store rai_analysis JSONB in framed_narratives
```

## Data Flow

### Input to RAI Service

```json
{
  "event_family": {
    "ef_id": "...",
    "title": "Biden announces new sanctions...",
    "summary": "...",
    "actors": ["US", "RU", "Biden"],
    "type": "diplomatic",
    "theater": "Eastern Europe",
    "tags": ["sanctions", "economy"],
    "context": "..."
  },
  "framed_narrative": {
    "fn_id": "uuid",
    "frame_description": "Frames as economic warfare",
    "stance_summary": "Sanctions presented as necessary deterrent",
    "supporting_headlines": ["Headline 1", "Headline 2"],
    "created_at": "2025-10-08T...",
    "updated_at": "2025-10-08T..."
  }
}
```

### Output from RAI Service

Based on API_CONTRACT_v1.md from archive:

```json
{
  "adequacy_score": 0.74,
  "final_synthesis": "Overall, the narrative presents a coherent framing...",
  "key_conflicts": [
    "Narrative claims victory yet reports rising energy imports"
  ],
  "blind_spots": [
    "No acknowledgment of rare earth dependency"
  ],
  "radical_shifts": [
    {
      "date": "2025-08-01",
      "description": "Pivot from renewables as climate policy to defense policy"
    }
  ],
  "last_analyzed": "2025-08-01"
}
```

## Database Changes

### Migration: 20251008_add_rai_analysis.sql

Adds `rai_analysis` JSONB column to `framed_narratives` table.

```sql
ALTER TABLE framed_narratives ADD COLUMN rai_analysis JSONB DEFAULT NULL;

-- Indexes for efficient querying
CREATE INDEX idx_framed_narratives_rai_analyzed
    ON framed_narratives(event_family_id)
    WHERE rai_analysis IS NOT NULL;

CREATE INDEX idx_framed_narratives_rai_pending
    ON framed_narratives(created_at DESC)
    WHERE rai_analysis IS NULL;
```

## Configuration

### Environment Variables (.env)

```bash
# RAI Configuration
RAI_API_URL=https://rai-backend-ldy4.onrender.com/api/analyze
RAI_API_KEY=HnD0AKtxbJQuvHYIVoHVGZtvtxDEfihNqLjWlGRKjJI
RAI_TIMEOUT_SECONDS=60
RAI_ENABLED=false  # Set to true after testing

# Phase 6 Controls
PHASE_6_RAI_ENABLED=false  # Enable in pipeline
PHASE_6_MAX_ITEMS=50
PHASE_6_TIMEOUT_MINUTES=20
PHASE_6_CONCURRENCY=3
```

### Config Fields (core/config.py)

- `rai_api_url`: External RAI service endpoint
- `rai_api_key`: Bearer token for authentication
- `rai_timeout_seconds`: HTTP request timeout (default: 60s)
- `rai_enabled`: Global RAI toggle
- `phase_6_rai_enabled`: Enable in pipeline cycle
- `phase_6_max_items`: Max FNs per cycle (default: 50)
- `phase_6_timeout_minutes`: Phase timeout (default: 20 min)
- `phase_6_concurrency`: Parallel HTTP requests (default: 3)

## Usage

### Run Migration

```bash
# Apply migration (if not already run)
psql -U postgres -d sni_v2 -f db/migrations/20251008_add_rai_analysis.sql
```

### Generate API Key

**TODO:** User needs to generate RAI API key at https://r-a-i.org and update `.env`:

```bash
RAI_API_KEY=<your_api_key>
RAI_ENABLED=true
PHASE_6_RAI_ENABLED=true
```

### Standalone Execution

```bash
# Check queue status
python apps/generate/run_rai.py status

# Process up to 50 FNs
python apps/generate/run_rai.py process --max-items 50

# Verbose logging
python apps/generate/run_rai.py process --verbose

# Via pipeline CLI
python run_pipeline.py phase6
python run_pipeline.py phase6 --max-items 10
```

### Pipeline Integration

Phase 6 runs automatically in daemon mode after Phase 5:

```bash
# Enable in .env
PHASE_6_RAI_ENABLED=true

# Runs in pipeline cycle
python run_pipeline.py run --daemon
```

## Processing Logic

### Queue Selection

RAI processor selects Framed Narratives where:
- `rai_analysis IS NULL` (not yet analyzed)
- Parent Event Family status is `'active'` or `'enriched'`
- Ordered by `created_at DESC` (newest first)

### Concurrency Control

- Uses asyncio.Semaphore to limit parallel HTTP requests
- Default concurrency: 3 (conservative for external API)
- Configurable via `PHASE_6_CONCURRENCY`

### Error Handling

- HTTP timeouts logged but don't crash batch
- Failed analyses skip database update (remain in queue)
- Transient failures can be retried in next cycle

### Success Criteria

- HTTP 200 response from RAI service
- Valid JSON response with expected fields
- Database update successful

## Monitoring

### Check Status

```bash
# Quick status
python apps/generate/run_rai.py status

# Output:
# RAI Analysis Status:
#   Pending:  130
#   Analyzed: 42
#   Total:    172
```

### Pipeline Logs

```bash
# Watch Phase 6 in pipeline
tail -f logs/sni_v2.log | grep "PHASE 6"

# Example output:
# 2025-10-08 14:32:15 | INFO | === PHASE 6: RAI ANALYSIS ===
# 2025-10-08 14:32:15 | INFO | Starting RAI analysis for 50 Framed Narratives
# 2025-10-08 14:33:42 | INFO | RAI batch complete: 48/50 succeeded, 2 failed in 87.3s
```

### Database Query

```sql
-- Count by status
SELECT
    COUNT(*) FILTER (WHERE rai_analysis IS NULL) as pending,
    COUNT(*) FILTER (WHERE rai_analysis IS NOT NULL) as analyzed
FROM framed_narratives fn
JOIN event_families ef ON fn.event_family_id = ef.id
WHERE ef.status IN ('active', 'enriched');

-- Sample RAI results
SELECT
    fn.id,
    ef.title as ef_title,
    fn.stance_summary,
    fn.rai_analysis->>'adequacy_score' as adequacy,
    fn.rai_analysis->>'final_synthesis' as synthesis
FROM framed_narratives fn
JOIN event_families ef ON fn.event_family_id = ef.id
WHERE fn.rai_analysis IS NOT NULL
LIMIT 5;
```

## Next Steps

1. **Generate RAI API Key**
   - Visit https://r-a-i.org/analyst.html
   - Create account / generate key
   - Update `.env` with key

2. **Run Migration**
   ```bash
   psql -U postgres -d sni_v2 -f db/migrations/20251008_add_rai_analysis.sql
   ```

3. **Enable Phase 6**
   ```bash
   # In .env
   RAI_ENABLED=true
   PHASE_6_RAI_ENABLED=true
   ```

4. **Test Standalone**
   ```bash
   # Test with small batch
   python apps/generate/run_rai.py process --max-items 5 --verbose
   ```

5. **Enable in Pipeline**
   - Daemon will pick up Phase 6 in next cycle
   - Monitor logs for success

## Files Changed/Created

### New Files
- `apps/generate/rai_processor.py` - RAI HTTP client and processor
- `apps/generate/run_rai.py` - CLI for standalone execution
- `db/migrations/20251008_add_rai_analysis.sql` - Database schema change
- `docs/RAI_INTEGRATION.md` - This document

### Modified Files
- `core/config.py` - Added RAI configuration fields
- `run_pipeline.py` - Added Phase 6 integration
- `.env` - Added RAI configuration variables

## Dependencies

- `httpx` - Async HTTP client (already in requirements)
- External RAI service at https://r-a-i.org/analyst.html

## Security Notes

- API key stored in `.env` (not committed to git)
- Bearer token authentication used for RAI requests
- Timeout protection against hanging requests
- Rate limiting via concurrency control (3 parallel max)

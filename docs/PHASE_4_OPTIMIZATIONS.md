# Phase 4 Optimizations

## 1. Concurrent Processing with Bounded Semaphore

**Problem**: Sequential processing of 55+ CTMs was slow
**Solution**: Process multiple CTMs concurrently with bounded semaphore

### Implementation

**Configuration** (`core/config.py`):
```python
v3_p4_max_concurrent: int = 5  # Max concurrent CTMs
```

**Architecture**:
- Each CTM = 1 LLM call (no change)
- N CTMs run concurrently (bounded by semaphore)
- Semaphore limits concurrent API calls to avoid rate limits

### Benefits

- **5x speedup**: With `max_concurrent=5`, process 5 CTMs simultaneously
- **API-safe**: Semaphore prevents overloading Deepseek API
- **Tunable**: Adjust concurrency via environment variable `V3_P4_MAX_CONCURRENT`

### Usage

```bash
# Default: 5 concurrent
python v3/phase_4/generate_events_digest.py

# Higher concurrency
V3_P4_MAX_CONCURRENT=10 python v3/phase_4/generate_events_digest.py

# Lower concurrency (safer)
V3_P4_MAX_CONCURRENT=3 python v3/phase_4/generate_events_digest.py
```

---

## 2. Date Extraction Validation

**Problem**: LLM occasionally extracts dates outside CTM month (hallucination or parsing errors)
**Solution**: Validate dates fall within reasonable range and flag low-confidence dates

### Implementation

**Validation Logic**:
```python
def validate_and_fix_event_date(event_date_str: str, ctm_month: str):
    # Calculate valid range: [month_start - 5 days, month_end + 5 days]
    if date within valid_range:
        return (date, "high")  # Confidence: high
    else:
        return (month_start, "low")  # Clamped to month start, confidence: low
```

**Buffer Rationale**:
- **±5 days**: Allows for titles published slightly before/after month boundary
- Example: Dec 28 title about Jan 2 event → Valid for Jan CTM
- Prevents dates like "2024-01-05" in a "2026-01" CTM

### Event Schema with Confidence

**Before**:
```json
{
  "date": "2026-01-05",
  "summary": "Event description",
  "source_title_ids": ["uuid1", "uuid2"]
}
```

**After**:
```json
{
  "date": "2026-01-05",
  "summary": "Event description",
  "source_title_ids": ["uuid1", "uuid2"],
  "date_confidence": "high"  // or "low"
}
```

### Auditability

- **High confidence**: Date extracted correctly, within expected range
- **Low confidence**: Date was out of range, clamped to month_start
  - Allows manual review of questionable dates
  - Prevents breaking UI/reports with invalid dates
  - Maintains data integrity

### Applied In

1. **Phase 4.1 batch extraction**: Validates dates from individual batches
2. **Phase 4.1 consolidation**: Re-validates dates in consolidated events
3. **Both passes**: Ensures all dates are validated regardless of processing path

---

## Performance Impact

### Before Optimizations

- **Sequential processing**: 55 CTMs × ~30s = ~27 minutes
- **No date validation**: Occasional invalid dates breaking reports

### After Optimizations

- **Concurrent processing** (5x): 55 CTMs ÷ 5 × ~30s = ~5.5 minutes
- **Date validation**: 100% valid dates with confidence tracking
- **Total speedup**: ~5x faster with better data quality

---

## Upcoming: System Prompt Improvements (Optimization #3)

**Status**: In progress (awaiting detailed requirements)

**Planned improvements**:
- Domain-specific prompt templates
- Enhanced deduplication instructions
- Better date extraction guidance
- Track-specific tone adjustments

---

## Configuration Summary

```python
# core/config.py
v3_p4_batch_size: int = 70           # API limit (discovered empirically)
v3_p4_min_titles: int = 20           # Daily processing threshold
v3_p4_max_concurrent: int = 5        # NEW: Concurrent CTMs
v3_p4_temperature: float = 0.5       # Summary creativity
v3_p4_max_tokens: int = 500          # Summary length
v3_p4_timeout_seconds: int = 600     # LLM timeout
```

**Environment variables**:
- `V3_P4_MAX_CONCURRENT=5` - Adjust concurrency
- All other params also configurable via env vars

---

## Testing Recommendations

1. **Start conservative**: Test with `max_concurrent=3` on first run
2. **Monitor API**: Watch for rate limit errors
3. **Gradual increase**: If no errors, increase to 5, then 10
4. **Date validation**: Check events for `date_confidence: "low"` flags
5. **Review outliers**: Manually inspect low-confidence dates

---

## Future Optimizations

1. **Delta processing**: Only process titles added since last run
2. **Smart scheduling**: High-volume CTMs early, low-volume at night
3. **Dynamic concurrency**: Adjust based on API response times
4. **Event caching**: Cache consolidated events to avoid re-consolidation
5. **Prompt templates**: Track-specific prompt optimization

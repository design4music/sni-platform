# Phase 2 v3: Centroid Matching

This phase assigns each title to a centroid using a 3-pass mechanical matching system.

## 3-Pass Matching Logic

### Pass 1: Theater-based (60-70% coverage)
- Geographic centroids with clear theaters (Ukraine, Israel, Taiwan, etc.)
- Uses countries, cities, persons, organizations from taxonomy_v3
- High precision, direct entity matching

### Pass 2: Global/Systemic (15-20% coverage)
- Systemic topics without single theaters (Climate, Energy, Pandemics, Tech)
- Uses institutional anchors (UNFCCC, OPEC, WHO, TSMC, etc.)
- Narrow, high-precision term matching

### Pass 3: Superpower buckets (10-15% coverage)
- Catch-all for major power markers (US, China, EU, Russia)
- Broad domestic/multi-vector centroids
- Prevents unclassified overflow

## Output

Each title gets:
- `centroid_id` - Matched centroid (or NULL if out of scope)
- `centroid_match_pass` - Which pass matched (1, 2, or 3)
- `centroid_confidence` - Match confidence score (0.0-1.0)
- `processing_status` - Updated to 'centroid_assigned' or 'out_of_scope'

## Implementation

The matcher queries `taxonomy_v3` by `match_pass` priority and scores matches based on:
- Term frequency in title
- Match weight from taxonomy
- Centroid priority

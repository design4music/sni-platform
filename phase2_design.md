# Phase 2: Direct Title→EF Assignment - Design Document

## Current Architecture Issues

**Current Flow:**
```
Titles → Buckets (CLUST-2) → Bucket Members → Event Families (GEN-1)
```

**Problems:**
- Unnecessary CLUST-2 bucketing step
- 31 columns in titles table (many unused)  
- Complex bucket/bucket_members relationships
- LLM has to work around bucket boundaries

## New Architecture (Phase 2)

**New Flow:**
```
Titles → Event Families (Direct Assignment)
```

## Database Schema Changes

### 1. Streamlined Titles Table

**Keep Essential Columns:**
```sql
-- Core identification
id (uuid, PK)
title_display (text, NOT NULL)
url_gnews (text, NOT NULL)
publisher_name (varchar)
pubdate_utc (timestamp)
detected_language (varchar)

-- Strategic filtering (CLUST-1 results)  
gate_keep (boolean, NOT NULL)
gate_reason (text)
gate_score (real)
gate_actor_hit (text)

-- Entity extraction for EF matching
entities (jsonb)

-- Direct EF assignment (NEW)
event_family_id (uuid, FK to event_families.id)
ef_assignment_confidence (real)
ef_assignment_reason (text)
ef_assignment_at (timestamp)

-- Timestamps
ingested_at (timestamp)
created_at (timestamp)
```

**Remove Unused Columns (10 columns):**
- publisher_country_code, lang
- is_strategic, strategic_confidence, strategic_signals
- entity_count, title_embedding, title_embedding_json
- processed_at, gate_anchor_labels

### 2. Remove Bucket Tables

**Drop Tables:**
- `buckets` (entire table)
- `bucket_members` (entire table)

### 3. Enhanced Event Families Table

**Add Direct Title Tracking:**
```sql
-- Already exists in current schema:
source_title_ids (text[])  -- Array of title UUIDs

-- Add for better querying:
CREATE INDEX idx_event_families_source_titles ON event_families USING GIN(source_title_ids);
```

## GEN-1 Processor Changes

### Current Process:
1. Query buckets table for recent buckets
2. Get bucket_members for each bucket
3. Group titles by bucket
4. Send bucket contexts to LLM
5. LLM creates Event Families

### New Process:
1. Query titles table directly (`gate_keep = true` AND `event_family_id IS NULL`)
2. Group titles by strategic similarity (actors, time window (?), geography)
3. Send title batches to LLM
4. LLM creates Event Families
5. Update titles with `event_family_id`

## Migration Strategy

### Step 1: Schema Migration
```sql
-- Add new columns to titles
ALTER TABLE titles ADD COLUMN event_family_id uuid REFERENCES event_families(id);
ALTER TABLE titles ADD COLUMN ef_assignment_confidence real;
ALTER TABLE titles ADD COLUMN ef_assignment_reason text;
ALTER TABLE titles ADD COLUMN ef_assignment_at timestamp;

-- Create index for EF lookups
CREATE INDEX idx_titles_event_family_id ON titles(event_family_id);
CREATE INDEX idx_titles_unassigned ON titles(gate_keep, event_family_id) WHERE gate_keep = true AND event_family_id IS NULL;
```

### Step 2: Update GEN-1 Processor
- New `get_unassigned_strategic_titles()` method
- Replace bucket context with title context
- Update LLM prompts for direct title processing
- Add title→EF assignment logic

### Step 3: Schema Cleanup (After Testing)
```sql
-- Remove unused columns
ALTER TABLE titles 
DROP COLUMN publisher_country_code,
DROP COLUMN lang, 
DROP COLUMN is_strategic,
DROP COLUMN strategic_confidence, DROP COLUMN strategic_signals,
DROP COLUMN entity_count, DROP COLUMN title_embedding,
DROP COLUMN title_embedding_json,
DROP COLUMN processed_at,
DROP COLUMN gate_anchor_labels;

-- Drop bucket tables
DROP TABLE bucket_members;
DROP TABLE buckets;
```

## Benefits

1. **Simplified Architecture** - Direct title→EF assignment
2. **Reduced Storage** - 22 fewer columns, 2 fewer tables
3. **Better Performance** - No complex bucket joins
4. **More Flexible** - LLM works with natural title groups
5. **Real-time Assignment** - New titles assigned to EFs immediately
6. **Cleaner Data Model** - Titles belong to EFs explicitly

## Testing Strategy

1. **Backup Current Data** - Full database backup
2. **Parallel Testing** - Run both old and new systems
3. **Gradual Migration** - Assign existing Event Family titles first
4. **Validation** - Compare results between systems
5. **Cleanup** - Remove bucket tables after successful migration

## Implementation Order

1. Add new columns to titles table ✅ Next
2. Update GEN-1 processor for direct title processing
3. Test with recent unassigned strategic titles
4. Migrate existing Event Family titles
5. Remove unused columns and bucket tables

This eliminates the intermediate CLUST-2 bucket layer entirely, creating a much cleaner and more direct architecture.
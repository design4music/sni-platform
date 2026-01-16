# SNI v3: Centroid-Based Architecture - Design Document

**Status:** Design Phase
**Created:** 2025-10-30
**Goal:** Replace P2-P3 with deterministic centroid matching and CTM (Centroid-Track-Month) aggregation

---

## Executive Summary

SNI v3 replaces fuzzy LLM-based strategic filtering and event clustering with **deterministic centroid matching** and **CTM units** (Centroid × Track × Month).

**Key Changes:**
- **P2:** 3-pass mechanical centroid matching (no LLM gate_keep)
- **P3:** CTM aggregation with LLM track assignment (replaces Event Families)
- **Outcome:** Stable, comparable analytical units instead of fuzzy event clusters

---

## Architecture Overview

### Current (SNI v2)
```
Title → Entity Extraction → Strategic Filter (LLM) → Event Clustering (Graph+LLM) → Event Families
```

### Proposed (SNI v3)
```
Title → Centroid Matching (3-pass mechanical) → Track Assignment (LLM) → CTM Aggregation
```

---

## Core Concepts

### 1. **Centroids** (Narrative Anchors)

Stable points of narrative gravity that titles cluster around.

**Types:**
- **Geographic:** War in Ukraine, Israel-Palestine Conflict, Taiwan Strait
- **Systemic/Global:** Climate Change, Global Energy, Pandemic Response
- **Superpower Domestic:** US Domestic, China Domestic, EU Domestic

**Current Count:** 26 centroids (target: 25-30 for initial launch)

**Properties:**
- `id`: Unique identifier (e.g., `ARC-UKR`, `ARC-MIDEAST-ISR`)
- `label`: Human-readable name
- `keywords`: Array of match terms
- `actors`: Array of key actors
- `theaters`: Array of geographic theaters
- `centroid_type`: `geographic` / `systemic` / `superpower`

---

### 2. **Three-Pass Centroid Matching**

#### **Pass 1: Theater-Based (60-70% coverage)**
- Match against geographic centroids using simple taxonomy
- Countries, cities, key actors directly linked to centroids
- Example: "Biden visits Kyiv" → Ukraine centroid (via "Kyiv" keyword)

#### **Pass 2: Systemic/Global (15-20% coverage)**
- Match specialized institutional anchors: UNFCCC, COP30, WTO, TSMC
- Global topics: energy, tech, climate, refugees, pandemics
- Example: "COP30 climate summit" → Climate Change centroid

#### **Pass 3: Superpower Buckets (10-15% coverage)**
- Catch-all for major powers: US, China, EU, Russia
- Prevents unclassified overflow
- Example: "Federal Reserve rate decision" → US Domestic centroid

**Unmatched = Out of Scope** (no more gate_keep ambiguity)

---

### 3. **CTM Units** (Centroid-Track-Month)

Deterministic aggregation replacing Event Families.

```
CTM = (Centroid) × (Track) × (Month)

Example:
  Centroid: israel_palestine_conflict
  Track: military
  Month: 2025-01
  → CTM: israel_palestine_conflict × military × 2025-01
```

**Tracks (LLM-assigned, one per title):**
- `military` - Military operations, force deployment
- `diplomacy` - Negotiations, summits, diplomatic statements
- `economic` - Sanctions, trade, economic policy
- `tech_cyber` - Technology, cybersecurity, information warfare
- `humanitarian` - Aid, refugees, civilian impact
- `information_media` - Media coverage, propaganda, narratives
- `legal_regulatory` - Laws, regulations, international law

---

## Database Schema

### Existing Tables (Reference)

#### **1. `centroids` (KEEP, EXTEND)**
```sql
-- Current schema
id VARCHAR(50) PRIMARY KEY
label TEXT NOT NULL
keywords TEXT[]
actors TEXT[]
theaters TEXT[]
created_at TIMESTAMP
updated_at TIMESTAMP
```

**Coverage:** 26 centroids
- War in Ukraine (ARC-UKR)
- Israel-Palestine (ARC-MIDEAST-ISR)
- US-China Relations (ARC-US-CN)
- Climate Change (TRANS-CLIMATE)
- Global Energy (TRANS-ENERGY)
- etc.

#### **2. `data_entities` (USE FOR PASS 1)**
```sql
-- Current schema (577 entities)
id UUID PRIMARY KEY
entity_id TEXT UNIQUE NOT NULL          -- "US", "CN", "META", "joe_biden"
entity_type TEXT NOT NULL               -- "COUNTRY", "PERSON", "ORG", "Company"
iso_code TEXT                           -- ISO country code
wikidata_qid TEXT                       -- Wikidata identifier
name_en TEXT NOT NULL                   -- "United States", "Joe Biden"
aliases JSONB                           -- Multilingual aliases
capital_entity_id TEXT                  -- Link to capital
country_entity_id TEXT                  -- Link to parent country
```

**Entity Types:**
- COUNTRY (181)
- CAPITAL (179)
- PERSON (60)
- Company (49)
- ORG (35)
- PoliticalParty (16)
- Others (57)

#### **3. `taxonomy_categories` (REFERENCE FOR PASS 2)**
```sql
-- Current schema (43 categories)
category_id TEXT PRIMARY KEY
name_en TEXT NOT NULL
description TEXT
is_positive BOOLEAN                     -- True=GO_LIST, False=STOP_LIST
is_active BOOLEAN
```

**Strategic Categories (is_positive=true):**
- politics_* (7 categories)
- economics_* (6 categories)
- security_* (3 categories)
- technology_* (4 categories)
- energy_* (5 categories)
- health_* (3 categories)
- environment_* (3 categories)

**STOP Categories (is_positive=false):**
- sport_* (5 categories) - Football, Olympics, General, etc.
- culture_* (6 categories) - Art, Cinema, Fashion, etc.

#### **4. `taxonomy_terms` (USE FOR PASS 2)**
```sql
-- Current schema (289 terms)
id UUID PRIMARY KEY
category_id TEXT REFERENCES taxonomy_categories
name_en TEXT NOT NULL
terms JSONB NOT NULL                    -- Multilingual term arrays
is_active BOOLEAN
```

**Example terms:**
- politics_diplomacy: ["summit", "treaty", "diplomatic"]
- energy_production: ["oil", "gas", "coal", "nuclear"]
- sport_football: ["FIFA", "Premier League", "Champions League"]

---

### New Tables (SNI v3)

#### **1. `centroids_v3` (REPLACES `centroids`)**
```sql
CREATE TABLE centroids_v3 (
    id TEXT PRIMARY KEY,                    -- "ukraine_conflict", "climate_change"
    label TEXT NOT NULL,                    -- "War in Ukraine"
    description TEXT,                       -- Optional longer description

    -- Centroid classification
    centroid_type TEXT NOT NULL,            -- "geographic" / "systemic" / "superpower"
    primary_theater TEXT,                   -- "Ukraine" / "Global" / "United States"

    -- Matching configuration
    match_priority INT DEFAULT 50,          -- Higher = matched first
    keywords TEXT[],                        -- Direct match terms
    required_actors TEXT[],                 -- Must have these actors
    required_entities TEXT[],               -- Must have these entities

    -- Status
    status TEXT DEFAULT 'active',           -- "active" / "archived" / "deprecated"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_centroids_v3_type ON centroids_v3(centroid_type);
CREATE INDEX idx_centroids_v3_status ON centroids_v3(status);
```

**Design Notes:**
- Simplified from current `centroids` table
- Added `centroid_type` for 3-pass logic
- Added `match_priority` for ordering
- Added `required_actors/entities` for precise matching
- Removed `theaters` array (use `primary_theater` string)

---

#### **2. `taxonomy_v3` (MERGES `data_entities` + `taxonomy_terms`)**
```sql
CREATE TABLE taxonomy_v3 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Term identification
    term TEXT NOT NULL,                     -- "Kyiv" / "UNFCCC" / "United States"
    term_type TEXT NOT NULL,                -- "entity" / "keyword" / "institution"

    -- Centroid linking
    centroid_id TEXT REFERENCES centroids_v3(id),
    match_pass INT NOT NULL,                -- 1 (theater), 2 (global), 3 (superpower)
    match_weight DECIMAL DEFAULT 1.0,       -- 0.0-1.0 (for multi-term matching)

    -- Additional metadata (from data_entities)
    entity_id TEXT,                         -- "US", "kyiv", "joe_biden" (if entity)
    entity_type TEXT,                       -- "COUNTRY", "CAPITAL", "PERSON" (if entity)
    iso_code TEXT,                          -- ISO country code (if applicable)

    -- Multilingual support
    aliases JSONB,                          -- {en: [...], es: [...], fr: [...]}

    -- Status
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_taxonomy_v3_term ON taxonomy_v3(term);
CREATE INDEX idx_taxonomy_v3_centroid ON taxonomy_v3(centroid_id);
CREATE INDEX idx_taxonomy_v3_pass ON taxonomy_v3(match_pass);
CREATE INDEX idx_taxonomy_v3_entity_id ON taxonomy_v3(entity_id);
```

**Design Notes:**
- **Merges** `data_entities` + `taxonomy_terms` into single lookup table
- Each term links to a centroid and has a match pass (1, 2, or 3)
- Preserves entity metadata (entity_id, iso_code) for Pass 1
- Preserves multilingual aliases for matching
- Simple, flat structure for fast lookups

**Example Records:**

```sql
-- Pass 1: Theater-based (geographic entities)
{term: "Kyiv", term_type: "entity", centroid_id: "ukraine_conflict",
 match_pass: 1, entity_id: "kyiv", entity_type: "CAPITAL", iso_code: "UA"}

{term: "Zelensky", term_type: "entity", centroid_id: "ukraine_conflict",
 match_pass: 1, entity_id: "volodymyr_zelensky", entity_type: "PERSON", iso_code: "UA"}

-- Pass 2: Global/systemic (institutional anchors)
{term: "UNFCCC", term_type: "institution", centroid_id: "climate_change",
 match_pass: 2, entity_id: NULL}

{term: "COP30", term_type: "keyword", centroid_id: "climate_change",
 match_pass: 2, entity_id: NULL}

-- Pass 3: Superpower buckets
{term: "United States", term_type: "entity", centroid_id: "us_domestic",
 match_pass: 3, entity_id: "US", entity_type: "COUNTRY", iso_code: "US"}
```

---

#### **3. `ctm` (NEW - Centroid-Track-Month Units)**
```sql
CREATE TABLE ctm (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- CTM composite key
    centroid_id TEXT NOT NULL REFERENCES centroids_v3(id),
    track TEXT NOT NULL,                    -- "military" / "diplomacy" / "economic"
    month DATE NOT NULL,                    -- First day of month: "2025-01-01"

    -- Aggregation metadata
    title_count INT DEFAULT 0,
    first_title_date TIMESTAMP,
    last_title_date TIMESTAMP,

    -- Status
    status TEXT DEFAULT 'active',           -- "active" / "archived"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(centroid_id, track, month)
);

CREATE INDEX idx_ctm_centroid ON ctm(centroid_id);
CREATE INDEX idx_ctm_month ON ctm(month);
CREATE INDEX idx_ctm_composite ON ctm(centroid_id, track, month);
```

**Design Notes:**
- Simple aggregation table
- One CTM = all titles for (centroid × track × month)
- `title_count` updated incrementally as titles assigned
- `month` is DATE (first day of month) for easy grouping

---

#### **4. `titles_v3` (NEW VERSION)**
```sql
CREATE TABLE titles_v3 (
    -- Core identity (from titles)
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title_display TEXT NOT NULL,
    title_clean TEXT,
    url_gnews TEXT,
    publisher_name TEXT,
    pubdate_utc TIMESTAMP NOT NULL,
    detected_language TEXT,

    -- SNI v3: Centroid assignment
    centroid_id TEXT REFERENCES centroids_v3(id),
    centroid_match_pass INT,                -- 1, 2, 3, or NULL (unmatched)
    centroid_confidence DECIMAL,            -- 0.0-1.0

    -- SNI v3: Track assignment
    track TEXT,                             -- "military" / "diplomacy" / etc.
    track_confidence DECIMAL,               -- 0.0-1.0 (LLM confidence)

    -- SNI v3: CTM linkage
    ctm_id UUID REFERENCES ctm(id),
    ctm_month DATE,                         -- Denormalized for fast queries

    -- Metadata
    processing_status TEXT DEFAULT 'raw',   -- "raw" / "centroid_matched" / "ctm_assigned"
    processing_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_titles_v3_centroid ON titles_v3(centroid_id);
CREATE INDEX idx_titles_v3_ctm ON titles_v3(ctm_id);
CREATE INDEX idx_titles_v3_month ON titles_v3(ctm_month);
CREATE INDEX idx_titles_v3_pubdate ON titles_v3(pubdate_utc);
CREATE INDEX idx_titles_v3_status ON titles_v3(processing_status);
```

**Design Notes:**
- **Drops** from `titles` table:
  - `entities` (not needed, use `taxonomy_v3` for matching)
  - `action_triple` (not used in v3)
  - `gate_keep` (replaced by `centroid_id IS NOT NULL`)
  - `event_id` (replaced by `ctm_id`)

- **Adds** v3-specific fields:
  - `centroid_id` + `centroid_match_pass` + `centroid_confidence`
  - `track` + `track_confidence`
  - `ctm_id` + `ctm_month` (denormalized)
  - `processing_status` (tracks pipeline progress)

- **Keeps** core fields:
  - title, URL, publisher, pubdate, language

---

## Migration from Existing Tables

### Data Flow

```
EXISTING                          NEW (v3)
--------                          --------
centroids (26 records)     →      centroids_v3 (26 records, extended)
                                  - Add: centroid_type, match_priority
                                  - Add: required_actors/entities

data_entities (577)        →      taxonomy_v3 (~600-800 records)
taxonomy_terms (289)              - Merge entities + terms
                                  - Add: centroid_id, match_pass
                                  - Keep: aliases, entity metadata

titles (current)           →      titles_v3 (simplified)
                                  - Drop: entities, action_triple, gate_keep, event_id
                                  - Add: centroid_id, track, ctm_id

(NEW)                      →      ctm (generated)
                                  - Create from titles_v3 aggregation
```

---

## Implementation Plan

### Folder Structure
```
/pipeline/
  /phase_1/           # Ingestion (reuse /apps/ingest/ or copy)
    run_p1_v3.py

  /phase_2/           # Centroid matching
    centroid_matcher.py
    taxonomy_loader_v3.py
    run_p2_v3.py

  /phase_3/           # CTM building
    track_classifier.py
    ctm_builder.py
    run_p3_v3.py

  /shared/            # Common utilities
    config_v3.py
    db_models_v3.py
```

### Configuration (`/core/config.py`)
```python
# ============================================================================
# SNI v3 Configuration
# ============================================================================

# Folder paths (configurable for future renaming)
V3_ROOT = Path(__file__).parent.parent / "v3"
V3_PHASE_1_PATH = V3_ROOT / "phase_1"
V3_PHASE_2_PATH = V3_ROOT / "phase_2"
V3_PHASE_3_PATH = V3_ROOT / "phase_3"

# Database tables (v3)
V3_CENTROIDS_TABLE = "centroids_v3"
V3_TAXONOMY_TABLE = "taxonomy_v3"
V3_CTM_TABLE = "ctm"
V3_TITLES_TABLE = "titles_v3"

# Processing parameters
V3_CENTROID_MATCHING_ENABLED = True
V3_TRACK_CLASSIFICATION_ENABLED = True
V3_TRACK_LLM_MODEL = "deepseek-chat"
V3_TRACK_CONCURRENCY = 10
```

---

## Phase Implementations

### **Phase 2 v3: Centroid Matching**

**Input:** Raw titles from Phase 1
**Output:** Titles with `centroid_id` assigned

**Algorithm:**
1. **Pass 1 (Theater-based):**
   - Load all `taxonomy_v3` records where `match_pass=1`
   - For each title, check for entity matches (countries, capitals, persons)
   - If match found: assign `centroid_id`, set `centroid_match_pass=1`

2. **Pass 2 (Global/systemic):**
   - Load all `taxonomy_v3` records where `match_pass=2`
   - For unmatched titles, check for institutional/keyword matches
   - If match found: assign `centroid_id`, set `centroid_match_pass=2`

3. **Pass 3 (Superpower buckets):**
   - Load all `taxonomy_v3` records where `match_pass=3`
   - For still-unmatched titles, check for major power markers
   - If match found: assign `centroid_id`, set `centroid_match_pass=3`

4. **Unmatched:**
   - Titles with `centroid_id IS NULL` are out of scope
   - Set `processing_status='out_of_scope'`

**Key Files:**
- `/pipeline/phase_2/centroid_matcher.py`
- `/pipeline/phase_2/taxonomy_loader_v3.py`
- `/pipeline/phase_2/run_p2_v3.py`

---

### **Phase 3 v3: CTM Building**

**Input:** Titles with `centroid_id` assigned
**Output:** Titles with `track` + `ctm_id` assigned

**Algorithm:**
1. **Track Classification (LLM):**
   - For each title with `centroid_id`:
     - Call LLM with title + centroid context
     - Prompt: "Classify this title into one track: military, diplomacy, economic, tech_cyber, humanitarian, information_media, legal_regulatory"
     - Assign `track` + `track_confidence`

2. **CTM Assignment:**
   - Extract `month` from `pubdate_utc` (first day of month)
   - Look up or create CTM: `(centroid_id, track, month)`
   - Assign `ctm_id` to title
   - Increment `ctm.title_count`

3. **Finalization:**
   - Set `processing_status='ctm_assigned'`
   - Update CTM metadata (`first_title_date`, `last_title_date`)

**Key Files:**
- `/pipeline/phase_3/track_classifier.py`
- `/pipeline/phase_3/ctm_builder.py`
- `/pipeline/phase_3/run_p3_v3.py`

---

## Validation & Testing

### Coverage Metrics

**Expected Coverage:**
- Pass 1 (Theater): 60-70%
- Pass 2 (Global): 15-20%
- Pass 3 (Superpower): 10-15%
- **Total In-Scope: 85-95%**
- Out of Scope: 5-15%

**Validation Queries:**
```sql
-- Coverage by pass
SELECT
    centroid_match_pass,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as pct
FROM titles_v3
WHERE centroid_id IS NOT NULL
GROUP BY centroid_match_pass;

-- Top centroids by title count
SELECT
    c.label,
    COUNT(t.id) as title_count
FROM centroids_v3 c
JOIN titles_v3 t ON t.centroid_id = c.id
GROUP BY c.id, c.label
ORDER BY title_count DESC
LIMIT 20;

-- CTMs by month
SELECT
    ctm_month,
    COUNT(DISTINCT ctm_id) as ctm_count,
    COUNT(*) as title_count
FROM titles_v3
WHERE ctm_id IS NOT NULL
GROUP BY ctm_month
ORDER BY ctm_month DESC;
```

---

## Next Steps

### Immediate (Week 1)
1. ✅ Design database schema (this document)
2. ⏳ Create database migration script
3. ⏳ Create `/pipeline/` folder structure
4. ⏳ Add v3 configuration to `core/config.py`

### Short-term (Week 2-3)
1. ⏳ Migrate `centroids` → `centroids_v3` (add new fields)
2. ⏳ Build `taxonomy_v3` from `data_entities` + `taxonomy_terms`
3. ⏳ Implement Phase 2 v3 (centroid matcher)
4. ⏳ Test Pass 1 coverage on existing titles

### Medium-term (Week 4-5)
1. ⏳ Implement Phase 3 v3 (track classifier + CTM builder)
2. ⏳ Run full pipeline on test data
3. ⏳ Compare v2 vs v3 coverage and quality

### Long-term (Month 2+)
1. ⏳ Adapt Phase 4-6 to work with CTMs
2. ⏳ Deprecate v2 pipeline
3. ⏳ Rename `/pipeline/` → `/pipeline/`

---

**Last Updated:** 2025-10-30
**Status:** Design Complete, Ready for Implementation

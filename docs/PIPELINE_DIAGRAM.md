# SNI-v2 Pipeline Data Flow - Current Implementation

## Rendering Instructions

View this diagram:
- **GitHub/GitLab**: Renders automatically in markdown
- **VS Code**: Install "Markdown Preview Mermaid Support" extension
- **Online**: https://mermaid.live - paste code and export as PNG/SVG
- **Figma**: Export SVG from mermaid.live, drag into Figma

---

## Pipeline Architecture

```mermaid
flowchart TD
    %% External Data Sources
    RSS[(RSS Feeds<br/>~50 sources)]
    DATA_ENTITIES[(data_entities table<br/>Strategic actors & people<br/>iso_code for country enrichment)]
    TAXONOMY[(taxonomy_terms table<br/>GO_LIST & STOP_LIST)]
    EVENT_TYPES[data/event_types.csv<br/>11 event type enums]
    THEATERS[data/theaters.csv<br/>16 theater enums]
    RAI_APP[RAI Service<br/>render.com:rai-backend]
    NEO4J[(Neo4j Graph<br/>Entity network intelligence)]

    %% Database
    DB[(PostgreSQL<br/>sni_v2)]

    %% Phase 1: RSS Ingestion
    P1_START[PHASE 1: RSS INGESTION]
    P1_FETCH[Fetch RSS feeds<br/>lookback_days: 3]
    P1_PARSE[Parse & extract<br/>title, url, publisher, pubdate]
    P1_DEDUP[Deduplicate by content_hash<br/>cosine > 0.95]
    P1_EMBED[Generate embeddings<br/>sentence-transformers/all-MiniLM-L6-v2]
    P1_STORE[INSERT INTO titles<br/>gate_keep=NULL, event_family_id=NULL<br/>processing_status=NULL]

    %% Phase 2: Strategic Filtering + Entity Enrichment
    P2_START[PHASE 2: STRATEGIC FILTERING]
    P2_LOAD[SELECT FROM titles<br/>WHERE entities IS NULL]
    P2_TAXONOMY[Static taxonomy extraction<br/>DB: data_entities + taxonomy_terms<br/>GO_LIST vs STOP_LIST]
    P2_LLM[LLM strategic review<br/>For ambiguous titles<br/>Extract entities + decision]
    P2_NEO4J[Neo4j override<br/>Network intelligence<br/>Entity centrality + patterns]
    P2_COUNTRY[Country enrichment<br/>Auto-add countries<br/>via iso_code field]
    P2_UPDATE[UPDATE titles<br/>SET gate_keep, entities JSONB<br/>name_en format]

    %% Phase 3: Event Family Generation
    P3_START[PHASE 3: GENERATE EVENT FAMILIES]
    P3_QUEUE[SELECT FROM titles<br/>WHERE gate_keep=true<br/>AND event_family_id IS NULL<br/>AND processing_status NOT IN recycling]
    P3_BUCKET[Semantic clustering<br/>cosine > 0.60 bucketing]
    P3_CLUSTER[Hierarchical merge<br/>cosine > 0.85 threshold]

    P35A_START[P3.5a: SEED VALIDATION]
    P35A_VALIDATE[Individual title validation<br/>Micro-prompts YES/NO per title]
    P35A_FILTER[Filter cluster<br/>Keep only validated titles]
    P35A_SIZE{Cluster >= MIN_SIZE?}
    P35A_REJECT[Mark titles as recycling<br/>processing_status=recycling]

    P3_LLM[LLM incident analysis<br/>DeepSeek generates ALL fields<br/>+ strategic_purpose semantic anchor]
    P3_EF_KEY[Generate ef_key<br/>SHA256 theater + event_type]

    P3_CHECK[Check existing EF<br/>WHERE ef_key=X<br/>AND status IN seed,active<br/>AND parent_ef_id != new.parent_ef_id]
    P3_MERGE[MERGE: Update existing EF<br/>extend source_title_ids]
    P3_CREATE[CREATE: INSERT event_families<br/>ALL fields + status=seed]
    P3_LINK[UPDATE titles<br/>SET event_family_id=ef.id<br/>processing_status=assigned]

    %% Phase 3.5: Intelligence Layer
    P35B_START[P3.5b: CROSS-BATCH ASSIGNMENT]
    P35B_QUEUE[SELECT FROM titles<br/>WHERE gate_keep=true<br/>AND event_family_id IS NULL<br/>AND processing_status NOT IN recycling]
    P35B_MATCH[Find candidate EFs<br/>event_type + theater/actor match]
    P35B_VALIDATE[Micro-prompt validation<br/>strategic_purpose fit check]
    P35B_ASSIGN[UPDATE titles<br/>SET event_family_id, processing_status=assigned]

    P35C_START[P3.5c: INTERPRETIVE MERGING]
    P35C_FIND[Find candidate pairs<br/>same event_type<br/>compatible theaters<br/>EXCLUDE siblings same parent_ef_id]
    P35C_VALIDATE[LLM semantic comparison<br/>strategic_purpose match]
    P35C_MERGE[Merge EF2 into EF1<br/>Mark EF2 as merged]

    P35D_START[P3.5d: INTERPRETIVE SPLITTING]
    P35D_FIND[Find candidates<br/>EFs with >N titles]
    P35D_ANALYZE[LLM narrative analysis<br/>ONE or MULTIPLE narratives?]
    P35D_SPLIT[Split into child EFs<br/>Set parent_ef_id for sibling tracking]
    P35D_MARK[Mark parent EF as split]

    %% Phase 4: Enrichment
    P4_START[PHASE 4: ENRICH EVENT FAMILIES]
    P4_QUEUE[SELECT FROM event_families<br/>WHERE status=seed]
    P4_LLM[LLM enrichment<br/>improve summary, generate tags/context]
    P4_UPDATE[UPDATE event_families<br/>SET summary, tags, ef_context]
    P4_STATUS[UPDATE status=active]

    %% Phase 5: Framed Narratives
    P5_START[PHASE 5: FRAMED NARRATIVES]
    P5_QUEUE[SELECT FROM event_families<br/>WHERE status=active<br/>AND NOT EXISTS framed_narratives]
    P5_FETCH_TITLES[Fetch source titles<br/>JOIN titles ON source_title_ids]
    P5_ANALYZE[Group titles by framing<br/>identify stance patterns]
    P5_LLM[LLM framing analysis<br/>extract distinct framings]
    P5_CREATE[INSERT framed_narratives<br/>frame_description, stance_summary, etc.]

    %% Phase 6: RAI Analysis
    P6_START[PHASE 6: RAI ANALYSIS<br/>MANUAL ONLY]
    P6_QUEUE[SELECT FROM framed_narratives<br/>WHERE rai_analysis IS NULL]
    P6_PAYLOAD[Build payload<br/>EF context + FN framing]
    P6_HTTP[POST to RAI<br/>timeout: 120s, concurrency: 3]
    P6_ANALYZE[RAI LLM analysis<br/>~103s per FN]
    P6_STORE[UPDATE framed_narratives<br/>SET rai_analysis JSONB]

    %% Flow connections
    RSS --> P1_START
    P1_START --> P1_FETCH --> P1_PARSE --> P1_DEDUP --> P1_EMBED --> P1_STORE --> DB

    DB --> P2_START
    DATA_ENTITIES --> P2_START
    TAXONOMY --> P2_START
    NEO4J --> P2_START
    P2_START --> P2_LOAD --> P2_TAXONOMY --> P2_LLM --> P2_NEO4J --> P2_COUNTRY --> P2_UPDATE --> DB

    DB --> P3_START
    EVENT_TYPES --> P3_START
    THEATERS --> P3_START
    P3_START --> P3_QUEUE --> P3_BUCKET --> P3_CLUSTER --> P35A_START
    P35A_START --> P35A_VALIDATE --> P35A_FILTER --> P35A_SIZE
    P35A_SIZE -->|Yes| P3_LLM
    P35A_SIZE -->|No| P35A_REJECT --> DB
    P3_LLM --> P3_EF_KEY --> P3_CHECK
    P3_CHECK -->|Found & Not Sibling| P3_MERGE --> P3_LINK --> DB
    P3_CHECK -->|Not Found| P3_CREATE --> P3_LINK

    DB --> P35B_START
    P35B_START --> P35B_QUEUE --> P35B_MATCH --> P35B_VALIDATE
    P35B_VALIDATE -->|Match| P35B_ASSIGN --> DB
    P35B_VALIDATE -->|No Match| DB

    DB --> P35C_START
    P35C_START --> P35C_FIND --> P35C_VALIDATE
    P35C_VALIDATE -->|Should Merge| P35C_MERGE --> DB
    P35C_VALIDATE -->|Keep Separate| DB

    DB --> P35D_START
    P35D_START --> P35D_FIND --> P35D_ANALYZE
    P35D_ANALYZE -->|Multiple Narratives| P35D_SPLIT --> P35D_MARK --> DB
    P35D_ANALYZE -->|Cohesive| DB

    DB --> P4_START
    P4_START --> P4_QUEUE --> P4_LLM --> P4_UPDATE --> P4_STATUS --> DB

    DB --> P5_START
    P5_START --> P5_QUEUE --> P5_FETCH_TITLES --> P5_ANALYZE --> P5_LLM --> P5_CREATE --> DB

    DB --> P6_START
    P6_START --> P6_QUEUE --> P6_PAYLOAD --> P6_HTTP --> RAI_APP
    RAI_APP --> P6_ANALYZE --> P6_STORE --> DB

    %% Styling
    classDef phaseClass fill:#e1f5ff,stroke:#0288d1,stroke-width:3px
    classDef phase35Class fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    classDef dataSource fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef dbClass fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef keyProcess fill:#e8f5e9,stroke:#388e3c,stroke-width:3px

    class P1_START,P2_START,P3_START,P4_START,P5_START,P6_START phaseClass
    class P35A_START,P35B_START,P35C_START,P35D_START phase35Class
    class RSS,DATA_ENTITIES,TAXONOMY,EVENT_TYPES,THEATERS,RAI_APP dataSource
    class DB,NEO4J dbClass
    class P2_COUNTRY,P3_EF_KEY,P3_CHECK,P3_MERGE,P35A_VALIDATE,P35C_MERGE,P35D_SPLIT keyProcess
```

---

## EF Key System with Sibling Protection

**Critical Design: 2-Parameter Matching + Sibling Exclusion**

```mermaid
flowchart LR
    subgraph "P3 LLM Analysis Output"
        LLM_OUT[title: 'Biden sanctions...'<br/>summary: '...'<br/>strategic_purpose: 'US diplomatic pressure...'<br/>key_actors: Russia, US, Biden<br/>event_type: 'Diplomacy/Negotiations'<br/>primary_theater: 'UKRAINE'<br/>parent_ef_id: NULL]
    end

    subgraph "EF Key Generation"
        EXTRACT[Extract Parameters<br/>theater = 'UKRAINE'<br/>event_type = 'Diplomacy/Negotiations'<br/>actors = IGNORED]
        HASH[SHA256 Hash<br/>UKRAINE + Diplomacy/Negotiations]
        KEY[ef_key = 'a3f8b2c5e7d91a4f'<br/>first 16 chars of hash]
    end

    subgraph "Merge Check with Sibling Protection"
        QUERY[SELECT id, parent_ef_id FROM event_families<br/>WHERE ef_key = 'a3f8b2c5e7d91a4f'<br/>AND status IN seed, active<br/>AND parent_ef_id IS NULL OR parent_ef_id != new.parent_ef_id<br/>LIMIT 1]
        FOUND{Existing EF?}
        SIBLING_CHECK{Same parent?}
        MERGE[UPDATE event_families<br/>SET source_title_ids = array_append...]
        CREATE[INSERT event_families<br/>status = seed, parent_ef_id = ...]
    end

    LLM_OUT --> EXTRACT --> HASH --> KEY --> QUERY --> FOUND
    FOUND -->|Yes| SIBLING_CHECK
    SIBLING_CHECK -->|No - Different Parents| MERGE
    SIBLING_CHECK -->|Yes - Siblings| CREATE
    FOUND -->|No| CREATE
```

**Why Actors Are Ignored:**
- **Problem**: Using actors in ef_key causes fragmentation
- **Solution**: Only use `theater + event_type`
- **Result**: Long-lived saga EFs that absorb related incidents over time

**Sibling Protection:**
- P3.5d splits create child EFs with `parent_ef_id` set
- Siblings share same `parent_ef_id` and will NOT merge together
- Prevents intentionally separated narratives from re-merging
- Allows cross-family merges when semantically appropriate

**Code Reference:** `apps/generate/ef_key.py`, `apps/generate/database.py:246-264`

---

## Phase 3.5: Intelligence Layer (Detailed)

**Post-Mechanical Processing: LLM-Powered Refinement**

```mermaid
flowchart TD
    P3_OUTPUT[Phase 3 Output<br/>Event Families with status=seed]

    subgraph "P3.5a: Seed Validation"
        P35A_GET[Get mechanical clusters<br/>BEFORE EF creation]
        P35A_THEME[Generate brief theme<br/>from top 3 entities]
        P35A_VAL[Validate each title individually<br/>Micro-prompt: Does title fit theme?]
        P35A_SIZE{>= MIN_CLUSTER_SIZE<br/>validated titles?}
        P35A_CREATE[Proceed to EF creation]
        P35A_RECYCLE[Send to recycling bin<br/>processing_status=recycling]
    end

    subgraph "P3.5b: Cross-Batch Assignment"
        P35B_GET[Get unassigned titles<br/>gate_keep=true, ef_id IS NULL]
        P35B_FIND[Find candidate EFs<br/>event_type match<br/>+ theater OR 50%+ actor overlap]
        P35B_PROMPT[Micro-prompt per candidate<br/>Does title fit strategic_purpose?]
        P35B_ASSIGN[Assign to best-fit EF<br/>or leave for new seed]
    end

    subgraph "P3.5c: Interpretive Merging"
        P35C_PAIRS[Find EF pairs<br/>same event_type<br/>compatible theaters<br/>EXCLUDE same parent_ef_id]
        P35C_PROMPT[Micro-prompt comparison<br/>Same broader narrative?]
        P35C_MERGE[Merge EF2 into EF1<br/>Mark EF2 as merged]
    end

    subgraph "P3.5d: Interpretive Splitting"
        P35D_FIND[Find EFs with >N titles]
        P35D_PROMPT[LLM analysis<br/>ONE or MULTIPLE narratives?]
        P35D_SPLIT[Split into child EFs<br/>Set parent_ef_id on children]
        P35D_ACTORS[LLM assigns key_actors<br/>per narrative]
        P35D_PARENT[Mark parent EF as split]
    end

    P3_OUTPUT --> P35A_GET
    P35A_GET --> P35A_THEME --> P35A_VAL --> P35A_SIZE
    P35A_SIZE -->|Yes| P35A_CREATE
    P35A_SIZE -->|No| P35A_RECYCLE

    P35A_CREATE --> P35B_GET
    P35B_GET --> P35B_FIND --> P35B_PROMPT --> P35B_ASSIGN

    P35B_ASSIGN --> P35C_PAIRS
    P35C_PAIRS --> P35C_PROMPT --> P35C_MERGE

    P35C_MERGE --> P35D_FIND
    P35D_FIND --> P35D_PROMPT --> P35D_SPLIT --> P35D_ACTORS --> P35D_PARENT
```

**Key Features:**

- **P3.5a (Seed Validation)**: Prevents noise from entering EFs via individual title validation
- **P3.5b (Cross-Batch Assignment)**: Continuously assigns new titles to existing EFs using strategic_purpose
- **P3.5c (Interpretive Merging)**: Merges semantically similar EFs beyond mechanical ef_key matching
- **P3.5d (Interpretive Splitting)**: Splits mixed-narrative EFs into coherent sub-narratives with sibling tracking

**Micro-Prompts:**
- Temperature: 0.0
- Max tokens: 10 (YES/NO only)
- Fast, cheap validation without explanation

**Strategic Purpose:**
- One-sentence semantic anchor generated by Phase 3 LLM
- Used across all Phase 3.5 components for thematic validation
- Enables consistent intelligence operations

**Code References:**
- `apps/generate/seed_validator.py` - P3.5a implementation
- `apps/generate/thematic_validator.py` - P3.5b implementation
- `apps/generate/ef_merger.py` - P3.5c implementation
- `apps/generate/ef_splitter.py` - P3.5d implementation
- `apps/generate/p35_pipeline.py` - Complete orchestration

---

## Database Schema

```mermaid
erDiagram
    titles ||--o{ event_families : "event_family_id"
    event_families ||--o{ framed_narratives : "event_family_id"
    event_families ||--o| event_families : "parent_ef_id"
    event_families ||--o| event_families : "merged_into"

    titles {
        uuid id PK
        text title_display
        text url_gnews UK
        boolean gate_keep "NULL→true/false in P2"
        uuid event_family_id FK "NULL→uuid in P3"
        text processing_status "NULL/pending/assigned/recycling"
        vector embedding_384
        jsonb entities "P2: name_en format + auto-country"
        timestamp pubdate_utc
        text gate_reason
        real gate_score
    }

    event_families {
        uuid id PK
        text title "Generated P3"
        text summary "Generated P3, enriched P4"
        text strategic_purpose "P3: Semantic anchor for P3.5"
        jsonb key_actors "Generated P3"
        text event_type "Generated P3"
        text primary_theater "Generated P3"
        text ef_key UK "SHA256 theater|type"
        enum status "seed/active/merged/split/archived"
        uuid parent_ef_id FK "P3.5d: Split sibling tracking"
        uuid merged_into FK "P3.5c: If merged to another EF"
        text merge_rationale "P3.5c: Why merged"
        jsonb source_title_ids "Array of title UUIDs"
        jsonb tags "Added P4"
        jsonb ef_context "Added P4"
        jsonb events "Timeline array"
        text coherence_reason "Why titles form coherent event"
        text processing_notes "Pipeline processing history"
        timestamp created_at
        timestamp updated_at
    }

    framed_narratives {
        uuid id PK
        uuid event_family_id FK
        text frame_description "Generated P5"
        text stance_summary "Generated P5"
        jsonb supporting_headlines "Generated P5"
        jsonb supporting_title_ids "Generated P5"
        real prevalence_score "Generated P5"
        jsonb rai_analysis "Added P6, NULL before"
        timestamp created_at
    }
```

**Key Schema Changes (v2.1):**
- `titles.processing_status`: Tracks title lifecycle (pending/assigned/recycling)
- `event_families.strategic_purpose`: Semantic anchor for Phase 3.5
- `event_families.parent_ef_id`: Sibling tracking for P3.5d splits
- `event_families.status`: Now includes 'split' for parent EFs
- Removed: `confidence_score` (unused)

---

## Status Flow

```mermaid
stateDiagram-v2
    [*] --> pending: P1 ingests to titles

    state "titles.gate_keep" as gate {
        pending --> true: P2 strategic accept
        pending --> false: P2 strategic reject
    }

    state "titles.processing_status" as proc {
        true --> pending: Awaiting P3
        pending --> recycling: P3.5a rejects
        pending --> assigned: P3 or P3.5b assigns
    }

    state "event_families.status" as ef_status {
        [*] --> seed: P3 creates or merges
        seed --> active: P4 enriches
        seed --> merged: P3.5c merges into another
        seed --> split: P3.5d splits into children
        active --> merged: P3.5c merges into another
        active --> split: P3.5d splits into children
        active --> archived: Manual archive
    }

    state "framed_narratives" as fn {
        active --> fn_created: P5 analyzes
        fn_created --> fn_analyzed: P6 adds RAI manual
    }
```

**Key State Transitions:**

1. **titles.gate_keep**: `NULL` (P1) → `true` (P2 accept) / `false` (P2 reject)
2. **titles.processing_status**: `NULL` → `pending` → `assigned` (P3/P3.5b) / `recycling` (P3.5a)
3. **event_families.status**: `seed` (P3) → `active` (P4) / `merged` (P3.5c) / `split` (P3.5d) → `archived` (manual)
4. **framed_narratives.rai_analysis**: `NULL` (P5 creates) → `<jsonb>` (P6 manual analysis)

---

## Key Queries

### P1 → P2 Queue
```sql
SELECT * FROM titles
WHERE entities IS NULL
ORDER BY pubdate_utc DESC
```

### P2 → P3 Queue
```sql
SELECT * FROM titles
WHERE gate_keep = true
AND event_family_id IS NULL
AND processing_status NOT IN ('recycling')
ORDER BY pubdate_utc DESC
```

### P3 EF Merge Check (with Sibling Protection)
```sql
SELECT id, parent_ef_id, source_title_ids FROM event_families
WHERE ef_key = :ef_key
AND status IN ('seed', 'active')
AND (parent_ef_id IS NULL OR parent_ef_id != :new_parent_ef_id OR :new_parent_ef_id IS NULL)
LIMIT 1
```

### P3 Title Assignment
```sql
UPDATE titles
SET event_family_id = :ef_id,
    processing_status = 'assigned'
WHERE id = ANY(:title_ids)
```

### P3.5a Recycling Bin
```sql
UPDATE titles
SET processing_status = 'recycling'
WHERE id = ANY(:rejected_title_ids)
```

### P3.5b Cross-Batch Queue
```sql
SELECT * FROM titles
WHERE gate_keep = true
AND event_family_id IS NULL
AND processing_status NOT IN ('recycling', 'assigned')
ORDER BY pubdate_utc DESC
```

### P3.5c Merge Candidates (Exclude Siblings)
```sql
SELECT ef1.id, ef2.id, ef1.strategic_purpose, ef2.strategic_purpose
FROM event_families ef1, event_families ef2
WHERE ef1.event_type = ef2.event_type
AND ef1.status IN ('seed', 'active')
AND ef2.status IN ('seed', 'active')
AND ef1.id < ef2.id
AND (ef1.parent_ef_id IS NULL OR ef2.parent_ef_id IS NULL OR ef1.parent_ef_id != ef2.parent_ef_id)
```

### P3.5d Split Candidates
```sql
SELECT * FROM event_families
WHERE status IN ('seed', 'active')
AND ARRAY_LENGTH(source_title_ids, 1) > :min_titles_for_split
ORDER BY ARRAY_LENGTH(source_title_ids, 1) DESC
```

### P4 → P5 Queue
```sql
SELECT * FROM event_families
WHERE status = 'seed'
ORDER BY created_at ASC
```

---

## Critical Configuration

```yaml
# Clustering Thresholds
COSINE_THRESHOLD_DEDUP: 0.95   # P1: Near-duplicate detection
COSINE_THRESHOLD_BUCKET: 0.60  # P3: Initial bucketing
COSINE_THRESHOLD_MERGE: 0.85   # P3: Hierarchical merge

# Phase 2: Strategic Filtering
P2_TAXONOMY_SOURCE: database    # data_entities + taxonomy_terms
P2_ENTITY_FORMAT: name_en       # Use full names (not entity_id codes)
P2_COUNTRY_ENRICHMENT: true     # Auto-add countries via iso_code
P2_NEO4J_OVERRIDE: enabled      # Network intelligence
P2_STRATEGIC_SCORE_MIN: 2       # Neo4j multi-signal threshold

# Phase 3: EF Generation
EF_KEY_ALGORITHM: SHA256        # Hash function
EF_KEY_LENGTH: 16              # First 16 chars of hash
EF_KEY_PARAMS: "theater|type"  # actors IGNORED

# Phase 3.5: Intelligence Layer
P35A_ENABLED: true             # Seed validation
P35A_MIN_CLUSTER_SIZE: 3       # Minimum validated titles
P35A_VALIDATION_TEMPERATURE: 0.0
P35A_VALIDATION_MAX_TOKENS: 10

P35B_ENABLED: true             # Cross-batch assignment
P35B_ASSIGNMENT_TEMPERATURE: 0.0
P35B_ASSIGNMENT_MAX_TOKENS: 10

P35C_ENABLED: true             # Interpretive merging
P35C_MERGE_TEMPERATURE: 0.0
P35C_MERGE_MAX_TOKENS: 10
P35C_MAX_PAIRS_PER_CYCLE: 20

P35D_ENABLED: true             # Interpretive splitting
P35D_MIN_TITLES_FOR_SPLIT: 3
P35D_SPLIT_TEMPERATURE: 0.3
P35D_SPLIT_MAX_TOKENS: 4000
P35D_MAX_EFS_PER_CYCLE: 50

# Phase Enables
PHASE_4_ENRICHMENT_ENABLED: true
PHASE_5_FRAMING_ENABLED: true
PHASE_6_RAI_ENABLED: false     # Manual only

# LLM Provider
LLM_PROVIDER: deepseek
LLM_MODEL: deepseek-chat
DEEPSEEK_API_URL: https://api.deepseek.com/v1

# RAI Integration
RAI_API_URL: https://rai-backend-ldy4.onrender.com/api/v1/analyze
RAI_TIMEOUT_SECONDS: 120
PHASE_6_CONCURRENCY: 3
```

---

## Code References

### Phase 2: Strategic Filtering
- `apps/filter/entity_enrichment.py` - Main orchestration
- `apps/filter/taxonomy_extractor.py` - Static GO/STOP matching
- `apps/filter/country_enrichment.py` - Auto-country via iso_code
- `apps/filter/vocab_loader_db.py` - Database vocabulary loader
- `core/neo4j_sync.py` - Network intelligence

### Phase 3: EF Generation
- `apps/generate/ef_key.py` - ef_key generation (theater + type)
- `apps/generate/database.py` - EF upsert with sibling protection
- `apps/generate/incident_processor.py` - Incident clustering & processing
- `apps/generate/reduce_assembler.py` - REDUCE phase EF assembly
- `apps/generate/theater_inference.py` - Mechanical theater inference

### Phase 3.5: Intelligence Layer
- `apps/generate/seed_validator.py` - P3.5a: Individual title validation
- `apps/generate/thematic_validator.py` - P3.5b: Cross-batch assignment
- `apps/generate/ef_merger.py` - P3.5c: Interpretive EF merging
- `apps/generate/ef_splitter.py` - P3.5d: Interpretive EF splitting
- `apps/generate/p35_pipeline.py` - Complete P3.5 orchestration

### Phase 4-6
- `apps/enrich/processor.py` - P4: EF enrichment
- `apps/generate/framing_processor.py` - P5: Framed narratives
- `apps/generate/rai_processor.py` - P6: RAI analysis (manual)

### Core Infrastructure
- `core/config.py` - All Phase 3.5 configuration
- `core/database.py` - Database session management
- `core/llm_client.py` - DeepSeek LLM integration

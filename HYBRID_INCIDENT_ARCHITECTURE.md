# Hybrid Incident-First Architecture

**Strategic Narrative Intelligence (SNI) Event Family Generation System**

## Overview

The SNI system has evolved from an "event-first" to an "incident-first" architecture, solving the critical EF fragmentation problem while ensuring 100% strategic title coverage.

## Problem Solved: EF Fragmentation

**Before (Event-First):**
- Poland drone incident → 5 headlines → 3 separate EFs (fragmented)
- Lost siblings across batches → no reunification
- Early signals → missed or ignored
- 42% strategic titles unclustered

**After (Incident-First + Hybrid):**
- Poland drone incident → 5 headlines → 1 EF (clustered)
- Cross-batch merging via ef_key → siblings reunite
- Single-title EF seeds → early signals preserved
- 100% strategic coverage

## Architecture Components

### 1. Incident Processor (`incident_processor.py`)
**Primary pipeline:** Incident clustering → Analysis → Database upsert

**Pipeline Flow:**
```
Unassigned Strategic Titles
           ↓
      MAP Phase: Incident Clustering
      ├─ Multi-title incidents → Incident clusters
      ├─ Single-title incidents → Individual clusters
      └─ Orphaned titles → Detected for Step 3.5
           ↓
      REDUCE Phase: Incident Analysis
      ├─ Cluster analysis → (theater, event_type, EF content)
      ├─ ef_key generation → For cross-batch merging
      └─ Event timeline extraction
           ↓
      Step 3.5: Orphaned Title Processing
      ├─ Single-title clusters → Same REDUCE pipeline
      └─ ef_key generation → For future merging
           ↓
      Database Upsert
      ├─ ef_key matching → Merge with existing EFs
      └─ Title assignment → Strategic coverage
```

### 2. MAP Phase (`map_classifier.py`)
**Semantic incident clustering using LLM analysis**

```python
async def process_incidents_parallel(titles: List[Dict]) -> List[IncidentCluster]:
    # Batch titles (100 per batch)
    # LLM identifies strategic incidents
    # Returns clustered + orphaned titles
```

**Key Features:**
- Temporal proximity (48-hour windows)
- Causal relationships (action → reaction → consequence)
- Strategic coherence (unified narrative threads)
- Cross-border incident handling

### 3. REDUCE Phase (`reduce_assembler.py`)
**Incident analysis and EF generation**

```python
async def analyze_incident_cluster(cluster: IncidentCluster) -> IncidentAnalysis:
    # LLM analyzes cluster → theater + event_type
    # Generates EF content (title, summary, events timeline)
    # ef_key = hash(theater + event_type) → For merging
```

**Handles both:**
- Multi-title incident clusters (coherent strategic incidents)
- Single-title clusters (orphaned strategic content)

### 4. Hybrid Processing Logic

**Step 1:** Process multi-title incidents via clustering
**Step 2:** Detect orphaned strategic titles
**Step 3:** Generate single-title EF seeds for orphans
**Step 4:** ef_key merging reunites lost siblings across batches

## Data Models

### IncidentCluster
```python
class IncidentCluster(BaseModel):
    incident_name: str           # "Charlie Kirk Assassination and Aftermath"
    title_ids: List[str]         # ["id1", "id2", "id3"...]
    rationale: str               # Why these belong together
```

### IncidentAnalysis
```python
class IncidentAnalysis(BaseModel):
    primary_theater: str         # "US_DOMESTIC"
    event_type: str             # "Domestic Politics"
    ef_title: str               # Strategic EF title (≤120 chars)
    ef_summary: str             # Strategic context (≤280 chars)
    events: List[Dict]          # Chronological timeline
```

## Prompting Strategy

### MAP Phase: Incident Clustering
```
INCIDENT_CLUSTERING_SYSTEM_PROMPT = """
Identify which titles describe the same strategic incident:

1. SAME CORE INCIDENT: Initial event + reactions + consequences
2. TEMPORAL PROXIMITY: Events within 48 hours causally connected
3. STRATEGIC COHERENCE: Actions forming one strategic narrative
```

### REDUCE Phase: Incident Analysis
```
INCIDENT_ANALYSIS_SYSTEM_PROMPT = """
Analyze this strategic incident cluster:

1. PRIMARY_THEATER: Main geographic/thematic theater
2. EVENT_TYPE: Primary classification category
3. EF_CONTENT: Title, summary, chronological events timeline
```

## Database Integration

### ef_key Generation
```python
def generate_ef_key(actors: List[str], theater: str, event_type: str) -> str:
    key_string = f"{theater}|{event_type}"
    return hashlib.sha256(key_string.encode()).hexdigest()[:16]
```

### Cross-Batch Merging
```sql
SELECT id FROM event_families
WHERE ef_key = ? AND status IN ('seed', 'active')
LIMIT 1
```

**If match found:** Merge title_ids, extend timespan, update processing_notes
**If no match:** Create new EF with ef_key for future merging

## Success Metrics

**From 50-title test:**
- ✅ 16 incident clusters (multi-title + single-title from clustering)
- ✅ 4 orphaned titles → single-title EF seeds
- ✅ 20 total EFs (100% strategic coverage)
- ✅ Cross-batch merging: Poland + Ukraine incidents merged via ef_key `7d8e3b755fe4342e`

## Benefits Achieved

1. **No EF Fragmentation:** Related events stay together
2. **Lost Sibling Reunification:** Cross-batch ef_key merging
3. **Early Signal Preservation:** Single-title EF seeds for future epic events
4. **100% Strategic Coverage:** Every strategic title becomes an EF
5. **Scalable Architecture:** Ready for 7,500 title backlog processing

## Next Phase: Intelligent EF Enrichment

**Concept:** LLM mini-research to add strategic context
- Background research on key actors
- Historical precedent analysis
- Strategic implications assessment
- Regional impact evaluation

**Goal:** Transform basic EF seeds into comprehensive strategic intelligence products.
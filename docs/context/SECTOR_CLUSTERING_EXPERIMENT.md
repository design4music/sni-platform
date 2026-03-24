# Sector-Based Clustering Experiment

**Branch**: `feat/sector-clustering`
**Last Updated**: 2026-03-21
**Status**: In progress -- France/March written, event titles not yet generated

---

## Motivation

The Iran war spike (4-5x daily ingestion) exposed clustering fragility. The existing Phase 4
incremental clustering (`incremental_clustering.py`) uses anchor signals (persons, orgs, places)
to group titles within track buckets. Under volume spikes, generic signals like "Iran" or "Hormuz"
pull hundreds of unrelated titles into mega-events (2K+ titles on a single event).

Root cause: clustering happens per-track, per-bucket, using raw signal overlap. There is no
semantic grouping by topic before identity-based splitting.

## New Approach: Sector + Subject + Identity

### Phase 3.1 Taxonomy Extension

Added two new fields to `title_labels`:
- **SECTOR** (11 values): MILITARY, INTELLIGENCE, SECURITY, DIPLOMACY, GOVERNANCE, ECONOMY,
  ENERGY_RESOURCES, TECHNOLOGY, HEALTH_ENVIRONMENT, SOCIETY, INFRASTRUCTURE
- **SUBJECT** (controlled vocab per sector): e.g., MILITARY/NUCLEAR, ECONOMY/TRADE,
  GOVERNANCE/ELECTION, SOCIETY/MEDIA_PRESS

DB columns: `title_labels.sector TEXT`, `title_labels.subject TEXT`
(Added in previous session, already populated for France/March.)

### Clustering Algorithm (`cluster_topdown` in `rebuild_centroid.py`)

1. **Group by sector+subject** -- creates topic groups (e.g., all MILITARY/NUCLEAR titles)
2. **Split by identity signals** -- within each topic group, split by persons/orgs/places/named_events
3. **Merge orphans** -- titles with no identity signals merge into the largest sub-cluster
4. Groups with <= 3 titles stay as single clusters (no splitting)

### Track Assignment (mechanical, not LLM)

Replaces Phase 3.3 per-title LLM track assignment with a static mapping:

```
SECTOR_TO_TRACK = {
    MILITARY, INTELLIGENCE, SECURITY -> geo_security
    DIPLOMACY, GOVERNANCE            -> geo_politics
    ECONOMY, TECHNOLOGY, INFRASTRUCTURE -> geo_economy
    ENERGY_RESOURCES                  -> geo_energy
    HEALTH_ENVIRONMENT, SOCIETY       -> geo_humanitarian
    UNKNOWN                           -> geo_politics (fallback)
}
```

Track is assigned per-cluster, not per-title. `title_assignments` table is bypassed entirely.

### Geo Tagging (domestic vs bilateral)

Each cluster is tagged by counting foreign centroids across its titles.
**Threshold: 50%** -- the top foreign centroid must appear in >= 50% of cluster titles to be
tagged bilateral. Below that, the cluster is domestic. This prevents noise (e.g., 2/119 titles
mentioning Levant) from flipping a French election cluster to bilateral.

### Key Architectural Change

The old pipeline: title -> track assignment (LLM) -> CTM -> cluster within CTM
The new pipeline: title -> cluster ALL centroid/month titles -> assign clusters to CTMs mechanically

This means:
- **title_assignments is not used** for loading or routing
- **All titles with the centroid in centroid_ids** are included, not just those with a
  title_assignments row (this caught 242 previously-orphaned titles)
- CTMs still exist as the storage unit; clusters route to them via SECTOR_TO_TRACK

---

## Experiment: France / March 2026

### Test Harness

`pipeline/phase_4/rebuild_centroid.py` -- temporary script, not a pipeline replacement.

```bash
# Dry run (inspect clusters, no DB writes)
python -m pipeline.phase_4.rebuild_centroid --centroid EUROPE-FRANCE --month 2026-03-01

# Write clusters to DB
python -m pipeline.phase_4.rebuild_centroid --centroid EUROPE-FRANCE --month 2026-03-01 --write

# Write + generate event titles/summaries
python -m pipeline.phase_4.rebuild_centroid --centroid EUROPE-FRANCE --month 2026-03-01 --write --titles
```

### Data Source Fix (this session)

The original `load_all_titles()` joined `title_assignments` to find titles. Changed to query
`titles_v3` directly by `centroid_ids` array + `processing_status = 'assigned'` + month filter.

This revealed **242 orphaned titles** -- they had `EUROPE-FRANCE` in `centroid_ids` and
`processing_status = 'assigned'`, but no row in `title_assignments` at all. The old Phase 3.3
marked them assigned but never created the assignment. These titles also had NULL sector
(labeled by old Phase 3.1 which set domain but not sector).

**Fix**: Ran targeted label extraction on all 264 NULL-sector titles. Result: 263/264 got sector.
Coverage went from 81% to 99%.

### Results (after write, 2026-03-21)

| Metric | Value |
|--------|-------|
| Total titles loaded | 1404 |
| Sector coverage | 99% (1403/1404) |
| Emerged clusters | 146 |
| Catchall (single-title) | 285 (20%) |
| Total events written | 431 |
| Largest cluster | 119 (GOVERNANCE/ELECTION, domestic) |

**Per-track distribution:**

| Track | Events | Emerged | Max size |
|-------|--------|---------|----------|
| geo_politics | 99 | 36 | 119 |
| geo_humanitarian | 148 | 43 | 52 |
| geo_security | 104 | 37 | 75 |
| geo_economy | 57 | 21 | 42 |
| geo_energy | 23 | 9 | 40 |
| geo_information | 0 | 0 | 0 |

**Top clusters:**

| Size | Sector/Subject | Track | Geo | Sample |
|------|---------------|-------|-----|--------|
| 119 | GOVERNANCE/ELECTION | geo_politics | domestic | Paris municipal elections |
| 75 | MILITARY/NUCLEAR | geo_security | domestic | Franco-German nuclear deterrence |
| 53 | MILITARY/NAVAL | geo_security | domestic | Aircraft carrier deployments |
| 53 | DIPLOMACY/NULL | geo_politics | domestic | Trump/Macron diplomacy |
| 52 | SOCIETY/NULL | geo_humanitarian | domestic | Ligue 1 / sports |
| 42 | ECONOMY/TRADE | geo_economy | bilateral USA | Paris trade talks |
| 40 | ENERGY_RESOURCES/OIL_GAS | geo_energy | domestic | Hormuz/oil impacts |
| 25 | DIPLOMACY/MEDIATION | geo_politics | bilateral Levant | Macron/Netanyahu |
| 23 | DIPLOMACY/ALLIANCE | geo_politics | bilateral EUROPE-SOUTH | Macron/Mitsotakis Cyprus |

---

## Known Issues (to review before --titles)

### 1. geo_information CTM gets 0 events
No sector maps to `geo_information`. All titles fall back to other tracks.
**Decision needed**: Drop this CTM from the sector model? Or map a sector to it?

### 2. SOCIETY/NULL is a grab-bag (52 titles in one cluster)
Sports (Ligue 1, rugby) and social issues mix under SOCIETY with NULL subject.
The identity splitting separates them somewhat, but the topic group is too broad.
**Possible fix**: Better subject extraction for SOCIETY -- SPORTS, RELIGION, etc.

### 3. Large domestic clusters may need sub-splitting
The 119-title election cluster covers the entire Paris municipal election cycle.
It could benefit from temporal splitting (round 1 vs round 2) or candidate splitting.
**Not urgent**: 119 is manageable, not a mega-event.

### 4. AIR FRANCE normalizing to FRANCE
`normalize_signals.py` merges "AIR FRANCE" and "AIR FRANCE-KLM" into "FRANCE" (the country).
This is a signal normalization bug that could cause false cluster merges.

### 5. "Coupe de France" normalizing to "Tour de France"
Same normalization issue -- sports events getting merged into unrelated named_events.

### 6. Event titles not yet generated
Clusters are written but events have no `title` or `summary`. Need `--titles` run.

### 7. 1 title still has NULL sector
264 extracted, 263 got sector. 1 title (`MEDIA_PRESS` returned as sector, which is a subject
not a sector) remains NULL. Negligible.

---

## Pending (NOT this experiment)

- **Track consolidation 6->4** (Politics, Security, Economy, Society) -- separate task
- **Pipeline modernization** -- replace `incremental_clustering.py` with sector-based approach
  after experiment confirms quality
- **title_assignments refactoring** -- the new system doesn't use it, but the old pipeline still does
- **Signal normalization fixes** -- AIR FRANCE, Coupe de France (items 4-5 above)
- **UNKNOWN sector handling** -- 1 remaining title; for pipeline integration, need a strategy
  for titles where LLM can't determine sector

---

## Files

| File | Role |
|------|------|
| `pipeline/phase_4/rebuild_centroid.py` | Test harness (this experiment) |
| `pipeline/phase_4/extract_concurrent.py` | Label extraction (used for bulk runs) |
| `pipeline/phase_3_1/extract_labels.py` | Core extraction functions (sector/subject added) |
| `pipeline/phase_4/normalize_signals.py` | Signal normalization (has bugs, see #4-5) |
| `core/config.py` | HIGH_FREQ_ORGS exclusion list |

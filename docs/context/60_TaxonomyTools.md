# Taxonomy Tools Documentation

## Overview

The taxonomy tools suite provides automated analysis and maintenance capabilities for the v3 taxonomy system. All tools produce **reports only** (no automatic DB writes) and are designed for daily pipeline integration.

**Location**: `v3/taxonomy_tools/`

---

## Tool Suite

### 1. Profile Alias Coverage (`profile_alias_coverage.py`)

**Purpose**: Measure alias effectiveness per centroid/language

**Usage**:
```bash
python profile_alias_coverage.py --centroid-id SYS-TECH
python profile_alias_coverage.py --language ar
```

**Output**:
- `out/taxonomy_profile/centroid_<id>__lang_<lang>__alias_stats.json` - per-alias match counts
- `out/taxonomy_profile/centroid_<id>__lang_<lang>__summary.json` - coverage metrics

**Key Features**:
- Analyzes current corpus coverage (not future-predictive)
- Uses Phase 2 normalization exactly (no divergence)
- Shows which aliases are actively matching vs. unused

---

### 2. Prune Redundant Aliases (`prune_aliases.py`)

**Purpose**: Remove aliases subsumed by other aliases using static subsumption analysis

**Usage**:
```bash
# Dry-run (review before applying)
python prune_aliases.py --centroid-id SYS-MEDIA --mode dry-run

# Apply changes
python prune_aliases.py --mode apply
```

**Algorithm**: Static subsumption (token-based)
- Alias A subsumes alias B if tokens(A) ⊂ tokens(B)
- Example: "AI" subsumes "AI infrastructure"
- Never removes based on zero current matches (taxonomy is forward-looking)

**Safety**:
- Dry-run by default
- Only JSONB alias edits (no row deletions)
- Safety threshold: aborts if >2000 removals per group
- Min-keep constraint: preserves at least 1 alias per centroid+language

**Scope**: Within (centroid_id, language) groups only

**Output**: `out/taxonomy_prune/<timestamp>/prune_report.json`

**Results** (2026-01-05):
- 588 groups processed
- 836 aliases removed (6.5%)
- 12,077 aliases kept (93.5%)

---

### 3. Export Taxonomy Snapshot (`export_taxonomy_snapshot.py`)

**Purpose**: Create safety backups for rollback and git diffing

**Usage**:
```bash
python export_taxonomy_snapshot.py
python export_taxonomy_snapshot.py --centroid-id SYS-TECH
```

**Output**: `out/taxonomy_snapshots/taxonomy_<filter>_<timestamp>.json`

**Use Cases**:
- Pre-pruning safety backup
- Git diff tracking of taxonomy changes
- Manual rollback capability

---

### 4. Restore Taxonomy Snapshot (`restore_taxonomy_snapshot.py`)

**Purpose**: Rollback to a previous taxonomy state

**Usage**:
```bash
# Dry-run
python restore_taxonomy_snapshot.py --snapshot out/taxonomy_snapshots/taxonomy_full_20260105_150214.json --mode dry-run

# Apply
python restore_taxonomy_snapshot.py --snapshot out/taxonomy_snapshots/taxonomy_full_20260105_150214.json --mode apply
```

**Safety**: Never deletes items not in snapshot

---

### 5. NameBombs Detector (`namebombs.py`)

**Purpose**: Detect emerging proper names (people/orgs/places) leaking into out-of-scope

**Supported Languages**: EN, FR, ES, RU

**Usage**:
```bash
python namebombs.py --since-hours 24
```

**Extraction Logic**:
- Multi-word TitleCase phrases (2-4 words): "John Doe", "European Union"
- Acronyms (2-6 uppercase letters): "NATO", "IMF", "UN"
- Russian: Both Cyrillic and Latin acronyms

**Filters**:
- Must appear ≥ min_total_support times (default: 5 for EN, 3 for others)
- Must leak into OOS ≥ min_oos_support times (default: 1)
- Not already in taxonomy aliases
- Not month/day boilerplate

**Output**: `out/oos_reports/namebombs_<lang>_<timestamp>.json`

**Ranking**: By total support DESC, then OOS support DESC

**Example Result** (2026-01-05):
- 675 EN titles analyzed
- 1 candidate: "New Year" (13 total, 4 OOS)

---

### 6. OOS Keyword Candidates (`oos_keyword_candidates.py`)

**Purpose**: Detect general keywords/noun phrases (not proper names) leaking into OOS

**Language**: EN only

**Usage**:
```bash
python oos_keyword_candidates.py --since-hours 24
python oos_keyword_candidates.py --min-total-support 2 --min-oos-support 1 --top 100
```

**Extraction Logic**:
- N-grams: unigrams + bigrams
- Tokenization: Phase 2 normalization + apostrophe removal
- Filters out: proper names, stopwords, headline boilerplate

**Stopword Categories**:
- Common stopwords (the, and, of, etc.)
- News boilerplate (says, reported, breaking, etc.)
- Temporal/ordinal (first, second, next, last, new)
- Generic qualifiers (major, big, top, key)
- Scope words (global, international, world)
- Content types (opinion, analysis, editorial)
- Headline glue (here's, why, how, what)
- Low-value verbs (take, make, get)

**Bigram Preference**: Only outputs unigrams if OOS support ≥ 5 (reduces noise)

**Output**: `out/oos_reports/oos_candidates_en_<timestamp>.json`

**Ranking**: By OOS leakage DESC (prioritizes actual gaps)

**Example Results** (2026-01-06, min_support=2):
- 31 bigram candidates
- "fraud scandal", "fire victims", "child care", "investor appetite"

---

## Common Utilities (`common.py`)

Shared functions across all tools:

**Normalization** (extracted from Phase 2):
- `normalize_text()` - canonical normalization
- `normalize_title()` / `normalize_alias()` - aliases for clarity
- `tokenize_text()` - Phase 2 tokenization with possessive/compound handling
- `strip_diacritics()` - Unicode diacritic removal

**Matching**:
- `title_matches_alias()` - Phase 2 matching semantics

**Database**:
- `get_db_connection()` - reuses core/config.py

**Constants**:
- `SUPPORTED_LANGUAGES = ["ar", "en", "de", "fr", "es", "ru", "zh", "ja", "hi"]`

---

## Operational Workflow

### Safe Pruning Workflow

```bash
# 1. Snapshot
python export_taxonomy_snapshot.py

# 2. Dry-run
python prune_aliases.py --mode dry-run

# 3. Review report
cat out/taxonomy_prune/<timestamp>/prune_report.json

# 4. Apply
python prune_aliases.py --mode apply

# 5. Rollback if needed
python restore_taxonomy_snapshot.py --snapshot out/taxonomy_snapshots/taxonomy_full_<timestamp>.json --mode apply
```

### Daily Pipeline Integration

After Phase 2 completes:

```bash
# Detect emerging names
python namebombs.py --since-hours 24

# Detect keyword gaps
python oos_keyword_candidates.py --since-hours 24

# Review reports manually
ls -lh out/oos_reports/
```

---

## Design Principles

1. **Reports Only**: No automatic DB writes (human approval required)
2. **Phase 2 Fidelity**: All normalization reuses Phase 2 logic exactly
3. **Minimal Complexity**: Simple, deterministic algorithms
4. **Safety First**: Dry-run defaults, safety thresholds, rollback capability
5. **Auditability**: JSON reports with examples and metadata

---

## Output Directories

All tools write to `out/` (git-ignored):

```
out/
├── taxonomy_profile/       # Coverage analysis
├── taxonomy_prune/         # Pruning reports
├── taxonomy_snapshots/     # Safety backups
└── oos_reports/            # NameBombs + keyword candidates
```

---

## Future Enhancements (Not Implemented)

From original specs but deferred:

- **Candidate Mining** (`suggest_candidates.py`) - Extract n-grams from unmatched assigned titles
- **Cross-Centroid Overlap Detection** - Flag aliases appearing in multiple centroids
- **Multi-language OOS Keywords** - Extend beyond EN-only

---

## Related Documentation

- Specs: `v3/context/taxonomy compiler spec.txt`
- Specs: `v3/context/NameBombs.txt`
- Specs: `v3/context/OOS Keyword Candidates.txt`
- Phase 2 Matching: `v3/phase_2/match_centroids.py`
- Decision Log: `v3/context/30_DecisionLog.yml` (D-006: Accumulative matching)

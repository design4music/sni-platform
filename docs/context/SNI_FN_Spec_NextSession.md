# Friction Nodes Taxonomy & Narratives — Next Session Specification

## Executive Summary

This session completed Phase 1 & 2 of the Friction Nodes (FN) system: taxonomy bundle generation and event bootstrapping across 113 atomic FNs globally. The next session focuses on frontend visualization, narrative generation, and FN content enrichment.

---

## Project Background: Friction Nodes Architecture

### What Are Friction Nodes?

Friction Nodes represent geopolitical conflict zones, tensions, and strategic competitions. The system uses a three-level hierarchy:

- **Theaters**: 30 regional conflict zones (e.g., `ukraine_war_theater`, `australia_china_theater`)
- **Atomic FNs**: 110+ specific friction points within theaters (e.g., `ukraine_battlefield`, `western_aid_to_ukraine`)
- **Centroids**: 114 geographic reference points (EUROPE-UKRAINE, ASIA-CHINA, etc.)

### Core Data Model

1. **friction_nodes** table: Theater and atomic FN metadata
2. **taxonomy_v3** (fn_anchor): Multilingual keyword bundles (10 languages: EN, AR, DE, ES, FR, HI, IT, JA, RU, ZH)
3. **event_friction_nodes**: Links events to FNs via keyword + centroid matching
4. **title_narratives**: Links titles to narrative framings (pro/con perspectives)
5. **narratives_v2**: Editorial framings with publisher cohorts and framing keywords

### Matching Pipeline (Working)

```
Title → centroid_ids overlap? → YES
       → FN keyword match? → YES
       → primary_target in 50%+ of titles? → YES
       → Link to event_friction_nodes
```

---

## Session Completion Summary (2026-06-23)

### Completed

- [OK] Australia FN bundles: 3 atomics (security_alignment, economic_coercion, pacific_island_alignment)
- [OK] Europe FN bundles: 5 atomics (ukraine_battlefield, western_aid_to_ukraine, etc.)
- [OK] Global FN bundles: 105 additional atomics across all regions
- [OK] Bootstrap pipeline: 26,921 events linked across 113 FNs (88% success rate)
- [OK] primary_target filtering: Eliminates cross-regional false positives
- [OK] 50% centroid threshold: Ensures event relevance
- [OK] 10-language translations: All bundles support multilingual matching

### Event Coverage (Final State)

- Total events linked: 26,921
- FNs bootstrapped: 100/113 (88% success)
- Top FN: `ukraine_proxy_war` (3,582 events)
- Average events/FN: 269

---

## Next Session Goals

### Phase 3A: Frontend Visualization (/narratives page)

**Goal**: Display all FNs organized by geography with atomic-to-theater hierarchy

**Requirements**:

1. Open `/narratives` page and populate content block under "Experimental
Friction Nodes — contested phenomena with pro/con narrative split". Show:
   - FNs grouped by region (EUROPE, ASIA, AMERICAS, AFRICA, ARCTIC)
   - Theater circles with atomic FN cards nested below
   - Event count badges
   - "Dormant" badge for FNs >90 days quiet

2. FN Card layout:
   - FN name (EN + DE translation)
   - Event count
   - Last activity date
   - Link to `/friction-nodes/[id]` detail page

3. Theater grouping logic:
   - Query: `friction_nodes WHERE fn_type='theater' AND is_active=true`
   - For each theater: fetch `member_fn_ids` (atomic FNs)
   - Sort by centroid region

### Phase 3B: Narrative Generation (Content Layer)

**Goal**: Create pro/con editorial framings for FNs (enable discourse analysis)

**Reference Example**: Middle East Iran (created manually weeks ago)

- `iran_theater` has 4 atomic FNs
- Each atomic has 2-3 narratives with:
  - Narrative ID (e.g., `iran_nuclear_maximalist_vs_pragmatist`)
  - `name_en` & `name_de`
  - `claim_en` & `claim_de` (3-5 word framing)
  - `publishers`: [publisher names] (news sources)
  - `framing_keywords`: [list] (vocabulary signals)
  - `stance_label_en` (e.g., "Maximalist", "Pragmatist")
  - `stance`: -1 to +1 (bias direction)

**Approach**:

1. For FNs WITH event data (26,921 total): Extract real publisher + framing patterns from `title_narratives`
2. For FNs WITHOUT events: Curate manually or use LLM-assisted generation with Iran as template
3. Populate `narratives_v2` for all 113 FNs

### Phase 3C: FN Content Enrichment

- FN summaries (`description_en`, `description_de`)
- `editorial_summary_en` (1-2 sentence overview)
- Last active date calculation
- Event intensity scoring (sqrt-normalized)

---

## Technical Architecture Reference

### Key Validation Rules (DO NOT CHANGE)

**Rule 1: primary_target filtering**
- FN must have `primary_target` set
- At least 50% of event titles must contain `primary_target` centroid
- Prevents "Iran" + "beef tariff" false matches

**Rule 2: 10-language bundles**
- Always include: EN, AR, DE, ES, FR, HI, IT, JA, RU, ZH
- Use concept-based translation (not word-for-word)
- Keep keywords 2-4 words (matches headline scanning patterns)

**Rule 3: Centroid consistency**
- Use ONLY existing 114 centroids from `centroids_v3` table
- Do NOT create new centroids
- Region prefixes: `EUROPE-`, `ASIA-`, `AFRICA-`, `AMERICAS-`, `OCEANIA-`, `MIDEAST-`, `NON-STATE-`

### Bootstrap Script

**Location**: `scripts/bootstrap_friction_node.py`

**Usage**: `python scripts/bootstrap_friction_node.py --fn-id [fn_id]`

**Does**: Links events + titles to FN via keyword matching + centroid + primary_target filters

---

## Reference: Middle East Iran (Manual Example)

### Structure

```
iran_theater (theater)
├── iran_nuclear_program (atomic)
│   ├── iran_nuclear_maximalist (narrative)
│   │   └── publishers: [IRIB, Press TV, Mehr News]
│   │   └── claim_en: "Iran has right to nuclear deterrent"
│   └── iran_nuclear_pragmatist (narrative)
│       └── publishers: [Reuters, AP, BBC]
│       └── claim_en: "Negotiated limits on enrichment"
├── iran_proxy_network (atomic)
└── [2 other atomics]
```

### Lesson: Start narratives with 2 opposing framings

- Pro-Iran: government/aligned sources
- International/Western: mainstream/independent sources
- Avoid 3+ framings per FN (dilutes discourse signal)

---

## Resources to Review in New Session

### Documentation

- `docs/context/30_DecisionLog.yml` — design decisions for FN system
- `docs/fn_anchor_generation_spec.md` — keyword bundle creation rules
- `docs/context/FN_ANCHOR_VOCABULARY_SPEC.md` — vocabulary standards
- `docs/context/PIPELINE_V4_ARCHITECTURE.md` — event pipeline architecture

### Git Status & Recent Commits

```bash
git status  # Review any uncommitted changes
git log --oneline -20  # See recent FN-related commits
git diff main..fn-map  # View all changes on fn-map branch
```

### Key Files to Understand

**Core Tables**:
- `friction_nodes`: Theater & atomic FN metadata
- `taxonomy_v3`: fn_anchor multilingual keywords
- `narratives_v2`: Editorial framings (pro/con)
- `event_friction_nodes`: Event-to-FN links
- `title_narratives`: Title-to-narrative links

**Frontend Components**:
- `apps/frontend/components/FrictionNodeLayer.tsx`: Map visualization
- `apps/frontend/components/WorldMap.tsx`: Map state + mode toggle
- `apps/frontend/app/api/friction-nodes-map/route.ts`: API aggregation

**Automation**:
- `scripts/bootstrap_friction_node.py`: Event linking
- `db/migrations/`: All FN schema + seed migrations

---

## Current Git State (as of 2026-06-23 14:18)

**Branch**: `fn-map`

**Recent commits**:

1. fix(fn-bootstrap): require 50% of event titles contain primary_target centroid
2. fix(fn-bootstrap): match keywords in first clause only for multi-story titles
3. fix(fn-bootstrap): add primary_target filtering to event matching
4. feat(fn-map): friction node theater visualization on home map
5. feat(freeze): add outlet entity stance scoring

**Untracked/Modified Files** (review before starting):
- `.claude/settings.local.json`
- `docs/context/30_DecisionLog.yml`
- `docs/context/SESSION_START.md`
- `PLAN.md`
- `db/migrations/` (20+ new migration files for FN system)

---

## Quick Checklist for New Session

Before diving into narrative generation:

- [ ] Read `docs/context/30_DecisionLog.yml` (FN design decisions)
- [ ] Review `git log` (recent commits)
- [ ] Check `git status` (uncommitted changes)
- [ ] Verify all 113 FNs have `fn_anchor` bundles in `taxonomy_v3`
- [ ] Verify 26,921 events linked in `event_friction_nodes`
- [ ] Confirm `primary_target` column populated for all FNs
- [ ] Test `/friction-nodes/iran_nuclear_program` detail page (reference)
- [ ] Start narratives generation with 2-3 atomics as pilots

---

## Contact Points & Examples

**Working Examples** (test these in new session):
- Middle East Iran: `/friction-nodes/iran_nuclear_program`
- Australia: `/friction-nodes/australia_china_theater`
- Europe: `/friction-nodes/ukraine_war_theater`

**Database Queries** (useful for verification):

```sql
-- Count FNs by region
SELECT fn_type, COUNT(*) FROM friction_nodes WHERE is_active GROUP BY fn_type;

-- Events per FN
SELECT fn_id, COUNT(*) FROM event_friction_nodes GROUP BY fn_id ORDER BY COUNT(*) DESC;

-- FNs missing fn_anchor bundles
SELECT id FROM friction_nodes WHERE id NOT IN (SELECT linked_id FROM taxonomy_v3 WHERE taxonomy_function='fn_anchor');

-- Narratives per FN
SELECT fn_id, COUNT(*) FROM narratives_v2 WHERE is_active GROUP BY fn_id ORDER BY COUNT(*) DESC;
```

---

## Success Criteria (New Session End-Goal)

- [OK] `/narratives` page shows all 113 FNs grouped by geography
- [OK] Atomic FNs linked to parent theaters in UI
- [OK] Narratives generated for 30+ high-impact FNs
- [OK] FN detail pages show narratives with pro/con framings
- [OK] Event counts and last-active dates display correctly
- [OK] Cross-regional false positives eliminated via `primary_target`

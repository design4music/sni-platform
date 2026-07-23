# Narrative Consolidation Spec v2 — the position/card model

Status: **approved architecture, execution not started.** This is a full rewrite
(2026-07-23) of the flat "narratives_v2 is the narrative" plan. The prior version
is archived at `archive/NARRATIVE_CONSOLIDATION_SPEC_v1_flat.md`. It was correct
about retiring v1 and keeping the meta layer; it was wrong to treat each of the
411 FN cards as a standalone narrative. Measurement (P0e) showed those 411 cards
collapse to ~101 recurring **positions**, so the narrative entity is the
position, not the card.

Companions: `FN_THEATER_BUILD_SPEC.md` (how cards are authored),
`OFFICIAL_DOCUMENTS_LAYER.md` (regime-B ingestion), `FRICTION_NODES_RUNBOOK.md`.

Author pass: 2026-07-23. Design decisions in §1–§7 are settled by the P0
artifacts and the review in the design conversation; do not re-litigate without a
new finding from those artifacts.

---

## 0. What changed from v1-flat, in one paragraph

v1-flat proposed: attach a meta to each `narratives_v2` row, give each row a
standalone page, gate the thin ones. Three findings from P0 overturned that:
(a) **23% of rows looked empty only because theater roll-ups were miscounted** —
the true zero-title count is 14/411, not 71/309 (P0c); (b) **the same claim is
authored 2–22 times across friction nodes** — 411 cards are ~101 distinct
positions (P0e, 4.07× collapse); (c) **coalition/ownership cannot come from a
card's publisher-majority alone** — on domestic friction nodes foreign wires
dominate the bloc, so resolution must be home-country-aware (P0-coalitions). The
model below is the result.

---

## 1. Target architecture

```
meta_narratives (9)              ← unchanged, the abstraction layer
        ↑ meta_narrative_id (primary) + meta_secondary_ids[]   ON THE POSITION
positions (~101)                 ← THE narrative entity; owns the standalone page
        │ owner_centroids[]  (many-to-many; assigned label, corpus-verified)
        ↓ position_id
narratives_v2  (411, = "cards")  ← one position × one friction_node
        ↓ fn_id                        ↓ title_narratives
friction_nodes (157)             titles_v3 (media echo)
                                       ↑
official_documents ──────────────────┘  (primary source, joins via owner_centroids)
```

Three levels, each with a job:

- **position** — the universal narrative core: a claim + stance orientation that
  recurs across theaters (`america_first_transactional_alliance`,
  `china_lawful_not_coercive`). Carries meta, owner, and the **standalone page**,
  which aggregates evidence across every friction node the position appears on.
- **card** (`narratives_v2` row, unchanged table) — one appearance of a position
  on one friction node. Carries the measured `publishers[]`, `framing_keywords`,
  FN-relative `stance` (−2..+2), and the `title_narratives` attribution. Renders
  as a card on the FN page.
- **friction node** — the contested situation. Unchanged.

Reachable through four lenses: by friction node (exists), by meta (new), by
owner/coalition (new), and — the point of this rewrite — **by position**, which
is the "what does this bloc assert everywhere" view that a flat card layer could
never give.

### 1.1 Why position and card are separate

`autonomy_illusion` has zero attributed titles as a card and would be a broken
standalone page. As one card of the `america_first_transactional_alliance`
position — which also appears on transatlantic trade, defence burden-sharing and
Greenland, with real titles — it is a legitimate facet of a page that has
plenty. **The position layer dissolves the thin-page problem at its cause** (a
claim spread thin across nodes) rather than gating it. This is why v1-flat's
publication gate is dropped entirely (§6, decided).

### 1.2 The one merge principle (settled)

Positions cluster by **frame + stance sign**, NOT by frame + owner. The sincere
sovereignty defense (Mexico/Cuba/Venezuela) and the rift-exploitation echo
(Russia/China) of "US coercion of the sovereign" are **one position**: the
targeted powers are themselves sanctioned and read the hemisphere pressure as a
proxy strike, so the claim is genuinely shared. The who-said-it distinction is
not lost — it lives on the **card** (publisher bloc) and in the position's
`owner_centroids[]` list. Bias toward **less fragmentation**; split a position
later only if it proves too broad to page coherently.

### 1.3 What v1 got right and is preserved

- **The 9 meta-narratives** — abstract, stable, content-neutral. Unchanged, and
  they now attach to positions.
- **The page shape** — claim / normative line / vocabulary / timeline / matched
  items / competing narratives, meta breadcrumb up, siblings sideways. This is
  the position page.
- **Cross-surface presence** — narratives appear on event, centroid, trending and
  comparative pages, not just their own section. Preserved; those surfaces now
  show positions/cards.

---

## 2. Workstream A — build the position layer

### A1. Schema

```sql
CREATE TABLE positions (
  id                  text PRIMARY KEY,          -- slug, snake_case, globally unique
  name_en             text NOT NULL,
  name_de             text NOT NULL,
  claim_en            text NOT NULL,             -- the universal claim
  claim_de            text NOT NULL,
  stance_sign         smallint NOT NULL,         -- -1 / 0 / +1 (orientation only)
  meta_narrative_id   text REFERENCES meta_narratives(id),   -- primary
  meta_secondary_ids  text[] NOT NULL DEFAULT '{}',          -- populated now (DG-0 #4)
  owner_centroids     text[] NOT NULL DEFAULT '{}',          -- assigned, corpus-verified
  is_active           boolean NOT NULL DEFAULT true,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE narratives_v2
  ADD COLUMN position_id text REFERENCES positions(id);
```

`narratives_v2` keeps its name and every existing column — it is now the **card**
table. It loses nothing; it gains a parent. Meta and owner do **not** live on the
card (they were never there); they live on the position. `coalition` is **not** a
stored column anywhere — it is derived at read time from card publishers (§3).

### A2. The registry is the source of truth

`db/registry/narrative_positions.yaml` — one entry per position: `id`,
`name_en/de`, `claim_en/de`, `stance_sign`, `meta` (primary), `meta_secondary[]`,
`owner_centroids[]`, and `cards: [narrative_id, ...]`. A reconcile script writes
`positions` and back-fills `narratives_v2.position_id`. Diffable in git; the
mapping is a domain-model decision (house rule). The P0e draft
(`scripts/narrative_positions_draft.py`, 101 positions, every card assigned
exactly once) is the seed for this registry.

### A3. Meta assignment — now per position, not per card

Meta attaches to the **position** (101 coherent decisions, not 411). The P0a
scorer (kNN over v1's 260 human meta labels blended with each meta's signal
vocabulary, 68% leave-one-out) proposes a primary + secondary meta per position
by averaging its cards' scores. Per DG-0 #4, **secondary metas are populated
now** — a near-tie between two metas is the answer (primary + secondary), not a
deferral. Reviewed at the (now small) gate below.

### A4. Rebalancing check

Expect `security_order`, `sovereign_resistance` and `great_power_competition` to
dominate and `planetary_governance` near-empty — the corpus is Mideast/security
heavy and almost no climate/pandemic/AI friction nodes exist. **Do not fabricate
positions to fill a meta.** An empty meta page is an honest coverage statement
and a backlog signal for which theaters to build. Render it as such.

---

## 3. Workstream B — ownership and coalitions

Two distinct notions, deliberately separated (they were conflated in v1-flat):

### B1. Coalition — a named group of ISO country codes (DERIVED)

`db/registry/coalitions.yaml` defines coalitions as sets of ISO codes, assembled
from countries already in `centroids_v3.iso_codes` and `feeds.country_code`. A
card's coalition is **measured**: `publishers[] → feeds.country_code →
coalition`. Resolver: `scripts/narrative_coalitions.py`. Three rules that P0
measurement forced:

1. **ISO codes, not centroids** — `EUROPE-BALKANS` bundles Serbia + Croatia +
   Kosovo, who disagree; keying on it would force them into one voice.
2. **Hierarchical** — the Western bloc splits into `west_us/west_eu/west_uk/…`
   for intra-Western friction nodes, and rolls up to a `west` parent on US-China
   nodes where they speak as one. Without this, 174/411 came out `mixed`; with
   it, 31.
3. **Domestic-scope aware** — on a friction node whose `primary_target` sits
   inside its own `centroid_ids` (US immigration: terrain USA, target USA), the
   publisher bloc is dominated by foreign wires covering someone else's fight, so
   resolution restricts to home-country publishers. This is what correctly sends
   `usdom_ice_due_process` to `west_us` instead of `west_eu`.

Coalition is **display-only** grouping. It is NOT the join key to official
documents (that is owner, below), and it is NOT stored — it is recomputed at
read time so it always reflects the current publisher blocs.

### B2. Owner — the centroid(s) that assert the position (ASSIGNED + verified)

`positions.owner_centroids[]` names who owns the claim, from the centroid
vocabulary (`centroids_v3`, which already includes non-state owners
`NON-STATE-EU`, `NON-STATE-NATO`, `NON-STATE-UN`). Assigned editorially, then
corpus-verified against the card publisher coalitions (the derived coalition of a
position's cards should be consistent with its owner centroids). Only 2 of 253
publisher countries lack a centroid (`UN`, `WOR`), so "no centroid ⇒ cannot own a
position" costs essentially nothing.

Many-to-many is expected and correct: `us_imperial_coercion_hemisphere` is owned
by Mexico, Cuba, Venezuela **and** echoed by Russia and China. A coalition
position (NATO, EU) is either the sum of member-state positions or a flagman
state's claim echoed by allies — recorded as multiple owner centroids.

**Deferred, not solved: party/faction ownership.** AfD, Republicans, Democrats
are not centroids and must not be minted as `NON-STATE-*` (that class means armed
groups and IGOs). For the documents pilot every organ is a state/IGO body
(Kremlin, MFA, State Dept, EU Commission, NATO, UN, IRNA), so centroid ownership
suffices now. The US partisan split is already captured without factional
ownership — it lives in the card publisher bloc and the FN-relative stance (the
`us_domestic_liberal_alarm` vs `us_executive_mandate` positions on the same
nodes). Factional ownership is a real, deferrable extension.

### B3. The official-documents join

`official_documents` join to a position via `owner_centroids`: a Kremlin
statement (`actor_centroid = EUROPE-RUSSIA`) verifies the Russian-owned
positions. This is the "ultimate verification from a country-owner narrative
source website" — the join key is **owner**, not coalition, not the card. See §5.

---

## 4. Workstream C — retire v1

### C1. Consumer inventory (everything that breaks)

| Surface | File | Reads |
|---|---|---|
| `/narratives` landing | `app/[locale]/narratives/page.tsx` | `getAllMetaNarratives`, `getStrategicNarratives`, `getNarrativeSparklines` |
| `/narratives/[id]` | `app/[locale]/narratives/[id]/page.tsx` | `getStrategicNarrativeById`, `getNarrativeWeeklyActivity`, `getNarrativeEvents` |
| `/narratives/meta/[id]` | `app/[locale]/narratives/meta/[id]/page.tsx` | `getMetaNarrativeActivity` + the above |
| `/narratives/map` | `app/[locale]/narratives/map/page.tsx` | `getNarrativeMapData` |
| Event pages | `components/narratives/EventNarrativeBadges.tsx` | `getNarrativesForEvent` |
| Centroid pages | `components/narratives/CentroidNarrativeSection.tsx` | `getNarrativesForCentroid` |
| Competing panel | `components/narratives/CompetingNarrativesPanel.tsx` | `getCompetingNarratives` |
| Trending cards | `queries.ts:2008` | `getTopNarrativePerEvent` |
| Comparative analysis | `app/[locale]/analysis/comparative/.../page.tsx` | `getNarrativesForEvent` |

`getNarrativesForEvent` and `getTopNarrativePerEvent` are event-keyed; v2 has no
event link. See §4-derived-table below.

### C2. Retirement sequence

Soft-delete before drop. `is_active = false` on `strategic_narratives`, leave
tables one full release, then drop via `scripts/safe_db_migrate.py`.
`event_strategic_narratives` is 82k rows with an FK — print the cascade blast
radius before touching it (house rule).

Pipeline code to retire once the frontend is off v1:
`pipeline/phase_4/match_narratives.py`, `match_narratives_llm.py`,
`review_narratives_llm.py`, `materialize_narratives_landing.py`,
`materialize_narrative_detail.py`, daemon phases 4.2f/g/h. That is the whole LLM
discovery+review loop — a real Slot-4 cost cut.

`docs/narrative_taxonomy.yaml` and `narrative_taxonomy_v2.yaml` → `docs/archive/`.

### C3. URL policy

`/narratives/[id]` stays canonical; **position slugs** now occupy it (not card
ids). v1 ids and position slugs are disjoint (P0d verified 0 collisions between
v1's 260 and v2's 425 ids; position slugs are a fresh namespace, re-verify before
cutover). This is a **demo**, so redirect policy is light (decided): 301 the
handful of high-traffic v1 ids to their nearest position, blanket-301 the rest to
`/narratives` or the homepage. P0d's draft map ranks v1 ids by old event count
for the hand-mapped few; it also now skips any target below a page threshold —
moot here since there is no gate, so it simply maps to the best position.

---

## 5. Workstream D — the pages

### D1. Field parity: what a position page renders

| v1 element | position-model replacement | Status |
|---|---|---|
| `name` | `positions.name_en/de` | new |
| `claim` | `positions.claim_en/de` | new (the universal claim) |
| `normative_conclusion` | strongest card `stance_label_en/de` | exists on cards |
| `keywords` (invented) | union of card `framing_keywords` (corpus-verified) | exists on cards |
| `actor_centroid` (single) | `positions.owner_centroids[]` + derived coalition | new |
| `action_classes`, `domains` | — | **drop** (v1 matcher signals; nothing reads them) |
| `meta_narrative_id` | `positions.meta_narrative_id` + `meta_secondary_ids[]` | new |
| `event_count` | derived from `title_narratives` rolled card→position→event | see below |
| weekly timeline | `title_narratives ⋈ titles_v3`, unioned over the position's cards | query exists `friction-nodes.ts:510`, promote to MV |
| matched events list | derived events, aggregated across cards | see below |
| competing narratives | **sibling positions on the shared friction nodes** | structural, strictly better |

### D2. Position page layout

Keep the v1 shell. Header = position `name` (h1), `claim`, strongest card
`stance_label` as the normative line, meta + owner breadcrumb. Sidebar = meta
card, owner/coalition card, stance-position strip, **sibling-positions panel**
(replaces `CompetingNarrativesPanel`). Body = activity timeline (headline volume
over time, unioned across the position's cards, same weekly form as
`friction-nodes.ts:510`) → **primary sources** (official documents by owner, §7)
→ **where this position appears** (its cards, one row per friction node, with
that card's publisher bloc and match_count) → derived events.

Three genuinely new elements:

- **Cross-FN reach panel** — "this position appears on N friction nodes," the
  list with per-FN match counts. This is the surface a flat card layer could
  never produce, and the reason the position layer exists.
- **Owner/coalition panel** — `owner_centroids[]` plus the derived publisher
  coalitions that carry it. Honest about who asserts vs who amplifies.
- **Stance-position strip** — where the position sits on each FN's −2..+2 axis,
  siblings plotted alongside. Reuse `FrictionNodeNarrativeBricks.tsx`.
  **Stance is FN-relative and must never be aggregated across friction nodes**
  (open question 3, answer: forbidden).

### D3. The FN page — two-column card display (idea 2)

On `/friction-nodes/[slug]`, cards render in **two stacked columns**: supporting
(card stance > 0) and critical (card stance < 0), neutral in its own band. Each
card shows its stance label + publisher bloc and links up to its **position
page**. Pure UI change over the current accordion — no data-model impact. The
pro/con nuance is visible at a glance; the universal claim is one click up.

### D4. The event-link derivation

v2 links to **titles**; v1 linked to **events**. Derive, never re-match (a second
matcher would patch an upstream decision). A title belongs to a card via
`title_narratives`, a card to a position via `position_id`, a title to an event
via existing membership. Roll up mechanically into a derived table:

```sql
CREATE TABLE event_positions (
  event_id     uuid NOT NULL,
  position_id  text NOT NULL REFERENCES positions(id),
  title_count  integer NOT NULL,        -- event's titles carrying this position
  PRIMARY KEY (event_id, position_id)
);
```

Rebuilt in the `fn_refresh` daemon slot right after `link_titles`, a single
`INSERT … SELECT … GROUP BY` over `title_narratives ⋈ position_id ⋈ title→event
membership`. Derived: every row reproducible from `title_narratives`; nothing
else writes to it. Event-page badges become "N of this event's M headlines carry
position X" — defensible in a way v1's confidence percentage never was.

**Theater sub-case.** Theater cards carry no bundle; their titles come from
`THEATER_ROLLUP_SQL` (member-atomic titles of the same stance sign, publisher in
the card's bloc). The event derivation for a position that includes a theater
card must mirror that union, or counts won't reconcile with the FN page. Effective
per-card counts already handle this: `scripts/narrative_counts.py`.

### D5. Caching

Positions need MVs (the standalone page has timeline + derived events + siblings +
cross-FN reach + primary sources — well past a 12h in-process cache):

- `mv_positions_landing` — one row per locale: metas, positions, sparklines.
- `mv_position_detail` — one row per (position, locale): position, weekly
  activity, top headlines across cards, derived events, sibling positions, cards
  list, primary sources.

New Phase 4.2 materializer. Freshness ceiling: FN refresh 6h, ingestion 12h → a
12h MV staleness gate is correct, no tighter.

---

## 6. Publication gate — REMOVED (decided)

v1-flat proposed a ≥25-title gate. **Dropped.** With the position layer, thin
cards roll up into pages that have real evidence, so the empty-page problem
largely dissolves. Every position gets a standalone page — even a genuinely thin
one is a valid claim backed by its card text, its owner, and (later) official
documents, which are better evidence than media volume anyway. `noindex` on a
position whose *aggregate* title count is still near-zero is a cheap SEO hedge to
apply later, not a gate. The 14 truly-zero cards (P0c) are FN-calibration work
(dead vocab / bad bloc), tracked under `FN_THEATER_BUILD_SPEC.md`, not here.

---

## 7. Workstream E — official documents as primary sources

`OFFICIAL_DOCUMENTS_LAYER.md` (approved 2026-07-10) specifies statement ingestion
with a `narrative_id` FK, a `coalition`/`actor_centroid` per source, and a
registry symmetry rule. **Design approved, zero implementation exists.** This
project inherits the build of its Phase 1 (statements pilot).

Rewire for the position model: a document joins to a **position** via
`owner_centroids` (§3.3), not to a card. When documents exist for a position they
are its **primary evidence** and lead the page; headline samples demote to a
"media echo" strip. The position page is where the three-way screen lands:

> what officials assert (statements) · what the rules say (regulatory) · how media frames it (headlines)

Two dependencies:

1. The owner join needs `owner_centroids` populated on positions (§2/§3) to be
   checkable — the registry symmetry rule ("every owner has organs listed")
   becomes mechanical.
2. The statement enrichment prompt flags claims **not yet in the position's claim
   structure** — a narrative-evolution signal, rendered as a review queue for the
   author, never auto-editing `claim_en`. Prompt changes are business logic
   (house rule).

Sequencing: Phase 1 pilot (`ukraine_war_theater` + `iran_theater`, ~13 sources)
proves the section. Do not block the page rebuild on full document coverage —
design the "Primary sources" block to degrade to absent.

---

## 8. Open questions (updated)

1. **Owner-label assignment per position** — `owner_centroids[]` is assigned then
   corpus-verified against derived coalitions. The verification rule (how much
   inconsistency between assigned owner and measured publisher coalition is
   tolerated before flagging) needs a threshold. Proposed: flag when the
   position's dominant coalition maps to no owner centroid.
2. **Does `/narratives/map` survive?** Built on v1's single `actor_centroid` →
   ISO mapping. Rebuild as an owner/coalition map or retire. Proposed: retire for
   the demo, rebuild later if wanted.
3. **Cross-FN stance** — FN-relative, never aggregated. Settled: forbid it.
4. **`title_narratives` provenance** — add `matched_keywords text[]` at attribution
   time? Cheap at write, makes the vocabulary panel evidential. Proposed: yes.
5. **Position granularity** — accepted at ~101 (frame-level, less fragmentation).
   Revisit only if a specific position proves too broad to page coherently; the
   registry makes a split a local edit.

---

## 9. Implementation plan — phases

Domain judgment is concentrated in the gates below (owner: Maksim). Between gates
every phase is mechanical spec-compliance with a stated verification. A phase that
discovers a decision not listed at its gate stops and asks.

### Decision gates

**DG-0 — before any schema change (mostly RESOLVED this session)**
1. Position list + card membership — **accepted** (P0e draft, 101 positions).
   Registry review is a diff, not a from-scratch call.
2. Meta per position (primary + secondary) — review the P0a-scored proposals over
   the 101 positions. *Domain model change; nothing writes before sign-off.*
3. `owner_centroids[]` per position — assign from the centroid vocabulary,
   corpus-verified. Reviewed as a registry diff.
4. Coalition vocabulary (`coalitions.yaml`) — **accepted** (hierarchical,
   ISO-keyed, domestic-scope aware).
5. Publication gate — **removed** (decided).
6. Secondary metas — **populate now** (decided).

**DG-1 — before derivation (P2)**
7. `matched_keywords[]` on `title_narratives` at attribution time (open q4).
8. Theater derivation mirrors `THEATER_ROLLUP_SQL` for positions that include a
   theater card (§5.4).

**DG-2 — before UI build (P5)**
9. Cross-FN stance: render only within an FN; never aggregate (open q3, settled).
10. `/narratives/map`: retire now, rebuild later (open q2, proposed retire).
11. Redirect policy for v1 ids: light for the demo — hand-map the top few, blanket
    the rest (§4.3).

**DG-3 — before documents content (P7) and before drops (P8)**
12. Pilot organ set (~13 sources, `ukraine_war_theater` + `iran_theater`).
13. Statement enrichment prompt sign-off (business logic).
14. Review workflow: CLI vs minimal admin page (default CLI).
15. Final confirmation to DROP v1 tables (destructive, cascade-checked, row counts
    stated — house rule).

### Phases

| # | Phase | Deliverable | Verification | Needs |
|---|---|---|---|---|
| **P0** | Research artifacts | **DONE.** (a) archetype→meta scorer + report `P0a_archetypes.md`; (b) draft `narrative_meta_mapping.yaml`; (c) thin-narrative triage `P0c_thin_narratives.md`; (d) v1↔v2 id + redirect map `P0d_redirect_map.md`; (e) **position clustering `P0e_positions_draft.md` (411→101)** and `scripts/narrative_positions_draft.py`; coalition resolver `scripts/narrative_coalitions.py` + `db/registry/coalitions.yaml`; effective-count `scripts/narrative_counts.py` | Human review of all artifacts | — |
| **P1** | Position schema + registry | `positions` table + `narratives_v2.position_id` (via `safe_db_migrate.py`); `db/registry/narrative_positions.yaml` (id/name/claim/stance_sign/meta+secondary/owner_centroids/cards) from the P0e seed; reconcile script (registry → tables, idempotent); meta + owner reviewed | Every active card maps to exactly one position; every position has a primary meta and ≥1 owner centroid; reconcile re-run is a no-op | DG-0 |
| **P2** | Derived event links + provenance | `event_positions` derived table (§5.4) built in `fn_refresh` after `link_titles`; `matched_keywords` capture in `link_titles` if DG-1 says yes | Derived per-position event counts reconcile with card-level `match_count` for atomic and theater paths; full rebuild idempotent | DG-1, P1 |
| **P3** | Materializers | `mv_positions_landing` + `mv_position_detail` (adapt v1 `materialize_narratives_landing.py` / `materialize_narrative_detail.py` as templates); weekly timeline unioned across a position's cards baked into the detail blob; daemon hook after `fn_refresh`, 12h staleness | MV blobs carry every §5.1 field for both locales; spot-check 5 positions vs live queries | P1, P2 |
| **P4** | Landing + meta pages | `/narratives` and `/narratives/meta/[id]` rebuilt on the new MVs; empty-meta honest rendering; v1 rows `is_active=false` | Pages render from MV only (no live v1 reads); DE parity | P3 |
| **P5** | Position page + FN two-column cards | `/narratives/[id]` = position page per §5.2 (header, meta/owner/coalition sidebar, sibling panel, stance strip, cross-FN reach, cards list, derived events, Primary Sources block degrading to absent); FN page card display → two columns (§5.3) | Every §5.1 field renders; FN two-column display; DE parity | DG-2, P3 |
| **P6** | Cross-surface re-point + redirects | Event badges → `event_positions`; centroid section, trending badge, comparative analysis re-pointed to positions; v1 URL redirects per DG-2 #11 | Zero frontend reads of `strategic_narratives`/`event_strategic_narratives` (grep-verified) | P2, P5 |
| **P7** | Official documents — greenfield (per `OFFICIAL_DOCUMENTS_LAYER.md` Phase 1) | **P7a** tables + `official_sources_statements.yaml` reconcile; **P7b** `scripts/fetch_official_documents.py` (RSS/listing, `ON CONFLICT (url) DO NOTHING`, manual-first); **P7c** enrichment prompt + pending-review CLI; **P7d** Primary Sources block wired on P5 pages, joined via `owner_centroids`, claim-evolution flags as a review queue (never auto-editing `claim_en`) | Pilot sources fetch idempotently; enriched rows land `pending`; only `published` renders; a position with zero documents is visually unchanged | DG-3 #12–14; P1 (needs `owner_centroids`); independent of P3–P6, can run in parallel after P1 |
| **P8** | v1 retirement | One release with v1 tables inactive but present; then drop `strategic_narratives`, `event_strategic_narratives`, `narrative_weekly_activity`, both v1 MVs; retire daemon 4.2f/g/h + the five v1 pipeline scripts; archive `narrative_taxonomy*.yaml` | Cascade blast radius printed and confirmed; daemon cycle green without the retired phases | DG-3 #15, P6 shipped + one release soak |

**Parallelism:** P7 is independent of the page rebuild after P1. Everything else
sequential.

DE parity is not a phase — every field ships `_en` + `_de` from the start
(`meta_narratives`, `narratives_v2`, `friction_nodes`, and the new `positions`
are all bilingual). Only new UI strings are net-new translation surface.

---

## 10. Decision log entries this implies

Next free id is **D-095**.

- **D-095** — the narrative entity is the **position** (universal claim across
  friction nodes), not the FN card. v1 strategic narratives retired as
  unfalsifiable; `narratives_v2` rows become cards under positions.
- **D-096** — positions cluster by frame + stance sign, not frame + owner; the
  who-said-it distinction lives on the card publisher bloc and the position's
  `owner_centroids[]`. Bias to less fragmentation (~101 positions).
- **D-097** — meta attaches to the position (primary + secondary, both populated);
  mapping lives in a git registry.
- **D-098** — coalition is derived at read time from card publishers
  (ISO-keyed, hierarchical, domestic-scope aware), display-only, never stored.
- **D-099** — ownership is `owner_centroids[]` on the position (assigned +
  corpus-verified, many-to-many); it is the join key for official documents.
- **D-100** — event↔position links are *derived* from title attribution rolled
  card→position→event, never separately matched.
- **D-101** — no publication gate; every position gets a standalone page.

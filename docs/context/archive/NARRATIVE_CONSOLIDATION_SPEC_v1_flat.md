# Narrative Consolidation Spec — v2 becomes the narrative layer

Status: **approved plan, execution not started.** Reviewed and confirmed
2026-07-19. Execute per the phase table in §8 — P0 is autonomous; every phase
after that is blocked on the decision gate (DG-0..DG-3) listed at its row.
Do not skip a gate. Do not re-litigate the architecture in §1–§7 without a
new finding from the P0 artifacts contradicting it.
Author pass: 2026-07-19.

Companions: `FN_THEATER_BUILD_SPEC.md` (how v2 narratives are authored),
`OFFICIAL_DOCUMENTS_LAYER.md` (regime-B ingestion, already carries a
`narratives_v2` FK), `FRICTION_NODES_RUNBOOK.md` (FN architecture).

---

## 1. What exists right now

Two narrative systems share a name and nothing else. They do not read each
other's tables, do not share a matcher, and do not share a cache layer.

| | **v1 — strategic narratives** | **v2 — FN card narratives** |
|---|---|---|
| Narrative table | `strategic_narratives` (260) | `narratives_v2` (309 rows, 303 active: 230 atomic / 73 theater) |
| Parent | `meta_narratives` (9) via `meta_narrative_id` FK | `friction_nodes` (184) via `fn_id` FK |
| Link table | `event_strategic_narratives` (82,040) — **event** level, has `confidence` + `matched_signals` | `title_narratives` (61,209) — **title** level, no confidence, no provenance |
| Matcher | `pipeline/phase_4/match_narratives.py` — weighted score `0.40*keyword + 0.35*action_class + 0.25*domain`, threshold 0.55, plus LLM discovery + LLM review | `scripts/bootstrap_friction_node.py:link_titles` — pure SQL, boolean AND-gate (publisher ∈ set, centroid overlap, `fn_anchor` alias hit, optional framing keyword, theater/atomic precedence) |
| Scheduling | daemon Slot 4, Phase 4.2f/g/h | daemon slot `fn_refresh`, every 6h |
| Timeline | `narrative_weekly_activity` (5,735) | none — computed live in `friction-nodes.ts:510` |
| MV | `mv_narratives_landing`, `mv_narrative_detail` | **none** — every query is request-time under a 12h in-process cache |
| Pages | `/narratives`, `/narratives/[id]`, `/narratives/meta/[id]`, `/narratives/map` | only as cards inside `/friction-nodes/[slug]` |
| Data depth | Jan–Jul 2026 | Jan 4 – Jul 14 2026, 61k titles |

### Why v1 content is not defensible

`strategic_narratives` rows were authored from `docs/narrative_taxonomy_v2.yaml`
— a hand-written catalogue of what actors *plausibly* claim, drafted ahead of
the data. Matching is then a keyword/action-class score against that invented
vocabulary. Two consequences:

- The claim text is unfalsifiable against the corpus. Nothing in the pipeline
  ever checks that any publisher said it.
- `confidence` is a score against a made-up keyword list, not evidence
  strength. 82k event links at threshold 0.55 read as precision they do not have.

v2 inverts this. A narrative is defined by **a measured publisher bloc plus a
measured vocabulary inside a bounded contested phenomenon**. The theater build
spec forces corpus verification of every keyword before it ships. That is the
asset worth keeping.

### What v1 got right — and must be preserved

- **The meta layer.** The 9 meta-narratives are genuinely good: abstract,
  stable, non-overlapping, and they answer "what kind of world-order argument
  is this." They are not tied to the invented content and survive the swap.
- **The page shape.** Claim / normative conclusion / vocabulary / actor /
  timeline / matched items / competing narratives, with meta breadcrumb up and
  sibling nav sideways. This is the target layout.
- **Cross-surface presence.** v1 narratives appear on event pages, centroid
  pages, trending cards and comparative analysis — not just their own section.

---

## 2. Target architecture

```
meta_narratives (9)          ← unchanged, the abstraction layer
        ↑ meta_narrative_id (NEW on narratives_v2)
narratives_v2 (309)          ← the ONLY narrative entity
        ↓ fn_id                        ↓ title_narratives        ↓ narrative_id
friction_nodes (184)          titles_v3 (media echo)      official_documents (primary source)
```

One narrative entity, reachable through three lenses:

- **by friction node** — "what is contested here" (exists today)
- **by meta-narrative** — "what kind of world-order claim is this" (new)
- **by coalition/actor** — "what does this bloc assert everywhere" (new)

`strategic_narratives`, `event_strategic_narratives`, `narrative_weekly_activity`,
and both v1 MVs are retired.

---

## 3. Workstream A — map narratives_v2 to meta-narratives

### A1. Where the mapping attaches

**On the narrative, not the FN.** Within one FN the competing stances belong to
*different* meta-narratives — that asymmetry is the product. Example, `gaza_war`:

| narrative | stance | meta |
|---|---|---|
| `israel_dismantle_hamas` | +2 | `security_order` |
| `gaza_humanitarian_catastrophe` | −2 | `global_justice` |

Attaching meta at FN level would collapse exactly the distinction that makes the
page interesting.

### A2. Proposed schema delta

```sql
ALTER TABLE narratives_v2
  ADD COLUMN meta_narrative_id text REFERENCES meta_narratives(id),
  ADD COLUMN meta_secondary_ids text[] NOT NULL DEFAULT '{}',
  ADD COLUMN coalition text;
```

- `meta_narrative_id` — primary, one per narrative, required before a narrative
  can render standalone.
- `meta_secondary_ids` — a sovereignty claim that is also a multipolarity claim
  is common; forcing one label loses signal. Secondary metas list the narrative
  on the meta page under a "also argues" band, and do not count toward primary
  totals (avoids double-counting in aggregates).
- `coalition` — free-slug bloc label (`west_us`, `west_eu`, `ru`, `iran`,
  `multilateral`, `global_south`, …). **This is not decoration.**
  `official_sources.coalition` already exists in the approved documents spec;
  without the same field on `narratives_v2` the statement→narrative join in
  Workstream D has nothing to join on but a hand-maintained FK. `actor_centroids`
  is too granular (a 5-centroid array) to group by.

### A3. How the assignment gets made

Not by LLM over 309 rows in one pass, and not by hand from scratch. Pre-filter
mechanically first (Rule 4):

1. **Mechanical pre-grouping.** Cluster the 309 narratives by
   `(sign(stance), actor_centroids overlap, FN region)`. This collapses to on the
   order of 25–40 recurring archetypes — "Western coalition asserts enforcement
   right", "multipolar sovereignty backing", "post-colonial dispossession
   framing", "EU engage-and-criticise". Publisher blocs repeat hard across
   theaters; so do the claims.
2. **Assign meta per archetype**, by hand, in a reviewable YAML table. ~30
   judgment calls, not 309.
3. **LLM only for the residue** — narratives that do not fall into an archetype,
   plus a verification pass that re-derives each assignment from `claim_en` and
   flags disagreements with step 2 for human adjudication.
4. **Registry, not table edits.** Per the asset-registry precedent, the mapping
   lives in `db/registry/narrative_meta_mapping.yaml` and is reconciled into the
   column by a script. The mapping is a domain-model decision and must be
   diffable in git.

Note this is a **domain model change** under the global rules — step 2's
archetype table needs sign-off before anything is written.

### A4. Rebalancing check

v1's 260 narratives spread across 9 metas by construction. v2's 309 will not
spread evenly — the corpus is Mideast-heavy (the top 12 narratives by volume are
all Iran/Israel/Gaza/Lebanon). Expect `security_order` and `global_justice` to
dominate and `planetary_governance` to come out near-empty, because we have
built almost no climate/pandemic/AI friction nodes.

**Do not fabricate narratives to fill a meta.** An empty meta page is an honest
statement about coverage and a legitimate backlog signal for which theaters to
build next. Render it as such.

---

## 4. Workstream B — retire v1

### B1. Consumer inventory (everything that breaks)

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

`getNarrativesForEvent` and `getTopNarrativePerEvent` are the awkward ones: they
are **event**-keyed and v2 has no event link. See §5.3.

### B2. Retirement sequence

Soft-delete before drop, always. `is_active = false` on `strategic_narratives`,
leave the tables in place through one full release, then drop in a separate
migration via `scripts/safe_db_migrate.py`. `event_strategic_narratives` is 82k
rows with an FK — check the cascade blast radius before touching it.

Pipeline code to retire once the frontend is off v1: `pipeline/phase_4/match_narratives.py`,
`match_narratives_llm.py`, `review_narratives_llm.py`, `materialize_narratives_landing.py`,
`materialize_narrative_detail.py`, and daemon phases 4.2f/g/h. That is the whole
LLM discovery+review loop — a real cost reduction in Slot 4.

`docs/narrative_taxonomy.yaml` and `narrative_taxonomy_v2.yaml` move to
`docs/archive/`. They are the record of the invented layer, not a live input.

### B3. URL policy

Keep `/narratives/[id]` as the canonical narrative route and let v2 ids occupy
it. v1 ids (`nato_collective_defense`, …) and v2 ids (`israel_dismantle_hamas`, …)
do not collide — both are slugs in the same namespace, verified disjoint before
cutover. Old ids 301 to their nearest v2 successor where one exists, else to the
meta page. `/narratives/meta/[id]` is unchanged — same 9 ids, new children.

---

## 5. Workstream C — the standalone narrative page

### C1. Field parity: what replaces what

| v1 element | v2 replacement | Status |
|---|---|---|
| `name` | `name_en/de` | exists — **currently fetched but never rendered** (`FrictionNodeNarrativeCards.tsx` titles cards by `stance_label`) |
| `claim` | `claim_en/de` | exists |
| `normative_conclusion` | `stance_label_en/de` | exists, and is sharper — it is the compressed normative position |
| `keywords` (invented) | `framing_keywords` (corpus-verified) | exists, strictly better |
| `actor_centroid` (single) | `actor_centroids` (bloc) + new `coalition` | exists |
| `action_classes`, `domains` | — | **drop.** Signal fields for the v1 matcher; v2 does not match on them and nothing else reads them |
| `meta_narrative_id` | new (§3) | to build |
| — | `stance` (−2..+2), `publishers`, `fn_id` | v2-only, no v1 analogue |
| `event_count` | `match_count` (titles) + derived event count | see §5.3 |
| weekly timeline | derive from `title_narratives ⋈ titles_v3` | query exists at `friction-nodes.ts:510`, needs promoting to a materialized column |
| matched events list | matched headlines + derived events | see §5.3 |
| competing narratives (shared-event heuristic) | **sibling narratives on the same `fn_id`** | strictly better — competition is structural, not inferred |

### C2. Page layout

Keep the v1 shell. Header = `name` (h1), `claim`, `stance_label` as the normative
line, meta + FN breadcrumb. Sidebar = meta card, friction node card, coalition
card, stance position indicator, sibling-narrative panel (replaces
`CompetingNarrativesPanel`). Body = activity timeline → primary sources (new,
§6) → headlines under this frame → derived events.

The activity timeline is **headline volume over time, in the same weekly form
as today** — the query already exists at `friction-nodes.ts:510` and only needs
promoting into the detail MV. No lifecycle states, no decay machinery, nothing
beyond what the current implementation renders. (Lifecycle modeling is the
parked `situation entity` backlog item, explicitly out of scope here.)

Three genuinely new elements v1 could not support:

- **Stance-position strip** — where this narrative sits on the FN's −2..+2 axis,
  with the sibling narratives plotted alongside and sized by `match_count`.
  `FrictionNodeNarrativeBricks.tsx` already does exactly this per-FN; reuse it.
- **Publisher bloc panel** — the `publishers` array *is* the evidence for who
  carries the frame. v1 had nothing comparable.
- **Cross-FN coalition rail** — "this coalition also argues X here, Y there,"
  driven by the new `coalition` field. This is the surface that makes the
  narrative layer more than a per-FN accordion.

### C3. The event-link gap — the one real architectural decision

v2 links to **titles**; v1 linked to **events**. Event links are needed for:
matched-events lists, event-page badges, trending badges, comparative analysis,
and any "narrative activity" measure comparable to the old one.

Two options:

- **(A) Derive.** A title belongs to an event via existing membership; roll
  `title_narratives → titles_v3 → events_v3` up mechanically.
  No new matcher, no new matching logic, no new failure mode. Event relevance is
  a strength count (how many of the event's titles carry the frame), which is a
  more honest number than v1's `confidence`.
- **(B) A new event-level matcher.**

**Recommend (A).** (B) reintroduces a scoring layer of exactly the kind we are
retiring, and would be a downstream phase patching an upstream design — the
attribution decision already happened at the title gate. Derivation keeps one
matcher and one truth.

Under (A), event-page badges become "N of this event's M headlines carry frame
X," which is defensible in a way the old confidence percentage never was.

**Where the derivation lands matters.** Three consumers are event-keyed (event
badges, trending cards, comparative analysis) and cannot be served from an MV
blob keyed by narrative. The derivation materializes into a persistent derived
table:

```sql
CREATE TABLE event_narratives_v2 (
  event_id     uuid NOT NULL,
  narrative_id text NOT NULL REFERENCES narratives_v2(id),
  title_count  integer NOT NULL,       -- how many of the event's titles carry the frame
  PRIMARY KEY (event_id, narrative_id)
);
```

Rebuilt mechanically in the `fn_refresh` daemon slot right after `link_titles`
— a single `INSERT ... SELECT ... GROUP BY` over `title_narratives` ⋈ title→event
membership, no LLM, no score. It is a *derived* table: any row must be
reproducible from `title_narratives`; nothing else may ever write to it.

**Theater sub-case.** Theater narrative counts on the FN page come from
`THEATER_ROLLUP_SQL` (own attributed titles + member-atomic titles with the
same `sign(stance)`), not from `title_narratives` alone. The event derivation
for theater narratives must mirror that same union, or theater event counts
will not reconcile with the page numbers.

### C4. Thin narratives — a publication gate is required

Measured over `narratives_v2` ⋈ `title_narratives`:

- **71 of 309 (23%) have zero attributed titles**
- 56 more have 1–9
- only 75 have ≥100

FN cards hide this today: `filterNarrativesForDisplay` always renders the first
two by `display_order` and hides the rest below 5 titles. As a card in a pro/con
pair, a thin narrative is still meaningful — it shows one side is barely voiced.
**As a standalone indexable page with a timeline and statistics, an empty
narrative is a broken page.**

Proposed gate: a narrative gets a standalone page at ≥25 attributed titles.
Below that it renders only as a card on its FN, and its `/narratives/[id]` URL
either 404s or redirects to the FN anchor. Meta pages list thin narratives in a
muted "low signal" band without linking out. `noindex` on anything under the
threshold.

The 71 zero-match narratives also need triage on their own terms — each is
either a mis-specified publisher bloc, a dead vocabulary, or a genuinely silent
position, and those want different fixes. That is FN calibration work under
`FN_THEATER_BUILD_SPEC.md`, not part of this project, but it blocks a clean
launch and should run in parallel.

### C5. Caching

v2 currently has no MV. A standalone page with timeline + derived events +
sibling panel + coalition rail is well past what a 12h in-process cache should
carry, and `/narratives` is `force-dynamic` precisely because the MV made it
cheap. Mirror the v1 pattern:

- `mv_narratives_v2_landing` — one row per locale: metas, narratives, sparklines,
  meta activity.
- `mv_narrative_v2_detail` — one row per (narrative, locale): narrative, weekly
  activity, top headlines, derived events, siblings, primary sources.

Built by a new Phase 4.2 materializer. Note the freshness ceiling: FN refresh is
6h and ingestion is 12h, so a 12h MV staleness gate is correct — no tighter.

---

## 6. Workstream D — official documents as primary sources

`OFFICIAL_DOCUMENTS_LAYER.md` (approved 2026-07-10) already specifies
`official_documents.narrative_id REFERENCES narratives_v2(id)`, a statement
enrichment prompt that maps FN + narrative, extracts `speaker`, 1–3 verbatim
`quotes`, and a `claims` list, and a registry symmetry rule that every coalition
carrying a narrative gets its official organs listed.

**Status: the design is approved but zero implementation exists** (as of
2026-07-19 — no tables, no registry files, no fetch script). This project
therefore inherits the *build* of the layer's Phase 1 (statements pilot), not
just the wiring. The design work is done; the implementation is greenfield and
is scoped as its own workstream in §8.

When documents exist for a narrative they are its **primary evidence** and lead
the page; headline samples demote to the "media echo" strip. The standalone
narrative page is where the three-way screen lands:

> what officials assert (statements) · what the rules say (regulatory) · how media frames it (headlines)

Two dependencies to name:

1. The registry symmetry rule needs `coalition` on `narratives_v2` (§3.2) to be
   checkable. Without it, "every coalition has organs listed" cannot be asserted
   mechanically.
2. The statement enrichment prompt flags claims *not yet present in the
   narrative's claim structure* — a narrative-evolution signal. On the standalone
   page this is the "what changed" surface, and it is the first real feedback
   loop from evidence back into narrative definitions. It should render as a
   review queue for the author, not auto-edit `claim_en`. Prompt changes here
   are business logic (Rule 9).

Sequencing: Phase 1 of the documents layer (statements pilot,
`ukraine_war_theater` + `iran_theater`, ~13 sources) is enough to prove the
page section. Do not block the narrative page rebuild on full document coverage
— design the "Primary sources" block to degrade to absent.

---

## 7. Open questions

Each of these now has a *proposed* answer registered at a decision gate in §8
(DG-1 #6, DG-2 #7–10, DG-1 #5). They stay listed here as questions until the
gate is signed off.

1. **Theater narratives on the same footing as atomic ones?** 73 of 309 are
   theater-level roll-ups whose `match_count` is computed by entirely different
   SQL (`THEATER_ROLLUP_SQL`, publisher ∩ member-atomic-with-same-stance-sign),
   and whose event count is hardcoded 0. Do they get standalone pages, or does a
   theater narrative live only on its theater page? Leaning: yes to standalone,
   but the derived-events work (§5.3) has to cover the roll-up path too.
2. **Does `/narratives/map` survive?** It is built on v1's single
   `actor_centroid` → ISO mapping. v2's `actor_centroids` is a bloc array, which
   maps to a region rather than a country. Either rebuild as a coalition map or
   retire the route.
3. **Is `stance` comparable across FNs?** −2 means "opposed to the status quo of
   this friction node," which is FN-relative. Aggregating stance across a meta
   page or a coalition rail may be meaningless. Needs a decision before any
   cross-FN stance visual ships.
4. **`title_narratives` carries no provenance** — no confidence, no matched
   signal, no `fn_id`. "Why did this headline match?" is unanswerable without
   re-running the gate, and per-FN counts need a 3-table join. Worth adding
   `matched_keywords text[]` at attribution time? Cheap at write, and it is what
   makes the vocabulary panel evidential rather than declarative.
5. **`actor_centroids` is display-only** — never read by the matcher
   (`bootstrap_friction_node.py:141` selects only id/name/publishers/framing_keywords/framing_required).
   Scope is entirely the parent FN's `centroid_ids`. Promoting it to a page-level
   "Coalition" statement implies a precision it does not have. Either verify it
   against the attributed corpus or label it as editorial.

---

## 8. Implementation plan — Sonnet-executable phases

Design principle for the breakdown: **all domain judgment is concentrated in
four decision gates** (DG-0..DG-3, owner: Maksim). Between gates, every phase is
mechanical spec-compliance work with a stated verification — executable by
Sonnet without further judgment calls. A phase that discovers it needs a
decision not listed at its gate must stop and ask, not improvise.

### Decision gates (what Maksim decides, grouped)

**DG-0 — before any schema change** (domain model gate, the big one)
1. Approve the archetype→meta mapping table (P0 output). *This is the domain
   model change; nothing writes to the DB before this sign-off.*
2. Coalition slug vocabulary: the canonical list of `coalition` values and
   where it lives (Rule 5 — proposed: `db/registry/coalitions.yaml`, shared
   with `official_sources.coalition`).
3. Publication gate threshold (proposed: ≥25 attributed titles).
4. Secondary metas: populate now or add the column and defer population
   (proposed: defer — column ships, YAML supports it, populate opportunistically).

**DG-1 — before derivation work (P2)**
5. Provenance capture: add `matched_keywords text[]` to `title_narratives` at
   attribution time? (proposed: yes — cheap at write, makes the vocabulary
   panel evidential; open question 4).
6. Theater derivation: confirm theaters get derived events via the rollup
   union (own titles + member-atomic same-sign titles), mirroring
   `THEATER_ROLLUP_SQL` (§5.3).

**DG-2 — before UI build (P5)**
7. Theater narratives: standalone pages yes/no (proposed: yes; open question 1).
8. Cross-FN stance rule: stance visuals render only within an FN context;
   no cross-FN stance aggregation anywhere (open question 3 — proposed answer:
   forbid it, stance is FN-relative).
9. `actor_centroids` labeling: it is editorial, not matcher-derived (open
   question 5). Proposed: keep it, label the panel honestly ("Coalition
   (editorial)" or rename), do not imply measurement.
10. `/narratives/map`: retire now, rebuild later as a coalition map if wanted
    (open question 2 — proposed: retire).
11. Redirect policy for 260 v1 ids: hand-map only the top ~30 by old event
    count to v2 successors, blanket-301 the rest to `/narratives` (proposed).

**DG-3 — before documents-layer content ships (P7) and before drops (P8)**
12. Pilot organ set approval (~13 sources, `ukraine_war_theater` + `iran_theater`).
13. Statement enrichment prompt sign-off (Rule 9 — prompts are business logic).
14. Review workflow: CLI listing vs minimal admin page (spec default: CLI).
15. Final confirmation to DROP v1 tables (destructive, cascade-checked,
    stated row counts — house rule).

### Phases

| # | Phase | Deliverable | Verification | Needs |
|---|---|---|---|---|
| **P0** | Research artifacts (read-only, no schema) | (a) mechanical archetype clustering script + report over active `narratives_v2` grouped by `(sign(stance), actor_centroids overlap, FN region)`; (b) draft `db/registry/narrative_meta_mapping.yaml`; (c) thin-narrative triage report (71 zero-match rows classified: bad publisher bloc / dead vocab / genuinely silent); (d) v1↔v2 id collision check + draft redirect map | Human review of all four artifacts | — |
| **P1** | Schema + reconcile | Migration adding `meta_narrative_id`, `meta_secondary_ids`, `coalition` to `narratives_v2` (via `safe_db_migrate.py`); `db/registry/coalitions.yaml`; reconcile script (registry → column, idempotent, Rule 8) | Every active narrative over the publication threshold has a primary meta and a coalition; reconcile re-run is a no-op | DG-0 |
| **P2** | Derived event links + provenance | `event_narratives_v2` derived table (§5.3) + builder hooked into the `fn_refresh` slot after `link_titles`; `matched_keywords` capture in `bootstrap_friction_node.py:link_titles` if DG-1 says yes | Derived per-narrative event counts reconcile with FN-page `match_count` logic for both atomic and theater paths; full rebuild is idempotent | DG-1 |
| **P3** | Materializers | `mv_narratives_v2_landing` + `mv_narrative_v2_detail`, adapted from the v1 materializers (`materialize_narratives_landing.py` / `materialize_narrative_detail.py` are the templates); weekly timeline (same shape as `friction-nodes.ts:510`) baked into the detail blob; daemon hook after `fn_refresh`, 12h staleness gate | MV blobs contain every §5.1 field for both locales; spot-check 5 narratives against live queries | P1, P2 |
| **P4** | Landing + meta pages | `/narratives` and `/narratives/meta/[id]` rebuilt on the new MVs; publication gate live; "low signal" muted band; empty-meta honest rendering; v1 rows `is_active = false` | Pages render from MV only (no live v1 reads); DE parity; gated narratives not linked, `noindex` | P3 |
| **P5** | Standalone narrative page | `/narratives/[id]` per §5.2: header, sidebar (meta / FN / coalition cards), sibling panel, stance strip (reuse `FrictionNodeNarrativeBricks`), coalition rail, headlines, derived events; Primary Sources block built to degrade to absent | Every §5.1 field renders; gate + redirect behavior for thin narratives; theater pages per DG-2 #7 | DG-2, P3 |
| **P6** | Cross-surface re-point + redirects | Event badges → `event_narratives_v2` counts; centroid section, trending badge, comparative analysis re-pointed; v1 URL redirects per DG-2 #11 | Zero remaining frontend reads of `strategic_narratives` / `event_strategic_narratives` (grep-verified) | P2, P5 |
| **P7** | Official documents layer — greenfield build (per `OFFICIAL_DOCUMENTS_LAYER.md`, Phase 1 statements pilot) | **P7a** tables migration + `official_sources_statements.yaml` + reconcile; **P7b** `scripts/fetch_official_documents.py` (RSS/listing, `ON CONFLICT (url) DO NOTHING`, manual-first); **P7c** statement enrichment prompt + pending-review CLI; **P7d** Primary Sources block wired on P5 pages + claim-evolution flags surfaced as a review queue (never auto-editing `claim_en`) | Pilot sources fetch idempotently; enriched rows land `pending`; only `published` renders; a narrative page with zero documents is visually unchanged | DG-3 #12–14; P1 (needs `coalition`); independent of P3–P6, can run in parallel after P1 |
| **P8** | v1 retirement | One full release with v1 tables inactive but present; then drop `strategic_narratives`, `event_strategic_narratives`, `narrative_weekly_activity`, both v1 MVs; retire daemon Phases 4.2f/g/h + the five v1 pipeline scripts; archive `narrative_taxonomy*.yaml` | Cascade blast radius printed and confirmed; daemon cycle green without the retired phases | DG-3 #15, P6 shipped + one release soak |

**Parallelism:** P7 is independent of the page rebuild after P1 — run it
alongside P3–P6 if wanted. Everything else is sequential as ordered.

DE parity is not a phase. Every field above ships `_en` + `_de` from the start,
per house rule — `meta_narratives`, `narratives_v2`, and `friction_nodes` are
all already fully bilingual, so the only new translation surface is UI strings.

---

## 9. Decision log entries this implies

Next free id is **D-095**.

- **D-095** — `narratives_v2` is the single narrative entity; v1 strategic
  narratives retired as unfalsifiable against the corpus.
- **D-096** — meta-narrative attaches per narrative (not per FN); primary +
  secondary; mapping lives in a git registry.
- **D-097** — event↔narrative links are *derived* from title attribution, never
  separately matched.
- **D-098** — standalone narrative pages are gated at ≥25 attributed titles;
  below that a narrative exists only as an FN card.
- **D-099** — `coalition` added to `narratives_v2` as the join key to
  `official_sources.coalition`.

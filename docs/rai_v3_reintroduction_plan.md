# RAI v3 Reintroduction Plan -- Narrative Analysis on WorldBrief

Status: PLAN ONLY (2026-07-09). No implementation started.
Engine: `apps/frontend/lib/rai-engine-v3.ts` (28 tension-pair premises, 18 modules,
Stage 0 skew calibration). Philosophy documented in
`book/new_material/framework_v3_adjustments.md`.

## Goal

Re-introduce on-demand RAI analysis, v1 scope = friction-node narratives only
(e.g. the two competing narratives on `/friction-nodes/western_aid_to_ukraine`).
Each narrative has a short title (`name_en`) and a full claim (`claim_en`) --
static content, so analysis reports may be stored indefinitely and served stale.

## Core principles

1. **On-demand only.** No daemon phase, no batch. Analysis runs when a user asks.
2. **Auth-gated now, paywall-ready.** NextAuth v5 session required (existing
   pattern in `api/user-analyse`). Gate check isolated in one helper so the
   future paywall is a one-function change.
3. **Generate once, serve forever.** First requester pays the latency; the report
   is stored and served to every later viewer (cache-first, existing
   `rai-analyse-comparative` pattern). Static narratives = stale reports are fine.
4. **Reuse, don't rebuild.** `entity_analyses` table, `/analysis/*` page patterns,
   DeepSeek caller and parsers from `rai-engine.ts`, translate route for DE.
5. **Versioned engine.** Every report records `engine_version` + `model` so
   framework upgrades can regenerate selectively instead of guessing.
6. **DE from the start.** `entity_analyses` already has `sections_de` etc.;
   narrative claims already exist in DE. On-demand translate button, same as
   comparative analysis.

## What exists (verified 2026-07-09)

- **`entity_analyses`** -- shared analysis store. `(entity_type, entity_id)`
  UNIQUE; `sections` (JSON text), `scores` (jsonb), `synthesis`, `blind_spots`,
  `conflicts` + `_de` variants; `user_id`, `input_text`, `title` (used by
  `user_input` rows). Current rows: 7 `event`, 1 `user_input`.
- **`narratives_v2`** -- FN narratives. `id` is a TEXT slug
  (`aid_sustains_defense`), `name_en/de`, `claim_en/de`, `stance_label_en/de`,
  `framing_keywords`, `publishers`, `fn_id` -> `friction_nodes`.
  `title_narratives` junction gives attributed headlines per narrative.
- **API patterns** -- `api/rai-analyse-comparative/route.ts` (cache-first,
  internal-key bypass, entity analysis), `api/user-analyse/route.ts`
  (auth-gated POST + user history GET).
- **Pages** -- `/analysis/comparative/[entity_type]/[entity_id]`,
  `/analysis/user/[id]`, FN page components
  (`FrictionNodeNarrativeCards` renders title + full claim per narrative).
- **Engine v3** -- prompt builders exist (`buildUserInputPrompt`,
  `buildAnalysisPrompt`); DeepSeek caller + response parsers live in
  `rai-engine.ts` and are imported, not duplicated.

## Gaps to close

1. **Type mismatch:** `entity_analyses.entity_id` is `uuid`; narrative IDs are
   text slugs. Fix: `ALTER COLUMN entity_id TYPE text USING entity_id::text`
   (8 existing rows cast cleanly; no FKs; verified). One migration, run via
   `scripts/safe_db_migrate.py` (per migration-cascade-safety rule).
2. **No user<->shared-analysis link.** `user_id` on `entity_analyses` only fits
   private `user_input` rows. Shared narrative reports need a junction so BOTH
   the generator and later viewers get it on their profile:
   `user_analysis_history (user_id, analysis_id FK entity_analyses, role
   'generated'|'viewed', created_at)`. Small, genuinely new content -- justified
   new table.
3. **No engine metadata.** Add `engine_version text`, `model text` to
   `entity_analyses` (2-column expansion of existing table, per schema
   preference).
4. **v3 has no narrative-claim prompt builder.** Add
   `buildNarrativeClaimPrompt(narrative, fnContext, modules, coverage)` to v3:
   claim text + stance label + FN context + coverage stats (see opportunity 2).

## Implementation phases

### Phase 1 -- Migration (1 file)
- `entity_analyses.entity_id` uuid -> text; add `engine_version`, `model`.
- Create `user_analysis_history` + index on `(user_id, created_at DESC)`.
- Run locally via safe_db_migrate.py; Render sync per DB-sync safety protocol
  (pause, confirm, COPY pattern if data involved -- here DDL only).

### Phase 2 -- Engine wiring
- `buildNarrativeClaimPrompt` in rai-engine-v3.ts. Inputs: `narratives_v2` row
  (claim, stance label, framing keywords), parent FN (name, description),
  coverage stats derived from `title_narratives` (publisher list, match counts,
  both-narratives share -- feeds Stage 0 skew estimate with REAL data).
- Module selection: FN narratives carry no track labels -> use fallback set
  initially; map `friction_nodes.kind` -> label keys later if useful.

### Phase 3 -- API route `api/narrative-analyse`
- POST `{ narrative_id }`: auth -> load narrative + FN -> cache check
  `(entity_type='fn_narrative', entity_id=narrative_id)` -> on miss: build
  prompt, `callDeepSeek` (reuse caller/parsers from rai-engine.ts), INSERT with
  `ON CONFLICT (entity_type, entity_id) DO NOTHING` then re-read (single-flight
  guard against two users clicking simultaneously) -> upsert
  `user_analysis_history` for the requester (role per cache hit/miss).
- GET: list current user's history (profile feed).
- `maxDuration = 180`, input validated against narratives_v2 (no free text).

### Phase 4 -- UI
- FN page: "RAI Analysis" button per narrative card. If a report exists, show
  "View analysis" state for everyone (badge doubles as social proof).
  Signed-out users see the button -> sign-in prompt (paywall funnel later).
- Report page `/[locale]/analysis/narrative/[narrative_id]` -- reuse the
  comparative report rendering (sections, scores, skew line, blind spots) with
  DE translate button.
- Profile: extend the user analyses list to include `user_analysis_history`
  entries alongside `user_input` ones.
- All new UI strings EN + DE from day one.

### Phase 5 -- Rollout
- FN pages are still shadow (`IS_SHADOW`, noindex) -- natural soft-launch venue.
- Verify: run both `western_aid_to_ukraine` narratives end-to-end; check skew
  line, `null_hypothesis_wins` population, DE translation, second-user cache
  path, profile listing.
- Render deploy manual (no git-push auto-deploy).

## Opportunities (proposals beyond the ask)

1. **Node-level comparative report (recommend as v1.1, high value).** The real
   product on an FN page is not two isolated claim analyses -- it is the RAI
   comparison of the competing narratives (convergence, divergence, collective
   blind spots). `buildComparativePrompt` already exists for stance clusters;
   an FN variant is cheap once per-narrative works. Store as
   `entity_type='friction_node', entity_id=fn_id`.
2. **Real coverage stats into Stage 0.** `title_narratives` + `publishers`
   give per-narrative amplification data. Feeding actual publisher/volume
   asymmetry into the skew estimate makes v3's calibration data-driven --
   something the standalone RAI never had. This is WorldBrief's unfair
   advantage over generic LLM analysis; lead with it.
3. **Surface `environment_skew` + `null_hypothesis_wins` as UI chips.** These
   are the framework's differentiators; don't bury them in prose. A "SKEW:
   HIGH" chip on a report is instantly legible and brandable.
4. **Report footer = paywall funnel.** Shared stale reports are free marketing:
   "Analysis generated by RAI v3 -- run your own analysis" CTA for signed-out
   viewers.
5. **Regeneration policy.** UNIQUE(entity_type, entity_id) means one report per
   narrative. When engine_version bumps, an internal-key `force` regeneration
   (existing pattern) refreshes flagship FNs; old report is overwritten. If
   history matters later, relax to UNIQUE(entity_type, entity_id,
   engine_version).
6. **Reader feedback loop.** Thumbs up/down + optional one-liner per report ->
   calibration data for the probe battery; cheap now, valuable when tuning
   premise wording.
7. **Probe battery doubles as QA.** The differential test harness (vanilla vs
   v2 vs v3) planned for framework validation can run against these same
   narratives -- one investment, two uses.
8. **Per-user rate limit** (e.g. N fresh generations/day) -- trivial with
   `user_analysis_history`, and it is the natural free-tier boundary when the
   paywall lands.

## Open questions (user decision)

1. v1 ships per-narrative analysis only, or per-narrative + node-level
   comparative together? (Recommend: per-narrative first, comparative as fast
   follow -- it reuses everything.)
2. Should existing v2-engine `event` analyses coexist untouched? (Recommend:
   yes -- different entity_type, no interference.)
3. Anonymous visibility: can signed-out users READ existing reports (funnel,
   opportunity 4), or is viewing also gated? (Recommend: existing reports
   readable, generation gated.)

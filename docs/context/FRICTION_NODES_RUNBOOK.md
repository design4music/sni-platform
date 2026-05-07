# Friction Nodes Runbook

How to add a new friction node end-to-end. Assumes the architecture
described in `out/concept_friction_nodes_and_narratives_v2.md` and the
schema from the `db/migrations/20260507_friction_nodes_v2*.sql` series.

## Mental model

A friction node is a curated, atomic, contested phenomenon. It has:

- **Phenomenology fields** — name, description, editorial summary, the
  centroids it manifests in, and topic keywords that scope FN-relevance.
- **An event-FN gate** — three keyword arrays
  (`event_actor_markers`, `event_topic_markers`, `event_title_anchors`)
  that decide which `events_v3` rows substantively belong to this FN.
  Logic: title matches `(any actor) AND (any topic) OR (any anchor)`.
- **Linked narratives** — the coalitions framing this contest, attached
  via `friction_node_narratives` with a stance label and display order.

Narratives are reusable across friction nodes:
`eu_diplomatic_preservation_norm` lives once in `narratives_v2` and is
linked to every FN where the EU plays the diplomatic-preservation role.

## Steps to add a new FN

### 1. Curate the FN entry

Decide:
- `id` (slug, e.g. `taiwan_status`)
- `name_en` / `name_de`
- `description_en` / `description_de` — what's contested, in 2-3 sentences
- `editorial_summary_en` / `editorial_summary_de` — 1-2 paragraphs of
  strategic context, who the players are, recent shifts
- `centroid_ids` — centroids where this manifests
  (e.g. `[ASIA-CHINA, ASIA-TAIWAN, AMERICAS-USA, ASIA-JAPAN]`)
- `topic_keywords` — neutral terms used to scope title attribution
  (e.g. `[Taiwan, Taipei, Taiwan Strait, Lai Ching-te, ADIZ, Pelosi Taiwan]`)
- `event_actor_markers` — Iran-marker analog
  (e.g. `[Taiwan, Taipei, Tsai, Lai]`)
- `event_topic_markers` — domain words
  (e.g. `[strait, sovereignty, reunification, PLA exercise, ADIZ, Pelosi visit]`)
- `event_title_anchors` — phrases that alone qualify an event
  (e.g. `[Taiwan Strait crisis, Pelosi Taiwan, Lai Ching-te]`)

Write a SQL migration `db/migrations/<date>_friction_node_<slug>.sql`
with `INSERT INTO friction_nodes (...)`. Apply locally.

### 2. Decide which narratives apply

Cross-reference your FN against the existing `narratives_v2` library.
For Taiwan you'd probably want:

- `west_china_strategic_competition` (existing — to be drafted in v2)
- `china_alternative_order` (existing — partially drafted)
- `multipolar_systemic_alternative` (existing) — China-Russia anti-Western frame
- A new `china_taiwan_reunification_doctrine` (new — Beijing-side all-in)
- A new `taiwan_self_determination` (new — Taipei-side all-in)
- Potentially `eu_diplomatic_preservation_norm` (existing — applies wherever EU mediates)

For each *new* narrative:
- Draft in `out/<fn>_narrative_drafts.md` first (readable markdown)
- Insert into `narratives_v2` with `actor_centroids`, `tier`, `narrative_type`
  (`all_in` vs `stand_by`), `framing_keywords`, `topic_keywords`,
  `claim_en` / `claim_de`, `publishers`, `editorial_organ_publishers`
- Run `python scripts/calibrate_narrative_keywords.py
   --narrative <id> --publishers "<comma-list>"` to surface vocabulary
  the analyst draft missed
- Curate the calibration output into framing_keyword updates

For each *existing* narrative reused on this FN, no narrative change
needed — just the link.

### 3. Link narratives to the FN

```sql
INSERT INTO friction_node_narratives
    (fn_id, narrative_id, stance_label_en, stance_label_de, display_order)
VALUES
    ('taiwan_status', 'china_taiwan_reunification_doctrine',
     'Reunification mandate', 'Wiedervereinigungs-Mandat', 1),
    ('taiwan_status', 'taiwan_self_determination',
     'Sovereign self-determination', 'Souveraene Selbstbestimmung', 2),
    ...;
```

`display_order` controls both the brick row order and the colour slot
(see `apps/frontend/lib/friction-nodes-shared.ts` `NARRATIVE_COLORS`).

### 4. Run the bootstrap

```bash
python scripts/bootstrap_friction_node.py --fn-id taiwan_status
```

This:
- Reads the FN config (event-title gate, topic_keywords)
- Reads the linked narratives + their publishers + editorial organs
- DELETEs existing event_friction_nodes for the FN
- DELETEs existing title_narratives for the FN's narratives
- INSERTs the new attribution sets
- Prints per-narrative match counts

If a narrative gets 0 matches, run the calibration helper (step 2) to
diagnose. Common causes:
- Publishers not in the corpus (check `publishers` array against actual
  `titles_v3.publisher_name` values)
- Framing keywords too specific (calibration will surface what they
  *do* say in headlines)
- FN topic_keywords too tight (the title-narrative attribution requires
  FN-topic match)

### 5. Sanity-check the page

```
http://localhost:3000/friction-nodes/<slug>
http://localhost:3000/de/friction-nodes/<slug>
```

Look for:
- Brick row colors and stance labels match expectations
- Activity chart shows credible weekly distribution
- Event volume bars in "Events per week" surface real on-topic events
- Narrative card sample headlines are on-frame for each coalition
- Country pills resolve (no raw centroid IDs visible)

If the editorial summary needs editing:
```sql
UPDATE friction_nodes SET
  editorial_summary_en = '...', editorial_summary_de = '...', updated_at = now()
WHERE id = 'taiwan_status';
```

After editing on Render, bust the cache:
```bash
curl -X POST https://www.worldbrief.info/api/admin/revalidate-cache \
  -H "x-revalidate-token: $REVALIDATE_API_KEY" \
  -d '{"prefix":"fn"}'
```

## Deploying a new FN to Render

1. `git push` your migration files + any narrative drafts
2. Run the migration on Render:
   ```sql
   \i db/migrations/<date>_friction_node_<slug>.sql
   ```
3. Run the bootstrap on Render:
   ```bash
   python scripts/bootstrap_friction_node.py --fn-id <slug>
   ```
   (Or if you don't want to run Python on Render, copy+paste the
    bootstrap's INSERT statements after running locally.)
4. Bust the frontend cache (curl above)

## Promoting from shadow route to main navigation

When the FN architecture is stable enough to expose:

1. In `apps/frontend/app/[locale]/friction-nodes/[slug]/page.tsx`,
   flip `const IS_SHADOW = true` to `false`. This:
   - Removes the in-page amber "shadow route" notice
   - Removes the `noindex, nofollow` robots override
2. Add a "Friction Nodes" link to main `Navigation.tsx`
3. Build a `/friction-nodes` index page (lists all active FNs, similar
   to `/narratives`)
4. Optionally: register the FN URLs in `app/sitemap.ts` so search
   engines find them
5. Also flip the footer link from "Friction Nodes (preview)" to plain
   "Friction Nodes" in `messages/en.json` + `messages/de.json`

## Pipeline integration (later)

Currently event_friction_nodes + title_narratives are populated by the
manual bootstrap. To make them live:

- Add a daemon slot that runs `bootstrap_friction_node.py --fn-id <id>`
  for every active FN nightly (or whenever the underlying titles/events
  change materially)
- Or wire the bootstrap logic into the existing pipeline phases so new
  titles get attributed at ingest time

The bootstrap script is idempotent and re-runnable — re-running on
fresh data is the main scaling concern, not correctness.

## Files

| Concern | File |
|---|---|
| Schema | `db/migrations/20260507_friction_nodes_v2.sql` plus follow-on `20260507_friction_nodes_v2_*.sql` |
| Generic bootstrap | `scripts/bootstrap_friction_node.py` |
| Calibration helper | `scripts/calibrate_narrative_keywords.py` |
| Frontend page | `apps/frontend/app/[locale]/friction-nodes/[slug]/page.tsx` |
| Server queries | `apps/frontend/lib/friction-nodes.ts` |
| Client-safe types + colours | `apps/frontend/lib/friction-nodes-shared.ts` |
| Components | `apps/frontend/components/friction-nodes/` |
| Concept doc | `out/concept_friction_nodes_and_narratives_v2.md` |

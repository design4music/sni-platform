# Friction Nodes Runbook

How to add a new friction node end-to-end. Reflects the architecture
as of **2026-05-12** (1-to-1 narrative<->FN collapse, theater pattern,
5-step stance scale).

## Mental model

The Friction Node layer maps the contested geopolitical surface in
three tiers:

```
Theater FN (catch-all)            iran_theater
   |
   +-- Atomic FN (specific)       iran_nuclear_program
   |     |
   |     +-- Narrative (pro)      iran_nuclear_sovereign_right     stance=+2
   |     +-- Narrative (con)      west_iran_nuclear_threat         stance=-2
   |
   +-- Atomic FN                  iran_proxy_network
   |     +-- ...
   |
   +-- Atomic FN                  strait_of_hormuz_sovereignty
   |     +-- ...
   |
   +-- Atomic FN                  gulf_attacks_on_arab_states
   |     +-- ...
```

- **Theater FN** (`fn_type='theater'`) — umbrella grouping of atomic
  FNs that share a geopolitical surface. Carries broad-scope narratives
  that don't belong to any single atomic FN (e.g. EU diplomatic
  engagement, multipolar sovereignty backing). Acts as a *catch-all*:
  titles already attributed to any atomic FN's narrative are excluded
  from theater attribution.
- **Atomic FN** (`fn_type='atomic'`) — single contested phenomenon.
  Usually carries one pro-side and one anti-side narrative.
- **Narrative** — 1-to-1 with an FN (`narratives_v2.fn_id`). Each
  narrative carries its own FN-specific prose, publisher cohort,
  framing vocabulary, and stance integer (-2..+2).

### Why 1-to-1?

The legacy join table (`friction_node_narratives`) allowed many-to-many.
We collapsed to 1-to-1 on 2026-05-12 because:

- Cross-FN narratives forced generic prose; FN-specific prose reads
  better and gives the analyst more control.
- Disambiguation between FNs no longer needs the framing-keyword gate:
  publisher cohort + the FN's own anchor bundle is enough.
- Schema is leaner — `narrative_type`, `tier`, `topic_keywords`,
  `editorial_organ_publishers`, `scope_centroid_ids`, `notes_*` all
  retired.

A future meta-narrative layer may reconnect narratives across FNs at a
higher level of abstraction. That's outside this runbook.

### Data model (current)

```
friction_nodes
  id text PK
  name_en/de, description_en/de, editorial_summary_en/de
  centroid_ids text[]            actor scope; titles must overlap
  fn_type text                   'atomic' | 'theater'
  member_fn_ids text[]           theater only — atomic FN ids it bundles
  is_active, display_order, timestamps

narratives_v2
  id text PK
  fn_id text FK -> friction_nodes.id     1-to-1
  display_order int                       order within FN
  name_en/de, claim_en/de
  actor_centroids text[]                  countries carrying this stance
  publishers text[]                       outlets editorially aligned
  framing_keywords text[]                 used for sample-title ranking + UI vocabulary chip (NOT for attribution)
  stance smallint                         -2..+2, mirrors outlet_entity_stance.stance
  stance_label_en/de text                 short label shown on the brick
  is_active, timestamps

taxonomy_v3 (fn_anchor row per FN)
  taxonomy_function = 'fn_anchor'
  linked_id = friction_nodes.id
  aliases jsonb                           {ar:[...], de:[...], en:[...], ...}
                                          multi-lingual surface vocab the FN matches

title_narratives (derived, bootstrap-populated)
  title_id uuid FK -> titles_v3
  narrative_id text FK -> narratives_v2

event_friction_nodes (derived, bootstrap-populated)
  event_id uuid FK -> events_v3
  fn_id text FK -> friction_nodes
```

### Attribution rules (what bootstrap does)

**Event -> FN** (`event_friction_nodes`):
- Event is `is_promoted = true` and not merged
- Within window (default 180 days)
- Some member title overlaps `friction_nodes.centroid_ids`
- Event's canonical title matches any alias in the FN's `fn_anchor`
  taxonomy_v3 bundle

**Title -> narrative** (`title_narratives`):
- `titles_v3.publisher_name` in `narratives_v2.publishers`
- Within window
- `titles_v3.centroid_ids` overlaps `friction_nodes.centroid_ids`
- `titles_v3.title_display` matches any alias in the FN's `fn_anchor`
  bundle
- For `fn_type='theater'`: the title is NOT already attributed to any
  narrative on any atomic FN (catch-all semantics)

`framing_keywords` are explicitly *not* an attribution filter under the
1-to-1 model — they exist to rank sample titles and populate the
"Loaded vocabulary" UI chip.

### Stance scale + palette

`narratives_v2.stance` is a smallint -2..+2, mirroring
`outlet_entity_stance.stance`. The frontend colour function
(`apps/frontend/lib/friction-nodes-shared.ts:colorForNarrative`) maps:

| stance | hue | meaning |
|---|---|---|
| -2 | `#b91c1c` red-700 | strong criticism (regime-change, existential threat) |
| -1 | `#ef4444` red-500 | criticism (legal / normative) |
|  0 | `#71717a` zinc-500 | mixed / neutral (e.g. EU "engage and criticise") |
| +1 | `#10b981` emerald-500 | support (outside backing, qualified) |
| +2 | `#15803d` green-700 | strong support (full sovereign defence) |

## Steps to add a new FN

### 1. Curate the FN row

Decide:
- `id` (slug — e.g. `taiwan_status` or, if it's an umbrella for several
  atomic FNs, `taiwan_theater` with `fn_type='theater'`)
- `name_en` / `name_de`
- `description_en` / `description_de` — what's contested, 2-3 sentences
- `editorial_summary_en` / `editorial_summary_de` — 1-2 paragraphs of
  strategic context
- `centroid_ids` — centroids where this manifests (e.g.
  `[ASIA-CHINA, ASIA-TAIWAN, AMERICAS-USA, ASIA-JAPAN]`)
- `fn_type` — `'atomic'` (default) or `'theater'`
- `member_fn_ids` — theater only: list of atomic FN ids it bundles

Write a SQL migration `db/migrations/<date>_friction_node_<slug>.sql`
with `INSERT INTO friction_nodes (...)`. Apply locally.

### 2. Create the fn_anchor taxonomy_v3 bundle

Each FN needs one `taxonomy_v3` row with `taxonomy_function='fn_anchor'`
and `linked_id=<fn.id>`. The `aliases` jsonb is multi-lingual:

```json
{
  "ar": ["...", "..."],
  "de": ["...", "..."],
  "en": ["Taiwan Strait", "ADIZ incursion", "Lai Ching-te", "..."],
  "es": [...], "fr": [...], "hi": [...], "it": [...],
  "ja": [...], "ru": [...], "zh": [...]
}
```

Use the deepseek anchor extractor if you don't have one already drafted
(`scripts/extract_fn_anchor_via_deepseek.py`). Aliases are matched as
case-insensitive `ILIKE '%alias%'` against `title_display`.

Insert via migration:
```sql
INSERT INTO taxonomy_v3 (item_raw, aliases, is_active, taxonomy_function, linked_id)
VALUES ('<fn_id> fn_anchor', '<json>'::jsonb, true, 'fn_anchor', '<fn_id>');
```

### 3. Curate the narratives (1 per stance side)

For most atomic FNs you'll want a pro/con pair; theaters often carry
a wider set (e.g. iran_theater carries 4: regime-change criticism,
sovereign defence, EU mixed, multipolar backing).

For each narrative, write the `INSERT INTO narratives_v2` directly:

```sql
INSERT INTO narratives_v2 (
    id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de,
    actor_centroids, publishers, framing_keywords, is_active
) VALUES (
    'taiwan_self_determination',
    'taiwan_status', 1, 2,                              -- stance +2 = strong support
    'Sovereign self-determination', 'Souveraene Selbstbestimmung',
    'Taiwan-aligned: self-determination...',
    'Taiwan-orientiert: Selbstbestimmung...',
    'Full claim text (EN)...',
    'Vollstaendige Behauptung (DE)...',
    ARRAY['ASIA-TAIWAN','AMERICAS-USA','ASIA-JAPAN'],
    ARRAY['Taipei Times','Focus Taiwan','Liberty Times','...'],
    ARRAY['self-determination','sovereignty','democratic Taiwan','...'],
    true
);
```

Optional but recommended:
- Run `python scripts/calibrate_narrative_keywords.py
   --narrative <id> --publishers "<comma-list>"` to discover vocabulary
  the analyst draft missed → add to `framing_keywords`.

### 4. Run the bootstrap

```bash
python scripts/bootstrap_friction_node.py --fn-id taiwan_status
```

This:
- Reads `friction_nodes.centroid_ids` + the fn_anchor bundle
- Reads all `narratives_v2` rows for this fn_id
- DELETEs existing `event_friction_nodes` for the FN
- DELETEs existing `title_narratives` for the FN's narratives
- INSERTs the new attribution sets
- Prints per-narrative match counts

For `fn_type='theater'`, the event step is skipped (theaters have no
events directly — events live on the bundled atomic FNs) and title
attribution uses the catch-all exclusion (titles claimed by atomic
FNs first).

### 5. Sanity-check the page

```
http://localhost:3001/en/friction-nodes/<slug>
http://localhost:3001/de/friction-nodes/<slug>
```

Look for:
- Brick row hues match expected stance (red-700 / red-500 / zinc /
  emerald / green-700)
- Activity chart shows credible weekly distribution
- "Events per week" surfaces real on-topic events
- Narrative card sample headlines read on-frame
- Country pills resolve (no raw centroid IDs visible)
- For theater: "Specific conflicts in this zone" lists member atomic FNs

### 6. Deploy to Render

1. `git push` your migration files.
2. Apply the migration on Render:
   ```bash
   docker run --rm -e PGPASSWORD=$RENDER_DB_PASSWORD postgres:18 psql \
     -h $RENDER_DB_HOST -U $RENDER_DB_USER -d sni_v2 \
     -f db/migrations/<date>_friction_node_<slug>.sql
   ```
3. Run the bootstrap against Render:
   ```bash
   DB_HOST=$RENDER_DB_HOST DB_USER=$RENDER_DB_USER \
   DB_PASSWORD=$RENDER_DB_PASSWORD DB_NAME=sni_v2 \
     python scripts/bootstrap_friction_node.py --fn-id <slug>
   ```
4. Bust the frontend cache:
   ```bash
   curl -X POST https://www.worldbrief.info/api/admin/revalidate-cache \
     -H "x-revalidate-token: $REVALIDATE_API_KEY"
   ```

## Common diagnosis (low attribution)

If a narrative attributes 0 or far fewer titles than expected, walk the
gate step-by-step in psql:

```sql
WITH n  AS (SELECT publishers FROM narratives_v2 WHERE id='<narrative_id>'),
     fn AS (SELECT centroid_ids FROM friction_nodes WHERE id='<fn_id>'),
     ta AS (SELECT aliases FROM taxonomy_v3 WHERE taxonomy_function='fn_anchor' AND linked_id='<fn_id>' AND is_active),
     af AS (SELECT array_agg(a) arr FROM ta, jsonb_each(ta.aliases) lang, jsonb_array_elements_text(lang.value) a)
SELECT 'A. publisher gate'      AS step, COUNT(*) FROM titles_v3 t, n
  WHERE t.pubdate_utc > NOW() - INTERVAL '180 days' AND t.publisher_name = ANY(n.publishers)
UNION ALL SELECT 'B. + centroid', COUNT(*) FROM titles_v3 t, n, fn
  WHERE t.pubdate_utc > NOW() - INTERVAL '180 days' AND t.publisher_name = ANY(n.publishers)
    AND t.centroid_ids && fn.centroid_ids
UNION ALL SELECT 'C. + fn_anchor alias', COUNT(*) FROM titles_v3 t, n, fn, af
  WHERE t.pubdate_utc > NOW() - INTERVAL '180 days' AND t.publisher_name = ANY(n.publishers)
    AND t.centroid_ids && fn.centroid_ids
    AND EXISTS (SELECT 1 FROM unnest(af.arr) kw WHERE t.title_display ILIKE '%' || kw || '%');
```

The biggest drop reveals the bottleneck. Common causes:
- **Publishers not in corpus**: cross-check against
  `SELECT DISTINCT publisher_name FROM titles_v3 WHERE pubdate_utc > NOW() - INTERVAL '180 days'`.
- **centroid_ids too narrow**: many headlines mention the FN's actor
  in a story dominated by other centroids — widen `friction_nodes.centroid_ids`.
- **fn_anchor bundle too tight**: extract more aliases via deepseek
  against actual headlines.

## Promoting from shadow route to main navigation

When the FN architecture is stable enough to expose:

1. In `apps/frontend/app/[locale]/friction-nodes/[slug]/page.tsx`,
   flip `const IS_SHADOW = true` to `false`. Removes the `noindex,
   nofollow` robots override on metadata.
2. Add a "Conflicts" link to main `Navigation.tsx`.
3. Build a `/friction-nodes` index page listing active FNs (group by
   theater).
4. Register URLs in `app/sitemap.ts`.
5. Update i18n footer link from "preview" to plain "Conflicts" in
   `messages/en.json` + `messages/de.json`.

## Files

| Concern | File |
|---|---|
| Schema (consolidated) | `db/migrations/20260512_narratives_v2_*.sql` (collapse + 5-step + drops) |
| fn_anchor pattern | `db/migrations/20260511_taxonomy_v3_add_taxonomy_function_and_linked_id.sql` |
| Bootstrap | `scripts/bootstrap_friction_node.py` |
| Calibration helper | `scripts/calibrate_narrative_keywords.py` |
| Anchor extractor | `scripts/extract_fn_anchor_via_deepseek.py` |
| **fn_anchor drafting rules** | [`FN_ANCHOR_VOCABULARY_SPEC.md`](FN_ANCHOR_VOCABULARY_SPEC.md) — read before hand-editing any bundle |
| Frontend page | `apps/frontend/app/[locale]/friction-nodes/[slug]/page.tsx` |
| Server queries | `apps/frontend/lib/friction-nodes.ts` |
| Client-safe types + palette | `apps/frontend/lib/friction-nodes-shared.ts` |
| Components | `apps/frontend/components/friction-nodes/` |

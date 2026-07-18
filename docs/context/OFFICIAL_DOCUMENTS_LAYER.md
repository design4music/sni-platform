# Official Documents Layer -- Unified Spec

Status: approved design, 2026-07-10. Ready for implementation.
Supersedes the storage section (2) of `docs/regulatory_layer_concept.md`;
every other section of that doc (frontend identity, coming-into-force
timeline, integration points, out-of-scope discipline) remains in force
and applies to this layer. Companion: the narrative-sources discussion
is recorded in the decision log entry for this date.

## 1. Principle: two regimes, not three layers

WorldBrief ingests exactly two kinds of source material:

| | Regime A: mass media | Regime B: authoritative documents |
|---|---|---|
| Tables | `feeds` -> `titles_v3` -> `events_v3` | `official_sources` -> `official_documents` |
| Volume | thousands/day, redundant | tens/week, unique |
| Truth status | reports (we assert the report) | the source IS the fact |
| Value creation | clustering into events | interpretation + extraction |
| Machinery | dedup, clustering, importance | relevance gate, enrichment, review |

Regime B serves two document classes through one infrastructure,
discriminated by `doc_class`:

- **`regulatory`** -- gazettes, sanctions lists, tariff schedules.
  Signal: the rules changed. (Full rationale: `regulatory_layer_concept.md`.)
- **`statement`** -- UNSC speeches, MFA statements, presidential
  addresses, doctrine documents, official op-eds. Signal: this is what a
  coalition actually asserts. Statements are the *substance* layer of
  theater-level narratives; media headlines remain only the *propagation*
  meter (echo volume per outlet cohort). Theater narratives are not
  sourced from catch-all headline residue.

Every row of the regulatory concept's "inverted semantics" table holds
for both classes -- that identity is why they share infrastructure.

Future document classes (think-tank reports, central-bank communiques,
party manifestos) are a `doc_class` value plus an enrichment prompt, not
an architecture decision.

## 2. Storage

Two tables. No news machinery (clustering, dedup, importance) touches
these rows. **No `ON DELETE CASCADE` anywhere** (house rule, D-091).

```sql
CREATE TABLE official_sources (
    id                text PRIMARY KEY,          -- slug, permanent (registry convention)
    source_class      text NOT NULL CHECK (source_class IN ('regulatory','statement')),
    name_en           text NOT NULL,
    org               text NOT NULL,             -- issuing authority / institution
    url               text NOT NULL UNIQUE,      -- listing page or RSS endpoint
    fetch_format      text NOT NULL CHECK (fetch_format IN ('rss','html_listing')),
    language_code     varchar(5) NOT NULL,
    jurisdiction      text,                      -- regulatory only (DE, EU, US, ...)
    actor_centroid    text,                      -- statement only: centroids_v3 id of the speaking actor
    coalition         text,                      -- statement only: ru | ua | west_us | west_eu | iran | multilateral | ...
    fetch_interval_hours integer NOT NULL DEFAULT 24,
    is_active         boolean NOT NULL DEFAULT true,
    etag              text,                      -- fetch state, same mechanics as feeds
    last_modified     text,
    last_run_at       timestamptz,
    notes             text,                      -- source anchoring: why this source is on the list
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE official_documents (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id         text NOT NULL REFERENCES official_sources(id),
    doc_class         text NOT NULL CHECK (doc_class IN ('regulatory','statement')),
    url               text NOT NULL UNIQUE,      -- canonical link; uniqueness = idempotency key
    title             text NOT NULL,
    published_date    date,
    retrieved_at      timestamptz NOT NULL DEFAULT now(),
    language_code     varchar(5),
    summary_en        text,                      -- plain-language one-liner (enrichment)
    summary_de        text,                      -- DE from the start (house rule)
    centroid_ids      text[] NOT NULL DEFAULT '{}',   -- universal join surface
    fn_id             text REFERENCES friction_nodes(id),
    narrative_id      text REFERENCES narratives_v2(id),
    -- regulatory-class fields (NULL for statements):
    effective_date    date,
    lifecycle_status  text CHECK (lifecycle_status IN
                        ('draft','adopted','in_force','amended','repealed')),
    official_ref      text,                      -- CELEX number, BGBl citation, S/PV record no.
    -- statement-class fields (NULL for regulatory):
    speaker           text,
    quotes            jsonb,                     -- [{"quote": "...", "note": "..."}]
    claims            jsonb,                     -- ["claim 1", "claim 2", ...] as extracted
    -- shared tail:
    meta              jsonb NOT NULL DEFAULT '{}',
    review_status     text NOT NULL DEFAULT 'pending'
                        CHECK (review_status IN ('pending','published','rejected')),
    reviewed_at       timestamptz
);

CREATE INDEX idx_offdocs_class_date ON official_documents (doc_class, published_date DESC);
CREATE INDEX idx_offdocs_fn        ON official_documents (fn_id) WHERE fn_id IS NOT NULL;
CREATE INDEX idx_offdocs_narrative ON official_documents (narrative_id) WHERE narrative_id IS NOT NULL;
CREATE INDEX idx_offdocs_pending   ON official_documents (review_status) WHERE review_status = 'pending';
CREATE INDEX idx_offdocs_centroids ON official_documents USING gin (centroid_ids);
```

Typed-column rule: a field earns a typed column only when we filter or
sort by it (`effective_date`, `narrative_id`, `lifecycle_status`);
everything else stays in `meta` until proven otherwise.

## 3. Source registry (YAML -> DB)

Same pattern as the asset registry: YAML in `db/registry/` is the single
source of truth, generated into `official_sources` by a reconcile script
(match by permanent `id`; never edit the table directly). Fetch-state
columns (`etag`, `last_modified`, `last_run_at`) are owned by the
fetcher and preserved on reconcile.

Files:
- `db/registry/official_sources_statements.yaml`
- `db/registry/official_sources_regulatory.yaml`

Registry conventions inherited from `db/registry/README.md`: permanent
snake_case ids, ASCII only, every row carries a `notes` line anchoring
why the source qualifies (the analog of `ranking_source`). Symmetry rule
for statements: every coalition carrying a narrative in `narratives_v2`
gets its official organs listed -- no narrative may be evidence-starved
by registry omission.

## 4. Pipeline

One script, `scripts/fetch_official_documents.py`, manual-first (daemon
slot only after the pilot proves out; daily cadence when it lands).

1. **Fetch**: for each active source due per `fetch_interval_hours`,
   pull the RSS/listing page, extract item URLs + titles + dates.
   `INSERT ... ON CONFLICT (url) DO NOTHING` -- idempotent, re-runnable.
2. **Relevance gate** (regulatory class only, title-level, cheap model):
   drop administrative minutiae before enrichment
   (think-before-scaling). Statements skip the gate -- registry
   curation IS the gate at tens/week volume.
3. **Enrichment** (cheap model; two prompts, deliberately NOT merged --
   they encode different business logic, Rule 9):
   - regulatory: domain + jurisdiction + instrument type,
     effective date, centroid/commodity/asset mapping, one-liner EN+DE.
   - statement: FN + narrative mapping, speaker, 1-3 verbatim quotes,
     claim list, and a flag for claims not yet present in the
     narrative's claim structure (narrative-evolution signal).
4. **Review**: everything lands `pending`. Human review promotes to
   `published` (or `rejected`). v1 review surface: CLI listing or a
   minimal admin page -- not a build project. Only `published` rows
   render on the frontend.

Model tiering: fetch and storage are mechanical (no LLM); gate +
enrichment run on the cheap tier; nothing here needs a frontier model.

## 5. Frontend integration

Inherited unchanged from the two concept docs:

- Regulatory: country-page rail, coming-into-force timeline, brief
  section, lens/watchlist hooks (`regulatory_layer_concept.md` section 4-5).
- Statements: theater narrative cards lead with a "Primary sources"
  block -- dated statements with speaker, quotes, link -- and the
  existing headline samples demote to a "media echo" strip. The
  three-way screen (what the law says / what officials assert / how
  media frames it) is the differentiating product surface.
- Both classes keep distinct visual identity; never interleaved with
  news cards.

## 6. Phasing

1. **Phase 1 -- infrastructure + statements pilot.** Tables, registry
   generator, fetch script, statement enrichment prompt. Pilot scope:
   `ukraine_war_theater` + `iran_theater` organ sets (~13 sources).
   Validates the shared infrastructure with the simplest document class
   and directly feeds the in-progress theater narrative review.
2. **Phase 2 -- regulatory class.** BGBl + EUR-Lex OJ L sources,
   relevance gate, regulatory enrichment prompt, country-page rail.
   (Swap with Phase 1 is safe if partner pull demands it -- the
   infrastructure is shared by design.)
3. **Phase 3 -- scale + integration.** Top 10-20 actors' organ sets,
   daemon slot, sanctions-list substream driving asset/flow status with
   citations, statement-claims feeding narrative claim evolution,
   news<->document cross-links.

## 7. Deliberately not unified

- The two enrichment prompts (different business logic).
- Lifecycle vocabulary (legal draft/in-force/repealed means nothing for
  a speech; statements are simply dated).
- `feeds` stays as-is; no migration of the news pipeline onto this
  layer, ever -- the regimes are inverted by nature.

## 8. Out of scope

Verbatim from the regulatory concept: no full legal-text analysis, no
amendment graphs, nothing resembling legal advice; classify, summarize,
date, map, link to the authoritative source. For statements
additionally: we record what officials assert, attributed and dated --
assertion is not endorsement; the stance/framing analysis stays in the
narrative layer where it belongs.

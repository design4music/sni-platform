# Regulatory Data Layer: Architecture Concept

Status: concept draft, 2026-07-07. Companion to
`intelligence_dashboards_concept.md` (personas, product surfaces) and
`fn_map_data_sources.md` (provenance discipline). Trigger: regulatory
data (German/EU law, sanctions, tariffs) confirmed as high-relevance by a
prospective design partner (KWS conversation).

## 1. Principle: inverted semantics

Regulation is not news, and the architecture must honor the inversion:

| Axis | News (existing pipeline) | Regulatory |
|---|---|---|
| Volume | thousands/day, redundant | a handful/day, unique |
| Truth status | reports (we assert the report) | the source IS the fact (gazette = ground truth) |
| Value creation | clustering many articles into one event | interpretation: legalese -> who is affected, from when |
| Time axis | published = happened | published != in force (often future-dated) |
| Lifecycle | ephemeral attention | draft -> adopted -> in force -> amended -> repealed |
| Signal type | attention / pressure | state change |

Consequence: **separate ingestion, separate storage, separate
presentation -- joined at the entity layer** (centroids, commodities,
assets, flows), the same join surface everything else in WorldBrief uses.

## 2. Storage

**New table `regulatory_items`** -- not rows in titles/events. The house
rule (prefer extending existing tables with a kind discriminator) has an
escape clause for genuinely different content schemas, and this qualifies:
jurisdiction, instrument_type (law / ordinance / EU regulation / directive
/ decision), lifecycle status, effective_date distinct from
published_date, official identifier (BGBl citation, CELEX number),
canonical link to authoritative text. None of the news machinery
(clustering, dedup, importance) may touch these rows.

Supporting pieces:
- **`regulatory_sources`** registry (feed URL, authority, jurisdiction,
  kind) -- the analog of the feeds table, deliberately NOT mixed into the
  media outlets table. Adding a jurisdiction later = a row, not a project.
- Entity mapping via the existing house pattern: `centroid_ids[]`,
  commodity slugs, `affected_asset_ids[]` arrays (same as friction_nodes).
- Cross-links to news events (Phase 3) as a link table: event -> reg item
  ("media reaction to this law").

## 3. Pipeline (thin, cheap, separate slot)

- **Daily cadence**, own small slot. Gazettes publish daily; no 12h
  pressure. Volume is tiny (BGBl: a few items/day).
- **Relevance gate first** (think-before-scaling): title-level LLM filter
  for business relevance (trade, sanctions, tariffs, export control, agri,
  energy, chemicals, data). Most gazette items (pension adjustments,
  administrative minutiae) drop here, before any deeper processing.
- **Enrichment pass** (where the value lives): classify domain +
  jurisdiction + instrument type; extract effective date; map to
  centroids/commodities/assets; write a plain-language one-liner EN + DE.
  ("Zweite Verordnung zur Aenderung der Aussenwirtschaftsverordnung" ->
  "Germany tightens export-control licensing for dual-use goods; in force
  Sept 1.")
- **v1 scope: title + metadata + link out.** No full-text legal parsing;
  the authoritative text stays at the source, we summarize and link.

Initial sources: BGBl Teil I RSS (recht.bund.de) + EUR-Lex Official
Journal L-series. Next candidates via registry: EU consolidated sanctions
list, OFAC, UK OFSI, Federal Register, TARIC (tariffs), WTO notifications.

## 4. Frontend: distinct identity

Regulatory items get their own visual class -- a paragraph-sign glyph,
distinct card style, never anonymously interleaved with news. A news card
shows attention (counts, glow); a regulatory card shows authority and
dates: issuer, instrument type, published, **in force**.

Placement (by value):
1. **Country/centroid pages** -- "Regulatory" rail per jurisdiction.
2. **"Coming into force" timeline** -- the killer feature; regulation is
   the only stream that shows the FUTURE. "What takes effect in the next
   90 days touching your watchlist." Natural fit for the day-centric
   calendar UI. Core value for the strategic-planning persona.
3. **Briefs** -- separate "Regulatory developments" section in daily/
   weekly briefs; never blended into event prose.
4. **Commodity/asset lenses** -- mapped regs surface on lens pages (EU
   deforestation regulation -> cocoa/soy belts; export controls -> fabs).
5. **Watchlist alerts** -- regulatory triggers are MORE alertable than
   news: discrete, dated, actionable.

## 5. Meaningful incorporation (the two big integration points)

1. **Regulation as codified state-change in the pressure chain.**
   asset_flows.status currently reflects reporting. A sanctions regulation
   can drive that status with a legal citation attached: "suspended, per
   Council Regulation (EU) XXXX, in force since <date>". Parts of the map
   upgrade from *reported* to *codified*. News pressure = attention is
   rising; regulatory item = the rules actually changed. The map learns to
   distinguish weather from law.
2. **The law vs. the narrative.** Link news coverage OF a regulation to
   the regulation itself (keyword/CELEX matching; LLM judge for
   ambiguity). A country or theater page then shows: what the law says
   (plain-language summary of the authoritative text) next to how
   different media systems frame it. For the KWS gene-editing/NGT file,
   this is the entire product in one screen. No incumbent offers it.

## 6. Phasing

1. **Phase 1:** BGBl + EUR-Lex feeds -> regulatory_sources +
   regulatory_items -> relevance gate + EN/DE enrichment -> country-page
   rail + brief section.
2. **Phase 2:** entity mapping (centroids/commodities/assets) -> lens and
   watchlist integration + coming-into-force timeline.
3. **Phase 3:** sanctions lists as structured sub-stream driving
   flow/asset status flags with citations; news<->regulation cross-links
   (media reaction to a law).

## 7. Out of scope (deliberately)

- Full legal-text analysis or amendment/consolidation graphs.
- Anything resembling legal advice. We classify, summarize, date, map,
  and always link to the authoritative source. The disclaimer discipline
  from the asset layer applies verbatim: transparent, sourced, honest
  about what we are (an editorial intelligence layer over official
  publications, not counsel).

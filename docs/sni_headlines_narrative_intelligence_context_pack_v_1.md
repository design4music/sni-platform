# SNI: Headlines | Narrative Intelligence

**Status:** Draft (context for LLM collaborators; exploratory, not a hard spec)\
04.09.2025 - v.1

---

## 1) Project snapshot

- **Concept:** Build a lean, multilingual system that turns *news headlines only* (no scraping) into **Events** and **Framed Narratives**, then rolls them up into **Arcs**.
- **Why:** Reveal how meaning is manufactured. We don’t average viewpoints; we place **competing framings** side‑by‑side for the same episode.
- **Source:** Google News RSS (per domain). Posibly other RSS feeds and XML sitemaps. We link to Google News URLs for humans; we do not unwrap/visit publisher pages.
- **Scope:** MVP/garage scale. Initial backfill ≈ **10,000** headlines; daily flow **≤ 500**.
- **Languages:** Multilingual tolerant; realistically **80% EN** to start. The pipeline must not break on non‑EN.
- **Data granularity:** **Titles-only** (optional short RSS description if present).

---

## 2) Purpose & north star

- **North star:** Make **strategic narratives** legible: who frames what, how, and why it matters now.
- **User promise:** Expose **alternative framings** for the same event, with neutral shared facts and clickable sources. **Arcs** surface the main (trending) processes driving global politics over time by linking all related Events into a coherent, navigable storyline.
- **Success looks like:** Coherent Event pages with 1–2 strong Framed Narrative cards; Arc pages that connect episodes without mushy blending.

> **Practical stance:** The goal isn’t to achieve a mythical “objective” state; it’s to forensically diagram the landscape of competing subjectivities. SNI doesn’t combat propaganda; it dissects it—and it doesn’t eliminate bias; it catalogs and contrasts it.

## 3) Editorial values

- **No fake neutrality.** We publish **competing framings** rather than a synthetic middle.
- **Evidence discipline.** Event “shared facts” = **intersection** across member headlines; anything else lives in framing.
- **Transparency.** Every narrative cites actual headlines (IDs/domains) and lists its lexical cues (verbs/hedges/evaluatives).
- **Caution over invention.** Inputs‑only. No backstory, numbers, or causes that aren’t in the titles.

### 3.1 Generative freedom policy (where writing is allowed)

- **EF shared\_facts:** Inputs-only. Use intersection facts supported by *all* titles in the bucket. No backstory, numbers, causal chains, or new actors.
- **Narrative theses (1–2 sentences):** You **may write in your own words** to summarize how the headlines **frame** the same event differently. Use attribution/hedging (e.g., “headlines frame…”, “is cast as…”, “according to X”). Tie claims to visible **lexicon markers** (verbs/hedges/evaluatives) present in the titles.
- **Arc theses (1–2 sentences):** You **may generalize** across multiple Events to name a recurring pattern. Stay abstract (roles, legitimacy, intent, norms). Do **not** introduce new facts or assert inter-event causality unless a headline states it.
- **Style:** Short, neutral, analytic. Avoid flourish. Prefer “framed as / presented as / cast as” over declaratives.
- **If uncertain:** Say so briefly (“titles diverge on intent/legitimacy”), or return one narrative instead of two.

**Examples (good):**

- *FN thesis:* “Sources allied with A **frame** the measure as rule-based accountability, while sources aligned with B **cast** it as politicized interference.”
- *Arc thesis:* “Across these events, headlines **recur** on a split between stability-maintenance claims and sovereignty-defense claims.”

**Examples (bad):**

- “The measure caused a 30% drop…” (no numbers in titles)
- “This definitively proves…” (no hard proof language)

---

## 4) Core concepts (entities)

- **Event Family (EF):** Neutral description of an episode/phase (actors, mechanism, time, place) plus **1–3 shared facts** true for all items.
- **Framed Narrative (FN):** A distinct storyline **about the same EF**, defined by its **framing vector** (roles, cause, legitimacy, intent, solution, norms/salience, temporal). Usually 1 per EF; create 2 when framing materially diverges.
- **Structural Arc (SA):** Optional umbrella that links multiple EFs via a recurring storyline pattern (e.g., “Technology’s dark unintended consequences”).

> Working unit formula: **Narrative = Event × Framing**. Arcs connect many Events.

---

## 5) Source & ingestion constraints

- **Only Google News RSS.** Uniform XML; legal to link; stable.
- **Stored fields per item:** `title_original, title_display, url_gnews, publisher_name, publisher_domain, pubdate_utc, lang, content_hash` (+ housekeeping).
- **Normalization:** Unicode NFKC → lowercase for `title_norm`; strip trailing “ – Publisher” when it exactly matches `<source>`; **collapse internal whitespace**; and drop non‑informative emoji/symbols to avoid clustering artifacts.

---

## 6) Architecture & workflow (high level)

### Phase CLUST — Preparation (deterministic)

1. **Ingest & normalize** (titles‑only; idempotent; UTC dates).
2. **Strategic gate v2 (lightweight, explicit):**
   - **Keep** items with **(a)** a recognized country/major‑org actor *or* **(b)** semantic proximity ≥ **0.70** to *strategic anchors* (sanctions, strikes, court, elections, diplomacy, cyber, energy, platform governance).
   - **Exclude** obvious non‑strategic domains (sports/celebs/local crime/entertainment) unless an anchor is present.
   - **Output** a gate **confidence score** per item for metrics; prefer minimal false negatives over false positives.
3. **Big‑bucket grouping (pick one or combine; non‑exclusive options):**
   - **Actor‑set buckets (preferred for MVP):** bucket by top actor set (e.g., `US–China–Taiwan`) within a 24–48h window.
   - **Embedding clustering:** HDBSCAN/agglomerative on title embeddings per day, tuned for **few, large** clusters.
4. **Critical guardrail (when applicable):** For `sanctions / export_controls / strike_airstrike / platform_ban`, enforce **issuer → instrument → target** uniformity; mixed triples must be split.
5. **De‑dup inside bucket:** collapse near‑identical titles (cosine ≥ 0.95 or trigram/Jaccard).
6. **Prepare bucket payload:** header + up to **100** representative items (cap total prompt to **≤ 8k tokens**); log token/cost estimates per bucket for budgeting.

### Phase GEN — Generation (LLM, one pass per bucket)

- Input: a **bucket**. Output: **one EF** + **1–2 FNs** (with `why_different` if 2), plus lexicon markers and representative sources/IDs.
- Hard guards: inputs‑only; shared‑facts = intersection; do not mix issuer/target inside guarded mechanisms.
- **Writing freedom:** You may compose 1–2 sentence theses for narratives and arcs in your own words, **but**: (a) ground them in the provided headlines and their lexicon markers; (b) use hedging/attribution (“is framed as”, “headlines describe”); (c) do **not** add new facts, numbers, actors, or backstory beyond the titles.

### Phase MERGE — Cross‑feed/batch reconciliation

- **Auto‑merge** same events using a **narrative fingerprint**: `(actor_set + mechanism + geo_hint + date±1)` and **cosine ≥ 0.85** on title embeddings between cluster centroids.
- **Tiny compare** prompt only for ambiguous pairs (“merge or distinct?”). Minimal LLM load.

### Phase ARC — Optional roll‑up — Optional roll‑up

- Deterministic candidateing (recurring actors/mechanisms) → small LLM labeler to name the Arc & link **all** member events (full connection graph), optionally flagging 2–3 *featured* events for UI previews.
  - The Arc stores the **complete list of member Event IDs** (full connection set).
  - UI can render all members via grouping (by year/actor/mechanism), filters & search, a small featured strip, and **lazy‑load/timeline** for very large sets.

---

## 7) Methods library (options, not commitments)

- **Embeddings:** English first (MiniLM). **Thresholds (locked for MVP):** cosine **0.95** (dupe collapse), **0.60** (bucket membership to centroid), **0.85** (MERGE event fingerprint). Optional multilingual later.
- **Cosine thresholds:** 0.95 (dupe collapse); \~0.60 (bucket membership to centroid). Tunable.
- **NER:** Enable spaCy **EN/DE/ES/FR/RU/ZH** (small models to start); add IT later if useful. For **HI (Hindi)** use wrappers (spacy‑stanza / spacy‑udpipe). Treat NER as **optional enrichment**, not a blocker.
  - **Posture for MVP:** **Do not use NER for clustering.** Use alias‑list string matching to detect actor sets; run NER only for guarded checks/labels.
  - **Why add RU/ZH:** vital coverage where English sources are sparse; improves actor extraction for “muted giants.”
  - **Tradeoffs:** larger container size & memory, slower cold‑starts, extra CPU per item (especially if we ever use *md/lg/trf* models), and occasional headline ambiguity. Mitigation: **language‑router**, **lazy‑load per language**, **batch inference**, and **use NER only where it matters** (issuer→target guard; bucket labels).
- **Actor canonicalization:** Minimal alias sheet → canonical IDs (ISO for states; Wikidata QIDs for orgs). Grow slowly.
- **Mechanism label:** **MVP Core‑20** frozen set + \`\` fallback. Classify by similarity to 2–3 English anchor phrases per label; below threshold routes to `unspecified`. (Full extended list remains in Appendix B for future use).
- **Language stance (Phase‑1):** Target **EN/DE/ES/FR/RU/ZH**; pipeline must not break on others. **Language detection:** lightweight detector; if low confidence, set `lang=null` (don’t block).

---

## 8) Minimal data model (bare bones)

> Just what the MVP needs; we can extend later.

**items**

- `item_id` (pk), `content_hash` (unique), `title_original`, `title_display`, `url_gnews`, `publisher_name`, `publisher_domain`, `publisher_country_code` (nullable, heuristic), `pubdate_utc`, `lang`, `feed_url`, `ingested_at`

**buckets**

- `bucket_id` (pk), `date_window_start`, `date_window_end`, `top_actors` (json array of canonical IDs), `mechanism_hint` (nullable), `members_count`, `members_checksum`, `created_at`

**events**

- `event_id` (pk), `bucket_id` (fk), `version` (int), `title_neutral`, `shared_facts` (json array), `actors` (json), `mechanism`, `time_window` (json), `geography` (json), `categories` (json), `consistency_note`, `created_at`

**narratives**

- `narrative_id` (pk), `event_id` (fk), `version` (int), `title`, `thesis`, `framing_vector` (json), `lexicon_markers` (json), `representative_sources` (json), `representative_headlines` (json), `why_different` (nullable)

**arcs**

- `arc_id` (pk), `version` (int), `title`, `thesis`, `framing_pattern` (json), `member_event_ids` (json array of `event_id`), `featured_event_ids` (json array, nullable), `created_at`

> Notes:
>
> - Arcs **materialize** long‑lived storylines. Store the **full connection set** in `member_event_ids`. Use `featured_event_ids` only for UI previews.
> - *(Optional normalization later)* If you need relational queries at scale, add an `arc_events` table: `arc_id` (fk), `event_id` (fk). For the MVP we keep arrays for simplicity.

**runs**

- `run_id` (pk), `phase` (enum: ingest|clust1|gen1|merge|arc), `prompt_version`, `input_ref` (e.g., bucket\_id list or hash), `output_ref` (blob/json), `created_at`

> We intentionally skip many joins and histories for MVP. Provenance lives in `runs`.

---

## 9) JSON exchange formats (essentials)

**Bucket → GEN‑1 (input)**

```
{
  "bucket_header": {
    "bucket_id": "B-2025-09-01-US-CN-TW",
    "date_window": "2025-08-31..2025-09-02",
    "top_actors": ["US","CN","TW"],
    "mechanism_hint": "",
    "members_count": 146,
    "members_checksum": "a84c1e...",
    "note": "issuer/target guard n/a"
  },
  "examples": [
    "h001 | 2025-09-01 | reuters.com | en | US says Taiwan partnership remains a cornerstone of stability | https://news.google.com/...",
    "h017 | 2025-09-01 | globaltimes.cn | en | US 'interference' in Taiwan is a dangerous provocation, warns Beijing | https://news.google.com/..."
  ]
}
```

**GEN‑1 → Event + Narratives (output)**

```
{
  "event": {
    "title_neutral": "...",
    "shared_facts": ["...","..."],
    "actors": ["..."],
    "mechanism": "sanctions | strike_airstrike | summit_meeting | diplomatic_statement | court_ruling | regulation_policy | aid_package | election | protest_unrest | cyber_operation | energy_supply | natural_disaster | platform_ban | unspecified",
    "time_window": {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"},
    "geography": ["..."],
    "categories": ["Politics"],
    "consistency_note": "..."
  },
  "narratives": [
    {
      "title": "...",
      "thesis": "...",
      "framing_vector": {"roles":"...","cause":"...","legitimacy":"...","intent":"...","solution":"...","norms_or_salience":"...","temporal":"..."},
      "lexicon_markers": {"verbs":["..."],"hedges":["..."],"evaluatives":["..."]},
      "representative_sources": ["reuters.com","rt.com"],
      "representative_headlines": ["h001","h017"]
    }
  ],
  "why_different": "roles + legitimacy + intent"  // include only if two narratives
}
```

---

## 10) Milestones (small, safe steps)

1. **Step‑1 ingest** (idempotent) for 10–20 feeds; dry run twice; idempotency proven.
2. **CLUST‑1 buckets** (actor‑set per 24–48h) with de‑dup + issuer/target guard.
3. **GEN‑1** on 5–10 buckets; inspect Event/Narrative clarity; tweak guardrails only.
4. **MERGE** index + tiny compare prompt; verify Reuters ↔ RT overlaps merge cleanly.
5. **First UI:** Event cards → Event detail with Narrative cards (no Arcs yet).
6. **Scale‑up:** add feeds; run bulk backfill, then daily trickle.

---

## 11) Open questions (intentionally unresolved)

- Do we keep **mechanism labels** frozen forever, or allow a rare new label?
- How big should a bucket get before we split by time or actor subset?
- When do we promote a roll‑up to a **Structural Arc** vs keeping it implicit in navigation?
- What minimal **explanatory snippets** (RSS descriptions vs model paraphrases) best “decorate” Event/Narrative cards without drifting into article text?

---

## 12) Risks & mitigations

- **Bad blends (e.g., mixed sanctions).** Mitigation: issuer→instrument→target guard; shared‑facts intersection only.
- **Token/length limits.** Mitigation: examples cap (≤100); echo counts+checksum instead of full lists.
- **Language brittleness.** Mitigation: English‑first tools, but multilingual‑tolerant logic; optional spaCy NER per language later.
- **Scope creep.** Mitigation: greenfield repo + minimal tables; feature‑flag UI.

---

## 13) Glossary (quick)

- **EF:** Event Family (neutral episode).
- **FN:** Framed Narrative (storyline about an EF; may have alternatives).
- **SA:** Structural Arc (broad umbrella linking many EFs).
- **Bucket:** Deterministic pre‑LLM pile of similar titles.

#

## 14) Examples

### 14.1 Example Event Family (EF)

**EF-01 — Neutral record**

- **title\_neutral:** US–Taiwan partnership statement and Beijing response
- **shared\_facts:**
  - A senior US official described the US–Taiwan relationship as a “cornerstone of stability.”
  - Beijing issued a warning, calling US involvement a “dangerous provocation.”
- **actors:** United States, Taiwan, China
- **mechanism:** diplomatic\_statement
- **time\_window:** {start: "2025-09-01", end: "2025-09-02"}
- **geography:** ["Indo-Pacific"]
- **categories:** ["Politics"]
- **consistency\_note:** Items consistently describe paired statements (US affirmation; PRC warning).

---

### 14.2 Framed Narratives (FNs) for EF-01

**FN-A (stability framing)**

- **title:** Reaffirming a stabilizing partnership
- **thesis:** The US presents its Taiwan ties as a steadying factor that supports regional balance and predictability.
- **framing\_vector (snapshot):**
  - roles: US/Taiwan as partners; China as challenger
  - cause: strategic balance
  - legitimacy: lawful partnership / status quo support
  - intent: preserve stability
  - solution: continued engagement
  - norms\_or\_salience: stability, deterrence
  - temporal: continuity
- **lexicon\_markers:** verbs:[“remains”, “reaffirms”]; hedges:[]; evaluatives:[“cornerstone of stability”]
- **representative\_sources:** ["state.gov","reuters.com"]
- **representative\_headlines:** ["h001","h009"]

**FN-B (provocation framing)**

- **title:** Warning against sovereignty violations
- **thesis:** Beijing casts US–Taiwan engagement as illegitimate interference that heightens risk.
- **framing\_vector (snapshot):**
  - roles: US as intervener; China as sovereign; Taiwan as subject of interference
  - cause: foreign meddling
  - legitimacy: violation of sovereignty
  - intent: provoke / contain China
  - solution: cessation of US involvement
  - norms\_or\_salience: non-interference, risk
  - temporal: escalation risk
- **lexicon\_markers:** verbs:[“warns”]; hedges:[]; evaluatives:[“dangerous provocation”]
- **representative\_sources:** ["globaltimes.cn"]
- **representative\_headlines:** ["h017"]

**why\_different:** roles + legitimacy + intent.

---

### 14.3 Example Event Family (EF) — sanctions (shows issuer→instrument→target discipline)

**EF-02 — Neutral record**

- **title\_neutral:** Belgium announces sanctions on Israel
- **shared\_facts:**
  - Belgian authorities announced a sanctions measure targeting Israel.
- **actors:** Belgium, Israel
- **mechanism:** sanctions
- **time\_window:** {start: "2025-08-30", end: "2025-08-30"}
- **geography:** ["Belgium","Israel"]
- **categories:** ["Politics"]
- **consistency\_note:** Single issuer→target pair maintained.

**FN-A (accountability frame)**

- **title:** Sanctions as accountability for policy conduct
- **thesis:** Measures are framed as a lawful, values-based response intended to influence behavior.
- **framing\_vector (snapshot):** roles: Belgium as rule-setter; Israel as target; legitimacy: rule-of-law; intent: pressure for compliance; solution: sanctions enforcement; norms: human-rights/rule-based; temporal: immediate action.
- **lexicon\_markers:** verbs:[“announces”]; hedges:[“officially”]; evaluatives:[“measure”]
- **representative\_sources:** ["europa.eu","apnews.com"]
- **representative\_headlines:** ["h201","h205"]

**FN-B (illegitimacy frame)**

- **title:** Politicized measures that undermine sovereignty
- **thesis:** Sanctions depicted as biased interference that damages legitimate security policy.
- **framing\_vector (snapshot):** roles: EU actor as politicized; Israel as unfairly targeted; legitimacy: contested/illegitimate; intent: punish/pressure; solution: reject or counter-measures; norms: sovereignty; temporal: contested.
- **lexicon\_markers:** verbs:[“condemns”]; hedges:[“claims”]; evaluatives:[“politicized”]
- **representative\_sources:** ["rt.com","jpost.com"]
- **representative\_headlines:** ["h212","h218"]

> **Note:** “US presses EU to sanction India” and “India rejects US Iran sanctions” must be **separate EFs** (different issuer/target). An Arc could later relate them.

---

### 14.4 Structural Arc (SA) example

**SA-01 — Great Power Diplomacy: Cooperation & Friction**

- **thesis:** The US engages in simultaneous cooperation on global goods and confrontation over regional security, producing recurring tension in narrative framing.
- **framing\_pattern (summary):**
  - roles: US as central actor; peers/rivals (China, Russia, regional actors) respond
  - cause: competing strategic interests
  - legitimacy: contested across cases
  - intent: stability vs containment
  - solution: working groups, deterrence, sanctions, statements
  - norms\_or\_salience: rules-based order vs sovereignty
- **representative\_events:** ["EF-01 (US–Taiwan statements)","EF-02 (Belgium→sanctions→Israel)","EF-03 (US/EU aid posture on Ukraine)"]
- **example\_headlines:** ["h001","h017","h205","h303"]

**Alternative Arc (counter-pattern):**\
**SA-02 — Multipolar Realignment**

- **thesis:** Non-Western coalitions emphasize sovereignty and alternative institutions to dilute Western centrality, framing Western measures as interference.
- **representative\_events:** ["EF-01","EF-02","EF-X (SCO/BRICS summit episode)"]

---

*This document is meant to be edited, annotated, and shared with other LLM collaborators (Claude Code, DeepSeek, etc.). Add comments, propose options, and strike out ideas—nothing here is locked until we say so.*

---

## Appendix C — Roadmap triage (from multi‑LLM feedback)

### Must do (implemented above / to wire in code)

- Strategic gate v2 with **actor/anchor** rule, **≥0.70** proximity, **exclusions** for non‑strategic domains, and an **item confidence score**.
- MERGE **narrative fingerprint** + **cosine ≥ 0.85** across batches.
- **Guarded mechanisms** hard rule: issuer→instrument→target uniformity; split mixed triples.
- **Mechanism size**: use **MVP Core‑20** + `unspecified` fallback; park the rest.
- **Embedding thresholds** locked: 0.95 (dupe), 0.60 (bucket), 0.85 (merge).
- **Bucket caps**: ≤100 examples and ≤8k tokens per GEN; log token/cost per bucket.
- **Publisher signal**: store `publisher_domain`; derive `publisher_country_code`.
- **Language stance**: target EN/DE/ES/FR/RU/ZH; pipeline must not break on others.
- **NER posture**: no NER in clustering; alias match first; NER only for guarded checks/labels.
- **DB/JSON hygiene**: add `version` to events/narratives/arcs; keep `consistency_note` in GEN output; normalization drops emojis/symbols.

### Can do (high‑value next)

- Write the strategic gate as a small, testable function; emit the confidence score.
- Add `unspecified_bucket` path when mechanism similarity < 0.6; quarterly taxonomy review.
- Enforce framing vector required fields (roles/legitimacy/intent) with light validation.
- 10% human spot‑check of GEN outputs; log error types.
- Arc promotion heuristic: (actor\_set + mechanism) recurs in ≥3 Events within 7–30 days.
- Combine cosine ≥0.95 with trigram/Jaccard for near‑identicals across languages.
- Add `source_diversity_score` (entropy over `publisher_domain`) to Events.
- UI ethics note about headline‑only limits; label narrative theses as AI‑generated.
- Language router & lazy‑load NER for guarded cases/bucket labels.

### Do later (Phase‑2/3)

- Auto‑canonicalization via Wikidata with human review queue.
- Localized mechanism display names (ES/FR/RU/ZH).
- Evaluate multilingual NER (Babelscape/WikiNEuRal, IndicNER) if volume justifies.
- Normalize Arcs to `arc_events` or graph index for very large sets.
- Optional sentiment/stance enrichers (kept out of shared facts).
- Token/cost dashboards and monthly budget alerts for GEN.
- Resilience: add domain‑topic Google News RSS or sitemaps as fallbacks.


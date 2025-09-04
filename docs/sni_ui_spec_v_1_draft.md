# SNI — UI Spec (v1 Draft)

**Status:** Draft for Figma‑driven build. Shapes backend contracts but stays implementation‑light. **Audience:** Designers, Claude Code (frontend), backend engineers. **Scope:** Headlines‑only SNI. Reuse your existing Figma prototype visual language where possible.

---

## 1) Product goals for UI

- Make **competing framings** legible at a glance.
- Let users **drill down**: Arc → Event → Framed Narrative → Sources.
- Keep it **fast** (headline‑only) and transparent (explicit sources & lexical cues).

**Design mantras**: minimum clicks to insight • no fake neutrality • clarity over ornament • accessible by default.

---

## 2) Information Architecture (routes)

- `/` **Home** — sectioned discovery landing (7 ribbons).
- `/category/:id` **Category index** — full‑height grid of cards (no horizontal scroll), filter panel.
- `/event/:eventId` **Event page** — neutral EF header + FN cards + timeline + sources + metadata.
- `/arc/:arcId` **Arc page** — umbrella storyline with many linked Events.
- `/search` **Search** — global search results (items, events, arcs).
- `/sources` **Sources** — publisher domains listing & drill‑through.
- `/about`, `/method`, `/glossary` — text pages.
- `/profile` *(future)* — saved filters, follows, personalization.

---

## 3) Home (7 ribbons)

Use your existing hero + 7 horizontally scrollable sections. Replace “Narrative cards” with **Event cards** (EFs). Sections map to **Categories**:

1. Featured Analysis *(editorial picks)*
2. Geopolitical Intelligence
3. Technology & Innovation
4. Environment & Climate
5. Social & Cultural Dynamics
6. Regional Focus *(region filtered)*
7. Historical Context *(older EFs or SAs)*

**Event Card (compact)**

- Title (neutral) — `event.title_neutral`
- One‑liner (shared facts collapsed to 1 sentence)
- Chips: **Mechanism**, **Top actors**, **Region**, **Updated Xh ago**
- Badges: **FN variants count** (1/2), **Trend** (up/flat/down), **Confidence** *(optional later)*
- Tap → `/event/:id`

Load more = arrow on ribbon; keyboard scroll; lazy‑load cells.

---

## 4) Category index

- Three‑column masonry grid of **Event cards (expanded)**.
- Top bar: query input + “Open Filters” button.
- Right‑side **Slide‑over filter panel** (your working prototype):
  - Geographic scope (multi‑select actors/regions)
  - Narrative type (has 2 FNs / has 1 FN)
  - Trending status (7‑day change by event count or mentions)
  - Time frame (date range)
  - Categories (checkboxes)
  - Narrative intent facets *(roles/legitimacy/intent keywords; optional later)*
- Sort: **Newest**, **Most discussed** (member\_headlines count), **Most contested** (framing\_disagreement), **Arc relevance**.

**Event Card (expanded)**

- Adds: tiny sparkline timeline, source diversity mini‑meter, representative sources (logos), and quick‑peek of FN titles (A/B).

---

## 5) Event page (EF)

**Header (neutral)**

- Title neutral, mechanism chip, actors (avatar chips with flags/logos), time window, geography chips.
- Shared facts list (1–3 bullet points).

**Framed Narrative cards (1–2)**

- Title + 1–2 sentence **thesis** (hedged, per policy).
- **Framing vector** table (roles, cause, legitimacy, intent, solution, norms, temporal).
- **Lexicon markers** (verbs/hedges/evaluatives) as inline chips.
- **Representative sources** (domain chips) + **headline IDs** (hover shows full title).
- `why_different` strip (if 2 FNs).

**Timeline**

- EF activity timeline (headline counts per day/week). Hover shows counts and top verb markers for that day.

**Turning points**

- Key peaks labeled using simple heuristics (peaks in activity; GEN note if present).

**Source distribution**

- Donut or bars: publishers by share; option to filter by source cluster.

**Source excerpts**

- Quote list: short excerpts from the RSS `description` (if present) or brief model paraphrases tied to specific headline IDs.

**Metadata**

- Language distribution of items, data quality note, bucket size, members checksum.

---

## 6) Arc page (SA)

**Header**

- Arc title + 1–2 sentence thesis (hedged).
- Pattern panel (roles, legitimacy, intent) summarized.

**Members**

- Large lists possible (hundreds). Render:
  - **Featured strip** (2–4 Events) — editorial or heuristic.
  - **Full list** grouped by **year → mechanism → actor set** with collapse/expand.
  - **Timeline** view option for Events (virtualized list; lazy‑load tiles).
  - Filters: actors, mechanisms, time.

**Why relations**

- Short explainer: why these Events are linked (pattern cues).

---

## 7) Search

- Single input, segmented results: **Events**, **Arcs**, **Sources**.
- Filters mirror category panel.
- Result cards reuse Event card components; Arcs show member count & featured tiles.

---

## 8) Sources page

- Table of publishers with: domain, country, volume, first/last seen, category distribution.
- Domain drill‑down → list of Events where it appears as representative source.

---

## 9) Component library (tokens)

- **Cards:** EventCardCompact, EventCardExpanded, NarrativeCard, ArcCard
- **Chips:** MechanismChip, ActorChip, RegionChip, SourceChip, LexiconChip
- **Graphs:** MiniSparkline, BarDonut (source distribution), ActivityTimeline
- **Panels:** FilterSlideOver, SourceExcerptList, MetadataBlock
- **Loaders:** SkeletonCard, SkeletonTimeline

**Styling**: Tailwind; reuse your Figma color‑coding per section; keep high contrast and AA minimum.

---

## 10) Data ↔ UI mapping (contracts)

### 10.1 EventCard (compact)

```
{
  id, title_neutral, mechanism, actors[], time_window, geography[],
  fn_variant_count, members_count, updated_at, rep_sources[]
}
```

- `fn_variant_count`: derived (# of narratives).
- `rep_sources`: top 2–3 domains from `representative_sources`.

### 10.2 NarrativeCard

```
{
  id, title, thesis,
  framing_vector:{roles,cause,legitimacy,intent,solution,norms_or_salience,temporal},
  lexicon_markers:{verbs[],hedges[],evaluatives[]},
  representative_sources[], representative_headlines[]
}
```

### 10.3 ArcCard

```
{ id, title, thesis, featured_event_ids[], member_count }
```

### 10.4 Filters payload (URL‑state)

```
{
  q, categories[], actors[], regions[], mechanisms[], timeframe:{start,end},
  contested?:boolean, sort?:"newest|discussed|contested|arc"
}
```

---

## 11) Minimal API surface (MVP)

*(These are read‑only, cached; map directly to your DB model.)*

- `GET /api/events?filters…` → paged list of EventCardCompact
- `GET /api/events/:id` → full Event + narratives + stats
- `GET /api/arcs?filters…` → list of ArcCard
- `GET /api/arcs/:id` → full Arc + paged member events
- `GET /api/sources?filters…` → publisher table
- `GET /api/search?q=…` → segmented results (events/arcs/sources)

**Pagination**: `page`, `page_size`, `next_cursor`. Use cursor for long Arc member lists.

**Caching**: stale‑while‑revalidate; edge cache for list endpoints.

---

## 12) State & performance

- **URL = state** for filters; no hidden local state for discoverability.
- **Virtualized lists** for long Event/Arc pages; infinite scroll or “Load more”.
- **Skeletons** during loads; optimistic UI only where idempotent.
- **Client search** on already‑loaded dataset allowed (your prototype behavior) but guard with server filters for large sets.

---

## 13) Accessibility

- Keyboardable ribbons and filter drawers.
- Color tokens meet WCAG AA; don’t rely on color alone to signal A/B framing.
- Descriptive aria‑labels on chips and graphs; focus traps in drawers.

---

## 14) Personalization (later)

- Auth module → saved filters, followed actors/mechanisms, “new contested EF” alerts.
- Local preferences: density, language, dark mode.

---

## 15) Frontend engineering guardrails

- **Stack**: React + Tailwind (+ shadcn/ui). Keep SSR option open (Next.js) for SEO later.
- **Data**: Strong types (TypeScript). Schema types generated from API.
- **State**: URL params + light client store (Zustand or Context); avoid global complexity.
- **Routing**: file‑system routes; guard against 404/empty states with friendly blanks.
- **Testing**: component tests for cards and filter panel; Cypress smoke flow.
- **Telemetry**: anonymous page/view events; measure ribbon CTR, filter apply rate, dwell time on FN cards.

---

## 16) Mapping the existing Figma

- Keep the hero + 7 ribbons layout.
- Replace narrative cards with **Event cards**; narrative cards live *inside* Event pages.
- The right slide‑over filter stays (wire to URL state; debounce 200ms).
- The dynamic timeline component can render minimal bars first; upgrade later.

---

## 17) Content examples (wire into mocks)

- Use section 14 examples from Context Pack to seed Event/Narrative mocks.
- Ensure at least one Arc demo with 50–200 member Events to test virtualization.

---

## 18) Open UI questions

- How to visualize **why\_different** succinctly on Event cards?
- Do we surface **source diversity** on cards or only on Event detail?
- Should “Featured Analysis” be human‑curated or heuristic (e.g., top contested this week)?



## 19) Figma → Code mapping (working table)

> I couldn’t load the live Figma site via the browser sandbox (it requires client‑side JS). Until we get an Inspect export or component list, here’s a ready‑to‑fill mapping that ties Figma components/tokens to our React/Tailwind code. Paste names/links and we’ll lock contracts.
>
> [https://false-patron-02026584.figma.site/](https://false-patron-02026584.figma.site/) - home page
>
> [https://false-patron-02026584.figma.site/narrative/SC-023-A](https://false-patron-02026584.figma.site/narrative/SC-023-A) - individual item page (Narrative → EF)
>
> [https://false-patron-02026584.figma.site/category/featured](https://false-patron-02026584.figma.site/category/featured) - category page

### 19.1 Design tokens → Tailwind config

| Token groupFigma style/variableTailwind mappingNotes |                                           |                                                           |                           |
| ---------------------------------------------------- | ----------------------------------------- | --------------------------------------------------------- | ------------------------- |
| Brand colors                                         | `Brand/Primary`, `Brand/Accent`           | `--color-brand`, `--color-accent` → `theme.extend.colors` | Keep AA contrast for text |
| Surfaces                                             | `Surface/0..3`                            | `--surface-0..3` → `bg-surface-0..3`                      | Map ribbons to surfaces   |
| Text                                                 | `Text/Heading`, `Text/Body`, `Text/Muted` | `--text-heading`, `--text-body`, `--text-muted`           | Heading/Body scale        |
| Spacing                                              | `Space/2..64`                             | `theme.spacing`                                           | Convert to `rem` scale    |
| Radius                                               | `Radius/sm..2xl`                          | `theme.extend.borderRadius`                               | Cards use `2xl`           |
| Shadows                                              | `Shadow/card`, `Shadow/overlay`           | `theme.extend.boxShadow`                                  | Soft depth only           |

**Action:** export Figma Variables JSON → we’ll generate a `tailwind.config.ts` snippet.

### 19.2 Components (Figma → React)

| Figma component       | Route/usage      | React component          | Props (data contract)                                                                                          |
| --------------------- | ---------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------- |
| `Card/Event/Compact`  | Home ribbons     | `<EventCardCompact />`   | `{ id, title_neutral, one_liner, mechanism, actors[], updated_at, fn_variant_count, rep_sources[] }`           |
| `Card/Event/Expanded` | Category grid    | `<EventCardExpanded />`  | `{ ...Compact, sparkline[], diversity_score? }`                                                                |
| `Card/Narrative`      | Event page       | `<NarrativeCard />`      | `{ id, title, thesis, framing_vector, lexicon_markers, representative_sources[], representative_headlines[] }` |
| `Card/Arc`            | Arc index        | `<ArcCard />`            | `{ id, title, thesis, featured_event_ids[], member_count }`                                                    |
| `Chip/Mechanism`      | Various          | `<MechanismChip />`      | `{ code, label }`                                                                                              |
| `Chip/Actor`          | Various          | `<ActorChip />`          | `{ id, label, flag? }`                                                                                         |
| `Graph/Timeline`      | Event, Arc       | `<ActivityTimeline />`   | `{ buckets:[{date,count}], highlights? }`                                                                      |
| `Graph/Donut`         | Event            | `<SourceDistribution />` | `{ domains:[{domain,share}] }`                                                                                 |
| `Drawer/Filters`      | Category, Search | `<FilterSlideOver />`    | `{ stateFromURL }`                                                                                             |

### 19.3 Interaction patterns

- **Ribbons**: horizontal scroll with wheel/trackpad + arrow buttons; snap to card; lazy‑load pages.
- **Drawer**: right slide‑over, 32px gutter; keyboard focus trap; `Esc` closes; updates **URL state** with debounce (200ms).
- **Cards**: entire card clickable; secondary actions (copy link) on hover/… menu.
- **Timelines**: hover tooltip shows day count and top verb markers.

### 19.4 Icons & motion

- Icons: lucide-react (map to Figma’s set). Keep outline style.
- Motion: Framer Motion; cards fade‑in/slide 8–12px; drawer spring `stiffness: 260, damping: 24`.

### 19.5 Asset handoff checklist

- Share **Figma Inspect** (component names, variants, constraints)
- Export **Variables JSON** (colors/typography/spacing)
- Provide **component list** and the **section → frame** mapping for: Home ribbons, Category grid, Event page, Arc page, Filter drawer.
- If possible: publish a static Inspect link (no JS blocking) or screenshots for tokens.

---

*This UI spec is intentionally concise. Add Figma links/screenshots comments inline as you iterate; keep contracts stable as much as possible.*




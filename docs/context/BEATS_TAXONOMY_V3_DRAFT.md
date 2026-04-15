# ELO v3.0 — Taxonomy Revision Draft

**Status**: **IMPLEMENTED in core/ontology.py, core/config.py, core/prompts.py** (2026-04-13)
**Revision note**: Final count is 25 classes (not 24 as initially counted — T5 has 4 classes after adding STATEMENT).
**Deferred**: `industries[]` / `sectors[]` entity field — renamed to `industries[]` to avoid collision with existing singular `sector` field used for track routing. Requires DB column migration + `pipeline/phase_3_1/extract_labels.py` update + prompt update. Scoped as a follow-up since it touches 4 files and needs a migration. Tracked in Beats Asana tickets.
**Context**: Part of the Beats project direction (D-055, `BEATS_DIRECTION.md`)
**Evidence basis**: 145 sampled titles across 5 CTMs (USA economy/politics, France politics, China economy, Baltic politics — March 2026)
**Intended files to change**: `core/ontology.py`, `core/prompts.py`

---

## Goals

1. **Cover all four tracks equally** — Politics, Security, Economy, Society. Current v2.0 is security-biased.
2. **Minimize ambiguity** — every class should have a clear, non-overlapping scope the LLM can apply deterministically.
3. **Fill gaps identified in real data** — elections, natural events, corporate transactions.
4. **Don't expand for its own sake** — 23 → 25 classes net, with re-scoped existing ones doing more work.

Non-goals: we are **not** trying to encode every nuance. Discrimination happens at entity level (actor + places + orgs + sectors), not at action-class level.

---

## Evidence summary (what the data showed)

Full analysis in Beats project discussion. Headline findings:

| Problem | Frequency in sample | Example |
|---|---|---|
| Elections → COLLECTIVE_PROTEST | 7 of 7 election titles | "French elect mayors in key cities" |
| ECONOMIC_DISRUPTION = market catch-all | ~15 of 30 USA econ | "Microsoft freezes hiring", "Nvidia trillion-dollar forecast", F1 racing headline |
| Corporate M&A → RESOURCE_ALLOCATION | 8+ titles | "Kleiner Perkins Raises $3.5B", "SpaceX IPO", "GM invests in Korea" |
| Corporate products → INFRASTRUCTURE_DEVELOPMENT | 4+ titles | "Meta unveils AI chips", "Amazon Zoox robotaxi" |
| POLITICAL_PRESSURE / DIPLOMATIC_PRESSURE split inconsistent | Every sampled CTM | "China warns..." → ECON_PRESS and "China urges..." → DIPL_PRESS on sibling titles |
| COLLECTIVE_PROTEST used for non-protests | Every occurrence in sample | Elections, polls, mayoral victories |
| No slot for natural events | Not sampled but structural | Floods, quakes → SOCIAL_INCIDENT (meant for "riots, disasters, mass events" — 3 things in 1 bucket) |

---

## Proposed changes

### ADD — 4 new action classes (revised)

#### `ELECTORAL_EVENT` (Tier 4 — Coordination / formal democratic process)
**Scope**: elections, referendums, primaries, government transitions resulting from popular vote, appointments-by-election.
**Includes**:
- Local, regional, national, EU elections
- Referendums, plebiscites
- Party primaries where outcomes are newsworthy
- Election results, vote counts, coalition formations triggered by election
**Excludes**:
- Opinion polls (→ not an event for Beats; filter at Phase 3.3)
- Appointments by parliamentary vote without popular election (→ LEGISLATIVE_DECISION)
- Impeachments (→ LEGISLATIVE_DECISION or LEGAL_RULING depending on body)

#### `NATURAL_EVENT` (Tier 7 — Incidents)
**Scope**: natural disasters, health crises, environmental incidents with natural cause.
**Includes**:
- Floods, quakes, fires, storms, typhoons, droughts, famines
- Epidemics, pandemics, disease outbreaks
- Volcanic eruptions, tsunamis, avalanches
**Excludes**:
- Mechanical accidents (→ SECURITY_INCIDENT)
- Industrial disasters with human cause (→ SECURITY_INCIDENT)
- Climate policy announcements (→ POLICY_CHANGE)

#### `COMMERCIAL_TRANSACTION` (Tier 3 — Resource & Capability)
**Scope**: corporate transactions that transfer ownership, capital, or commercial commitments — and product releases.
**Includes**:
- Mergers, acquisitions, divestitures
- IPOs, share issuance, private fundraising, VC rounds
- Major contracts, supply agreements, partnership deals
- Investment announcements (corporate, not state)
- Restructurings, spinoffs
- Product releases and launches ("Apple releases MacBook Neo", "Meta unveils AI chips")
- Service launches ("Amazon Zoox robotaxi targets paid service")
- Major feature rollouts
**Excludes**:
- State budget/aid disbursement (→ RESOURCE_ALLOCATION)
- Physical infrastructure projects with durable capex (→ INFRASTRUCTURE_DEVELOPMENT)
- Corporate strategy commentary without a concrete transaction or release (→ STATEMENT or exclude)

**Why no separate PRODUCT_LAUNCH class** (data check 2026-04-13):
Sampling 25 CORPORATION+INFRASTRUCTURE_DEVELOPMENT titles in USA/economy/March, ~17 were real infrastructure (chip fabs, data centers, mines), ~5 actual product launches, ~3 ambiguous. Keyword scan across 3 CTMs found product-launch-like titles at ~1.2% of corpus (45 titles total in USA+CN economy combined). Volume too low to justify a dedicated class; folded into COMMERCIAL_TRANSACTION.

#### `STATEMENT` (Tier 5 — Pressure & Influence) *(NEW — added per Max Q1)*
**Scope**: public statements by named officials, leaders, or recognized figures that do not constitute coercive pressure.
**Includes**:
- Speeches, press conferences, interviews ("Trump says X")
- Op-eds by named political or institutional figures
- Tweets/posts when reported as news by multiple outlets
- "X says Y" stories where Y is a view, opinion, or forecast — not a decision
**Excludes**:
- Demands, ultimatums, condemnations with coercive framing (→ PRESSURE)
- Organized propaganda or state media campaigns (→ INFORMATION_INFLUENCE)
- Anonymous commentary or journalist analysis (→ exclude at Phase 3.3)
- Statements that contain a concrete decision or action ("X announces resignation") (→ use the action class of the decision)

**Rationale**: Trump-style "statement of the day" noise is a huge fraction of political coverage and currently scatters across POLITICAL_PRESSURE / INFORMATION_INFLUENCE / POLICY_CHANGE. Treating it as its own class lets us isolate the noise: Beats can default to **excluding STATEMENT events from Briefs**, but keep them extractable for users who want to track e.g. Trump's rhetorical shifts over time. Frontend adds a "show statements" toggle.

**Beat lane behavior**: STATEMENT lanes are expected to be large and noisy. Beats algorithm should keep them but de-emphasize in Mode A theater rendering (small badge instead of main timeline item).

---

### MERGE — 2 classes → 1

| From | To | Rationale |
|---|---|---|
| `POLITICAL_PRESSURE` + `DIPLOMATIC_PRESSURE` | `PRESSURE` | LLM splits inconsistently across sibling titles. The operational difference is invisible to readers. |

**New `PRESSURE` scope**: verbal/political/diplomatic coercion — demands, ultimatums, notes, statements of coercive intent, summonings, condemnations, recalls. Single class replaces two.

`ECONOMIC_PRESSURE` stays **separate but with a tightened boundary vs `SANCTION_ENFORCEMENT`** (Max's feedback — overlap observed):

| Class | Tier | Scope |
|---|---|---|
| `ECONOMIC_PRESSURE` | T5 (non-binding) | **THREATS and announced intent** of financial levers: "Trump threatens 25% tariffs", "Warns of sanctions", "Signals investment freeze" |
| `SANCTION_ENFORCEMENT` | T2 (coercive) | **ACTUAL implementation**: "US imposes 25% tariff", "Treasury freezes IRGC assets", "Bank sanctioned under OFAC rules" |

Decision rule for the LLM: **Has the measure been enacted?** If yes → SANCTION_ENFORCEMENT. If no (threat, warning, proposal, negotiation stage) → ECONOMIC_PRESSURE.

---

### NARROW — 6 existing classes (definition tightening only, no structural change)

#### `RESOURCE_ALLOCATION`
**Old**: "Budget, funding, aid disbursement"
**New**: "STATE budgets, aid disbursement, government funding, sovereign wealth allocations ONLY."
**Enforcement in prompt**: "Corporate M&A, fundraising, and investment → use COMMERCIAL_TRANSACTION."

#### `INFRASTRUCTURE_DEVELOPMENT`
**Old**: "Construction, deployment of physical systems"
**New**: "Physical or digital infrastructure projects with durable capital footprint: ports, rail, grids, data centers, power plants, pipelines, undersea cables, 5G networks."
**Enforcement in prompt**: "Consumer products and commercial services → use PRODUCT_LAUNCH."

#### `POLICY_CHANGE`
**Old**: "Executive/regulatory policy adoption"
**New**: "GOVERNMENT executive/regulatory policy adoption ONLY."
**Enforcement in prompt**: "Corporate strategy decisions → use COMMERCIAL_TRANSACTION or exclude."

#### `ECONOMIC_DISRUPTION` → renamed to `MARKET_SHOCK`
**Old**: "Market crashes, supply shocks, defaults"
**New name**: `MARKET_SHOCK`
**New scope**: Significant asset/commodity/currency price moves (≥2σ) driven by **macro or geopolitical causes**. Covers crashes, surges, defaults, supply shocks, safe-haven flows, and currency runs. **Directionless** — up-moves and down-moves both qualify when the cause is macro.
**Enforcement in prompt**:
> Routine stock moves based on company fundamentals or earnings are NOT MARKET_SHOCK — exclude at Phase 3.3.
> Macro-driven commodity flows (gold/silver/oil/wheat surging or crashing on war, sanctions, Fed action, supply disruption) ARE MARKET_SHOCK.
> Currency moves driven by monetary policy or geopolitical flight-to-safety → MARKET_SHOCK.
> Pair with `commodities[]` (gold, oil, wheat, USD) and `sectors=[FINANCE]` (or ENERGY for oil, FOOD_AGRI for grains).

**Examples**:
- "Gold climbs 7% as Iran war sparks safe-haven demand" → MARKET_SHOCK, commodities=[gold], sectors=[FINANCE]
- "Oil surges to $130 on Hormuz closure" → MARKET_SHOCK, commodities=[oil], sectors=[ENERGY]
- "Dollar hits record on Fed tightening" → MARKET_SHOCK, commodities=[USD], sectors=[FINANCE]
- "US stocks tumble on Iran ultimatum" → MARKET_SHOCK, sectors=[FINANCE]
- "Tesla stock up 3% on earnings" → **excluded at Phase 3.3** (company-specific)

#### `COLLECTIVE_PROTEST` → rename to `CIVIL_ACTION`
**Old name + scope**: "Demonstrations, strikes, civil disobedience"
**New name + scope**: "Organized collective civil action: demonstrations, rallies, strikes, walkouts, civil disobedience campaigns, occupations."
**Enforcement in prompt**: "Elections → ELECTORAL_EVENT. Opinion polls → exclude or INFORMATION_INFLUENCE. Vote results → ELECTORAL_EVENT."

#### `INFORMATION_INFLUENCE`
**Old**: "Propaganda campaigns, disinformation ops"
**New**: same scope, tighter enforcement. "Only use for active influence operations: propaganda, disinformation, state media campaigns, leaks, psyops. Routine commentary and reporting are NOT INFORMATION_INFLUENCE."

---

### KEEP unchanged (13 classes)

`MILITARY_OPERATION`, `LAW_ENFORCEMENT_OPERATION`, `SANCTION_ENFORCEMENT`, `CAPABILITY_TRANSFER`, `ALLIANCE_COORDINATION`, `STRATEGIC_REALIGNMENT`, `MULTILATERAL_ACTION`, `LEGAL_RULING`, `LEGISLATIVE_DECISION`, `REGULATORY_ACTION`, `LEGAL_CONTESTATION`, `INSTITUTIONAL_RESISTANCE`, `SECURITY_INCIDENT`, `ECONOMIC_PRESSURE`

### DROP (1 class)

- `SOCIAL_INCIDENT` *(Max Q4 — confirmed drop)*
  - Redistribution: riots → `CIVIL_ACTION`, natural disasters → `NATURAL_EVENT`, mass events like accidents → `SECURITY_INCIDENT`. With `NATURAL_EVENT` and the clarified `CIVIL_ACTION`, SOCIAL_INCIDENT has no remaining scope.

---

## Final ELO v3.0 action class list (24 classes, 7 tiers)

### T1 — FORMAL DECISION (highest priority)
- `LEGAL_RULING`
- `LEGISLATIVE_DECISION`
- `POLICY_CHANGE` *(narrowed to government only)*
- `REGULATORY_ACTION`
- `ELECTORAL_EVENT` *(NEW)*

### T2 — COERCIVE ENFORCEMENT
- `MILITARY_OPERATION`
- `LAW_ENFORCEMENT_OPERATION`
- `SANCTION_ENFORCEMENT` *(boundary clarified vs ECONOMIC_PRESSURE)*

### T3 — RESOURCE & CAPABILITY
- `RESOURCE_ALLOCATION` *(narrowed to state only)*
- `INFRASTRUCTURE_DEVELOPMENT` *(narrowed to physical/digital infra only)*
- `CAPABILITY_TRANSFER`
- `COMMERCIAL_TRANSACTION` *(NEW — includes product launches)*

### T4 — COORDINATION
- `ALLIANCE_COORDINATION`
- `STRATEGIC_REALIGNMENT`
- `MULTILATERAL_ACTION`

### T5 — PRESSURE & INFLUENCE
- `PRESSURE` *(merged from POLITICAL_PRESSURE + DIPLOMATIC_PRESSURE)*
- `ECONOMIC_PRESSURE` *(narrowed — threats only, not enacted measures)*
- `STATEMENT` *(NEW — statements by named figures, filterable from Briefs)*
- `INFORMATION_INFLUENCE` *(narrowed — organized influence ops only)*

### T6 — CONTESTATION
- `LEGAL_CONTESTATION`
- `INSTITUTIONAL_RESISTANCE`
- `CIVIL_ACTION` *(renamed from COLLECTIVE_PROTEST, narrowed)*

### T7 — INCIDENTS (last resort)
- `SECURITY_INCIDENT`
- `NATURAL_EVENT` *(NEW — placeholder for hurricanes, pandemics, etc.)*
- `MARKET_SHOCK` *(renamed from ECONOMIC_DISRUPTION, directionless, covers commodity/currency flows)*

**Count**: 24 classes (was 23). Net +1.
Dropped: `POLITICAL_PRESSURE` (merged), `DIPLOMATIC_PRESSURE` (merged), `SOCIAL_INCIDENT` (redistributed), `PRODUCT_LAUNCH` (folded into COMMERCIAL_TRANSACTION after data check).
Added: `ELECTORAL_EVENT`, `NATURAL_EVENT`, `COMMERCIAL_TRANSACTION`, `STATEMENT`.
Renamed: `COLLECTIVE_PROTEST` → `CIVIL_ACTION`, `ECONOMIC_DISRUPTION` → `MARKET_SHOCK`.

---

## New entity field: `sectors[]`

**Schema change**: `title_labels.sectors` — TEXT[] column, nullable, populated by LLM.

**Closed vocabulary (18 values)**:
```
AEROSPACE
AI               (AI labs, frontier models, training infrastructure, GPU datacenters when AI-specific)
AUTOMOTIVE
BIOTECH
DEFENSE
ENERGY           (oil, gas, nuclear, electricity broadly)
FINANCE          (banks, funds, markets, insurance, crypto)
FOOD_AGRI        (food, agriculture, commodities, fertilizers)
GREEN_TECH       (EV, solar, wind, batteries, hydrogen)
IT_SOFTWARE      (software companies, cloud, SaaS, platforms — excluding AI-specific and media)
MEDIA            (news media, social platforms, streaming services — strategic stories only:
                  ownership, regulation, electoral influence, propaganda, censorship, platform
                  transactions. Entertainment/celebrity content is filtered out at Phase 3.3.)
MINING           (metals, rare earths, minerals)
PHARMA           (drugs, medical devices, healthcare systems)
RETAIL
SEMICONDUCTORS   (chips, foundries, EDA tools, memory)
SHIPPING         (maritime, logistics, ports, freight, aviation freight)
TELECOMS         (carriers, 5G, undersea cables, satellites, broadband)
OTHER            (explicit escape hatch)
```

**Notes on added sectors:**
- **AI and IT_SOFTWARE are separate** because the strategic/geopolitical story is distinct. AI labs (OpenAI, Anthropic, Mistral) and frontier-model infrastructure are subject to export controls, sovereign capability concerns, and different regulatory treatment than general software. Traditional cloud/SaaS goes to IT_SOFTWARE.
- **Overlap rules**:
  - NVIDIA chip sales → `SEMICONDUCTORS`
  - NVIDIA AI datacenter buildout → `SEMICONDUCTORS, AI` (multi-value)
  - Microsoft Azure cloud → `IT_SOFTWARE`
  - Microsoft Copilot AI rollout → `IT_SOFTWARE, AI`
  - OpenAI fundraising → `AI`
  - Amazon smartphone → `IT_SOFTWARE` (it's a hardware product from a software company)
  - TikTok US ban debate → `MEDIA` (platform regulation)
- **Quantum** deliberately excluded for now — not enough newsflow yet. Add later if it emerges as a persistent beat.

**Multi-value allowed**: one title can carry multiple sectors. E.g. "Apple cuts fees in China as BYD boosts charging network" → `[SEMICONDUCTORS, AUTOMOTIVE, GREEN_TECH]`.

**Priority**: use `sectors[]` only when the title is materially about a sector's activity. A headline about "Microsoft earnings" is SEMICONDUCTORS only if the content is about chip business; otherwise just `OTHER` or null.

---

## Proposed prompt changes in `core/prompts.py`

Changes are concentrated in the action-class instructions and the entity extraction block. Key new rules:

1. **Elections rule** (add to PRIORITY_RULES):
   > Elections (local, national, primaries, referendums, government transitions via vote) ALWAYS use ELECTORAL_EVENT, never COLLECTIVE_PROTEST or LEGISLATIVE_DECISION.

2. **Corporate vs state rule** (new section):
   > State actors (executives, central banks, regulators) with funding/budget decisions → RESOURCE_ALLOCATION.
   > Corporate actors with deals, M&A, IPOs, contracts → COMMERCIAL_TRANSACTION.
   > Product / feature / model releases → PRODUCT_LAUNCH.
   > A corporation doing POLICY_CHANGE is an error — use COMMERCIAL_TRANSACTION.

3. **MARKET_SHOCK vs routine market noise**:
   > Company-specific stock moves (earnings, guidance, analyst calls) are NOT MARKET_SHOCK. Exclude at Phase 3.3.
   > Macro or geopolitically-driven moves ARE MARKET_SHOCK — directionless (crashes AND surges).
   > Commodity/currency flows during stress → MARKET_SHOCK + commodities[] entity + FINANCE/ENERGY/FOOD_AGRI sector as appropriate.
   > Safe-haven flows (gold up, dollar up, bonds up on war) → MARKET_SHOCK.
   > Routine daily market reports ("stocks mixed today") → exclude at Phase 3.3.

4. **Pressure consolidation + sanction boundary**:
   > PRESSURE covers verbal/diplomatic/political coercion: ultimatums, demands, summonings, recalls, statements of coercive intent, condemnations.
   > ECONOMIC_PRESSURE is separate: it covers THREATS and non-binding financial pressure only — "Trump threatens 25% tariffs", "Warns of sanctions", "Signals investment freeze".
   > SANCTION_ENFORCEMENT is for ENACTED measures only — "US imposes 25% tariff", "Treasury freezes assets", "Bank sanctioned under OFAC rules".
   > Decision rule: has the measure been enacted? Yes → SANCTION_ENFORCEMENT. No (threat/warning/proposal) → ECONOMIC_PRESSURE.

7. **STATEMENT vs PRESSURE vs INFORMATION_INFLUENCE**:
   > STATEMENT: any non-coercive public statement by a named figure (Trump says, Xi says, Macron says, CEO says). Opinions, forecasts, reactions, views.
   > PRESSURE: statements with coercive intent — ultimatums, demands, condemnations.
   > INFORMATION_INFLUENCE: organized propaganda, disinformation campaigns, state media operations. NOT individual statements.
   > If a statement contains a concrete decision or action ("X announces resignation", "Y signs bill"), use the decision's action class, not STATEMENT.

5. **Sectors extraction** (new section):
   > When a title is materially about a sector's activity, populate `sectors[]` from the closed list. Multi-value allowed. Do not guess — if uncertain, leave empty.

6. **Civil action vs protest rule**:
   > CIVIL_ACTION is for organized collective action: strikes, rallies, demonstrations, walkouts, civil disobedience. Opinion polls, vote results, and news commentary are NOT CIVIL_ACTION.

---

## Ambiguity log

Known edge cases where the taxonomy is still fuzzy. Each needs an explicit rule in the prompt or gets flagged at review time.

### AMB-01: ELECTORAL_EVENT vs LEGISLATIVE_DECISION for appointments
A PM appointed by parliament without popular election — which class?
**Proposed rule**: If the appointment is the direct outcome of a popular vote, ELECTORAL_EVENT. If it's a legislative vote independent of an election, LEGISLATIVE_DECISION. "Zelensky appoints new PM" → LEGISLATIVE_DECISION (it's an executive appointment). "Coalition formed after March 5 vote" → ELECTORAL_EVENT.

### AMB-02: COMMERCIAL_TRANSACTION vs PRODUCT_LAUNCH for acquisitions of product companies
"Amazon acquires Zoox" — is it a transaction (M&A) or a product launch (new capability)?
**Proposed rule**: If the headline frames it as ownership transfer → COMMERCIAL_TRANSACTION. If it frames it as a new product/service reaching market → PRODUCT_LAUNCH. Default to COMMERCIAL_TRANSACTION when ambiguous.

### AMB-03: SECURITY_INCIDENT vs NATURAL_EVENT for mixed-cause incidents
Plane crash due to weather, bridge collapse in earthquake, etc.
**Proposed rule**: Primary cause wins. "Earthquake caused bridge collapse" → NATURAL_EVENT. "Pilot error in bad weather" → SECURITY_INCIDENT. If unclear, SECURITY_INCIDENT.

### AMB-04: Commentary/statements — no home class *(RESOLVED: new STATEMENT class)*
Op-eds by named figures, "X says Y", leader reactions — now handled by the new `STATEMENT` class in T5. Beats excludes STATEMENT events from Briefs by default; frontend adds a "show statements" toggle. Unnamed journalist commentary and anonymous analyst takes are still excluded at Phase 3.3.

### AMB-05: Poll results
"Reuters/Ipsos poll: Trump approval 36%" — currently labeled COLLECTIVE_PROTEST. Not a protest.
**Proposed rule**: Exclude at Phase 3.3. Polls are meta-information, not events. If a poll is genuinely newsworthy (e.g. "Exit poll: Orbán loses"), it gets folded into ELECTORAL_EVENT.

### AMB-06: Corporate strategy statements without a deal
"OpenAI to cut back on side projects", "BlackRock boss says plumbers > lawyers". Commentary by corporate actors.
**Proposed rule**: Exclude at Phase 3.3 unless there's a concrete action (layoff, divestment, pivot with numbers). "Plans to" statements without numbers or dates → exclude.

### AMB-07: Multi-sector stories
"Apple + BYD + semiconductors" — how many sectors?
**Proposed rule**: `sectors[]` is multi-value. Include each sector materially discussed, max 3.

### AMB-08: Regional/continental targets
"Europe", "ASEAN", "MENA" — target normalization?
**Proposed rule**: Use existing region codes (EU, ASEAN, MENA, LATAM). If a title says "European allies" and the context is clearly NATO military, use NATO. If context is economic trade, use EU. Default to EU for ambiguous Europe.

---

## Rollout plan (post-review)

1. **Review gate**: Max reviews this draft. Edits happen in-place in this file.
2. **Implementation PR 1**: update `core/ontology.py` to v3.0 schema. Add `sectors[]` column migration.
3. **Implementation PR 2**: update `core/prompts.py` with new rules from § Proposed prompt changes.
4. **Dry-run test**: re-extract labels for 50 titles from ONE CTM (suggest USA/geo_economy/March — it exposes the most bad labels today). Hand-grade the new labels against the old. If >80% improvement on the problem categories, proceed.
5. **Controlled extension**: re-extract 5 CTMs end-to-end (USA security, USA economy, USA politics, France politics, China economy, Baltic politics). Run Beats on new data. Compare Beats output.
6. **Full backfill decision**: if controlled extension looks good, plan a from-January backfill. Estimated cost: ~$40-80 in LLM calls for ~500K titles re-extraction (cheap by project standards).

---

## Review resolutions (2026-04-13)

All six open questions resolved by Max:

- **Q1 STATEMENT class** → RESOLVED: **add explicit STATEMENT class** (T5). Frontend-filterable. Rationale from Max: "Trump says a different thing every few days — pure noise and yet 'events' that tell a lot about US politics. Opinions also change reflecting the battle field. Interesting to track."
- **Q2 Sectors granularity** → RESOLVED: **add AI and IT_SOFTWARE**. Quantum deferred (not enough newsflow). 18 values total.
- **Q3 PRODUCT_LAUNCH** → RESOLVED: **dropped**. Data check 2026-04-13 showed low volume (~1.2% of corpus). Folded into COMMERCIAL_TRANSACTION.
- **Q4 Drop SOCIAL_INCIDENT** → RESOLVED: **dropped**.
- **Q5 ELECTORAL_EVENT tier** → RESOLVED: **keep at T1**. No strong opinion from Max; T1 stands.
- **Q6 NATURAL_EVENT without empirical validation** → RESOLVED: **keep as placeholder**. Rationale from Max: "we do have hurricanes, massive forest fires, extreme weather. And we had Covid — it was like Iran war 10 times over."

## Remaining open questions

- **Q7**: With the sector list now at 18 values, do we want sub-sector granularity for SEMICONDUCTORS (FOUNDRY / FABLESS / EDA / MEMORY)? Probably no — entity names (TSMC, ASML, Micron) already carry that signal. Flagging for explicit NO unless you disagree.
- **Q8**: Should the Phase 3.3 intel gating filter continue to exclude entertainment/sports/celebrity — same as today — and additionally exclude pure commentary/poll-result titles? I'd say yes to both. Confirm?

---

## References

- `docs/context/BEATS_DIRECTION.md` — project direction doc
- `docs/context/30_DecisionLog.yml` — D-055 (Beats adoption)
- `core/ontology.py` — current v2.0 (file to edit)
- `core/prompts.py` — extraction prompt (file to edit)
- `scripts/prototype_whale_extraction.py` — Beats prototype using current v2.0 taxonomy (for comparing outputs pre/post v3.0)

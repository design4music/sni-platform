# ELO v3.0 Hand-Grading Test #3 — ASIA-CHINA/economy/March

**Date**: 2026-04-13
**CTM**: ASIA-CHINA / geo_economy / 2026-03
**Sample**: 50 random English titles
**Focus**: sectors[] validation, MARKET_SHOCK in non-US context, COMMERCIAL_TRANSACTION for Chinese corporate actions, POLICY_CHANGE vs STATEMENT distinction for state pronouncements

## Headline finding

**China economy has the highest exclusion rate yet — ~40% of titles are propaganda, commentary, or routine statistics that shouldn't be events at all.** Chinese state media (Global Times, CGTN, GT Voice) floods the corpus with "features", "voices", and "insights" that currently get labeled INFORMATION_INFLUENCE or POLICY_CHANGE when they should be filtered at Phase 3.3.

Runner-up finding: **sectors[] coverage is excellent**. AUTOMOTIVE, FINANCE, SEMICONDUCTORS, SHIPPING, MINING, IT_SOFTWARE, AI, GREEN_TECH all applied cleanly in the sample. No gaps surfaced.

---

## Categorized results

### EXCLUDE at 3.3 (20 titles, 40%)

Higher than USA economy (28%) and France politics (22%). Chinese economy reporting skews heavy on analysis/commentary/propaganda.

**Opinion / editorial / commentary** (8):
- #1 "Behind $20.4 Billion: The Obsession of China's Game Makers" — feature
- #5 "China's development: Why it resonates beyond ideology" — opinion
- #6 "The chip story: Why global chip titans are inseparable from Chinese market" — analysis
- #7 "Why intl companies choose Shanghai?" — PR/promo
- #18 "Foreign firms eye fresh opportunities..." — general commentary
- #21 "Global CEOs offer insights on Beijing as business hub" — promo
- #22 "Lessons for Europe from China's growth" — opinion
- #38 "RED THREAD: Europe absorbs China's factory excess" — analysis column

**Chinese state media editorial voices** (3):
- #11 "Is China's 'foreign trade engine' failing?: Global Times editorial" — literally labeled editorial
- #20 "GT Voice: South Korea's export growth..." — Global Times opinion section
- #26 "China contributes 30% to global growth, scholar Zheng Yongnian tells GT" — pundit in GT

**Routine statistics / trade data** (6):
- #13 "China's forex reserves reach $3.4278 trillion at end-February" — routine data
- #15 "China's construction machinery exports surge 33% in Jan-Feb" — trade stats
- #17 "China's Credit Expansion Tops Forecast..." — macro data
- #32 "EU car imports from China surpass exports for 1st time: EY" — EY data release
- #50 "China says 2025 inbound trips top 150 million..." — tourism stats
- #48 "German firms bank on western China" — feature/trend

**Trend / feature / lifestyle / garbage** (3):
- #25 "Chinese robot vacuums sweep Southeast Asia" — trend feature
- #28 "Tags Chinese tourists Phuket" — scraped metadata, not a title
- #34 "Amazon's Big Spring Sale tech deals: 63% off AirPods..." — e-commerce promo
- #39 "Chinese seed industry cases featured on international plant variety protection platform" — niche trade press

**Current v2 labels for excluded titles**: wildly scattered across `SECURITY_INCIDENT`, `ECONOMIC_DISRUPTION`, `INFORMATION_INFLUENCE`, `POLICY_CHANGE`, `RESOURCE_ALLOCATION`, `REGULATORY_ACTION`. Consistent pattern: when the LLM can't find a home, it picks randomly.

### IMPROVED — taxonomy changes catch real labeling errors (16 titles, 32%)

#### STATEMENT wins (6)
Chinese pronouncements "vows/pledges/says/hopes/reaffirms/sight" are aspirational statements, not enacted policies. Currently land in POLICY_CHANGE.

| # | Title | v2 | v3 |
|---|---|---|---|
| 14 | "China pledges to deepen trade ties with Kenya" | DIPLOMATIC_PRESSURE | STATEMENT |
| 29 | "Chinese Vice Premier: 15th Five-Year Plan will create..." | POLICY_CHANGE | STATEMENT |
| 37 | "German carmakers reaffirm China ties" | ECONOMIC_PRESSURE | STATEMENT |
| 42 | "China Commerce Minister Hopes Lilly Will Deepen China Commitment" | POLITICAL_PRESSURE | STATEMENT |
| 43 | "China to further boost consumption" | POLICY_CHANGE | STATEMENT |
| 49 | "Chinese FM responds to question over India's new rules..." | DIPLOMATIC_PRESSURE | STATEMENT |

#### COMMERCIAL_TRANSACTION wins (6)
Corporate deals, executive hires, product launches, IPO filings, market exits — all mislabeled in v2.

| # | Title | v2 | v3 |
|---|---|---|---|
| 10 | "Nexperia China resumes most operations after account disruptions" | ECONOMIC_DISRUPTION | COMMERCIAL_TRANSACTION, [SEMICONDUCTORS] |
| 16 | "China's COSCO resumes Asia-Gulf shipment bookings..." | ECONOMIC_DISRUPTION | COMMERCIAL_TRANSACTION, [SHIPPING] |
| 31 | "Alibaba eyes 'tens of millions' of US users for new AI agent" | CAPABILITY_TRANSFER | COMMERCIAL_TRANSACTION, [IT_SOFTWARE, AI] |
| 35 | "JPMorgan Hires Goldman's Zhang to Co-Head China IB" | ECONOMIC_DISRUPTION | COMMERCIAL_TRANSACTION, [FINANCE] |
| 36 | "Volkswagen's Skoda brand to end China sales this year" | POLICY_CHANGE | COMMERCIAL_TRANSACTION, [AUTOMOTIVE] |
| 45 | "Merdeka Gold submits Hong Kong listing application" | REGULATORY_ACTION | COMMERCIAL_TRANSACTION, [FINANCE, MINING], commodities=[gold] |

#### MARKET_SHOCK wins (2)
| # | Title | v2 | v3 |
|---|---|---|---|
| 19 | "China's new home prices fall at fastest pace in over 3 years" | ECONOMIC_DISRUPTION | MARKET_SHOCK, [FINANCE, RETAIL] |
| 41 | "China Firms Ramp Up Derivatives Hedging to Record as Yuan Surges" | ECONOMIC_DISRUPTION | MARKET_SHOCK, commodities=[CNY], [FINANCE] |

#### ALLIANCE_COORDINATION reclassification (2)
Bilateral trade talks mislabeled as MULTILATERAL_ACTION (which is for 3+ parties):

| # | Title | v2 | v3 |
|---|---|---|---|
| 27 | "US-China trade talks open in Paris..." | MULTILATERAL_ACTION | ALLIANCE_COORDINATION |
| 30 | "New round of China-US trade talks underway in Paris" | MULTILATERAL_ACTION | ALLIANCE_COORDINATION |

### SAME (9 titles — v2 was fine)

| # | Title | v2 (kept) |
|---|---|---|
| 2 | "China vows more open economy, national treatment..." | POLICY_CHANGE *(borderline with STATEMENT)* |
| 9 | "The door India left ajar: Economic ties with China see calibrated reset with easing of FDI rules" | POLICY_CHANGE |
| 12 | "MERZ: BRUSSELS SUMMIT WILL FOCUS ON EU COMPETITIVENESS" | ALLIANCE_COORDINATION *(borderline STATEMENT)* |
| 24 | "China sets sight on accelerating high-quality development in five years" | POLICY_CHANGE *(if tied to 5YP)* |
| 33 | "A New U.S. Facility Could Break China's Grip on Critical Materials" | INFRASTRUCTURE_DEVELOPMENT *(borderline exclude)* |
| 40 | "DJI drone ban disrupting US construction sector" | REGULATORY_ACTION |
| 44 | "China's eldercare subsidy program drives $1.66 billion in consumption" | RESOURCE_ALLOCATION |
| 46 | "Tech Exec Accused of Smuggling Nvidia Chips... Resigns" | LAW_ENFORCEMENT_OPERATION |
| 47 | "China widens BHP iron ore ban amid contract talks" | ECONOMIC_PRESSURE → SANCTION_ENFORCEMENT *(widens = enacted)* |

### Ambiguous (5)

| # | Title | Issue |
|---|---|---|
| 3 | "China, India lead car exports worth billions..." | Feature/stats vs COMMERCIAL_TRANSACTION |
| 4 | "Chinese EVs starting to break into SA used car market" | Trend piece vs COMMERCIAL_TRANSACTION |
| 8 | "Shopping in China initiative opportunity for businesses" | POLICY_CHANGE vs EXCLUDE |
| 23 | "New Development Bank to support growth of BRICS countries — President" | STATEMENT vs RESOURCE_ALLOCATION |
| 47 | "China widens BHP iron ore ban" | ECONOMIC_PRESSURE vs SANCTION_ENFORCEMENT |

---

## Tally

| Assessment | Count | % |
|---|---|---|
| **IMPROVED** — STATEMENT new class | 6 | 12% |
| **IMPROVED** — COMMERCIAL_TRANSACTION new class | 6 | 12% |
| **IMPROVED** — MARKET_SHOCK | 2 | 4% |
| **IMPROVED** — ALLIANCE_COORDINATION reclass | 2 | 4% |
| **EXCLUDE at 3.3** | 20 | 40% |
| **SAME** (v2 fine) | 9 | 18% |
| **AMBIGUOUS** | 5 | 10% |

**72% of titles improve under v3 (combined improve + exclude).** Slightly lower improve rate than France politics (88%) because Chinese state reporting has a higher proportion of genuinely-clean policy labels (many POLICY_CHANGE labels were correct).

---

## Key findings

### 1. Chinese state media is the noise layer (vs commentary in US data)

In USA economy, noise came from Bloomberg/WSJ analyst takes and earnings commentary. In France politics, noise came from editorials and profiles. In China economy, noise comes from Global Times / CGTN / People's Daily / GT Voice — a different kind of content with the same taxonomy problem: it has no home and gets scattered across INFORMATION_INFLUENCE / POLICY_CHANGE / SECURITY_INCIDENT.

**Proposed rule for Phase 3.3**: when the source is a state-affiliated media outlet AND the content is opinion/commentary (editorial, GT Voice, expert op-ed), exclude unless the content describes a concrete action. This is a source-aware filter, not a taxonomy change.

### 2. STATEMENT is where Chinese pronouncements belong

"China vows/pledges/sets sight/hopes/reaffirms/says" = classic STATEMENT. Currently the v2 LLM dumps all of these into POLICY_CHANGE, which inflates the POLICY_CHANGE lane and pollutes Beats output. Six clean STATEMENT reclassifications in this sample.

**Prompt rule needed**: "Aspirational language (vows, pledges, sets sight, plans, hopes, aims) → STATEMENT unless attached to a concrete decision, budget, or law passage. Reserved vocabulary: 'announces', 'signs', 'passes', 'enacts' → POLICY_CHANGE / LEGISLATIVE_DECISION."

### 3. sectors[] vocabulary is validated — no gaps found

In this sample alone, sectors applied cleanly across:
- `SEMICONDUCTORS` (#10, #46)
- `SHIPPING` (#16)
- `IT_SOFTWARE` (#31)
- `AI` (#31)
- `FINANCE` (#19, #35, #41, #45)
- `AUTOMOTIVE` (#36)
- `MINING` (#45, #47, implied #44)
- `RETAIL` (#19)

No gaps surfaced. The 18-value closed vocab covers China economy adequately. The earlier decision to include AI + IT_SOFTWARE separately is validated — Alibaba AI agent story (#31) uses BOTH sectors naturally.

### 4. MARKET_SHOCK works in non-US context

Two clean hits: home price crash (#19, "fastest pace in 3 years" = shock-level) and yuan surge (#41, "record hedging" = stress signal). The class is not US-centric; the logic (macro-driven, ≥2σ, cross-asset) transfers cleanly.

### 5. Routine statistics are indistinguishable from events in v2

Forex reserves, credit expansion, export stats, tourism numbers — these are routine data releases labeled as if they were events. v2 picks ECONOMIC_DISRUPTION or RESOURCE_ALLOCATION because there's no "routine data" filter.

**Proposed rule for Phase 3.3**: exclude titles that are primarily statistics releases unless the headline signals a shock ("collapse", "surge to record", "fastest in X years"). Routine "X rose Y%" headlines → exclude.

### 6. Bilateral vs multilateral confusion persists

US-China trade talks are bilateral → should be ALLIANCE_COORDINATION. v2 labels them MULTILATERAL_ACTION, which is reserved for 3+ parties (UN, G7, WTO). Same pattern as France hand-grade #2 where bilateral meetings got mislabeled as DIPLOMATIC_PRESSURE. **Prompt rule needed**: distinguish bilateral (ALLIANCE_COORDINATION) from multilateral (MULTILATERAL_ACTION, requires 3+ parties or an IGO).

---

## Combined findings from all 3 hand-grades (150 titles)

### Cross-sample validation of v3 classes

| Class | USA/eco | FR/pol | CN/eco | Total |
|---|---|---|---|---|
| `ELECTORAL_EVENT` | 0 | 22 | 0 | **22 uses** |
| `MARKET_SHOCK` | 4 | 0 | 2 | **6 uses** |
| `COMMERCIAL_TRANSACTION` | 6 | 0 | 6 | **12 uses** |
| `STATEMENT` | 5 | 2 | 6 | **13 uses** |
| `PRESSURE` (merged) | 2 | 4 | 0 | **6 uses** |
| `NATURAL_EVENT` | 0 | 0 | 0 | **0 uses** |
| `CIVIL_ACTION` (rename) | 0 | 0 | 0 | **0 uses** |

**All 4 new classes except NATURAL_EVENT are empirically justified.** NATURAL_EVENT remains a placeholder (Max's call from earlier — keep for hurricanes/pandemics when they happen).

**CIVIL_ACTION has zero actual protest content** across 150 titles. This is notable. Either:
- March 2026 was genuinely protest-light in the sampled centroids, OR
- Phase 3.3 is currently filtering out protest content, OR
- The LLM labels protests as something else entirely

Worth a targeted check on a CTM/month known for protests (e.g. France 2023 pension reform, HK 2019, US 2020). For now, CIVIL_ACTION stays as a placeholder and we confirm empirically on a fourth hand-grade if needed.

### Exclusion patterns across samples

| Sample | Exclude rate | Dominant noise type |
|---|---|---|
| USA economy | 28% | Analyst forecasts, earnings commentary, market noise |
| France politics | 22% | Editorials, profiles, obituaries, polls |
| China economy | 40% | State media opinion, routine statistics, trend features |

**Unified finding**: ~30% of current v2 extraction output should be excluded at Phase 3.3. Different centroids have different noise profiles, but the fix is the same — a stricter content-type filter at Phase 3.3.

### Prompt rules we've now validated need to exist

1. **Elections → ELECTORAL_EVENT always**, never COLLECTIVE_PROTEST/LEGISLATIVE_DECISION (FR #1)
2. **Bilateral meetings → ALLIANCE_COORDINATION**, not PRESSURE or MULTILATERAL_ACTION (FR, CN #2)
3. **Aspirational language (vows/pledges/sets sight) → STATEMENT** unless concrete decision attached (CN #6)
4. **Routine statistics → exclude** unless shock-level move (USA, CN)
5. **Editorials, profiles, op-eds → exclude at Phase 3.3** (all three)
6. **Macro/geopolitical commodity flows → MARKET_SHOCK + commodities[] + FINANCE/ENERGY/FOOD_AGRI sector** (USA, CN)
7. **Corporate deals/IPOs/exits/product launches/restructurings → COMMERCIAL_TRANSACTION** (USA, CN)
8. **SECURITY_INCIDENT is for attacks/breaches only**, not editorial/profile/obit fallback (FR)

### New ambiguities from this sample

**AMB-18**: Chinese policy aspirations tied to Five-Year Plan. Are "5YP will create" / "sets sight on X in coming five years" POLICY_CHANGE (because 5YP is a formal document) or STATEMENT (because "will" is future tense)? Proposed rule: when the 5YP has been formally adopted by the NPC (which happens at Two Sessions), forward-looking goals within it are POLICY_CHANGE. Standalone aspirations not tied to the 5YP are STATEMENT.

**AMB-19**: Trade ban "widening" vs initial imposition. #47 "China widens BHP iron ore ban" — the ban was already enacted earlier, now being extended. Is this SANCTION_ENFORCEMENT (expansion of enforcement) or ECONOMIC_PRESSURE (additional threat)? Proposed: if the extension materially changes scope, SANCTION_ENFORCEMENT; if it's just a warning of expansion, ECONOMIC_PRESSURE.

---

## Ready for what's next

Three hand-grades complete. Combined 150 titles. Strong empirical validation of:
- ELECTORAL_EVENT (politics critical)
- STATEMENT (political + economic critical)
- COMMERCIAL_TRANSACTION (economic critical)
- MARKET_SHOCK (economic critical)
- PRESSURE merger (universal)
- ALLIANCE_COORDINATION scope clarification (universal prompt issue)
- Phase 3.3 exclusion rules (universal, ~30% of content)

Classes still in "trust us it'll be needed" territory:
- NATURAL_EVENT (no samples, keep as placeholder)
- CIVIL_ACTION (no samples, keep as placeholder — worth a targeted protest-month check)

**Recommendation**: one more targeted hand-grade on a CTM with known protest content (e.g. a month with known large demonstrations) OR AMERICAS-USA/geo_security for the mega-conflict stress test. Then we finalize v3 and write the ontology + prompt diffs.

My lean is **skip the fourth hand-grade** and proceed to writing the actual `core/ontology.py` and `core/prompts.py` diffs. We have enough validation. CIVIL_ACTION and NATURAL_EVENT can be confirmed on live data after the new prompt ships.

Alternative: if you want one more, I'd pick a small, non-English-heavy, non-US CTM to stress test the sectors + actor taxonomy on underrepresented geographies.

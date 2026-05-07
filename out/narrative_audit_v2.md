# Narrative v2 Audit — Unity Rule, Splits, Merges, Gaps

**Date**: 2026-05-06
**Status**: Working audit. Companion to `out/concept_friction_nodes_and_narratives_v2.md` and `out/draft_friction_nodes_seed.md`.

**The diagnostic** (from concept doc section 6):
> A narrative is one worldview's framing of an actor/phenomenon, identified by a unified loaded vocabulary. The vocabulary is the diagnostic. Would the two pieces ever fire WITHOUT each other in real source coverage? If yes (different headlines use only A or only B vocabulary in serious quantity), split. If no (vocabularies always co-fire), one narrative.

The audit applies this to all 30 active narratives in `narrative_consolidation_pass1_v2.md` (N1-N30, with N31 already marked for fold into N1).

---

## Section A. Split candidates (ranked by confidence)

### A1. N3 `west_iran_proxy_threat` — STRONG SPLIT (highest confidence)

**Confirms the concept-doc pre-flag.** Split into:
- `west_iran_nuclear_threat` — Coalition: `[AMERICAS-USA, MIDEAST-ISRAEL, MIDEAST-SAUDI]`. Frames Iran's enrichment program as existential threat warranting preemptive strike or maximum pressure.
- `west_iran_proxy_network_threat` — Same coalition. Frames Iran-aligned armed groups (Hezbollah, Hamas, Houthis, IRGC, PMF) as terror infrastructure warranting counterterrorism operations.

**Vocabulary evidence** (from N3's framing_keywords list, partitioned):

Cluster A (nuclear): `existential threat` (Natanz/Fordow context), `preemptive strike`, `maximum pressure`, `regime change Iran`, plus topic keywords `Iran`, `nuclear`, `IRGC` (in nuclear-weapons-program context), `Mossad` (when paired with Natanz operations).

Cluster B (proxy/territorial): `Iran proxy network`, `terror infrastructure`, `human shields`, `self-defence`, `counterterrorism`, `right to defend`, plus topic keywords `Hezbollah`, `Hamas`, `Houthis`, `Iraqi militias`, `IDF`, `Gaza`, `Lebanon`, `Strait of Hormuz`, `Iron Dome`.

**Will they fire without each other?** Yes, regularly. Headlines about Natanz centrifuge counts, IAEA inspection access, and breakout-time estimates rarely use *human shields* or *Hezbollah tunnels* vocabulary. Headlines about Rafah operations, IDF strikes in southern Lebanon, Houthi shipping attacks rarely use *enrichment* or *breakout time* vocabulary. The two clusters share the framing word `existential threat` and the umbrella `Iran proxy/regime`, but the operational vocabularies are measurably distinct.

**FN evidence**: FN2 (Iran nuclear) and FN6 (Bab el-Mandeb) and FN9 (Israel-Palestine) draw on the *same* v2 narrative N3 with very different actual sub-frames. The seed FN list naturally split N3 in three places. That is the empirical signal — one v2 narrative is doing the work of three FNs' worth of distinct framings.

**Recommendation**: Split. Both halves keep the same coalition; framing_keywords and topic_keywords partition cleanly along the lines above. Migration cost: low (both halves are operational tier; matcher reruns automatically).

---

### A2. N5 `multipolar_anti_us_hegemony` — MEDIUM-STRONG SPLIT

**Proposed split** into two narratives along the operational/ideological line that the v2 worksheet already maintains elsewhere:
- `multipolar_systemic_alternative` — Coalition: `[ASIA-CHINA, MIDEAST-IRAN, ASIA-NORKOREA]`, **ideological** tier. Frames US-led order as hegemony to be replaced by multipolar architecture (BRICS+, Russia-China-Iran-DPRK alignment, dollar de-dependence, Global South solidarity). General-purpose worldview.
- `iran_axis_of_resistance` — Coalition: `[MIDEAST-IRAN]` (with armed-group affiliates as actor extensions). Frames the Iran-aligned regional armed-group network as legitimate liberation against Israeli/US occupation.

**Vocabulary evidence** (from N5's framing_keywords list, partitioned):

Cluster A (systemic/multipolar): `US hegemony`, `unilateralism`, `imperialism`, `Cold War mentality`, `collective punishment`, `regime change`, `multipolar`, `BRICS`, `Global South`. Applies broadly across China, Iran, DPRK, Russia, and Global South contexts.

Cluster B (axis-of-resistance specific): `Axis of Resistance`, `legitimate resistance`, `liberation`, `foreign occupation` (in Israeli context), Iran's `moral duty` to support armed groups. Applies specifically to the Iran-Hezbollah-Hamas-Houthis-PMF network.

**Will they fire without each other?** Yes. Chinese statements on US sanctions on Cuba/Venezuela use cluster A vocabulary without any cluster B (Axis of Resistance never appears). Iranian statements on Hezbollah's Lebanon operations use cluster B without engaging the broader BRICS+ framing. DPRK statements on USFK use cluster A only. Cluster B is genuinely Iran-specific subject-matter, while cluster A is the broad shared anti-hegemonic worldview across the China-Iran-DPRK-Russia-aligned space.

**Counter-argument**: the unity rule says "applies to many friction nodes does not split it" — and on first reading cluster B is just cluster A applied to the Israel-Palestine FN. The strong rebuttal is that the *actor coalition is different*: cluster A is genuinely shared across China, Iran, DPRK; cluster B is Iran-specific, with a distinct loaded vocabulary (`Axis of Resistance`, `liberation`, `legitimate resistance`) that Chinese and DPRK sources rarely deploy.

**Borderline assessment**: medium-strong, not as clean as N3. Recommendation is to split, but with explicit acknowledgement that cluster B could alternatively be modeled as an Iran-coalition narrative branching off, while cluster A stays as the multi-actor ideological narrative. The v2 worksheet's coalition field would need to handle this — N5's coalition is `[ASIA-CHINA, MIDEAST-IRAN, ASIA-NORKOREA]`, but Axis-of-Resistance vocabulary is genuinely Iran-only.

**FN evidence**: FN6 (Bab el-Mandeb), FN9 (Israel-Palestine) need the resistance-axis frame specifically; FN1 (Taiwan), FN5 (AI/semiconductors), FN10 (climate regulation), FN11 (electoral legitimacy in the Americas) need the systemic-multipolar frame and would be over-flagged by the resistance vocabulary if not split.

**Recommendation**: Split, with the borderline acknowledgement above. User should weigh: is the vocabulary distinction sharp enough to justify two narrative IDs, or sharp enough only to live as `framing_keywords` partitions inside one narrative?

---

### A3. N7 `us_hemispheric_primacy` — MEDIUM SPLIT (possibly)

**Proposed split**:
- `us_hemispheric_exclusion_of_rivals` — pressure-campaign sanctions, exclusion of foreign powers, Monroe-Doctrine revival, regime change in Venezuela/Cuba/Nicaragua.
- `us_territorial_acquisition_norm_break` — Greenland acquisition, Panama Canal "reclamation", Canada union/economic-coercion discourse. Distinct because the contested phenomenon is the *transfer norm*, not the *exclusion norm*.

**Vocabulary evidence**:

Cluster A: `Monroe Doctrine`, `Western Hemisphere`, `regime change Latin America`, `pressure campaign`, `hostile foothold`, `sphere of influence`. Applies to Venezuela, Cuba, anti-Russia/China posture in the region.

Cluster B: `acquire Greenland`, `reclaim Panama Canal`, `unfair partner` (Canada), `51st state` discourse. Applies to allied/Western-aligned territories, not to adversary regimes.

**Will they fire without each other?** Yes. Venezuela-sanctions / Maduro-pressure-campaign coverage rarely invokes Greenland-acquisition vocabulary. Greenland/Panama/Canada coverage rarely invokes Monroe-Doctrine-against-Russia-China vocabulary. The targets, the legal mechanisms, and the loaded vocabulary diverge.

**Borderline assessment**: medium. They share a coalition (US) and a deep logic (US strategic primacy in the hemisphere). But the v2 narrative has them merged with quite different vocabularies and quite different target sets. The unity rule's "interlock by design" test (as applied to N4 Russia-defensive-imperialism) would suggest these *don't* interlock — Trump-era Greenland-acquisition discourse does not require Monroe-Doctrine-against-Maduro discourse to make sense, and vice versa.

**Argument against split**: both are Trump-era / nationalist-Republican primacy logic. They might be one worldview applied to two different target sets. If the v2 unity rule means "one worldview = one narrative regardless of how many FNs it touches", then N7 stays merged.

**Recommendation**: borderline. If the user reads them as one worldview applied to multiple FNs, keep merged. If the user reads them as distinct strategic postures (exclusion of rivals vs. territorial revisionism against allies), split. Lower confidence than A1 and A2.

---

### A4. N9 `ukraine_resistance_to_russia` — WEAK / NO SPLIT

**Considered**: split between Ukrainian military-survival vocabulary (`Western hesitation`, `decisive weapons`, `lost territory`) and Ukrainian moral-frame vocabulary (`unprovoked invasion`, `genocide Ukraine`, `Russian imperialism`, `victim-blaming`).

**Vocabulary evidence**: the two clusters do mostly co-fire in Ukrainian government and Ukrainian-media coverage. Zelensky's public statements interlock material requests (ATACMS, Patriot, F-16) with moral framing (unprovoked, genocidal, Russian imperialism) by design. Ukraine never separates them, and rhetorically they reinforce each other.

**Recommendation**: keep merged. This is the same pattern as N4 (Russia-defensive-imperialism) — interlocking vocabulary, single worldview, applies across many FNs (territorial integrity, weapons aid, sanctions, accession).

---

### A5. N24 `africa_great_power_competition_navigation` — WEAK SPLIT (flag for review)

**Considered**: split between East Africa BRI/AFRICOM/Camp-Lemonnier framing and Horn of Africa Bab-el-Mandeb chokepoint / Houthi-shipping framing.

**Vocabulary evidence**: framing_keywords are mostly shared (`sovereign navigation`, `diversified partnerships`, `non-alignment Africa`). Chokepoint-specific vocabulary (`Bab el-Mandeb`, `Red Sea security`) is more concentrated in Horn coverage but used across both. Topic keywords overlap heavily (Djibouti is both East-Africa-BRI and Horn-chokepoint).

**Will they fire without each other?** Marginally. Mombasa-port BRI coverage doesn't usually need Houthi-shipping vocabulary; Houthi-shipping coverage doesn't usually need Lamu-port vocabulary. But the framing — sovereign navigation, diversified partnerships — is genuinely shared.

**Recommendation**: keep merged. The split would create two narratives with near-identical framing language and similar coalitions, violating the unity rule from the other direction. The two halves are *one worldview applied to two contiguous geographies*.

---

## Section B. Merge candidates

**No strong merge candidates found.** The audit looked for cases where two v2 narratives have so much vocabulary overlap that they're really one. The closest cases:

- **N10 `germany_zeitenwende_rearmament`** vs **N13 `eu_defence_rearmament`** vs **N31 `nato_burden_sharing_internal`**. All three share vocabulary (`peace dividend ended`, `defence anchor`, `2% GDP`). But they differ in coalition (Germany / EU / NATO) and in prescription specificity (German Sondervermögen, EU joint procurement / EDIS, NATO burden-sharing-fairness). The v2 worksheet already proposes folding N31 into N1; the remaining N10/N13 split is justified because the EU and German positions diverge on substance (e.g., extent of EU-level defence-industrial integration vs national German industrial protection). Keep separate.

- **N1 `west_russia_threat_response`** vs **N9 `ukraine_resistance_to_russia`**. Some vocabulary overlap (`unprovoked invasion`, `war crimes Bucha`, `Mariupol`, `Russian war crimes`). But coalitions differ (Western coalition vs Ukraine), and prescriptions differ (Western policy posture vs Ukrainian existential framing). Different worldviews speaking partly the same language about the same events; not a merge.

- **N17 `korea_peninsula_existential_security`** vs **N19 `japan_defence_normalisation`**. Both are US-allied East Asian operational defence narratives invoking DPRK launches as a justifying pressure. Vocabulary diverges enough (`Kill Chain`/`KAMD`/`KMPR`/`Washington Declaration` vs `Article 9 reinterpretation`/`counterstrike capability`). Different coalition, different doctrinal language. Not a merge.

**Conclusion**: no merges recommended. The v2 worksheet's existing merges (N1 from 8 sources, N2 from 10, N3 from 7) appear correctly bounded.

---

## Section C. Missing narratives

Cross-referenced with the seed FN list (Output 1). Listed by priority.

### C1. EU digital / tech sovereignty — HIGH PRIORITY

**Coalition**: `[NON-STATE-EU]` (with member-state extensions: Germany, France, Netherlands).
**Tier**: operational.
**Frames**: Chips Act EU, gigafactory subsidies, AI Act extraterritoriality (`Brussels effect`), GDPR-as-export-norm, sovereign-cloud programs (Gaia-X), critical-raw-materials act, foundry localisation. Distinct frame from N2 (Western anti-China decoupling) because the EU position explicitly includes *autonomy from US* as well as resilience against China.
**Needed for**: FN5 (AI and semiconductor sovereignty). Critical gap — currently FN5 has only N2 (US-led), N5 (Chinese resistance), N6 (Chinese alternative). The EU as third pole is invisible.
**1-2 sentence sketch**: The EU describes its tech and AI position in a framework of strategic autonomy from both the US tech stack and Chinese capability. Industrial policy (Chips Act, AI factories, gigafactories), regulatory extraterritoriality (AI Act, DMA, GDPR), and rare-earth-supply diversification are framed as essential to European technological sovereignty.

---

### C2. EU green-deal / CBAM-as-climate-leadership — HIGH PRIORITY

**Coalition**: `[NON-STATE-EU]`.
**Tier**: ideological.
**Frames**: CBAM as legitimate carbon-border policy and not-protectionism, EU ETS as global model, Green Deal as competitiveness-and-leadership strategy, methane regulation, deforestation regulation, Fit-for-55. The EU explicitly self-identifies as climate-leader and sees its regulatory exports as global-norm-setting.
**Needed for**: FN10 (climate regulation regime). Currently FN10 has *zero* v2 narrative coverage of the regulation-leader position; only N5's anti-hegemony Global-South-sovereignty slice gestures at the contest from one side.
**1-2 sentence sketch**: The EU describes its climate regulation suite (CBAM, ETS, Green Deal, methane regulation) as legitimate global-norm-setting and a competitive-advantage industrial strategy. Anti-CBAM positioning by Global South or US administrations is framed as a threat to the planetary regime the EU is building.

---

### C3. US energy security and energy dominance — MEDIUM PRIORITY

**Coalition**: `[AMERICAS-USA]`.
**Tier**: operational.
**Frames**: LNG export expansion, fossil-fuel-subsidy-language resistance at COPs, Paris Agreement reversibility, oil-and-gas-permit liberalisation, energy-cost-of-living framing, anti-CBAM positioning. Distinct US energy frame that the v2 worksheet does not have because both N7 (hemispheric primacy) and N2 (China competition) speak past it.
**Needed for**: FN10 (climate regulation regime). Without this narrative the FN10 contest looks one-sided in the v2 set.
**1-2 sentence sketch**: The US describes its energy posture in a framework of energy security, energy dominance, and resistance to regulatory regimes that constrain American hydrocarbons. LNG exports to Europe, fossil-fuel-permitting, and rejection of binding-emissions language at COPs are framed as legitimate national-interest energy policy.

---

### C4. Global South climate-finance-justice — MEDIUM PRIORITY (possibly fold)

**Coalition**: `[AFRICA-EAST, AFRICA-HORN, AFRICA-SAHEL, AFRICA-NIGERIA, AFRICA-DRC, AMERICAS-MEXICO, ASIA-INDIA, ASIA-SOUTHEAST]` (broad).
**Tier**: ideological.
**Frames**: loss-and-damage funding, climate-debt, transition-minerals revenue, climate-finance commitments, just-transition, common-but-differentiated-responsibility. A coherent self-frame distinct from N5 because it's about *climate norms specifically*, not generalised anti-hegemony.
**Needed for**: FN10 (climate regulation regime). Borderline whether this is a separate narrative or whether it's adequately captured by N5's Global-South-sovereignty slice. If kept separate, it's because the climate-justice vocabulary is itself a unified loaded vocabulary distinct from anti-hegemony's `BRICS / multipolar / collective punishment` register.
**1-2 sentence sketch**: African, South Asian, and Latin American states describe the climate-regulation regime in a framework of climate-debt and just-transition. Loss-and-damage funding obligations, fair-share emissions accounting, and transition-mineral revenue rights are framed as conditions for any binding regime.
**Recommendation**: discuss whether to add as a separate narrative or fold into a future N5 split.

---

### C5. Palestinian self-framing — MEDIUM PRIORITY (politically sensitive)

**Coalition**: needs a new centroid (`NON-STATE-PALESTINE` or similar) or a coalition decision.
**Tier**: probably ideological.
**Frames**: occupation, right of return, two-state framing, ICJ-and-ICC processes, settlements as illegal under international law, blockade language. Distinct from N5 because Palestinian framing isn't the same as Iran's `Axis of Resistance` framing — Palestinian Authority and broader Palestinian-civil-society discourse uses different vocabulary (rights-based, international-law-based, two-state) than the Iran-coalition resistance vocabulary.
**Needed for**: FN9 (Israel-Palestine status). Currently FN9 has the Israeli frame (N3), the Iran-coalition resistance frame (N5), and the Gulf de-escalation frame (N21) — but no Palestinian self-frame.
**1-2 sentence sketch**: Palestinian political actors (PA, civil society, diaspora, with internal disagreement among them) describe the Israel-Palestine status in a framework of occupation, denied rights, settlement illegality, and international-law remedy. Two-state framing, right of return, ICJ/ICC processes, and end-of-blockade are framed as legitimate sovereignty claims.
**Recommendation**: add. The current v2 absence is genuinely a coverage gap.

---

### C6. Post-1945 territorial-transfer norm defence — LOW PRIORITY (possibly fold)

**Coalition**: probably `[NON-STATE-EU, AMERICAS-CANADA, EUROPE-NORDIC, EUROPE-UK]` plus broader Western coalition.
**Tier**: ideological.
**Frames**: rules-based-order language, defence of the post-1945 norm against territorial acquisition by pressure, sovereign-equality, UN Charter Article 2(4). Distinct from N1 (Russia-focused threat-response) because the contest is the *transfer norm itself*, not Russia specifically.
**Needed for**: FN12 (Greenland acquisition discourse). Without it, the FN12 contest has only N7 (acquire) and N14 (Arctic sovereignty) — no explicit defence of the post-1945 acquisition prohibition.
**Recommendation**: probably fold into a future Pass 2 LIO meta-narrative cluster, since the post-1945 norm is more naturally a Liberal-International-Order ideological narrative than a stand-alone strategic narrative. Flag for Pass 2.

---

### Cross-reference summary table

| Missing narrative | Required by FN | Priority | Recommendation |
|---|---|---|---|
| EU digital/tech sovereignty | FN5 | HIGH | Add now |
| EU green-deal/CBAM | FN10 | HIGH | Add now |
| US energy security/dominance | FN10 | MEDIUM | Add now |
| Global South climate-finance-justice | FN10 | MEDIUM | Discuss |
| Palestinian self-framing | FN9 | MEDIUM | Add now |
| Post-1945 transfer-norm defence | FN12 | LOW | Defer to Pass 2 (LIO) |

---

## Section D. Granularity verdict

**Top-line: the v2 worksheet is approximately right at the strategic level but has uneven coverage and one clear under-split. Net assessment: a structural pass is worth doing before going to schema, but the pass is small (one definite split, one probable split, ~3 high-priority additions) and should not delay schema work by more than a few days.**

The v2 worksheet's strengths:
- The unity-rule logic (one worldview = one loaded vocabulary across many FNs) is correctly applied to N1 and N4. These are the hardest cases because the temptation to split them by FN is strong, and the worksheet correctly resists.
- The merge work (35 sources collapsed into 7 coalition narratives) is well-bounded. No spurious merges that need undoing.
- The framing-explicit style (loaded vocabulary in **bold quotes** tied to what it labels) is the right format and directly enables the FN-narrative cross-reference table.

The v2 worksheet's weaknesses, in order of severity:
1. **N3 is genuinely under-split**, doing the work of three FNs' frames at once. This is the single highest-confidence change. (Section A1.)
2. **Coverage gap on the normative-regime axis**: FN10 (climate regulation regime) has almost no v2 narrative coverage. FN5 (AI/semiconductors) has a third-pole gap (no EU). These are not split-or-merge problems — they are missing-narrative problems exposed by the FN seed list. The hybrid-drafting approach in concept doc section 7 was designed to surface exactly this, and it has.
3. **Coverage gap on subject populations**: FN9 has no Palestinian self-frame. This is a known politically-sensitive gap, but it is a gap.
4. **Borderline cases on N5 and N7** that the user should adjudicate. Either way is defensible; document the choice in the migration notes.

What the audit does NOT find:
- No spurious merges that need to be undone.
- No granularity drift toward source-data shape (the worksheet has resisted this — N1 across 8 sources is one narrative not eight).
- No narrative that should be deleted entirely.

**Recommendation on path forward**:
1. Apply the N3 split (highest confidence, lowest disruption). Re-run matching.
2. Decide N5 split (medium-strong evidence, real cost if got wrong because N5 is broad-impact). Discuss with user before applying.
3. Hold N7 decision; revisit after looking at actual headline samples for cluster A vs cluster B vocabulary in current data.
4. Add C1, C2, C3, C5 (high/medium-priority missing narratives) before schema migration. They each have a clear coalition and a clear loaded vocabulary; drafting cost is small.
5. Defer C4 (climate-finance-justice) and C6 (transfer-norm) to a Pass 2 alongside the LIO cluster.

This is enough work for ~2-3 days of careful drafting. Do not block schema migration on it past a week.

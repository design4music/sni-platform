# P0(a) -- Narrative archetype grouping (meta axis)

Artifact for `NARRATIVE_CONSOLIDATION_SPEC.md` 3.A3 step 1, feeding **DG-0 #1**. Read-only; nothing was written to the database.

## Method, and what changed from the first attempt

The first version of this artifact clustered narratives by **publisher-set overlap**. That was the wrong axis. The 9 meta-narratives are a *claim-type* axis; publisher bloc is a *who* axis, and the two are orthogonal. Empirically the publisher signal does not discriminate at all -- narratives carry 22.5 publishers on average and the same Western wire set appears in ~42% of them -- so the clustering collapsed into one 87-member bloc spanning 86 friction nodes, from Arctic climate alarm to Hungary rule-of-law to the Cuba embargo. No single meta is assignable to such a group, so it could not feed DG-0.

This version groups on the meta axis directly. Each narrative gets a **mechanically proposed** meta from two measured signals, blended 50/50:

1. **kNN (k=5) over `strategic_narratives`** -- v1's 260 active rows carry *human* meta assignments. v1's content is being retired, but the meta layer is explicitly preserved (spec 1), and those rows are the only existing record of how this project maps a claim to a meta.
2. **Cosine against each meta's own `meta_narratives.signals`** vocabulary plus its description.

**Trust calibration: leave-one-out accuracy against v1's own human labels is 68%** (majority-class baseline is 21%). That is good enough to *pre-group* and far too weak to *auto-assign*. What you are approving below is the grouping, not the individual rows.

**Margin calibration.** Confidence is the relative gap between the top two metas, `(top1-top2)/top1`. Measured against v1's human labels it is a real signal, so the cutoff is a coverage/accuracy trade you can move:

| rel. margin cutoff | coverage | accuracy |
|---|---:|---:|
| >= 0.50 | 135/260 (52%) | 86% |
| >= 0.40 | 161/260 (62%) | 81% |
| >= 0.30 **(in use)** | 195/260 (75%) | 76% |
| >= 0.25 | 202/260 (78%) | 75% |
| >= 0.20 | 210/260 (81%) | 73% |
| >= 0.10 | 234/260 (90%) | 70% |
| >= 0.00 | 260/260 (100%) | 68% |

Narratives below the cutoff are **not** placed in an archetype -- they are assigned BOTH metas -- primary and secondary (DG-0 #4). A near-tie between two metas is not a failure to classify; it is the honest answer, and it is why populating secondary metas now makes the review EASIER rather than harder: no narrative has to be forced into one box.

| | |
|---|---|
| active narratives | 411 |
| single clear meta | 271 |
| primary + secondary meta | 140 |
| **archetypes (meta x sign)** | **22** |

### Proposed distribution across the 9 metas

| meta | narratives | share |
|---|---:|---:|
| `sovereign_resistance` | 90 | 22% |
| `security_order` | 80 | 19% |
| `great_power_competition` | 66 | 16% |
| `economic_order` | 50 | 12% |
| `liberal_international_order` | 45 | 11% |
| `plural_world_order` | 41 | 10% |
| `global_justice` | 21 | 5% |
| `information_order` | 10 | 2% |
| `planetary_governance` | 8 | 2% |

Spec 3.A4 predicted `security_order` and `global_justice` would dominate and `planetary_governance` come out near-empty. Check the table above against that expectation -- a large divergence is a finding about the scorer, the corpus, or both.

---

## Archetypes

Each section is **one decision**: accept the proposed meta for the whole group, or name a different one. Per-narrative exceptions go in the `overrides:` block of `db/registry/narrative_meta_mapping.yaml` (P0b).

`titles` is the effective attributed-title count -- direct `title_narratives` for atomic narratives, the `THEATER_ROLLUP_SQL` union for theater ones. Rows below the proposed publication gate (25) are marked `[thin]`.

### A01 -- `sovereign_resistance`, critical (-) -- 63 narratives, 6,661 titles

- **proposed meta**: `sovereign_resistance`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (16), `ru` (15), `west_eu` (8), `china` (7), `mixed` (6), `arab_gulf` (4)
- **secondary metas proposed**: `liberal_international_order` (5), `security_order` (4), `plural_world_order` (3), `great_power_competition` (2)
- **top publishers**: RT (27), TASS (EN) (27), Reuters (26), BBC World (26), Associated Press (26), Deutsche Welle (26), France 24 (EN) (26), El País (25)
- **regions**: AMERICAS-CUBA (8), AMERICAS-USA (6), AFRICA-HORN (6), ASIA-TAIWAN (5), AMERICAS-ANDEAN (4), NON-STATE-EU (4)
- **friction nodes**: 51 distinct -- alberta_separatism_us_ties, cuba_embargo_sanctions, cuba_energy_collapse, cuba_theater, ethiopia_regional_confrontation, eu_migration_burden_sharing

<details><summary>63 narratives</summary>

- `west_iran_regime_change_doctrine` (iran_theater, stance -2, 2746 titles, coalition `west_us`, also `security_order`) -- Western coalition: the Iranian regime is illegitimate and replaceable
- `uscat_canadian_consensus` (us_canada_theater, stance -2, 262 titles, coalition `west`, also `plural_world_order`) -- An ally treated as a target
- `mexth_mexican_sovereignty` (mexico_theater, stance -2, 238 titles, coalition `global_south`) -- US pressure violates Mexican sovereignty and dignity
- `jc_theater_chinese_state_counter` (japan_china_theater, stance -2, 233 titles, coalition `china`) -- Japan is breaking the postwar settlement and reviving militarism behind a pacifist facade
- `taiwan_strait_beijing_counter` (taiwan_strait_theater, stance -2, 208 titles, coalition `ru`) -- Taiwan is Chinese territory and foreign interference, not Chinese action, is the provocation
- `sahel_theater_state_collapse_critique` (sahel_theater, stance -2, 197 titles, coalition `west`) -- A managed collapse: military rule that delivers neither security nor politics
- `cuba_theater_anti_imperial` (cuba_theater, stance -2, 193 titles, coalition `mixed`, also `global_justice`) -- A siege to break a sovereign nation that refuses to submit
- `myanmar_illegitimate_junta_rule` (myanmar_civil_conflict, stance -2, 184 titles, coalition `west`) -- Sham election, illegitimate junta
- `eu_sovereigntist_revolt` (eu_cohesion_theater, stance -1, 130 titles, coalition `west_eu`) -- Nations and voters are resisting an overreaching Brussels
- `usdom_fed_capture_risk` (us_fed_independence, stance -1, 127 titles, coalition `west_us`) -- Political pressure is testing the limits of central-bank independence
- `usdom_epstein_obstruction` (us_epstein_elite_network, stance -1, 126 titles, coalition `west_us`) -- Disclosure is being managed, delayed and selectively withheld
- `mexican_sovereignty_defense` (us_mexico_military_pressure, stance -2, 122 titles, coalition `global_south`) -- US pressure violates Mexican sovereignty; non-intervention is the red line
- `usdom_loyalty_hollowing` (us_executive_loyalty, stance -1, 111 titles, coalition `west_us`) -- Professional institutions are being hollowed out by loyalty tests
- `cuba_theater_western_critique` (cuba_theater, stance -1, 104 titles, coalition `west`) -- The pressure campaign has become a humanitarian and legal problem of its own
- `greenland_sovereignty_defense` (greenland_control, stance -1, 104 titles, coalition `west_eu`) -- Coercion over Greenland is unacceptable; Danish/European sovereignty must be defended
- `somali_territorial_integrity` (somaliland_recognition_contest, stance -2, 104 titles, coalition `mixed`) -- A violation of Somalia's territorial integrity
- `jde_militarism_revival` (japan_defense_expansion, stance -2, 96 titles, coalition `china`, also `plural_world_order`) -- Japan is hollowing out its pacifist constitution and reviving militarism
- `cuba_economic_warfare` (cuba_embargo_sanctions, stance -2, 90 titles, coalition `mixed`) -- The blockade is economic warfare against a sovereign nation
- `beijing_antiseparatism_unity` (taiwan_political_warfare, stance -1, 90 titles, coalition `ru`) -- Opposing separatism and building cross-strait unity is legitimate, and the governing party obstructs
- `alberta_unity_defence` (alberta_separatism_us_ties, stance -1, 85 titles, coalition `west`) -- A dangerous bluff, and an opening for outside pressure
- `jc_taiwan_interference_charge` (japan_china_taiwan_question, stance -2, 84 titles, coalition `china`) -- Japan's Taiwan remarks are interference in China's internal affairs and breach the postwar understan
- `migration_national_control` (eu_migration_burden_sharing, stance -1, 72 titles, coalition `west_eu`) -- Member states must control borders and curb irregular migration
- `horn_sovereignty_bloc` (horn_africa_theater, stance -2, 68 titles, coalition `arab_gulf`) -- Sovereignty and non-interference
- `one_china_consensus` (taiwan_international_recognition, stance -1, 63 titles, coalition `ru`) -- The one-China principle is settled international consensus and Taiwan's diplomacy is doomed to fail
- `caucasus_russia_china_counter` (caucasus_theater, stance -2, 61 titles, coalition `ru`, also `great_power_competition`) -- The West is destabilizing Russia's neighbourhood and dragging it into an anti-Russian orbit
- `ethiopia_renewed_war_alarm` (ethiopia_regional_confrontation, stance -1, 56 titles, coalition `west`) -- A second northern war in the making
- `pla_sovereignty_enforcement` (taiwan_military_pressure, stance -1, 56 titles, coalition `ru`) -- Military and coast guard activity around Taiwan is routine, lawful enforcement of Chinese sovereignt
- `casp_sovereignty_defence` (canada_sovereignty_pressure, stance -2, 47 titles, coalition `west`) -- Sovereignty under pressure
- `cuba_collapse_starvation_siege` (cuba_energy_collapse, stance -2, 47 titles, coalition `mixed`) -- Starvation by siege is a deliberate instrument of policy
- `colombia_theater_external_pressure` (colombia_theater, stance -1, 45 titles, coalition `west`) -- Decisions shaped from outside
- `awp_russian_capture` (armenia_western_pivot, stance -2, 43 titles, coalition `ru`) -- Armenia is being dragged into an anti-Russian orbit by a Western-engineered capture
- `saudi_coalition_legitimacy_restoration` (saudi_houthi_war, stance -2, 43 titles, coalition `arab_gulf`) -- Saudi-led coalition is restoring the internationally-recognised Yemeni government
- `sahel_state_losing_ground` (sahel_jihadist_insurgency, stance -2, 39 titles, coalition `west`) -- The state is losing territory it cannot recover
- `ethiopia_regional_revisionism` (ethiopia_regional_confrontation, stance -2, 31 titles, coalition `arab_gulf`) -- A revisionist power destabilising the region
- `cuba_lifelines_humanitarian_duty` (cuba_external_lifelines, stance -1, 29 titles, coalition `west`) -- Relief is a humanitarian obligation and third states should not be coerced
- `horn_russian_iranian_counter` (horn_africa_theater, stance -2, 28 titles, coalition `ru`) -- Russian and Iranian counter-framing
- `memory_historical_accountability` (japan_china_memory_wars, stance -2, 27 titles, coalition `china`, also `liberal_international_order`) -- Japan has never reckoned with its wartime aggression and continues to honour war criminals
- `sahel_theater_civilian_cost` (sahel_theater, stance -1, 27 titles, coalition `arab_gulf`) -- The population pays for every side's campaign
- `western_intervention_scrutiny` (us_mexico_military_pressure, stance -1, 23 titles, coalition `west`) -- US pressure is straining the relationship and inviting scandal
- `france_popular_will` (french_nationalist_challenge, stance -1, 22 titles, coalition `west_eu`) -- The establishment and the courts are blocking the popular will
- `cuba_collapse_humanitarian_alarm` (cuba_energy_collapse, stance -1, 21 titles, coalition `west`) -- A humanitarian emergency is unfolding whoever is to blame
- `taiwan_us_pawn` (taiwan_us_security_commitment, stance -2, 21 titles, coalition `ru`) -- US arms sales violate the one-China principle and use Taiwan as a pawn Washington will discard
- `usdom_loyalty_court_politics` (us_executive_loyalty, stance -2, 20 titles, coalition `china`, also `liberal_international_order`) -- Court politics inside a distracted superpower
- `usdom_violence_instability` (us_political_violence, stance -2, 18 titles, coalition `china`, also `liberal_international_order`) -- A superpower unable to secure its own political life
- `latam_theater_coercion_critique` (latam_hemispheric_theater, stance -2, 14 titles, coalition `ru`, also `plural_world_order`) -- Washington coerces, Beijing is punished
- `colombia_us_imperial_overreach` (colombia_us_alignment, stance -2, 13 titles, coalition `mixed`) -- A sovereign state treated as a subordinate
- `migration_eu_failure_kremlin` (eu_migration_burden_sharing, stance -2, 12 titles, coalition `ru`) -- EU migration policy is chaos and a failure of the European project
- `colombia_transition_institutional_concern` (colombia_political_transition, stance -1, 11 titles, coalition `west_eu`, also `liberal_international_order`) -- The result strains the guardrails
- `somali_foreign_militarisation_critique` (somalia_state_security, stance -2, 10 titles, coalition `ru`) -- Foreign militarisation is the destabiliser
- `cuba_sanctions_overreach` (cuba_embargo_sanctions, stance -1, 9 titles, coalition `west`) -- Extraterritorial sanctions are collective punishment
- `cuba_force_unlawful` (cuba_military_coercion, stance -1, 9 titles, coalition `west`, also `liberal_international_order`) -- Threatening to take an island is unlawful and reckless
- `budget_national_sovereignty` (eu_budget_sovereignty, stance -1, 8 titles, coalition `west_eu`) -- Brussels wants more money and power at the expense of nations and taxpayers
- `alberta_external_amplification` (alberta_separatism_us_ties, stance -2, 5 titles, coalition `china`) -- A fraying federation, watched from outside
- `kurdish_political_rights_critique` (turkey_kurdish_question, stance -1, 5 titles, coalition `west`, also `security_order`) -- Turkey collapses Kurdish political rights into terror designation
- `france_decline_kremlin` (french_nationalist_challenge, stance -2, 4 titles, coalition `ru`, also `great_power_competition`) -- France's model is failing amid chaos and instability
- `ggd_sovereignty_stability` (georgia_geopolitical_drift, stance -2, 4 titles, coalition `ru`) -- Tbilisi is resisting a Western-orchestrated colour revolution and defending its sovereignty
- `hungary_sovereignty_interference` (hungary_rule_of_law, stance -1, 4 titles, coalition `west_eu`) -- Brussels interferes in a sovereign nation's democracy
- `pyongyang_closed_the_door` (inter_korean_relations, stance -2, 4 titles, coalition `west`, also `security_order`) -- Pyongyang has formally closed the inter-Korean track
- `drc_minerals_as_resource_capture` (drc_minerals_competition, stance -2, 2 titles, coalition `ru`, also `security_order`) -- A takeover of an established position
- `drc_sanctions_rejected` (drc_peace_process, stance -2, 2 titles, coalition `mixed`) -- The designated parties reject the designations
- `hungary_brussels_coercion` (hungary_rule_of_law, stance -2, 2 titles, coalition `ru`) -- Brussels overreaches against a sovereign nation
- `colombia_peace_process_failure` (colombia_armed_groups_peace, stance -1, 1 titles, coalition `global_south`) -- Talks bought the cartels time
- `realignment_new_majority` (eu_right_realignment, stance -1, 1 titles, coalition `west_eu`) -- The right has a democratic mandate to govern and to cooperate

</details>

### A02 -- `security_order`, supportive (+) -- 48 narratives, 8,180 titles

- **proposed meta**: `security_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (16), `west_us` (6), `global_south` (4), `israel` (4), `iran` (4), `mixed` (4)
- **secondary metas proposed**: `great_power_competition` (5), `sovereign_resistance` (4), `economic_order` (1), `plural_world_order` (1)
- **top publishers**: Reuters (17), BBC World (16), Associated Press (16), Deutsche Welle (16), The Guardian (15), Bloomberg (15), Fox News (15), New York Times (14)
- **regions**: ASIA-INDIA (5), AMERICAS-USA (4), AMERICAS-ANDEAN (4), MIDEAST-ISRAEL (4), ASIA-NORKOREA (4), MIDEAST-YEMEN (3)
- **friction nodes**: 46 distinct -- korea_theater, south_asia_theater, arctic_military_presence, armenia_azerbaijan_settlement, balochistan_insurgency, canada_sovereignty_pressure

<details><summary>48 narratives</summary>

- `israel_existential_self_defense` (israel_theater, stance +2, 2541 titles, coalition `israel`) -- Israel: existential self-defense against multi-front Iran-led axis
- `israel_self_defense_north` (israel_lebanon_border, stance +2, 1546 titles, coalition `israel`) -- Israel: push Hezbollah north of the Litani; restore northern security
- `israel_dismantle_hamas` (gaza_war, stance +2, 686 titles, coalition `israel`) -- Israel: war is non-negotiable until Hamas is dismantled and hostages freed
- `ukrainian_defense_and_deep_strikes` (ukraine_battlefield, stance +2, 516 titles, coalition `west`, also `sovereign_resistance`) -- Ukraine-aligned: defending the front, liberating territory
- `iran_axis_of_resistance` (iran_proxy_network, stance +2, 451 titles, coalition `iran`) -- Iran-aligned: Axis of Resistance as legitimate liberation movement
- `iran_hormuz_sovereign_pressure` (strait_of_hormuz_sovereignty, stance +1, 299 titles, coalition `iran`) -- Iran: Hormuz as sovereign waters and deterrence asymmetry
- `aid_sustains_defense` (western_aid_to_ukraine, stance +2, 243 titles, coalition `west`) -- Western military, economic, and industrial aid is sustaining and must be scaled
- `taiwan_coercion_deterrence` (taiwan_military_pressure, stance +1, 203 titles, coalition `west`, also `great_power_competition`) -- Chinese military and coast guard pressure around Taiwan is coercion that must be deterred
- `iran_nuclear_sovereign_right` (iran_nuclear_program, stance +2, 147 titles, coalition `iran`) -- Iran: nuclear program as sovereign right and deterrence hedge
- `south_asia_indian_account` (south_asia_theater, stance +2, 129 titles, coalition `india`) -- India is the status-quo power defending its territory against a militancy-exporting neighbour
- `arctic_nato_deterrence` (arctic_military_presence, stance +1, 122 titles, coalition `west_us`, also `great_power_competition`) -- NATO must reinforce the Arctic to deter a growing Russian (and Chinese) threat
- `korea_sanctioned_bloc` (korea_theater, stance +2, 122 titles, coalition `ru`, also `plural_world_order`) -- A bloc of sanctioned states drawing closer around Pyongyang
- `israel_preemptive_strike_doctrine` (israel_iran_strikes, stance +2, 115 titles, coalition `israel`) -- Israel: preemptive and reactive strikes against an existential nuclear-bound enemy
- `militancy_pakistan_sponsorship` (india_pakistan_militancy, stance +2, 100 titles, coalition `india`) -- Pakistan shelters and directs the groups that attack India
- `south_asia_pakistani_security_account` (south_asia_theater, stance +1, 74 titles, coalition `global_south`) -- Pakistan is fighting militancy on two fronts against externally backed enemies
- `cartel_offensive_progress` (mexico_cartel_war, stance +2, 72 titles, coalition `west`) -- The militarised offensive is working: captures and takedowns weaken the cartels
- `houthis_fourth_front_solidarity` (yemen_red_sea_theater, stance +2, 71 titles, coalition `mixed`) -- Houthi attacks on Israel and Red Sea shipping are legitimate Gaza solidarity
- `pakafg_counterterror_necessity` (pakistan_afghanistan_border, stance +2, 67 titles, coalition `global_south`) -- Strikes target militant sanctuaries Kabul refuses to close
- `iran_gulf_resistance_solidarity` (gulf_attacks_on_arab_states, stance +2, 62 titles, coalition `iran`) -- Iran-aligned: Axis of Resistance as legitimate liberation movement
- `usdom_violence_protective_response` (us_political_violence, stance +1, 49 titles, coalition `west_us`, also `information_order`) -- The protective response worked and the perpetrators face the law
- `us_russia_theater_engagement_case` (us_russia_theater, stance +1, 49 titles, coalition `west`, also `sovereign_resistance`) -- Managed engagement is the responsible way to handle a nuclear-armed adversary
- `houthi_naval_pressure_legitimate` (red_sea_shipping_security, stance +2, 46 titles, coalition `mixed`) -- Houthi targeting of Israel-linked shipping is legitimate non-state pressure tied to Gaza ceasefire
- `sahel_counterterror_necessity` (sahel_jihadist_insurgency, stance +2, 46 titles, coalition `ru`) -- A legitimate war against armed extremist groups
- `jde_deterrence_response` (japan_defense_expansion, stance +2, 43 titles, coalition `west`, also `great_power_competition`) -- Japan's defense build-up is a proportionate response to China's military expansion
- `korea_allied_dual_track` (korea_theater, stance +2, 43 titles, coalition `west`, also `great_power_competition`) -- Hold the line, keep the door open: deterrence alongside engagement
- `sahel_theater_regional_security_response` (sahel_theater, stance +1, 40 titles, coalition `global_south`) -- A regional security emergency being fought by national armies
- `pkk_terror_full_disarmament` (turkey_kurdish_question, stance +2, 38 titles, coalition `turkey`) -- PKK / YPG / SDF are one terror organisation; disarmament is the only acceptable path
- `foreign_military_withdrawal_demand` (syria_counter_terror, stance +1, 30 titles, coalition `mixed`) -- Foreign military presence violates sovereignty and should withdraw
- `us_russia_new_treaty_needed` (us_russia_arms_control, stance +1, 29 titles, coalition `west`) -- The expiry of New START is dangerous and a successor framework must be built
- `thaicam_thai_sovereignty_defence` (thailand_cambodia_border, stance +2, 24 titles, coalition `asean`, also `sovereign_resistance`) -- The border and Koh Kood are Thai territory; Cambodia breaches the memoranda and provokes
- `alliance_deterrence_necessary` (korea_peninsula_deterrence, stance +2, 23 titles, coalition `west`) -- The alliance and its exercises are what hold deterrence together
- `inter_korean_engagement` (inter_korean_relations, stance +2, 20 titles, coalition `west`, also `great_power_competition`) -- Engagement can lower tension and reopen the inter-Korean track
- `colombia_theater_negotiated_path` (colombia_theater, stance +1, 19 titles, coalition `west`) -- Bargaining still works, at home and abroad
- `indus_treaty_obsolete` (indus_water_sharing, stance +2, 18 titles, coalition `india`) -- The 1960 treaty no longer fits India's needs and its terms are being revisited
- `colombia_us_rapprochement` (colombia_us_alignment, stance +1, 14 titles, coalition `west`) -- The channel was repaired
- `aas_durable_peace` (armenia_azerbaijan_settlement, stance +2, 12 titles, coalition `west`) -- A historic peace is ending a 30-year conflict and normalizing the region
- `kashmir_integral_to_india` (kashmir_dispute, stance +2, 12 titles, coalition `india`) -- Jammu and Kashmir is Indian territory; Pakistan must vacate what it holds
- `baloch_foreign_backed_insurgency` (balochistan_insurgency, stance +2, 9 titles, coalition `global_south`) -- The attacks are externally sponsored terrorism, not a domestic grievance
- `houthi_resistance_strikes_legitimate` (houthi_strikes_on_israel, stance +2, 9 titles, coalition `mixed`) -- Houthi missile and drone strikes on Israel are legitimate axis-of-resistance action
- `mexth_us_pressure_justified` (mexico_theater, stance +2, 9 titles, coalition `west_us`) -- US pressure on Mexico is justified and is producing results
- `nk_sovereign_deterrent` (north_korea_missile_program, stance +2, 7 titles, coalition `ru`) -- The arsenal is a sovereign deterrent that will not be traded away
- `ven_coercion_justified` (us_venezuela_relations, stance +1, 7 titles, coalition `west`) -- The US removed a narco-dictator and a security threat
- `colombia_transition_mandate` (colombia_political_transition, stance +2, 6 titles, coalition `west`) -- Voters chose a harder line
- `sahel_separatism_as_jihadist_alliance` (sahel_tuareg_separatism, stance +2, 5 titles, coalition `ru`) -- The separatists are a front for the armed extremists
- `defence_europe_must_pay` (europe_us_defence_dependence, stance +2, 4 titles, coalition `west_us`, also `economic_order`) -- Europe has freeloaded on US protection for decades and must finally pay its share
- `casp_continental_dependence` (canada_sovereignty_pressure, stance +2, 1 titles, coalition `west_us`) -- Canada depends on American protection
- `colombia_peace_negotiation_defense` (colombia_armed_groups_peace, stance +1, 1 titles, coalition `west`, also `sovereign_resistance`) -- Talks are how the war ends
- `intervention_necessity` (us_mexico_military_pressure, stance +2, 1 titles, coalition `west_us`) -- US action against the cartels is necessary because Mexico cannot or will not stop them

</details>

### A03 -- `great_power_competition`, critical (-) -- 43 narratives, 3,645 titles

- **proposed meta**: `great_power_competition`  (accept / replace: __________)
- **coalitions** (derived from publishers): `ru` (14), `west` (10), `china` (7), `west_eu` (5), `west_us` (4), `mixed` (3)
- **secondary metas proposed**: `security_order` (4), `sovereign_resistance` (3), `global_justice` (3), `planetary_governance` (2)
- **top publishers**: Global Times (22), CGTN (22), China Daily (22), RT (20), TASS (20), TASS (EN) (19), Xinhua (16), Press TV (16)
- **regions**: EUROPE-RUSSIA (11), OCEANIA-AUSTRALIA (4), ASIA-CHINA (3), ASIA-NORKOREA (3), AMERICAS-VENEZUELA (3), ASIA-CAUCASUS (2)
- **friction nodes**: 33 distinct -- arctic_theater, aukus_alliance_reliability, australia_theater, korea_peninsula_deterrence, korea_theater, russia_europe_theater

<details><summary>43 narratives</summary>

- `russia_europe_kremlin_counter` (russia_europe_theater, stance -2, 737 titles, coalition `ru`, also `information_order`) -- Western Russophobia, NATO encirclement and self-defeating sanctions manufacture a "Russia threat"
- `ven_theater_anti_imperial` (venezuela_theater, stance -2, 365 titles, coalition `mixed`, also `global_justice`) -- A US imperial operation to seize a sovereign nation's oil
- `korea_hardening_threat` (korea_theater, stance -2, 347 titles, coalition `west`) -- A hardening threat while the pressure regime frays
- `arctic_russia_china_counter` (arctic_theater, stance -2, 335 titles, coalition `ru`) -- NATO expansion and the US Greenland grab are the real provocation and Western hypocrisy
- `sudan_proxy_war_critique` (sudan_civil_war, stance -2, 240 titles, coalition `west`, also `plural_world_order`) -- Sudan war is sustained by UAE arms to RSF; Egypt/Saudi back the army
- `nk_proliferation_threat` (north_korea_missile_program, stance -2, 213 titles, coalition `west`) -- An expanding arsenal that must be contained
- `west_gulf_aggression_response` (gulf_attacks_on_arab_states, stance -2, 153 titles, coalition `west_us`, also `security_order`) -- US-Israel-Saudi-UAE: Iranian and Houthi strikes are state-sponsored aggression
- `nato_complicity_provocation` (russia_airspace_incursions, stance -2, 141 titles, coalition `ru`) -- NATO territory hosts and enables Ukrainian drone strikes; incursions are Western provocations, not R
- `hybrid_russophobia_denial` (russia_hybrid_warfare, stance -2, 121 titles, coalition `ru`) -- Hybrid-threat claims are evidence-free Russophobia; shadow-fleet seizures are piracy
- `aid_as_escalation_and_proxy` (western_aid_to_ukraine, stance -2, 115 titles, coalition `ru`, also `security_order`) -- Western aid prolongs proxy war, wastes taxpayer money, escalates direct NATO-Russia risk
- `ven_coercion_anti_imperial` (us_venezuela_relations, stance -2, 107 titles, coalition `mixed`, also `global_justice`) -- US gunboat imperialism against a sovereign nation
- `horn_western_alarm` (horn_africa_theater, stance -1, 105 titles, coalition `west`) -- Western alarm at fragmentation and famine
- `us_china_summit_new_chapter` (us_china_summit_diplomacy, stance -2, 98 titles, coalition `china`) -- Leader diplomacy opens a new chapter proving cooperation beats containment
- `nato_encirclement_provocation` (russia_nato_deterrence, stance -2, 92 titles, coalition `ru`) -- NATO's eastern build-up is aggressive encirclement driving escalation
- `arctic_western_sovereignty_stewardship` (arctic_theater, stance -1, 87 titles, coalition `west_eu`, also `planetary_governance`) -- Coercion and reckless exploitation of the Arctic must be resisted — for allied sovereignty and the c
- `arctic_nato_militarization` (arctic_military_presence, stance -1, 50 titles, coalition `ru`) -- NATO is militarising the Arctic and provoking a dangerous new confrontation
- `cjer_lawful_regulation` (china_japan_economic_restrictions, stance -2, 42 titles, coalition `china`) -- China's export controls are lawful regulation and Japan's own conduct caused the downturn
- `alliance_autonomy_strain` (korea_peninsula_deterrence, stance -1, 40 titles, coalition `west`, also `sovereign_resistance`) -- Seoul is pushing for autonomy and the alliance terms are being renegotiated
- `cuba_force_imperial_aggression` (cuba_military_coercion, stance -2, 32 titles, coalition `mixed`) -- Gunboat diplomacy against a small neighbour is imperial aggression
- `us_china_summit_weak_hand` (us_china_summit_diplomacy, stance -1, 30 titles, coalition `west`, also `economic_order`) -- Washington left the summit with little to show for it
- `aukus_capability_doubt` (aukus_alliance_reliability, stance -1, 28 titles, coalition `west`) -- AUKUS is delivering less than promised and binds Australia to an unreliable partner
- `australia_alliance_scepticism` (australia_theater, stance -1, 28 titles, coalition `west`) -- The alliance is delivering less than Australia was promised
- `australia_china_counter` (australia_theater, stance -2, 21 titles, coalition `china`) -- Australia is manufacturing a threat and importing a bloc confrontation it does not need
- `western_systemic_alarm` (ukraine_official_corruption, stance -1, 17 titles, coalition `west`, also `global_justice`) -- Western alarm: high-level corruption threatens Ukraine credibility and aid
- `senkaku_chinese_rights_protection` (senkaku_diaoyu_islands, stance -2, 16 titles, coalition `china`, also `security_order`) -- Diaoyu Dao is inherent Chinese territory and coast guard patrols are lawful rights protection
- `port_expropriation_coercion` (latam_port_infrastructure_control, stance -2, 14 titles, coalition `china`) -- Expropriation under US pressure
- `sahel_patron_model_failing` (sahel_security_patron_contest, stance -2, 13 titles, coalition `west`, also `sovereign_resistance`) -- The replacement security model is buckling
- `ven_coercion_western_critical` (us_venezuela_relations, stance -1, 10 titles, coalition `west_eu`, also `sovereign_resistance`) -- The intervention is lawless regime change
- `zc_sovereignty_threat` (zangezur_corridor, stance -1, 10 titles, coalition `ru`, also `security_order`) -- The corridor is an extraterritorial threat to Armenian sovereignty and Iran's border
- `trade_mutual_benefit` (australia_china_trade_leverage, stance -2, 8 titles, coalition `china`) -- Australia-China trade is complementary and growing, and quota mechanics are routine rather than coer
- `cpc_russia_iran_resistance` (caucasus_power_competition, stance -2, 5 titles, coalition `ru`) -- Outside penetration of the region is a hostile encirclement to be resisted
- `arctic_route_strategic_threat` (arctic_shipping_routes, stance -1, 4 titles, coalition `west_us`) -- Russian and Chinese control of Arctic routes is a strategic threat
- `colombia_theater_hegemonic_critique` (colombia_theater, stance -2, 4 titles, coalition `ru`) -- The region as a sphere of influence
- `mexth_anti_hegemony_rift` (mexico_theater, stance -2, 4 titles, coalition `ru`) -- US pressure on Mexico exposes American imperialism in its own backyard
- `anti_hegemony_rift` (us_mexico_military_pressure, stance -2, 4 titles, coalition `ru`) -- US pressure on Mexico is imperial overreach in Washington's backyard
- `alliance_containment_instrument` (korea_peninsula_deterrence, stance -2, 2 titles, coalition `ru`) -- Washington treats its allies as instruments for containing China
- `korea_us_containment_critique` (korea_theater, stance -2, 2 titles, coalition `ru`) -- US alliances on the peninsula serve the containment of China
- `aukus_bloc_confrontation` (aukus_alliance_reliability, stance -2, 1 titles, coalition `china`) -- AUKUS is bloc confrontation that spreads nuclear submarine technology and fuels an arms race
- `latam_theater_strategic_warning` (latam_hemispheric_theater, stance -2, 1 titles, coalition `west_us`) -- Commerce with a strategic tail
- `resource_strategic_penetration` (latam_resource_access, stance -2, 1 titles, coalition `west_us`) -- Beijing is buying strategic depth
- `russia_europe_critical_restraint` (russia_europe_theater, stance -1, 1 titles, coalition `west_eu`, also `planetary_governance`) -- Threat inflation, militarisation and escalation risk: a skeptical European counter-current
- `militarisation_overreach` (russia_nato_deterrence, stance -1, 1 titles, coalition `west_eu`, also `plural_world_order`) -- Threat inflation and war-economy drift are a costly overreach
- `securitisation_caution` (russia_hybrid_warfare, stance -1, 0 titles, coalition `west_eu`) -- Caution against over-attribution: accidents and criminality get mislabeled as Kremlin sabotage

</details>

### A04 -- `security_order`, critical (-) -- 30 narratives, 7,185 titles

- **proposed meta**: `security_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (10), `israel` (5), `ru` (4), `india` (3), `global_south` (2), `west_us` (2)
- **secondary metas proposed**: `sovereign_resistance` (5), `plural_world_order` (2), `global_justice` (2), `liberal_international_order` (2)
- **top publishers**: Associated Press (11), Al Jazeera (11), Reuters (10), BBC World (10), Fox News (10), Deutsche Welle (9), The Guardian (9), France 24 (EN) (9)
- **regions**: EUROPE-UKRAINE (4), ASIA-PAKISTAN (3), ASIA-INDIA (3), MIDEAST-LEVANT (3), AFRICA-DRC (2), MIDEAST-YEMEN (2)
- **friction nodes**: 29 distinct -- pakistan_afghanistan_border, balochistan_insurgency, colombia_us_alignment, europe_us_theater, great_lakes_theater, houthi_strikes_on_israel

<details><summary>30 narratives</summary>

- `russia_special_military_operation` (ukraine_war_theater, stance -2, 1461 titles, coalition `ru`, also `sovereign_resistance`) -- Russia's special military operation defends Russian-speaking populations from Western-backed Kyiv re
- `hezbollah_resistance_north` (israel_lebanon_border, stance -2, 920 titles, coalition `mixed`) -- Hezbollah and aligned: northern front as legitimate solidarity resistance
- `russian_smo_operations` (ukraine_battlefield, stance -2, 874 titles, coalition `ru`) -- Russia-aligned: the special military operation advancing -- liberation of Donbass
- `west_iran_proxy_network_threat` (iran_proxy_network, stance -2, 860 titles, coalition `west_us`) -- Western coalition: Iran proxy network as terror infrastructure
- `europe_us_transatlantic_rupture` (europe_us_theater, stance -1, 775 titles, coalition `west`, also `plural_world_order`) -- A vital alliance is rupturing, forcing an alarmed Europe to defend itself and its interests
- `west_iran_nuclear_threat` (iran_nuclear_program, stance -2, 660 titles, coalition `west_us`) -- Western coalition: Iran nuclear as existential threat
- `infrastructure_war_energy_terror` (ukraine_infrastructure_war, stance -2, 259 titles, coalition `ru`) -- Russia-aligned: Kyiv attacks civilian energy and endangers nuclear safety
- `russian_maximalist_peace` (ukraine_peace_negotiations, stance -2, 227 titles, coalition `ru`, also `global_justice`) -- Settlement must complete all SMO objectives: denazification, demilitarisation, neutrality, recognise
- `iran_legitimate_retaliation_doctrine` (israel_iran_strikes, stance -2, 171 titles, coalition `mixed`) -- Iran-aligned: Iranian retaliation is legitimate state self-defense under the UN Charter
- `iran_proxy_destabilisation` (yemen_red_sea_theater, stance -2, 165 titles, coalition `arab_gulf`) -- Houthis are an Iranian proxy that has hijacked the Yemeni state
- `pakafg_civilian_harm_alarm` (pakistan_afghanistan_border, stance -1, 136 titles, coalition `west`) -- The border war is killing civilians and risks a wider conflict
- `pakafg_afghan_sovereignty_violation` (pakistan_afghanistan_border, stance -2, 128 titles, coalition `india`, also `sovereign_resistance`) -- Pakistani strikes on Afghan territory are aggression against a sovereign state
- `south_asia_indian_critique_of_pakistan` (south_asia_theater, stance -2, 102 titles, coalition `india`) -- Pakistan's conduct beyond its borders and failures within them destabilise the region
- `sahel_northern_autonomy_claim` (sahel_tuareg_separatism, stance -2, 80 titles, coalition `west`) -- Northern Mali is a political question, not only a military one
- `somali_fragility_and_harm` (somalia_state_security, stance -1, 72 titles, coalition `west`) -- A fragile state and an abandoned population
- `myanmar_criminal_economy_spillover` (myanmar_civil_conflict, stance -1, 44 titles, coalition `west`) -- Scam-compound economy and cross-border crime
- `baloch_pakistan_internal_failure` (balochistan_insurgency, stance -2, 39 titles, coalition `india`, also `sovereign_resistance`) -- The insurgency is Pakistan's own governance failure, not foreign subversion
- `great_lakes_proxy_war_and_its_costs` (great_lakes_theater, stance -2, 39 titles, coalition `west`, also `plural_world_order`) -- A cross-border war paid for by civilians
- `syria_jihadist_takeover_warning` (syria_theater, stance -2, 31 titles, coalition `israel`) -- HTS rule is rebranded al-Qaeda and a long-term security threat
- `recognition_legitimises_jihadists` (syria_recognition_and_normalisation, stance -2, 27 titles, coalition `israel`, also `liberal_international_order`) -- International recognition whitewashes a former al-Qaeda operative
- `colombia_us_coercion` (colombia_us_alignment, stance -1, 25 titles, coalition `west`) -- Threats replaced diplomacy
- `us_russia_relief_rewards_moscow` (us_russia_sanctions_leverage, stance -1, 25 titles, coalition `west`, also `liberal_international_order`) -- Easing sanctions hands Moscow a windfall and squanders the West's main lever
- `houthi_iranian_proxy_aggression` (houthi_strikes_on_israel, stance -2, 16 titles, coalition `israel`) -- Houthi strikes are Iranian-orchestrated proxy aggression requiring kinetic answer
- `indus_water_weaponisation` (indus_water_sharing, stance -2, 15 titles, coalition `global_south`) -- Suspending the treaty is coercion against a downstream population
- `m23_externally_backed_offensive` (m23_conflict, stance -2, 11 titles, coalition `west`) -- An externally backed offensive
- `cartel_narco_state_critique` (mexico_cartel_war, stance -1, 10 titles, coalition `west`, also `global_justice`) -- Militarisation is failing and the state is compromised: collusion, corruption and impunity
- `militancy_indian_pretext` (india_pakistan_militancy, stance -2, 5 titles, coalition `global_south`, also `sovereign_resistance`) -- India weaponises unproven allegations to justify pressure and strikes
- `turkey_wrong_side_on_iran` (turkey_iran_war_spillover, stance -1, 5 titles, coalition `israel`, also `sovereign_resistance`) -- Erdogan shields the Iranian regime from accountability
- `israeli_strikes_on_syria_legitimate` (syria_israeli_strikes, stance -1, 3 titles, coalition `israel`) -- Israeli strikes on Syria are legitimate preventive defense
- `escalation_risk_restraint` (russia_airspace_incursions, stance -1, 0 titles, coalition `west_eu`, also `great_power_competition`) -- Shoot-down authority and forward posture risk uncontrolled escalation; many incidents are accidental

</details>

### A05 -- `liberal_international_order`, critical (-) -- 28 narratives, 4,350 titles

- **proposed meta**: `liberal_international_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (10), `china` (10), `ru` (3), `west_eu` (3), `west_us` (2)
- **secondary metas proposed**: `sovereign_resistance` (9), `plural_world_order` (2), `global_justice` (1), `security_order` (1)
- **top publishers**: France 24 (EN) (17), Reuters (15), BBC World (15), Associated Press (15), France 24 (13), Deutsche Welle (13), Le Monde (12), The Guardian (12)
- **regions**: AMERICAS-USA (12), AFRICA-SAHEL (3), AFRICA-DRC (2), ASIA-CAUCASUS (1), ASIA-PAKISTAN (1), NON-STATE-EU (1)
- **friction nodes**: 26 distinct -- us_domestic_theater, us_electoral_legitimacy, armenia_azerbaijan_settlement, balochistan_insurgency, canada_sovereignty_pressure, drc_minerals_competition

<details><summary>28 narratives</summary>

- `west_hormuz_freedom_of_navigation` (strait_of_hormuz_sovereignty, stance -1, 1864 titles, coalition `west_us`) -- Western coalition: free passage through Hormuz is non-negotiable
- `usdom_theater_liberal_alarm` (us_domestic_theater, stance -1, 1111 titles, coalition `west`, also `sovereign_resistance`) -- Checks and balances under sustained strain
- `usdom_theater_decline` (us_domestic_theater, stance -2, 292 titles, coalition `china`, also `sovereign_resistance`) -- American decline and the collapse of its claim to model status
- `freedom_of_navigation_defense` (red_sea_shipping_security, stance -1, 165 titles, coalition `west`) -- Houthi attacks on commercial vessels violate UNCLOS; coalition naval ops are necessary
- `usdom_epstein_western_impunity` (us_epstein_elite_network, stance -2, 134 titles, coalition `china`, also `sovereign_resistance`) -- A Western elite protecting itself, exposed by its own scandal
- `usdom_electoral_franchise_threat` (us_electoral_legitimacy, stance -1, 116 titles, coalition `west_us`) -- The rules are being rewritten to shape the result in advance
- `scs_rules_based_maritime_order` (south_china_sea_claims, stance -2, 102 titles, coalition `west`) -- China's claims lack legal basis and its conduct coerces smaller claimants
- `sahel_democratic_closure` (sahel_junta_consolidation, stance -2, 100 titles, coalition `west_eu`, also `sovereign_resistance`) -- Military rule is closing the last civic space
- `zelensky_regime_corruption` (ukraine_official_corruption, stance -2, 72 titles, coalition `ru`, also `security_order`) -- Zelensky inner circle is systemically corrupt; Western aid is being stolen at scale
- `usdom_ice_american_repression` (us_interior_immigration_enforcement, stance -2, 67 titles, coalition `china`) -- A self-described democracy policing its own population
- `us_china_trade_unilateralism` (us_china_trade_tariffs, stance -2, 59 titles, coalition `china`, also `plural_world_order`) -- US tariffs are unilateral coercion that damages the global trading order
- `ven_transition_democracy_betrayed` (venezuela_political_transition, stance -1, 58 titles, coalition `west_eu`) -- Chavismo survives; the opposition is frozen out
- `usdom_courts_politicised` (us_judicial_constraint, stance -2, 28 titles, coalition `china`, also `sovereign_resistance`) -- A judiciary treated as an instrument of factional power
- `baloch_rights_repression` (balochistan_insurgency, stance -1, 25 titles, coalition `west`) -- The state answers Baloch grievances with force and detention
- `uscat_external_rift` (us_canada_theater, stance -1, 21 titles, coalition `china`) -- The Western bloc coming apart
- `m23_civilian_toll` (m23_conflict, stance -1, 19 titles, coalition `west`, also `sovereign_resistance`) -- The population pays for every advance
- `sahel_rupture_deepens_isolation` (sahel_france_rupture, stance -2, 19 titles, coalition `west`, also `sovereign_resistance`) -- The break leaves the Sahel with fewer options, not more
- `usdom_fed_dollar_decline` (us_fed_independence, stance -2, 17 titles, coalition `china`, also `plural_world_order`) -- Politicised money and the erosion of the dollar order
- `defence_nato_racket` (europe_us_defence_dependence, stance -2, 13 titles, coalition `ru`, also `sovereign_resistance`) -- NATO is a crumbling Cold-War racket through which the US bleeds Europe
- `drc_minerals_human_cost` (drc_minerals_competition, stance -1, 11 titles, coalition `west`, also `global_justice`) -- The price is paid at the pit
- `sahel_counterinsurgency_abuses` (sahel_jihadist_insurgency, stance -1, 11 titles, coalition `west`) -- The counterinsurgency is killing the civilians it claims to protect
- `turkey_authoritarian_drift_critique` (turkey_democratic_backsliding, stance -2, 11 titles, coalition `west_eu`) -- Imamoglu trial and CHP crackdown dismantle Turkish democracy
- `usdom_press_hypocrisy` (us_press_freedom, stance -2, 10 titles, coalition `china`, also `information_order`) -- Press-freedom advocacy abroad, licence pressure at home
- `usdom_electoral_democracy_facade` (us_electoral_legitimacy, stance -2, 9 titles, coalition `china`) -- A system that lectures others while contesting its own elections
- `casp_imperial_overreach` (canada_sovereignty_pressure, stance -1, 7 titles, coalition `china`) -- Imperial overreach in its own hemisphere
- `us_russia_normalisation_premature` (us_russia_bilateral_channel, stance -1, 5 titles, coalition `west`) -- Normalising relations while the war continues legitimises the Kremlin and sidelines Europe
- `aas_contested_settlement` (armenia_azerbaijan_settlement, stance -2, 4 titles, coalition `ru`, also `sovereign_resistance`) -- The settlement is a contested, externally shaped arrangement rather than a genuine peace
- `thaicam_cambodian_territorial_claim` (thailand_cambodia_border, stance -2, 0 titles, coalition `west`) -- Thailand occupies Cambodian ground; the ICJ ruling and demarcation favour Cambodia

</details>

### A06 -- `sovereign_resistance`, supportive (+) -- 27 narratives, 3,074 titles

- **proposed meta**: `sovereign_resistance`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (5), `west_us` (5), `ru` (3), `west_eu` (3), `iran` (2), `turkey` (2)
- **secondary metas proposed**: `economic_order` (3), `liberal_international_order` (3), `plural_world_order` (2), `security_order` (2)
- **top publishers**: Reuters (11), Associated Press (10), BBC World (10), Deutsche Welle (10), Bloomberg (9), Financial Times (9), Anadolu Agency (9), France 24 (EN) (8)
- **regions**: AMERICAS-USA (6), EUROPE-BALKANS (2), NON-STATE-EU (2), AFRICA-DRC (2), AFRICA-SAHEL (2), EUROPE-UKRAINE (2)
- **friction nodes**: 27 distinct -- balkan_foreign_capital, balkan_theater, essequibo_dispute, eu_right_realignment, europe_us_theater, french_nationalist_challenge

<details><summary>27 narratives</summary>

- `iran_sovereign_existence` (iran_theater, stance +2, 836 titles, coalition `iran`) -- Iran: Islamic Republic as sovereign state under permanent foreign assault
- `ukrainian_maximalist_peace` (ukraine_peace_negotiations, stance +2, 498 titles, coalition `west_eu`, also `security_order`) -- Just peace requires full Russian withdrawal to 1991 borders with NATO-backed security guarantees
- `sudan_state_legitimacy` (sudan_civil_war, stance +2, 351 titles, coalition `arab_gulf`) -- Sudan's army is the constitutional state defending against an RSF mutiny
- `judea_samaria_sovereignty` (west_bank_settlements, stance +1, 265 titles, coalition `israel`) -- Israeli right: Jewish sovereignty over biblical Judea-Samaria
- `usdom_theater_conservative_case` (us_domestic_theater, stance +1, 171 titles, coalition `west_us`) -- A mandate being executed against institutional resistance
- `damascus_territorial_reunification` (syria_kurdish_question, stance +2, 153 titles, coalition `turkey`) -- Damascus must restore central authority over all Syrian territory
- `usdom_ice_enforcement_mandate` (us_interior_immigration_enforcement, stance +1, 102 titles, coalition `west_us`) -- Enforcement is delivering a mandate voters asked for
- `balkan_theater_external_backing` (balkan_theater, stance +1, 97 titles, coalition `ru`) -- Russia and China back the region's governments as they resist Western-aligned pressure
- `usdom_fed_orderly_succession` (us_fed_independence, stance +1, 93 titles, coalition `west_us`) -- A normal succession that leaves the institution intact
- `scs_chinese_sovereignty_claim` (south_china_sea_claims, stance +2, 89 titles, coalition `china`) -- China's South China Sea claims are historic, lawful, and enforcement is defensive
- `us_russia_buyer_autonomy` (us_russia_sanctions_leverage, stance +1, 79 titles, coalition `india`, also `economic_order`) -- Sovereign buyers never accepted that US permission was required
- `us_russia_theater_buyer_autonomy` (us_russia_theater, stance +1, 79 titles, coalition `india`, also `plural_world_order`) -- Third countries treat the rivalry as something to navigate, not to join
- `taiwan_international_space` (taiwan_international_recognition, stance +1, 55 titles, coalition `west`, also `liberal_international_order`) -- Taiwan's international participation is legitimate and Beijing's campaign to isolate it is coercive
- `france_republican_defense` (french_nationalist_challenge, stance +2, 44 titles, coalition `west_eu`, also `liberal_international_order`) -- The rule of law and republican norms must apply to the RN
- `realignment_firewall_defense` (eu_right_realignment, stance +2, 43 titles, coalition `west_eu`) -- The mainstream must not normalise the radical right
- `turkey_anti_graft_legalism_defense` (turkey_democratic_backsliding, stance +2, 31 titles, coalition `turkey`) -- Imamoglu indictment is routine anti-corruption process
- `great_lakes_engagement_working` (great_lakes_theater, stance +2, 28 titles, coalition `west`, also `plural_world_order`) -- Outside engagement is starting to bite
- `houthi_authority_legitimate_resistance` (saudi_houthi_war, stance +2, 19 titles, coalition `iran`) -- Houthi-led Sanaa authority is legitimate national resistance to Saudi-Western intervention
- `europe_us_america_first` (europe_us_theater, stance +2, 10 titles, coalition `west_us`, also `economic_order`) -- America First: a freeloading, over-regulating Europe must pay, open up and submit
- `balkan_investment_development` (balkan_foreign_capital, stance +1, 7 titles, coalition `west`, also `economic_order`) -- Foreign investment brings jobs, tourism and international partnership to the Western Balkans
- `ven_essequibo_venezuelan_claim` (essequibo_dispute, stance +1, 7 titles, coalition `mixed`, also `great_power_competition`) -- Essequibo is historically Venezuelan territory
- `sahel_russian_partnership_delivers` (sahel_security_patron_contest, stance +2, 6 titles, coalition `ru`, also `liberal_international_order`) -- The new partnership delivers what the old one did not
- `sahel_break_with_paris_justified` (sahel_france_rupture, stance +2, 5 titles, coalition `ru`) -- Cutting ties ends a relationship that never became equal
- `leverage_justified` (us_mexico_trade_border, stance +2, 4 titles, coalition `west_us`, also `security_order`) -- Tariff and border pressure are legitimate leverage that forces Mexican cooperation
- `m23_backing_charge_rejected` (m23_conflict, stance +1, 1 titles, coalition `global_south`) -- The accused parties reject the charge
- `us_russia_engagement_necessary` (us_russia_bilateral_channel, stance +1, 1 titles, coalition `west`) -- Keeping a working channel with Moscow is how wars are ended and accidents avoided
- `reform_in_progress` (ukraine_official_corruption, stance +1, 0 titles, coalition `west`) -- Ukrainian anti-corruption institutions are investigating and prosecuting successfully

</details>

### A07 -- `economic_order`, supportive (+) -- 24 narratives, 1,497 titles

- **proposed meta**: `economic_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (16), `west_us` (3), `west_eu` (2), `global_south` (2), `ru` (1)
- **secondary metas proposed**: `great_power_competition` (4), `global_justice` (1), `information_order` (1), `sovereign_resistance` (1)
- **top publishers**: Bloomberg (18), Financial Times (18), Reuters (17), Deutsche Welle (15), Associated Press (14), Wall Street Journal (14), The Guardian (14), BBC World (13)
- **regions**: AMERICAS-USA (7), NON-STATE-EU (3), AMERICAS-CANADA (2), ASIA-CHINA (2), ASIA-CAUCASUS (2), AMERICAS-BRAZIL (2)
- **friction nodes**: 23 distinct -- us_russia_sanctions_leverage, alberta_separatism_us_ties, arctic_resources_competition, australia_china_trade_leverage, balkan_theater, caucasus_power_competition

<details><summary>24 narratives</summary>

- `infrastructure_war_economy_strikes` (ukraine_infrastructure_war, stance +2, 364 titles, coalition `west`, also `great_power_competition`) -- Ukraine-aligned: precision degradation of Russia's war economy; Russian grid strikes are terror
- `jc_theater_japanese_western_consensus` (japan_china_theater, stance +2, 265 titles, coalition `west`, also `great_power_competition`) -- China's pressure on Japan is coercion that hardens Japanese resolve rather than changing it
- `us_china_export_control_necessity` (us_china_tech_restrictions, stance +1, 250 titles, coalition `west`, also `great_power_competition`) -- Restricting advanced chip access is necessary to hold a security-critical technology lead
- `ven_oil_restart_opportunity` (venezuela_sanctions_oil, stance +1, 150 titles, coalition `west`) -- Sanctions relief reopens Venezuela's oil to the world
- `us_china_minerals_dependence_risk` (us_china_critical_minerals, stance +1, 95 titles, coalition `west`) -- US dependence on Chinese rare earths is a vulnerability that must be engineered away
- `cjer_economic_coercion` (china_japan_economic_restrictions, stance +2, 91 titles, coalition `west`) -- China is weaponizing trade, minerals and tourism to punish Japanese political speech
- `us_russia_sanctions_illegitimate` (us_russia_sanctions_leverage, stance +2, 89 titles, coalition `ru`, also `plural_world_order`) -- Unilateral sanctions have failed and Washington has been forced to admit it
- `trade_derisking_necessity` (australia_china_trade_leverage, stance +2, 47 titles, coalition `west`) -- Concentrated dependence on the Chinese market is a strategic vulnerability Australia must reduce
- `cpc_western_engagement` (caucasus_power_competition, stance +1, 23 titles, coalition `west`) -- Outside engagement brings beneficial partnership and integration to the region
- `us_china_summit_engagement_works` (us_china_summit_diplomacy, stance +1, 22 titles, coalition `west`, also `great_power_competition`) -- Leader-level engagement is putting a floor under a dangerous rivalry
- `latam_theater_regional_agency` (latam_hemispheric_theater, stance +2, 21 titles, coalition `global_south`, also `sovereign_resistance`) -- Courted by all sides, committed to none
- `us_russia_relief_pragmatic` (us_russia_sanctions_leverage, stance +1, 19 titles, coalition `west`) -- Sanctions relief is a pragmatic response to energy-market reality
- `arctic_resource_development` (arctic_resources_competition, stance +1, 14 titles, coalition `west`, also `global_justice`) -- Arctic energy and minerals are a legitimate sovereign development opportunity
- `drc_minerals_as_development` (drc_minerals_competition, stance +2, 9 titles, coalition `west`) -- Capital arriving at last
- `resource_sovereign_development` (latam_resource_access, stance +1, 8 titles, coalition `global_south`) -- The region sets its own terms
- `balkan_theater_investment_opportunity` (balkan_theater, stance +1, 7 titles, coalition `west_eu`) -- Foreign capital and international partnerships are framed as development opportunities governments a
- `trade_us_tariffs_justified` (transatlantic_trade, stance +2, 6 titles, coalition `west_us`) -- US tariffs are a justified correction of unfair European trade practices
- `zc_connectivity_prosperity` (zangezur_corridor, stance +1, 6 titles, coalition `west`) -- The corridor unlocks connectivity, trade and a regional peace dividend
- `us_china_tariff_leverage` (us_china_trade_tariffs, stance +1, 4 titles, coalition `west`) -- Tariffs and trade probes are legitimate leverage against an unbalanced relationship
- `budget_more_europe` (eu_budget_sovereignty, stance +2, 3 titles, coalition `west_eu`) -- A capable Union needs stronger common financing
- `alberta_legitimate_grievance` (alberta_separatism_us_ties, stance +1, 2 titles, coalition `west`) -- A grievance the federation has not answered
- `uscat_provincial_grievance` (us_canada_theater, stance +1, 2 titles, coalition `west`) -- A federation strained from within
- `tech_eu_overreach` (europe_us_tech_sovereignty, stance +2, 0 titles, coalition `west_us`, also `information_order`) -- EU tech rules are protectionist harassment of successful American companies
- `usca_trade_rebalancing` (us_canada_trade_coercion, stance +2, 0 titles, coalition `west_us`) -- Rebalancing an unfair trading relationship

</details>

### A08 -- `economic_order`, critical (-) -- 24 narratives, 1,533 titles

- **proposed meta**: `economic_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (10), `global_south` (4), `west_eu` (3), `china` (3), `west_us` (2), `ru` (1)
- **secondary metas proposed**: `great_power_competition` (4), `liberal_international_order` (1), `security_order` (1), `planetary_governance` (1)
- **top publishers**: Reuters (14), Associated Press (14), Financial Times (14), The Guardian (13), Deutsche Welle (13), Bloomberg (13), France 24 (EN) (12), El País (12)
- **regions**: AMERICAS-USA (6), AMERICAS-BRAZIL (5), AMERICAS-MEXICO (3), AFRICA-DRC (2), ASIA-NORKOREA (2), ASIA-TAIWAN (2)
- **friction nodes**: 20 distinct -- latam_hemispheric_theater, transatlantic_trade, us_mexico_trade_border, venezuela_sanctions_oil, drc_peace_process, great_lakes_theater

<details><summary>24 narratives</summary>

- `trade_european_defence` (transatlantic_trade, stance -1, 504 titles, coalition `west_eu`) -- Trump's tariffs are economic coercion that Europe must resist with unity and countermeasures
- `usca_economic_coercion` (us_canada_trade_coercion, stance -2, 136 titles, coalition `west`) -- Tariff coercion against a treaty partner
- `ven_oil_imperial_plunder` (venezuela_sanctions_oil, stance -2, 123 titles, coalition `mixed`) -- Washington is looting Venezuela's oil wealth
- `trade_coercion_pushback` (us_mexico_trade_border, stance -2, 112 titles, coalition `global_south`) -- US tariff threats are economic coercion that violate USMCA and Mexican dignity
- `dprk_russia_blood_for_technology` (north_korea_russia_alignment, stance -2, 86 titles, coalition `west`, also `great_power_competition`) -- Troops and shells for cash and missile technology
- `trade_western_vassalage` (transatlantic_trade, stance -2, 78 titles, coalition `ru`, also `plural_world_order`) -- US tariffs expose how Washington milks its European "vassals" and the hollowness of the alliance
- `mexth_western_scrutiny` (mexico_theater, stance -1, 61 titles, coalition `west`) -- US pressure strains the relationship and carries scandal and economic risk
- `us_china_western_engagement_critique` (us_china_theater, stance -1, 46 titles, coalition `west`) -- The instruments are backfiring: costs at home, allies hedging, leverage overstated
- `trade_pressure_sovereignty_defense` (latam_us_trade_pressure, stance -1, 45 titles, coalition `west`) -- Tariffs punish a trade partner
- `taiwan_strait_western_doubt` (taiwan_strait_theater, stance -1, 44 titles, coalition `west`) -- Taiwan's protection is not assured -- Washington may bargain the island away and its defences fall s
- `us_commitment_doubted` (taiwan_us_security_commitment, stance -1, 44 titles, coalition `west`, also `planetary_governance`) -- Washington's commitment is wavering and Taiwan risks being traded away
- `us_china_ai_suppression` (us_china_ai_primacy, stance -2, 38 titles, coalition `china`, also `great_power_competition`) -- Chinese AI succeeds on merit and Washington answers with smears and blacklists
- `latam_theater_terms_imposed` (latam_hemispheric_theater, stance -1, 37 titles, coalition `west_us`) -- The costs land locally
- `trade_economic_disruption` (us_mexico_trade_border, stance -1, 37 titles, coalition `west_us`) -- Tariff brinkmanship disrupts an integrated economy and rattles markets
- `latam_theater_european_objection` (latam_hemispheric_theater, stance -2, 35 titles, coalition `west_eu`) -- Europe resists its own agreement
- `us_china_tech_containment` (us_china_tech_restrictions, stance -2, 29 titles, coalition `china`, also `great_power_competition`) -- Export controls are containment dressed as security, and they are failing
- `us_china_tariff_self_harm` (us_china_trade_tariffs, stance -1, 19 titles, coalition `west`) -- Tariff escalation costs US industry and consumers more than it wins
- `us_china_minerals_lawful_leverage` (us_china_critical_minerals, stance -2, 17 titles, coalition `china`) -- China's minerals controls are lawful management and Western blocs undermine open trade
- `ven_oil_deals_opacity` (venezuela_sanctions_oil, stance -1, 15 titles, coalition `west_eu`) -- The oil restart is opaque and serves Trump, not Venezuelans
- `beijing_shields_pyongyang` (north_korea_china_patronage, stance -2, 11 titles, coalition `west`, also `great_power_competition`) -- Beijing's lifeline is what keeps the pressure regime from working
- `mercosur_european_obstruction` (latam_eu_market_access, stance -1, 6 titles, coalition `global_south`) -- Europe signs, then restricts
- `drc_accords_stalling` (drc_peace_process, stance -1, 5 titles, coalition `west`, also `liberal_international_order`) -- Signed, stalled, and unenforced
- `great_lakes_scepticism_of_outside_fixes` (great_lakes_theater, stance -1, 4 titles, coalition `global_south`, also `security_order`) -- African scepticism about externally designed fixes
- `resource_extractivism_critique` (latam_resource_access, stance -1, 1 titles, coalition `global_south`) -- Extraction externalises its costs

</details>

### A09 -- `great_power_competition`, supportive (+) -- 23 narratives, 5,202 titles

- **proposed meta**: `great_power_competition`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (14), `mixed` (3), `ru` (3), `west_us` (2), `west_eu` (1)
- **secondary metas proposed**: `plural_world_order` (3), `economic_order` (2), `security_order` (2), `liberal_international_order` (1)
- **top publishers**: Bloomberg (17), Reuters (16), Financial Times (16), Wall Street Journal (16), The Guardian (15), Deutsche Welle (15), New York Times (15), Associated Press (14)
- **regions**: EUROPE-RUSSIA (5), ASIA-CHINA (3), AMERICAS-USA (3), OCEANIA-AUSTRALIA (2), ASIA-TAIWAN (2), EUROPE-GREENLAND (1)
- **friction nodes**: 23 distinct -- arctic_shipping_routes, arctic_theater, aukus_alliance_reliability, australia_theater, china_threat_assessment, greenland_control

<details><summary>23 narratives</summary>

- `ukraine_resistance_solidarity` (ukraine_war_theater, stance +2, 1585 titles, coalition `west_eu`, also `sovereign_resistance`) -- Ukraine's war of national defense deserves full Western and democratic-world solidarity
- `russia_europe_western_resolve` (russia_europe_theater, stance +2, 942 titles, coalition `west`) -- Europe must deter, defend and sanction a revanchist Russia
- `us_china_western_competition_consensus` (us_china_theater, stance +2, 754 titles, coalition `west`, also `economic_order`) -- Managed competition: hold the technology lead, reduce dependence, keep talking
- `us_china_ai_lead_contest` (us_china_ai_primacy, stance +1, 481 titles, coalition `west`) -- Chinese AI has closed the gap and the US lead is now contested on merit and by hard tactics
- `taiwan_strait_western_consensus` (taiwan_strait_theater, stance +2, 297 titles, coalition `west`, also `security_order`) -- Taiwan is a democracy under escalating Chinese coercion and its deterrence must be reinforced
- `hybrid_campaign_defence` (russia_hybrid_warfare, stance +2, 288 titles, coalition `west`) -- Russia is waging a coordinated gray-zone campaign that requires attribution and hardening
- `eastern_flank_deterrence` (russia_nato_deterrence, stance +2, 150 titles, coalition `west`) -- Eastern-flank build-up is necessary deterrence against a revanchist Russia
- `arctic_western_security_consensus` (arctic_theater, stance +2, 127 titles, coalition `west_us`) -- The Arctic must be secured against Russian militarization and Sino-Russian encroachment
- `jc_taiwan_japan_security_stake` (japan_china_taiwan_question, stance +2, 119 titles, coalition `west`, also `liberal_international_order`) -- A Taiwan contingency directly threatens Japan's security and Japan is entitled to say so
- `australia_western_consensus` (australia_theater, stance +2, 117 titles, coalition `west`) -- Australia must reduce its exposure to China and deepen its alliances
- `horn_regional_stabilisers` (horn_africa_theater, stance +1, 101 titles, coalition `mixed`, also `economic_order`) -- Regional partners rebuilding state capacity
- `us_russia_us_buildup_drives_race` (us_russia_arms_control, stance +2, 50 titles, coalition `ru`) -- US missile defence and rejected proposals are what drive the new arms race
- `china_threat_substantiated` (china_threat_assessment, stance +2, 33 titles, coalition `west`) -- Chinese espionage and military reach against Australia are real and growing
- `pacific_western_partnership` (pacific_island_contest, stance +2, 29 titles, coalition `west`, also `plural_world_order`) -- Pacific island states are choosing Australia and its partners as their security partner
- `sahel_theater_partnership_frame` (sahel_theater, stance +2, 27 titles, coalition `ru`, also `plural_world_order`) -- A sovereign realignment that is finally fighting the real enemy
- `senkaku_japanese_administration` (senkaku_diaoyu_islands, stance +2, 27 titles, coalition `west`, also `security_order`) -- The Senkakus are Japanese-administered territory and Chinese vessel entries are grey-zone pressure
- `port_control_restored` (latam_port_infrastructure_control, stance +2, 19 titles, coalition `west`) -- Host-state control restored
- `syrian_sovereignty_under_israeli_aggression` (syria_israeli_strikes, stance +2, 17 titles, coalition `mixed`) -- Israeli strikes violate Syrian sovereignty and undermine the transition
- `arctic_route_opportunity` (arctic_shipping_routes, stance +1, 13 titles, coalition `mixed`) -- Melting ice opens Arctic sea routes as a shared economic opportunity
- `aukus_strategic_necessity` (aukus_alliance_reliability, stance +2, 9 titles, coalition `west`) -- AUKUS is essential to Australian deterrence and is progressing
- `latam_theater_eastern_partnership` (latam_hemispheric_theater, stance +1, 9 titles, coalition `ru`, also `plural_world_order`) -- A second partner on offer
- `greenland_us_strategic_claim` (greenland_control, stance +2, 5 titles, coalition `west_us`) -- US control of Greenland is a strategic and national-security necessity
- `us_commitment_firm` (taiwan_us_security_commitment, stance +1, 3 titles, coalition `west`) -- US arms supply and the security commitment to Taiwan are holding and being strengthened

</details>

### A10 -- `plural_world_order`, critical (-) -- 21 narratives, 3,282 titles

- **proposed meta**: `plural_world_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `ru` (6), `west` (4), `china` (3), `mixed` (3), `west_us` (2), `israel` (2)
- **secondary metas proposed**: `great_power_competition` (5), `security_order` (2), `sovereign_resistance` (2), `liberal_international_order` (2)
- **top publishers**: CGTN (10), China Daily (10), Global Times (9), RT (8), TASS (EN) (8), Reuters (7), BBC World (7), France 24 (EN) (7)
- **regions**: AMERICAS-USA (6), NON-STATE-EU (4), MIDEAST-TURKEY (2), EUROPE-UKRAINE (2), ASIA-CHINA (1), AMERICAS-VENEZUELA (1)
- **friction nodes**: 20 distinct -- eu_strategic_autonomy, china_threat_assessment, essequibo_dispute, europe_us_defence_dependence, europe_us_theater, israel_theater

<details><summary>21 narratives</summary>

- `multipolar_anti_israel_alignment` (israel_theater, stance -1, 1268 titles, coalition `mixed`) -- Russia / China / Global South: Israel as US-backed colonial outlier
- `sanctions_ineffective_and_backfiring` (russia_sanctions_regime, stance -2, 556 titles, coalition `ru`) -- Sanctions hurt Europe more than Russia; frozen-asset seizure would destroy financial trust
- `us_china_beijing_moscow_counter` (us_china_theater, stance -2, 241 titles, coalition `ru`) -- Containment is the anomaly: cooperation, lawful trade and a multipolar order
- `kurdish_self_administration` (syria_kurdish_question, stance -1, 199 titles, coalition `west`, also `security_order`) -- Kurdish self-administration is a legitimate democratic experiment to be protected
- `usdom_courts_deference` (us_judicial_constraint, stance -1, 151 titles, coalition `west_us`, also `sovereign_resistance`) -- The bench is expanding executive discretion rather than checking it
- `proxy_war_restraint_critique` (ukraine_war_theater, stance -1, 143 titles, coalition `mixed`) -- The war is a US/NATO proxy war prolonged by Western intervention; settlement requires restraint
- `frontline_freeze_settlement` (ukraine_peace_negotiations, stance -1, 131 titles, coalition `mixed`, also `liberal_international_order`) -- End the killing through frozen line of contact + Ukrainian neutrality, without endorsing Russian max
- `europe_us_western_disunity` (europe_us_theater, stance -2, 121 titles, coalition `ru`) -- The transatlantic split exposes Western hypocrisy and the arrival of a multipolar world
- `defence_unreliable_america` (europe_us_defence_dependence, stance -1, 100 titles, coalition `west`, also `great_power_competition`) -- A wavering America is an unreliable protector, forcing an alarmed Europe to scramble
- `turkey_two_faced_opportunist` (turkey_mediator_role, stance -2, 91 titles, coalition `israel`) -- Erdogan plays every side for influence without delivering
- `turkey_unreliable_ally_warning` (turkey_theater, stance -2, 88 titles, coalition `israel`, also `sovereign_resistance`) -- Erdogan's Turkey is a hostile or unreliable NATO partner
- `autonomy_european_awakening` (eu_strategic_autonomy, stance -1, 62 titles, coalition `west`) -- Europe is finally awakening to strategic autonomy and must build its own defence
- `autonomy_multipolar_welcome` (eu_strategic_autonomy, stance -2, 30 titles, coalition `ru`) -- European autonomy means the end of US hegemony and a welcome multipolar world
- `us_russia_theater_western_alarm` (us_russia_theater, stance -1, 30 titles, coalition `west`, also `security_order`) -- Accommodation is being granted without reciprocity, over the heads of Europe and Kyiv
- `somaliland_transactional_scramble` (somaliland_recognition_contest, stance -1, 24 titles, coalition `west_eu`, also `great_power_competition`) -- Statehood traded for bases and minerals
- `usca_bloc_fracture` (us_canada_trade_coercion, stance -1, 12 titles, coalition `china`, also `liberal_international_order`) -- The Western bloc turning on itself
- `us_china_summit_multipolar_framing` (us_china_summit_diplomacy, stance -2, 10 titles, coalition `ru`) -- Washington cannot dictate terms to Beijing
- `us_russia_washington_bad_faith` (us_russia_bilateral_channel, stance -2, 10 titles, coalition `ru`, also `great_power_competition`) -- Washington talks while acting in bad faith and refusing to treat Russia as an equal
- `china_threat_fabricated` (china_threat_assessment, stance -2, 7 titles, coalition `china`, also `great_power_competition`) -- The "China threat" is a fabricated narrative used to justify Australian alignment against Beijing
- `pacific_china_cooperation` (pacific_island_contest, stance -2, 5 titles, coalition `china`, also `great_power_competition`) -- Chinese engagement in the Pacific is ordinary development cooperation that no third party should con
- `ven_essequibo_guyana_sovereignty` (essequibo_dispute, stance -1, 3 titles, coalition `west_us`) -- Venezuela's claim is an oil-driven threat to Guyana

</details>

### A11 -- `plural_world_order`, supportive (+) -- 18 narratives, 1,042 titles

- **proposed meta**: `plural_world_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `ru` (5), `west` (4), `global_south` (2), `west_us` (2), `mixed` (2), `israel` (1)
- **secondary metas proposed**: `security_order` (1), `sovereign_resistance` (1), `liberal_international_order` (1)
- **top publishers**: TASS (EN) (9), RT (6), TASS (6), RIA Novosti (6), Anadolu Agency (5), Kommersant (5), Reuters (4), Associated Press (4)
- **regions**: ASIA-NORKOREA (2), MIDEAST-TURKEY (2), AMERICAS-USA (2), ASIA-CAUCASUS (1), AMERICAS-ANDEAN (1), AMERICAS-CUBA (1)
- **friction nodes**: 18 distinct -- caucasus_theater, colombia_theater, cuba_theater, drc_peace_process, eu_strategic_autonomy, horn_africa_theater

<details><summary>18 narratives</summary>

- `turkey_independent_middle_power` (turkey_theater, stance +2, 243 titles, coalition `mixed`) -- Turkey has earned regional stature through balanced diplomacy
- `us_russia_theater_kremlin_vindication` (us_russia_theater, stance +2, 180 titles, coalition `ru`) -- The West's containment strategy has failed and Russia is being dealt with as an equal
- `turkey_legitimate_broker` (turkey_mediator_role, stance +2, 179 titles, coalition `arab_gulf`) -- Erdogan's mediation across Gaza, Iran, Ukraine is indispensable
- `serbia_sovereignty_defense` (serbia_government_legitimacy, stance +1, 97 titles, coalition `ru`) -- Belgrade's resistance to Western pressure defends Serbia's sovereign right to choose its own path
- `dprk_russia_comradeship` (north_korea_russia_alignment, stance +2, 65 titles, coalition `ru`) -- A lawful partnership between states under the same sanctions
- `horn_new_partnerships` (horn_africa_theater, stance +2, 55 titles, coalition `israel`) -- New partnerships remaking the Horn
- `china_dprk_friendship` (north_korea_china_patronage, stance +2, 50 titles, coalition `china`) -- Traditional friendship restored, to the benefit of regional stability
- `caucasus_western_consensus` (caucasus_theater, stance +2, 43 titles, coalition `west`) -- The South Caucasus is realigning westward -- peace, connectivity and a break from Russia
- `international_engagement_pragmatic` (syria_recognition_and_normalisation, stance +2, 41 titles, coalition `west`, also `liberal_international_order`) -- Arab, Western, and Russia/Ukraine engagement with Damascus is pragmatic stabilisation
- `us_russia_washington_realism` (us_russia_bilateral_channel, stance +2, 41 titles, coalition `ru`) -- Washington is returning to realism and accepting a multipolar order
- `cuba_theater_pressure_consensus` (cuba_theater, stance +2, 20 titles, coalition `west`) -- The government, not the blockade, is what has to change
- `mercosur_market_opportunity` (latam_eu_market_access, stance +2, 13 titles, coalition `global_south`) -- The agreement opens a large market
- `sahel_sovereigntist_self_reliance` (sahel_junta_consolidation, stance +2, 8 titles, coalition `ru`, also `sovereign_resistance`) -- Reclaiming sovereignty after decades of external tutelage
- `drc_accords_are_working` (drc_peace_process, stance +2, 5 titles, coalition `west`) -- The accords are the route out of the war
- `colombia_theater_hard_turn` (colombia_theater, stance +2, 1 titles, coalition `global_south`, also `security_order`) -- The electorate chose confrontation
- `uscat_us_leverage_case` (us_canada_theater, stance +2, 1 titles, coalition `west_us`) -- A relationship being put on fairer terms
- `autonomy_illusion` (eu_strategic_autonomy, stance +2, 0 titles, coalition `west_us`) -- European strategic autonomy is a costly fantasy that only weakens NATO
- `multipolar_systemic_alternative` (iran_theater, stance +1, 0 titles, coalition `mixed`) -- Multipolar sovereignty backing for Iran

</details>

### A12 -- `liberal_international_order`, supportive (+) -- 17 narratives, 2,433 titles

- **proposed meta**: `liberal_international_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west_eu` (6), `west` (5), `west_us` (4), `ru` (1), `mixed` (1)
- **secondary metas proposed**: `security_order` (2), `global_justice` (2), `sovereign_resistance` (1)
- **top publishers**: Reuters (15), Associated Press (15), Deutsche Welle (15), France 24 (EN) (14), BBC World (13), The Guardian (12), Euronews (12), France 24 (11)
- **regions**: AMERICAS-USA (4), EUROPE-GERMANY (2), ASIA-CAUCASUS (2), EUROPE-RUSSIA (2), AFRICA-DRC (1), NON-STATE-EU (1)
- **friction nodes**: 17 distinct -- afd_and_german_polarisation, armenia_western_pivot, drc_peace_process, eu_cohesion_theater, eu_migration_burden_sharing, georgia_geopolitical_drift

<details><summary>17 narratives</summary>

- `usdom_epstein_accountability` (us_epstein_elite_network, stance +1, 743 titles, coalition `west_us`, also `global_justice`) -- The files are forcing accountability on a protected elite
- `tighten_and_seize` (russia_sanctions_regime, stance +2, 603 titles, coalition `west`, also `global_justice`) -- Sanctions must be tightened, evasion closed, and frozen Russian assets seized for Ukraine
- `eu_cohesion_hold` (eu_cohesion_theater, stance +2, 276 titles, coalition `west_eu`) -- European cohesion and the rule of law must hold against centrifugal forces
- `usdom_courts_checks_hold` (us_judicial_constraint, stance +1, 195 titles, coalition `west_us`) -- The courts are still binding the executive
- `afd_democratic_defense` (afd_and_german_polarisation, stance +2, 177 titles, coalition `west_eu`) -- The AfD is a threat to the democratic order that must be contained
- `airspace_violation_deterrence` (russia_airspace_incursions, stance +2, 120 titles, coalition `west`) -- Russia deliberately probes NATO airspace to intimidate; NATO must enforce, including shoot-down auth
- `somali_state_rebuilding` (somalia_state_security, stance +2, 101 titles, coalition `mixed`, also `security_order`) -- A state rebuilding with regional partners
- `usdom_loyalty_prerogative` (us_executive_loyalty, stance +1, 47 titles, coalition `west_us`) -- A president is entitled to a team that executes his agenda
- `myanmar_beijing_backed_normalisation` (myanmar_civil_conflict, stance +2, 46 titles, coalition `ru`, also `sovereign_resistance`) -- Legitimate transition, backed by Beijing
- `usdom_electoral_integrity_case` (us_electoral_legitimacy, stance +1, 43 titles, coalition `west_us`) -- Tightening the rules is protecting the integrity of the vote
- `hungary_eu_standards` (hungary_rule_of_law, stance +2, 35 titles, coalition `west_eu`) -- Rule of law and EU standards must be upheld in Hungary
- `latam_theater_western_terms_hold` (latam_hemispheric_theater, stance +2, 19 titles, coalition `west`) -- The Western offer still sets the terms
- `drc_sanctions_as_enforcement` (drc_peace_process, stance +1, 14 titles, coalition `west`, also `security_order`) -- Designations as the only real leverage
- `migration_solidarity_rights` (eu_migration_burden_sharing, stance +2, 8 titles, coalition `west_eu`) -- Migration requires European solidarity and respect for rights and law
- `awp_european_choice` (armenia_western_pivot, stance +2, 3 titles, coalition `west_eu`) -- Armenia's turn to Europe is a sovereign, democratic escape from Russian domination
- `nato_solidarity_territorial_defense` (turkey_iran_war_spillover, stance +1, 3 titles, coalition `west`) -- Patriot redeployment and missile interception are legitimate alliance defence
- `ggd_european_aspiration` (georgia_geopolitical_drift, stance +2, 0 titles, coalition `west_eu`) -- Georgians want a European future their government is betraying

</details>

### A13 -- `global_justice`, critical (-) -- 16 narratives, 4,771 titles

- **proposed meta**: `global_justice`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (4), `west_eu` (3), `mixed` (3), `arab_gulf` (2), `global_south` (2), `ru` (1)
- **secondary metas proposed**: `sovereign_resistance` (3), `liberal_international_order` (2)
- **top publishers**: Al Jazeera (12), The Guardian (9), Reuters (8), Daily Sabah (8), Euronews (7), Associated Press (7), BBC World (7), Deutsche Welle (7)
- **regions**: ASIA-INDIA (4), EUROPE-BALKANS (3), AMERICAS-CUBA (3), MIDEAST-ISRAEL (3), EUROPE-GREENLAND (1), MIDEAST-SUDAN (1)
- **friction nodes**: 13 distinct -- cuba_regime_survival, kashmir_dispute, south_asia_theater, balkan_foreign_capital, balkan_theater, cuba_external_lifelines

<details><summary>16 narratives</summary>

- `palestine_genocide_framing` (israel_theater, stance -2, 2145 titles, coalition `arab_gulf`) -- Pan-Arab / pro-Palestinian: Israel commits systemic violence against Palestinians
- `gaza_humanitarian_catastrophe` (gaza_war, stance -2, 904 titles, coalition `arab_gulf`) -- Pan-Arab / pro-Palestinian: Israel's Gaza campaign is humanitarian catastrophe and genocide
- `west_bank_apartheid_framing` (west_bank_settlements, stance -2, 335 titles, coalition `mixed`) -- Palestinian / international human rights: occupation, settler impunity, apartheid system
- `sudan_humanitarian_catastrophe` (sudan_civil_war, stance -1, 294 titles, coalition `west`) -- Both sides commit atrocities; RSF violence in Darfur amounts to genocide
- `greenland_western_hypocrisy` (greenland_control, stance -2, 289 titles, coalition `ru`) -- US imperialism over Greenland exposes Western hypocrisy and disunity
- `usdom_ice_due_process` (us_interior_immigration_enforcement, stance -1, 222 titles, coalition `west_us`) -- Enforcement is outrunning due process and harming residents
- `south_asia_international_rights` (south_asia_theater, stance -1, 167 titles, coalition `west_eu`, also `liberal_international_order`) -- Across every front the cost falls on civilians and dissenters
- `balkan_theater_accountability_deficit` (balkan_theater, stance -2, 128 titles, coalition `west_eu`, also `sovereign_resistance`) -- From a collapsed canopy to a privatised coastline, political elites are accused of prioritising powe
- `serbia_protest_accountability` (serbia_government_legitimacy, stance -2, 81 titles, coalition `west_eu`, also `sovereign_resistance`) -- Systemic corruption and negligence behind the Novi Sad canopy collapse demand Vucic's resignation
- `balkan_sovereignty_environmental_rejection` (balkan_foreign_capital, stance -2, 67 titles, coalition `west`, also `liberal_international_order`) -- 'Albania is not for sale': a protected coastline is being privatised for elite foreign gain
- `cuba_reform_under_siege` (cuba_regime_survival, stance -1, 37 titles, coalition `west`) -- A real opening is under way but external pressure is throttling it
- `south_asia_pakistani_grievance` (south_asia_theater, stance -2, 30 titles, coalition `global_south`) -- India is the coercive party: occupier, water aggressor and fabricator of charges
- `cuba_lifelines_solidarity` (cuba_external_lifelines, stance -2, 27 titles, coalition `mixed`) -- Solidarity with a besieged island against an illegal siege
- `cuba_sovereign_resistance` (cuba_regime_survival, stance -2, 20 titles, coalition `mixed`) -- A sovereign people is resisting an externally engineered regime change
- `kashmir_disputed_territory` (kashmir_dispute, stance -2, 17 titles, coalition `global_south`) -- Kashmir's status is unresolved and its people are owed self-determination
- `kashmir_rights_and_restrictions` (kashmir_dispute, stance -1, 8 titles, coalition `west`, also `sovereign_resistance`) -- Both administrations face unrest and answer it with force

</details>

### A14 -- `information_order`, critical (-) -- 7 narratives, 539 titles

- **proposed meta**: `information_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `ru` (3), `west_eu` (2), `west` (1), `west_us` (1)
- **secondary metas proposed**: `liberal_international_order` (1), `sovereign_resistance` (1), `global_justice` (1)
- **top publishers**: Euronews (4), France 24 (EN) (4), Le Monde (4), Süddeutsche Zeitung (4), Frankfurter Allgemeine (4), Die Zeit (4), RT (3), TASS (EN) (3)
- **regions**: EUROPE-GERMANY (3), NON-STATE-EU (2), AMERICAS-BRAZIL (1), AMERICAS-USA (1)
- **friction nodes**: 5 distinct -- afd_and_german_polarisation, europe_us_tech_sovereignty, eu_cohesion_theater, latam_eu_market_access, us_press_freedom

<details><summary>7 narratives</summary>

- `usdom_press_suppression` (us_press_freedom, stance -1, 250 titles, coalition `west_us`) -- State leverage is being used against critical coverage
- `tech_digital_sovereignty` (europe_us_tech_sovereignty, stance -1, 120 titles, coalition `west`) -- Europe must rein in US Big Tech and reclaim its digital sovereignty
- `eu_fracture_rift_exploitation` (eu_cohesion_theater, stance -2, 65 titles, coalition `ru`, also `sovereign_resistance`) -- Brussels overreach vindicates a Europe of sovereign nations
- `afd_persecution_kremlin` (afd_and_german_polarisation, stance -2, 47 titles, coalition `ru`) -- Germany persecutes its opposition and silences dissent
- `mercosur_farm_protection` (latam_eu_market_access, stance -2, 33 titles, coalition `west_eu`) -- The deal undercuts European farmers
- `afd_exclusion_undemocratic` (afd_and_german_polarisation, stance -1, 24 titles, coalition `west_eu`, also `liberal_international_order`) -- Excluding a party millions vote for is itself undemocratic
- `tech_digital_colonialism` (europe_us_tech_sovereignty, stance -2, 0 titles, coalition `ru`, also `global_justice`) -- US tech dominance is a digital colonialism Europe is only now waking up to

</details>

### A15 -- `planetary_governance`, critical (-) -- 6 narratives, 351 titles

- **proposed meta**: `planetary_governance`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (2), `west_eu` (1), `west_us` (1), `ru` (1), `mixed` (1)
- **secondary metas proposed**: _none -- all members have one clear meta_
- **top publishers**: Le Monde (5), The Guardian (4), Euronews (4), France 24 (EN) (4), El País (4), Le Figaro (4), Frankfurter Allgemeine (4), Die Zeit (4)
- **regions**: AMERICAS-USA (2), AMERICAS-VENEZUELA (2), EUROPE-RUSSIA (1), AMERICAS-BRAZIL (1)
- **friction nodes**: 6 distinct -- arctic_resources_competition, latam_eu_market_access, us_political_violence, us_russia_theater, venezuela_political_transition, venezuela_theater

<details><summary>6 narratives</summary>

- `ven_transition_imperial_puppet` (venezuela_political_transition, stance -2, 231 titles, coalition `mixed`) -- The transition is a US-installed puppet regime
- `ven_theater_western_critical` (venezuela_theater, stance -1, 86 titles, coalition `west`) -- The means were lawless and the transition is hollow
- `usdom_violence_climate` (us_political_violence, stance -1, 16 titles, coalition `west_us`) -- Violence is becoming a recurring feature of political life
- `us_russia_theater_kremlin_grievance` (us_russia_theater, stance -2, 10 titles, coalition `ru`) -- Washington cannot be trusted to keep its side of any bargain
- `arctic_drilling_environmental_alarm` (arctic_resources_competition, stance -1, 6 titles, coalition `west`) -- Arctic warming and resource extraction are an environmental and climate emergency
- `mercosur_environmental_critique` (latam_eu_market_access, stance -1, 2 titles, coalition `west_eu`) -- The deal rewards forest clearance

</details>

### A16 -- `global_justice`, supportive (+) -- 4 narratives, 105 titles

- **proposed meta**: `global_justice`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (1), `ru` (1), `israel` (1), `west_eu` (1)
- **secondary metas proposed**: `sovereign_resistance` (1), `plural_world_order` (1)
- **top publishers**: Reuters (2), Bloomberg (2), Financial Times (2), The Telegraph (2), The Guardian (2), Deutsche Welle (2), Japan Times (1), Nikkei Asia (1)
- **regions**: ASIA-CHINA (1), AMERICAS-BRAZIL (1), AFRICA-HORN (1), AMERICAS-VENEZUELA (1)
- **friction nodes**: 4 distinct -- japan_china_memory_wars, latam_resource_access, somaliland_recognition_contest, venezuela_political_transition

<details><summary>4 narratives</summary>

- `somaliland_statehood_earned` (somaliland_recognition_contest, stance +2, 55 titles, coalition `israel`) -- Recognition of an earned statehood
- `ven_transition_stabilization` (venezuela_political_transition, stance +1, 36 titles, coalition `west_eu`) -- The interim government is stabilising Venezuela
- `resource_south_south_partnership` (latam_resource_access, stance +2, 9 titles, coalition `ru`, also `plural_world_order`) -- Cooperation brings development
- `memory_political_leverage` (japan_china_memory_wars, stance +2, 5 titles, coalition `west`, also `sovereign_resistance`) -- Historical grievances are raised as political leverage in a deteriorating relationship

</details>

### A17 -- `information_order`, supportive (+) -- 3 narratives, 67 titles

- **proposed meta**: `information_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (2), `west_us` (1)
- **secondary metas proposed**: `sovereign_resistance` (1), `economic_order` (1)
- **top publishers**: Fox News (3), Jerusalem Post (2), Reuters (2), Associated Press (2), BBC World (2), CNN (2), New York Times (2), Washington Post (2)
- **regions**: AMERICAS-CUBA (1), ASIA-TAIWAN (1), AMERICAS-USA (1)
- **friction nodes**: 3 distinct -- cuba_regime_survival, taiwan_political_warfare, us_press_freedom

<details><summary>3 narratives</summary>

- `united_front_subversion` (taiwan_political_warfare, stance +1, 37 titles, coalition `west`) -- Beijing's united front work, infiltration and disinformation are subverting Taiwan's democracy
- `usdom_press_accountability` (us_press_freedom, stance +1, 16 titles, coalition `west_us`, also `economic_order`) -- Broadcasters are being held to obligations that come with a licence
- `cuba_repression_documented` (cuba_regime_survival, stance +1, 14 titles, coalition `west`, also `sovereign_resistance`) -- One-party rule holds by arresting those who protest

</details>

### A18 -- `plural_world_order`, neutral (0) -- 2 narratives, 6 titles

- **proposed meta**: `plural_world_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west_eu` (1), `china` (1)
- **secondary metas proposed**: _none -- all members have one clear meta_
- **top publishers**: BBC (1), BBC World (1), The Guardian (1), Financial Times (1), The Independent (1), The Times (1), Le Monde (1), Le Figaro (1)
- **regions**: MIDEAST-IRAN (1), ASIA-SOUTHEAST (1)
- **friction nodes**: 2 distinct -- iran_theater, thailand_cambodia_border

<details><summary>2 narratives</summary>

- `thaicam_great_power_mediation` (thailand_cambodia_border, stance +0, 6 titles, coalition `china`) -- Outside powers and ASEAN broker the ceasefire and urge both sides to de-escalate
- `eu_diplomatic_preservation_norm` (iran_theater, stance +0, 0 titles, coalition `west_eu`) -- EU/E3 diplomatic engagement on Iran

</details>

### A19 -- `economic_order`, neutral (0) -- 2 narratives, 0 titles

- **proposed meta**: `economic_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west_eu` (2)
- **secondary metas proposed**: `security_order` (1), `liberal_international_order` (1)
- **top publishers**: Le Monde (2), Tagesschau (2), Deutsche Welle (2), Die Zeit (2), Euronews (2), Frankfurter Allgemeine (2), Financial Times (2), BBC World (2)
- **regions**: MIDEAST-ISRAEL (1), MIDEAST-TURKEY (1)
- **friction nodes**: 2 distinct -- israel_theater, turkey_theater

<details><summary>2 narratives</summary>

- `eu_two_state_pathway` (israel_theater, stance +0, 0 titles, coalition `west_eu`, also `security_order`) -- EU/E3 two-state framework: condemn excesses on both sides, preserve the negotiated horizon
- `turkey_eu_engagement_pragmatic` (turkey_theater, stance +0, 0 titles, coalition `west_eu`, also `liberal_international_order`) -- Engage Turkey on shared interests while flagging democratic concerns

</details>

### A20 -- `security_order`, neutral (0) -- 2 narratives, 50 titles

- **proposed meta**: `security_order`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west_us` (1), `west` (1)
- **secondary metas proposed**: `sovereign_resistance` (1)
- **top publishers**: Reuters (2), Associated Press (2), BBC World (2), France 24 (EN) (2), Wall Street Journal (2), Deutsche Welle (2), Jerusalem Post (1), Fox News (1)
- **regions**: MIDEAST-LEVANT (1), MIDEAST-YEMEN (1)
- **friction nodes**: 2 distinct -- syria_counter_terror, yemen_red_sea_theater

<details><summary>2 narratives</summary>

- `coalition_counter_isis_necessary` (syria_counter_terror, stance +0, 50 titles, coalition `west_us`) -- Coalition counter-ISIS operations are necessary until ISIS threat is contained
- `western_pragmatic_navigation` (yemen_red_sea_theater, stance +0, 0 titles, coalition `west`, also `sovereign_resistance`) -- Houthi problem is a freedom-of-navigation problem; Gaza ceasefire removes the casus belli

</details>

### A21 -- `planetary_governance`, supportive (+) -- 2 narratives, 408 titles

- **proposed meta**: `planetary_governance`  (accept / replace: __________)
- **coalitions** (derived from publishers): `mixed` (1), `west` (1)
- **secondary metas proposed**: `global_justice` (1)
- **top publishers**: Reuters (2), BBC World (2), Financial Times (2), Le Monde (2), Deutsche Welle (2), Anadolu Agency (1), Daily Sabah (1), TRT World (1)
- **regions**: MIDEAST-LEVANT (1), AMERICAS-VENEZUELA (1)
- **friction nodes**: 2 distinct -- syria_theater, venezuela_theater

<details><summary>2 narratives</summary>

- `syria_legitimate_transition` (syria_theater, stance +2, 214 titles, coalition `mixed`, also `global_justice`) -- New Syrian government is a legitimate post-Assad transition
- `ven_theater_western_consensus` (venezuela_theater, stance +2, 194 titles, coalition `west`) -- Removing Maduro opened a stabilising, pragmatic path for Venezuela

</details>

### A22 -- `global_justice`, neutral (0) -- 1 narratives, 7 titles

- **proposed meta**: `global_justice`  (accept / replace: __________)
- **coalitions** (derived from publishers): `west` (1)
- **secondary metas proposed**: _none -- all members have one clear meta_
- **top publishers**: Reuters (1), BBC World (1), Deutsche Welle (1), France 24 (EN) (1), Euronews (1), Associated Press (1), The Guardian (1), ERR News (1)
- **regions**: EUROPE-GREENLAND (1)
- **friction nodes**: 1 distinct -- greenland_control

<details><summary>1 narratives</summary>

- `greenland_self_determination` (greenland_control, stance +0, 7 titles, coalition `west`) -- Greenland's future is for Greenlanders to decide -- not Washington or Copenhagen

</details>

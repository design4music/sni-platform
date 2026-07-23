# P0(c) -- Thin-narrative triage

Artifact for `NARRATIVE_CONSOLIDATION_SPEC.md` P0(c), feeding **DG-0 #3** (publication-gate threshold). Read-only; nothing was written.

## Correction to spec 5.4

Spec 5.4 reports **71 of 309 (23%) with zero attributed titles**. That figure counts `title_narratives` rows only. Theater narratives carry no `fn_anchor` bundle *by design* and never attribute a title directly -- their count is the `THEATER_ROLLUP_SQL` union over member atomics, which is what the FN page actually renders. Counting them off `title_narratives` reports every theater narrative as dead.

Measured roll-up-aware over 411 active narratives (attribution rebuilt in full on 2026-07-21, 180-day window):

| attributed titles | narratives | share |
|---|---:|---:|
| zero | 14 | 3% |
| 1-9 | 86 | 21% |
| 10-24 | 68 | 17% |
| 25-99 | 122 | 30% |
| 100+ | 121 | 29% |

**14 truly have zero, not 71.** But **168 of 411 (41%) fall under the proposed gate of 25** -- so the gate, not the zero count, is the live question at DG-0 #3.

### Where the gate would land

| gate | published | suppressed |
|---:|---:|---:|
| >= 10 | 311 | 100 |
| >= 25 | 243 | 168 |
| >= 50 | 173 | 238 |
| >= 100 | 121 | 290 |

---

## Triage of the 168 under-gate narratives

The **14 zero-title** narratives are classified by replaying the `link_titles` conjunction as a funnel and finding which condition zeroes it: `S0` terrain (centroids + primary_target), `S1` + fn_anchor alias hit, `S2` + publisher bloc, `S3` + framing keyword when `framing_required`.

The other 154 are `GENUINELY_THIN` **by construction** -- a narrative that attributed any titles at all has a gate that demonstrably works at every step, so there is nothing to diagnose. (This is also why the funnel is not run on them: each step is a ~325k-title scan with alias regex.)

| class | narratives | meaning |
|---|---:|---|
| `BAD_PUBLISHER_BLOC` | 4 | The FN has titles, but no outlet in this narrative's publisher bloc covers this terrain. |
| `DEAD_VOCABULARY` | 5 | Publishers match, framing keywords match nothing. |
| `GENUINELY_THIN` | 154 | The gate works and the position is honestly barely voiced. |
| `THEATER_NO_SAMESIGN_MEMBER` | 4 | No member atomic carries a narrative of the same stance sign, so the roll-up can never find titles. |
| `THEATER_BLOC_MISS` | 1 | Member atomics have same-sign titles, but none from this theater card's publisher bloc. |

Note `GENUINELY_THIN` is the only class the publication gate is *for*. The others are calibration defects that a gate would hide rather than fix -- they belong to FN work under `FN_THEATER_BUILD_SPEC.md`, and spec 5.4 already says that runs in parallel and blocks a clean launch.

---

### `BAD_PUBLISHER_BLOC` -- 4 narratives

**Remedy.** The FN has titles, but no outlet in this narrative's publisher bloc covers this terrain. Re-measure the bloc against the corpus before shipping the narrative.

| narrative | friction node | type | stance | titles | funnel |
|---|---|---|---:|---:|---|
| `autonomy_illusion` | `eu_strategic_autonomy` | atomic | +2 | 0 | S0 76606 -> S1 138 -> S2 0 -> S3 0 |
| `tech_digital_colonialism` | `europe_us_tech_sovereignty` | atomic | -2 | 0 | S0 56677 -> S1 146 -> S2 0 -> S3 0 |
| `tech_eu_overreach` | `europe_us_tech_sovereignty` | atomic | +2 | 0 | S0 56677 -> S1 146 -> S2 0 -> S3 0 |
| `usca_trade_rebalancing` | `us_canada_trade_coercion` | atomic | +2 | 0 | S0 1025 -> S1 155 -> S2 0 -> S3 0 |

---

### `DEAD_VOCABULARY` -- 5 narratives

**Remedy.** Publishers match, framing keywords match nothing. framing_required is filtering everything out -- corpus-verify the keywords or drop the requirement.

| narrative | friction node | type | stance | titles | funnel |
|---|---|---|---:|---:|---|
| `ggd_european_aspiration` | `georgia_geopolitical_drift` | atomic | +2 | 0 | S0 1056 -> S1 12 -> S2 2 -> S3 0 |
| `escalation_risk_restraint` | `russia_airspace_incursions` | atomic | -1 | 0 | S0 77267 -> S1 368 -> S2 22 -> S3 0 |
| `securitisation_caution` | `russia_hybrid_warfare` | atomic | -1 | 0 | S0 77267 -> S1 556 -> S2 46 -> S3 0 |
| `thaicam_cambodian_territorial_claim` | `thailand_cambodia_border` | atomic | -2 | 0 | S0 33429 -> S1 31 -> S2 1 -> S3 0 |
| `reform_in_progress` | `ukraine_official_corruption` | atomic | +1 | 0 | S0 15596 -> S1 106 -> S2 24 -> S3 0 |

---

### `GENUINELY_THIN` -- 154 narratives

**Remedy.** The gate works and the position is honestly barely voiced. Keep as an FN card; this is the population the publication gate exists for.

| narrative | friction node | type | stance | titles | funnel |
|---|---|---|---:|---:|---|
| `afd_exclusion_undemocratic` | `afd_and_german_polarisation` | atomic | -1 | 24 | - |
| `alberta_external_amplification` | `alberta_separatism_us_ties` | atomic | -2 | 5 | - |
| `alberta_legitimate_grievance` | `alberta_separatism_us_ties` | atomic | +1 | 2 | - |
| `arctic_drilling_environmental_alarm` | `arctic_resources_competition` | atomic | -1 | 6 | - |
| `arctic_resource_development` | `arctic_resources_competition` | atomic | +1 | 14 | - |
| `arctic_route_opportunity` | `arctic_shipping_routes` | atomic | +1 | 13 | - |
| `arctic_route_strategic_threat` | `arctic_shipping_routes` | atomic | -1 | 4 | - |
| `aas_contested_settlement` | `armenia_azerbaijan_settlement` | atomic | -2 | 4 | - |
| `aas_durable_peace` | `armenia_azerbaijan_settlement` | atomic | +2 | 12 | - |
| `awp_european_choice` | `armenia_western_pivot` | atomic | +2 | 3 | - |
| `aukus_bloc_confrontation` | `aukus_alliance_reliability` | atomic | -2 | 1 | - |
| `aukus_strategic_necessity` | `aukus_alliance_reliability` | atomic | +2 | 9 | - |
| `trade_mutual_benefit` | `australia_china_trade_leverage` | atomic | -2 | 8 | - |
| `australia_china_counter` | `australia_theater` | theater | -2 | 21 | - |
| `balkan_investment_development` | `balkan_foreign_capital` | atomic | +1 | 7 | - |
| `balkan_theater_investment_opportunity` | `balkan_theater` | theater | +1 | 7 | - |
| `baloch_foreign_backed_insurgency` | `balochistan_insurgency` | atomic | +2 | 9 | - |
| `casp_continental_dependence` | `canada_sovereignty_pressure` | atomic | +2 | 1 | - |
| `casp_imperial_overreach` | `canada_sovereignty_pressure` | atomic | -1 | 7 | - |
| `cpc_russia_iran_resistance` | `caucasus_power_competition` | atomic | -2 | 5 | - |
| `cpc_western_engagement` | `caucasus_power_competition` | atomic | +1 | 23 | - |
| `china_threat_fabricated` | `china_threat_assessment` | atomic | -2 | 7 | - |
| `colombia_peace_negotiation_defense` | `colombia_armed_groups_peace` | atomic | +1 | 1 | - |
| `colombia_peace_process_failure` | `colombia_armed_groups_peace` | atomic | -1 | 1 | - |
| `colombia_transition_institutional_concern` | `colombia_political_transition` | atomic | -1 | 11 | - |
| `colombia_transition_mandate` | `colombia_political_transition` | atomic | +2 | 6 | - |
| `colombia_theater_hard_turn` | `colombia_theater` | theater | +2 | 1 | - |
| `colombia_theater_hegemonic_critique` | `colombia_theater` | theater | -2 | 4 | - |
| `colombia_theater_negotiated_path` | `colombia_theater` | theater | +1 | 19 | - |
| `colombia_us_imperial_overreach` | `colombia_us_alignment` | atomic | -2 | 13 | - |
| `colombia_us_rapprochement` | `colombia_us_alignment` | atomic | +1 | 14 | - |
| `cuba_sanctions_overreach` | `cuba_embargo_sanctions` | atomic | -1 | 9 | - |
| `cuba_collapse_humanitarian_alarm` | `cuba_energy_collapse` | atomic | -1 | 21 | - |
| `cuba_force_unlawful` | `cuba_military_coercion` | atomic | -1 | 9 | - |
| `cuba_repression_documented` | `cuba_regime_survival` | atomic | +1 | 14 | - |
| `cuba_sovereign_resistance` | `cuba_regime_survival` | atomic | -2 | 20 | - |
| `cuba_theater_pressure_consensus` | `cuba_theater` | theater | +2 | 20 | - |
| `drc_minerals_as_development` | `drc_minerals_competition` | atomic | +2 | 9 | - |
| `drc_minerals_as_resource_capture` | `drc_minerals_competition` | atomic | -2 | 2 | - |
| `drc_minerals_human_cost` | `drc_minerals_competition` | atomic | -1 | 11 | - |
| `drc_accords_are_working` | `drc_peace_process` | atomic | +2 | 5 | - |
| `drc_accords_stalling` | `drc_peace_process` | atomic | -1 | 5 | - |
| `drc_sanctions_as_enforcement` | `drc_peace_process` | atomic | +1 | 14 | - |
| `drc_sanctions_rejected` | `drc_peace_process` | atomic | -2 | 2 | - |
| `ven_essequibo_guyana_sovereignty` | `essequibo_dispute` | atomic | -1 | 3 | - |
| `ven_essequibo_venezuelan_claim` | `essequibo_dispute` | atomic | +1 | 7 | - |
| `budget_more_europe` | `eu_budget_sovereignty` | atomic | +2 | 3 | - |
| `budget_national_sovereignty` | `eu_budget_sovereignty` | atomic | -1 | 8 | - |
| `migration_eu_failure_kremlin` | `eu_migration_burden_sharing` | atomic | -2 | 12 | - |
| `migration_solidarity_rights` | `eu_migration_burden_sharing` | atomic | +2 | 8 | - |
| `realignment_new_majority` | `eu_right_realignment` | atomic | -1 | 1 | - |
| `defence_europe_must_pay` | `europe_us_defence_dependence` | atomic | +2 | 4 | - |
| `defence_nato_racket` | `europe_us_defence_dependence` | atomic | -2 | 13 | - |
| `europe_us_america_first` | `europe_us_theater` | theater | +2 | 10 | - |
| `france_decline_kremlin` | `french_nationalist_challenge` | atomic | -2 | 4 | - |
| `france_popular_will` | `french_nationalist_challenge` | atomic | -1 | 22 | - |
| `ggd_sovereignty_stability` | `georgia_geopolitical_drift` | atomic | -2 | 4 | - |
| `great_lakes_scepticism_of_outside_fixes` | `great_lakes_theater` | theater | -1 | 4 | - |
| `greenland_self_determination` | `greenland_control` | atomic | +0 | 7 | - |
| `greenland_us_strategic_claim` | `greenland_control` | atomic | +2 | 5 | - |
| `houthi_iranian_proxy_aggression` | `houthi_strikes_on_israel` | atomic | -2 | 16 | - |
| `houthi_resistance_strikes_legitimate` | `houthi_strikes_on_israel` | atomic | +2 | 9 | - |
| `hungary_brussels_coercion` | `hungary_rule_of_law` | atomic | -2 | 2 | - |
| `hungary_sovereignty_interference` | `hungary_rule_of_law` | atomic | -1 | 4 | - |
| `militancy_indian_pretext` | `india_pakistan_militancy` | atomic | -2 | 5 | - |
| `indus_treaty_obsolete` | `indus_water_sharing` | atomic | +2 | 18 | - |
| `indus_water_weaponisation` | `indus_water_sharing` | atomic | -2 | 15 | - |
| `inter_korean_engagement` | `inter_korean_relations` | atomic | +2 | 20 | - |
| `pyongyang_closed_the_door` | `inter_korean_relations` | atomic | -2 | 4 | - |
| `memory_political_leverage` | `japan_china_memory_wars` | atomic | +2 | 5 | - |
| `kashmir_disputed_territory` | `kashmir_dispute` | atomic | -2 | 17 | - |
| `kashmir_integral_to_india` | `kashmir_dispute` | atomic | +2 | 12 | - |
| `kashmir_rights_and_restrictions` | `kashmir_dispute` | atomic | -1 | 8 | - |
| `alliance_containment_instrument` | `korea_peninsula_deterrence` | atomic | -2 | 2 | - |
| `alliance_deterrence_necessary` | `korea_peninsula_deterrence` | atomic | +2 | 23 | - |
| `korea_us_containment_critique` | `korea_theater` | theater | -2 | 2 | - |
| `mercosur_environmental_critique` | `latam_eu_market_access` | atomic | -1 | 2 | - |
| `mercosur_european_obstruction` | `latam_eu_market_access` | atomic | -1 | 6 | - |
| `mercosur_market_opportunity` | `latam_eu_market_access` | atomic | +2 | 13 | - |
| `latam_theater_coercion_critique` | `latam_hemispheric_theater` | theater | -2 | 14 | - |
| `latam_theater_eastern_partnership` | `latam_hemispheric_theater` | theater | +1 | 9 | - |
| `latam_theater_regional_agency` | `latam_hemispheric_theater` | theater | +2 | 21 | - |
| `latam_theater_strategic_warning` | `latam_hemispheric_theater` | theater | -2 | 1 | - |
| `latam_theater_western_terms_hold` | `latam_hemispheric_theater` | theater | +2 | 19 | - |
| `port_control_restored` | `latam_port_infrastructure_control` | atomic | +2 | 19 | - |
| `port_expropriation_coercion` | `latam_port_infrastructure_control` | atomic | -2 | 14 | - |
| `resource_extractivism_critique` | `latam_resource_access` | atomic | -1 | 1 | - |
| `resource_south_south_partnership` | `latam_resource_access` | atomic | +2 | 9 | - |
| `resource_sovereign_development` | `latam_resource_access` | atomic | +1 | 8 | - |
| `resource_strategic_penetration` | `latam_resource_access` | atomic | -2 | 1 | - |
| `m23_backing_charge_rejected` | `m23_conflict` | atomic | +1 | 1 | - |
| `m23_civilian_toll` | `m23_conflict` | atomic | -1 | 19 | - |
| `m23_externally_backed_offensive` | `m23_conflict` | atomic | -2 | 11 | - |
| `cartel_narco_state_critique` | `mexico_cartel_war` | atomic | -1 | 10 | - |
| `mexth_anti_hegemony_rift` | `mexico_theater` | theater | -2 | 4 | - |
| `mexth_us_pressure_justified` | `mexico_theater` | theater | +2 | 9 | - |
| `beijing_shields_pyongyang` | `north_korea_china_patronage` | atomic | -2 | 11 | - |
| `nk_sovereign_deterrent` | `north_korea_missile_program` | atomic | +2 | 7 | - |
| `pacific_china_cooperation` | `pacific_island_contest` | atomic | -2 | 5 | - |
| `russia_europe_critical_restraint` | `russia_europe_theater` | theater | -1 | 1 | - |
| `militarisation_overreach` | `russia_nato_deterrence` | atomic | -1 | 1 | - |
| `sahel_break_with_paris_justified` | `sahel_france_rupture` | atomic | +2 | 5 | - |
| `sahel_rupture_deepens_isolation` | `sahel_france_rupture` | atomic | -2 | 19 | - |
| `sahel_counterinsurgency_abuses` | `sahel_jihadist_insurgency` | atomic | -1 | 11 | - |
| `sahel_sovereigntist_self_reliance` | `sahel_junta_consolidation` | atomic | +2 | 8 | - |
| `sahel_patron_model_failing` | `sahel_security_patron_contest` | atomic | -2 | 13 | - |
| `sahel_russian_partnership_delivers` | `sahel_security_patron_contest` | atomic | +2 | 6 | - |
| `sahel_separatism_as_jihadist_alliance` | `sahel_tuareg_separatism` | atomic | +2 | 5 | - |
| `houthi_authority_legitimate_resistance` | `saudi_houthi_war` | atomic | +2 | 19 | - |
| `senkaku_chinese_rights_protection` | `senkaku_diaoyu_islands` | atomic | -2 | 16 | - |
| `somali_foreign_militarisation_critique` | `somalia_state_security` | atomic | -2 | 10 | - |
| `somaliland_transactional_scramble` | `somaliland_recognition_contest` | atomic | -1 | 24 | - |
| `israeli_strikes_on_syria_legitimate` | `syria_israeli_strikes` | atomic | -1 | 3 | - |
| `syrian_sovereignty_under_israeli_aggression` | `syria_israeli_strikes` | atomic | +2 | 17 | - |
| `taiwan_us_pawn` | `taiwan_us_security_commitment` | atomic | -2 | 21 | - |
| `us_commitment_firm` | `taiwan_us_security_commitment` | atomic | +1 | 3 | - |
| `thaicam_great_power_mediation` | `thailand_cambodia_border` | atomic | +0 | 6 | - |
| `thaicam_thai_sovereignty_defence` | `thailand_cambodia_border` | atomic | +2 | 24 | - |
| `trade_us_tariffs_justified` | `transatlantic_trade` | atomic | +2 | 6 | - |
| `turkey_authoritarian_drift_critique` | `turkey_democratic_backsliding` | atomic | -2 | 11 | - |
| `nato_solidarity_territorial_defense` | `turkey_iran_war_spillover` | atomic | +1 | 3 | - |
| `turkey_wrong_side_on_iran` | `turkey_iran_war_spillover` | atomic | -1 | 5 | - |
| `kurdish_political_rights_critique` | `turkey_kurdish_question` | atomic | -1 | 5 | - |
| `western_systemic_alarm` | `ukraine_official_corruption` | atomic | -1 | 17 | - |
| `uscat_external_rift` | `us_canada_theater` | theater | -1 | 21 | - |
| `uscat_provincial_grievance` | `us_canada_theater` | theater | +1 | 2 | - |
| `uscat_us_leverage_case` | `us_canada_theater` | theater | +2 | 1 | - |
| `usca_bloc_fracture` | `us_canada_trade_coercion` | atomic | -1 | 12 | - |
| `us_china_minerals_lawful_leverage` | `us_china_critical_minerals` | atomic | -2 | 17 | - |
| `us_china_summit_engagement_works` | `us_china_summit_diplomacy` | atomic | +1 | 22 | - |
| `us_china_summit_multipolar_framing` | `us_china_summit_diplomacy` | atomic | -2 | 10 | - |
| `us_china_tariff_leverage` | `us_china_trade_tariffs` | atomic | +1 | 4 | - |
| `us_china_tariff_self_harm` | `us_china_trade_tariffs` | atomic | -1 | 19 | - |
| `usdom_electoral_democracy_facade` | `us_electoral_legitimacy` | atomic | -2 | 9 | - |
| `usdom_loyalty_court_politics` | `us_executive_loyalty` | atomic | -2 | 20 | - |
| `usdom_fed_dollar_decline` | `us_fed_independence` | atomic | -2 | 17 | - |
| `anti_hegemony_rift` | `us_mexico_military_pressure` | atomic | -2 | 4 | - |
| `intervention_necessity` | `us_mexico_military_pressure` | atomic | +2 | 1 | - |
| `western_intervention_scrutiny` | `us_mexico_military_pressure` | atomic | -1 | 23 | - |
| `leverage_justified` | `us_mexico_trade_border` | atomic | +2 | 4 | - |
| `usdom_violence_climate` | `us_political_violence` | atomic | -1 | 16 | - |
| `usdom_violence_instability` | `us_political_violence` | atomic | -2 | 18 | - |
| `usdom_press_accountability` | `us_press_freedom` | atomic | +1 | 16 | - |
| `usdom_press_hypocrisy` | `us_press_freedom` | atomic | -2 | 10 | - |
| `us_russia_engagement_necessary` | `us_russia_bilateral_channel` | atomic | +1 | 1 | - |
| `us_russia_normalisation_premature` | `us_russia_bilateral_channel` | atomic | -1 | 5 | - |
| `us_russia_washington_bad_faith` | `us_russia_bilateral_channel` | atomic | -2 | 10 | - |
| `us_russia_relief_pragmatic` | `us_russia_sanctions_leverage` | atomic | +1 | 19 | - |
| `us_russia_theater_kremlin_grievance` | `us_russia_theater` | theater | -2 | 10 | - |
| `ven_coercion_justified` | `us_venezuela_relations` | atomic | +1 | 7 | - |
| `ven_coercion_western_critical` | `us_venezuela_relations` | atomic | -1 | 10 | - |
| `ven_oil_deals_opacity` | `venezuela_sanctions_oil` | atomic | -1 | 15 | - |
| `zc_connectivity_prosperity` | `zangezur_corridor` | atomic | +1 | 6 | - |
| `zc_sovereignty_threat` | `zangezur_corridor` | atomic | -1 | 10 | - |

---

### `THEATER_NO_SAMESIGN_MEMBER` -- 4 narratives

**Remedy.** No member atomic carries a narrative of the same stance sign, so the roll-up can never find titles. Either the theater card's stance is wrong or the member atomics are missing that side.

| narrative | friction node | type | stance | titles | funnel |
|---|---|---|---:|---:|---|
| `eu_diplomatic_preservation_norm` | `iran_theater` | theater | +0 | 0 | same-sign member titles: 0 |
| `eu_two_state_pathway` | `israel_theater` | theater | +0 | 0 | same-sign member titles: 0 |
| `turkey_eu_engagement_pragmatic` | `turkey_theater` | theater | +0 | 0 | same-sign member titles: 0 |
| `western_pragmatic_navigation` | `yemen_red_sea_theater` | theater | +0 | 0 | same-sign member titles: 0 |

---

### `THEATER_BLOC_MISS` -- 1 narratives

**Remedy.** Member atomics have same-sign titles, but none from this theater card's publisher bloc. Same-sign theater cards must be publisher-DISJOINT, so widening the bloc risks double-counting -- check both.

| narrative | friction node | type | stance | titles | funnel |
|---|---|---|---:|---:|---|
| `multipolar_systemic_alternative` | `iran_theater` | theater | +1 | 0 | same-sign member titles: 836 |

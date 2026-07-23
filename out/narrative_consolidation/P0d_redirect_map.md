# P0(d) -- v1/v2 id collision check + draft redirect map

Artifact for `NARRATIVE_CONSOLIDATION_SPEC.md` P0(d), feeding **DG-2 #11**. Read-only; nothing was written.

## 1. Collision check

Spec B3 keeps `/narratives/[id]` as the canonical route and lets v2 ids occupy it, on the stated assumption that the two id sets are disjoint.

| | |
|---|---:|
| `strategic_narratives` ids (v1) | 260 |
| `narratives_v2` ids (v2) | 425 |
| **ids present in both** | **0** |

**Disjoint, as spec B3 assumed.** v2 ids can take over the route with no id remapping, and every v1 id is free to become a 301 source.

---

## 2. Draft redirect map

Successor proposal is TF-IDF cosine between each v1 narrative's text (`name` + `claim` + `normative_conclusion` + `keywords`) and every active v2 narrative's text. Below 0.20 similarity no successor is claimed and the row falls back to its meta page, per spec B3.

Candidates under the publication gate (0 attributed titles, spec C4) are **skipped**, not proposed: those narratives get no standalone page, so a 301 to one would land on a 404. The next publishable match above the similarity floor is used instead, else the meta page.

**This is mechanical and unverified.** Similarity is a lexical overlap score, not a judgment that two narratives make the same argument. Every row in the hand-map table below needs a human accept/retarget -- that is the DG-2 #11 decision.

Ranking is by v1 `event_strategic_narratives` count, so the top 30 rows carry 62% of all 82,040 v1 event links. That is the argument for hand-mapping only these and blanket-301'ing the tail.

### 2a. Hand-map candidates -- top 30 by v1 event count

| v1 id | events | sim | proposed target | v2 successor | v2 titles |
|---|---:|---:|---|---|---:|
| `us_iran_containment` | 5408 | 0.00 | `/narratives/meta/security_order` | _(no successor -- meta page)_ | 0 |
| `us_iran_regime_change` | 5232 | 0.23 | `/narratives/west_iran_regime_change_doctrine` | Western coalition: the Iranian regime is illegitimate and re | 2746 |
| `us_sanctions_enforce_norms` | 4372 | 0.00 | `/narratives/meta/liberal_international_order` | _(no successor -- meta page)_ | 0 |
| `us_maga_national_revival` | 2956 | 0.00 | `/narratives/meta/sovereign_resistance` | _(no successor -- meta page)_ | 0 |
| `ru_special_military_operation` | 2594 | 0.33 | `/narratives/russia_special_military_operation` | Russia's special military operation defends Russian-speaking | 1461 |
| `us_immigration_crackdown` | 2364 | 0.00 | `/narratives/meta/sovereign_resistance` | _(no successor -- meta page)_ | 0 |
| `ua_russia_unprovoked_aggression` | 2187 | 0.27 | `/narratives/ukraine_resistance_solidarity` | Ukraine's war of national defense deserves full Western and  | 1585 |
| `us_monroe_doctrine_revival` | 1801 | 0.00 | `/narratives/meta/great_power_competition` | _(no successor -- meta page)_ | 0 |
| `ir_us_israel_aggression` | 1791 | 0.23 | `/narratives/multipolar_systemic_alternative` | Multipolar sovereignty backing for Iran | 0 |
| `il_iran_existential_threat` | 1707 | 0.31 | `/narratives/israel_preemptive_strike_doctrine` | Israel: preemptive and reactive strikes against an existenti | 115 |
| `us_counter_disinformation` | 1502 | 0.00 | `/narratives/meta/information_order` | _(no successor -- meta page)_ | 0 |
| `us_deep_state_purge` | 1473 | 0.00 | `/narratives/meta/information_order` | _(no successor -- meta page)_ | 0 |
| `us_russia_aggression` | 1311 | 0.21 | `/narratives/ukraine_resistance_solidarity` | Ukraine's war of national defense deserves full Western and  | 1585 |
| `us_indo_pacific_alliances` | 1279 | 0.00 | `/narratives/meta/great_power_competition` | _(no successor -- meta page)_ | 0 |
| `nato_collective_defense` | 1267 | 0.00 | `/narratives/meta/liberal_international_order` | _(no successor -- meta page)_ | 0 |
| `ir_sovereignty_defense` | 1167 | 0.00 | `/narratives/meta/sovereign_resistance` | _(no successor -- meta page)_ | 0 |
| `us_energy_dominance` | 1125 | 0.00 | `/narratives/meta/economic_order` | _(no successor -- meta page)_ | 0 |
| `ru_energy_as_leverage` | 1085 | 0.00 | `/narratives/meta/economic_order` | _(no successor -- meta page)_ | 0 |
| `ru_sanctions_are_economic_warfare` | 1013 | 0.00 | `/narratives/meta/sovereign_resistance` | _(no successor -- meta page)_ | 0 |
| `eu_russia_existential_threat` | 997 | 0.00 | `/narratives/meta/great_power_competition` | _(no successor -- meta page)_ | 0 |
| `cn_taiwan_reunification` | 972 | 0.36 | `/narratives/taiwan_strait_beijing_counter` | Taiwan is Chinese territory and foreign interference, not Ch | 208 |
| `ru_military_strength_security` | 957 | 0.00 | `/narratives/meta/security_order` | _(no successor -- meta page)_ | 0 |
| `ir_nuclear_sovereignty` | 940 | 0.33 | `/narratives/iran_nuclear_sovereign_right` | Iran: nuclear program as sovereign right and deterrence hedg | 147 |
| `eu_ukraine_accession` | 801 | 0.00 | `/narratives/meta/great_power_competition` | _(no successor -- meta page)_ | 0 |
| `cn_narrative_counter_offensive` | 788 | 0.00 | `/narratives/meta/information_order` | _(no successor -- meta page)_ | 0 |
| `ir_regional_power` | 743 | 0.00 | `/narratives/meta/plural_world_order` | _(no successor -- meta page)_ | 0 |
| `in_strategic_autonomy` | 734 | 0.00 | `/narratives/meta/plural_world_order` | _(no successor -- meta page)_ | 0 |
| `tw_de_facto_sovereignty` | 727 | 0.00 | `/narratives/meta/sovereign_resistance` | _(no successor -- meta page)_ | 0 |
| `in_hindu_civilizational` | 692 | 0.00 | `/narratives/meta/sovereign_resistance` | _(no successor -- meta page)_ | 0 |
| `cn_multipolar_world` | 671 | 0.00 | `/narratives/meta/plural_world_order` | _(no successor -- meta page)_ | 0 |

### 2b. Tail -- blanket 301 (230 ids)

DG-2 #11 proposes sending all of these to `/narratives`. The per-row proposal is listed anyway: where similarity is high the redirect costs nothing extra to make specific, and where it is low the meta page is a better landing than the index.

| v1 id | events | sim | proposed target |
|---|---:|---:|---|
| `us_ai_governance` | 646 | 0.00 | `/narratives/meta/planetary_governance` |
| `south_europe_migration_frontline` | 640 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `us_tariff_economic_nationalism` | 626 | 0.24 | `/narratives/trade_us_tariffs_justified` |
| `br_global_south_leader` | 592 | 0.00 | `/narratives/meta/global_justice` |
| `ps_occupation_apartheid` | 590 | 0.44 | `/narratives/palestine_genocide_framing` |
| `ir_sanctions_economic_warfare` | 590 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `in_global_south_voice` | 583 | 0.00 | `/narratives/meta/global_justice` |
| `ua_european_path` | 567 | 0.22 | `/narratives/awp_european_choice` |
| `jp_china_threat` | 531 | 0.24 | `/narratives/jc_taiwan_japan_security_stake` |
| `il_counterterrorism_operations` | 520 | 0.36 | `/narratives/west_iran_proxy_network_threat` |
| `us_nato_collective_defense` | 516 | 0.00 | `/narratives/meta/liberal_international_order` |
| `cn_technology_self_reliance` | 493 | 0.00 | `/narratives/meta/economic_order` |
| `cn_sanctions_illegitimate` | 480 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `tr_domestic_sovereignty` | 470 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `ru_nato_encirclement` | 466 | 0.00 | `/narratives/meta/great_power_competition` |
| `us_rules_based_order` | 461 | 0.00 | `/narratives/meta/liberal_international_order` |
| `tw_democracy_model` | 444 | 0.00 | `/narratives/meta/liberal_international_order` |
| `us_human_rights_enforcement` | 428 | 0.00 | `/narratives/meta/liberal_international_order` |
| `us_anti_globalism` | 428 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `by_russia_equal_partnership` | 427 | 0.00 | `/narratives/meta/plural_world_order` |
| `ru_protect_russian_speakers` | 426 | 0.26 | `/narratives/russia_special_military_operation` |
| `cn_global_security_initiative` | 410 | 0.00 | `/narratives/meta/great_power_competition` |
| `ru_multipolar_world` | 407 | 0.22 | `/narratives/multipolar_systemic_alternative` |
| `ir_islamic_governance` | 399 | 0.24 | `/narratives/iran_sovereign_existence` |
| `andean_coca_sovereignty` | 390 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `eu_counter_disinformation` | 374 | 0.00 | `/narratives/meta/information_order` |
| `us_china_systemic_rival` | 348 | 0.00 | `/narratives/meta/great_power_competition` |
| `tr_neo_ottoman_sphere` | 334 | 0.23 | `/narratives/turkey_independent_middle_power` |
| `southerncone_mercosur_autonomy` | 329 | 0.00 | `/narratives/meta/plural_world_order` |
| `cn_peaceful_rise` | 329 | 0.00 | `/narratives/meta/plural_world_order` |
| `alpine_neutrality_tested` | 316 | 0.00 | `/narratives/meta/plural_world_order` |
| `eu_us_reliability_crisis` | 314 | 0.00 | `/narratives/meta/plural_world_order` |
| `il_right_to_self_defense` | 312 | 0.30 | `/narratives/israel_existential_self_defense` |
| `nordic_climate_model` | 293 | 0.00 | `/narratives/meta/planetary_governance` |
| `kr_north_korea_existential` | 282 | 0.21 | `/narratives/alliance_deterrence_necessary` |
| `kr_tech_manufacturing_power` | 277 | 0.00 | `/narratives/meta/economic_order` |
| `us_territorial_expansion` | 273 | 0.22 | `/narratives/greenland_us_strategic_claim` |
| `ve_bolivarian_revolution` | 270 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `baltic_russia_existential` | 267 | 0.00 | `/narratives/meta/great_power_competition` |
| `cn_digital_sovereignty` | 265 | 0.00 | `/narratives/meta/information_order` |
| `eu_migration_solidarity` | 262 | 0.25 | `/narratives/migration_solidarity_rights` |
| `balkans_ethnic_sovereignty` | 260 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `southerncone_economic_crisis` | 260 | 0.00 | `/narratives/meta/economic_order` |
| `ua_sovereignty_defense` | 252 | 0.37 | `/narratives/ukraine_resistance_solidarity` |
| `cn_pla_modernization` | 250 | 0.00 | `/narratives/meta/security_order` |
| `us_deterrence_forward_presence` | 247 | 0.00 | `/narratives/meta/great_power_competition` |
| `eu_rule_of_law_internal` | 247 | 0.28 | `/narratives/hungary_eu_standards` |
| `in_pakistan_terrorism` | 245 | 0.28 | `/narratives/militancy_pakistan_sponsorship` |
| `ru_western_hegemony_decline` | 241 | 0.00 | `/narratives/meta/plural_world_order` |
| `nato_china_systemic_challenge` | 230 | 0.00 | `/narratives/meta/great_power_competition` |
| `ve_sanctions_collective_punishment` | 219 | 0.22 | `/narratives/cuba_economic_warfare` |
| `cn_us_hegemony_threat` | 216 | 0.00 | `/narratives/meta/great_power_competition` |
| `eu_sanctions_tool` | 210 | 0.00 | `/narratives/meta/liberal_international_order` |
| `af_islamic_emirate` | 209 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `nk_us_hostile_policy` | 206 | 0.00 | `/narratives/meta/great_power_competition` |
| `cu_embargo_longest_siege` | 203 | 0.30 | `/narratives/cuba_economic_warfare` |
| `central_asia_energy_corridor` | 195 | 0.00 | `/narratives/meta/economic_order` |
| `pk_india_existential_threat` | 193 | 0.00 | `/narratives/meta/security_order` |
| `us_climate_global_action` | 190 | 0.00 | `/narratives/meta/planetary_governance` |
| `ru_information_sovereignty` | 189 | 0.00 | `/narratives/meta/information_order` |
| `sahel_expel_france` | 188 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `pk_china_iron_brotherhood` | 187 | 0.00 | `/narratives/meta/plural_world_order` |
| `by_stability_sovereignty` | 183 | 0.27 | `/narratives/ggd_sovereignty_stability` |
| `ve_oil_sovereignty` | 182 | 0.27 | `/narratives/ven_oil_imperial_plunder` |
| `cn_us_containment_resisted` | 179 | 0.00 | `/narratives/meta/great_power_competition` |
| `cn_belt_and_road` | 178 | 0.00 | `/narratives/meta/economic_order` |
| `andean_indigenous_rights` | 177 | 0.00 | `/narratives/meta/global_justice` |
| `nordic_arctic_sovereignty` | 171 | 0.24 | `/narratives/arctic_western_security_consensus` |
| `us_globalist_order` | 167 | 0.00 | `/narratives/meta/liberal_international_order` |
| `eu_migration_control` | 166 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `ca_trade_diversification` | 163 | 0.00 | `/narratives/meta/economic_order` |
| `us_supply_chain_friendshoring` | 159 | 0.00 | `/narratives/meta/economic_order` |
| `cn_global_governance_reform` | 156 | 0.00 | `/narratives/meta/plural_world_order` |
| `visegrad_traditional_values` | 148 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `ua_weapons_decisive` | 147 | 0.00 | `/narratives/meta/security_order` |
| `nato_russia_deterrence` | 145 | 0.30 | `/narratives/eastern_flank_deterrence` |
| `gulf_opec_market_management` | 145 | 0.00 | `/narratives/meta/economic_order` |
| `af_recognition_sanctions` | 141 | 0.00 | `/narratives/meta/global_justice` |
| `mx_cartel_sovereignty` | 140 | 0.00 | `/narratives/meta/security_order` |
| `il_settlement_sovereignty` | 139 | 0.46 | `/narratives/judea_samaria_sovereignty` |
| `jp_economic_security` | 137 | 0.00 | `/narratives/meta/economic_order` |
| `br_multi_alignment` | 136 | 0.00 | `/narratives/meta/plural_world_order` |
| `ru_sovereignty_defense` | 136 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `il_western_alliance` | 136 | 0.00 | `/narratives/meta/liberal_international_order` |
| `eu_trade_tariff_response` | 134 | 0.00 | `/narratives/meta/economic_order` |
| `cn_social_stability` | 122 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `balkans_eu_aspiration` | 121 | 0.00 | `/narratives/meta/liberal_international_order` |
| `de_china_economic_dependence` | 118 | 0.00 | `/narratives/meta/economic_order` |
| `tr_mediator_broker` | 116 | 0.23 | `/narratives/turkey_legitimate_broker` |
| `gulf_energy_transition_terms` | 113 | 0.00 | `/narratives/meta/planetary_governance` |
| `in_digital_economic_power` | 112 | 0.00 | `/narratives/meta/economic_order` |
| `gulf_vision_post_oil` | 111 | 0.00 | `/narratives/meta/economic_order` |
| `hk_freedoms_destroyed` | 108 | 0.00 | `/narratives/meta/liberal_international_order` |
| `hk_stability_restored` | 108 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `cu_revolutionary_sovereignty` | 108 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `cn_chip_self_sufficiency` | 102 | 0.00 | `/narratives/meta/economic_order` |
| `uk_ukraine_champion` | 101 | 0.00 | `/narratives/meta/great_power_competition` |
| `eu_regulatory_superpower` | 100 | 0.00 | `/narratives/meta/information_order` |
| `ng_oil_economy_transition` | 97 | 0.00 | `/narratives/meta/economic_order` |
| `ru_western_disinformation` | 97 | 0.00 | `/narratives/meta/information_order` |
| `us_democracy_vs_authoritarianism` | 95 | 0.00 | `/narratives/meta/liberal_international_order` |
| `eu_energy_independence` | 94 | 0.00 | `/narratives/meta/economic_order` |
| `ru_anti_colonial_alignment` | 92 | 0.00 | `/narratives/meta/global_justice` |
| `ng_insurgency_sovereignty` | 92 | 0.00 | `/narratives/meta/security_order` |
| `kr_us_alliance` | 91 | 0.00 | `/narratives/meta/liberal_international_order` |
| `ca_sovereignty_under_us_pressure` | 90 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `cn_global_south_development` | 86 | 0.00 | `/narratives/meta/global_justice` |
| `cn_sovereignty_non_interference` | 86 | 0.20 | `/narratives/jc_taiwan_interference_charge` |
| `pk_terrorism_victim` | 81 | 0.22 | `/narratives/militancy_indian_pretext` |
| `eu_green_deal_industrial` | 79 | 0.00 | `/narratives/meta/planetary_governance` |
| `visegrad_sovereignty_over_brussels` | 79 | 0.21 | `/narratives/eu_sovereigntist_revolt` |
| `ru_dollar_hegemony_challenge` | 78 | 0.00 | `/narratives/meta/plural_world_order` |
| `za_brics_global_south` | 77 | 0.00 | `/narratives/meta/plural_world_order` |
| `nk_nuclear_deterrent` | 73 | 0.00 | `/narratives/meta/security_order` |
| `uk_channel_migration` | 70 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `nato_enlargement_open_door` | 69 | 0.00 | `/narratives/meta/liberal_international_order` |
| `gulf_iran_containment` | 67 | 0.00 | `/narratives/meta/security_order` |
| `sahel_jihad_existential` | 66 | 0.00 | `/narratives/meta/security_order` |
| `cn_trade_politicization` | 65 | 0.00 | `/narratives/meta/economic_order` |
| `ca_arctic_sovereignty` | 65 | 0.00 | `/narratives/meta/great_power_competition` |
| `central_asia_multi_vector` | 65 | 0.24 | `/narratives/serbia_sovereignty_defense` |
| `ve_multipolar_alliance` | 62 | 0.00 | `/narratives/meta/plural_world_order` |
| `caucasus_connectivity_crossroads` | 60 | 0.00 | `/narratives/meta/economic_order` |
| `tw_semiconductor_leverage` | 58 | 0.00 | `/narratives/meta/economic_order` |
| `baltic_russian_minority_security` | 58 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `cn_climate_differentiated_responsibility` | 57 | 0.00 | `/narratives/meta/planetary_governance` |
| `sahel_russia_partnership` | 57 | 0.00 | `/narratives/meta/plural_world_order` |
| `fr_nuclear_deterrent` | 57 | 0.00 | `/narratives/meta/security_order` |
| `de_fiscal_discipline` | 56 | 0.00 | `/narratives/meta/economic_order` |
| `ps_resistance_legitimate` | 55 | 0.20 | `/narratives/iran_axis_of_resistance` |
| `ps_international_law_weapon` | 54 | 0.00 | `/narratives/meta/global_justice` |
| `west_africa_democratic_resilience` | 50 | 0.00 | `/narratives/meta/liberal_international_order` |
| `de_industrial_crisis` | 50 | 0.00 | `/narratives/meta/economic_order` |
| `eu_multilateral_rules_order` | 50 | 0.00 | `/narratives/meta/liberal_international_order` |
| `za_non_alignment_pragmatic` | 49 | 0.22 | `/narratives/multipolar_anti_israel_alignment` |
| `cn_de_dollarization` | 49 | 0.00 | `/narratives/meta/plural_world_order` |
| `mx_non_intervention_doctrine` | 48 | 0.23 | `/narratives/mexican_sovereignty_defense` |
| `et_unity_sovereignty` | 48 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `eu_climate_diplomacy` | 48 | 0.00 | `/narratives/meta/planetary_governance` |
| `uk_global_britain` | 48 | 0.00 | `/narratives/meta/plural_world_order` |
| `us_tech_decoupling_china` | 48 | 0.00 | `/narratives/meta/great_power_competition` |
| `us_counterterrorism` | 45 | 0.00 | `/narratives/meta/security_order` |
| `eu_industrial_sovereignty` | 43 | 0.00 | `/narratives/meta/economic_order` |
| `ru_western_values_imposition` | 42 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `de_energiewende` | 41 | 0.00 | `/narratives/meta/planetary_governance` |
| `balkans_east_frontline_nato` | 41 | 0.00 | `/narratives/meta/great_power_competition` |
| `horn_red_sea_chokepoint` | 41 | 0.00 | `/narratives/meta/great_power_competition` |
| `cn_xinjiang_hong_kong_internal` | 38 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `ru_traditional_values` | 37 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `andean_lithium_copper_sovereignty` | 36 | 0.00 | `/narratives/meta/economic_order` |
| `visegrad_russia_engagement` | 35 | 0.00 | `/narratives/meta/plural_world_order` |
| `ps_self_determination` | 33 | 0.00 | `/narratives/meta/global_justice` |
| `gulf_multi_alignment` | 33 | 0.00 | `/narratives/meta/plural_world_order` |
| `south_europe_fiscal_solidarity` | 33 | 0.00 | `/narratives/meta/economic_order` |
| `nato_burden_sharing` | 30 | 0.00 | `/narratives/meta/great_power_competition` |
| `au_pacific_step_up` | 29 | 0.38 | `/narratives/pacific_western_partnership` |
| `tr_kurdish_threat` | 29 | 0.25 | `/narratives/kurdish_political_rights_critique` |
| `fr_republican_secularism` | 29 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `nz_independent_values_foreign_policy` | 28 | 0.00 | `/narratives/meta/plural_world_order` |
| `tw_china_military_threat` | 28 | 0.23 | `/narratives/taiwan_strait_western_consensus` |
| `jp_free_open_indo_pacific` | 27 | 0.00 | `/narratives/meta/liberal_international_order` |
| `fr_africa_influence` | 26 | 0.00 | `/narratives/meta/great_power_competition` |
| `central_bukele_security_model` | 26 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `asean_centrality` | 25 | 0.00 | `/narratives/meta/plural_world_order` |
| `ir_resistance_axis` | 25 | 0.36 | `/narratives/iran_axis_of_resistance` |
| `ng_west_africa_anchor` | 25 | 0.00 | `/narratives/meta/plural_world_order` |
| `kurd_rojava_democratic_model` | 24 | 0.39 | `/narratives/kurdish_self_administration` |
| `cn_western_values_rejected` | 24 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `drc_rwandan_aggression` | 23 | 0.00 | `/narratives/meta/security_order` |
| `melanesia_great_power_pawn` | 22 | 0.00 | `/narratives/meta/plural_world_order` |
| `au_aukus_deterrence` | 21 | 0.20 | `/narratives/aukus_strategic_necessity` |
| `asean_economic_integration` | 20 | 0.00 | `/narratives/meta/economic_order` |
| `cu_solidarity_internationalism` | 20 | 0.00 | `/narratives/meta/global_justice` |
| `nordic_nato_turn` | 20 | 0.00 | `/narratives/meta/security_order` |
| `uk_special_relationship` | 19 | 0.00 | `/narratives/meta/liberal_international_order` |
| `br_amazon_sovereignty` | 19 | 0.25 | `/narratives/mercosur_environmental_critique` |
| `mx_nearshoring_opportunity` | 19 | 0.22 | `/narratives/trade_economic_disruption` |
| `de_zeitenwende` | 18 | 0.00 | `/narratives/meta/security_order` |
| `eu_rearmament` | 18 | 0.00 | `/narratives/meta/security_order` |
| `tr_energy_hub` | 18 | 0.00 | `/narratives/meta/economic_order` |
| `za_anti_apartheid_solidarity` | 17 | 0.21 | `/narratives/iran_gulf_resistance_solidarity` |
| `eu_human_rights_universal` | 17 | 0.00 | `/narratives/meta/liberal_international_order` |
| `et_nile_sovereignty` | 17 | 0.25 | `/narratives/ethiopia_regional_revisionism` |
| `central_migration_survival` | 17 | 0.00 | `/narratives/meta/global_justice` |
| `caribbean_climate_survival` | 16 | 0.00 | `/narratives/meta/planetary_governance` |
| `br_regional_stability` | 15 | 0.00 | `/narratives/meta/plural_world_order` |
| `pk_kashmir_self_determination` | 15 | 0.34 | `/narratives/kashmir_disputed_territory` |
| `fr_strategic_autonomy` | 14 | 0.00 | `/narratives/meta/plural_world_order` |
| `kurd_self_determination` | 14 | 0.00 | `/narratives/meta/global_justice` |
| `nk_juche_self_reliance` | 13 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `in_china_border_threat` | 13 | 0.00 | `/narratives/meta/great_power_competition` |
| `tr_muslim_world_leadership` | 12 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `eu_global_gateway` | 12 | 0.00 | `/narratives/meta/global_justice` |
| `east_africa_eac_integration` | 11 | 0.00 | `/narratives/meta/economic_order` |
| `visegrad_migration_refusal` | 10 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `east_africa_great_power_competition` | 9 | 0.00 | `/narratives/meta/great_power_competition` |
| `au_china_coercion_resistance` | 9 | 0.00 | `/narratives/meta/great_power_competition` |
| `gulf_regional_stability` | 8 | 0.00 | `/narratives/meta/security_order` |
| `central_africa_resource_governance` | 8 | 0.00 | `/narratives/meta/economic_order` |
| `ca_middle_power_multilateralism` | 7 | 0.00 | `/narratives/meta/liberal_international_order` |
| `ke_western_partner` | 7 | 0.00 | `/narratives/meta/liberal_international_order` |
| `mn_third_neighbor` | 7 | 0.00 | `/narratives/meta/plural_world_order` |
| `ru_economic_self_reliance` | 7 | 0.00 | `/narratives/meta/economic_order` |
| `mx_migration_root_causes` | 7 | 0.00 | `/narratives/meta/global_justice` |
| `kurd_anti_isis_sacrifice` | 6 | 0.00 | `/narratives/meta/security_order` |
| `west_africa_youth_digital_economy` | 6 | 0.00 | `/narratives/meta/economic_order` |
| `au_rules_based_indo_pacific` | 6 | 0.00 | `/narratives/meta/liberal_international_order` |
| `caribbean_debt_trap` | 6 | 0.00 | `/narratives/meta/global_justice` |
| `il_normalization_abraham` | 6 | 0.00 | `/narratives/meta/economic_order` |
| `melanesia_climate_existential` | 6 | 0.00 | `/narratives/meta/planetary_governance` |
| `pk_nuclear_deterrent` | 4 | 0.00 | `/narratives/meta/security_order` |
| `drc_resource_curse` | 4 | 0.00 | `/narratives/meta/global_justice` |
| `benelux_trade_openness` | 4 | 0.00 | `/narratives/meta/economic_order` |
| `southern_africa_land_reform` | 4 | 0.00 | `/narratives/meta/global_justice` |
| `nz_pacific_climate_champion` | 3 | 0.00 | `/narratives/meta/planetary_governance` |
| `polynesia_ocean_identity` | 2 | 0.00 | `/narratives/meta/global_justice` |
| `png_resource_sovereignty` | 1 | 0.00 | `/narratives/meta/economic_order` |
| `kurd_turkish_oppression` | 1 | 0.25 | `/narratives/kurdish_political_rights_critique` |
| `benelux_eu_deepening` | 0 | 0.00 | `/narratives/meta/liberal_international_order` |
| `png_great_power_balancing` | 0 | 0.00 | `/narratives/meta/plural_world_order` |
| `micronesia_nuclear_legacy` | 0 | 0.00 | `/narratives/meta/global_justice` |
| `micronesia_compact_sovereignty` | 0 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `jp_defense_normalization` | 0 | 0.00 | `/narratives/meta/security_order` |
| `cn_south_china_sea_sovereignty` | 0 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `kurd_krg_pragmatic_autonomy` | 0 | 0.00 | `/narratives/meta/economic_order` |
| `asean_south_china_sea` | 0 | 0.00 | `/narratives/meta/security_order` |
| `caucasus_frozen_conflicts` | 0 | 0.00 | `/narratives/meta/security_order` |
| `ke_tech_finance_hub` | 0 | 0.00 | `/narratives/meta/economic_order` |
| `southern_africa_liberation_legacy` | 0 | 0.00 | `/narratives/meta/sovereign_resistance` |
| `horn_al_shabaab_threat` | 0 | 0.00 | `/narratives/meta/security_order` |

---

## 3. Summary

| | |
|---|---:|
| v1 ids needing a redirect | 260 |
| with a proposed v2 successor | 51 |
| falling back to a meta page | 209 |
| v1 ids with zero event links | 12 |

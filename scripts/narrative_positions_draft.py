"""Position-clustering experiment (idea 1): does 411 cards collapse to ~80 or ~300?

A POSITION is the universal narrative core -- a (frame, stance-sign) that recurs
across friction nodes. A CARD is one appearance of a position on one FN
(narratives_v2 row today). This encodes an LLM-judgment clustering of all 411
active cards into positions, keyed on the claim/frame, NOT on text similarity.

Owners are an ATTRIBUTE of a position, not its key: the same frame ("US imperial
coercion of the hemisphere") is carried by Cuba, Venezuela, Mexico AND echoed by
Russia/China. Many-to-many, per idea 3. The per-card publisher bloc keeps the
who-said-it nuance the merge would otherwise lose.

Read-only. Validates completeness (every id assigned exactly once) and writes a
review report with the collapse ratio. Touches no table. This is a DRAFT for
human review, exactly like the other P0 artifacts -- positions were grouped by
judgment and will be wrong at the margins.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

DUMP = Path(
    r"C:\Users\Maksim\AppData\Local\Temp\claude"
    r"\C--Users-Maksim-Documents-SNI"
    r"\1a19ec7c-1fd1-425a-b2b6-a85888605a36\scratchpad\narratives_dump.json"
)
OUT = (
    Path(__file__).parent.parent
    / "out"
    / "narrative_consolidation"
    / "P0e_positions_draft.md"
)

# position_id -> (human name, stance_sign, [card narrative_ids])
# Grouped into families only for readability; each position is flat.
POSITIONS: dict[str, tuple[str, int, list[str]]] = {
    # ================= WESTERN / ATLANTICIST CONSENSUS (pro-order, +) =========
    "russia_threat_deterrence": (
        "Russia is an aggressive threat; deterrence and rearmament are justified",
        +1,
        [
            "airspace_violation_deterrence",
            "eastern_flank_deterrence",
            "russia_europe_western_resolve",
            "hybrid_campaign_defence",
            "tighten_and_seize",
            "arctic_nato_deterrence",
            "arctic_western_security_consensus",
            "nato_solidarity_territorial_defense",
        ],
    ),
    "ukraine_defense_solidarity": (
        "Ukraine's war is legitimate national defense deserving full support",
        +1,
        [
            "aid_sustains_defense",
            "ukrainian_defense_and_deep_strikes",
            "infrastructure_war_economy_strikes",
            "ukraine_resistance_solidarity",
            "ukrainian_maximalist_peace",
        ],
    ),
    "ukraine_reform_progress": (
        "Ukraine's anti-corruption institutions are working / reform in progress",
        +1,
        ["reform_in_progress"],
    ),
    "china_strategic_competition": (
        "China is a strategic competitor; firmness, derisking and export controls justified",
        +1,
        [
            "us_china_ai_lead_contest",
            "us_china_export_control_necessity",
            "us_china_minerals_dependence_risk",
            "us_china_summit_engagement_works",
            "us_china_tariff_leverage",
            "us_china_western_competition_consensus",
            "trade_derisking_necessity",
            "china_threat_substantiated",
            "cjer_economic_coercion",
        ],
    ),
    "taiwan_japan_security_consensus": (
        "Taiwan/Japan under Chinese coercion; deterrence and administration legitimate",
        +1,
        [
            "jc_taiwan_japan_security_stake",
            "taiwan_coercion_deterrence",
            "taiwan_international_space",
            "taiwan_strait_western_consensus",
            "us_commitment_firm",
            "united_front_subversion",
            "senkaku_japanese_administration",
            "jde_deterrence_response",
            "jc_theater_japanese_western_consensus",
            "memory_political_leverage",
        ],
    ),
    "us_russia_engagement_pragmatic": (
        "Reopened US-Russia channel and energy waivers are pragmatic realism",
        +1,
        [
            "us_russia_new_treaty_needed",
            "us_russia_engagement_necessary",
            "us_russia_relief_pragmatic",
            "us_russia_theater_engagement_case",
        ],
    ),
    "korea_deterrence_dualtrack": (
        "Alliance deterrence plus engagement is the right Korea policy",
        +1,
        [
            "alliance_deterrence_necessary",
            "korea_allied_dual_track",
            "inter_korean_engagement",
        ],
    ),
    "caucasus_western_tilt": (
        "The South Caucasus is tilting West; engagement and the settlement are gains",
        +1,
        [
            "caucasus_western_consensus",
            "cpc_western_engagement",
            "aas_durable_peace",
            "zc_connectivity_prosperity",
            "awp_european_choice",
        ],
    ),
    "australia_alliance_consensus": (
        "Australia's alliances (AUKUS, Pacific) are a necessary security anchor",
        +1,
        [
            "aukus_strategic_necessity",
            "australia_western_consensus",
            "pacific_western_partnership",
        ],
    ),
    "colombia_negotiated_path": (
        "Colombia's negotiated demobilisation and democratic transition are working",
        +1,
        [
            "colombia_peace_negotiation_defense",
            "colombia_theater_negotiated_path",
            "colombia_transition_mandate",
            "colombia_us_rapprochement",
        ],
    ),
    "greatlakes_engagement_working": (
        "External mediation and mineral deals are finally stabilising the Great Lakes",
        +1,
        [
            "drc_accords_are_working",
            "drc_minerals_as_development",
            "drc_sanctions_as_enforcement",
            "great_lakes_engagement_working",
        ],
    ),
    "latam_western_terms_hold": (
        "Latin America still chooses rules-based Western terms over rivals",
        +1,
        ["latam_theater_western_terms_hold", "port_control_restored"],
    ),
    "cuba_pressure_justified": (
        "Cuba's one-party regime jails critics and wrecked its economy; pressure is warranted",
        +1,
        ["cuba_repression_documented", "cuba_theater_pressure_consensus"],
    ),
    "venezuela_intervention_justified": (
        "Removing the Maduro narco-state and restoring the oil sector is a win",
        +1,
        [
            "ven_coercion_justified",
            "ven_oil_restart_opportunity",
            "ven_theater_western_consensus",
        ],
    ),
    "balkan_investment_development": (
        "Foreign investment in the Balkans is legitimate development",
        +1,
        ["balkan_investment_development", "balkan_theater_investment_opportunity"],
    ),
    "alberta_grievance_legitimate": (
        "Alberta's grievance reflects real material fault lines",
        +1,
        ["alberta_legitimate_grievance", "uscat_provincial_grievance"],
    ),
    "arctic_development_normal": (
        "Arctic resource development and shipping are normal opportunity",
        +1,
        ["arctic_resource_development", "arctic_route_opportunity"],
    ),
    "mexico_cartel_offensive_progress": (
        "Mexico's own offensive against the cartels is making progress",
        +1,
        ["cartel_offensive_progress"],
    ),
    # ================= AMERICA FIRST (US right-flank, +) ======================
    "america_first_transactional_alliance": (
        "America First: allies freeload on US protection and must pay / rebalance",
        +1,
        [
            "defence_europe_must_pay",
            "europe_us_america_first",
            "trade_us_tariffs_justified",
            "autonomy_illusion",
            "tech_eu_overreach",
            "uscat_us_leverage_case",
            "usca_trade_rebalancing",
            "casp_continental_dependence",
        ],
    ),
    "america_first_manifest_expansion": (
        "US strategic expansion (Greenland, hemisphere) is legitimate necessity",
        +1,
        ["greenland_us_strategic_claim"],
    ),
    "america_first_cartel_intervention": (
        "Cartels are terrorists; US pressure and intervention on Mexico is justified",
        +1,
        ["mexth_us_pressure_justified", "intervention_necessity", "leverage_justified"],
    ),
    "us_executive_mandate": (
        "The administration is lawfully executing the mandate voters gave it",
        +1,
        [
            "usdom_theater_conservative_case",
            "usdom_electoral_integrity_case",
            "usdom_epstein_accountability",
            "usdom_fed_orderly_succession",
            "usdom_ice_enforcement_mandate",
            "usdom_loyalty_prerogative",
            "usdom_press_accountability",
            "usdom_violence_protective_response",
            "usdom_courts_checks_hold",
        ],
    ),
    # ================= WESTERN LIBERAL / RESTRAINT CRITIQUE (−) ===============
    "us_domestic_liberal_alarm": (
        "US institutions, due process and democratic norms are under threat from within",
        -1,
        [
            "usdom_theater_liberal_alarm",
            "usdom_electoral_franchise_threat",
            "usdom_epstein_obstruction",
            "usdom_loyalty_hollowing",
            "usdom_fed_capture_risk",
            "usdom_ice_due_process",
            "usdom_courts_deference",
            "usdom_violence_climate",
            "usdom_press_suppression",
            "western_systemic_alarm",
        ],
    ),
    "eu_sovereigntist_revolt": (
        "Brussels overreaches; nations and voters are right to resist",
        -1,
        [
            "eu_sovereigntist_revolt",
            "budget_national_sovereignty",
            "migration_national_control",
            "realignment_new_majority",
            "hungary_sovereignty_interference",
            "france_popular_will",
            "afd_exclusion_undemocratic",
            "hungary_brussels_coercion",
        ],
    ),
    "russia_threat_restraint_skeptic": (
        "Threat inflation and militarisation drift are a costly overreaction",
        -1,
        [
            "escalation_risk_restraint",
            "russia_europe_critical_restraint",
            "securitisation_caution",
            "militarisation_overreach",
        ],
    ),
    "western_intervention_scrutiny": (
        "Western/US coercive interventions deserve legal and humanitarian scrutiny",
        -1,
        [
            "western_intervention_scrutiny",
            "mexth_western_scrutiny",
            "ven_coercion_western_critical",
            "ven_transition_democracy_betrayed",
            "ven_oil_deals_opacity",
            "colombia_transition_institutional_concern",
            "greenland_sovereignty_defense",
            "arctic_western_sovereignty_stewardship",
            "south_asia_international_rights",
            "ven_theater_western_critical",
        ],
    ),
    "trade_war_economic_harm": (
        "Tariffs and trade coercion are self-harming economic disruption",
        -1,
        [
            "trade_european_defence",
            "trade_economic_disruption",
            "us_china_tariff_self_harm",
            "usca_economic_coercion",
            "trade_pressure_sovereignty_defense",
            "us_china_summit_weak_hand",
            "us_china_western_engagement_critique",
        ],
    ),
    "alliance_reliability_doubt": (
        "The US alliance is unreliable and delivering less than promised",
        -1,
        [
            "aukus_capability_doubt",
            "australia_alliance_scepticism",
            "defence_unreliable_america",
            "alliance_autonomy_strain",
            "autonomy_european_awakening",
            "us_commitment_doubted",
            "taiwan_strait_western_doubt",
            "europe_us_transatlantic_rupture",
            "uscat_canadian_consensus",
            "us_russia_normalisation_premature",
            "us_russia_relief_rewards_moscow",
            "us_russia_theater_western_alarm",
        ],
    ),
    # ================= ADVERSARIAL STATE MEDIA (RU/CN/IR, mostly −) ===========
    "west_rift_hypocrisy": (
        "Intra-Western disputes expose Western hypocrisy, disunity and decline",
        -1,
        [
            "eu_fracture_rift_exploitation",
            "europe_us_western_disunity",
            "autonomy_multipolar_welcome",
            "defence_nato_racket",
            "tech_digital_colonialism",
            "greenland_western_hypocrisy",
            "trade_western_vassalage",
            "migration_eu_failure_kremlin",
            "france_decline_kremlin",
            "afd_persecution_kremlin",
            "alberta_external_amplification",
        ],
    ),
    "us_imperial_coercion_hemisphere": (
        "US imperial/hegemonic coercion of smaller sovereign states",
        -1,
        [
            "anti_hegemony_rift",
            "mexth_anti_hegemony_rift",
            "colombia_theater_hegemonic_critique",
            "latam_theater_coercion_critique",
            "colombia_us_imperial_overreach",
            "casp_imperial_overreach",
            "uscat_external_rift",
            "usca_bloc_fracture",
            "latam_theater_terms_imposed",
            "cuba_theater_anti_imperial",
            "cuba_force_imperial_aggression",
            "cuba_sovereign_resistance",
            "ven_coercion_anti_imperial",
            "ven_oil_imperial_plunder",
            "ven_theater_anti_imperial",
            "ven_transition_imperial_puppet",
            "colombia_us_coercion",
            "colombia_theater_external_pressure",
            "casp_sovereignty_defence",
            "mexth_mexican_sovereignty",
            "mexican_sovereignty_defense",
            "trade_coercion_pushback",
        ],
    ),
    "cuba_venezuela_humanitarian_siege": (
        "US sanctions are an illegal humanitarian siege on Cuba/Venezuela",
        -1,
        [
            "cuba_economic_warfare",
            "cuba_collapse_starvation_siege",
            "cuba_lifelines_solidarity",
            "cuba_collapse_humanitarian_alarm",
            "cuba_force_unlawful",
            "cuba_lifelines_humanitarian_duty",
            "cuba_reform_under_siege",
            "cuba_sanctions_overreach",
            "cuba_theater_western_critique",
        ],
    ),
    "nato_aggression_russia_defensive": (
        "NATO encirclement/provocation is the aggressor; Russia responds defensively",
        -1,
        [
            "nato_complicity_provocation",
            "russia_europe_kremlin_counter",
            "nato_encirclement_provocation",
            "arctic_nato_militarization",
            "arctic_russia_china_counter",
            "caucasus_russia_china_counter",
            "hybrid_russophobia_denial",
            "awp_russian_capture",
            "cpc_russia_iran_resistance",
        ],
    ),
    "russia_smo_defensive": (
        "Russia's war is a defensive special military operation; Ukraine strikes are terror",
        -1,
        [
            "russian_smo_operations",
            "russia_special_military_operation",
            "infrastructure_war_energy_terror",
        ],
    ),
    "ukraine_regime_illegitimate": (
        "The Zelensky government is corrupt and illegitimate",
        -1,
        ["zelensky_regime_corruption"],
    ),
    "ukraine_war_proxy_escalation": (
        "The war is a US/NATO proxy war; Western aid prolongs it; freeze/settle",
        -1,
        [
            "aid_as_escalation_and_proxy",
            "proxy_war_restraint_critique",
            "russian_maximalist_peace",
            "frontline_freeze_settlement",
        ],
    ),
    "russia_sanctions_backfire": (
        "Sanctions on Russia are ineffective and backfire on the West",
        -1,
        ["sanctions_ineffective_and_backfiring"],
    ),
    "russia_vindicated": (
        "Events vindicate Russia; the West must recognise its position",
        +1,
        [
            "us_russia_us_buildup_drives_race",
            "us_russia_washington_realism",
            "us_russia_sanctions_illegitimate",
            "us_russia_theater_kremlin_vindication",
        ],
    ),
    "russia_washington_bad_faith": (
        "Washington negotiates in bad faith while pressuring Russia",
        -1,
        [
            "us_russia_washington_bad_faith",
            "us_russia_theater_kremlin_grievance",
            "us_china_summit_multipolar_framing",
        ],
    ),
    "china_territorial_sovereignty": (
        "Taiwan, the SCS and the Senkakus are Chinese territory; foreign interference provokes",
        -1,
        [
            "one_china_consensus",
            "pla_sovereignty_enforcement",
            "beijing_antiseparatism_unity",
            "taiwan_strait_beijing_counter",
            "taiwan_us_pawn",
            "jc_taiwan_interference_charge",
            "senkaku_chinese_rights_protection",
        ],
    ),
    "china_lawful_not_coercive": (
        "China's trade/tech measures are lawful and normal; the US is the aggressor",
        -1,
        [
            "cjer_lawful_regulation",
            "trade_mutual_benefit",
            "us_china_minerals_lawful_leverage",
            "us_china_tech_containment",
            "us_china_trade_unilateralism",
            "us_china_ai_suppression",
            "us_china_summit_new_chapter",
            "us_china_beijing_moscow_counter",
            "china_threat_fabricated",
            "australia_china_counter",
            "aukus_bloc_confrontation",
            "pacific_china_cooperation",
            "port_expropriation_coercion",
        ],
    ),
    "japan_militarism_revival": (
        "Japan is reviving militarism behind a pacifist facade",
        -1,
        [
            "jc_theater_chinese_state_counter",
            "jde_militarism_revival",
            "memory_historical_accountability",
        ],
    ),
    "us_domestic_decline_adversarial": (
        "US democracy and institutions are decaying (adversarial state-media reading)",
        -1,
        [
            "usdom_theater_decline",
            "usdom_electoral_democracy_facade",
            "usdom_epstein_western_impunity",
            "usdom_loyalty_court_politics",
            "usdom_fed_dollar_decline",
            "usdom_ice_american_repression",
            "usdom_courts_politicised",
            "usdom_violence_instability",
            "usdom_press_hypocrisy",
        ],
    ),
    "multipolar_alternative": (
        "A multipolar order is the legitimate alternative to US hegemony",
        +1,
        [
            "multipolar_systemic_alternative",
            "resource_south_south_partnership",
            "latam_theater_eastern_partnership",
            "balkan_theater_external_backing",
            "serbia_sovereignty_defense",
        ],
    ),
    "korea_us_containment_critique": (
        "US alliances on the peninsula are a containment instrument",
        -1,
        ["korea_us_containment_critique", "alliance_containment_instrument"],
    ),
    "dprk_sovereign_deterrent": (
        "North Korea's deterrent and its Russia/China partnerships are legitimate",
        +1,
        [
            "nk_sovereign_deterrent",
            "dprk_russia_comradeship",
            "korea_sanctioned_bloc",
            "china_dprk_friendship",
        ],
    ),
    # ================= REGIONAL OWNERS =======================================
    # -- Israel / pro-Israel
    "israel_existential_self_defense": (
        "Israel's campaigns are existential self-defense after October 7",
        +1,
        [
            "israel_dismantle_hamas",
            "israel_existential_self_defense",
            "israel_preemptive_strike_doctrine",
            "israel_self_defense_north",
            "judea_samaria_sovereignty",
            "houthi_iranian_proxy_aggression",
            "israeli_strikes_on_syria_legitimate",
        ],
    ),
    "israel_syria_jihadist_warning": (
        "The new Syrian government are jihadists; normalisation legitimises them",
        -1,
        ["recognition_legitimises_jihadists", "syria_jihadist_takeover_warning"],
    ),
    "israel_turkey_unreliable": (
        "Erdogan's Turkey is a two-faced, hostile actor",
        -1,
        [
            "turkey_two_faced_opportunist",
            "turkey_unreliable_ally_warning",
            "turkey_wrong_side_on_iran",
        ],
    ),
    # -- Iran / Axis of Resistance
    "iran_axis_of_resistance": (
        "The Axis of Resistance is legitimate anti-Israel/anti-US liberation",
        +1,
        [
            "iran_axis_of_resistance",
            "iran_gulf_resistance_solidarity",
            "houthi_authority_legitimate_resistance",
            "houthi_naval_pressure_legitimate",
            "houthi_resistance_strikes_legitimate",
            "houthis_fourth_front_solidarity",
            "hezbollah_resistance_north",
            "iran_legitimate_retaliation_doctrine",
            "syrian_sovereignty_under_israeli_aggression",
        ],
    ),
    "iran_sovereign_rights": (
        "Iran's nuclear program, system and Hormuz stance are sovereign rights",
        +1,
        [
            "iran_nuclear_sovereign_right",
            "iran_sovereign_existence",
            "iran_hormuz_sovereign_pressure",
        ],
    ),
    "iran_regime_threat": (
        "The Israel-US-Saudi coalition: Iran is an illegitimate existential threat",
        -1,
        [
            "west_iran_nuclear_threat",
            "west_iran_proxy_network_threat",
            "west_iran_regime_change_doctrine",
            "west_gulf_aggression_response",
            "west_hormuz_freedom_of_navigation",
            "iran_proxy_destabilisation",
            "freedom_of_navigation_defense",
        ],
    ),
    # -- Palestine / pan-Arab
    "palestine_catastrophe": (
        "Israel's Gaza/West Bank campaign is a humanitarian catastrophe / apartheid",
        -1,
        [
            "gaza_humanitarian_catastrophe",
            "palestine_genocide_framing",
            "west_bank_apartheid_framing",
            "multipolar_anti_israel_alignment",
        ],
    ),
    "eu_two_state_engagement": (
        "The EU/E3 pursue calibrated engagement (Iran diplomacy, two-state, Turkey)",
        0,
        [
            "eu_diplomatic_preservation_norm",
            "eu_two_state_pathway",
            "turkey_eu_engagement_pragmatic",
            "western_pragmatic_navigation",
            "coalition_counter_isis_necessary",
        ],
    ),
    # -- India / Pakistan
    "india_account": (
        "India's account: Pakistan sponsors militancy; Kashmir is integral; treaty obsolete",
        +1,
        [
            "militancy_pakistan_sponsorship",
            "indus_treaty_obsolete",
            "kashmir_integral_to_india",
            "south_asia_indian_account",
            "baloch_pakistan_internal_failure",
            "south_asia_indian_critique_of_pakistan",
        ],
    ),
    "pakistan_grievance": (
        "Pakistan's account: India coerces, weaponises water, occupies Kashmir",
        -1,
        [
            "militancy_indian_pretext",
            "indus_water_weaponisation",
            "kashmir_disputed_territory",
            "south_asia_pakistani_grievance",
            "baloch_rights_repression",
            "kashmir_rights_and_restrictions",
        ],
    ),
    "pakistan_security_account": (
        "Pakistan's security account: cross-border counterterror is legitimate",
        +1,
        [
            "baloch_foreign_backed_insurgency",
            "pakafg_counterterror_necessity",
            "south_asia_pakistani_security_account",
        ],
    ),
    "afghan_sovereignty_violation": (
        "Pakistani cross-border strikes violate Afghan sovereignty",
        -1,
        ["pakafg_afghan_sovereignty_violation", "pakafg_civilian_harm_alarm"],
    ),
    # -- Global South agency / non-alignment
    "global_south_buyer_autonomy": (
        "Sanctions/pressure are conditional; the Global South asserts buyer autonomy",
        +1,
        [
            "us_russia_buyer_autonomy",
            "us_russia_theater_buyer_autonomy",
            "resource_sovereign_development",
            "latam_theater_regional_agency",
            "m23_backing_charge_rejected",
            "drc_sanctions_rejected",
        ],
    ),
    "latam_resource_extractivism_critique": (
        "Whichever external buyer wins, extraction reproduces dependency",
        -1,
        ["resource_extractivism_critique"],
    ),
    "latam_china_penetration_warning": (
        "Chinese port/rail/mineral holdings are strategic penetration of the hemisphere",
        -1,
        ["latam_theater_strategic_warning", "resource_strategic_penetration"],
    ),
    "mercosur_market_opportunity": (
        "The Mercosur-EU deal is long-delayed market access",
        +1,
        ["mercosur_market_opportunity"],
    ),
    "mercosur_european_protection": (
        "European farmers/environment object to Mercosur market opening",
        -1,
        [
            "mercosur_farm_protection",
            "mercosur_environmental_critique",
            "latam_theater_european_objection",
            "mercosur_european_obstruction",
        ],
    ),
    # -- Turkey
    "turkey_middle_power": (
        "Turkey is a legitimate independent middle power and broker",
        +1,
        [
            "turkey_independent_middle_power",
            "turkey_legitimate_broker",
            "turkey_anti_graft_legalism_defense",
            "pkk_terror_full_disarmament",
            "damascus_territorial_reunification",
        ],
    ),
    "turkey_authoritarian_drift": (
        "Turkey is sliding into authoritarianism (Western liberal critique)",
        -1,
        ["turkey_authoritarian_drift_critique"],
    ),
    # -- Syria
    "syria_legitimate_transition": (
        "The post-Assad transition is legitimate; foreign forces should leave",
        +1,
        [
            "syria_legitimate_transition",
            "foreign_military_withdrawal_demand",
            "international_engagement_pragmatic",
        ],
    ),
    # -- Horn of Africa
    "horn_new_partnerships": (
        "New recognition/basing/minerals partnerships are reordering the Horn",
        +1,
        [
            "horn_new_partnerships",
            "horn_regional_stabilisers",
            "somali_state_rebuilding",
        ],
    ),
    "horn_sovereignty_violated": (
        "The Horn realignment violates borders and sovereignty",
        -1,
        [
            "horn_sovereignty_bloc",
            "somali_territorial_integrity",
            "ethiopia_regional_revisionism",
            "somaliland_transactional_scramble",
            "horn_russian_iranian_counter",
            "somali_foreign_militarisation_critique",
        ],
    ),
    "somaliland_statehood": (
        "Somaliland has earned recognition through self-governance",
        +1,
        ["somaliland_statehood_earned"],
    ),
    "somalia_western_alarm": (
        "Somalia's fragility and civilian harm are deepening",
        -1,
        [
            "somali_fragility_and_harm",
            "horn_western_alarm",
            "ethiopia_renewed_war_alarm",
        ],
    ),
    # -- Sahel
    "sahel_sovereigntist_partnership": (
        "The Sahel juntas rightly chose new partners free of colonial conditions",
        +1,
        [
            "sahel_break_with_paris_justified",
            "sahel_counterterror_necessity",
            "sahel_russian_partnership_delivers",
            "sahel_sovereigntist_self_reliance",
            "sahel_theater_partnership_frame",
            "sahel_separatism_as_jihadist_alliance",
            "sahel_theater_regional_security_response",
        ],
    ),
    "sahel_managed_collapse": (
        "Sahel military rule delivers neither security nor politics; abuses mount",
        -1,
        [
            "sahel_theater_state_collapse_critique",
            "sahel_democratic_closure",
            "sahel_counterinsurgency_abuses",
            "sahel_patron_model_failing",
            "sahel_rupture_deepens_isolation",
            "sahel_state_losing_ground",
            "sahel_theater_civilian_cost",
            "sahel_northern_autonomy_claim",
        ],
    ),
    # -- Sudan
    "sudan_army_legitimacy": (
        "The Sudanese army is the legitimate authority against the RSF",
        +1,
        ["sudan_state_legitimacy"],
    ),
    "sudan_catastrophe": (
        "Sudan is a humanitarian catastrophe and proxy war",
        -1,
        ["sudan_humanitarian_catastrophe", "sudan_proxy_war_critique"],
    ),
    # -- Saudi / Yemen
    "saudi_coalition_legitimacy": (
        "The Saudi-led coalition restores legitimate government in Yemen",
        -1,
        ["saudi_coalition_legitimacy_restoration"],
    ),
    # -- DRC / Great Lakes critical
    "greatlakes_costs_critique": (
        "External fixes stall; minerals extraction and proxy war impose costs",
        -1,
        [
            "drc_minerals_as_resource_capture",
            "drc_minerals_human_cost",
            "drc_accords_stalling",
            "great_lakes_proxy_war_and_its_costs",
            "great_lakes_scepticism_of_outside_fixes",
            "m23_civilian_toll",
            "m23_externally_backed_offensive",
        ],
    ),
    # -- Colombia critical
    "colombia_peace_failure": (
        "Open-ended negotiation lets armed groups regroup",
        -1,
        ["colombia_peace_process_failure"],
    ),
    "colombia_hard_turn": (
        "Voters rejected negotiation with armed groups (hard-line reading)",
        +1,
        ["colombia_theater_hard_turn"],
    ),
    # -- Balkan / Serbia critical
    "serbia_accountability_deficit": (
        "Balkan elites (Serbia) face an accountability deficit; protests are legitimate",
        -1,
        [
            "balkan_theater_accountability_deficit",
            "serbia_protest_accountability",
            "balkan_sovereignty_environmental_rejection",
        ],
    ),
    # -- Georgia
    "georgia_european_aspiration": (
        "Georgians want a European future their government is blocking",
        +1,
        ["ggd_european_aspiration"],
    ),
    "georgia_sovereignty_stability": (
        "Georgia's government rightly resisted a Western-funded destabilisation",
        -1,
        ["ggd_sovereignty_stability"],
    ),
    # -- Myanmar
    "myanmar_junta_illegitimate": (
        "Myanmar's junta and sham election are illegitimate",
        -1,
        ["myanmar_illegitimate_junta_rule", "myanmar_criminal_economy_spillover"],
    ),
    "myanmar_normalisation": (
        "Myanmar's election and civilian handover mark a return to order",
        +1,
        ["myanmar_beijing_backed_normalisation"],
    ),
    # -- Korea / DPRK threat (Western)
    "dprk_proliferation_threat": (
        "North Korea's proliferation and closed door are a hardening threat",
        -1,
        [
            "nk_proliferation_threat",
            "korea_hardening_threat",
            "pyongyang_closed_the_door",
            "beijing_shields_pyongyang",
            "dprk_russia_blood_for_technology",
        ],
    ),
    # -- Kurds
    "kurdish_political_rights": (
        "Kurdish political rights and self-administration deserve protection",
        -1,
        ["kurdish_political_rights_critique", "kurdish_self_administration"],
    ),
    # -- misc single-frame regional
    "essequibo_guyana": (
        "Guyana's Essequibo border is settled; Venezuela's claim is revanchist",
        -1,
        ["ven_essequibo_guyana_sovereignty"],
    ),
    "essequibo_venezuela": (
        "The Essequibo is Venezuelan by historical right",
        +1,
        ["ven_essequibo_venezuelan_claim"],
    ),
    "venezuela_stabilization": (
        "The caretaker administration is stabilising Venezuela",
        +1,
        ["ven_transition_stabilization"],
    ),
    "arctic_environmental_alarm": (
        "Arctic warming and extraction are an environmental emergency",
        -1,
        ["arctic_drilling_environmental_alarm"],
    ),
    "arctic_route_strategic_threat": (
        "Russian/Chinese control of Arctic routes is a strategic threat",
        -1,
        ["arctic_route_strategic_threat"],
    ),
    "scs_rules_based_order": (
        "The South China Sea must follow the rules-based maritime order",
        +1,
        ["scs_rules_based_maritime_order"],
    ),
    "scs_chinese_claim": (
        "China's South China Sea claims are sovereign",
        +1,
        ["scs_chinese_sovereignty_claim"],
    ),
    "eu_more_integration": (
        "Deeper EU integration and solidarity are the answer",
        +1,
        [
            "budget_more_europe",
            "eu_cohesion_hold",
            "migration_solidarity_rights",
            "realignment_firewall_defense",
            "france_republican_defense",
            "afd_democratic_defense",
            "hungary_eu_standards",
        ],
    ),
    "tech_digital_sovereignty": (
        "Europe needs digital sovereignty against US tech dominance",
        -1,
        ["tech_digital_sovereignty"],
    ),
    "greenland_self_determination": (
        "Greenland's own agency and self-determination come first",
        0,
        ["greenland_self_determination"],
    ),
    "thaicam_thai": (
        "Thailand's account of the border dispute (Koh Kood is Thai)",
        +1,
        ["thaicam_thai_sovereignty_defence"],
    ),
    "thaicam_cambodian": (
        "Cambodia's account (Thailand occupies Cambodian ground)",
        -1,
        ["thaicam_cambodian_territorial_claim"],
    ),
    "thaicam_mediation": (
        "The Thailand-Cambodia clash as an occasion for great-power mediation",
        0,
        ["thaicam_great_power_mediation"],
    ),
    "zangezur_threat": (
        "The Zangezur corridor is an extraterritorial strategic threat",
        -1,
        ["zc_sovereignty_threat"],
    ),
    "aas_contested": (
        "The Armenia-Azerbaijan settlement is contested / imposed",
        -1,
        ["aas_contested_settlement"],
    ),
    "alberta_unity_defence": (
        "Alberta separatism is a dangerous bluff and an opening for outside pressure",
        -1,
        ["alberta_unity_defence"],
    ),
    "cartel_narco_state_critique": (
        "Mexico's cartel problem is a narco-state failure",
        -1,
        ["cartel_narco_state_critique"],
    ),
    "taiwan_one_china_recognition": (
        "One-China: Resolution 2758 settles Taiwan's status",
        -1,
        [],  # placeholder folded below
    ),
}


def main():
    rows = json.loads(DUMP.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in rows}
    all_ids = set(by_id)

    # fold the accidental placeholder
    POSITIONS.pop("taiwan_one_china_recognition", None)

    assigned: dict[str, str] = {}
    dupes = []
    unknown = []
    for pid, (_, _, ids) in POSITIONS.items():
        for nid in ids:
            if nid not in all_ids:
                unknown.append((pid, nid))
            elif nid in assigned:
                dupes.append((nid, assigned[nid], pid))
            else:
                assigned[nid] = pid
    missing = sorted(all_ids - set(assigned))

    print("positions defined : %d" % len(POSITIONS))
    print("cards assigned    : %d / %d" % (len(assigned), len(all_ids)))
    print("collapse ratio    : %.2fx" % (len(all_ids) / max(len(POSITIONS), 1)))
    if unknown:
        print("\nUNKNOWN ids (%d):" % len(unknown))
        for p, n in unknown:
            print("  %s -> %s" % (p, n))
    if dupes:
        print("\nDUPLICATE assignments (%d):" % len(dupes))
        for n, a, b in dupes:
            print("  %s in both %s and %s" % (n, a, b))
    if missing:
        print("\nUNASSIGNED (%d):" % len(missing))
        for n in missing:
            r = by_id[n]
            print(
                "  %-40s [%s %+d] %s"
                % (n, r["fn_id"][:24], r["stance"] or 0, (r["claim_en"] or "")[:60])
            )

    if unknown or dupes or missing:
        sys.exit("\nNOT COMPLETE -- fix before writing report")

    # size distribution
    sizes = collections.Counter(len(ids) for _, _, ids in POSITIONS.values())
    multi = sum(1 for _, _, ids in POSITIONS.values() if len(ids) > 1)
    print("\npositions with >1 card: %d" % multi)
    print("singletons            : %d" % (len(POSITIONS) - multi))
    print("size histogram        : %s" % dict(sorted(sizes.items())))

    # cross-theater reach: how many distinct FNs does each position span?
    L = []
    L.append("# P0(e) -- Position clustering (idea 1 experiment)")
    L.append("")
    L.append(
        "Does the flat 411-card layer collapse into a smaller set of reusable "
        "**positions** (universal narrative cores)? This is an LLM-judgment "
        "clustering of every active card, keyed on frame + stance sign, not text "
        "similarity. Read-only, nothing written. DRAFT for review."
    )
    L.append("")
    L.append("| | |")
    L.append("|---|---:|")
    L.append("| active cards (narratives_v2) | %d |" % len(all_ids))
    L.append("| **positions** | **%d** |" % len(POSITIONS))
    L.append("| collapse ratio | %.2fx |" % (len(all_ids) / len(POSITIONS)))
    L.append("| positions spanning >1 friction node | %d |" % multi)
    L.append("| single-card positions | %d |" % (len(POSITIONS) - multi))
    L.append("")
    L.append(
        "The %d single-card positions are genuinely theater-specific voices "
        "(Thai border claim, Somaliland statehood). They are not merge failures -- "
        "a position may legitimately appear once. The value is concentrated in the "
        "%d multi-FN positions, which absorb %d of the %d cards."
        % (
            len(POSITIONS) - multi,
            multi,
            sum(len(ids) for _, _, ids in POSITIONS.values() if len(ids) > 1),
            len(all_ids),
        )
    )
    L.append("")
    L.append("## Positions, largest first")
    L.append("")
    L.append(
        "`FNs` = distinct friction nodes the position spans. A position with FNs "
        "far below its card count is double-counting one FN and needs a split."
    )
    L.append("")
    ordered = sorted(POSITIONS.items(), key=lambda kv: -len(kv[1][2]))
    for pid, (name, sign, ids) in ordered:
        fns = {by_id[n]["fn_id"] for n in ids}
        cos = collections.Counter(by_id[n]["coalition"] for n in ids)
        L.append(
            "### `%s`  (%+d) -- %d cards / %d FNs" % (pid, sign, len(ids), len(fns))
        )
        L.append("")
        L.append("> %s" % name)
        L.append("")
        L.append(
            "- owners (from card publisher blocs): %s"
            % ", ".join("`%s`(%d)" % (c, n) for c, n in cos.most_common())
        )
        L.append("- cards: %s" % ", ".join("`%s`" % n for n in sorted(ids)))
        L.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

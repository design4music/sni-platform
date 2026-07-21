# P0(a) — Narrative archetype clustering

Artifact for `NARRATIVE_CONSOLIDATION_SPEC.md` §3.A3 step 1, feeding **DG-0 #1**.
Read-only; nothing was written to the database.

**Method.** Narratives are clustered by *measured publisher-set overlap* (average-linkage Jaccard, threshold 0.22), not by an invented bloc vocabulary — naming coalitions is DG-0 #2. An **archetype** is then (publisher bloc x stance sign). Assign one meta-narrative per archetype below; that is the ~39 judgment calls the spec asks for, instead of 411.

> Title/match counts are deliberately omitted: a full attribution rebuild was in flight when this ran, so any count here would be a moving target. Thin-narrative triage (P0c) must run after that completes.

| | |
|---|---|
| active narratives | 411 |
| clustered (>= 3 publishers) | 408 |
| too thin to cluster | 3 |
| publisher blocs found | 24 |
| **archetypes (bloc x sign)** | **39** |

---

## Archetypes

Each row is one assignment decision. `meta:` is left blank for you to fill.

### A01 — bloc 0, critical (-) — 87 narratives

- **top publishers**: BBC World (85), Deutsche Welle (85), Associated Press (85), Reuters (85), France 24 (EN) (84), The Guardian (84), Euronews (70), New York Times (63)
- **regions**: AMERICAS-USA (17), NON-STATE-EU (7), AMERICAS-CUBA (6), AFRICA-SAHEL (6), AMERICAS-VENEZUELA (5), ASIA-NORKOREA (5)
- **friction nodes**: 86 distinct — m23_conflict, eu_budget_sovereignty, eu_migration_burden_sharing, hungary_rule_of_law, eu_cohesion_theater, cuba_embargo_sanctions
- `meta:` _______________

<details><summary>87 narratives</summary>

- `alberta_unity_defence` (alberta_separatism_us_ties, stance -1) — A dangerous bluff, and an opening for outside pressure
- `arctic_drilling_environmental_alarm` (arctic_resources_competition, stance -1) — Arctic warming and resource extraction are an environmental and climate emergency
- `arctic_route_strategic_threat` (arctic_shipping_routes, stance -1) — Russian and Chinese control of Arctic routes is a strategic threat
- `arctic_western_sovereignty_stewardship` (arctic_theater, stance -1) — Coercion and reckless exploitation of the Arctic must be resisted — for allied sovereignty
- `aukus_capability_doubt` (aukus_alliance_reliability, stance -1) — AUKUS is delivering less than promised and binds Australia to an unreliable partner
- `australia_alliance_scepticism` (australia_theater, stance -1) — The alliance is delivering less than Australia was promised
- `balkan_sovereignty_environmental_rejection` (balkan_foreign_capital, stance -2) — 'Albania is not for sale': a protected coastline is being privatised for elite foreign gai
- `balkan_theater_accountability_deficit` (balkan_theater, stance -2) — From a collapsed canopy to a privatised coastline, political elites are accused of priorit
- `baloch_rights_repression` (balochistan_insurgency, stance -1) — The state answers Baloch grievances with force and detention
- `casp_sovereignty_defence` (canada_sovereignty_pressure, stance -2) — Sovereignty under pressure
- `colombia_transition_institutional_concern` (colombia_political_transition, stance -1) — The result strains the guardrails
- `colombia_theater_external_pressure` (colombia_theater, stance -1) — Decisions shaped from outside
- `colombia_us_coercion` (colombia_us_alignment, stance -1) — Threats replaced diplomacy
- `cuba_sanctions_overreach` (cuba_embargo_sanctions, stance -1) — Extraterritorial sanctions are collective punishment
- `cuba_collapse_humanitarian_alarm` (cuba_energy_collapse, stance -1) — A humanitarian emergency is unfolding whoever is to blame
- `cuba_lifelines_humanitarian_duty` (cuba_external_lifelines, stance -1) — Relief is a humanitarian obligation and third states should not be coerced
- `cuba_force_unlawful` (cuba_military_coercion, stance -1) — Threatening to take an island is unlawful and reckless
- `cuba_reform_under_siege` (cuba_regime_survival, stance -1) — A real opening is under way but external pressure is throttling it
- `cuba_theater_western_critique` (cuba_theater, stance -1) — The pressure campaign has become a humanitarian and legal problem of its own
- `drc_minerals_human_cost` (drc_minerals_competition, stance -1) — The price is paid at the pit
- `drc_accords_stalling` (drc_peace_process, stance -1) — Signed, stalled, and unenforced
- `ven_essequibo_guyana_sovereignty` (essequibo_dispute, stance -1) — Venezuela's claim is an oil-driven threat to Guyana
- `ethiopia_renewed_war_alarm` (ethiopia_regional_confrontation, stance -1) — A second northern war in the making
- `budget_national_sovereignty` (eu_budget_sovereignty, stance -1) — Brussels wants more money and power at the expense of nations and taxpayers
- `eu_sovereigntist_revolt` (eu_cohesion_theater, stance -1) — Nations and voters are resisting an overreaching Brussels
- `migration_national_control` (eu_migration_burden_sharing, stance -1) — Member states must control borders and curb irregular migration
- `autonomy_european_awakening` (eu_strategic_autonomy, stance -1) — Europe is finally awakening to strategic autonomy and must build its own defence
- `defence_unreliable_america` (europe_us_defence_dependence, stance -1) — A wavering America is an unreliable protector, forcing an alarmed Europe to scramble
- `tech_digital_sovereignty` (europe_us_tech_sovereignty, stance -1) — Europe must rein in US Big Tech and reclaim its digital sovereignty
- `europe_us_transatlantic_rupture` (europe_us_theater, stance -1) — A vital alliance is rupturing, forcing an alarmed Europe to defend itself and its interest
- `great_lakes_proxy_war_and_its_costs` (great_lakes_theater, stance -2) — A cross-border war paid for by civilians
- `greenland_sovereignty_defense` (greenland_control, stance -1) — Coercion over Greenland is unacceptable; Danish/European sovereignty must be defended
- `horn_western_alarm` (horn_africa_theater, stance -1) — Western alarm at fragmentation and famine
- `hungary_sovereignty_interference` (hungary_rule_of_law, stance -1) — Brussels interferes in a sovereign nation's democracy
- `pyongyang_closed_the_door` (inter_korean_relations, stance -2) — Pyongyang has formally closed the inter-Korean track
- `kashmir_rights_and_restrictions` (kashmir_dispute, stance -1) — Both administrations face unrest and answer it with force
- `alliance_autonomy_strain` (korea_peninsula_deterrence, stance -1) — Seoul is pushing for autonomy and the alliance terms are being renegotiated
- `korea_hardening_threat` (korea_theater, stance -2) — A hardening threat while the pressure regime frays
- `latam_theater_terms_imposed` (latam_hemispheric_theater, stance -1) — The costs land locally
- `trade_pressure_sovereignty_defense` (latam_us_trade_pressure, stance -1) — Tariffs punish a trade partner
- `m23_civilian_toll` (m23_conflict, stance -1) — The population pays for every advance
- `m23_externally_backed_offensive` (m23_conflict, stance -2) — An externally backed offensive
- `cartel_narco_state_critique` (mexico_cartel_war, stance -1) — Militarisation is failing and the state is compromised: collusion, corruption and impunity
- `mexth_western_scrutiny` (mexico_theater, stance -1) — US pressure strains the relationship and carries scandal and economic risk
- `myanmar_illegitimate_junta_rule` (myanmar_civil_conflict, stance -2) — Sham election, illegitimate junta
- `beijing_shields_pyongyang` (north_korea_china_patronage, stance -2) — Beijing's lifeline is what keeps the pressure regime from working
- `nk_proliferation_threat` (north_korea_missile_program, stance -2) — An expanding arsenal that must be contained
- `dprk_russia_blood_for_technology` (north_korea_russia_alignment, stance -2) — Troops and shells for cash and missile technology
- `pakafg_civilian_harm_alarm` (pakistan_afghanistan_border, stance -1) — The border war is killing civilians and risks a wider conflict
- `freedom_of_navigation_defense` (red_sea_shipping_security, stance -1) — Houthi attacks on commercial vessels violate UNCLOS; coalition naval ops are necessary
- `sahel_rupture_deepens_isolation` (sahel_france_rupture, stance -2) — The break leaves the Sahel with fewer options, not more
- `sahel_state_losing_ground` (sahel_jihadist_insurgency, stance -2) — The state is losing territory it cannot recover
- `sahel_democratic_closure` (sahel_junta_consolidation, stance -2) — Military rule is closing the last civic space
- `sahel_patron_model_failing` (sahel_security_patron_contest, stance -2) — The replacement security model is buckling
- `sahel_theater_state_collapse_critique` (sahel_theater, stance -2) — A managed collapse: military rule that delivers neither security nor politics
- `sahel_northern_autonomy_claim` (sahel_tuareg_separatism, stance -2) — Northern Mali is a political question, not only a military one
- `somali_fragility_and_harm` (somalia_state_security, stance -1) — A fragile state and an abandoned population
- `south_asia_international_rights` (south_asia_theater, stance -1) — Across every front the cost falls on civilians and dissenters
- `sudan_humanitarian_catastrophe` (sudan_civil_war, stance -1) — Both sides commit atrocities; RSF violence in Darfur amounts to genocide
- `kurdish_self_administration` (syria_kurdish_question, stance -1) — Kurdish self-administration is a legitimate democratic experiment to be protected
- `taiwan_strait_western_doubt` (taiwan_strait_theater, stance -1) — Taiwan's protection is not assured -- Washington may bargain the island away and its defen
- `us_commitment_doubted` (taiwan_us_security_commitment, stance -1) — Washington's commitment is wavering and Taiwan risks being traded away
- `trade_european_defence` (transatlantic_trade, stance -1) — Trump's tariffs are economic coercion that Europe must resist with unity and countermeasur
- `kurdish_political_rights_critique` (turkey_kurdish_question, stance -1) — Turkey collapses Kurdish political rights into terror designation
- `western_systemic_alarm` (ukraine_official_corruption, stance -1) — Western alarm: high-level corruption threatens Ukraine credibility and aid
- `uscat_canadian_consensus` (us_canada_theater, stance -2) — An ally treated as a target
- `usca_economic_coercion` (us_canada_trade_coercion, stance -2) — Tariff coercion against a treaty partner
- `us_china_summit_weak_hand` (us_china_summit_diplomacy, stance -1) — Washington left the summit with little to show for it
- `us_china_western_engagement_critique` (us_china_theater, stance -1) — The instruments are backfiring: costs at home, allies hedging, leverage overstated
- `us_china_tariff_self_harm` (us_china_trade_tariffs, stance -1) — Tariff escalation costs US industry and consumers more than it wins
- `usdom_theater_liberal_alarm` (us_domestic_theater, stance -1) — Checks and balances under sustained strain
- `usdom_electoral_franchise_threat` (us_electoral_legitimacy, stance -1) — The rules are being rewritten to shape the result in advance
- `usdom_epstein_obstruction` (us_epstein_elite_network, stance -1) — Disclosure is being managed, delayed and selectively withheld
- `usdom_loyalty_hollowing` (us_executive_loyalty, stance -1) — Professional institutions are being hollowed out by loyalty tests
- `usdom_fed_capture_risk` (us_fed_independence, stance -1) — Political pressure is testing the limits of central-bank independence
- `usdom_ice_due_process` (us_interior_immigration_enforcement, stance -1) — Enforcement is outrunning due process and harming residents
- `usdom_courts_deference` (us_judicial_constraint, stance -1) — The bench is expanding executive discretion rather than checking it
- `western_intervention_scrutiny` (us_mexico_military_pressure, stance -1) — US pressure is straining the relationship and inviting scandal
- `usdom_violence_climate` (us_political_violence, stance -1) — Violence is becoming a recurring feature of political life
- `usdom_press_suppression` (us_press_freedom, stance -1) — State leverage is being used against critical coverage
- `us_russia_normalisation_premature` (us_russia_bilateral_channel, stance -1) — Normalising relations while the war continues legitimises the Kremlin and sidelines Europe
- `us_russia_relief_rewards_moscow` (us_russia_sanctions_leverage, stance -1) — Easing sanctions hands Moscow a windfall and squanders the West's main lever
- `us_russia_theater_western_alarm` (us_russia_theater, stance -1) — Accommodation is being granted without reciprocity, over the heads of Europe and Kyiv
- `ven_coercion_western_critical` (us_venezuela_relations, stance -1) — The intervention is lawless regime change
- `ven_transition_democracy_betrayed` (venezuela_political_transition, stance -1) — Chavismo survives; the opposition is frozen out
- `ven_oil_deals_opacity` (venezuela_sanctions_oil, stance -1) — The oil restart is opaque and serves Trump, not Venezuelans
- `ven_theater_western_critical` (venezuela_theater, stance -1) — The means were lawless and the transition is hollow

</details>

### A02 — bloc 1, critical (-) — 87 narratives

- **top publishers**: RT (76), TASS (EN) (75), TASS (72), CGTN (71), Global Times (71), China Daily (71), Press TV (57), Xinhua (56)
- **regions**: AMERICAS-USA (20), EUROPE-RUSSIA (7), ASIA-CHINA (7), NON-STATE-EU (6), ASIA-CAUCASUS (6), EUROPE-UKRAINE (6)
- **friction nodes**: 86 distinct — us_china_summit_diplomacy, afd_and_german_polarisation, eu_migration_burden_sharing, french_nationalist_challenge, hungary_rule_of_law, us_russia_bilateral_channel
- `meta:` _______________

<details><summary>87 narratives</summary>

- `afd_persecution_kremlin` (afd_and_german_polarisation, stance -2) — Germany persecutes its opposition and silences dissent
- `alberta_external_amplification` (alberta_separatism_us_ties, stance -2) — A fraying federation, watched from outside
- `arctic_nato_militarization` (arctic_military_presence, stance -1) — NATO is militarising the Arctic and provoking a dangerous new confrontation
- `arctic_russia_china_counter` (arctic_theater, stance -2) — NATO expansion and the US Greenland grab are the real provocation and Western hypocrisy
- `aas_contested_settlement` (armenia_azerbaijan_settlement, stance -2) — The settlement is a contested, externally shaped arrangement rather than a genuine peace
- `awp_russian_capture` (armenia_western_pivot, stance -2) — Armenia is being dragged into an anti-Russian orbit by a Western-engineered capture
- `aukus_bloc_confrontation` (aukus_alliance_reliability, stance -2) — AUKUS is bloc confrontation that spreads nuclear submarine technology and fuels an arms ra
- `trade_mutual_benefit` (australia_china_trade_leverage, stance -2) — Australia-China trade is complementary and growing, and quota mechanics are routine rather
- `australia_china_counter` (australia_theater, stance -2) — Australia is manufacturing a threat and importing a bloc confrontation it does not need
- `casp_imperial_overreach` (canada_sovereignty_pressure, stance -1) — Imperial overreach in its own hemisphere
- `cpc_russia_iran_resistance` (caucasus_power_competition, stance -2) — Outside penetration of the region is a hostile encirclement to be resisted
- `caucasus_russia_china_counter` (caucasus_theater, stance -2) — The West is destabilizing Russia's neighbourhood and dragging it into an anti-Russian orbi
- `cjer_lawful_regulation` (china_japan_economic_restrictions, stance -2) — China's export controls are lawful regulation and Japan's own conduct caused the downturn
- `china_threat_fabricated` (china_threat_assessment, stance -2) — The "China threat" is a fabricated narrative used to justify Australian alignment against 
- `colombia_theater_hegemonic_critique` (colombia_theater, stance -2) — The region as a sphere of influence
- `colombia_us_imperial_overreach` (colombia_us_alignment, stance -2) — A sovereign state treated as a subordinate
- `cuba_economic_warfare` (cuba_embargo_sanctions, stance -2) — The blockade is economic warfare against a sovereign nation
- `cuba_collapse_starvation_siege` (cuba_energy_collapse, stance -2) — Starvation by siege is a deliberate instrument of policy
- `cuba_lifelines_solidarity` (cuba_external_lifelines, stance -2) — Solidarity with a besieged island against an illegal siege
- `cuba_force_imperial_aggression` (cuba_military_coercion, stance -2) — Gunboat diplomacy against a small neighbour is imperial aggression
- `cuba_sovereign_resistance` (cuba_regime_survival, stance -2) — A sovereign people is resisting an externally engineered regime change
- `cuba_theater_anti_imperial` (cuba_theater, stance -2) — A siege to break a sovereign nation that refuses to submit
- `drc_minerals_as_resource_capture` (drc_minerals_competition, stance -2) — A takeover of an established position
- `eu_fracture_rift_exploitation` (eu_cohesion_theater, stance -2) — Brussels overreach vindicates a Europe of sovereign nations
- `migration_eu_failure_kremlin` (eu_migration_burden_sharing, stance -2) — EU migration policy is chaos and a failure of the European project
- `autonomy_multipolar_welcome` (eu_strategic_autonomy, stance -2) — European autonomy means the end of US hegemony and a welcome multipolar world
- `defence_nato_racket` (europe_us_defence_dependence, stance -2) — NATO is a crumbling Cold-War racket through which the US bleeds Europe
- `tech_digital_colonialism` (europe_us_tech_sovereignty, stance -2) — US tech dominance is a digital colonialism Europe is only now waking up to
- `europe_us_western_disunity` (europe_us_theater, stance -2) — The transatlantic split exposes Western hypocrisy and the arrival of a multipolar world
- `france_decline_kremlin` (french_nationalist_challenge, stance -2) — France's model is failing amid chaos and instability
- `ggd_sovereignty_stability` (georgia_geopolitical_drift, stance -2) — Tbilisi is resisting a Western-orchestrated colour revolution and defending its sovereignt
- `greenland_western_hypocrisy` (greenland_control, stance -2) — US imperialism over Greenland exposes Western hypocrisy and disunity
- `hungary_brussels_coercion` (hungary_rule_of_law, stance -2) — Brussels overreaches against a sovereign nation
- `memory_historical_accountability` (japan_china_memory_wars, stance -2) — Japan has never reckoned with its wartime aggression and continues to honour war criminals
- `jc_taiwan_interference_charge` (japan_china_taiwan_question, stance -2) — Japan's Taiwan remarks are interference in China's internal affairs and breach the postwar
- `jc_theater_chinese_state_counter` (japan_china_theater, stance -2) — Japan is breaking the postwar settlement and reviving militarism behind a pacifist facade
- `jde_militarism_revival` (japan_defense_expansion, stance -2) — Japan is hollowing out its pacifist constitution and reviving militarism
- `alliance_containment_instrument` (korea_peninsula_deterrence, stance -2) — Washington treats its allies as instruments for containing China
- `korea_us_containment_critique` (korea_theater, stance -2) — US alliances on the peninsula serve the containment of China
- `latam_theater_coercion_critique` (latam_hemispheric_theater, stance -2) — Washington coerces, Beijing is punished
- `port_expropriation_coercion` (latam_port_infrastructure_control, stance -2) — Expropriation under US pressure
- `mexth_anti_hegemony_rift` (mexico_theater, stance -2) — US pressure on Mexico exposes American imperialism in its own backyard
- `pacific_china_cooperation` (pacific_island_contest, stance -2) — Chinese engagement in the Pacific is ordinary development cooperation that no third party 
- `nato_complicity_provocation` (russia_airspace_incursions, stance -2) — NATO territory hosts and enables Ukrainian drone strikes; incursions are Western provocati
- `russia_europe_kremlin_counter` (russia_europe_theater, stance -2) — Western Russophobia, NATO encirclement and self-defeating sanctions manufacture a "Russia 
- `hybrid_russophobia_denial` (russia_hybrid_warfare, stance -2) — Hybrid-threat claims are evidence-free Russophobia; shadow-fleet seizures are piracy
- `nato_encirclement_provocation` (russia_nato_deterrence, stance -2) — NATO's eastern build-up is aggressive encirclement driving escalation
- `sanctions_ineffective_and_backfiring` (russia_sanctions_regime, stance -2) — Sanctions hurt Europe more than Russia; frozen-asset seizure would destroy financial trust
- `senkaku_chinese_rights_protection` (senkaku_diaoyu_islands, stance -2) — Diaoyu Dao is inherent Chinese territory and coast guard patrols are lawful rights protect
- `one_china_consensus` (taiwan_international_recognition, stance -1) — The one-China principle is settled international consensus and Taiwan's diplomacy is doome
- `pla_sovereignty_enforcement` (taiwan_military_pressure, stance -1) — Military and coast guard activity around Taiwan is routine, lawful enforcement of Chinese 
- `beijing_antiseparatism_unity` (taiwan_political_warfare, stance -1) — Opposing separatism and building cross-strait unity is legitimate, and the governing party
- `taiwan_strait_beijing_counter` (taiwan_strait_theater, stance -2) — Taiwan is Chinese territory and foreign interference, not Chinese action, is the provocati
- `taiwan_us_pawn` (taiwan_us_security_commitment, stance -2) — US arms sales violate the one-China principle and use Taiwan as a pawn Washington will dis
- `trade_western_vassalage` (transatlantic_trade, stance -2) — US tariffs expose how Washington milks its European "vassals" and the hollowness of the al
- `russian_smo_operations` (ukraine_battlefield, stance -2) — Russia-aligned: the special military operation advancing -- liberation of Donbass
- `infrastructure_war_energy_terror` (ukraine_infrastructure_war, stance -2) — Russia-aligned: Kyiv attacks civilian energy and endangers nuclear safety
- `zelensky_regime_corruption` (ukraine_official_corruption, stance -2) — Zelensky inner circle is systemically corrupt; Western aid is being stolen at scale
- `russian_maximalist_peace` (ukraine_peace_negotiations, stance -2) — Settlement must complete all SMO objectives: denazification, demilitarisation, neutrality,
- `russia_special_military_operation` (ukraine_war_theater, stance -2) — Russia's special military operation defends Russian-speaking populations from Western-back
- `uscat_external_rift` (us_canada_theater, stance -1) — The Western bloc coming apart
- `usca_bloc_fracture` (us_canada_trade_coercion, stance -1) — The Western bloc turning on itself
- `us_china_ai_suppression` (us_china_ai_primacy, stance -2) — Chinese AI succeeds on merit and Washington answers with smears and blacklists
- `us_china_minerals_lawful_leverage` (us_china_critical_minerals, stance -2) — China's minerals controls are lawful management and Western blocs undermine open trade
- `us_china_summit_multipolar_framing` (us_china_summit_diplomacy, stance -2) — Washington cannot dictate terms to Beijing
- `us_china_summit_new_chapter` (us_china_summit_diplomacy, stance -2) — Leader diplomacy opens a new chapter proving cooperation beats containment
- `us_china_tech_containment` (us_china_tech_restrictions, stance -2) — Export controls are containment dressed as security, and they are failing
- `us_china_beijing_moscow_counter` (us_china_theater, stance -2) — Containment is the anomaly: cooperation, lawful trade and a multipolar order
- `us_china_trade_unilateralism` (us_china_trade_tariffs, stance -2) — US tariffs are unilateral coercion that damages the global trading order
- `usdom_theater_decline` (us_domestic_theater, stance -2) — American decline and the collapse of its claim to model status
- `usdom_electoral_democracy_facade` (us_electoral_legitimacy, stance -2) — A system that lectures others while contesting its own elections
- `usdom_epstein_western_impunity` (us_epstein_elite_network, stance -2) — A Western elite protecting itself, exposed by its own scandal
- `usdom_loyalty_court_politics` (us_executive_loyalty, stance -2) — Court politics inside a distracted superpower
- `usdom_fed_dollar_decline` (us_fed_independence, stance -2) — Politicised money and the erosion of the dollar order
- `usdom_ice_american_repression` (us_interior_immigration_enforcement, stance -2) — A self-described democracy policing its own population
- `usdom_courts_politicised` (us_judicial_constraint, stance -2) — A judiciary treated as an instrument of factional power
- `anti_hegemony_rift` (us_mexico_military_pressure, stance -2) — US pressure on Mexico is imperial overreach in Washington's backyard
- `usdom_violence_instability` (us_political_violence, stance -2) — A superpower unable to secure its own political life
- `usdom_press_hypocrisy` (us_press_freedom, stance -2) — Press-freedom advocacy abroad, licence pressure at home
- `us_russia_washington_bad_faith` (us_russia_bilateral_channel, stance -2) — Washington talks while acting in bad faith and refusing to treat Russia as an equal
- `us_russia_theater_kremlin_grievance` (us_russia_theater, stance -2) — Washington cannot be trusted to keep its side of any bargain
- `ven_coercion_anti_imperial` (us_venezuela_relations, stance -2) — US gunboat imperialism against a sovereign nation
- `ven_transition_imperial_puppet` (venezuela_political_transition, stance -2) — The transition is a US-installed puppet regime
- `ven_oil_imperial_plunder` (venezuela_sanctions_oil, stance -2) — Washington is looting Venezuela's oil wealth
- `ven_theater_anti_imperial` (venezuela_theater, stance -2) — A US imperial operation to seize a sovereign nation's oil
- `aid_as_escalation_and_proxy` (western_aid_to_ukraine, stance -2) — Western aid prolongs proxy war, wastes taxpayer money, escalates direct NATO-Russia risk
- `zc_sovereignty_threat` (zangezur_corridor, stance -1) — The corridor is an extraterritorial threat to Armenian sovereignty and Iran's border

</details>

### A03 — bloc 0, supportive (+) — 73 narratives

- **top publishers**: Deutsche Welle (72), Associated Press (72), Reuters (72), BBC World (70), The Guardian (66), Financial Times (64), Bloomberg (63), France 24 (EN) (63)
- **regions**: AMERICAS-USA (16), EUROPE-RUSSIA (7), EUROPE-UKRAINE (6), ASIA-CAUCASUS (5), ASIA-TAIWAN (5), AMERICAS-VENEZUELA (4)
- **friction nodes**: 72 distinct — drc_peace_process, afd_and_german_polarisation, eu_budget_sovereignty, eu_cohesion_theater, eu_migration_burden_sharing, eu_right_realignment
- `meta:` _______________

<details><summary>73 narratives</summary>

- `afd_democratic_defense` (afd_and_german_polarisation, stance +2) — The AfD is a threat to the democratic order that must be contained
- `alberta_legitimate_grievance` (alberta_separatism_us_ties, stance +1) — A grievance the federation has not answered
- `arctic_nato_deterrence` (arctic_military_presence, stance +1) — NATO must reinforce the Arctic to deter a growing Russian (and Chinese) threat
- `arctic_western_security_consensus` (arctic_theater, stance +2) — The Arctic must be secured against Russian militarization and Sino-Russian encroachment
- `aas_durable_peace` (armenia_azerbaijan_settlement, stance +2) — A historic peace is ending a 30-year conflict and normalizing the region
- `awp_european_choice` (armenia_western_pivot, stance +2) — Armenia's turn to Europe is a sovereign, democratic escape from Russian domination
- `aukus_strategic_necessity` (aukus_alliance_reliability, stance +2) — AUKUS is essential to Australian deterrence and is progressing
- `trade_derisking_necessity` (australia_china_trade_leverage, stance +2) — Concentrated dependence on the Chinese market is a strategic vulnerability Australia must 
- `australia_western_consensus` (australia_theater, stance +2) — Australia must reduce its exposure to China and deepen its alliances
- `balkan_investment_development` (balkan_foreign_capital, stance +1) — Foreign investment brings jobs, tourism and international partnership to the Western Balka
- `balkan_theater_investment_opportunity` (balkan_theater, stance +1) — Foreign capital and international partnerships are framed as development opportunities gov
- `cpc_western_engagement` (caucasus_power_competition, stance +1) — Outside engagement brings beneficial partnership and integration to the region
- `caucasus_western_consensus` (caucasus_theater, stance +2) — The South Caucasus is realigning westward -- peace, connectivity and a break from Russia
- `china_threat_substantiated` (china_threat_assessment, stance +2) — Chinese espionage and military reach against Australia are real and growing
- `colombia_peace_negotiation_defense` (colombia_armed_groups_peace, stance +1) — Talks are how the war ends
- `colombia_theater_negotiated_path` (colombia_theater, stance +1) — Bargaining still works, at home and abroad
- `colombia_us_rapprochement` (colombia_us_alignment, stance +1) — The channel was repaired
- `cuba_repression_documented` (cuba_regime_survival, stance +1) — One-party rule holds by arresting those who protest
- `cuba_theater_pressure_consensus` (cuba_theater, stance +2) — The government, not the blockade, is what has to change
- `drc_accords_are_working` (drc_peace_process, stance +2) — The accords are the route out of the war
- `drc_sanctions_as_enforcement` (drc_peace_process, stance +1) — Designations as the only real leverage
- `budget_more_europe` (eu_budget_sovereignty, stance +2) — A capable Union needs stronger common financing
- `eu_cohesion_hold` (eu_cohesion_theater, stance +2) — European cohesion and the rule of law must hold against centrifugal forces
- `migration_solidarity_rights` (eu_migration_burden_sharing, stance +2) — Migration requires European solidarity and respect for rights and law
- `realignment_firewall_defense` (eu_right_realignment, stance +2) — The mainstream must not normalise the radical right
- `france_republican_defense` (french_nationalist_challenge, stance +2) — The rule of law and republican norms must apply to the RN
- `ggd_european_aspiration` (georgia_geopolitical_drift, stance +2) — Georgians want a European future their government is betraying
- `great_lakes_engagement_working` (great_lakes_theater, stance +2) — Outside engagement is starting to bite
- `hungary_eu_standards` (hungary_rule_of_law, stance +2) — Rule of law and EU standards must be upheld in Hungary
- `inter_korean_engagement` (inter_korean_relations, stance +2) — Engagement can lower tension and reopen the inter-Korean track
- `alliance_deterrence_necessary` (korea_peninsula_deterrence, stance +2) — The alliance and its exercises are what hold deterrence together
- `korea_allied_dual_track` (korea_theater, stance +2) — Hold the line, keep the door open: deterrence alongside engagement
- `latam_theater_western_terms_hold` (latam_hemispheric_theater, stance +2) — The Western offer still sets the terms
- `port_control_restored` (latam_port_infrastructure_control, stance +2) — Host-state control restored
- `cartel_offensive_progress` (mexico_cartel_war, stance +2) — The militarised offensive is working: captures and takedowns weaken the cartels
- `pacific_western_partnership` (pacific_island_contest, stance +2) — Pacific island states are choosing Australia and its partners as their security partner
- `airspace_violation_deterrence` (russia_airspace_incursions, stance +2) — Russia deliberately probes NATO airspace to intimidate; NATO must enforce, including shoot
- `russia_europe_western_resolve` (russia_europe_theater, stance +2) — Europe must deter, defend and sanction a revanchist Russia
- `hybrid_campaign_defence` (russia_hybrid_warfare, stance +2) — Russia is waging a coordinated gray-zone campaign that requires attribution and hardening
- `eastern_flank_deterrence` (russia_nato_deterrence, stance +2) — Eastern-flank build-up is necessary deterrence against a revanchist Russia
- `tighten_and_seize` (russia_sanctions_regime, stance +2) — Sanctions must be tightened, evasion closed, and frozen Russian assets seized for Ukraine
- `taiwan_international_space` (taiwan_international_recognition, stance +1) — Taiwan's international participation is legitimate and Beijing's campaign to isolate it is
- `taiwan_coercion_deterrence` (taiwan_military_pressure, stance +1) — Chinese military and coast guard pressure around Taiwan is coercion that must be deterred
- `united_front_subversion` (taiwan_political_warfare, stance +1) — Beijing's united front work, infiltration and disinformation are subverting Taiwan's democ
- `taiwan_strait_western_consensus` (taiwan_strait_theater, stance +2) — Taiwan is a democracy under escalating Chinese coercion and its deterrence must be reinfor
- `us_commitment_firm` (taiwan_us_security_commitment, stance +1) — US arms supply and the security commitment to Taiwan are holding and being strengthened
- `ukrainian_defense_and_deep_strikes` (ukraine_battlefield, stance +2) — Ukraine-aligned: defending the front, liberating territory
- `infrastructure_war_economy_strikes` (ukraine_infrastructure_war, stance +2) — Ukraine-aligned: precision degradation of Russia's war economy; Russian grid strikes are t
- `reform_in_progress` (ukraine_official_corruption, stance +1) — Ukrainian anti-corruption institutions are investigating and prosecuting successfully
- `ukrainian_maximalist_peace` (ukraine_peace_negotiations, stance +2) — Just peace requires full Russian withdrawal to 1991 borders with NATO-backed security guar
- `ukraine_resistance_solidarity` (ukraine_war_theater, stance +2) — Ukraine's war of national defense deserves full Western and democratic-world solidarity
- `uscat_provincial_grievance` (us_canada_theater, stance +1) — A federation strained from within
- `us_china_ai_lead_contest` (us_china_ai_primacy, stance +1) — Chinese AI has closed the gap and the US lead is now contested on merit and by hard tactic
- `us_china_minerals_dependence_risk` (us_china_critical_minerals, stance +1) — US dependence on Chinese rare earths is a vulnerability that must be engineered away
- `us_china_summit_engagement_works` (us_china_summit_diplomacy, stance +1) — Leader-level engagement is putting a floor under a dangerous rivalry
- `us_china_export_control_necessity` (us_china_tech_restrictions, stance +1) — Restricting advanced chip access is necessary to hold a security-critical technology lead
- `us_china_western_competition_consensus` (us_china_theater, stance +2) — Managed competition: hold the technology lead, reduce dependence, keep talking
- `us_china_tariff_leverage` (us_china_trade_tariffs, stance +1) — Tariffs and trade probes are legitimate leverage against an unbalanced relationship
- `usdom_electoral_integrity_case` (us_electoral_legitimacy, stance +1) — Tightening the rules is protecting the integrity of the vote
- `usdom_epstein_accountability` (us_epstein_elite_network, stance +1) — The files are forcing accountability on a protected elite
- `usdom_fed_orderly_succession` (us_fed_independence, stance +1) — A normal succession that leaves the institution intact
- `usdom_ice_enforcement_mandate` (us_interior_immigration_enforcement, stance +1) — Enforcement is delivering a mandate voters asked for
- `usdom_courts_checks_hold` (us_judicial_constraint, stance +1) — The courts are still binding the executive
- `usdom_violence_protective_response` (us_political_violence, stance +1) — The protective response worked and the perpetrators face the law
- `us_russia_new_treaty_needed` (us_russia_arms_control, stance +1) — The expiry of New START is dangerous and a successor framework must be built
- `us_russia_engagement_necessary` (us_russia_bilateral_channel, stance +1) — Keeping a working channel with Moscow is how wars are ended and accidents avoided
- `us_russia_relief_pragmatic` (us_russia_sanctions_leverage, stance +1) — Sanctions relief is a pragmatic response to energy-market reality
- `us_russia_theater_engagement_case` (us_russia_theater, stance +1) — Managed engagement is the responsible way to handle a nuclear-armed adversary
- `ven_coercion_justified` (us_venezuela_relations, stance +1) — The US removed a narco-dictator and a security threat
- `ven_transition_stabilization` (venezuela_political_transition, stance +1) — The interim government is stabilising Venezuela
- `ven_oil_restart_opportunity` (venezuela_sanctions_oil, stance +1) — Sanctions relief reopens Venezuela's oil to the world
- `ven_theater_western_consensus` (venezuela_theater, stance +2) — Removing Maduro opened a stabilising, pragmatic path for Venezuela
- `aid_sustains_defense` (western_aid_to_ukraine, stance +2) — Western military, economic, and industrial aid is sustaining and must be scaled

</details>

### A04 — bloc 1, supportive (+) — 23 narratives

- **top publishers**: TASS (EN) (21), RT (21), TASS (20), RIA Novosti (20), Kommersant (18), CGTN (18), China Daily (18), Global Times (16)
- **regions**: AFRICA-SAHEL (6), ASIA-NORKOREA (4), AMERICAS-USA (4), AMERICAS-BRAZIL (2), EUROPE-BALKANS (2), ASIA-SOUTHEAST (1)
- **friction nodes**: 23 distinct — north_korea_russia_alignment, us_russia_arms_control, us_russia_bilateral_channel, us_russia_sanctions_leverage, us_russia_theater, latam_hemispheric_theater
- `meta:` _______________

<details><summary>23 narratives</summary>

- `arctic_route_opportunity` (arctic_shipping_routes, stance +1) — Melting ice opens Arctic sea routes as a shared economic opportunity
- `balkan_theater_external_backing` (balkan_theater, stance +1) — Russia and China back the region's governments as they resist Western-aligned pressure
- `ven_essequibo_venezuelan_claim` (essequibo_dispute, stance +1) — Essequibo is historically Venezuelan territory
- `multipolar_systemic_alternative` (iran_theater, stance +1) — Multipolar sovereignty backing for Iran
- `korea_sanctioned_bloc` (korea_theater, stance +2) — A bloc of sanctioned states drawing closer around Pyongyang
- `latam_theater_eastern_partnership` (latam_hemispheric_theater, stance +1) — A second partner on offer
- `resource_south_south_partnership` (latam_resource_access, stance +2) — Cooperation brings development
- `myanmar_beijing_backed_normalisation` (myanmar_civil_conflict, stance +2) — Legitimate transition, backed by Beijing
- `china_dprk_friendship` (north_korea_china_patronage, stance +2) — Traditional friendship restored, to the benefit of regional stability
- `nk_sovereign_deterrent` (north_korea_missile_program, stance +2) — The arsenal is a sovereign deterrent that will not be traded away
- `dprk_russia_comradeship` (north_korea_russia_alignment, stance +2) — A lawful partnership between states under the same sanctions
- `sahel_break_with_paris_justified` (sahel_france_rupture, stance +2) — Cutting ties ends a relationship that never became equal
- `sahel_counterterror_necessity` (sahel_jihadist_insurgency, stance +2) — A legitimate war against armed extremist groups
- `sahel_sovereigntist_self_reliance` (sahel_junta_consolidation, stance +2) — Reclaiming sovereignty after decades of external tutelage
- `sahel_russian_partnership_delivers` (sahel_security_patron_contest, stance +2) — The new partnership delivers what the old one did not
- `sahel_theater_partnership_frame` (sahel_theater, stance +2) — A sovereign realignment that is finally fighting the real enemy
- `sahel_separatism_as_jihadist_alliance` (sahel_tuareg_separatism, stance +2) — The separatists are a front for the armed extremists
- `serbia_sovereignty_defense` (serbia_government_legitimacy, stance +1) — Belgrade's resistance to Western pressure defends Serbia's sovereign right to choose its o
- `scs_chinese_sovereignty_claim` (south_china_sea_claims, stance +2) — China's South China Sea claims are historic, lawful, and enforcement is defensive
- `us_russia_us_buildup_drives_race` (us_russia_arms_control, stance +2) — US missile defence and rejected proposals are what drive the new arms race
- `us_russia_washington_realism` (us_russia_bilateral_channel, stance +2) — Washington is returning to realism and accepting a multipolar order
- `us_russia_sanctions_illegitimate` (us_russia_sanctions_leverage, stance +2) — Unilateral sanctions have failed and Washington has been forced to admit it
- `us_russia_theater_kremlin_vindication` (us_russia_theater, stance +2) — The West's containment strategy has failed and Russia is being dealt with as an equal

</details>

### A05 — bloc 2, supportive (+) — 12 narratives

- **top publishers**: Daily Sabah (12), Anadolu Agency (12), TRT World (10), Al-Ahram (8), Khaleej Times (5), Egypt Today (4), Arab News (4), Reuters (4)
- **regions**: MIDEAST-TURKEY (5), MIDEAST-LEVANT (3), AFRICA-HORN (2), MIDEAST-SUDAN (1), ASIA-CAUCASUS (1)
- **friction nodes**: 12 distinct — turkey_mediator_role, turkey_theater, sudan_civil_war, horn_africa_theater, somalia_state_security, syria_kurdish_question
- `meta:` _______________

<details><summary>12 narratives</summary>

- `horn_regional_stabilisers` (horn_africa_theater, stance +1) — Regional partners rebuilding state capacity
- `somali_state_rebuilding` (somalia_state_security, stance +2) — A state rebuilding with regional partners
- `sudan_state_legitimacy` (sudan_civil_war, stance +2) — Sudan's army is the constitutional state defending against an RSF mutiny
- `damascus_territorial_reunification` (syria_kurdish_question, stance +2) — Damascus must restore central authority over all Syrian territory
- `international_engagement_pragmatic` (syria_recognition_and_normalisation, stance +2) — Arab, Western, and Russia/Ukraine engagement with Damascus is pragmatic stabilisation
- `syria_legitimate_transition` (syria_theater, stance +2) — New Syrian government is a legitimate post-Assad transition
- `turkey_anti_graft_legalism_defense` (turkey_democratic_backsliding, stance +2) — Imamoglu indictment is routine anti-corruption process
- `nato_solidarity_territorial_defense` (turkey_iran_war_spillover, stance +1) — Patriot redeployment and missile interception are legitimate alliance defence
- `pkk_terror_full_disarmament` (turkey_kurdish_question, stance +2) — PKK / YPG / SDF are one terror organisation; disarmament is the only acceptable path
- `turkey_legitimate_broker` (turkey_mediator_role, stance +2) — Erdogan's mediation across Gaza, Iran, Ukraine is indispensable
- `turkey_independent_middle_power` (turkey_theater, stance +2) — Turkey has earned regional stature through balanced diplomacy
- `zc_connectivity_prosperity` (zangezur_corridor, stance +1) — The corridor unlocks connectivity, trade and a regional peace dividend

</details>

### A06 — bloc 4, supportive (+) — 12 narratives

- **top publishers**: New York Post (12), Newsmax (12), Fox News (12), Washington Times (11), The National Interest (9), Washington Examiner (9), Breitbart (9), Daily Caller (8)
- **regions**: NON-STATE-EU (5), AMERICAS-MEXICO (3), AMERICAS-USA (3), EUROPE-GREENLAND (1)
- **friction nodes**: 12 distinct — europe_us_defence_dependence, europe_us_tech_sovereignty, europe_us_theater, eu_strategic_autonomy, transatlantic_trade, mexico_theater
- `meta:` _______________

<details><summary>12 narratives</summary>

- `autonomy_illusion` (eu_strategic_autonomy, stance +2) — European strategic autonomy is a costly fantasy that only weakens NATO
- `defence_europe_must_pay` (europe_us_defence_dependence, stance +2) — Europe has freeloaded on US protection for decades and must finally pay its share
- `tech_eu_overreach` (europe_us_tech_sovereignty, stance +2) — EU tech rules are protectionist harassment of successful American companies
- `europe_us_america_first` (europe_us_theater, stance +2) — America First: a freeloading, over-regulating Europe must pay, open up and submit
- `greenland_us_strategic_claim` (greenland_control, stance +2) — US control of Greenland is a strategic and national-security necessity
- `mexth_us_pressure_justified` (mexico_theater, stance +2) — US pressure on Mexico is justified and is producing results
- `trade_us_tariffs_justified` (transatlantic_trade, stance +2) — US tariffs are a justified correction of unfair European trade practices
- `usdom_theater_conservative_case` (us_domestic_theater, stance +1) — A mandate being executed against institutional resistance
- `usdom_loyalty_prerogative` (us_executive_loyalty, stance +1) — A president is entitled to a team that executes his agenda
- `intervention_necessity` (us_mexico_military_pressure, stance +2) — US action against the cartels is necessary because Mexico cannot or will not stop them
- `leverage_justified` (us_mexico_trade_border, stance +2) — Tariff and border pressure are legitimate leverage that forces Mexican cooperation
- `usdom_press_accountability` (us_press_freedom, stance +1) — Broadcasters are being held to obligations that come with a licence

</details>

### A07 — bloc 5, supportive (+) — 11 narratives

- **top publishers**: Fars News (11), Press TV (11), Al Mayadeen (11), IRNA (11), Tasnim News (5), Fars News Agency (5), Al Manar (5), Mehr News (5)
- **regions**: MIDEAST-IRAN (4), MIDEAST-YEMEN (4), MIDEAST-LEVANT (2), MIDEAST-GULF (1)
- **friction nodes**: 11 distinct — gulf_attacks_on_arab_states, iran_proxy_network, iran_nuclear_program, iran_theater, strait_of_hormuz_sovereignty, houthi_strikes_on_israel
- `meta:` _______________

<details><summary>11 narratives</summary>

- `iran_gulf_resistance_solidarity` (gulf_attacks_on_arab_states, stance +2) — Iran-aligned: Axis of Resistance as legitimate liberation movement
- `houthi_resistance_strikes_legitimate` (houthi_strikes_on_israel, stance +2) — Houthi missile and drone strikes on Israel are legitimate axis-of-resistance action
- `iran_nuclear_sovereign_right` (iran_nuclear_program, stance +2) — Iran: nuclear program as sovereign right and deterrence hedge
- `iran_axis_of_resistance` (iran_proxy_network, stance +2) — Iran-aligned: Axis of Resistance as legitimate liberation movement
- `iran_sovereign_existence` (iran_theater, stance +2) — Iran: Islamic Republic as sovereign state under permanent foreign assault
- `houthi_naval_pressure_legitimate` (red_sea_shipping_security, stance +2) — Houthi targeting of Israel-linked shipping is legitimate non-state pressure tied to Gaza c
- `houthi_authority_legitimate_resistance` (saudi_houthi_war, stance +2) — Houthi-led Sanaa authority is legitimate national resistance to Saudi-Western intervention
- `iran_hormuz_sovereign_pressure` (strait_of_hormuz_sovereignty, stance +1) — Iran: Hormuz as sovereign waters and deterrence asymmetry
- `foreign_military_withdrawal_demand` (syria_counter_terror, stance +1) — Foreign military presence violates sovereignty and should withdraw
- `syrian_sovereignty_under_israeli_aggression` (syria_israeli_strikes, stance +2) — Israeli strikes violate Syrian sovereignty and undermine the transition
- `houthis_fourth_front_solidarity` (yemen_red_sea_theater, stance +2) — Houthi attacks on Israel and Red Sea shipping are legitimate Gaza solidarity

</details>

### A08 — bloc 2, critical (-) — 8 narratives

- **top publishers**: Daily Sabah (8), Anadolu Agency (8), Al Jazeera (7), TRT World (7), Al-Ahram (7), Arab News (7), Al Arabiya (6), Gulf News (5)
- **regions**: MIDEAST-ISRAEL (3), AFRICA-SAHEL (2), AFRICA-HORN (1), MIDEAST-YEMEN (1), MIDEAST-SUDAN (1)
- **friction nodes**: 8 distinct — gaza_war, israel_theater, west_bank_settlements, somaliland_recognition_contest, saudi_houthi_war, sahel_jihadist_insurgency
- `meta:` _______________

<details><summary>8 narratives</summary>

- `gaza_humanitarian_catastrophe` (gaza_war, stance -2) — Pan-Arab / pro-Palestinian: Israel's Gaza campaign is humanitarian catastrophe and genocid
- `palestine_genocide_framing` (israel_theater, stance -2) — Pan-Arab / pro-Palestinian: Israel commits systemic violence against Palestinians
- `sahel_counterinsurgency_abuses` (sahel_jihadist_insurgency, stance -1) — The counterinsurgency is killing the civilians it claims to protect
- `sahel_theater_civilian_cost` (sahel_theater, stance -1) — The population pays for every side's campaign
- `saudi_coalition_legitimacy_restoration` (saudi_houthi_war, stance -2) — Saudi-led coalition is restoring the internationally-recognised Yemeni government
- `somali_territorial_integrity` (somaliland_recognition_contest, stance -2) — A violation of Somalia's territorial integrity
- `sudan_proxy_war_critique` (sudan_civil_war, stance -2) — Sudan war is sustained by UAE arms to RSF; Egypt/Saudi back the army
- `west_bank_apartheid_framing` (west_bank_settlements, stance -2) — Palestinian / international human rights: occupation, settler impunity, apartheid system

</details>

### A09 — bloc 3, critical (-) — 8 narratives

- **top publishers**: i24NEWS (8), Jerusalem Post (8), The Times of Israel (8), Times of Israel (8), Fox News (8), Arutz Sheva (7), Israel Hayom (4), Ynetnews (3)
- **regions**: MIDEAST-LEVANT (3), MIDEAST-TURKEY (3), MIDEAST-YEMEN (2)
- **friction nodes**: 8 distinct — syria_israeli_strikes, syria_recognition_and_normalisation, syria_theater, turkey_iran_war_spillover, turkey_theater, turkey_mediator_role
- `meta:` _______________

<details><summary>8 narratives</summary>

- `houthi_iranian_proxy_aggression` (houthi_strikes_on_israel, stance -2) — Houthi strikes are Iranian-orchestrated proxy aggression requiring kinetic answer
- `israeli_strikes_on_syria_legitimate` (syria_israeli_strikes, stance -1) — Israeli strikes on Syria are legitimate preventive defense
- `recognition_legitimises_jihadists` (syria_recognition_and_normalisation, stance -2) — International recognition whitewashes a former al-Qaeda operative
- `syria_jihadist_takeover_warning` (syria_theater, stance -2) — HTS rule is rebranded al-Qaeda and a long-term security threat
- `turkey_wrong_side_on_iran` (turkey_iran_war_spillover, stance -1) — Erdogan shields the Iranian regime from accountability
- `turkey_two_faced_opportunist` (turkey_mediator_role, stance -2) — Erdogan plays every side for influence without delivering
- `turkey_unreliable_ally_warning` (turkey_theater, stance -2) — Erdogan's Turkey is a hostile or unreliable NATO partner
- `iran_proxy_destabilisation` (yemen_red_sea_theater, stance -2) — Houthis are an Iranian proxy that has hijacked the Yemeni state

</details>

### A10 — bloc 3, supportive (+) — 7 narratives

- **top publishers**: i24NEWS (7), Jerusalem Post (7), Times of Israel (7), Israel Hayom (5), The Times of Israel (5), Arutz Sheva (5), Ynetnews (4), Fox News (4)
- **regions**: MIDEAST-ISRAEL (5), AFRICA-HORN (2)
- **friction nodes**: 7 distinct — gaza_war, israel_iran_strikes, israel_lebanon_border, israel_theater, west_bank_settlements, horn_africa_theater
- `meta:` _______________

<details><summary>7 narratives</summary>

- `israel_dismantle_hamas` (gaza_war, stance +2) — Israel: war is non-negotiable until Hamas is dismantled and hostages freed
- `horn_new_partnerships` (horn_africa_theater, stance +2) — New partnerships remaking the Horn
- `israel_preemptive_strike_doctrine` (israel_iran_strikes, stance +2) — Israel: preemptive and reactive strikes against an existential nuclear-bound enemy
- `israel_self_defense_north` (israel_lebanon_border, stance +2) — Israel: push Hezbollah north of the Litani; restore northern security
- `israel_existential_self_defense` (israel_theater, stance +2) — Israel: existential self-defense against multi-front Iran-led axis
- `somaliland_statehood_earned` (somaliland_recognition_contest, stance +2) — Recognition of an earned statehood
- `judea_samaria_sovereignty` (west_bank_settlements, stance +1) — Israeli right: Jewish sovereignty over biblical Judea-Samaria

</details>

### A11 — bloc 6, supportive (+) — 6 narratives

- **top publishers**: NDTV (6), Indian Express (6), The Hindu (6), Times of India (6), WION (6), Hindustan Times (6), Republic TV (6), DD India (4)
- **regions**: ASIA-INDIA (4), AMERICAS-USA (2)
- **friction nodes**: 6 distinct — india_pakistan_militancy, indus_water_sharing, kashmir_dispute, south_asia_theater, us_russia_sanctions_leverage, us_russia_theater
- `meta:` _______________

<details><summary>6 narratives</summary>

- `militancy_pakistan_sponsorship` (india_pakistan_militancy, stance +2) — Pakistan shelters and directs the groups that attack India
- `indus_treaty_obsolete` (indus_water_sharing, stance +2) — The 1960 treaty no longer fits India's needs and its terms are being revisited
- `kashmir_integral_to_india` (kashmir_dispute, stance +2) — Jammu and Kashmir is Indian territory; Pakistan must vacate what it holds
- `south_asia_indian_account` (south_asia_theater, stance +2) — India is the status-quo power defending its territory against a militancy-exporting neighb
- `us_russia_buyer_autonomy` (us_russia_sanctions_leverage, stance +1) — Sovereign buyers never accepted that US permission was required
- `us_russia_theater_buyer_autonomy` (us_russia_theater, stance +1) — Third countries treat the rivalry as something to navigate, not to join

</details>

### A12 — bloc 7, critical (-) — 6 narratives

- **top publishers**: La Nación (6), Clarín (6), O Estado de S. Paulo (5), O Globo (5), Folha de S.Paulo (5), Reforma (4), El Universal (4), El Mundo (4)
- **regions**: AMERICAS-MEXICO (3), AMERICAS-BRAZIL (2), AMERICAS-ANDEAN (1)
- **friction nodes**: 6 distinct — colombia_armed_groups_peace, mexico_theater, us_mexico_military_pressure, us_mexico_trade_border, latam_eu_market_access, latam_resource_access
- `meta:` _______________

<details><summary>6 narratives</summary>

- `colombia_peace_process_failure` (colombia_armed_groups_peace, stance -1) — Talks bought the cartels time
- `mercosur_european_obstruction` (latam_eu_market_access, stance -1) — Europe signs, then restricts
- `resource_extractivism_critique` (latam_resource_access, stance -1) — Extraction externalises its costs
- `mexth_mexican_sovereignty` (mexico_theater, stance -2) — US pressure violates Mexican sovereignty and dignity
- `mexican_sovereignty_defense` (us_mexico_military_pressure, stance -2) — US pressure violates Mexican sovereignty; non-intervention is the red line
- `trade_coercion_pushback` (us_mexico_trade_border, stance -2) — US tariff threats are economic coercion that violate USMCA and Mexican dignity

</details>

### A13 — bloc 8, supportive (+) — 6 narratives

- **top publishers**: The Economist (6), Kyodo News (6), Nikkei Asia (6), Channel NewsAsia (6), Wall Street Journal (6), The Telegraph (6), Japan Times (6), NHK World (6)
- **regions**: ASIA-CHINA (5), ASIA-JAPAN (1)
- **friction nodes**: 6 distinct — china_japan_economic_restrictions, japan_china_theater, japan_china_memory_wars, japan_china_taiwan_question, japan_defense_expansion, senkaku_diaoyu_islands
- `meta:` _______________

<details><summary>6 narratives</summary>

- `cjer_economic_coercion` (china_japan_economic_restrictions, stance +2) — China is weaponizing trade, minerals and tourism to punish Japanese political speech
- `memory_political_leverage` (japan_china_memory_wars, stance +2) — Historical grievances are raised as political leverage in a deteriorating relationship
- `jc_taiwan_japan_security_stake` (japan_china_taiwan_question, stance +2) — A Taiwan contingency directly threatens Japan's security and Japan is entitled to say so
- `jc_theater_japanese_western_consensus` (japan_china_theater, stance +2) — China's pressure on Japan is coercion that hardens Japanese resolve rather than changing i
- `jde_deterrence_response` (japan_defense_expansion, stance +2) — Japan's defense build-up is a proportionate response to China's military expansion
- `senkaku_japanese_administration` (senkaku_diaoyu_islands, stance +2) — The Senkakus are Japanese-administered territory and Chinese vessel entries are grey-zone 

</details>

### A14 — bloc 6, critical (-) — 5 narratives

- **top publishers**: NDTV (5), The Hindu (5), Times of India (5), WION (5), Hindustan Times (5), Indian Express (3), DD India (3), Republic World (3)
- **regions**: ASIA-PAKISTAN (2), EUROPE-UKRAINE (2), ASIA-INDIA (1)
- **friction nodes**: 5 distinct — balochistan_insurgency, south_asia_theater, pakistan_afghanistan_border, ukraine_peace_negotiations, ukraine_war_theater
- `meta:` _______________

<details><summary>5 narratives</summary>

- `baloch_pakistan_internal_failure` (balochistan_insurgency, stance -2) — The insurgency is Pakistan's own governance failure, not foreign subversion
- `pakafg_afghan_sovereignty_violation` (pakistan_afghanistan_border, stance -2) — Pakistani strikes on Afghan territory are aggression against a sovereign state
- `south_asia_indian_critique_of_pakistan` (south_asia_theater, stance -2) — Pakistan's conduct beyond its borders and failures within them destabilise the region
- `frontline_freeze_settlement` (ukraine_peace_negotiations, stance -1) — End the killing through frozen line of contact + Ukrainian neutrality, without endorsing R
- `proxy_war_restraint_critique` (ukraine_war_theater, stance -1) — The war is a US/NATO proxy war prolonged by Western intervention; settlement requires rest

</details>

### A15 — bloc 7, supportive (+) — 5 narratives

- **top publishers**: La Nación (5), Clarín (5), Infobae (5), O Estado de S. Paulo (3), La Tercera (3), O Globo (3), Brazil Reports (3), Folha de S.Paulo (3)
- **regions**: AMERICAS-BRAZIL (3), AMERICAS-ANDEAN (2)
- **friction nodes**: 5 distinct — colombia_theater, colombia_political_transition, latam_eu_market_access, latam_hemispheric_theater, latam_resource_access
- `meta:` _______________

<details><summary>5 narratives</summary>

- `colombia_transition_mandate` (colombia_political_transition, stance +2) — Voters chose a harder line
- `colombia_theater_hard_turn` (colombia_theater, stance +2) — The electorate chose confrontation
- `mercosur_market_opportunity` (latam_eu_market_access, stance +2) — The agreement opens a large market
- `latam_theater_regional_agency` (latam_hemispheric_theater, stance +2) — Courted by all sides, committed to none
- `resource_sovereign_development` (latam_resource_access, stance +1) — The region sets its own terms

</details>

### A16 — bloc 10, critical (-) — 5 narratives

- **top publishers**: Le Monde (5), Die Zeit (5), France 24 (EN) (5), Tagesschau (4), Süddeutsche Zeitung (4), Frankfurter Allgemeine (4), France 24 (4), EurActiv (3)
- **regions**: AMERICAS-BRAZIL (3), AFRICA-HORN (1), MIDEAST-TURKEY (1)
- **friction nodes**: 4 distinct — latam_eu_market_access, latam_hemispheric_theater, somaliland_recognition_contest, turkey_democratic_backsliding
- `meta:` _______________

<details><summary>5 narratives</summary>

- `mercosur_farm_protection` (latam_eu_market_access, stance -2) — The deal undercuts European farmers
- `mercosur_environmental_critique` (latam_eu_market_access, stance -1) — The deal rewards forest clearance
- `latam_theater_european_objection` (latam_hemispheric_theater, stance -2) — Europe resists its own agreement
- `somaliland_transactional_scramble` (somaliland_recognition_contest, stance -1) — Statehood traded for bases and minerals
- `turkey_authoritarian_drift_critique` (turkey_democratic_backsliding, stance -2) — Imamoglu trial and CHP crackdown dismantle Turkish democracy

</details>

### A17 — bloc 11, critical (-) — 5 narratives

- **top publishers**: New York Post (5), The New York Times (5), Times of Israel (5), Haaretz (5), WSJ (5), The Washington Post (5), Washington Post (5), New York Times (5)
- **regions**: MIDEAST-IRAN (4), MIDEAST-GULF (1)
- **friction nodes**: 5 distinct — gulf_attacks_on_arab_states, iran_proxy_network, iran_theater, strait_of_hormuz_sovereignty, iran_nuclear_program
- `meta:` _______________

<details><summary>5 narratives</summary>

- `west_gulf_aggression_response` (gulf_attacks_on_arab_states, stance -2) — US-Israel-Saudi-UAE: Iranian and Houthi strikes are state-sponsored aggression
- `west_iran_nuclear_threat` (iran_nuclear_program, stance -2) — Western coalition: Iran nuclear as existential threat
- `west_iran_proxy_network_threat` (iran_proxy_network, stance -2) — Western coalition: Iran proxy network as terror infrastructure
- `west_iran_regime_change_doctrine` (iran_theater, stance -2) — Western coalition: the Iranian regime is illegitimate and replaceable
- `west_hormuz_freedom_of_navigation` (strait_of_hormuz_sovereignty, stance -1) — Western coalition: free passage through Hormuz is non-negotiable

</details>

### A18 — bloc 0, neutral (0) — 4 narratives

- **top publishers**: BBC World (4), Deutsche Welle (4), Associated Press (4), Reuters (4), France 24 (EN) (4), The Guardian (3), Euronews (2), France 24 (2)
- **regions**: MIDEAST-ISRAEL (1), EUROPE-GREENLAND (1), MIDEAST-LEVANT (1), MIDEAST-YEMEN (1)
- **friction nodes**: 4 distinct — israel_theater, greenland_control, syria_counter_terror, yemen_red_sea_theater
- `meta:` _______________

<details><summary>4 narratives</summary>

- `greenland_self_determination` (greenland_control, stance +0) — Greenland's future is for Greenlanders to decide -- not Washington or Copenhagen
- `eu_two_state_pathway` (israel_theater, stance +0) — EU/E3 two-state framework: condemn excesses on both sides, preserve the negotiated horizon
- `coalition_counter_isis_necessary` (syria_counter_terror, stance +0) — Coalition counter-ISIS operations are necessary until ISIS threat is contained
- `western_pragmatic_navigation` (yemen_red_sea_theater, stance +0) — Houthi problem is a freedom-of-navigation problem; Gaza ceasefire removes the casus belli

</details>

### A19 — bloc 9, critical (-) — 4 narratives

- **top publishers**: The Express Tribune (4), The Nation (4), The News International (4), Dawn (4), Express Tribune (4), TRT World (2), Anadolu Agency (2), Arab News (2)
- **regions**: ASIA-INDIA (4)
- **friction nodes**: 4 distinct — india_pakistan_militancy, south_asia_theater, indus_water_sharing, kashmir_dispute
- `meta:` _______________

<details><summary>4 narratives</summary>

- `militancy_indian_pretext` (india_pakistan_militancy, stance -2) — India weaponises unproven allegations to justify pressure and strikes
- `indus_water_weaponisation` (indus_water_sharing, stance -2) — Suspending the treaty is coercion against a downstream population
- `kashmir_disputed_territory` (kashmir_dispute, stance -2) — Kashmir's status is unresolved and its people are owed self-determination
- `south_asia_pakistani_grievance` (south_asia_theater, stance -2) — India is the coercive party: occupier, water aggressor and fabricator of charges

</details>

### A20 — bloc 12, critical (-) — 4 narratives

- **top publishers**: Süddeutsche Zeitung (4), The Independent (4), Al Jazeera (4), Frankfurter Allgemeine (4), Le Monde (4), La Repubblica (4), Die Zeit (4), El País (4)
- **regions**: EUROPE-RUSSIA (4)
- **friction nodes**: 4 distinct — russia_airspace_incursions, russia_europe_theater, russia_hybrid_warfare, russia_nato_deterrence
- `meta:` _______________

<details><summary>4 narratives</summary>

- `escalation_risk_restraint` (russia_airspace_incursions, stance -1) — Shoot-down authority and forward posture risk uncontrolled escalation; many incidents are 
- `russia_europe_critical_restraint` (russia_europe_theater, stance -1) — Threat inflation, militarisation and escalation risk: a skeptical European counter-current
- `securitisation_caution` (russia_hybrid_warfare, stance -1) — Caution against over-attribution: accidents and criminality get mislabeled as Kremlin sabo
- `militarisation_overreach` (russia_nato_deterrence, stance -1) — Threat inflation and war-economy drift are a costly overreach

</details>

### A21 — bloc 5, critical (-) — 3 narratives

- **top publishers**: Fars News (3), Press TV (3), TRT World (3), Anadolu Agency (3), Al Mayadeen (3), IRNA (3), CGTN (2), TASS (EN) (2)
- **regions**: MIDEAST-ISRAEL (3)
- **friction nodes**: 3 distinct — israel_iran_strikes, israel_lebanon_border, israel_theater
- `meta:` _______________

<details><summary>3 narratives</summary>

- `iran_legitimate_retaliation_doctrine` (israel_iran_strikes, stance -2) — Iran-aligned: Iranian retaliation is legitimate state self-defense under the UN Charter
- `hezbollah_resistance_north` (israel_lebanon_border, stance -2) — Hezbollah and aligned: northern front as legitimate solidarity resistance
- `multipolar_anti_israel_alignment` (israel_theater, stance -1) — Russia / China / Global South: Israel as US-backed colonial outlier

</details>

### A22 — bloc 9, supportive (+) — 3 narratives

- **top publishers**: The Express Tribune (3), The Nation (3), The News International (3), Dawn (3), Express Tribune (3)
- **regions**: ASIA-PAKISTAN (2), ASIA-INDIA (1)
- **friction nodes**: 3 distinct — balochistan_insurgency, pakistan_afghanistan_border, south_asia_theater
- `meta:` _______________

<details><summary>3 narratives</summary>

- `baloch_foreign_backed_insurgency` (balochistan_insurgency, stance +2) — The attacks are externally sponsored terrorism, not a domestic grievance
- `pakafg_counterterror_necessity` (pakistan_afghanistan_border, stance +2) — Strikes target militant sanctuaries Kabul refuses to close
- `south_asia_pakistani_security_account` (south_asia_theater, stance +1) — Pakistan is fighting militancy on two fronts against externally backed enemies

</details>

### A23 — bloc 13, critical (-) — 3 narratives

- **top publishers**: OKdiario (3), Brussels Signal (3), La Verità (3), Valeurs Actuelles (3), Causeur (3), Libertad Digital (3), NIUS (3), Tichys Einblick (3)
- **regions**: EUROPE-GERMANY (1), NON-STATE-EU (1), EUROPE-FRANCE (1)
- **friction nodes**: 3 distinct — afd_and_german_polarisation, eu_right_realignment, french_nationalist_challenge
- `meta:` _______________

<details><summary>3 narratives</summary>

- `afd_exclusion_undemocratic` (afd_and_german_polarisation, stance -1) — Excluding a party millions vote for is itself undemocratic
- `realignment_new_majority` (eu_right_realignment, stance -1) — The right has a democratic mandate to govern and to cooperate
- `france_popular_will` (french_nationalist_challenge, stance -1) — The establishment and the courts are blocking the popular will

</details>

### A24 — bloc 4, critical (-) — 2 narratives

- **top publishers**: Atlantic Council (2), The Federalist (2), Washington Times (2), New York Post (2), The National Interest (2), National Review (2), Washington Examiner (2), Breitbart (2)
- **regions**: AMERICAS-BRAZIL (2)
- **friction nodes**: 2 distinct — latam_hemispheric_theater, latam_resource_access
- `meta:` _______________

<details><summary>2 narratives</summary>

- `latam_theater_strategic_warning` (latam_hemispheric_theater, stance -2) — Commerce with a strategic tail
- `resource_strategic_penetration` (latam_resource_access, stance -2) — Beijing is buying strategic depth

</details>

### A25 — bloc 8, critical (-) — 2 narratives

- **top publishers**: Kyodo News (2), BBC World (2), Bangkok Post (2), Nikkei Asia (2), Channel NewsAsia (2), Associated Press (2), The Telegraph (2), Japan Times (2)
- **regions**: ASIA-SOUTHEAST (1), ASIA-CHINA (1)
- **friction nodes**: 2 distinct — myanmar_civil_conflict, south_china_sea_claims
- `meta:` _______________

<details><summary>2 narratives</summary>

- `myanmar_criminal_economy_spillover` (myanmar_civil_conflict, stance -1) — Scam-compound economy and cross-border crime
- `scs_rules_based_maritime_order` (south_china_sea_claims, stance -2) — China's claims lack legal basis and its conduct coerces smaller claimants

</details>

### A26 — bloc 14, supportive (+) — 2 narratives

- **top publishers**: OilPrice (2), Financial Times (2), Bloomberg (2), TASS (EN) (1), RT (1), CNBC (1), RIA Novosti (1), Wall Street Journal (1)
- **regions**: EUROPE-RUSSIA (1), AFRICA-DRC (1)
- **friction nodes**: 2 distinct — arctic_resources_competition, drc_minerals_competition
- `meta:` _______________

<details><summary>2 narratives</summary>

- `arctic_resource_development` (arctic_resources_competition, stance +1) — Arctic energy and minerals are a legitimate sovereign development opportunity
- `drc_minerals_as_development` (drc_minerals_competition, stance +2) — Capital arriving at last

</details>

### A27 — bloc 15, critical (-) — 2 narratives

- **top publishers**: News24 (2), Mail & Guardian (2), Al-Ahram (2), The Standard (2), Daily Sabah (1), TASS (EN) (1), RT (1), TRT World (1)
- **regions**: AFRICA-DRC (2)
- **friction nodes**: 2 distinct — drc_peace_process, great_lakes_theater
- `meta:` _______________

<details><summary>2 narratives</summary>

- `drc_sanctions_rejected` (drc_peace_process, stance -2) — The designated parties reject the designations
- `great_lakes_scepticism_of_outside_fixes` (great_lakes_theater, stance -1) — African scepticism about externally designed fixes

</details>

### A28 — bloc 16, critical (-) — 2 narratives

- **top publishers**: Sputnik (2), TASS (EN) (2), RT (2), Press TV (2)
- **regions**: AFRICA-HORN (2)
- **friction nodes**: 2 distinct — horn_africa_theater, somalia_state_security
- `meta:` _______________

<details><summary>2 narratives</summary>

- `horn_russian_iranian_counter` (horn_africa_theater, stance -2) — Russian and Iranian counter-framing
- `somali_foreign_militarisation_critique` (somalia_state_security, stance -2) — Foreign militarisation is the destabiliser

</details>

### A29 — bloc 1, neutral (0) — 1 narratives

- **top publishers**: People's Daily (1), CGTN (1), Global Times (1), China Daily (1), Xinhua (1)
- **regions**: ASIA-SOUTHEAST (1)
- **friction nodes**: 1 distinct — thailand_cambodia_border
- `meta:` _______________

<details><summary>1 narratives</summary>

- `thaicam_great_power_mediation` (thailand_cambodia_border, stance +0) — Outside powers and ASEAN broker the ceasefire and urge both sides to de-escalate

</details>

### A30 — bloc 10, neutral (0) — 1 narratives

- **top publishers**: Reuters (1), Tagesschau (1), Süddeutsche Zeitung (1), BBC World (1), Der Standard (1), Euronews (1), Die Presse (1), Frankfurter Allgemeine (1)
- **regions**: MIDEAST-TURKEY (1)
- **friction nodes**: 1 distinct — turkey_theater
- `meta:` _______________

<details><summary>1 narratives</summary>

- `turkey_eu_engagement_pragmatic` (turkey_theater, stance +0) — Engage Turkey on shared interests while flagging democratic concerns

</details>

### A31 — bloc 14, critical (-) — 1 narratives

- **top publishers**: S&P Global (1), Reuters (1), The Economist (1), OilPrice (1), Financial Times (1), Mining.com (1), Bloomberg (1), Wall Street Journal (1)
- **regions**: AMERICAS-MEXICO (1)
- **friction nodes**: 1 distinct — us_mexico_trade_border
- `meta:` _______________

<details><summary>1 narratives</summary>

- `trade_economic_disruption` (us_mexico_trade_border, stance -1) — Tariff brinkmanship disrupts an integrated economy and rattles markets

</details>

### A32 — bloc 15, supportive (+) — 1 narratives

- **top publishers**: News24 (1), Mail & Guardian (1), Daily Nation (1), RT (1), TASS (EN) (1), Al-Ahram (1), Anadolu Agency (1), The Standard (1)
- **regions**: AFRICA-DRC (1)
- **friction nodes**: 1 distinct — m23_conflict
- `meta:` _______________

<details><summary>1 narratives</summary>

- `m23_backing_charge_rejected` (m23_conflict, stance +1) — The accused parties reject the charge

</details>

### A33 — bloc 17, critical (-) — 1 narratives

- **top publishers**: The National (1), Al-Ahram (1), Egypt Today (1)
- **regions**: AFRICA-HORN (1)
- **friction nodes**: 1 distinct — ethiopia_regional_confrontation
- `meta:` _______________

<details><summary>1 narratives</summary>

- `ethiopia_regional_revisionism` (ethiopia_regional_confrontation, stance -2) — A revisionist power destabilising the region

</details>

### A34 — bloc 18, critical (-) — 1 narratives

- **top publishers**: The National (1), Al Jazeera (1), Al Arabiya (1), Arab News (1), Dawn (1)
- **regions**: AFRICA-HORN (1)
- **friction nodes**: 1 distinct — horn_africa_theater
- `meta:` _______________

<details><summary>1 narratives</summary>

- `horn_sovereignty_bloc` (horn_africa_theater, stance -2) — Sovereignty and non-interference

</details>

### A35 — bloc 19, neutral (0) — 1 narratives

- **top publishers**: BBC World (1), RFI (1), Handelsblatt (1), Corriere della Sera (1), Spiegel (1), La Vanguardia (1), Deutsche Welle (1), El Mundo (1)
- **regions**: MIDEAST-IRAN (1)
- **friction nodes**: 1 distinct — iran_theater
- `meta:` _______________

<details><summary>1 narratives</summary>

- `eu_diplomatic_preservation_norm` (iran_theater, stance +0) — EU/E3 diplomatic engagement on Iran

</details>

### A36 — bloc 20, supportive (+) — 1 narratives

- **top publishers**: Vanguard (1), Premium Times Nigeria (1), Punch (1), The Nation Newspaper (1), Vanguard News (1), Punch Newspapers (1)
- **regions**: AFRICA-SAHEL (1)
- **friction nodes**: 1 distinct — sahel_theater
- `meta:` _______________

<details><summary>1 narratives</summary>

- `sahel_theater_regional_security_response` (sahel_theater, stance +1) — A regional security emergency being fought by national armies

</details>

### A37 — bloc 21, critical (-) — 1 narratives

- **top publishers**: Daily Sabah (1), Vijesti (1), Reuters (1), N1 (1), Tagesschau (1), Jerusalem Post (1), N1 Serbia (1), Novinite (1)
- **regions**: EUROPE-BALKANS (1)
- **friction nodes**: 1 distinct — serbia_government_legitimacy
- `meta:` _______________

<details><summary>1 narratives</summary>

- `serbia_protest_accountability` (serbia_government_legitimacy, stance -2) — Systemic corruption and negligence behind the Novi Sad canopy collapse demand Vucic's resi

</details>

### A38 — bloc 22, supportive (+) — 1 narratives

- **top publishers**: The Nation Thailand (1), Thai PBS (1), Bangkok Post (1), Thai PBS World (1)
- **regions**: ASIA-SOUTHEAST (1)
- **friction nodes**: 1 distinct — thailand_cambodia_border
- `meta:` _______________

<details><summary>1 narratives</summary>

- `thaicam_thai_sovereignty_defence` (thailand_cambodia_border, stance +2) — The border and Koh Kood are Thai territory; Cambodia breaches the memoranda and provokes

</details>

### A39 — bloc 23, critical (-) — 1 narratives

- **top publishers**: Khaleej Times (1), Reuters (1), Straits Times (1), Al Jazeera (1), Philippine Daily Inquirer (1), France 24 (EN) (1), Channel NewsAsia (1), Associated Press (1)
- **regions**: ASIA-SOUTHEAST (1)
- **friction nodes**: 1 distinct — thailand_cambodia_border
- `meta:` _______________

<details><summary>1 narratives</summary>

- `thaicam_cambodian_territorial_claim` (thailand_cambodia_border, stance -2) — Thailand occupies Cambodian ground; the ICJ ruling and demarcation favour Cambodia

</details>

---

## Unclustered — fewer than 3 publishers (3)

These need individual assignment, or are candidates for the thin-narrative triage in P0(c).

- `casp_continental_dependence` (canada_sovereignty_pressure, stance +2, 1 pubs) — Canada depends on American protection
- `uscat_us_leverage_case` (us_canada_theater, stance +2, 1 pubs) — A relationship being put on fairer terms
- `usca_trade_rebalancing` (us_canada_trade_coercion, stance +2, 1 pubs) — Rebalancing an unfair trading relationship

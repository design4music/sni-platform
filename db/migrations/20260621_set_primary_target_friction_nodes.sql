-- Set primary_target for all friction nodes (30 theaters + 110 atomics)
-- 2026-06-21

BEGIN;

-- MIDDLE EAST THEATERS (6)
UPDATE friction_nodes SET primary_target = 'MIDEAST-IRAN' WHERE id = 'iran_theater';
UPDATE friction_nodes SET primary_target = 'MIDEAST-ISRAEL' WHERE id = 'israel_theater';
UPDATE friction_nodes SET primary_target = 'MIDEAST-LEVANT' WHERE id = 'syria_theater';
UPDATE friction_nodes SET primary_target = 'MIDEAST-TURKEY' WHERE id = 'turkey_theater';
UPDATE friction_nodes SET primary_target = 'MIDEAST-YEMEN' WHERE id = 'yemen_red_sea_theater';

-- EUROPE THEATERS (7)
UPDATE friction_nodes SET primary_target = 'EUROPE-UKRAINE' WHERE id = 'ukraine_war_theater';
UPDATE friction_nodes SET primary_target = 'EUROPE-RUSSIA' WHERE id = 'russia_europe_theater';
UPDATE friction_nodes SET primary_target = 'EUROPE-EU' WHERE id = 'europe_us_theater';
UPDATE friction_nodes SET primary_target = 'NON-STATE-EU' WHERE id = 'eu_cohesion_theater';
UPDATE friction_nodes SET primary_target = 'EUROPE-EU' WHERE id = 'europe_sovereignty_theater';
UPDATE friction_nodes SET primary_target = 'EUROPE-BALKANS' WHERE id = 'balkan_theater';
UPDATE friction_nodes SET primary_target = 'EUROPE-ARMENIA' WHERE id = 'caucasus_theater';

-- ASIA-PACIFIC THEATERS (8)
UPDATE friction_nodes SET primary_target = 'OCEANIA-AUSTRALIA' WHERE id = 'australia_china_theater';
UPDATE friction_nodes SET primary_target = 'ASIA-TAIWAN' WHERE id = 'taiwan_strait_theater';
UPDATE friction_nodes SET primary_target = 'ASIA-SOUTHEAST' WHERE id = 'scs_theater';
UPDATE friction_nodes SET primary_target = 'ASIA-NORKOREA' WHERE id = 'korea_theater';
UPDATE friction_nodes SET primary_target = 'ASIA-INDIA' WHERE id = 'india_pakistan_theater';
UPDATE friction_nodes SET primary_target = 'ASIA-INDIA' WHERE id = 'india_china_theater';
UPDATE friction_nodes SET primary_target = 'ASIA-JAPAN' WHERE id = 'japan_china_theater';
UPDATE friction_nodes SET primary_target = 'ASIA-SOUTHEAST' WHERE id = 'myanmar_theater';

-- AFRICA THEATERS (3)
UPDATE friction_nodes SET primary_target = 'AFRICA-ETHIOPIA' WHERE id = 'horn_africa_theater';
UPDATE friction_nodes SET primary_target = 'AFRICA-SAHEL' WHERE id = 'sahel_theater';
UPDATE friction_nodes SET primary_target = 'AFRICA-DRC' WHERE id = 'great_lakes_theater';

-- AMERICAS THEATERS (4)
UPDATE friction_nodes SET primary_target = 'AMERICAS-USA' WHERE id = 'us_domestic_theater';
UPDATE friction_nodes SET primary_target = 'AMERICAS-USA' WHERE id = 'us_china_theater';
UPDATE friction_nodes SET primary_target = 'AMERICAS-USA' WHERE id = 'us_russia_theater';
UPDATE friction_nodes SET primary_target = 'AMERICAS-VENEZUELA' WHERE id = 'latam_theater';

-- ARCTIC THEATER (1)
UPDATE friction_nodes SET primary_target = 'EUROPE-RUSSIA' WHERE id = 'arctic_theater';

-- ATOMIC FNs: Inherit primary_target from their parent theater
-- MIDDLE EAST ATOMICS
UPDATE friction_nodes SET primary_target = 'MIDEAST-IRAN' WHERE id IN (
  'iran_nuclear_program', 'iran_proxy_network', 'strait_of_hormuz_sovereignty', 'gulf_attacks_on_arab_states'
);
UPDATE friction_nodes SET primary_target = 'MIDEAST-ISRAEL' WHERE id IN (
  'gaza_war', 'israel_lebanon_border', 'israel_iran_strikes', 'west_bank_settlements'
);
UPDATE friction_nodes SET primary_target = 'MIDEAST-LEVANT' WHERE id IN (
  'syria_kurdish_question', 'syria_israeli_strikes', 'syria_counter_terror', 'syria_recognition_and_normalisation'
);
UPDATE friction_nodes SET primary_target = 'MIDEAST-TURKEY' WHERE id IN (
  'turkey_kurdish_question', 'turkey_iran_war_spillover', 'turkey_mediator_role', 'turkey_democratic_backsliding'
);
UPDATE friction_nodes SET primary_target = 'MIDEAST-YEMEN' WHERE id IN (
  'red_sea_shipping_security', 'houthi_strikes_on_israel', 'saudi_houthi_war'
);

-- EUROPE ATOMICS
UPDATE friction_nodes SET primary_target = 'EUROPE-UKRAINE' WHERE id IN (
  'ukraine_battlefield', 'western_aid_to_ukraine', 'ukraine_peace_negotiations', 'ukraine_official_corruption'
);
UPDATE friction_nodes SET primary_target = 'EUROPE-RUSSIA' WHERE id IN (
  'nato_deterrence', 'sanctions_and_economy', 'baltic_security', 'energy_security_leverage'
);
UPDATE friction_nodes SET primary_target = 'EUROPE-EU' WHERE id IN (
  'greenland_sovereignty', 'transatlantic_trade', 'strategic_autonomy', 'defence_dependence'
);
UPDATE friction_nodes SET primary_target = 'NON-STATE-EU' WHERE id IN (
  'hungary_rule_of_law', 'slovakia_alignment', 'migration_burden_sharing', 'budget_and_sovereignty'
);
UPDATE friction_nodes SET primary_target = 'EUROPE-EU' WHERE id IN (
  'afd_and_german_polarisation', 'french_nationalist_challenge', 'post_brexit_realignment', 'italian_populist_government'
);
UPDATE friction_nodes SET primary_target = 'EUROPE-BALKANS' WHERE id IN (
  'serbia_kosovo_tensions', 'bosnia_fragmentation'
);
UPDATE friction_nodes SET primary_target = 'EUROPE-ARMENIA' WHERE id IN (
  'armenia_azerbaijan_settlement', 'nagorno_karabakh_aftermath', 'zangezur_corridor', 'regional_power_competition'
);

-- ASIA-PACIFIC ATOMICS
UPDATE friction_nodes SET primary_target = 'OCEANIA-AUSTRALIA' WHERE id IN (
  'security_alignment', 'economic_coercion', 'pacific_island_alignment'
);
UPDATE friction_nodes SET primary_target = 'ASIA-TAIWAN' WHERE id IN (
  'taiwan_sovereignty', 'taiwan_military_pressure', 'taiwan_semiconductor_dependence', 'taiwan_international_recognition'
);
UPDATE friction_nodes SET primary_target = 'ASIA-SOUTHEAST' WHERE id IN (
  'south_china_sea_claims', 'freedom_of_navigation', 'reef_militarisation', 'fisheries_conflict'
);
UPDATE friction_nodes SET primary_target = 'ASIA-NORKOREA' WHERE id IN (
  'north_korea_missile_program', 'peninsula_deterrence', 'north_korea_international_pressure',
  'reunification_and_identity', 'north_korea_china_leverage'
);
UPDATE friction_nodes SET primary_target = 'ASIA-INDIA' WHERE id IN (
  'kashmir_dispute', 'cross_border_militancy', 'nuclear_deterrence_balance', 'water_sharing_indus'
);
UPDATE friction_nodes SET primary_target = 'ASIA-INDIA' WHERE id IN (
  'ladakh_lac_dispute', 'himalayan_strategic_competition'
);
UPDATE friction_nodes SET primary_target = 'ASIA-JAPAN' WHERE id IN (
  'senkaku_diaoyu_islands', 'east_china_sea_claims', 'historical_memory_conflicts'
);
UPDATE friction_nodes SET primary_target = 'ASIA-SOUTHEAST' WHERE id IN (
  'myanmar_military_rule', 'ethnic_armed_conflicts', 'china_border_influence'
);

-- AFRICA ATOMICS
UPDATE friction_nodes SET primary_target = 'AFRICA-ETHIOPIA' WHERE id IN (
  'ethiopia_tigray_aftermath', 'ethiopia_amhara_conflict', 'somalia_al_shabaab', 'ethiopia_somaliland_access'
);
UPDATE friction_nodes SET primary_target = 'AFRICA-SAHEL' WHERE id IN (
  'sahel_jihadist_insurgency', 'french_withdrawal_legacy', 'russian_security_presence', 'regional_regime_consolidation'
);
UPDATE friction_nodes SET primary_target = 'AFRICA-DRC' WHERE id IN (
  'eastern_congo_armed_groups', 'm23_conflict', 'critical_minerals_competition', 'regional_intervention_forces'
);

-- AMERICAS ATOMICS
UPDATE friction_nodes SET primary_target = 'AMERICAS-USA' WHERE id IN (
  'us_electoral_legitimacy', 'federal_state_authority', 'immigration_border_politics', 'culture_war_conflicts'
);
UPDATE friction_nodes SET primary_target = 'AMERICAS-USA' WHERE id IN (
  'technology_restrictions', 'trade_and_tariffs', 'investment_screening', 'strategic_supply_chains'
);
UPDATE friction_nodes SET primary_target = 'AMERICAS-USA' WHERE id IN (
  'nuclear_arms_control', 'election_interference', 'arctic_competition', 'ukraine_proxy_war'
);
UPDATE friction_nodes SET primary_target = 'AMERICAS-VENEZUELA' WHERE id IN (
  'venezuela_political_transition', 'us_venezuela_relations', 'sanctions_and_oil', 'essequibo_dispute',
  'embargo_and_sanctions', 'migration_pressures', 'regime_survival', 'infrastructure_influence',
  'trade_dependence', 'strategic_resources'
);

-- ARCTIC ATOMICS
UPDATE friction_nodes SET primary_target = 'EUROPE-RUSSIA' WHERE id IN (
  'shipping_routes', 'greenland_control', 'military_presence', 'critical_resources'
);

COMMIT;

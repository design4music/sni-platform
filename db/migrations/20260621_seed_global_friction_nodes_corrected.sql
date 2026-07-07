-- Seed global friction nodes: 30 theaters + 110 atomic FNs
-- Corrected mapping to use existing 114 centroids (no ASIA-PACIFIC-*, LATAM-*)
-- 2026-06-21
--
-- SAFETY PATCH 2026-07-07: the original blanket DELETE below cascaded
-- (event_friction_nodes.fn_id has ON DELETE CASCADE) and silently wiped
-- 15,945 real production event-linkage rows when this file was replayed
-- against a database with live data -- no error, no warning. Recovered
-- from a fresh dump; see docs/context/DB_SAFETY_INCIDENT_20260707.md.
-- Patched to never delete a row that has real children (event links or
-- narratives). This migration is idempotent-safe to re-run now; it was
-- NOT before this patch. Still run only via scripts/safe_db_migrate.py.

DELETE FROM friction_nodes
WHERE (is_active = true OR fn_type = 'theater' OR fn_type = 'atomic')
  AND id NOT IN (SELECT DISTINCT fn_id FROM event_friction_nodes)
  AND id NOT IN (SELECT DISTINCT fn_id FROM narratives_v2 WHERE fn_id IS NOT NULL);

INSERT INTO friction_nodes (id, name_en, fn_type, centroid_ids, member_fn_ids, display_order, is_active) VALUES

-- MIDDLE EAST (6 theaters, 20 atomic FNs)
('iran_theater', 'Iran in regional and international confrontation', 'theater', ARRAY['MIDEAST-IRAN'], ARRAY['iran_nuclear_program','iran_proxy_network','strait_of_hormuz_sovereignty','gulf_attacks_on_arab_states'], 1, true),
('israel_theater', 'Israel in regional confrontation', 'theater', ARRAY['MIDEAST-ISRAEL','MIDEAST-PALESTINE','MIDEAST-LEVANT'], ARRAY['gaza_war','israel_lebanon_border','israel_iran_strikes','west_bank_settlements'], 2, true),
('syria_theater', 'Syria in post-Assad transition', 'theater', ARRAY['MIDEAST-LEVANT','MIDEAST-TURKEY','MIDEAST-IRAN','MIDEAST-ISRAEL','MIDEAST-GULF','MIDEAST-SAUDI','MIDEAST-IRAQ','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-UK','EUROPE-FRANCE','EUROPE-GERMANY','EUROPE-RUSSIA','EUROPE-UKRAINE','NON-STATE-EU'], ARRAY['syria_kurdish_question','syria_israeli_strikes','syria_counter_terror','syria_recognition_and_normalisation'], 3, true),
('turkey_theater', 'Turkey as contested regional power', 'theater', ARRAY['MIDEAST-TURKEY','MIDEAST-LEVANT','MIDEAST-IRAN','MIDEAST-ISRAEL','MIDEAST-GULF','MIDEAST-SAUDI','MIDEAST-IRAQ','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-RUSSIA','EUROPE-UKRAINE','EUROPE-GERMANY','EUROPE-SOUTH','NON-STATE-EU','NON-STATE-NATO'], ARRAY['turkey_kurdish_question','turkey_iran_war_spillover','turkey_mediator_role','turkey_democratic_backsliding'], 4, true),
('yemen_red_sea_theater', 'Yemen and the Red Sea front', 'theater', ARRAY['MIDEAST-YEMEN','MIDEAST-SAUDI','MIDEAST-GULF','MIDEAST-EGYPT','MIDEAST-IRAN','MIDEAST-ISRAEL','AMERICAS-USA','EUROPE-UK'], ARRAY['red_sea_shipping_security','houthi_strikes_on_israel','saudi_houthi_war'], 5, true),

-- EUROPE (7 theaters, 24 atomic FNs)
('ukraine_war_theater', 'Ukraine war theater', 'theater', ARRAY['EUROPE-UKRAINE','EUROPE-RUSSIA','AMERICAS-USA','EUROPE-BALTIC'], ARRAY['ukraine_battlefield','western_aid_to_ukraine','ukraine_peace_negotiations','ukraine_official_corruption'], 6, true),
('russia_europe_theater', 'Russia-Europe confrontation', 'theater', ARRAY['EUROPE-RUSSIA','EUROPE-EU','EUROPE-BALTIC','AMERICAS-USA'], ARRAY['nato_deterrence','sanctions_and_economy','baltic_security','energy_security_leverage'], 7, true),
('europe_us_theater', 'Europe-US strategic tensions', 'theater', ARRAY['EUROPE-EU','AMERICAS-USA','ASIA-CHINA','EUROPE-GREENLAND'], ARRAY['greenland_sovereignty','transatlantic_trade','strategic_autonomy','defence_dependence'], 8, true),
('eu_cohesion_theater', 'EU internal cohesion', 'theater', ARRAY['EUROPE-EU','EUROPE-HUNGARY','EUROPE-SLOVAKIA','EUROPE-VISEGRAD'], ARRAY['hungary_rule_of_law','slovakia_alignment','migration_burden_sharing','budget_and_sovereignty'], 9, true),
('europe_sovereignty_theater', 'European sovereignty movements', 'theater', ARRAY['EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-EU'], ARRAY['afd_and_german_polarisation','french_nationalist_challenge','post_brexit_realignment','italian_populist_government'], 10, true),
('balkan_theater', 'Balkan instability', 'theater', ARRAY['EUROPE-BALKANS'], ARRAY['serbia_kosovo_tensions','bosnia_fragmentation'], 11, true),
('caucasus_theater', 'South Caucasus realignment', 'theater', ARRAY['EUROPE-ARMENIA','EUROPE-AZERBAIJAN','EUROPE-RUSSIA','MIDEAST-TURKEY','MIDEAST-IRAN','AMERICAS-USA','NON-STATE-EU'], ARRAY['armenia_azerbaijan_settlement','nagorno_karabakh_aftermath','zangezur_corridor','regional_power_competition'], 12, true),

-- ASIA-PACIFIC (8 theaters, 29 atomic FNs)
('australia_china_theater', 'Australia-China strategic rivalry', 'theater', ARRAY['OCEANIA-AUSTRALIA','ASIA-CHINA','AMERICAS-USA','ASIA-JAPAN','ASIA-SOUTHKOREA'], ARRAY['security_alignment','economic_coercion','pacific_island_alignment'], 13, true),
('taiwan_strait_theater', 'Taiwan Strait confrontation', 'theater', ARRAY['ASIA-CHINA','ASIA-TAIWAN','AMERICAS-USA','ASIA-JAPAN'], ARRAY['taiwan_sovereignty','taiwan_military_pressure','taiwan_semiconductor_dependence','taiwan_international_recognition'], 14, true),
('scs_theater', 'South China Sea disputes', 'theater', ARRAY['ASIA-CHINA','ASIA-SOUTHEAST','AMERICAS-USA'], ARRAY['south_china_sea_claims','freedom_of_navigation','reef_militarisation','fisheries_conflict'], 15, true),
('korea_theater', 'Korean Peninsula standoff', 'theater', ARRAY['ASIA-NORKOREA','ASIA-SOUTHKOREA','AMERICAS-USA','ASIA-CHINA','ASIA-JAPAN'], ARRAY['north_korea_missile_program','peninsula_deterrence','north_korea_international_pressure','reunification_and_identity','north_korea_china_leverage'], 16, true),
('india_pakistan_theater', 'India-Pakistan rivalry', 'theater', ARRAY['ASIA-INDIA','ASIA-PAKISTAN','ASIA-CHINA'], ARRAY['kashmir_dispute','cross_border_militancy','nuclear_deterrence_balance','water_sharing_indus'], 17, true),
('india_china_theater', 'India-China border tensions', 'theater', ARRAY['ASIA-INDIA','ASIA-CHINA','ASIA-HIMALAYA'], ARRAY['ladakh_lac_dispute','himalayan_strategic_competition'], 18, true),
('japan_china_theater', 'Japan-China maritime disputes', 'theater', ARRAY['ASIA-JAPAN','ASIA-CHINA','ASIA-SOUTHKOREA'], ARRAY['senkaku_diaoyu_islands','east_china_sea_claims','historical_memory_conflicts'], 19, true),
('myanmar_theater', 'Myanmar civil conflict', 'theater', ARRAY['ASIA-SOUTHEAST','ASIA-CHINA','NON-STATE-ANTI-JUNTA','NON-STATE-ETHNIC-MILITIAS'], ARRAY['myanmar_military_rule','ethnic_armed_conflicts','china_border_influence'], 20, true),

-- AFRICA (3 theaters, 12 atomic FNs)
('horn_africa_theater', 'Horn of Africa instability', 'theater', ARRAY['AFRICA-ETHIOPIA','AFRICA-ERITREA','AFRICA-SOMALIA','AFRICA-KENYA','MIDEAST-EGYPT','AFRICA-DJIBOUTI','AMERICAS-USA','MIDEAST-TURKEY'], ARRAY['ethiopia_tigray_aftermath','ethiopia_amhara_conflict','somalia_al_shabaab','ethiopia_somaliland_access'], 21, true),
('sahel_theater', 'Sahel military transition zone', 'theater', ARRAY['AFRICA-SAHEL','AFRICA-NIGERIA','EUROPE-FRANCE','AMERICAS-USA','EUROPE-RUSSIA'], ARRAY['sahel_jihadist_insurgency','french_withdrawal_legacy','russian_security_presence','regional_regime_consolidation'], 22, true),
('great_lakes_theater', 'Great Lakes mineral conflict zone', 'theater', ARRAY['AFRICA-DRC','AFRICA-RWANDA','AFRICA-UGANDA','AFRICA-BURUNDI','ASIA-CHINA','AMERICAS-USA'], ARRAY['eastern_congo_armed_groups','m23_conflict','critical_minerals_competition','regional_intervention_forces'], 23, true),

-- AMERICAS (4 theaters, 17 atomic FNs)
('us_domestic_theater', 'United States domestic polarisation', 'theater', ARRAY['AMERICAS-USA'], ARRAY['us_electoral_legitimacy','federal_state_authority','immigration_border_politics','culture_war_conflicts'], 24, true),
('us_china_theater', 'US-China strategic competition', 'theater', ARRAY['AMERICAS-USA','ASIA-CHINA','ASIA-JAPAN','ASIA-SOUTHKOREA','ASIA-TAIWAN'], ARRAY['technology_restrictions','trade_and_tariffs','investment_screening','strategic_supply_chains'], 25, true),
('us_russia_theater', 'US-Russia strategic rivalry', 'theater', ARRAY['AMERICAS-USA','EUROPE-RUSSIA','EUROPE-UKRAINE','AMERICAS-CANADA'], ARRAY['nuclear_arms_control','election_interference','arctic_competition','ukraine_proxy_war'], 26, true),
('latam_theater', 'Latin America instability', 'theater', ARRAY['AMERICAS-USA','AMERICAS-VENEZUELA','AMERICAS-CUBA','AMERICAS-MEXICO','AMERICAS-CENTRAL','AMERICAS-COLOMBIA','AMERICAS-BRAZIL','AMERICAS-CHILE','AMERICAS-ARGENTINA','AMERICAS-BOLIVIA','AMERICAS-PERU','AMERICAS-GUYANA'], ARRAY['venezuela_political_transition','us_venezuela_relations','sanctions_and_oil','essequibo_dispute','embargo_and_sanctions','migration_pressures','regime_survival','infrastructure_influence','trade_dependence','strategic_resources'], 27, true),

-- ARCTIC (1 theater, 4 atomic FNs)
('arctic_theater', 'Arctic strategic competition', 'theater', ARRAY['EUROPE-RUSSIA','AMERICAS-USA','EUROPE-NORDIC','AMERICAS-CANADA','ASIA-CHINA','NON-STATE-EU','EUROPE-GREENLAND'], ARRAY['shipping_routes','greenland_control','military_presence','critical_resources'], 28, true),

-- ATOMIC FNs (MIDDLE EAST, 20 total)
('iran_nuclear_program', 'Iran''s nuclear programme', 'atomic', ARRAY['MIDEAST-IRAN'], NULL, 1, true),
('iran_proxy_network', 'Iran-linked armed groups in the region', 'atomic', ARRAY['MIDEAST-IRAN'], NULL, 2, true),
('strait_of_hormuz_sovereignty', 'Strait of Hormuz and Persian Gulf maritime security', 'atomic', ARRAY['MIDEAST-IRAN'], NULL, 3, true),
('gulf_attacks_on_arab_states', 'Missile and drone strikes against Gulf states', 'atomic', ARRAY['MIDEAST-GULF','MIDEAST-IRAN'], NULL, 4, true),
('gaza_war', 'Gaza war', 'atomic', ARRAY['MIDEAST-ISRAEL','MIDEAST-PALESTINE'], NULL, 5, true),
('west_bank_settlements', 'West Bank settlements', 'atomic', ARRAY['MIDEAST-ISRAEL','MIDEAST-PALESTINE'], NULL, 6, true),
('israel_lebanon_border', 'Israel-Lebanon border', 'atomic', ARRAY['MIDEAST-ISRAEL','MIDEAST-LEVANT'], NULL, 7, true),
('israel_iran_strikes', 'Israel-Iran direct strikes', 'atomic', ARRAY['MIDEAST-ISRAEL','MIDEAST-IRAN','AMERICAS-USA'], NULL, 8, true),
('syria_kurdish_question', 'Kurdish self-administration in northeast Syria', 'atomic', ARRAY['MIDEAST-LEVANT','MIDEAST-IRAQ','MIDEAST-TURKEY','AMERICAS-USA','NON-STATE-KURDISTAN','NON-STATE-ISIS'], NULL, 9, true),
('syria_israeli_strikes', 'Israeli strikes on Syrian targets', 'atomic', ARRAY['MIDEAST-LEVANT','MIDEAST-ISRAEL','MIDEAST-IRAN'], NULL, 10, true),
('syria_counter_terror', 'Counter-ISIS operations and residual terrorism', 'atomic', ARRAY['MIDEAST-LEVANT','MIDEAST-IRAQ','MIDEAST-TURKEY','MIDEAST-IRAN','AMERICAS-USA','NON-STATE-ISIS','NON-STATE-AL-QAEDA','NON-STATE-KURDISTAN'], NULL, 11, true),
('syria_recognition_and_normalisation', 'International recognition and normalisation with the new Syrian government', 'atomic', ARRAY['MIDEAST-LEVANT','MIDEAST-TURKEY','MIDEAST-SAUDI','MIDEAST-GULF','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-UK','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-RUSSIA','EUROPE-UKRAINE','NON-STATE-EU'], NULL, 12, true),
('turkey_kurdish_question', 'Turkey-side Kurdish question', 'atomic', ARRAY['MIDEAST-TURKEY','MIDEAST-LEVANT','MIDEAST-IRAQ'], NULL, 13, true),
('turkey_iran_war_spillover', 'Iran-war spillover into Turkey', 'atomic', ARRAY['MIDEAST-TURKEY','MIDEAST-IRAN'], NULL, 14, true),
('turkey_mediator_role', 'Turkey as regional mediator', 'atomic', ARRAY['MIDEAST-TURKEY','MIDEAST-IRAN','MIDEAST-ISRAEL','MIDEAST-EGYPT','MIDEAST-GULF','MIDEAST-SAUDI','EUROPE-UKRAINE'], NULL, 15, true),
('turkey_democratic_backsliding', 'Turkish domestic democratic backsliding', 'atomic', ARRAY['MIDEAST-TURKEY','EUROPE-GERMANY','NON-STATE-EU'], NULL, 16, true),
('saudi_houthi_war', 'Saudi-led coalition vs Houthi war', 'atomic', ARRAY['MIDEAST-YEMEN','MIDEAST-SAUDI','MIDEAST-GULF'], NULL, 17, true),
('houthi_strikes_on_israel', 'Houthi strikes on Israel', 'atomic', ARRAY['MIDEAST-YEMEN','MIDEAST-ISRAEL','MIDEAST-IRAN'], NULL, 18, true),
('red_sea_shipping_security', 'Red Sea and Bab al-Mandab shipping security', 'atomic', ARRAY['MIDEAST-YEMEN','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-UK'], NULL, 19, true),

-- ATOMIC FNs (EUROPE, 24 total)
('ukraine_battlefield', 'Battlefield operations and territorial control', 'atomic', ARRAY['EUROPE-UKRAINE','EUROPE-RUSSIA','AMERICAS-USA','EUROPE-BALTIC'], NULL, 20, true),
('western_aid_to_ukraine', 'Western military and economic aid to Ukraine', 'atomic', ARRAY['EUROPE-UKRAINE','AMERICAS-USA','EUROPE-UK','EUROPE-FRANCE','EUROPE-GERMANY'], NULL, 21, true),
('ukraine_peace_negotiations', 'Peace negotiations and diplomatic initiatives', 'atomic', ARRAY['EUROPE-UKRAINE','EUROPE-RUSSIA','AMERICAS-USA','NON-STATE-EU'], NULL, 22, true),
('ukraine_official_corruption', 'Official corruption and reconstruction challenges', 'atomic', ARRAY['EUROPE-UKRAINE','AMERICAS-USA','EUROPE-UK'], NULL, 23, true),
('nato_deterrence', 'NATO-Russia military deterrence on Eastern flank', 'atomic', ARRAY['EUROPE-RUSSIA','EUROPE-BALTIC','AMERICAS-USA','EUROPE-GERMANY'], NULL, 24, true),
('sanctions_and_economy', 'Sanctions regime and economic impact', 'atomic', ARRAY['EUROPE-RUSSIA','AMERICAS-USA','EUROPE-UK','EUROPE-EU'], NULL, 25, true),
('baltic_security', 'Baltic states security and NATO guarantees', 'atomic', ARRAY['EUROPE-RUSSIA','EUROPE-BALTIC','AMERICAS-USA'], NULL, 26, true),
('energy_security_leverage', 'Russian gas leverage and energy security', 'atomic', ARRAY['EUROPE-RUSSIA','EUROPE-EU','AMERICAS-USA'], NULL, 27, true),
('greenland_sovereignty', 'Greenland strategic control and Arctic geopolitics', 'atomic', ARRAY['EUROPE-GREENLAND','AMERICAS-USA','AMERICAS-CANADA'], NULL, 28, true),
('transatlantic_trade', 'Transatlantic trade disputes and tariffs', 'atomic', ARRAY['EUROPE-EU','AMERICAS-USA'], NULL, 29, true),
('strategic_autonomy', 'European strategic autonomy and decoupling from US', 'atomic', ARRAY['EUROPE-EU','AMERICAS-USA','ASIA-CHINA'], NULL, 30, true),
('defence_dependence', 'Defence burden-sharing and NATO spending', 'atomic', ARRAY['EUROPE-EU','AMERICAS-USA'], NULL, 31, true),
('hungary_rule_of_law', 'Hungary rule of law and EU institutions conflict', 'atomic', ARRAY['EUROPE-HUNGARY','EUROPE-EU'], NULL, 32, true),
('slovakia_alignment', 'Slovakia sovereignty and realignment pressures', 'atomic', ARRAY['EUROPE-SLOVAKIA','EUROPE-EU','EUROPE-RUSSIA'], NULL, 33, true),
('migration_burden_sharing', 'Migration burden-sharing and border conflicts', 'atomic', ARRAY['EUROPE-EU'], NULL, 34, true),
('budget_and_sovereignty', 'EU budget, Recovery Fund and sovereignty disputes', 'atomic', ARRAY['EUROPE-EU','EUROPE-VISEGRAD','EUROPE-UKRAINE'], NULL, 35, true),
('afd_and_german_polarisation', 'AfD and German political polarisation', 'atomic', ARRAY['EUROPE-GERMANY'], NULL, 36, true),
('french_nationalist_challenge', 'French nationalist movement and sovereignty', 'atomic', ARRAY['EUROPE-FRANCE'], NULL, 37, true),
('post_brexit_realignment', 'Post-Brexit UK-EU relationship', 'atomic', ARRAY['EUROPE-UK','EUROPE-EU'], NULL, 38, true),
('italian_populist_government', 'Italian right-wing populism and EU tensions', 'atomic', ARRAY['EUROPE-SOUTH'], NULL, 39, true),
('serbia_kosovo_tensions', 'Serbia-Kosovo status and normalisation', 'atomic', ARRAY['EUROPE-BALKANS'], NULL, 40, true),
('bosnia_fragmentation', 'Bosnia institutional fragmentation', 'atomic', ARRAY['EUROPE-BALKANS'], NULL, 41, true),
('armenia_azerbaijan_settlement', 'Armenia-Azerbaijan peace settlement and normalization', 'atomic', ARRAY['EUROPE-ARMENIA','EUROPE-AZERBAIJAN','EUROPE-RUSSIA','MIDEAST-TURKEY','AMERICAS-USA','NON-STATE-EU','MIDEAST-IRAN'], NULL, 42, true),
('nagorno_karabakh_aftermath', 'Nagorno-Karabakh humanitarian crisis and war crimes accountability', 'atomic', ARRAY['EUROPE-ARMENIA','EUROPE-AZERBAIJAN','EUROPE-RUSSIA','MIDEAST-TURKEY','AMERICAS-USA','NON-STATE-EU'], NULL, 43, true),
('zangezur_corridor', 'Zangezur corridor transit and regional connectivity', 'atomic', ARRAY['EUROPE-ARMENIA','EUROPE-AZERBAIJAN','MIDEAST-TURKEY','MIDEAST-IRAN'], NULL, 44, true),
('regional_power_competition', 'Russia-Turkey-Iran competition and regional balance', 'atomic', ARRAY['EUROPE-ARMENIA','EUROPE-AZERBAIJAN','EUROPE-RUSSIA','MIDEAST-TURKEY','MIDEAST-IRAN','AMERICAS-USA','NON-STATE-EU'], NULL, 45, true),

-- ATOMIC FNs (ASIA-PACIFIC, 29 total)
('security_alignment', 'AUKUS and Indo-Pacific security partnership', 'atomic', ARRAY['OCEANIA-AUSTRALIA','ASIA-CHINA','AMERICAS-USA','ASIA-JAPAN','ASIA-SOUTHKOREA'], NULL, 46, true),
('economic_coercion', 'Economic sanctions and trade weaponization', 'atomic', ARRAY['OCEANIA-AUSTRALIA','ASIA-CHINA'], NULL, 47, true),
('pacific_island_alignment', 'Geopolitical competition in Pacific island states', 'atomic', ARRAY['OCEANIA-AUSTRALIA','ASIA-CHINA','OCEANIA-MELANESIA'], NULL, 48, true),
('taiwan_sovereignty', 'Taiwan sovereignty dispute', 'atomic', ARRAY['ASIA-CHINA','ASIA-TAIWAN','AMERICAS-USA'], NULL, 49, true),
('taiwan_military_pressure', 'Military pressure and deterrence around Taiwan', 'atomic', ARRAY['ASIA-CHINA','ASIA-TAIWAN','AMERICAS-USA'], NULL, 50, true),
('taiwan_semiconductor_dependence', 'Semiconductor strategic dependence and supply chain security', 'atomic', ARRAY['ASIA-TAIWAN','ASIA-CHINA','AMERICAS-USA','ASIA-JAPAN'], NULL, 51, true),
('taiwan_international_recognition', 'Taiwan international recognition and diplomatic status', 'atomic', ARRAY['ASIA-TAIWAN','ASIA-CHINA'], NULL, 52, true),
('south_china_sea_claims', 'Maritime territorial claims and UNCLOS interpretation', 'atomic', ARRAY['ASIA-CHINA','ASIA-SOUTHEAST','AMERICAS-USA'], NULL, 53, true),
('freedom_of_navigation', 'Freedom of navigation and great power operations', 'atomic', ARRAY['ASIA-CHINA','AMERICAS-USA'], NULL, 54, true),
('reef_militarisation', 'Artificial islands militarisation and counter-presence', 'atomic', ARRAY['ASIA-CHINA','ASIA-SOUTHEAST','AMERICAS-USA'], NULL, 55, true),
('fisheries_conflict', 'Fisheries enforcement and maritime harassment', 'atomic', ARRAY['ASIA-CHINA','ASIA-SOUTHEAST'], NULL, 56, true),
('north_korea_missile_program', 'North Korean ballistic and nuclear missile programme', 'atomic', ARRAY['ASIA-NORKOREA','ASIA-SOUTHKOREA','AMERICAS-USA'], NULL, 57, true),
('peninsula_deterrence', 'Peninsula military deterrence and posture', 'atomic', ARRAY['ASIA-NORKOREA','ASIA-SOUTHKOREA','AMERICAS-USA'], NULL, 58, true),
('north_korea_international_pressure', 'International sanctions and pressure regime on North Korea', 'atomic', ARRAY['ASIA-NORKOREA','AMERICAS-USA','ASIA-CHINA','ASIA-JAPAN','ASIA-SOUTHKOREA'], NULL, 59, true),
('reunification_and_identity', 'Korean reunification question and national identity', 'atomic', ARRAY['ASIA-NORKOREA','ASIA-SOUTHKOREA'], NULL, 60, true),
('north_korea_china_leverage', 'China leverage over North Korea and sanctions', 'atomic', ARRAY['ASIA-NORKOREA','ASIA-CHINA'], NULL, 61, true),
('kashmir_dispute', 'Kashmir territorial dispute and border tensions', 'atomic', ARRAY['ASIA-INDIA','ASIA-PAKISTAN','ASIA-CHINA'], NULL, 62, true),
('cross_border_militancy', 'Cross-border militancy and proxy accusations', 'atomic', ARRAY['ASIA-INDIA','ASIA-PAKISTAN'], NULL, 63, true),
('nuclear_deterrence_balance', 'Nuclear deterrence balance and strategic stability', 'atomic', ARRAY['ASIA-INDIA','ASIA-PAKISTAN'], NULL, 64, true),
('water_sharing_indus', 'Indus waters treaty and resource sharing disputes', 'atomic', ARRAY['ASIA-INDIA','ASIA-PAKISTAN'], NULL, 65, true),
('ladakh_lac_dispute', 'Ladakh and LAC border militarization', 'atomic', ARRAY['ASIA-INDIA','ASIA-CHINA'], NULL, 66, true),
('himalayan_strategic_competition', 'Himalayan strategic competition and infrastructure', 'atomic', ARRAY['ASIA-INDIA','ASIA-CHINA','ASIA-HIMALAYA'], NULL, 67, true),
('senkaku_diaoyu_islands', 'Senkaku/Diaoyu islands territorial dispute', 'atomic', ARRAY['ASIA-JAPAN','ASIA-CHINA'], NULL, 68, true),
('east_china_sea_claims', 'East China Sea overlapping continental shelf claims', 'atomic', ARRAY['ASIA-JAPAN','ASIA-CHINA','ASIA-SOUTHKOREA'], NULL, 69, true),
('historical_memory_conflicts', 'Historical memory and memory wars', 'atomic', ARRAY['ASIA-JAPAN','ASIA-CHINA'], NULL, 70, true),
('myanmar_military_rule', 'Military rule and anti-junta resistance', 'atomic', ARRAY['ASIA-SOUTHEAST','NON-STATE-ANTI-JUNTA'], NULL, 71, true),
('ethnic_armed_conflicts', 'Ethnic armed conflicts and autonomy demands', 'atomic', ARRAY['ASIA-SOUTHEAST','NON-STATE-ETHNIC-MILITIAS'], NULL, 72, true),
('china_border_influence', 'Chinese influence on border stability and conflicts', 'atomic', ARRAY['ASIA-SOUTHEAST','ASIA-CHINA'], NULL, 73, true),

-- ATOMIC FNs (AFRICA, 12 total)
('ethiopia_tigray_aftermath', 'Tigray conflict aftermath and war crimes accountability', 'atomic', ARRAY['AFRICA-ETHIOPIA','AFRICA-ERITREA','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-UK'], NULL, 74, true),
('ethiopia_amhara_conflict', 'Amhara insurgency and border tensions', 'atomic', ARRAY['AFRICA-ETHIOPIA','AFRICA-ERITREA','NON-STATE-OROMIA-LIBERATION-FRONT'], NULL, 75, true),
('somalia_al_shabaab', 'Al-Shabaab insurgency and counter-terror operations', 'atomic', ARRAY['AFRICA-SOMALIA','AFRICA-KENYA','AMERICAS-USA','MIDEAST-TURKEY','NON-STATE-AL-SHABAAB'], NULL, 76, true),
('ethiopia_somaliland_access', 'Ethiopian sea access and Red Sea port competition', 'atomic', ARRAY['AFRICA-ETHIOPIA','AFRICA-SOMALIA','MIDEAST-EGYPT','AFRICA-DJIBOUTI','AFRICA-ERITREA'], NULL, 77, true),
('sahel_jihadist_insurgency', 'Jihadist insurgency and militant group operations', 'atomic', ARRAY['AFRICA-SAHEL','AFRICA-NIGERIA','AMERICAS-USA','EUROPE-FRANCE','NON-STATE-JIHADISTS'], NULL, 78, true),
('french_withdrawal_legacy', 'Post-French security vacuum and great power competition', 'atomic', ARRAY['AFRICA-SAHEL','EUROPE-FRANCE','AMERICAS-USA','EUROPE-RUSSIA'], NULL, 79, true),
('russian_security_presence', 'Wagner and Russian military expansion in Sahel', 'atomic', ARRAY['AFRICA-SAHEL','EUROPE-RUSSIA','EUROPE-FRANCE','AMERICAS-USA'], NULL, 80, true),
('regional_regime_consolidation', 'Military junta consolidation and democratic backsliding', 'atomic', ARRAY['AFRICA-SAHEL'], NULL, 81, true),
('eastern_congo_armed_groups', 'Armed group proliferation and territorial control', 'atomic', ARRAY['AFRICA-DRC','AFRICA-RWANDA','AFRICA-UGANDA','AFRICA-BURUNDI'], NULL, 82, true),
('m23_conflict', 'M23 insurgency and regional proxy dynamics', 'atomic', ARRAY['AFRICA-DRC','AFRICA-RWANDA','AFRICA-UGANDA','AFRICA-BURUNDI','NON-STATE-M23'], NULL, 83, true),
('critical_minerals_competition', 'Cobalt and coltan extraction and supply chain control', 'atomic', ARRAY['AFRICA-DRC','ASIA-CHINA','AMERICAS-USA'], NULL, 84, true),
('regional_intervention_forces', 'MONUSCO, AU and regional military deployments', 'atomic', ARRAY['AFRICA-DRC','AFRICA-RWANDA','AFRICA-UGANDA','AFRICA-BURUNDI'], NULL, 85, true),

-- ATOMIC FNs (AMERICAS, 17 total)
('us_electoral_legitimacy', 'Electoral legitimacy and democratic backsliding', 'atomic', ARRAY['AMERICAS-USA'], NULL, 86, true),
('federal_state_authority', 'Federal versus state authority and governance', 'atomic', ARRAY['AMERICAS-USA'], NULL, 87, true),
('immigration_border_politics', 'Immigration and Mexico-US border politics', 'atomic', ARRAY['AMERICAS-USA','AMERICAS-MEXICO','AMERICAS-CENTRAL'], NULL, 88, true),
('culture_war_conflicts', 'National culture war conflicts and polarisation', 'atomic', ARRAY['AMERICAS-USA'], NULL, 89, true),
('technology_restrictions', 'Technology controls and semiconductor restrictions', 'atomic', ARRAY['AMERICAS-USA','ASIA-CHINA'], NULL, 90, true),
('trade_and_tariffs', 'Trade and tariff competition', 'atomic', ARRAY['AMERICAS-USA','ASIA-CHINA'], NULL, 91, true),
('investment_screening', 'Foreign investment restrictions and capital controls', 'atomic', ARRAY['AMERICAS-USA','ASIA-CHINA'], NULL, 92, true),
('strategic_supply_chains', 'Strategic supply chain competition and dependencies', 'atomic', ARRAY['AMERICAS-USA','ASIA-CHINA','ASIA-JAPAN','ASIA-SOUTHKOREA','ASIA-TAIWAN'], NULL, 93, true),
('nuclear_arms_control', 'Nuclear arms control and strategic stability', 'atomic', ARRAY['AMERICAS-USA','EUROPE-RUSSIA'], NULL, 94, true),
('election_interference', 'Election interference and information warfare', 'atomic', ARRAY['AMERICAS-USA','EUROPE-RUSSIA'], NULL, 95, true),
('arctic_competition', 'Arctic energy and territorial competition', 'atomic', ARRAY['AMERICAS-USA','EUROPE-RUSSIA','AMERICAS-CANADA','EUROPE-NORDIC'], NULL, 96, true),
('ukraine_proxy_war', 'Ukraine war and NATO proxy dynamics', 'atomic', ARRAY['AMERICAS-USA','EUROPE-RUSSIA','EUROPE-UKRAINE'], NULL, 97, true),
('venezuela_political_transition', 'Venezuela regime change and political transition', 'atomic', ARRAY['AMERICAS-VENEZUELA','AMERICAS-USA','AMERICAS-COLOMBIA','AMERICAS-BRAZIL'], NULL, 98, true),
('us_venezuela_relations', 'US-Venezuela confrontation and foreign policy', 'atomic', ARRAY['AMERICAS-VENEZUELA','AMERICAS-USA'], NULL, 99, true),
('sanctions_and_oil', 'Sanctions, oil exports and economic pressure', 'atomic', ARRAY['AMERICAS-VENEZUELA','AMERICAS-USA'], NULL, 100, true),
('essequibo_dispute', 'Essequibo territorial dispute with Guyana', 'atomic', ARRAY['AMERICAS-VENEZUELA','AMERICAS-GUYANA','AMERICAS-BRAZIL'], NULL, 101, true),
('embargo_and_sanctions', 'US embargo and sanctions regime on Cuba', 'atomic', ARRAY['AMERICAS-CUBA','AMERICAS-USA'], NULL, 102, true),
('migration_pressures', 'Migration and refugee pressures', 'atomic', ARRAY['AMERICAS-CUBA','AMERICAS-USA'], NULL, 103, true),
('regime_survival', 'Cuban regime survival and external pressure', 'atomic', ARRAY['AMERICAS-CUBA','AMERICAS-USA'], NULL, 104, true),
('infrastructure_influence', 'Chinese Belt and Road versus US USAID influence', 'atomic', ARRAY['AMERICAS-USA','ASIA-CHINA','AMERICAS-BRAZIL','AMERICAS-MEXICO'], NULL, 105, true),
('trade_dependence', 'Trade dependence and manufacturing competition', 'atomic', ARRAY['AMERICAS-USA','ASIA-CHINA','AMERICAS-BRAZIL','AMERICAS-MEXICO'], NULL, 106, true),
('strategic_resources', 'Lithium and strategic minerals competition', 'atomic', ARRAY['ASIA-CHINA','AMERICAS-USA','AMERICAS-CHILE','AMERICAS-ARGENTINA','AMERICAS-BOLIVIA','AMERICAS-PERU'], NULL, 107, true),

-- ATOMIC FNs (ARCTIC, 4 total)
('shipping_routes', 'Arctic shipping routes and passage competition', 'atomic', ARRAY['EUROPE-RUSSIA','AMERICAS-USA','EUROPE-NORDIC','AMERICAS-CANADA','ASIA-CHINA','NON-STATE-EU'], NULL, 108, true),
('greenland_control', 'Greenland strategic control and Arctic geopolitics', 'atomic', ARRAY['EUROPE-GREENLAND','AMERICAS-USA','AMERICAS-CANADA','EUROPE-NORDIC'], NULL, 109, true),
('military_presence', 'Arctic military build-up and NATO expansion', 'atomic', ARRAY['EUROPE-RUSSIA','AMERICAS-USA','EUROPE-NORDIC','AMERICAS-CANADA'], NULL, 110, true),
('critical_resources', 'Arctic resources competition and climate access', 'atomic', ARRAY['EUROPE-RUSSIA','AMERICAS-USA','EUROPE-GREENLAND','AMERICAS-CANADA','ASIA-CHINA','NON-STATE-EU','EUROPE-NORDIC'], NULL, 111, true)

ON CONFLICT (id) DO NOTHING;

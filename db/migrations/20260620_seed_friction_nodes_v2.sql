-- Seed global friction nodes with correct centroid_id mappings
-- Uses existing centroids: ASIA-* (not ASIA-PACIFIC-*), OCEANIA-* for Pacific
-- 2026-06-20

INSERT INTO friction_nodes (id, name_en, fn_type, centroid_ids, member_fn_ids, display_order, is_active) VALUES

-- MIDDLE EAST (6 theaters, 20 atomic FNs)
('iran_theater', 'Iran in regional and international confrontation', 'theater', ARRAY['MIDEAST-IRAN'], ARRAY['iran_nuclear_program','iran_proxy_network','strait_of_hormuz_sovereignty','gulf_attacks_on_arab_states'], 1, true),
('israel_theater', 'Israel in regional confrontation', 'theater', ARRAY['MIDEAST-ISRAEL','MIDEAST-PALESTINE','MIDEAST-LEVANT'], ARRAY['gaza_war','israel_lebanon_border','israel_iran_strikes','west_bank_settlements'], 2, true),
('syria_theater', 'Syria in post-Assad transition', 'theater', ARRAY['MIDEAST-LEVANT','MIDEAST-TURKEY','MIDEAST-IRAN','MIDEAST-ISRAEL','MIDEAST-GULF','MIDEAST-SAUDI','MIDEAST-IRAQ','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-UK','EUROPE-FRANCE','EUROPE-GERMANY','EUROPE-RUSSIA','EUROPE-UKRAINE','NON-STATE-EU'], ARRAY['syria_kurdish_question','syria_israeli_strikes','syria_counter_terror','syria_recognition_and_normalisation'], 3, true),
('turkey_theater', 'Turkey as contested regional power', 'theater', ARRAY['MIDEAST-TURKEY','MIDEAST-LEVANT','MIDEAST-IRAN','MIDEAST-ISRAEL','MIDEAST-GULF','MIDEAST-SAUDI','MIDEAST-IRAQ','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-RUSSIA','EUROPE-VISEGRAD','EUROPE-GERMANY','EUROPE-SOUTH','NON-STATE-EU','NON-STATE-NATO'], ARRAY['turkey_kurdish_question','turkey_iran_war_spillover','turkey_mediator_role','turkey_democratic_backsliding'], 4, true),
('yemen_red_sea_theater', 'Yemen and the Red Sea front', 'theater', ARRAY['MIDEAST-YEMEN','MIDEAST-SAUDI','MIDEAST-GULF','MIDEAST-EGYPT','MIDEAST-IRAN','MIDEAST-ISRAEL','AMERICAS-USA','EUROPE-UK'], ARRAY['red_sea_shipping_security','houthi_strikes_on_israel','saudi_houthi_war'], 5, true),

-- EUROPE (7 theaters, 24 atomic FNs)
('ukraine_war_theater', 'Ukraine war theater', 'theater', ARRAY['EUROPE-UKRAINE','EUROPE-RUSSIA','AMERICAS-USA','EUROPE-BELARUS','EUROPE-BALKANS'], ARRAY['ukraine_battlefield','western_aid_to_ukraine','ukraine_peace_negotiations','ukraine_official_corruption'], 6, true),
('russia_europe_theater', 'Russia-Europe confrontation', 'theater', ARRAY['EUROPE-RUSSIA','EUROPE-EU','EUROPE-BALTIC','AMERICAS-USA'], ARRAY['nato_deterrence','sanctions_and_economy','baltic_security','energy_security_leverage'], 7, true),
('europe_us_theater', 'Europe-US strategic tensions', 'theater', ARRAY['EUROPE-EU','AMERICAS-USA','ASIA-CHINA'], ARRAY['greenland_sovereignty','transatlantic_trade','strategic_autonomy','defence_dependence'], 8, true),
('eu_cohesion_theater', 'EU internal cohesion', 'theater', ARRAY['EUROPE-EU','EUROPE-VISEGRAD'], ARRAY['hungary_rule_of_law','slovakia_alignment','migration_burden_sharing','budget_and_sovereignty'], 9, true),
('europe_sovereignty_theater', 'European sovereignty movements', 'theater', ARRAY['EUROPE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH'], ARRAY['afd_and_german_polarisation','french_nationalist_challenge','post_brexit_realignment','italian_populist_government'], 10, true),
('balkan_theater', 'Balkan instability', 'theater', ARRAY['EUROPE-BALKANS','EUROPE-BALKANS-EAST'], ARRAY['serbia_kosovo_tensions','bosnia_fragmentation'], 11, true),
('caucasus_theater', 'South Caucasus realignment', 'theater', ARRAY['EUROPE-ARMENIA','EUROPE-AZERBAIJAN','EUROPE-RUSSIA','MIDEAST-TURKEY','MIDEAST-IRAN','AMERICAS-USA','EUROPE-EU'], ARRAY['armenia_azerbaijan_settlement','nagorno_karabakh_aftermath','zangezur_corridor','regional_power_competition'], 12, true),

-- ASIA-PACIFIC (8 theaters, 29 atomic FNs) - using ASIA-*, OCEANIA-* for correct i18n
('australia_china_theater', 'Australia-China strategic rivalry', 'theater', ARRAY['OCEANIA-AUSTRALIA','ASIA-CHINA','AMERICAS-USA','ASIA-JAPAN','ASIA-SOUTHKOREA'], ARRAY['security_alignment','economic_coercion','pacific_island_alignment'], 13, true),
('taiwan_strait_theater', 'Taiwan Strait confrontation', 'theater', ARRAY['ASIA-CHINA','ASIA-TAIWAN','AMERICAS-USA','ASIA-JAPAN'], ARRAY['taiwan_sovereignty','taiwan_military_pressure','taiwan_semiconductor_dependence','taiwan_international_recognition'], 14, true),
('scs_theater', 'South China Sea disputes', 'theater', ARRAY['ASIA-CHINA','ASIA-SOUTHEAST','AMERICAS-USA'], ARRAY['south_china_sea_claims','freedom_of_navigation','reef_militarisation','fisheries_conflict'], 15, true),
('korea_theater', 'Korean Peninsula standoff', 'theater', ARRAY['ASIA-NORKOREA','ASIA-SOUTHKOREA','AMERICAS-USA','ASIA-CHINA','ASIA-JAPAN'], ARRAY['north_korea_missile_program','peninsula_deterrence','north_korea_international_pressure','reunification_and_identity','north_korea_china_leverage'], 16, true),
('india_pakistan_theater', 'India-Pakistan rivalry', 'theater', ARRAY['ASIA-INDIA','ASIA-PAKISTAN','ASIA-CHINA'], ARRAY['kashmir_dispute','cross_border_militancy','nuclear_deterrence_balance','water_sharing_indus'], 17, true),
('india_china_theater', 'India-China border tensions', 'theater', ARRAY['ASIA-INDIA','ASIA-CHINA','ASIA-HIMALAYA'], ARRAY['ladakh_lac_dispute','himalayan_strategic_competition'], 18, true),
('japan_china_theater', 'Japan-China maritime disputes', 'theater', ARRAY['ASIA-JAPAN','ASIA-CHINA','ASIA-SOUTHKOREA'], ARRAY['senkaku_diaoyu_islands','east_china_sea_claims','historical_memory_conflicts'], 19, true),
('myanmar_theater', 'Myanmar civil conflict', 'theater', ARRAY['ASIA-SOUTHEAST','ASIA-CHINA','NON-STATE-ANTI-JUNTA','NON-STATE-ETHNIC-MILITIAS'], ARRAY['myanmar_military_rule','ethnic_armed_conflicts','china_border_influence'], 20, true),

-- AFRICA (3 theaters, 12 atomic FNs)
('horn_africa_theater', 'Horn of Africa instability', 'theater', ARRAY['AFRICA-ETHIOPIA','AFRICA-HORN','AFRICA-SOMALIA','AFRICA-KENYA','MIDEAST-EGYPT','AFRICA-DJIBOUTI','AMERICAS-USA','MIDEAST-TURKEY'], ARRAY['ethiopia_tigray_aftermath','ethiopia_amhara_conflict','somalia_al_shabaab','ethiopia_somaliland_access'], 21, true),
('sahel_theater', 'Sahel military transition zone', 'theater', ARRAY['AFRICA-SAHEL','AFRICA-SAHEL','AFRICA-WEST','AFRICA-NIGERIA','AFRICA-MAURITANIA','EUROPE-FRANCE','AMERICAS-USA','EUROPE-RUSSIA'], ARRAY['sahel_jihadist_insurgency','french_withdrawal_legacy','russian_security_presence','regional_regime_consolidation'], 22, true),
('great_lakes_theater', 'Great Lakes mineral conflict zone', 'theater', ARRAY['AFRICA-DRC','AFRICA-EAST','AMERICAS-USA','ASIA-CHINA'], ARRAY['eastern_congo_armed_groups','m23_conflict','critical_minerals_competition','regional_intervention_forces'], 23, true),

-- AMERICAS (4 theaters, 17 atomic FNs)
('us_domestic_theater', 'United States domestic polarisation', 'theater', ARRAY['AMERICAS-USA'], ARRAY['us_electoral_legitimacy','federal_state_authority','immigration_border_politics','culture_war_conflicts'], 24, true),
('us_china_theater', 'US-China strategic competition', 'theater', ARRAY['AMERICAS-USA','ASIA-CHINA','ASIA-JAPAN','ASIA-SOUTHKOREA','ASIA-TAIWAN'], ARRAY['technology_restrictions','trade_and_tariffs','investment_screening','strategic_supply_chains'], 25, true),
('us_russia_theater', 'US-Russia strategic rivalry', 'theater', ARRAY['AMERICAS-USA','EUROPE-RUSSIA','EUROPE-UKRAINE','AMERICAS-CANADA'], ARRAY['nuclear_arms_control','election_interference','arctic_competition','ukraine_proxy_war'], 26, true),
('latam_theater', 'Latin America instability', 'theater', ARRAY['AMERICAS-USA','AMERICAS-VENEZUELA','AMERICAS-CUBA','AMERICAS-MEXICO','AMERICAS-CENTRAL','AMERICAS-COLOMBIA','AMERICAS-BRAZIL','AMERICAS-ANDEAN'], ARRAY['venezuela_political_transition','us_venezuela_relations','sanctions_and_oil','essequibo_dispute','embargo_and_sanctions','migration_pressures','regime_survival','infrastructure_influence','trade_dependence','strategic_resources'], 27, true),

-- ARCTIC (1 theater, 4 atomic FNs)
('arctic_theater', 'Arctic strategic competition', 'theater', ARRAY['EUROPE-RUSSIA','AMERICAS-USA','EUROPE-NORDIC','AMERICAS-CANADA','ASIA-CHINA','EUROPE-EU'], ARRAY['shipping_routes','greenland_sovereignty','military_presence','critical_resources'], 28, true),

-- ATOMIC FNs (rest of the implementation...)
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
('syria_recognition_and_normalisation', 'International recognition and normalisation with Syria', 'atomic', ARRAY['MIDEAST-LEVANT','MIDEAST-TURKEY','MIDEAST-SAUDI','MIDEAST-GULF','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-UK','EUROPE-FRANCE','EUROPE-GERMANY','EUROPE-RUSSIA','EUROPE-UKRAINE','NON-STATE-EU'], NULL, 12, true),
('turkey_kurdish_question', 'Turkey-side Kurdish question', 'atomic', ARRAY['MIDEAST-TURKEY','MIDEAST-LEVANT','MIDEAST-IRAQ'], NULL, 13, true),
('turkey_iran_war_spillover', 'Iran-war spillover into Turkey', 'atomic', ARRAY['MIDEAST-TURKEY','MIDEAST-IRAN'], NULL, 14, true),
('turkey_mediator_role', 'Turkey as regional mediator', 'atomic', ARRAY['MIDEAST-TURKEY','MIDEAST-IRAN','MIDEAST-ISRAEL','MIDEAST-EGYPT','MIDEAST-GULF','MIDEAST-SAUDI','EUROPE-UKRAINE'], NULL, 15, true),
('turkey_democratic_backsliding', 'Turkish domestic democratic backsliding', 'atomic', ARRAY['MIDEAST-TURKEY','EUROPE-GERMANY','NON-STATE-EU'], NULL, 16, true),
('saudi_houthi_war', 'Saudi-led coalition vs Houthi war', 'atomic', ARRAY['MIDEAST-YEMEN','MIDEAST-SAUDI','MIDEAST-GULF'], NULL, 17, true),
('houthi_strikes_on_israel', 'Houthi strikes on Israel', 'atomic', ARRAY['MIDEAST-YEMEN','MIDEAST-ISRAEL','MIDEAST-IRAN'], NULL, 18, true),
('red_sea_shipping_security', 'Red Sea and Bab al-Mandab shipping security', 'atomic', ARRAY['MIDEAST-YEMEN','MIDEAST-EGYPT','AMERICAS-USA','EUROPE-UK'], NULL, 19, true)

ON CONFLICT (id) DO NOTHING;

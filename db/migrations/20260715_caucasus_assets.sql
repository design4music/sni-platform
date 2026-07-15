-- Caucasus strategic assets: fix phantom centroids on the 2 existing assets and
-- add the 2 missing energy arteries (South Caucasus gas pipeline + Sangachal
-- terminal). Source of truth is db/registry/*.yaml (gas/pipelines/ports.yaml,
-- already updated); synced here directly because the asset generator currently
-- aborts on unrelated untracked official_sources_*.yaml files. meta shape matches
-- generate_asset_registry.py output. Idempotent.

BEGIN;

-- fix phantom EUROPE-AZERBAIJAN -> real ASIA-CAUCASUS centroid
UPDATE strategic_assets SET centroid_ids = ARRAY['ASIA-CAUCASUS','MIDEAST-TURKEY'], updated_at=now() WHERE id='btc_pipeline';
UPDATE strategic_assets SET centroid_ids = ARRAY['ASIA-CAUCASUS'], updated_at=now() WHERE id='shah_deniz_field';

INSERT INTO strategic_assets (id, name_en, name_de, asset_type, subcategory, commodities, centroid_ids, criticality, meta, geometry, description_en, description_de, is_active) VALUES
('scp_pipeline','South Caucasus Pipeline','Suedkaukasus-Pipeline','pipeline','gas_pipeline',
 ARRAY['gas'], ARRAY['ASIA-CAUCASUS','MIDEAST-TURKEY'], 3,
 '{"aliases":["South Caucasus Pipeline","SCP","Baku-Tbilisi-Erzurum"],"rank_note":"Carries Shah Deniz gas from Azerbaijan via Georgia to Turkey -- the first leg of the Southern Gas Corridor to Europe, running parallel to the BTC oil line.","ranking_source":"Global Energy Monitor GGIT route tracker","route_source":"Global Energy Monitor GOIT/GGIT (shared BTC/SCP corridor to Erzurum)","route_license":"CC BY 4.0"}'::jsonb,
 -- Route offset ~0.18 deg N of BTC so both parallel pipelines render distinctly
 -- (BTC and SCP share the physical corridor through Azerbaijan and Georgia).
 '{"type":"LineString","coordinates":[[49.208,40.343],[49.136,40.284],[48.96,40.25],[48.492,40.449],[48.299,40.467],[47.699,40.669],[47.558,40.651],[47.453,40.697],[47.425,40.757],[47.267,40.8],[47.218,40.771],[47.12,40.813],[46.85,40.838],[46.693,40.817],[46.537,41.001],[46.346,41.042],[46.213,41.023],[46.025,41.079],[45.686,41.25],[45.604,41.259],[45.43,41.434],[45.204,41.545],[44.98,41.745],[44.782,41.647],[44.583,41.635],[44.486,41.657],[44.368,41.766],[44.275,41.802],[43.894,41.784],[43.744,41.851],[43.565,41.799],[43.306,41.881],[43.115,41.839],[42.933,41.781],[42.795,41.69],[42.745,41.417],[42.674,41.389],[42.706,41.283],[42.851,41.137],[42.895,41.016],[42.839,40.921],[42.734,40.781],[42.4,40.61],[42.316,40.53],[42.288,40.444],[41.974,40.183],[41.66,40.112],[41.274,40.146]]}'::jsonb,
 'Carries Azerbaijani gas from the Shah Deniz field across Georgia to the Turkish border, forming the first leg of the Southern Gas Corridor that supplies non-Russian gas to Southeastern Europe, parallel to the Baku-Tbilisi-Ceyhan oil pipeline.',
 'Transportiert aserbaidschanisches Gas vom Shah-Deniz-Feld ueber Georgien zur tuerkischen Grenze und bildet die erste Etappe des Suedlichen Gaskorridors, der Suedosteuropa mit nicht-russischem Gas versorgt, parallel zur Baku-Tiflis-Ceyhan-Oelpipeline.',
 true),
('sangachal_terminal','Sangachal Terminal','Sangachal-Terminal','port','energy',
 ARRAY['oil','gas'], ARRAY['ASIA-CAUCASUS'], 3,
 '{"aliases":["Sangachal","Sangachal Terminal"],"rank_note":"One of the world''s largest oil and gas terminals; the origin point of the BTC oil pipeline and the South Caucasus gas pipeline.","ranking_source":"BP/AIOC operator disclosures; EIA Azerbaijan country analysis"}'::jsonb,
 '{"type":"Point","coordinates":[49.47,40.17]}'::jsonb,
 'A large oil and gas processing and export terminal on Azerbaijan''s Caspian coast south of Baku, where output from the offshore Azeri-Chirag-Gunashli oil fields and the Shah Deniz gas field is gathered before entering the BTC and South Caucasus pipelines.',
 'Ein grosses Oel- und Gasaufbereitungs- und Exportterminal an Aserbaidschans Kaspikueste suedlich von Baku, wo die Foerderung der Offshore-Oelfelder Azeri-Chirag-Gunaschli und des Gasfelds Shah Deniz gesammelt wird, bevor sie in die BTC- und die Suedkaukasus-Pipeline eingespeist wird.',
 true)
ON CONFLICT (id) DO UPDATE SET
 name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de, asset_type=EXCLUDED.asset_type,
 subcategory=EXCLUDED.subcategory, commodities=EXCLUDED.commodities, centroid_ids=EXCLUDED.centroid_ids,
 criticality=EXCLUDED.criticality, meta=EXCLUDED.meta, geometry=EXCLUDED.geometry, description_en=EXCLUDED.description_en,
 description_de=EXCLUDED.description_de, is_active=true, updated_at=now();

-- attach the 4 energy assets: theater (aggregate) + power_competition (energy atomic)
UPDATE friction_nodes SET affected_asset_ids = ARRAY['btc_pipeline','shah_deniz_field','scp_pipeline','sangachal_terminal'], updated_at=now() WHERE id='caucasus_theater';
UPDATE friction_nodes SET affected_asset_ids = ARRAY['btc_pipeline','shah_deniz_field','scp_pipeline','sangachal_terminal'], updated_at=now() WHERE id='caucasus_power_competition';

COMMIT;

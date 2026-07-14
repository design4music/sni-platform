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
 '{"type":"LineString","coordinates":[[49.208,40.163],[49.136,40.104],[48.96,40.07],[48.492,40.269],[48.299,40.287],[47.699,40.489],[47.558,40.471],[47.453,40.517],[47.425,40.577],[47.267,40.62],[47.218,40.591],[47.12,40.633],[46.85,40.658],[46.693,40.637],[46.537,40.821],[46.346,40.862],[46.213,40.843],[46.025,40.899],[45.686,41.07],[45.604,41.079],[45.43,41.254],[45.204,41.365],[44.98,41.565],[44.782,41.467],[44.583,41.455],[44.486,41.477],[44.368,41.586],[44.275,41.622],[43.894,41.604],[43.744,41.671],[43.565,41.619],[43.306,41.701],[43.115,41.659],[42.933,41.601],[42.795,41.51],[42.745,41.237],[42.674,41.209],[42.706,41.103],[42.851,40.957],[42.895,40.836],[42.839,40.741],[42.734,40.601],[42.4,40.43],[42.316,40.35],[42.288,40.264],[41.974,40.003],[41.66,39.932],[41.274,39.966]]}'::jsonb,
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

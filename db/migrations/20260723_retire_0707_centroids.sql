-- Retire 53 over-granular centroids created 2026-07-07; revert to regional composition.
-- titles_v3 has ZERO refs (pipeline labels on group centroids). Only config rows remap.
-- FK cascade tables (ctm, centroid_summaries) and restrict FKs all verified clear.
BEGIN;

-- friction_nodes.centroid_ids remap (order-preserving, deduped)
UPDATE friction_nodes SET centroid_ids = ARRAY['EUROPE-RUSSIA','AMERICAS-USA','EUROPE-NORDIC','AMERICAS-CANADA','ASIA-CHINA','NON-STATE-EU'] WHERE id = 'arctic_resources_competition';
UPDATE friction_nodes SET centroid_ids = ARRAY['EUROPE-RUSSIA','AMERICAS-USA','EUROPE-NORDIC','AMERICAS-CANADA','ASIA-CHINA','NON-STATE-EU'] WHERE id = 'arctic_theater';
UPDATE friction_nodes SET centroid_ids = ARRAY['AFRICA-DRC','AFRICA-EAST'] WHERE id = 'drc_intervention_forces';
UPDATE friction_nodes SET centroid_ids = ARRAY['AFRICA-DRC','AFRICA-EAST'] WHERE id = 'eastern_congo_armed_groups';
UPDATE friction_nodes SET centroid_ids = ARRAY['AFRICA-ETHIOPIA','AFRICA-HORN'] WHERE id = 'ethiopia_amhara_conflict';
UPDATE friction_nodes SET centroid_ids = ARRAY['AFRICA-ETHIOPIA','AFRICA-HORN','MIDEAST-EGYPT'] WHERE id = 'ethiopia_somaliland_access';
UPDATE friction_nodes SET centroid_ids = ARRAY['EUROPE-NORDIC','AMERICAS-USA','AMERICAS-CANADA','NON-STATE-EU','NON-STATE-NATO','EUROPE-RUSSIA'] WHERE id = 'greenland_control';
UPDATE friction_nodes SET centroid_ids = ARRAY['EUROPE-NORDIC','AMERICAS-USA','AMERICAS-CANADA'] WHERE id = 'greenland_sovereignty';
UPDATE friction_nodes SET centroid_ids = ARRAY['AMERICAS-USA','AMERICAS-VENEZUELA','AMERICAS-CUBA','AMERICAS-MEXICO','AMERICAS-CENTRAL','AMERICAS-ANDEAN','AMERICAS-BRAZIL','AMERICAS-SOUTHERNCONE','AMERICAS-CARIBBEAN'] WHERE id = 'latam_theater';
UPDATE friction_nodes SET centroid_ids = ARRAY['ASIA-SOUTHEAST'] WHERE id = 'myanmar_ethnic_conflicts';
UPDATE friction_nodes SET centroid_ids = ARRAY['ASIA-CAUCASUS','EUROPE-RUSSIA','MIDEAST-TURKEY','AMERICAS-USA','NON-STATE-EU'] WHERE id = 'nagorno_karabakh_aftermath';
UPDATE friction_nodes SET centroid_ids = ARRAY['AFRICA-SAHEL','AFRICA-NIGERIA','NON-STATE-BOKO-HARAM'] WHERE id = 'sahel_jihadist_insurgency';

-- narratives_v2.actor_centroids remap
UPDATE narratives_v2 SET actor_centroids = ARRAY['EUROPE-NORDIC'] WHERE id = 'greenland_self_determination';

-- strategic_assets.centroid_ids remap
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-SOUTHERNCONE'] WHERE id = 'atacama_lithium_triangle';
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-ANDEAN'] WHERE id = 'callao_port';
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-ANDEAN'] WHERE id = 'cartagena_co_port';
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-SOUTHERNCONE'] WHERE id = 'chilean_copper_belt';
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-ANDEAN'] WHERE id = 'colombia_eje_cafetero';
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-SOUTHERNCONE','MIDEAST-EGYPT'] WHERE id = 'lane_laplata_grain';
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-SOUTHERNCONE'] WHERE id = 'pampas_grain_belt';
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-ANDEAN'] WHERE id = 'peruvian_anchoveta_grounds';
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-ANDEAN'] WHERE id = 'salar_de_uyuni_lithium';
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-ANDEAN'] WHERE id = 'southern_peru_copper_belt';
UPDATE strategic_assets SET centroid_ids = ARRAY['AMERICAS-CARIBBEAN'] WHERE id = 'stabroek_block';

-- drop the 53 (explicit ids = the 2026-07-07 batch; deterministic across local/Render)
DELETE FROM centroids_v3 WHERE id IN (
  'AFRICA-ANGOLA',
  'AFRICA-BURKINA-FASO',
  'AFRICA-BURUNDI',
  'AFRICA-DJIBOUTI',
  'AFRICA-ERITREA',
  'AFRICA-MALI',
  'AFRICA-MAURITANIA',
  'AFRICA-NIGER',
  'AFRICA-RWANDA',
  'AFRICA-SOMALIA',
  'AFRICA-SUDAN',
  'AFRICA-UGANDA',
  'AMERICAS-ARGENTINA',
  'AMERICAS-BOLIVIA',
  'AMERICAS-CENTRAL-AMERICA',
  'AMERICAS-CHILE',
  'AMERICAS-COLOMBIA',
  'AMERICAS-GUYANA',
  'AMERICAS-PERU',
  'ASIA-PACIFIC-BHUTAN',
  'ASIA-PACIFIC-BRUNEI',
  'ASIA-PACIFIC-FIJI',
  'ASIA-PACIFIC-INDONESIA',
  'ASIA-PACIFIC-JAPAN',
  'ASIA-PACIFIC-MALAYSIA',
  'ASIA-PACIFIC-MYANMAR',
  'ASIA-PACIFIC-NORTH-KOREA',
  'ASIA-PACIFIC-PHILIPPINES',
  'ASIA-PACIFIC-SOLOMON-ISLANDS',
  'ASIA-PACIFIC-SOUTH-KOREA',
  'ASIA-PACIFIC-TAIWAN',
  'ASIA-PACIFIC-THAILAND',
  'ASIA-PACIFIC-VIETNAM',
  'EUROPE-ARMENIA',
  'EUROPE-AZERBAIJAN',
  'EUROPE-BOSNIA',
  'EUROPE-ESTONIA',
  'EUROPE-FINLAND',
  'EUROPE-GREENLAND',
  'EUROPE-HUNGARY',
  'EUROPE-KOSOVO',
  'EUROPE-LATVIA',
  'EUROPE-LITHUANIA',
  'EUROPE-SERBIA',
  'EUROPE-SLOVAKIA',
  'EUROPE-SWEDEN',
  'NON-STATE-AL-SHABAAB',
  'NON-STATE-ANTI-JUNTA',
  'NON-STATE-CARTELS',
  'NON-STATE-ETHNIC-MILITIAS',
  'NON-STATE-JIHADISTS',
  'NON-STATE-M23',
  'NON-STATE-OROMIA-LIBERATION-FRONT'
);

COMMIT;

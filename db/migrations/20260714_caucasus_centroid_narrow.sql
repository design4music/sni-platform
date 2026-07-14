-- Narrow region-internal Caucasus atomics to ASIA-CAUCASUS only.
-- Rationale: attribution = (ASIA-CAUCASUS overlap) AND (alias match). Keeping
-- external participant centroids (RUSSIA/EU/USA/TURKEY) makes discriminating
-- domain aliases (CSTO, EAEU, accession, normalization, energy) leak via
-- non-Caucasus titles that carry those big centroids. Every on-topic title
-- names a Caucasus actor (Armenia/Yerevan/Pashinyan/Baku/Aliyev/Tbilisi), so
-- ASIA-CAUCASUS alone is the correct participant gate.
-- zangezur_corridor stays WIDE on purpose (A2 archetype: toponym-only bundle
-- can't leak, wider scope only helps recall for sub-toponyms not in the anchor).

BEGIN;

UPDATE friction_nodes SET centroid_ids = ARRAY['ASIA-CAUCASUS'], updated_at = now()
WHERE id IN ('armenia_western_pivot','armenia_azerbaijan_settlement',
             'georgia_geopolitical_drift','caucasus_power_competition');

COMMIT;

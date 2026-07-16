-- Russia-Europe theater: centroid-gap fix found during alias audit (Phase 2, step C).
-- The 3 multilateral atomics (deterrence, hybrid, airspace) are effectively
-- co-extensive with the whole alliance response, not a geographic subset --
-- align their centroid_ids to the theater's full participant set (matches
-- the Arctic-lesson pattern: add the missing on-side participant, don't
-- blame the alias). Evidence: audit samples showed on-topic France
-- shadow-fleet-tanker seizures and UK/France defence-spending coverage
-- miscounted as "foreign" purely because those centroids were absent.
-- Sanctions stays target-centric (RUS + EU only) -- not touched here.

UPDATE friction_nodes SET
  centroid_ids = ARRAY['EUROPE-RUSSIA','NON-STATE-EU','NON-STATE-NATO','EUROPE-BALTIC','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-VISEGRAD','EUROPE-NORDIC','AMERICAS-USA'],
  updated_at = now()
WHERE id IN ('russia_nato_deterrence', 'russia_hybrid_warfare', 'russia_airspace_incursions');

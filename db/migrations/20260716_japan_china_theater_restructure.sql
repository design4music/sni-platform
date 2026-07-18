-- japan_china_theater: greenfield structural re-carve (FN_THEATER_BUILD_SPEC 0a step 2)
--
-- Phase 1 grounding (180d, ASIA-JAPAN AND ASIA-CHINA gate, 1032 titles) found the
-- drafted structure aimed at the two smallest themes and missing the three largest:
--   Taiwan question / Takaichi rupture  192  -> no atomic  (ADD)
--   Japan defense expansion             108  -> no atomic  (ADD)
--   Chinese economic restrictions        82  -> no atomic  (ADD)
--   Senkaku + East China Sea maritime     49  -> two atomics (MERGE to one)
--   Wartime memory                       28  -> kept (25 titles exclusive, live monthly)
--
-- Senkaku vs East China Sea cannot be two atomics (spec 2 A2b): toponym counts are
-- Senkaku/Diaoyu 12, East China Sea 5, carrying both 1, continental-shelf/gas 1.
-- No centroid exists for "the East China Sea" to target, so there is no AND to split on.
--
-- Centroid roles: the participant gate is an OVERLAP (OR), so {ASIA-JAPAN, ASIA-CHINA}
-- with a null target means "Japan OR China" (~31k titles). The dyad AND-gate is
-- centroid_ids={ASIA-CHINA} + primary_target=ASIA-JAPAN. Japan (9,362 titles/180d) is
-- the sparser centroid and goes in primary_target so China mega-events (22,725) cannot
-- pass link_events' 50%-of-event-titles rule.
--
-- No bundles/narratives here -- those are steps 3-7. Reversible: no DELETEs.

BEGIN;

-- 1. Theater: re-scope from "maritime disputes" (5% of coverage) to the real rivalry.
--    Drop ASIA-SOUTHKOREA (21/1032 titles = 2%). Keep anchor_point.
UPDATE friction_nodes
   SET name_en = 'Japan-China strategic rivalry',
       centroid_ids = ARRAY['ASIA-JAPAN', 'ASIA-CHINA'],
       member_fn_ids = ARRAY[
         'japan_china_taiwan_question',
         'japan_defense_expansion',
         'china_japan_economic_restrictions',
         'senkaku_diaoyu_islands',
         'japan_china_memory_wars'
       ],
       updated_at = now()
 WHERE id = 'japan_china_theater';

-- 2. MERGE: senkaku_diaoyu_islands absorbs east_china_sea_claims and re-scopes to
--    the maritime grey-zone friction as a whole (CCG patrols, EEZ, survey ships,
--    drilling structures, Yonaguni). Fixes the OR-gate bug in its centroid config.
UPDATE friction_nodes
   SET name_en = 'Senkaku/Diaoyu islands and East China Sea maritime friction',
       centroid_ids = ARRAY['ASIA-CHINA'],
       primary_target = 'ASIA-JAPAN',
       updated_at = now()
 WHERE id = 'senkaku_diaoyu_islands';

-- 3. RETIRE: merged into senkaku_diaoyu_islands. Deactivate, do not delete.
UPDATE friction_nodes
   SET is_active = false,
       updated_at = now()
 WHERE id = 'east_china_sea_claims';

-- 4. KEEP memory_wars; apply the dyad gate. The ASIA-JAPAN target is load-bearing
--    here: it keeps Korea-Japan comfort-women/textbook coverage out.
UPDATE friction_nodes
   SET name_en = 'Wartime history and historical memory',
       centroid_ids = ARRAY['ASIA-CHINA'],
       primary_target = 'ASIA-JAPAN',
       updated_at = now()
 WHERE id = 'japan_china_memory_wars';

-- 5. ADD the three missing atomics. Prose (description/editorial, bilingual) is
--    step 8; these are shells with correct structure only.
INSERT INTO friction_nodes (id, name_en, fn_type, scope, centroid_ids, primary_target,
                            is_active, display_order)
VALUES
  ('japan_china_taiwan_question',
   'Japan''s role in the Taiwan question',
   'atomic', 'regional', ARRAY['ASIA-CHINA'], 'ASIA-JAPAN', true, 71),
  ('japan_defense_expansion',
   'Japan''s defense expansion and postwar military constraints',
   'atomic', 'regional', ARRAY['ASIA-CHINA'], 'ASIA-JAPAN', true, 72),
  ('china_japan_economic_restrictions',
   'Chinese economic and travel restrictions on Japan',
   'atomic', 'regional', ARRAY['ASIA-CHINA'], 'ASIA-JAPAN', true, 73)
ON CONFLICT (id) DO UPDATE
   SET name_en = EXCLUDED.name_en,
       fn_type = EXCLUDED.fn_type,
       scope = EXCLUDED.scope,
       centroid_ids = EXCLUDED.centroid_ids,
       primary_target = EXCLUDED.primary_target,
       is_active = EXCLUDED.is_active,
       display_order = EXCLUDED.display_order,
       updated_at = now();

COMMIT;

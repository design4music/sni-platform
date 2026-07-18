-- japan_china_theater: static (structural) strategic-asset links.
--
-- Two-tier model (see project_asset_registry memory, D-092): this migration
-- sets the CURATED tier (friction_nodes.affected_asset_ids = home territory /
-- economic levers). The DYNAMIC tier (fn_asset_evidence, news-derived) is a
-- separate mechanical rebuild via scripts/compute_fn_asset_evidence.py, run
-- after this migration -- not curated here.
--
-- Picked one asset per genuinely asset-bearing atomic (3 of 5 -- memory_wars
-- and defense_expansion are not economic/infrastructure disputes, so they
-- structurally contribute none, matching the "less but better" restraint of
-- arctic_theater (3) and taiwan_strait_theater (3) rather than padding):
--   taiwan_strait               -- japan_china_taiwan_question: Japan's MSDF
--                                   Strait transits and Taiwan-contingency
--                                   posture bear directly on this chokepoint.
--                                   Already shared with taiwan_strait_theater
--                                   and us_china_theater -- precedent exists
--                                   for one asset serving multiple theaters
--                                   when genuinely load-bearing to each.
--   bayan_obo_rare_earths       -- china_japan_economic_restrictions: China's
--                                   principal rare-earth complex, the source
--                                   of the export-licensing lever applied to
--                                   Japan (the 2010 embargo precedent named
--                                   directly in cjer_economic_coercion).
--   northwest_pacific_fishing_grounds -- senkaku_diaoyu_islands: the fishing
--                                   grounds where Japan Coast Guard seizures
--                                   of Chinese trawlers recur.
--
-- No East China Sea / Senkaku chokepoint exists in the registry -- checked;
-- it is not a major commercial shipping artery by the registry's inclusion
-- bar (unlike Taiwan Strait / Malacca), so senkaku_diaoyu_islands gets its
-- asset link via the fishing-grounds production cluster instead.

BEGIN;

UPDATE friction_nodes
   SET affected_asset_ids = ARRAY['taiwan_strait', 'bayan_obo_rare_earths', 'northwest_pacific_fishing_grounds'],
       updated_at = now()
 WHERE id = 'japan_china_theater';

COMMIT;

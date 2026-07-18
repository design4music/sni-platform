-- Taiwan Strait theater: greenfield structural re-carve (Phase 1, approved 2026-07-16)
--
-- Structural re-assessment (FN_THEATER_BUILD_SPEC §2a) against 180 days of real
-- ASIA-TAIWAN coverage found the draft atomics were built on stale training data:
--
--   RETIRE  taiwan_sovereignty              -- tautological with the theater itself
--                                              ("sovereignty dispute" inside "Strait
--                                              confrontation"); its real content splits
--                                              into recognition (contest abroad) and
--                                              political warfare (contest inside Taiwan)
--   RETIRE  taiwan_semiconductor_dependence -- 252 Taiwan chip titles / 180d, only ~35
--                                              are Strait friction; rest is earnings and
--                                              AI-supply business news. Chip content is
--                                              already covered by us_china_supply_chains
--                                              + us_china_tech_restrictions, both of
--                                              which already carry ASIA-TAIWAN.
--   ADD     taiwan_us_security_commitment   -- largest real theme (~135-300 titles/180d),
--                                              previously homeless
--   ADD     taiwan_political_warfare        -- second gap (~94-188 titles/180d)
--   KEEP    taiwan_military_pressure        -- re-scoped to absorb grey-zone coercion
--   KEEP    taiwan_international_recognition
--
-- Centroid scoping: ASIA-TAIWAN carries ~2,000 titles/180d while AMERICAS-USA carries
-- 129,306 and ASIA-JAPAN 9,497. The participant gate is therefore a no-op theater-wide
-- and alias purity is the only lever (Arctic A2 pattern). Atomics are scoped to
-- {ASIA-TAIWAN, ASIA-CHINA}; AMERICAS-USA is added only where the US is itself the actor.
--
-- No fn_anchor bundles or narratives_v2 rows exist for any taiwan_* FN (greenfield).
-- Descriptions/editorial summaries are authored in a later step; names only here.

BEGIN;

-- 1. Retire the two atomics that do not carve a distinct phenomenon.
UPDATE friction_nodes
   SET is_active = false, updated_at = now()
 WHERE id IN ('taiwan_sovereignty', 'taiwan_semiconductor_dependence');

-- 2. Re-scope the two surviving atomics.
UPDATE friction_nodes
   SET name_en        = 'Military and grey-zone pressure around Taiwan',
       name_de        = 'Militärischer und hybrider Druck rund um Taiwan',
       centroid_ids   = ARRAY['ASIA-TAIWAN', 'ASIA-CHINA'],
       primary_target = NULL,
       display_order  = 49,
       updated_at     = now()
 WHERE id = 'taiwan_military_pressure';

UPDATE friction_nodes
   SET name_en        = 'International recognition and diplomatic status',
       name_de        = 'Internationale Anerkennung und diplomatischer Status',
       centroid_ids   = ARRAY['ASIA-TAIWAN', 'ASIA-CHINA'],
       primary_target = NULL,
       display_order  = 52,
       updated_at     = now()
 WHERE id = 'taiwan_international_recognition';

-- 3. Add the two atomics covering the themes that had no home.
INSERT INTO friction_nodes
    (id, name_en, name_de, fn_type, scope, centroid_ids, primary_target,
     is_active, display_order, affected_asset_ids, created_at, updated_at)
VALUES
    ('taiwan_us_security_commitment',
     'US security commitment and arms supply',
     'US-Sicherheitszusage und Waffenlieferungen',
     'atomic', 'regional',
     ARRAY['ASIA-TAIWAN', 'AMERICAS-USA'], 'ASIA-TAIWAN',
     true, 50, ARRAY[]::text[], now(), now()),
    ('taiwan_political_warfare',
     'Political influence and united front activity',
     'Politische Einflussnahme und Einheitsfrontarbeit',
     'atomic', 'regional',
     ARRAY['ASIA-TAIWAN', 'ASIA-CHINA'], NULL,
     true, 51, ARRAY[]::text[], now(), now())
ON CONFLICT (id) DO UPDATE
   SET name_en        = EXCLUDED.name_en,
       name_de        = EXCLUDED.name_de,
       fn_type        = EXCLUDED.fn_type,
       scope          = EXCLUDED.scope,
       centroid_ids   = EXCLUDED.centroid_ids,
       primary_target = EXCLUDED.primary_target,
       is_active      = EXCLUDED.is_active,
       display_order  = EXCLUDED.display_order,
       updated_at     = now();

-- 4. Re-point the theater at its four atomics.
UPDATE friction_nodes
   SET member_fn_ids = ARRAY[
           'taiwan_military_pressure',
           'taiwan_us_security_commitment',
           'taiwan_political_warfare',
           'taiwan_international_recognition'
       ],
       centroid_ids  = ARRAY['ASIA-TAIWAN', 'ASIA-CHINA', 'AMERICAS-USA'],
       updated_at    = now()
 WHERE id = 'taiwan_strait_theater';

COMMIT;

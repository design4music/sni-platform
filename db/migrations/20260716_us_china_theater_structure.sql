-- us_china_theater: greenfield structural re-carve (Phase 1 approved 2026-07-16)
--
-- Scope narrowing: the theater and us_china_supply_chains carried an OR over
-- {USA, CHINA, JAPAN, SOUTHKOREA, TAIWAN} = 155,265 titles in 180d scope --
-- essentially the whole US + East-Asia corpus, colliding with taiwan_strait,
-- japan_china and korea on every match. The dyad is trade + tech only; the
-- geographic theaters own the geography.
--
-- Atomics get a true AND gate via the transatlantic_trade pattern:
--   centroid_ids={AMERICAS-USA} + primary_target=ASIA-CHINA
-- => title must carry USA (participant gate) AND China (target gate) = 6,017.
-- Direction is deliberate: link_events requires >=50% of an event's titles to
-- carry primary_target. With CHINA as target the Iran mega-events fail (few of
-- their titles carry China). Reversed (China scope / USA target) they pass,
-- because ~90% of Iran-war titles do carry the USA.
--
-- Structure changes (all reversible; no bundles/narratives/attribution exist yet):
--   ADD       us_china_summit_diplomacy   (~800 titles, dominant homeless theme)
--   ADD       us_china_ai_primacy         (~342 titles, distinct from export controls)
--   RENAME    us_china_supply_chains   -> us_china_critical_minerals (was a category, not a phenomenon)
--   DEACTIVATE us_china_investment_screening (6 titles/180d; premise inverted --
--             2026 story is China blocking Meta-Manus + curbing OUTBOUND investment,
--             not CFIUS screening Chinese money)

BEGIN;

-- 1. Rename supply_chains -> critical_minerals (no FK children exist yet:
--    event_friction_nodes and narratives_v2 are empty for us_china%).
UPDATE friction_nodes
   SET id = 'us_china_critical_minerals',
       name_en = 'Critical minerals leverage',
       updated_at = now()
 WHERE id = 'us_china_supply_chains';

-- 2. Deactivate the fossil atomic (kept, not deleted -- ON DELETE CASCADE risk).
UPDATE friction_nodes
   SET is_active = false,
       updated_at = now()
 WHERE id = 'us_china_investment_screening';

-- 3. Two new atomics.
INSERT INTO friction_nodes (id, name_en, fn_type, scope, centroid_ids, primary_target, is_active, display_order)
VALUES
  ('us_china_summit_diplomacy', 'Summit diplomacy and relationship management',
   'atomic', 'regional', ARRAY['AMERICAS-USA'], 'ASIA-CHINA', true, 89),
  ('us_china_ai_primacy', 'Artificial intelligence primacy race',
   'atomic', 'regional', ARRAY['AMERICAS-USA'], 'ASIA-CHINA', true, 94)
ON CONFLICT (id) DO NOTHING;

-- 4. Rename tech_restrictions to name the instrument precisely.
UPDATE friction_nodes
   SET name_en = 'Export controls and semiconductor access',
       updated_at = now()
 WHERE id = 'us_china_tech_restrictions';

-- 5. Dyad AND gate on every active atomic.
UPDATE friction_nodes
   SET centroid_ids = ARRAY['AMERICAS-USA'],
       primary_target = 'ASIA-CHINA',
       updated_at = now()
 WHERE id IN ('us_china_trade_tariffs',
              'us_china_tech_restrictions',
              'us_china_critical_minerals',
              'us_china_summit_diplomacy',
              'us_china_ai_primacy');

-- 6. Theater: pure aggregator (no bundle, never matches). centroid_ids is
--    display/participants only -- drop Japan/Korea/Taiwan, keep the dyad.
UPDATE friction_nodes
   SET centroid_ids = ARRAY['AMERICAS-USA', 'ASIA-CHINA'],
       primary_target = NULL,
       member_fn_ids = ARRAY['us_china_summit_diplomacy',
                             'us_china_trade_tariffs',
                             'us_china_tech_restrictions',
                             'us_china_ai_primacy',
                             'us_china_critical_minerals'],
       updated_at = now()
 WHERE id = 'us_china_theater';

COMMIT;

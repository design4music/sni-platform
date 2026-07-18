-- australia_china_theater -> australia_theater: structural re-carve (spec 2a).
--
-- Phase 1 assessment against 180d of real coverage (OCEANIA-* centroids, 4,564
-- titles, only 334 co-tagging China) found the draft was built on a 2021 premise:
--
--  * aukus_security_alignment was premised as an Australia-China alignment topic.
--    Only 3 of 70 AUKUS titles carry the China centroid; 29 carry Australia alone.
--    The real story is Australia-US and domestic (second-hand Virginia-class subs,
--    Labor's split, the AUKUS inquiry). Re-scoped, China gate removed.
--  * china_australia_economic_coercion encoded the 2020-21 barley/wine/coal bans.
--    That phase is over (wine back, new beef licences granted). The live story is
--    quota mechanics and commodity pricing leverage running both ways. Re-scoped
--    and renamed -- "coercion" is also a framing word (neutral-prose rule).
--  * pacific_island_alignment carried only OCEANIA-MELANESIA, so it could not see
--    the July 2026 escalation peak (missile splashdown near Nauru/Tuvalu =
--    MICRONESIA/POLYNESIA). Centroid gap fixed.
--  * China's military reach had no home; it folds into the Pacific contest (the
--    missile test is the response to the Australia-Fiji pact -- same event chain).
--    The non-Pacific residual (~6 Lowy/ASPI strike-capacity titles) joins the new
--    espionage atomic: both are the threat-perception contest, and Chinese state
--    media rebut both with the same "'China threat' hype" line.
--  * No critical-minerals atomic: 68 titles but only 12 touch China; the rest is
--    Australia-US supply chain + mining-corporate noise. China-facing slice folds
--    into the trade atomic.
--
-- Theater re-scoped from a dyad to subject-anchored (precedent: turkey_theater,
-- iran_theater, cuba_theater), because Australia's two largest strategic themes
-- (AUKUS 70, minerals 68) are Australia-US, not Australia-China, and a strict
-- dyad theater has no home for them.
--
-- Safe to rename ids: zero event_friction_nodes rows, zero narratives_v2 rows,
-- zero code references. Greenfield -- no attribution to lose.
SET client_encoding TO 'UTF8';

-- ===================== ids + names + centroid roles =====================

-- 1. Pacific island contest (A2 toponym gate -- the island names carry the
--    precision, so participants widen freely and primary_target stays null).
UPDATE friction_nodes SET
  id = 'pacific_island_contest',
  name_en = 'Contest for alignment of Pacific island states',
  centroid_ids = ARRAY['OCEANIA-AUSTRALIA','OCEANIA-MELANESIA','OCEANIA-POLYNESIA',
                       'OCEANIA-MICRONESIA','OCEANIA-PAPUANEWGUINEA','OCEANIA-NEWZEALAND',
                       'ASIA-CHINA'],
  primary_target = NULL,
  display_order = 1,
  updated_at = NOW()
WHERE id = 'pacific_island_alignment';

-- 2. Trade and commodity leverage (dyad AND-gate: participants = the denser
--    centroid, primary_target = the sparser one, per us_china/japan_china).
UPDATE friction_nodes SET
  id = 'australia_china_trade_leverage',
  name_en = 'Trade dependence and commodity leverage',
  centroid_ids = ARRAY['ASIA-CHINA'],
  primary_target = 'OCEANIA-AUSTRALIA',
  display_order = 2,
  updated_at = NOW()
WHERE id = 'china_australia_economic_coercion';

-- 3. AUKUS (A2: the acronym is a near-perfect gate; no China involvement, so no
--    dyad gate -- one would cut it to 3 titles).
UPDATE friction_nodes SET
  id = 'aukus_alliance_reliability',
  name_en = 'AUKUS submarine programme and alliance reliability',
  centroid_ids = ARRAY['OCEANIA-AUSTRALIA','AMERICAS-USA','EUROPE-UK','NON-STATE-NATO'],
  primary_target = NULL,
  display_order = 3,
  updated_at = NOW()
WHERE id = 'aukus_security_alignment';

-- 4. NEW: espionage allegations + threat assessment (dyad AND-gate -- without it,
--    "spies"/"espionage" runs across all 4,564 Australian titles and catches
--    Iran-backed terrorism, ISIS, ransomware, the antisemitism inquiry).
INSERT INTO friction_nodes
  (id, name_en, fn_type, centroid_ids, primary_target, scope, is_active,
   display_order, affected_asset_ids, created_at, updated_at)
VALUES
  ('china_threat_assessment',
   'Espionage allegations and China threat assessment',
   'atomic',
   ARRAY['ASIA-CHINA'],
   'OCEANIA-AUSTRALIA',
   'regional',
   true,
   4,
   ARRAY[]::text[],
   NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ===================== theater =====================
-- Drop ASIA-JAPAN / ASIA-SOUTHKOREA (not parties to this terrain).
-- centroid_ids[0] must stay OCEANIA-AUSTRALIA -- it drives region derivation.
-- anchor_point was null, which kept the theater off the homepage conflicts map
-- (that layer needs scope='regional' AND a non-null anchor_point).
UPDATE friction_nodes SET
  id = 'australia_theater',
  name_en = 'Australia as a contested middle power',
  centroid_ids = ARRAY['OCEANIA-AUSTRALIA','ASIA-CHINA','AMERICAS-USA',
                       'OCEANIA-MELANESIA','OCEANIA-POLYNESIA','OCEANIA-MICRONESIA',
                       'OCEANIA-PAPUANEWGUINEA'],
  primary_target = NULL,
  member_fn_ids = ARRAY['pacific_island_contest','australia_china_trade_leverage',
                        'aukus_alliance_reliability','china_threat_assessment'],
  anchor_point = '{"type":"Point","coordinates":[149.13,-35.28]}'::jsonb,
  updated_at = NOW()
WHERE id = 'australia_china_theater';

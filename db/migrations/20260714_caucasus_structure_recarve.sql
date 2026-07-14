-- Caucasus theater structural re-carve (Phase 1 -> Phase 2 structure apply)
-- Greenfield: no bundles, no narratives, nothing attributed. Fully reversible.
--
-- Fixes (approved 2026-07-14):
--   1. CENTROID ERROR: phantom EUROPE-ARMENIA / EUROPE-AZERBAIJAN (0 titles)
--      replaced by the real single region centroid ASIA-CAUCASUS.
--   2. COVERAGE GAP: add armenia_western_pivot (dominant live cluster, ~124+/180d).
--   3. STALENESS: deactivate nagorno_karabakh_aftermath (0-5 titles/180d).
--   4. SCOPE: rescope caucasus_power_competition to external-actor jockeying.
--   5. RESILIENCE (user): armenia_azerbaijan_settlement becomes a war-or-peace
--      container; add georgia_geopolitical_drift as a durable placeholder;
--      extend ASIA-CAUCASUS anchor with Georgia terms so it can attribute.
--
-- NOTE: ids kept stable (armenia_azerbaijan_settlement, caucasus_power_competition)
-- even where scope broadened, to avoid FK/Render-sync drift. Display names accurate.
-- Rich description_en/de + editorial_summary_en/de deferred to the §6 completeness
-- step after narratives; names set bilingually now.

BEGIN;

-- ---------------------------------------------------------------------------
-- NEW ATOMIC: Armenia's realignment (the theater's namesake, homeless before)
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes
  (id, fn_type, scope, is_active, display_order, primary_target, centroid_ids, name_en, name_de)
VALUES
  ('armenia_western_pivot', 'atomic', 'regional', true, 41, NULL,
   ARRAY['ASIA-CAUCASUS','EUROPE-RUSSIA','NON-STATE-EU','AMERICAS-USA'],
   'Armenia''s realignment away from Russia',
   'Armeniens Abkehr von Russland')
ON CONFLICT (id) DO UPDATE SET
  fn_type = EXCLUDED.fn_type, scope = EXCLUDED.scope, is_active = EXCLUDED.is_active,
  display_order = EXCLUDED.display_order, primary_target = EXCLUDED.primary_target,
  centroid_ids = EXCLUDED.centroid_ids, name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
  updated_at = now();

-- ---------------------------------------------------------------------------
-- NEW ATOMIC: Georgia placeholder (durable fault line; thin now, ready to flare)
-- ---------------------------------------------------------------------------
INSERT INTO friction_nodes
  (id, fn_type, scope, is_active, display_order, primary_target, centroid_ids, name_en, name_de)
VALUES
  ('georgia_geopolitical_drift', 'atomic', 'regional', true, 43, NULL,
   ARRAY['ASIA-CAUCASUS','EUROPE-RUSSIA','NON-STATE-EU','NON-STATE-NATO'],
   'Georgia''s geopolitical drift and Russia''s shadow',
   'Georgiens geopolitische Drift und Russlands Schatten')
ON CONFLICT (id) DO UPDATE SET
  fn_type = EXCLUDED.fn_type, scope = EXCLUDED.scope, is_active = EXCLUDED.is_active,
  display_order = EXCLUDED.display_order, primary_target = EXCLUDED.primary_target,
  centroid_ids = EXCLUDED.centroid_ids, name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
  updated_at = now();

-- ---------------------------------------------------------------------------
-- RESCOPE: bilateral dyad -> war-or-peace container (+ Armenia-Turkey track)
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  centroid_ids = ARRAY['ASIA-CAUCASUS','MIDEAST-TURKEY','EUROPE-RUSSIA','NON-STATE-EU'],
  name_en = 'Armenia-Azerbaijan conflict and peace settlement',
  name_de = 'Konflikt und Friedensregelung zwischen Armenien und Aserbaidschan',
  display_order = 42, primary_target = NULL, updated_at = now()
WHERE id = 'armenia_azerbaijan_settlement';

-- ---------------------------------------------------------------------------
-- FIX CENTROIDS: Zangezur corridor (keep scope; add Russia/USA now central)
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  centroid_ids = ARRAY['ASIA-CAUCASUS','MIDEAST-TURKEY','MIDEAST-IRAN','EUROPE-RUSSIA','AMERICAS-USA'],
  name_en = 'Zangezur corridor and regional connectivity',
  name_de = 'Sangesur-Korridor und regionale Konnektivität',
  display_order = 44, primary_target = NULL, updated_at = now()
WHERE id = 'zangezur_corridor';

-- ---------------------------------------------------------------------------
-- RESCOPE: Russia-Turkey-Iran -> external power competition (incl. EU/US/Israel)
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  centroid_ids = ARRAY['ASIA-CAUCASUS','EUROPE-RUSSIA','MIDEAST-TURKEY','MIDEAST-IRAN','MIDEAST-ISRAEL','AMERICAS-USA','NON-STATE-EU'],
  name_en = 'External power competition over the South Caucasus',
  name_de = 'Wettbewerb externer Mächte um den Südkaukasus',
  display_order = 45, primary_target = NULL, updated_at = now()
WHERE id = 'caucasus_power_competition';

-- ---------------------------------------------------------------------------
-- DEACTIVATE: stale NK-aftermath (residual folded into settlement container)
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  is_active = false, display_order = 46, updated_at = now()
WHERE id = 'nagorno_karabakh_aftermath';

-- ---------------------------------------------------------------------------
-- THEATER: fix centroids, refresh members (drop deactivated NK), name_de
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  centroid_ids = ARRAY['ASIA-CAUCASUS','EUROPE-RUSSIA','MIDEAST-TURKEY','MIDEAST-IRAN','MIDEAST-ISRAEL','AMERICAS-USA','NON-STATE-EU','NON-STATE-NATO'],
  member_fn_ids = ARRAY['armenia_western_pivot','armenia_azerbaijan_settlement','georgia_geopolitical_drift','zangezur_corridor','caucasus_power_competition'],
  name_de = 'Neuordnung des Südkaukasus',
  updated_at = now()
WHERE id = 'caucasus_theater';

-- ---------------------------------------------------------------------------
-- CENTROID ANCHOR: extend ASIA-CAUCASUS (South Caucasus) with Georgia terms.
-- Unambiguous only (omit bare EN "Georgia" -> US-state collision). EN/DE/RU.
-- ---------------------------------------------------------------------------
UPDATE taxonomy_v3 SET
  aliases = jsonb_set(
              jsonb_set(
                jsonb_set(aliases, '{en}',
                  (aliases->'en') || '["Tbilisi","Sakartvelo","Georgian","Abkhazia","South Ossetia","Adjara"]'::jsonb),
                '{de}',
                  (aliases->'de') || '["Tiflis","Georgien","georgisch","Abchasien","Südossetien"]'::jsonb),
              '{ru}',
                (aliases->'ru') || '["Тбилиси","Грузия","Грузии","Абхазия","Южная Осетия"]'::jsonb),
  updated_at = now()
WHERE taxonomy_function = 'centroid_anchor'
  AND centroid_id = 'ASIA-CAUCASUS'
  AND item_raw = 'ASIA-CAUCASUS A: Geographic & Identity Anchors';

UPDATE taxonomy_v3 SET
  aliases = jsonb_set(
              jsonb_set(
                jsonb_set(aliases, '{en}',
                  (aliases->'en') || '["Ivanishvili","Kobakhidze","Kavelashvili","Georgian Dream"]'::jsonb),
                '{de}',
                  (aliases->'de') || '["Iwanischwili","Kobachidse","Georgischer Traum"]'::jsonb),
              '{ru}',
                (aliases->'ru') || '["Иванишвили","Кобахидзе","Грузинская мечта"]'::jsonb),
  updated_at = now()
WHERE taxonomy_function = 'centroid_anchor'
  AND centroid_id = 'ASIA-CAUCASUS'
  AND item_raw = 'ASIA-CAUCASUS B: Political Leadership & Power Figures';

COMMIT;

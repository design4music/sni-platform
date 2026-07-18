-- Centroid-role corrections found while drafting bundles (spec 4: "diagnose the
-- gate before you write the vocabulary").
--
-- pacific_island_contest: NOT a clean A2 after all. Bare island toponyms are only
-- ~63% on-topic (a random 35-title read returned earthquakes, cyclones, the Nauru
-- name change, the Nauru deportee story, a waste incinerator) -- unlike Arctic's
-- `Greenland` at ~95%. But the island centroids turn out to be an excellent
-- terrain gate: of every title mentioning Fiji/Vanuatu/Solomon Islands/Nauru/
-- Tuvalu/Kiribati in 180d, exactly ONE lacks an island centroid. So gate on the
-- islands as terrain and let the bundle carry the phenomenon.
-- AUSTRALIA/CHINA/NEWZEALAND are REMOVED from participants: aliases are OR'd, so
-- including them would let any Australia- or China-only title carrying a bundle
-- word (`pact`, `base`, `treaty`) attribute. Australia-Pacific titles reach the FN
-- via the island centroid they already carry.
UPDATE friction_nodes SET
  centroid_ids = ARRAY['OCEANIA-MELANESIA','OCEANIA-POLYNESIA','OCEANIA-MICRONESIA',
                       'OCEANIA-PAPUANEWGUINEA'],
  primary_target = NULL,
  updated_at = NOW()
WHERE id = 'pacific_island_contest';

-- aukus_alliance_reliability: narrow participants to Australia alone. With
-- {USA, UK, NATO} as participants the OR-gate would let any US/UK submarine story
-- worldwide attribute on a `submarine` alias. Every AUKUS title in 180d carries
-- OCEANIA-AUSTRALIA, so Australia alone loses nothing and makes the bundle safe.
-- This is the true A2 of this theater: `AUKUS` is a near-perfect gate (70 titles),
-- so no domain verbs and no target.
UPDATE friction_nodes SET
  centroid_ids = ARRAY['OCEANIA-AUSTRALIA'],
  primary_target = NULL,
  updated_at = NOW()
WHERE id = 'aukus_alliance_reliability';

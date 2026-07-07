-- Fix iran_theater.affected_asset_ids: it was wired to ras_tanura and
-- ghawar_field -- both SAUDI assets, not Iranian -- while every genuinely
-- Iran-located registry asset (Bushehr NPP, South Pars, Ahvaz-Marun,
-- Gachsaran) was missing. Caught via user review comparing the live
-- iran_theater page against South Pars Field on the map.
--
-- This is the worked example for the "home territory" principle: for a
-- theater whose primary actor IS its only real participant (centroid_ids
-- = a single country), affected_asset_ids should mechanically be every
-- active strategic_asset whose centroid_ids includes that country --
-- not a hand-picked subset, and never an asset from a DIFFERENT country.
-- strait_of_hormuz correctly stays (its centroid_ids includes MIDEAST-IRAN
-- alongside MIDEAST-GULF -- it IS partly Iran's shoreline).
--
-- Systematic backfill of this rule across the other 26 theaters lacking
-- primary_target is a separate follow-up (see chat) -- most have multiple
-- participant centroids where "all assets in all centroids" would flood
-- the theater with irrelevant assets, so each needs the same "home
-- territory vs. commentary participant" judgment call applied deliberately,
-- not a single blanket query.

UPDATE friction_nodes SET
  affected_asset_ids = ARRAY['strait_of_hormuz','bushehr_npp','south_pars_field','ahvaz_marun_fields','gachsaran_field'],
  updated_at = now()
WHERE id = 'iran_theater';

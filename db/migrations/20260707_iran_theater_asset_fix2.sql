-- Second pass on iran_theater.affected_asset_ids, per the "named mechanism"
-- framework (see chat 2026-07-07): the first fix removed ras_tanura for
-- the right reason (it's Saudi, not Iranian home territory) but the wrong
-- conclusion (it should have moved from "home territory" to "demonstrated
-- reach", not been dropped). Verified: Ras Tanura was directly hit by an
-- Iran-attributed drone strike on 2026-03-02 (Euronews, Arab News, Times
-- of Israel), continuing a real pattern (2021 Houthi strike on Ras
-- Tanura; 2019 Abqaiq-Khurais). Reinstated on that dated evidence.
-- ghawar_field has no equivalent direct-strike evidence found and stays
-- excluded -- co-location in the Gulf region is not sufficient grounds.

UPDATE friction_nodes SET
  affected_asset_ids = ARRAY['strait_of_hormuz','bushehr_npp','south_pars_field','ahvaz_marun_fields','gachsaran_field','ras_tanura'],
  updated_at = now()
WHERE id = 'iran_theater';

-- Completes 20260717_australia_theater_restructure.sql, whose final statement
-- (the theater rename) failed on fn_asset_evidence_fn_id_fkey. The four atomic
-- statements had already committed.
--
-- The blocker is a single DERIVED row: australia_china_theater -> strait_of_hormuz
-- (computed 2026-07-08 by scripts/compute_fn_asset_evidence.py). fn_asset_evidence
-- is a regenerable news-evidence cache, not source data, and this row is junk --
-- Hormuz is not an Australian asset; it came from Australia titles co-tagging
-- MIDEAST-IRAN, the same centroid noise the re-carve is meant to gate out.
-- Re-running compute_fn_asset_evidence.py rebuilds this table.
SET client_encoding TO 'UTF8';

DELETE FROM fn_asset_evidence WHERE fn_id = 'australia_china_theater';

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

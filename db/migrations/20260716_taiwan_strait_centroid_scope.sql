-- Taiwan Strait theater: tighten atomic centroid scope to ASIA-TAIWAN only
-- (FN_THEATER_BUILD_SPEC §2 / §4 centroid-role step, 2026-07-16)
--
-- Empirical basis, 180 days of titles_v3:
--   titles matching /Taiwan|Taipei|台湾|台灣|Тайвань|تايوان/ that CARRY  ASIA-TAIWAN: 1764
--   titles matching the same that are MISSING ASIA-TAIWAN:                            15
-- ASIA-TAIWAN tagging is therefore ~99.2% complete for Taiwan-mentioning coverage, so
-- the participant gate alone bounds the theater to a ~2,000-title universe.
--
-- By contrast AMERICAS-USA carries 129,306 titles/180d and ASIA-CHINA 23,093. Including
-- either as a participant buys no recall (their Taiwan content already carries
-- ASIA-TAIWAN) and only widens the surface for generic aliases to leak. Dropping them
-- makes domain vocabulary (drill, coast guard, arms sale, united front) safe by
-- cross-filtering -- the Archetype-A mechanic, with the participant gate doing the work
-- the target gate does elsewhere.
--
-- primary_target stays NULL on all four: with centroid_ids = {ASIA-TAIWAN} every matched
-- title already carries ASIA-TAIWAN, so a target gate is a no-op. A US target gate on
-- taiwan_us_security_commitment was tested and rejected -- only 100 of 108 real arms
-- titles carry AMERICAS-USA, so it would drop ~7% of legitimate content while the
-- US-specific aliases already supply the precision.
--
-- Cross-theater leak into scs_theater / japan_china_theater is structurally near-
-- impossible under this scope: those titles do not carry ASIA-TAIWAN. Expect
-- audit_fn_anchor_aliases.py to report high "%foreign" against ASIA-CHINA and
-- AMERICAS-USA -- that is benign co-mention (China and the US are participants in the
-- phenomenon), not leak. Do not prune aliases on that percentage alone.

BEGIN;

UPDATE friction_nodes
   SET centroid_ids   = ARRAY['ASIA-TAIWAN'],
       primary_target = NULL,
       updated_at     = now()
 WHERE id IN (
     'taiwan_military_pressure',
     'taiwan_us_security_commitment',
     'taiwan_political_warfare',
     'taiwan_international_recognition'
 );

COMMIT;

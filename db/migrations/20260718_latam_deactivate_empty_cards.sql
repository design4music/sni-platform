-- Deactivate the two narratives that measured exactly zero titles.
--
-- Finding: the US conservative/security publisher bloc is effectively absent
-- from South American coverage in this corpus. 'latam_theater_leverage_works'
-- and 'trade_pressure_enforcement_justified' both matched 0 titles, and
-- friction-nodes.ts applies no match_count filter before rendering, so they
-- would ship as empty cards.
--
-- Rows are KEPT (is_active=false), not deleted: the coalitions and framing are
-- already authored, so if that bloc starts covering the region this is a
-- one-line reactivation. The near-empty-but-nonzero cards
-- (latam_theater_strategic_warning at 1, resource_extractivism_critique at 1)
-- stay active.

UPDATE narratives_v2
SET is_active = false, updated_at = now()
WHERE id IN ('latam_theater_leverage_works', 'trade_pressure_enforcement_justified');

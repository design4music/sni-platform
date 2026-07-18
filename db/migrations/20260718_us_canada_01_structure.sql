-- us_canada_theater greenfield structural build (FN_THEATER_BUILD_SPEC §0a step 2).
-- Approved decomposition (Phase 1 structural re-assessment, 2026-07-18):
--   us_canada_trade_coercion    dyad AND   tariffs / USMCA / decertification / retaliation
--   canada_sovereignty_pressure dyad AND   annexation talk / bridge coercion / national response
--   alberta_separatism_us_ties  CA-gated   secession push + US contacts (A2 name-gate)
--
-- Gating rationale (measured over 180d, AMERICAS-CANADA = 3765 titles):
--   * Dyad AND = centroid_ids={AMERICAS-USA} + primary_target=AMERICAS-CANADA.
--     CANADA is the sparser centroid so it goes in primary_target (us_china
--     lesson). Trade co-tags USA at 76%, sovereignty at 54% -> both survive it.
--   * alberta_separatism_us_ties deliberately does NOT take the dyad AND:
--     only 33% of separatism coverage co-tags USA, and a dyad gate cuts it
--     73 -> 24 titles, deleting the Canadian domestic constitutional reporting
--     that carries the story. Gated on CANADA alone; the A2-class name anchors
--     (Alberta separatis- / secession / referendum) supply the precision.
--
-- Rejected atomics (corpus refused them, do not re-add without re-measuring):
--   defence/NORAD/F-35 = 9 titles; digital/tech sovereignty = 3; Great Lakes
--   water = 1. europe_us_theater's defence + tech atomics do NOT generalise here.
--   canada_energy_export_dependence dropped: 78-title pool but only 23% touches
--   the US and the bulk is internal Alberta-BC-Ottawa route politics.
--   Arctic / Northwest Passage (26) stays with arctic_theater -- an atomic lives
--   in the ONE theater whose terrain defines it.
-- Reversible; LOCAL only.
SET client_encoding TO 'UTF8';

-- ---- theater ------------------------------------------------------------
INSERT INTO friction_nodes (
  id, name_en, name_de, fn_type, scope, is_active, display_order,
  centroid_ids, primary_target, member_fn_ids, anchor_point, affected_asset_ids
) VALUES (
  'us_canada_theater',
  'United States-Canada rupture',
  'Bruch zwischen den USA und Kanada',
  'theater', 'regional', true, 112,
  ARRAY['AMERICAS-CANADA','AMERICAS-USA'],
  NULL,
  ARRAY['us_canada_trade_coercion','canada_sovereignty_pressure','alberta_separatism_us_ties'],
  '{"type":"Point","coordinates":[-75.7,45.4]}'::jsonb,
  ARRAY['athabasca_oil_sands','canadian_prairies_wheat','athabasca_basin_uranium']
)
ON CONFLICT (id) DO NOTHING;

-- ---- atomics ------------------------------------------------------------
INSERT INTO friction_nodes (
  id, name_en, name_de, fn_type, scope, is_active, display_order,
  centroid_ids, primary_target
) VALUES
(
  'us_canada_trade_coercion',
  'Tariffs, USMCA renegotiation and trade retaliation',
  'Zölle, USMCA-Neuverhandlung und Handelsvergeltung',
  'atomic', 'regional', true, 113,
  ARRAY['AMERICAS-USA'], 'AMERICAS-CANADA'
),
(
  'canada_sovereignty_pressure',
  'Annexation rhetoric and Canadian sovereignty response',
  'Annexionsrhetorik und kanadische Souveränitätsantwort',
  'atomic', 'regional', true, 114,
  ARRAY['AMERICAS-USA'], 'AMERICAS-CANADA'
),
(
  'alberta_separatism_us_ties',
  'Alberta separatism and its United States contacts',
  'Separatismus in Alberta und seine Kontakte in die USA',
  'atomic', 'regional', true, 115,
  ARRAY['AMERICAS-CANADA','AMERICAS-USA'], 'AMERICAS-CANADA'
)
ON CONFLICT (id) DO NOTHING;

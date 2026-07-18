-- colombia_theater: greenfield structure (FN_THEATER_BUILD_SPEC 0a, step 2).
--
-- Confirmed greenfield: no friction_nodes, narratives_v2 or taxonomy_v3
-- fn_anchor row referenced Colombia before this migration. Colombia is also
-- effectively unclaimed by neighbouring theaters -- only ~29 Colombia titles
-- are attributed anywhere in the system, and venezuela_theater holds 2 -- so
-- there is no dual-homing to unpick.
--
-- Gate design: centroid_ids = {AMERICAS-ANDEAN} only. Colombia has no centroid
-- of its own; ANDEAN covers CO/EC/BO/PE/GY and Colombia is 651 of its 1,498
-- titles. 91% of Colombia-mentioning titles carry ANDEAN, so the centroid is a
-- reliable scope. Because ANDEAN is multi-country, the country name itself
-- becomes legitimate sub-centroid geography in the bundles (the MIDEAST-LEVANT
-- edge case in FN_ANCHOR_VOCABULARY_SPEC pillar 2) -- the bundles carry
-- 'Colombia'/'colombiano', which they would NOT if Colombia had its own
-- centroid.
--
-- AMERICAS-USA is deliberately NOT a participant: it would admit all 134k US
-- titles through the participant gate, and it is unnecessary because Colombia
-- titles involving Washington carry ANDEAN anyway.
--
-- primary_target stays NULL on all three: ANDEAN is the sole participant, so a
-- target gate on the same centroid is a no-op.

BEGIN;

INSERT INTO friction_nodes (id, name_en, fn_type, scope, centroid_ids, primary_target, is_active, anchor_point, member_fn_ids) VALUES
(
    'colombia_theater',
    'Colombia',
    'theater',
    'regional',
    ARRAY['AMERICAS-ANDEAN'],
    NULL,
    true,
    '{"type":"Point","coordinates":[-74.1,4.7]}'::jsonb,
    ARRAY['colombia_us_alignment', 'colombia_political_transition', 'colombia_armed_groups_peace']
),
(
    'colombia_us_alignment',
    'Alignment with Washington',
    'atomic',
    'regional',
    ARRAY['AMERICAS-ANDEAN'],
    NULL,
    true,
    NULL,
    NULL
),
(
    'colombia_political_transition',
    'Presidential transition and institutional contest',
    'atomic',
    'regional',
    ARRAY['AMERICAS-ANDEAN'],
    NULL,
    true,
    NULL,
    NULL
),
(
    'colombia_armed_groups_peace',
    'Armed groups and the peace process',
    'atomic',
    'regional',
    ARRAY['AMERICAS-ANDEAN'],
    NULL,
    true,
    NULL,
    NULL
)
ON CONFLICT (id) DO NOTHING;

COMMIT;

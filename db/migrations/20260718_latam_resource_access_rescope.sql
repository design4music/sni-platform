-- Re-scope atomic 1 from China-only to actor-neutral resource access.
--
-- Audit finding (FN_THEATER_BUILD_SPEC 0a step 3): the mineral-vocabulary
-- corpus in the South American centroids is dominated by NON-Chinese external
-- competition -- "US in talks with Brazil on critical minerals", "EU courts
-- Brazil as strategic partner in global race for critical minerals", "Brazil,
-- India ink critical minerals deal", "US snubbed by Lula government at critical
-- minerals summit", "EE.UU. suma a la Argentina a un pacto global sobre
-- minerales". A China-only atomic would have to drop that vocabulary entirely
-- (falling to ~25 titles) or misfile US/EU/India competition as Chinese access.
--
-- Actor-neutral scope matches the re-scoped theater ("External powers in Latin
-- America") and keeps the Chinese operators as one vector among several.
-- Still safe to rename as a plain UPDATE: zero rows in narratives_v2,
-- event_friction_nodes, fn_asset_evidence for this id. The taxonomy_v3
-- fn_anchor row is repointed explicitly below.

BEGIN;

UPDATE friction_nodes
SET id = 'latam_resource_access',
    name_en = 'Critical minerals and infrastructure access',
    updated_at = now()
WHERE id = 'latam_china_access';

UPDATE taxonomy_v3
SET linked_id = 'latam_resource_access',
    item_raw = 'latam_resource_access fn_anchor',
    updated_at = now()
WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'latam_china_access';

UPDATE friction_nodes
SET member_fn_ids = array_replace(member_fn_ids, 'latam_china_access', 'latam_resource_access'),
    updated_at = now()
WHERE id = 'latam_hemispheric_theater';

COMMIT;

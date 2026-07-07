-- Fix: 20260707_latam_theater_split.sql wired Panama FNs to
-- AMERICAS-CENTRAL-AMERICA, but the pipeline actually tags Panama/canal
-- coverage as AMERICAS-CENTRAL (a pre-existing duplicate centroid pair in
-- centroids_v3, same label "Central America", both active -- not this
-- migration's problem to resolve, only to route around). Caught during
-- fn_anchor extraction for panama_ports_dispute: 0 headlines returned
-- against AMERICAS-CENTRAL-AMERICA despite confirmed corpus coverage.
-- Same silent-attribution-failure pattern as the Iran dormant bug --
-- wrong centroid wiring produces zero events forever with no error.

UPDATE friction_nodes
SET centroid_ids = array_replace(centroid_ids, 'AMERICAS-CENTRAL-AMERICA', 'AMERICAS-CENTRAL'),
    primary_target = CASE WHEN primary_target = 'AMERICAS-CENTRAL-AMERICA' THEN 'AMERICAS-CENTRAL' ELSE primary_target END,
    updated_at = now()
WHERE 'AMERICAS-CENTRAL-AMERICA' = ANY(centroid_ids);

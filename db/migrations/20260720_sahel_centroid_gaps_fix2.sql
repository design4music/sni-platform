-- Sahel: correction to 20260720_sahel_centroid_gaps.sql (2026-07-20).
--
-- That migration added NON-STATE-ISIS and NON-STATE-AL-QAEDA to
-- sahel_jihadist_insurgency to close a centroid gap. Measuring the result
-- showed it OVERCORRECTED: those two centroids are GLOBAL, not Sahelian.
-- They carry 624 titles/180d of which only 96 touch any Sahel-linked centroid,
-- so the atomic was pulling Syrian-camp, Iraqi and European-trial coverage
-- ("Une femme rejugée à Paris pour avoir rejoint le groupe État islamique en
-- Syrie", "Australia rules out helping families of IS militants leave Syrian
-- camp"). Title count was 417, far above the ~180 the theme supports.
--
-- NON-STATE-BOKO-HARAM is kept: unlike ISIS and al-Qaeda it IS geographically
-- specific to the Lake Chad basin, which is this atomic's terrain.
--
-- The 'Islamic State' and 'al Qaeda' aliases stay in the bundle. With the
-- global centroids removed they now fire only on titles that ALSO carry
-- AFRICA-SAHEL / AFRICA-NIGERIA / NON-STATE-BOKO-HARAM / NON-STATE-JIHADISTS --
-- which is the conjunction that was wanted in the first place.
--
-- Lesson worth keeping: "add the participant centroid" is the right move for an
-- actor whose centroid is CO-EXTENSIVE with the FN's terrain, and the wrong move
-- for a globally-distributed actor. Check the centroid's own footprint before
-- adding it, not just the %foreign that motivated the fix.

BEGIN;

UPDATE friction_nodes
SET centroid_ids = ARRAY[
        'AFRICA-SAHEL','AFRICA-NIGERIA','NON-STATE-JIHADISTS','NON-STATE-BOKO-HARAM'
    ],
    updated_at = NOW()
WHERE id = 'sahel_jihadist_insurgency';

COMMIT;

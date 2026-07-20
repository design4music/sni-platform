-- Sahel: centroid-gap corrections found during bundle pre-audit (2026-07-20).
-- Spec §4: diagnose leak as a possible CENTROID GAP before blaming aliases.

BEGIN;

-- 1. sahel_jihadist_insurgency -- CENTROID GAP, not leak.
--    Pre-audit: 'Boko Haram' 72 titles at 100% %foreign, 'Islamic State' 16 at
--    100%, 'al Qaeda' 12 at 100%. In every case the "foreign" centroid was
--    NON-STATE-BOKO-HARAM / NON-STATE-ISIS / NON-STATE-AL-QAEDA -- the FN's OWN
--    actors, simply absent from centroid_ids. Adding the participants rather
--    than dropping three of the atomic's most precise anchors.
UPDATE friction_nodes
SET centroid_ids = ARRAY[
        'AFRICA-SAHEL','AFRICA-NIGERIA','NON-STATE-JIHADISTS',
        'NON-STATE-BOKO-HARAM','NON-STATE-ISIS','NON-STATE-AL-QAEDA'
    ],
    updated_at = NOW()
WHERE id = 'sahel_jihadist_insurgency';

-- 2. sahel_security_patron_contest -- the OPPOSITE error: a participant that
--    must NOT be on the OR-gate. With EUROPE-RUSSIA in centroid_ids the audit
--    admitted every Russia title on earth: 'drone' 1702 (EUROPE-UKRAINE:1132),
--    'military cooperation' 13 (North Korea), 'arms' 76, 'training' 43,
--    'withdraw' 37. This is the australia_theater lesson -- gate on the TERRAIN
--    and put the phenomenon in the bundle. Dropping to AFRICA-SAHEL alone takes
--    'Wagner' from 8 titles (Moscow shootouts, European sabotage) to 1 real one.
UPDATE friction_nodes
SET centroid_ids = ARRAY['AFRICA-SAHEL'],
    updated_at = NOW()
WHERE id = 'sahel_security_patron_contest';

COMMIT;

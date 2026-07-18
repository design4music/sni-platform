-- Final tightening of us_commitment_firm. 'parliament approves' was still ambiguous:
-- it matched "Taiwan Parliament approves extra defence spending BUT LESS THAN what the
-- government seeks" -- a shortfall story, which also matched us_commitment_doubted's
-- 'less than' and so landed in both contradictory stances. Dropped; 'parliament
-- authorises' / 'authorises signing' / 'major arms deal' keep the genuine approvals.
BEGIN;
UPDATE narratives_v2
   SET framing_keywords = array_remove(framing_keywords, 'parliament approves'),
       updated_at = now()
 WHERE id = 'us_commitment_firm';
COMMIT;

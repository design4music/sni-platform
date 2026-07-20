-- Same "internal narrator voice" defect flagged on military_pressure and
-- international_recognition (Asana 1216618489706919) also appears here --
-- fixing for consistency within the same theater, same rule.
BEGIN;
UPDATE friction_nodes SET
  editorial_summary_en = replace(
    editorial_summary_en,
    'This node tracks that relationship in both directions.',
    'That relationship runs in both directions.'
  ),
  updated_at = now()
WHERE id = 'taiwan_us_security_commitment';
COMMIT;

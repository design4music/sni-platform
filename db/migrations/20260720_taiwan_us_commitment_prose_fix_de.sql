-- German parallel of the previous fix -- missed on first pass.
BEGIN;
UPDATE friction_nodes SET
  editorial_summary_de = replace(
    editorial_summary_de,
    'Dieser Knoten verfolgt diese Beziehung in beide Richtungen.',
    'Diese Beziehung verlaeuft in beide Richtungen.'
  ),
  updated_at = now()
WHERE id = 'taiwan_us_security_commitment';
COMMIT;

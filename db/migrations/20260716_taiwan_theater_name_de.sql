-- Theater name_de was never set on the original draft row (§6 completeness).
BEGIN;
UPDATE friction_nodes
   SET name_de = 'Konfrontation in der Taiwanstraße', updated_at = now()
 WHERE id = 'taiwan_strait_theater';
COMMIT;

-- Ukraine battlefield: remove colliding Arabic alias (2026-07-10)
-- See generator docstring for full rationale.
BEGIN;

UPDATE taxonomy_v3
   SET aliases = jsonb_set(
         aliases, '{ar}',
         (SELECT jsonb_agg(v) FROM jsonb_array_elements_text(aliases->'ar') v
           WHERE v <> 'شاهد')
       )
 WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'ukraine_battlefield';

COMMIT;

-- Corrects an ASCII-transliteration typo ('verlaeuft') introduced by the
-- previous migration (20260720_taiwan_us_commitment_prose_fix_de.sql), which
-- was authored via a bash heredoc that mangled the umlaut. Native orthography
-- convention (FN_ANCHOR_VOCABULARY_SPEC rule 6c) applies to all DE prose in
-- this system, not just fn_anchor aliases.
BEGIN;
UPDATE friction_nodes SET
  editorial_summary_de = replace(
    editorial_summary_de,
    'Diese Beziehung verlaeuft in beide Richtungen.',
    'Diese Beziehung verläuft in beide Richtungen.'
  ),
  updated_at = now()
WHERE id = 'taiwan_us_security_commitment';
COMMIT;

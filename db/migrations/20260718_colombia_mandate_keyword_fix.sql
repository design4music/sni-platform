-- Fix: colombia_transition_mandate was matching neutral result vocabulary.
--
-- Found by reading samples again after the tuning pass. The card is labelled
-- "A mandate for security / Voters chose a harder line", but it had claimed:
--   "Cepeda reconoció el triunfo del conservador De la Espriella"
--   "De la Espriella es declarado presidente electo de Colombia"
--   "Felicitará Sheinbaum a Presidente electo de Colombia"
--   "Iván Cepeda, el candidato de Petro, concede el triunfo"
-- These are concession and procedural announcements. They matched because
-- 'triunfo', 'victoria', 'ganó', 'elegido' and 'presidente electo' are neutral
-- RESULT words, not stance words -- the same defect as the Mercosur firehose,
-- one layer down: the publisher pool was right but the framing gate let
-- outcome-reporting through as endorsement.
--
-- Keeping only genuinely stance-bearing terms. This shrinks the card, which is
-- correct: much of the transition coverage simply has no stance to carry.

UPDATE narratives_v2 SET
    framing_keywords = ARRAY[
        'mandato','mano dura','seguridad','crackdown','mega-prison','megacárcel',
        'crime','rightward','giro a la derecha','ciclo de Petro','tough on',
        'respaldo','cartel','orden','autoridad'
    ],
    updated_at = now()
WHERE id = 'colombia_transition_mandate';

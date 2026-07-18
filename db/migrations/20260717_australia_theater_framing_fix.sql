-- Framing-keyword fix found by reading actual per-narrative samples (spec step 9,
-- "don't just check the counts look plausible").
--
-- `commitment` is stance-AMBIGUOUS and was putting a critical headline into the
-- SUPPORTIVE AUKUS card: "UK defence committee warns on AUKUS commitment, calls
-- for renewed impetus" (Janes) matched it and filed as aukus_strategic_necessity.
-- Same class as the eu_cohesion `Zusammenarbeit mit der AfD` bug.
--
-- Dropping it leaves that title matching neither framing, so it falls out of both
-- cards -- the intended precision-over-recall behaviour for framing_required
-- narratives. The other 9 supportive titles all match on unambiguous keywords
-- (backs / advance / pledges / savings / won't sink / hits out at).
SET client_encoding TO 'UTF8';

UPDATE narratives_v2 SET
  framing_keywords = array_remove(framing_keywords, 'commitment'),
  updated_at = NOW()
WHERE id = 'aukus_strategic_necessity';

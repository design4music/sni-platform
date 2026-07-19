-- Fix: port_sovereignty_squeeze was capturing neutral escalation reporting (2026-07-19)
--
-- Sample read after the first bootstrap found 3 of its 5 titles were really
-- the +2 stance, pulled in by escalation-DESCRIBING keywords rather than
-- squeeze-CRITICAL ones:
--   "Rubio warns China after Panama ship detentions, calls hemisphere
--    sovereignty 'non-negotiable'"        <- via `hemisphere` (also on the +2 card)
--   "Rubio accuses China of 'bullying' ... after canal clash"  <- via `clash`
--   "China's Cosco halts Panama port operations as tensions rise" <- via `tension`
--   "Panamakanal: Hafenstreit verschärft Spannungen ..."        <- via `Spannung`
-- Same class as the Colombia build's neutral RESULT words leaking into stance
-- narratives. Dropping the neutral escalation terms; keeping only vocabulary
-- that carries the critique itself (US force posture, host state as terrain).
--
-- Expect this card to end up small. Its strongest real evidence -- Bloomberg's
-- "Trump's Aggressive Military Buildup in Panama Is Keeping Latin America on
-- Edge" -- is OUT OF GATE, because it never says "Panama Canal" and bare
-- `Panama` is not alias-safe here (flag-of-convenience noise). Deliberately NOT
-- widening the bundle to reach it: US force posture is a different phenomenon
-- from port-infrastructure control, and precision beats recall.

BEGIN;

UPDATE narratives_v2
SET framing_keywords = ARRAY[
        'on edge', 'flexing', 'military might', 'buildup', 'Aufmarsch',
        'troops', 'Truppen', 'tropas', 'Southern Command',
        'squeez', 'caught between', 'zwischen den Fronten', 'battleground',
        'pressure on Panama', 'Druck auf Panama', 'presión sobre Panamá',
        'strong-arm', 'arm-twist', 'forced to choose', 'zur Wahl gezwungen'
    ],
    updated_at = NOW()
WHERE id = 'port_sovereignty_squeeze';

COMMIT;

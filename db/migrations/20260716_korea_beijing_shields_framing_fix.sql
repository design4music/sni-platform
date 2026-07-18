-- Fix: beijing_shields_pyongyang was mislabelling neutral wire copy.
--
-- Found by reading samples, not counts -- the count (122) looked plausible for
-- an atomic with 86 events. The samples were not: "China's Xi Jinping arrives
-- in North Korea on rare state visit" (Al Jazeera), "First train to Pyongyang
-- in six years leaves Beijing" (Reuters), "What do we know about Xi Jinping's
-- North Korea visit?" (The Australian) were all being filed under a card that
-- claims Beijing's lifeline is what keeps the pressure regime from working.
-- Publisher alone does not carry that stance here: Western/ROK/JP outlets
-- report the visit straight far more often than they argue the patronage case.
--
-- Same class of error as the eu_cohesion framing_required bug (317 -> 12).
-- Fix is the same: framing-gate it, with keywords that are actually
-- stance-bearing (grip, lifeline, leverage, declines to press, mum on) rather
-- than merely topical. Neutral visit reports now drop -- precision over recall.
--
-- The asymmetry with china_dprk_friendship (framing_required stays false) is
-- deliberate and verified: the Chinese state bloc IS stance-saturated here --
-- its straight-faced visit coverage ("friendship steadfast in a turbulent
-- world", "new era", CPV martyr tributes) is the friendship line itself.

BEGIN;

UPDATE narratives_v2
SET framing_required = true,
    framing_keywords = ARRAY[
        'lifeline', 'economy alive', 'grip', 'leverage', 'shield', 'prop up',
        'undercut', 'evasion', 'evade', 'declines to press', 'evita presionar',
        'mum on', 'defiance', 'influence', 'oblige', 'competing for',
        'sanctions relief', 'Einfluss', '影響力'
    ],
    updated_at = NOW()
WHERE id = 'beijing_shields_pyongyang';

COMMIT;

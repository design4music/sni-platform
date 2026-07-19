-- Cuba theater: retire the four unsupported +1 narratives (2026-07-19).
--
-- MEASUREMENT THAT SETTLED IT. Counting Western/Latin-bloc titles that match
-- each atomic's bundle AND carry any regime-fault framing term (castrismo,
-- dictad*, communist rule, must go, teetering, fracas*, arruin*, mismanag*,
-- obsolet*, envejec*):
--
--   atomic                    western titles on atomic   regime-fault framed
--   cuba_embargo_sanctions              212                        1
--   cuba_energy_collapse                198                        0
--   cuba_external_lifelines             126                        0
--   cuba_military_coercion               85                        0
--   cuba_regime_survival                108                        6
--
-- The regime-fault stance does not co-occur with the sanctions, energy,
-- lifelines or military phenomena in headlines at all. It exists only where it
-- belongs -- on the regime atomic, which keeps its full three-stance structure
-- (repression 14 / reform-under-siege 37 / sovereign-resistance 19).
--
-- This is a FINDING, not a tuning failure: in this corpus no significant
-- publisher bloc argues the coercion campaign is right. The live disagreement
-- on those four atomics is between Western-critical (-1) and anti-imperial
-- (-2), which differ over degree and over whom to blame. Two negative
-- narratives on an atomic is the honest shape here; inventing a positive card
-- to look balanced would misrepresent the coverage. Retained, deactivated, so
-- the judgement is reversible if coverage shifts.
--
-- The theater +2 card is re-scoped to match: it now carries the regime-fault
-- axis (which the regime atomic supplies) rather than "the pressure is
-- working" (which nothing supplies).

BEGIN;

UPDATE narratives_v2 SET is_active = false, updated_at = NOW()
WHERE id IN (
    'cuba_pressure_justified',
    'cuba_collapse_self_inflicted',
    'cuba_lifelines_prop_up',
    'cuba_force_credible_threat'
);

UPDATE narratives_v2 SET
 name_en = 'The government, not the blockade, is what has to change',
 name_de = 'Die Regierung, nicht die Blockade, muss sich ändern',
 claim_en = 'A one-party leadership that jails its critics, has run its economy into the ground and refuses to give up power is the reason the island is in this position -- and the reason pressure keeps being applied.',
 claim_de = 'Eine Einparteienführung, die ihre Kritiker einsperrt, die Wirtschaft ruiniert hat und die Macht nicht abgeben will, ist der Grund für die Lage der Insel -- und der Grund, warum weiter Druck ausgeübt wird.',
 stance_label_en = 'The government is the problem',
 stance_label_de = 'Die Regierung ist das Problem',
 updated_at = NOW()
WHERE id = 'cuba_theater_pressure_consensus';

COMMIT;

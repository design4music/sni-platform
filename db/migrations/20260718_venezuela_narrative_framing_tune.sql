-- Venezuela atomic narratives: framing-keyword + coalition tune (2026-07-18).
--
-- §9 skeptical read of sample titles caught two over-catches (same class as the
-- eu_cohesion 'Zusammenarbeit mit der AfD' bug):
--
-- 1. coercion_justified swept NEUTRAL bundle-words: bare 'drug'/'cartel'/'narco'/
--    'Tren de Aragua'/'threat'/'security' filed every neutral wire report -- and
--    even US-domestic crime ("ATM robberies", "ICE arrests teacher") -- as
--    "justified action". Those words are the BUNDLE's job, not stance framing.
--    Keep only genuinely justificatory framing. Neutral strike reports now match
--    neither +1 nor -1 and are dropped (precision over recall).
--
-- 2. transition_democracy_betrayed swept bare 'Machado'/'Opposition'/'oposición'
--    -> neutral opposition news ("Machado at Houston energy conference", "plans to
--    return home") mislabelled as "stolen transition". Keep repression/no-election
--    framing only.
--
-- 3. essequibo has NO Russia/China coverage (0 titles); the real corpus is Spanish
--    outlets covering Venezuela's claim + Anglo wires. Repoint the +1 pool at the
--    publishers that actually carry the claim so the card is not empty.
--
-- Reversible; re-run bootstrap after apply.

BEGIN;

-- NB: 'victory'/'triumph'/'win for' removed -- too generic (a World Baseball
-- Classic "victory" title leaked in). Keep only intervention-specific praise.
UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'narco-dictator','narco-state','narcoterror','counter-narcotics','counternarcotics',
  'kingpin','brought to justice','faces justice','justice served','justified','liberat',
  'eliminated','infamous','notorious','doorstep','decisive blow',
  'freed from','befreit','gerechtfertigt','liberar','narcodictador','justicia','capo'
] WHERE id = 'ven_coercion_justified';

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'frozen out','sidelined','no elections','without elections','snap elections','sham',
  'illegitim','betray','authoritarian','entrench','power grab','kidnap','arrest',
  'detention','detain','politically motivated','crackdown','repress','urges elections',
  'demands elections','keine Wahlen','Schein','ausgeschlossen','festgenommen','entführt',
  'sin elecciones','fraude','ilegítim','represión','detenc','secuestr','exige elecciones'
] WHERE id = 'ven_transition_democracy_betrayed';

UPDATE narratives_v2 SET publishers = ARRAY[
  'El Mundo','El País','La Nación','O Estado de S. Paulo','Clarín','Straits Times',
  'TASS (EN)','TASS','RT','CGTN','China Daily','Global Times','Press TV'
] WHERE id = 'ven_essequibo_venezuelan_claim';

COMMIT;

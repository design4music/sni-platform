-- Cuba theater: narrative recalibration after reading real samples (§4 step 6).
--
-- WHAT THE FIRST PASS GOT WRONG. Every +1 narrative came back at 1-2 titles.
-- That was not an under-keywording bug -- measurement against the Western/Latin
-- bloc (1,530 titles) showed:
--
--   pro-pressure evaluative framing   18 titles  (1.2%)
--   US-critical evaluative framing   139 titles  (9.1%)
--
-- I had authored a stance the corpus does not support. Western and Latin
-- coverage of this theater almost never endorses the pressure campaign; where
-- it carries a frame at all it is critical of it, and the remaining ~90% is
-- neutral wire reporting that framing_required correctly drops.
--
-- THE FIX: the +1 stance is re-scoped from "US pressure is justified"
-- (unattested) to "the Cuban government is the author of this crisis and rules
-- by coercion" (well attested: regime-label vocabulary 45 titles, repression
-- vocabulary 25, regime-fault 10). This keeps the sign convention shared with
-- the venezuela sibling -- positive = fault lies with the target government --
-- while describing a stance that real publishers actually take.
--
-- WHAT IS DELIBERATELY *NOT* ADDED AS A FRAMING KEYWORD: 'blockade' / 'bloqueo'
-- / 'embargo'. They are the largest Western-side terms (139) but they are the
-- NAME OF THE THING, not a stance -- "Cuba restores power after 29-hour
-- blackout amid US oil blockade" is Reuters describing an event. Promoting them
-- to framing keywords would sweep the entire neutral wire feed into the
-- Western-critical narrative and mislabel it. Only evaluative terms are used
-- ('economic bombing', 'chokes', 'asfixia', 'collective punishment',
-- 'coercive', 'breaking point').
--
-- Keywords only; no publisher, stance or sign changes, so the theater roll-up
-- buckets are unaffected.

BEGIN;

-- A. sanctions +1 -- instruments aimed at a government treated as illegitimate
UPDATE narratives_v2 SET
 name_en = 'The instruments are aimed at a government that rules without consent',
 name_de = 'Die Instrumente richten sich gegen eine Regierung, die ohne Zustimmung herrscht',
 claim_en = 'Sanctions, designations and criminal charges target a one-party leadership implicated in trafficking and repression -- the pressure is aimed at a government, not at a people it does not represent.',
 claim_de = 'Sanktionen, Listungen und Strafverfahren richten sich gegen eine Einparteienführung, die in Schmuggel und Repression verstrickt ist -- der Druck zielt auf eine Regierung, nicht auf ein Volk, das sie nicht vertritt.',
 stance_label_en = 'Aimed at the government',
 stance_label_de = 'Gegen die Regierung gerichtet',
 framing_keywords = ARRAY['castrismo','Castroism','dictad','dictat','ditadura','Diktatur','communist rule','one-party','partido único','must go','teetering','autocrat','narcotráfico','drug trafficking','murder charges','accountab','rendición de cuentas','sin consentimiento'],
 updated_at = NOW()
WHERE id = 'cuba_pressure_justified';

-- A. sanctions -1 -- evaluative critical vocabulary only, never bare 'blockade'
UPDATE narratives_v2 SET
 framing_keywords = ARRAY['extraterritorial','overreach','collective punishment','castigo colectivo','Kollektivstrafe','secondary sanctions','third countries','terceros países','unilateral','einseitig','coercive','coerci','counterproductive','contraproducente','kontraproduktiv','condemn','verurteil','condena','economic bombing','chok','asfixia','asphyx','strangl','breaking point','völkerrechtswidrig'],
 updated_at = NOW()
WHERE id = 'cuba_sanctions_overreach';

-- B. energy +1 -- regime-fault causation
UPDATE narratives_v2 SET
 framing_keywords = ARRAY['mismanagement','Misswirtschaft','mala gestión','decades of','décadas','Soviet-era','ageing','aging','obsolet','envejec','decay','marode','veraltet','state-run','central planning','Planwirtschaft','self-inflicted','failed model','modelo fallido','fracas','failing','arruin','ineficien','castrismo','gescheitert'],
 updated_at = NOW()
WHERE id = 'cuba_collapse_self_inflicted';

-- B. energy -1 -- add the attested suffering vocabulary
UPDATE narratives_v2 SET
 framing_keywords = ARRAY['humanitarian','humanitär','humanitaria','emergency','emergenc','Notlage','children are dying','civilians','Zivilisten','civiles','hospital','malnutrition','malnutri','hunger','hambre','Hunger','UN warns','catastroph','catástrofe','Katastroph','suffering','Leid','sufrimiento','desperate','desesper','misery','agoniz','asfixia','chok','breaking point','penuria'],
 updated_at = NOW()
WHERE id = 'cuba_collapse_humanitarian_alarm';

-- C. lifelines +1
UPDATE narratives_v2 SET
 framing_keywords = ARRAY['prop up','props up','apuntalar','stütz','undercut','circumvent','umgehen','evade','eludir','sanctions-busting','prolong','prolongar','verlängert','buy time','oxígeno','respiro','rescue','rescate','castrismo','dictad','ditadura'],
 updated_at = NOW()
WHERE id = 'cuba_lifelines_prop_up';

-- D. military +1
UPDATE narratives_v2 SET
 framing_keywords = ARRAY['credible','glaubwürdig','all options','alle Optionen','military option','opción militar','deterren','Abschreckung','disuasión','brought to the table','teetering','provocation','Provokation','provocación','drone attack','plotting','threat to the US','amenaza para'],
 updated_at = NOW()
WHERE id = 'cuba_force_credible_threat';

-- E. regime +1 -- broaden to the attested Spanish repression vocabulary
UPDATE narratives_v2 SET
 framing_keywords = ARRAY['political prisoner','preso polític','presos polític','dissident','disidente','arrest','arrestan','detien','detenid','encarcel','jailed','crackdown','one-party','partido único','censorship','censur','repress','repres','bargaining chip','politische Gefangene','inhaftiert','verhaftet','Einparteien','Zensur','castrismo','dictad'],
 updated_at = NOW()
WHERE id = 'cuba_repression_documented';

COMMIT;

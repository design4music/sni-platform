-- South Asia: narrative framing fixes found at the §4/step-9 measure pass by
-- reading actual sample titles per narrative (not by trusting the counts).
--
-- BUG 1 -- kashmir_dispute cards were a junk drawer. kashmir_dispute is an A2
-- NAME-gated atomic, so every Indian-bloc title merely containing a Kashmir
-- toponym landed on the "Kashmir is integral to India" card with
-- framing_required=false: a Pakistan Army helicopter crash in PoK, the Khamenei
-- assassination protests, a satellite-phone detention at Srinagar airport, a
-- "Go To Kashmir" domestic remark -- and an article comparing imported apples
-- with Kashmiri ones. 115 titles, a small minority of them the sovereignty
-- claim. This is exactly the eu_cohesion_theater failure (name-gated atomic +
-- framing_required off swept in unrelated country news, 317->12 once fixed).
-- FIX: framing_required=true on all three Kashmir cards, with gates verified
-- against real samples FIRST (integral 115->~13, all 13 genuinely the
-- sovereignty claim; disputed gate 14/15 on-topic).
--
-- BUG 2 -- kashmir_rights_and_restrictions was MISLABELLED. Its claim said
-- "under Indian administration", but 5 of 7 real hits are protests in
-- PAKISTAN-administered Kashmir (the refugee-seats unrest, ~20 dead) plus a
-- helicopter crash and a cricket-bat willow shortage. Rescoped to the unrest
-- and rights record across BOTH administrations, which is what the corpus
-- actually contains -- rather than keeping a label the data does not support.
--
-- BUG 3 -- baloch_foreign_backed_insurgency's framing keywords included the
-- generic 'killed' and 'attack', which admitted "Gwadar fisherman killed by
-- 'debris from Israeli projectile' in Iran waters". Generic-casualty verbs
-- removed; the sponsorship/counter-terror vocabulary carries the card.
--
-- NOT A BUG (checked, left alone): militancy_indian_pretext sits at 5 titles.
-- That is not the Australia-style recall gap -- only 7 Pakistani-bloc titles
-- exist in the whole atomic scope, because the Pakistani press covers its own
-- Afghan/Baloch militancy rather than India's accusations. 5 of 7 captured.

BEGIN;

UPDATE narratives_v2 SET
  framing_required = true,
  framing_keywords = ARRAY[
    'vacate','integral','unwarranted','internal matter','Article 370','Delimitation',
    'forcibly occupied','Solidarity Day','sovereignty','part of India','Indian territory',
    'special status','inalienable',
    'integraler','unteilbar','Souveränität','Artikel 370'],
  updated_at = now()
WHERE id = 'kashmir_integral_to_india';

UPDATE narratives_v2 SET
  framing_required = true,
  framing_keywords = ARRAY[
    'disputed','self-determination','UN resolution','occupied','unresolved','legal reality',
    'unilateral','plebiscite','resistance','solidarity','rights','anti-terror law','pledge',
    'just struggle',
    'umstritten','Selbstbestimmung','besetzt','ungelöst'],
  updated_at = now()
WHERE id = 'kashmir_disputed_territory';

UPDATE narratives_v2 SET
  framing_required = true,
  stance_label_en = 'Unrest and rights across the divided territory',
  stance_label_de = 'Unruhen und Rechte im geteilten Gebiet',
  name_en = 'Both administrations face unrest and answer it with force',
  name_de = 'Beide Verwaltungen stehen Unruhen gegenüber und begegnen ihnen mit Gewalt',
  claim_en = 'Rights-focused framing (Western mainstream and wire services) reports the line of control as dividing two administrations and concentrates on conditions on the ground on both sides of it: protests and deadly clashes in Pakistan-administered Kashmir over refugee seats and a shutdown, and detentions, demolitions, blacklisting and curbs on protest in Indian-administered Kashmir. The common thread is unrest met with force rather than either state''s territorial case.',
  claim_de = 'Die menschenrechtsorientierte Darstellung (westliche Leitmedien und Nachrichtenagenturen) beschreibt die Waffenstillstandslinie als Trennung zweier Verwaltungen und konzentriert sich auf die Lage vor Ort auf beiden Seiten: Proteste und tödliche Zusammenstöße im pakistanisch verwalteten Kaschmir um Flüchtlingssitze und einen Generalstreik sowie Festnahmen, Abrisse, Verbote und Einschränkungen von Protest im indisch verwalteten Kaschmir. Gemeinsam ist beiden, dass Unruhen mit Gewalt begegnet wird und nicht der territoriale Anspruch eines der Staaten im Vordergrund steht.',
  framing_keywords = ARRAY[
    'protest','rights','detention','detained','crackdown','restriction','shutdown',
    'sentenc','demolition','spying','blacklisted','curfew','jailed','Israel model','clashes',
    'Protest','Rechte','Festnahme','Einschränkung',
    'مظاهر','احتجاج'],
  updated_at = now()
WHERE id = 'kashmir_rights_and_restrictions';

UPDATE narratives_v2 SET
  framing_keywords = ARRAY[
    'terrorist','militant','BLA','Indian-backed','proxy','security forces','operation',
    'neutralis','designate','responsible','sponsor','Ghazab','terrorism','hostile',
    'Terrorist','Militante','Terrorismus'],
  updated_at = now()
WHERE id = 'baloch_foreign_backed_insurgency';

COMMIT;

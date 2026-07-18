-- South Asia theater-level narrative cards (§5.5)
--
-- The roll-up (THEATER_ROLLUP_SQL) pulls a card's headlines from the MEMBER
-- ATOMICS' title_narratives where sign(atomic.stance) = sign(theater.stance)
-- AND publisher ∈ card.publishers, DISTINCT ON title. So two cards of the SAME
-- sign whose publisher lists overlap double-count. All cards below are
-- publisher-disjoint within each sign bucket.
--
-- FIVE cards, not the usual three, because this theater has TWO principals.
-- Arctic/Ukraine/us_china get away with three because every atomic shares one
-- axis (pro-Western vs anti-Western). Here the acting state differs by atomic:
-- India acts in Kashmir/Indus/militancy, Pakistan acts in Afghanistan and
-- Balochistan. So each national bloc legitimately appears on BOTH signs --
-- India as claimant (+) and as critic of Pakistan's conduct (-), Pakistan as
-- security actor (+) and as aggrieved party (-). korea_theater already sets the
-- precedent for two cards per sign ([2,2,-2,-2]).
--
--   + bucket (disjoint): Indian bloc | Pakistani bloc
--   - bucket (disjoint): Indian bloc | Pakistani bloc | Western bloc
--
-- Turkish/Gulf outlets (Anadolu, TRT World, Daily Sabah, Arab News) and the
-- Russian/Iranian ones (RT, TASS, Press TV, IRNA) are deliberately OFF the
-- theater cards though they appear on atomic ones. They sit on the Pakistani
-- side for Kashmir/Indus but report the Pakistan-Afghanistan war neutrally, so
-- any theater card that included them would mislabel one or the other. Homeless
-- beats mislabelled; their coverage still shows on the atomic pages.
--
-- No rift-exploitation card: that caveat is for intra-Western disputes with
-- Russia/China as bystanders. India and Pakistan are the principals here.

BEGIN;

INSERT INTO narratives_v2
  (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
   name_en, name_de, claim_en, claim_de, publishers, framing_keywords,
   framing_required, actor_centroids, is_active)
VALUES

-- ---------------------------------------------------------------- + bucket
('south_asia_indian_account', 'south_asia_theater', 1, 2,
 'Indian claim and counter-terrorism framing', 'Indische Ansprüche und Terrorbekämpfung',
 'India is the status-quo power defending its territory against a militancy-exporting neighbour',
 'Indien ist die Status-quo-Macht, die ihr Gebiet gegen einen Militanz exportierenden Nachbarn verteidigt',
 'The Indian account (Indian mainstream press) runs through the three disputes in which India is the acting party: Jammu and Kashmir is Indian territory and the question is closed, the attacks on Indian soil are traced to groups operating from Pakistan with official tolerance, and the Indus Waters Treaty is an arrangement from another era that a state sponsoring militancy cannot expect to continue unchanged.',
 'Die indische Darstellung (indische Leitmedien) zieht sich durch die drei Streitfälle, in denen Indien die handelnde Partei ist: Jammu und Kaschmir ist indisches Territorium und die Frage ist entschieden, die Anschläge auf indischem Boden werden auf Gruppen zurückgeführt, die mit offizieller Duldung von Pakistan aus operieren, und der Indus-Wasservertrag ist eine Regelung aus einer anderen Zeit, deren unveränderte Fortführung ein Staat, der Militanz unterstützt, nicht erwarten kann.',
 ARRAY['Times of India','The Times of India','Hindustan Times','NDTV','The Hindu','Indian Express','The Indian Express','WION','Republic TV','Republic World','DD India'],
 ARRAY['integral','vacate','terror','Sindoor','Lashkar','sponsor','unwarranted','outdated','sovereignty'],
 false, ARRAY['ASIA-INDIA'], true),

('south_asia_pakistani_security_account', 'south_asia_theater', 2, 1,
 'Pakistani counter-terrorism framing', 'Pakistanische Terrorbekämpfungs-Darstellung',
 'Pakistan is fighting militancy on two fronts against externally backed enemies',
 'Pakistan bekämpft Militanz an zwei Fronten gegen von außen unterstützte Gegner',
 'The Pakistani security account (Pakistani press) covers the two conflicts in which Pakistan is the acting party: strikes into Afghanistan are presented as hitting Tehreek-e-Taliban sanctuaries that Kabul will not close, and the insurgency in Balochistan is presented as externally sponsored terrorism rather than an indigenous political movement. In both, Pakistan casts itself as responding to violence organised beyond its control.',
 'Die pakistanische Sicherheitsdarstellung (pakistanische Presse) umfasst die beiden Konflikte, in denen Pakistan die handelnde Partei ist: Angriffe nach Afghanistan gelten als Schläge gegen Rückzugsgebiete der Tehreek-e-Taliban, die Kabul nicht schließen will, und der Aufstand in Belutschistan gilt als von außen gesteuerter Terrorismus statt als einheimische politische Bewegung. In beiden Fällen stellt sich Pakistan als reagierend auf Gewalt dar, die jenseits seiner Kontrolle organisiert wird.',
 ARRAY['Dawn','Express Tribune','The Express Tribune','The News International','The Nation'],
 ARRAY['terrorist','militant','sanctuar','TTP','BLA','Ghazab','Indian-backed','operation','retaliat'],
 false, ARRAY['ASIA-PAKISTAN'], true),

-- ---------------------------------------------------------------- - bucket
('south_asia_pakistani_grievance', 'south_asia_theater', 3, -2,
 'Pakistani grievance framing', 'Pakistanische Beschwerde-Darstellung',
 'India is the coercive party: occupier, water aggressor and fabricator of charges',
 'Indien ist die erzwingende Partei: Besatzer, Wasseraggressor und Erfinder von Vorwürfen',
 'The Pakistani account (Pakistani press) reverses the Indian one across the same three disputes: Kashmir''s status is unresolved and its people are owed self-determination rather than a settlement imposed from Delhi, the Pahalgam allegations have never been substantiated and serve to justify pressure and strikes, and suspending a treaty on which a downstream population depends for its crops and drinking water is coercion whatever the pretext.',
 'Die pakistanische Darstellung (pakistanische Presse) kehrt die indische in denselben drei Streitfällen um: Kaschmirs Status ist ungeklärt und seiner Bevölkerung steht Selbstbestimmung zu statt einer von Delhi auferlegten Lösung, die Vorwürfe zu Pahalgam wurden nie belegt und dienen der Rechtfertigung von Druck und Angriffen, und die Aussetzung eines Vertrags, von dem eine flussabwärts lebende Bevölkerung für Ernten und Trinkwasser abhängt, ist Zwang, welcher Vorwand auch genannt wird.',
 ARRAY['Dawn','Express Tribune','The Express Tribune','The News International','The Nation'],
 ARRAY['occupied','disputed','self-determination','weaponisation','water aggression','false narrative','unsubstantiated','binding'],
 false, ARRAY['ASIA-PAKISTAN'], true),

('south_asia_indian_critique_of_pakistan', 'south_asia_theater', 4, -2,
 'Indian framing of Pakistan as destabiliser', 'Indische Darstellung Pakistans als Destabilisator',
 'Pakistan''s conduct beyond its borders and failures within them destabilise the region',
 'Pakistans Verhalten jenseits seiner Grenzen und sein Versagen im Inneren destabilisieren die Region',
 'The Indian critique (Indian mainstream press) addresses the conflicts where Pakistan, not India, is the acting party: the air campaign in Afghanistan is called an assault on the sovereignty of a neighbour and a threat to regional peace after UN findings on civilian deaths, and the insurgency in Balochistan is treated as evidence of Pakistani state failure, with Islamabad''s allegations of Indian backing dismissed as deflection from internal failings.',
 'Die indische Kritik (indische Leitmedien) betrifft die Konflikte, in denen Pakistan und nicht Indien die handelnde Partei ist: Die Luftkampagne in Afghanistan wird nach UN-Feststellungen zu zivilen Opfern als Angriff auf die Souveränität eines Nachbarn und als Bedrohung des regionalen Friedens bezeichnet, und der Aufstand in Belutschistan gilt als Beleg für das Versagen des pakistanischen Staates, wobei Islamabads Vorwürfe indischer Unterstützung als Ablenkung von inneren Defiziten zurückgewiesen werden.',
 ARRAY['Times of India','The Times of India','Hindustan Times','NDTV','The Hindu','Indian Express','The Indian Express','WION','Republic TV','Republic World','DD India'],
 ARRAY['sovereignty','assault','civilian','internal failing','civil war','condemn','baseless','destabilis'],
 false, ARRAY['ASIA-INDIA'], true),

('south_asia_international_rights', 'south_asia_theater', 5, -1,
 'International civilian-cost and rights framing', 'Internationale Darstellung ziviler Kosten und Rechte',
 'Across every front the cost falls on civilians and dissenters',
 'An jeder Front tragen Zivilisten und Andersdenkende die Kosten',
 'International framing (Western mainstream, wire services and Al Jazeera) sets aside each government''s territorial case and reports what the disputes do to the people inside them: the dead and displaced of the Pakistan-Afghanistan strikes and the collapse of successive ceasefires, protests met with force on both sides of the Kashmir line, and a Baloch activist sentenced to life amid enforced disappearances and curbs on peaceful protest.',
 'Die internationale Darstellung (westliche Leitmedien, Nachrichtenagenturen und Al Jazeera) lässt die territorialen Ansprüche der Regierungen beiseite und berichtet, was die Konflikte den Menschen in ihnen antun: die Toten und Vertriebenen der pakistanisch-afghanischen Angriffe und das Scheitern aufeinanderfolgender Waffenruhen, Proteste, denen auf beiden Seiten der Kaschmir-Linie mit Gewalt begegnet wird, und eine belutschische Aktivistin, die inmitten von Fällen des Verschwindenlassens und Einschränkungen friedlichen Protests zu lebenslanger Haft verurteilt wurde.',
 ARRAY['Reuters','BBC World','Associated Press','Deutsche Welle','The Guardian','France 24','France 24 (EN)','Euronews','Al Jazeera','Die Zeit','NPR'],
 ARRAY['civilian','killed','hospital','displaced','ceasefire','protest','rights','disappearance','Mahrang','detention'],
 false, ARRAY['ASIA-INDIA','ASIA-PAKISTAN','ASIA-AFGHANISTAN'], true)

ON CONFLICT (id) DO UPDATE SET
  fn_id = EXCLUDED.fn_id, display_order = EXCLUDED.display_order,
  stance = EXCLUDED.stance, stance_label_en = EXCLUDED.stance_label_en,
  stance_label_de = EXCLUDED.stance_label_de, name_en = EXCLUDED.name_en,
  name_de = EXCLUDED.name_de, claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
  publishers = EXCLUDED.publishers, framing_keywords = EXCLUDED.framing_keywords,
  framing_required = EXCLUDED.framing_required, actor_centroids = EXCLUDED.actor_centroids,
  is_active = EXCLUDED.is_active, updated_at = now();

COMMIT;

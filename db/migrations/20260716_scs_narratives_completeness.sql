-- South China Sea standalone atomic: narratives + bilingual completeness fields.
--
-- Coalitions are fully publisher-disjoint, measured over the 179 titles the
-- applied bundle matches in 180d: Chinese state media (Global Times 30, CGTN 24,
-- China Daily 21, People's Daily 11 = 86) against Western/Philippine/allied
-- press (Reuters 21, Philippine Daily Inquirer 12, Straits Times 9, ...).
-- Publisher alone therefore disambiguates stance, so framing_required stays
-- false on both (spec 5): this is a straight two-camp dispute, not an own-goal
-- topic where the supportive camp turns critic.
--
-- No rift-exploitation card (spec 5, Arctic precedent): that caveat applies to
-- INTRA-WESTERN disputes where Russian/Chinese media are bystanders amplifying
-- a split. Here China is a principal party asserting its own claim, so its
-- coverage belongs on the dispute's own axis. Russian outlets are absent from
-- the corpus entirely, so there is no third bloc to model.
--
-- No ASEAN-hedging (stance 0) card: Straits Times / Channel NewsAsia / Bangkok
-- Post carry heavy Reuters wire copy (the same Philippine floating-structure
-- story runs verbatim under Reuters, Straits Times and The Hindu), so a
-- Southeast-Asian-publisher narrative would misfile wire copy as an ASEAN voice.
--
-- FN description_en/_de and editorial_summary_en/_de are deliberately neutral,
-- factual and evergreen -- no framing, motive attribution or temporality.
-- Framing lives only in narratives_v2 below.

BEGIN;

DELETE FROM narratives_v2 WHERE fn_id = 'south_china_sea_claims';

INSERT INTO narratives_v2 (
    id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de,
    actor_centroids, publishers, framing_keywords, framing_required, is_active
) VALUES
(
    'scs_chinese_sovereignty_claim',
    'south_china_sea_claims',
    1,
    2,
    'Chinese sovereignty claim',
    'Chinesischer Souveränitätsanspruch',
    'China''s South China Sea claims are historic, lawful, and enforcement is defensive',
    'Chinas Ansprüche im Südchinesischen Meer sind historisch und rechtmäßig, die Durchsetzung ist defensiv',
    'Sovereignty framing (Chinese state media) holds that China''s claims to the Nansha, Xisha, Zhongsha and Huangyan features rest on historic rights and are consistent with international law; that the 2016 arbitral award is invalid, non-binding and "waste paper"; and that coast guard activity is routine rights-protection law enforcement in Chinese waters. It locates the source of instability in the Philippines and in external powers -- chiefly the United States, and increasingly Japan -- whose operations, exercises and arms transfers are cast as militarising the sea and as interference by states that are not parties to the dispute. Vocabulary: indisputable sovereignty, historic rights, waste paper, rights protection, law enforcement, provocation, hype, external interference, militarisation.',
    'Die Souveränitäts-Rahmung (chinesische Staatsmedien) sieht Chinas Ansprüche auf die Nansha-, Xisha-, Zhongsha- und Huangyan-Formationen als historisch begründet und völkerrechtskonform an; der Schiedsspruch von 2016 sei ungültig, unverbindlich und ein "Stück Altpapier". Küstenwacheinsätze gelten als routinemäßige Rechtsdurchsetzung in chinesischen Gewässern. Als Ursache der Instabilität werden die Philippinen und externe Mächte benannt -- vor allem die USA und zunehmend Japan --, deren Operationen, Manöver und Waffenlieferungen als Militarisierung des Meeres und als Einmischung nicht beteiligter Staaten dargestellt werden.',
    ARRAY['ASIA-CHINA'],
    ARRAY['Global Times', 'CGTN', 'China Daily', 'People''s Daily', 'Xinhua'],
    ARRAY['indisputable sovereignty', 'historic rights', 'waste paper', 'rights protection',
          'law enforcement', 'provocation', 'hype', 'interference', 'militariz', 'militaris',
          'unshirkable', 'Nansha', 'Xisha', 'Huangyan', 'Souveränität', 'Rechtsdurchsetzung'],
    false,
    true
),
(
    'scs_rules_based_maritime_order',
    'south_china_sea_claims',
    2,
    -2,
    'Rules-based maritime order',
    'Regelbasierte maritime Ordnung',
    'China''s claims lack legal basis and its conduct coerces smaller claimants',
    'Chinas Ansprüche entbehren einer Rechtsgrundlage, sein Vorgehen setzt kleinere Anrainer unter Druck',
    'Rules-based framing (Western, Philippine, Japanese and Southeast Asian press) treats the 2016 arbitral award as binding and the nine-dash line as without legal basis under UNCLOS, and reads Chinese coast guard and maritime-militia conduct -- water cannon, blocking, shadowing, and structures placed on contested features -- as coercion of smaller claimants inside their exclusive economic zones. It presents allied naval presence, joint patrols, exercises such as Balikatan and an effective ASEAN code of conduct as the legitimate response, and treats incidents at Scarborough Shoal and Second Thomas Shoal as tests of the alliance. Vocabulary: arbitral ruling, rules-based order, UNCLOS, exclusive economic zone, coercion, harassment, water cannon, illegal, freedom of navigation, alliance, code of conduct.',
    'Die regelbasierte Rahmung (westliche, philippinische, japanische und südostasiatische Presse) betrachtet den Schiedsspruch von 2016 als bindend und die Neun-Striche-Linie als völkerrechtlich unbegründet. Das Vorgehen der chinesischen Küstenwache und Seemiliz -- Wasserwerfer, Blockaden, Verfolgungsfahrten und Bauten auf umstrittenen Formationen -- gilt als Nötigung kleinerer Anrainer in deren ausschließlichen Wirtschaftszonen. Als legitime Antwort erscheinen alliierte Marinepräsenz, gemeinsame Patrouillen, Manöver wie Balikatan und ein wirksamer ASEAN-Verhaltenskodex.',
    ARRAY['ASIA-SOUTHEAST', 'AMERICAS-USA', 'ASIA-JAPAN'],
    ARRAY['Reuters', 'Philippine Daily Inquirer', 'Straits Times', 'Channel NewsAsia', 'CSIS',
          'Nikkei Asia', 'Bangkok Post', 'Japan Times', 'Asahi Shimbun', 'Kyodo News',
          'Associated Press', 'Bloomberg', 'Washington Post', 'Wall Street Journal', 'BBC World',
          'The Economist', 'The Telegraph', 'Sky News', 'The Australian', 'Al Jazeera',
          'France 24 (EN)', 'Die Zeit', 'Frankfurter Allgemeine', 'Handelsblatt', 'NZZ',
          'Chatham House', 'Defense News', 'Military Times', 'Janes', 'Jakarta Globe',
          'VN Express', 'The Star', 'The Hindu', 'WION'],
    ARRAY['arbitral', 'rules-based', 'UNCLOS', 'exclusive economic zone', 'coercion', 'coercive',
          'harassment', 'water cannon', 'illegal', 'freedom of navigation', 'code of conduct',
          'aggressive', 'incursion', 'Schiedsspruch', 'Wasserwerfer', 'Nötigung', 'Verhaltenskodex'],
    false,
    true
);

-- Completeness fields (spec 6): bilingual, neutral, evergreen.
UPDATE friction_nodes
SET name_en = 'South China Sea territorial and maritime disputes',
    name_de = 'Territorial- und Seerechtskonflikte im Südchinesischen Meer',
    description_en = 'China, the Philippines, Vietnam, Malaysia, Brunei, Indonesia and Taiwan hold overlapping territorial and maritime claims in the South China Sea. China''s claim, drawn as the nine-dash line, covers most of the sea and overlaps exclusive economic zones claimed by the other parties. An arbitral tribunal constituted under the UN Convention on the Law of the Sea ruled in 2016 that the line has no legal basis; China does not recognise the ruling. Several claimants occupy features in the Spratly and Paracel groups, and some have built installations on them. Coast guard, naval, militia and fishing vessels operate in contested waters, and encounters occur around features including Scarborough Shoal, Second Thomas Shoal and Reed Bank. The United States and other states outside the dispute conduct naval and air operations in the sea and hold exercises with claimant states. China and ASEAN have negotiated a code of conduct for the sea since 2002. Roughly a third of global shipping transits the sea, and the seabed holds oil, gas and fishing grounds.',
    description_de = 'China, die Philippinen, Vietnam, Malaysia, Brunei, Indonesien und Taiwan erheben einander überlappende Territorial- und Seerechtsansprüche im Südchinesischen Meer. Chinas Anspruch, als Neun-Striche-Linie gezogen, umfasst den größten Teil des Meeres und überlappt die von den anderen Parteien beanspruchten ausschließlichen Wirtschaftszonen. Ein nach dem UN-Seerechtsübereinkommen gebildetes Schiedsgericht entschied 2016, dass die Linie keine Rechtsgrundlage hat; China erkennt den Schiedsspruch nicht an. Mehrere Anrainer besetzen Formationen der Spratly- und Paracel-Gruppen, einige haben dort Anlagen errichtet. Küstenwach-, Marine-, Milizen- und Fischereifahrzeuge operieren in umstrittenen Gewässern; Begegnungen ereignen sich unter anderem am Scarborough-Riff, am Second-Thomas-Riff und an der Reed Bank. Die USA und weitere nicht am Streit beteiligte Staaten führen Marine- und Lufteinsätze im Meer durch und halten Manöver mit Anrainerstaaten ab. China und die ASEAN verhandeln seit 2002 über einen Verhaltenskodex. Etwa ein Drittel des weltweiten Seehandels passiert das Meer; der Meeresboden birgt Öl-, Gas- und Fischereivorkommen.',
    editorial_summary_en = 'Seven parties hold overlapping claims to the South China Sea, through which roughly a third of global shipping passes. China''s nine-dash line covers most of the sea and overlaps the exclusive economic zones of the other claimants; a 2016 arbitral tribunal under UNCLOS found the line has no legal basis, and China does not recognise that ruling. Claimants occupy and have built on features in the Spratly and Paracel groups, and coast guard, militia and naval vessels meet around Scarborough Shoal, Second Thomas Shoal and Reed Bank. The United States and other non-claimant states operate naval and air forces in the sea and exercise with claimant states, and China and ASEAN have negotiated a code of conduct since 2002. Coverage splits along two lines: Chinese state media present the claims as historic and lawful, the arbitral award as invalid, and coast guard activity as routine law enforcement against Philippine and American provocation; Western, Philippine, Japanese and Southeast Asian press treat the award as binding and Chinese conduct as coercion of smaller claimants, and support allied presence and a binding code of conduct.',
    editorial_summary_de = 'Sieben Parteien erheben überlappende Ansprüche auf das Südchinesische Meer, durch das etwa ein Drittel des weltweiten Seehandels läuft. Chinas Neun-Striche-Linie umfasst den größten Teil des Meeres und überlappt die ausschließlichen Wirtschaftszonen der übrigen Anrainer; ein Schiedsgericht nach dem UN-Seerechtsübereinkommen befand 2016, die Linie habe keine Rechtsgrundlage -- China erkennt den Schiedsspruch nicht an. Anrainer besetzen und bebauen Formationen der Spratly- und Paracel-Gruppen; Küstenwach-, Milizen- und Marinefahrzeuge begegnen einander am Scarborough-Riff, am Second-Thomas-Riff und an der Reed Bank. Die USA und weitere nicht beteiligte Staaten operieren mit Marine und Luftwaffe im Meer und üben mit Anrainerstaaten; China und die ASEAN verhandeln seit 2002 über einen Verhaltenskodex. Die Berichterstattung teilt sich in zwei Linien: Chinesische Staatsmedien stellen die Ansprüche als historisch und rechtmäßig dar, den Schiedsspruch als ungültig und die Küstenwacheinsätze als routinemäßige Rechtsdurchsetzung gegen philippinische und amerikanische Provokation. Westliche, philippinische, japanische und südostasiatische Presse hält den Schiedsspruch für bindend, wertet Chinas Vorgehen als Nötigung kleinerer Anrainer und befürwortet alliierte Präsenz und einen verbindlichen Verhaltenskodex.',
    updated_at = NOW()
WHERE id = 'south_china_sea_claims';

COMMIT;

-- Thailand-Cambodia border conflict: greenfield standalone atomic (no theater).
--
-- Structural assessment (FN_THEATER_BUILD_SPEC 2a/1a, user-approved 2026-07-17):
-- grounded against 365d of ASIA-SOUTHEAST coverage. This is the SCS/Myanmar/Cuba
-- shape -- a single standalone atomic, NOT a theater:
--   * Volume ~42 tight titles/180d and declining; the kinetic phase (temple
--     clashes + the Trump-brokered ceasefire) predates the data window, so the
--     corpus is a post-ceasefire diplomatic simmer (MOU44 maritime row, border
--     closures, "third clash" warnings, ASEAN mediation).
--   * It cannot be split into atomics (spec 2 A2b): the only populated centroid
--     is the 11-country ASIA-SOUTHEAST bucket (ASIA-PACIFIC-THAILAND is empty --
--     ASEAN centroid bug -- and Cambodia has no centroid), so there is no
--     primary_target to gate on and any second atomic would reuse the same
--     toponym/pair anchors and match identical titles. Land vs maritime is one
--     dispute (same MOU framework, same actors, same Thai outlets), not two
--     orthogonal phenomena.
--   * Archetype B bilateral: both are principals, action runs both directions,
--     so primary_target stays NULL and alias purity is the only lever.
-- The large Cambodia scam-centre / transnational-crime story is a DIFFERENT FN
-- (flagged separately) and is deliberately excluded here.
--
-- Per 1a a standalone atomic must carry its OWN anchor_point (Preah Vihear temple,
-- the iconic epicentre) or it vanishes from the conflicts map. Region routing uses
-- centroid_ids[0] -> ASIA-SOUTHEAST -> Southeast Asia.
--
-- The fn_anchor bundle is applied separately via apply_fn_anchor_bundle.py from
-- out/extraction/thailand_cambodia_border__curated.json (bare country names
-- excluded to keep the scam story out). This migration creates the FN row, the
-- three narratives, and the bilingual completeness fields.
--
-- Narrative design, grounded (spec 5): the feed has NO Cambodian outlets, so the
-- Cambodian voice exists only as wire-quoted statements. Chinese state media do
-- NOT push a pro-Cambodia territorial line -- they self-cast as peace-broker
-- ("China's mediation helps advance peace", "China pleased to see ceasefire") and
-- even attribute incident reports to Thai media -- so filing them as pro-Cambodia
-- would mislabel them (Korea/us_china lesson). Hence three publisher-disjoint
-- cards:
--   +2 Thai sovereignty defence   -> Thai outlets (uniform Thai-POV framing)
--   -2 Cambodian territorial claim -> wire, framing_required (only occupation/
--                                     aggression-framed quotes attribute, not all
--                                     neutral wire copy); thin now, scaffold for
--                                     escalation
--    0 Great-power mediation        -> Chinese state media (peace-broker framing)
-- Descriptions/editorial are neutral, factual, evergreen (spec 6); framing lives
-- only in narratives_v2.

BEGIN;

-- 1. The standalone atomic. Greenfield INSERT (no prior shell).
INSERT INTO friction_nodes (
    id, name_en, name_de, fn_type, scope, is_active,
    centroid_ids, primary_target, affected_asset_ids, anchor_point, display_order,
    description_en, description_de, editorial_summary_en, editorial_summary_de
) VALUES (
    'thailand_cambodia_border',
    'Thailand–Cambodia border conflict',
    'Grenzkonflikt zwischen Thailand und Kambodscha',
    'atomic',
    'regional',
    true,
    ARRAY['ASIA-SOUTHEAST', 'ASIA-PACIFIC-THAILAND'],
    NULL,
    '{}',
    '{"type":"Point","coordinates":[104.68,14.39]}'::jsonb,
    60,
    'Thailand and Cambodia contest their shared 817-kilometre land border and an overlapping maritime zone in the Gulf of Thailand. The land dispute centres on 11th-century Khmer temples and their surrounding ground -- Preah Vihear, awarded to Cambodia by the International Court of Justice in 1962 and again in 2013, and the Ta Moan and Ta Krabey complexes and the tri-border "Emerald Triangle", which remain undemarcated. Boundary work proceeds under a 2000 memorandum (MOU 43) through a Joint Boundary Committee; a separate 2001 memorandum (MOU 44) governs talks on the overlapping maritime claims area, where the island of Koh Kood and seabed oil and gas are at stake. Armed clashes along the frontier in 2025 killed soldiers and civilians and displaced tens of thousands before a ceasefire brokered with outside mediation. Since then the border crossings have been closed at times, both armies have traded accusations of truce violations and troop build-ups, and Cambodia has moved parts of the maritime question toward the UN Convention on the Law of the Sea. Malaysia, the Philippines as ASEAN chair, China and the United States have all been involved in de-escalation.',
    'Thailand und Kambodscha streiten um ihre gemeinsame 817 Kilometer lange Landgrenze und eine überlappende Seezone im Golf von Thailand. Der Landstreit dreht sich um Khmer-Tempel aus dem 11. Jahrhundert und das umliegende Gebiet -- Preah Vihear, das der Internationale Gerichtshof 1962 und erneut 2013 Kambodscha zusprach, sowie die Anlagen Ta Moan und Ta Krabey und das Dreiländereck "Smaragddreieck", die unvermessen bleiben. Die Grenzarbeit läuft unter einem Memorandum von 2000 (MOU 43) über eine Gemeinsame Grenzkommission; ein separates Memorandum von 2001 (MOU 44) regelt Gespräche über das überlappende Seegebiet, in dem die Insel Koh Kood sowie Öl- und Gasvorkommen am Meeresboden umstritten sind. Bewaffnete Zusammenstöße entlang der Grenze im Jahr 2025 töteten Soldaten und Zivilisten und vertrieben Zehntausende, bevor unter externer Vermittlung eine Waffenruhe zustande kam. Seither waren die Grenzübergänge zeitweise geschlossen, beide Armeen warfen einander Verstöße gegen die Waffenruhe und Truppenaufmärsche vor, und Kambodscha verlagerte Teile der Seefrage zum UN-Seerechtsübereinkommen. Malaysia, die Philippinen als ASEAN-Vorsitz, China und die USA waren an der Deeskalation beteiligt.',
    'Thailand and Cambodia dispute their shared land border -- centred on the 11th-century temples of Preah Vihear (awarded to Cambodia by the ICJ), Ta Moan and Ta Krabey and the undemarcated "Emerald Triangle" -- and an overlapping maritime zone in the Gulf of Thailand governed by the MOU 44 framework, where the island of Koh Kood and seabed oil and gas are at stake. Border clashes in 2025 caused deaths and mass displacement before an externally brokered ceasefire; since then crossings have periodically closed, both armies allege truce violations and build-ups, and Cambodia has pushed part of the maritime question toward UNCLOS. Coverage divides along national lines: Thai outlets frame the border and Koh Kood as inviolable Thai territory and Cambodia as the party breaching the boundary memoranda and provoking incidents; the Cambodian counter-claim -- that Thailand occupies Cambodian ground and that the ICJ ruling and demarcation favour Phnom Penh -- reaches the corpus mainly through international wire quotes, as no Cambodian outlets are present. Chinese state media cover the dispute as a showcase for their own mediation and ASEAN de-escalation rather than backing either territorial claim.',
    'Thailand und Kambodscha streiten um ihre Landgrenze -- im Zentrum stehen die Tempel Preah Vihear (vom IGH Kambodscha zugesprochen), Ta Moan und Ta Krabey aus dem 11. Jahrhundert sowie das unvermessene "Smaragddreieck" -- und um eine überlappende Seezone im Golf von Thailand, die durch das MOU-44-Rahmenwerk geregelt wird und in der die Insel Koh Kood sowie Öl- und Gasvorkommen umstritten sind. Grenzgefechte 2025 forderten Tote und Massenvertreibung, bevor eine extern vermittelte Waffenruhe zustande kam; seither waren Übergänge zeitweise geschlossen, beide Armeen werfen einander Verstöße und Aufmärsche vor, und Kambodscha verlagerte einen Teil der Seefrage zum UN-Seerechtsübereinkommen. Die Berichterstattung teilt sich entlang nationaler Linien: Thailändische Medien stellen die Grenze und Koh Kood als unverletzliches thailändisches Gebiet dar und Kambodscha als jene Partei, die die Grenzmemoranden bricht und Zwischenfälle provoziert; die kambodschanische Gegenposition -- Thailand besetze kambodschanischen Boden, und IGH-Urteil wie Vermessung sprächen für Phnom Penh -- erreicht das Korpus vor allem über internationale Agenturzitate, da keine kambodschanischen Medien vertreten sind. Chinesische Staatsmedien behandeln den Streit als Bühne für die eigene Vermittlung und die ASEAN-Deeskalation, statt einen der Gebietsansprüche zu stützen.'
);

-- 2. Narratives. Publisher-disjoint across the two territorial cards; the
--    Cambodian card is framing_required so neutral wire copy is not misfiled.
INSERT INTO narratives_v2 (
    id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de,
    actor_centroids, publishers, framing_keywords, framing_required, is_active
) VALUES
(
    'thaicam_thai_sovereignty_defence',
    'thailand_cambodia_border',
    1,
    2,
    'Thai sovereignty defence',
    'Thailändische Souveränitätsverteidigung',
    'The border and Koh Kood are Thai territory; Cambodia breaches the memoranda and provokes',
    'Die Grenze und Koh Kood sind thailändisches Gebiet; Kambodscha bricht die Memoranden und provoziert',
    'Thai framing (Thai press) treats the disputed frontier and the island of Koh Kood as inviolable Thai sovereign territory, and casts Cambodia as the party that repeatedly breaches the boundary memoranda (MOU 43/44), moves troops and tanks toward the line, and manufactures or exaggerates incidents. It presents the Royal Thai Army''s posture as defensive and lawful, frames Cambodia''s UNCLOS move over the maritime area as a unilateral provocation that Thailand need not answer, and treats calls to scrap MOU 43 as a response to Cambodian violations. Vocabulary: sovereignty, Thai territory, Koh Kood remains Thai, violation, breach, provocation, fake news, under control, crossings closed.',
    'Die thailändische Rahmung (thailändische Presse) behandelt die umstrittene Grenze und die Insel Koh Kood als unverletzliches thailändisches Hoheitsgebiet und stellt Kambodscha als jene Partei dar, die wiederholt die Grenzmemoranden (MOU 43/44) bricht, Truppen und Panzer an die Linie verlegt und Zwischenfälle inszeniert oder übertreibt. Die Haltung der Königlich Thailändischen Armee gilt als defensiv und rechtmäßig; Kambodschas UNCLOS-Vorstoß zum Seegebiet erscheint als einseitige Provokation, die Thailand nicht beantworten müsse.',
    ARRAY['ASIA-SOUTHEAST', 'ASIA-PACIFIC-THAILAND'],
    ARRAY['The Nation Thailand', 'Bangkok Post', 'Thai PBS World', 'Thai PBS'],
    ARRAY['sovereignty', 'Thai territory', 'Koh Kood', 'violation', 'breach', 'provocation',
          'fake news', 'under control', 'Souveränität', 'Provokation'],
    false,
    true
),
(
    'thaicam_cambodian_territorial_claim',
    'thailand_cambodia_border',
    2,
    -2,
    'Cambodian territorial claim',
    'Kambodschanischer Gebietsanspruch',
    'Thailand occupies Cambodian ground; the ICJ ruling and demarcation favour Cambodia',
    'Thailand besetzt kambodschanischen Boden; IGH-Urteil und Vermessung sprechen für Kambodscha',
    'Cambodian framing (reaching the corpus through international wire quotes, as no Cambodian outlets are present) holds that Thailand occupies Cambodian territory -- including ground it did not withdraw from after the ceasefire -- and that the 1962 and 2013 International Court of Justice rulings on Preah Vihear and the surrounding area, together with proper demarcation, establish Cambodia''s claim. It presents Cambodia as the aggrieved smaller party seeking demarcation, international adjudication and UNCLOS process rather than force. Vocabulary: occupying, occupied, Cambodian territory, aggression, incursion, ICJ ruling, 1962, demarcation, withdraw, aggrieved.',
    'Die kambodschanische Rahmung (die das Korpus über internationale Agenturzitate erreicht, da keine kambodschanischen Medien vertreten sind) besagt, dass Thailand kambodschanisches Gebiet besetzt -- auch Boden, aus dem es sich nach der Waffenruhe nicht zurückzog -- und dass die IGH-Urteile von 1962 und 2013 zu Preah Vihear samt Umland sowie eine ordentliche Vermessung Kambodschas Anspruch begründen. Kambodscha erscheint als benachteiligte kleinere Partei, die Vermessung, internationale Schlichtung und UNCLOS-Verfahren statt Gewalt sucht.',
    ARRAY['ASIA-SOUTHEAST'],
    ARRAY['Reuters', 'Associated Press', 'Channel NewsAsia', 'Al Jazeera', 'Straits Times',
          'France 24 (EN)', 'Philippine Daily Inquirer', 'Khaleej Times'],
    ARRAY['occupying', 'occupied', 'occupy', 'Cambodian territory', 'aggression', 'incursion',
          'ICJ', '1962', 'demarcation', 'withdraw', 'seized', 'besetzt', 'besetzen', 'Rückzug'],
    true,
    true
),
(
    'thaicam_great_power_mediation',
    'thailand_cambodia_border',
    3,
    0,
    'Great-power mediation',
    'Großmacht-Vermittlung',
    'Outside powers and ASEAN broker the ceasefire and urge both sides to de-escalate',
    'Externe Mächte und die ASEAN vermitteln die Waffenruhe und mahnen beide Seiten zur Deeskalation',
    'Mediation framing (Chinese state media) presents the conflict primarily as an occasion for external de-escalation, foregrounding China''s own mediation and Track-II diplomacy, ASEAN''s role under the chair, and the maintenance of the ceasefire, rather than endorsing either side''s territorial claim. It reports incidents in neutral terms -- often attributing them to Thai or Cambodian sources -- and stresses the economic cost of continued conflict and the value of a negotiated settlement. Vocabulary: mediation, peace process, ceasefire, de-escalation, ASEAN, dialogue, stability, Track II.',
    'Die Vermittlungs-Rahmung (chinesische Staatsmedien) stellt den Konflikt vor allem als Anlass externer Deeskalation dar und hebt Chinas eigene Vermittlung und Track-II-Diplomatie, die Rolle der ASEAN unter dem Vorsitz sowie die Wahrung der Waffenruhe hervor, ohne einen der Gebietsansprüche zu stützen. Zwischenfälle werden neutral berichtet -- oft thailändischen oder kambodschanischen Quellen zugeschrieben -- und die wirtschaftlichen Kosten eines fortdauernden Konflikts sowie der Wert einer Verhandlungslösung betont.',
    ARRAY['ASIA-CHINA', 'ASIA-SOUTHEAST'],
    ARRAY['Global Times', 'CGTN', 'China Daily', 'People''s Daily', 'Xinhua'],
    ARRAY['mediation', 'peace process', 'ceasefire', 'de-escalation', 'ASEAN', 'dialogue',
          'stability', 'Track II', 'Vermittlung', 'Waffenruhe'],
    false,
    true
);

COMMIT;

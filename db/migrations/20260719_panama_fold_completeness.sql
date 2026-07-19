-- Completeness fields + theater roll-up cards for the folded Panama atomic (2026-07-19)
--
-- Roll-up gap found by inspection (spec section 5.5): the theater's five active
-- cards are LatAm-national (+2), Chinese/Russian state (+1), Western mainstream
-- (-1), European (-2) and US-conservative (-2). The new atomic's +2 narrative
-- runs on Western mainstream publishers -- which have NO positive-sign card --
-- and its -2 narrative runs on Chinese/Russian state, which have no
-- negative-sign card. All 34 of its attributed titles were therefore homeless
-- on the theater page. Two cards added to close both holes.
--
-- Disjointness (the section 5.5 hard rule) re-checked per sign bucket:
--   positive: LatAm nationals | CN+RU state | Western mainstream  -> disjoint
--   negative: Western mainstream (-1) | European (-2) | US conservative (-2)
--             | CN+RU state (-2)                                  -> disjoint
-- Western mainstream now appears on both a + and a - card, and CN+RU state on
-- both a + and a - card. That is explicitly allowed: opposite signs pull
-- different-signed atomic titles, so no title can double-count.

BEGIN;

-- 1. Atomic completeness fields (bilingual, all four).
UPDATE friction_nodes SET
    description_en = 'Contests over who operates strategically sensitive port and canal infrastructure in the Americas -- concession cancellations, court-ordered operator changes, and the commercial and maritime retaliation that follows.',
    description_de = 'Auseinandersetzungen darüber, wer strategisch sensible Hafen- und Kanalinfrastruktur in Amerika betreibt -- Annullierung von Konzessionen, gerichtlich angeordnete Betreiberwechsel und die darauf folgenden kommerziellen und maritimen Vergeltungsmaßnahmen.',
    editorial_summary_en = 'Panama''s Supreme Court voided CK Hutchison''s concession over two Panama Canal terminals in January 2026 and handed operations to Maersk and MSC; Peru''s courts upheld state control of the Chinese-built Chancay port five months later. Beijing treated both as expropriation of its companies, warned Panama of "heavy prices", suspended Cosco''s port operations, pressed the European carriers to withdraw, and detained Panama-flagged vessels under port-state-control inspections -- drawing a joint US-and-allies statement backing Panama''s sovereignty. The contest is over operators and legal title, not the waterways themselves, and it is the sharpest test yet of how far a host state can unwind Chinese infrastructure positions without absorbing retaliation.',
    editorial_summary_de = 'Panamas Oberster Gerichtshof erklärte im Januar 2026 die Konzession von CK Hutchison für zwei Terminals am Panamakanal für nichtig und übertrug den Betrieb an Maersk und MSC; fünf Monate später bestätigten perus Gerichte die staatliche Kontrolle über den von China gebauten Hafen Chancay. Peking wertete beides als Enteignung seiner Unternehmen, drohte Panama mit "hohen Preisen", setzte den Hafenbetrieb von Cosco aus, drängte die europäischen Reedereien zum Rückzug und hielt Schiffe unter Panama-Flagge im Rahmen von Hafenstaatkontrollen fest -- woraufhin die USA und Verbündete in einer gemeinsamen Erklärung Panamas Souveränität bekräftigten. Der Streit dreht sich um Betreiber und Rechtstitel, nicht um die Wasserstraßen selbst, und ist der bislang schärfste Test dafür, wie weit ein Gastland chinesische Infrastrukturpositionen zurückdrehen kann, ohne Vergeltung zu tragen.',
    updated_at = NOW()
WHERE id = 'latam_port_infrastructure_control';

-- 2. Theater scope now includes Central America and the infrastructure-control
--    dimension; the old text said "in South America" and named only trade,
--    resources and contracts.
UPDATE friction_nodes SET
    description_en = 'Competition among external powers -- the United States, China and the European Union -- for trade terms, resource access, infrastructure contracts and control of strategic ports across Latin America.',
    description_de = 'Wettbewerb externer Mächte -- der Vereinigten Staaten, Chinas und der Europäischen Union -- um Handelsbedingungen, Rohstoffzugang, Infrastrukturaufträge und die Kontrolle strategischer Häfen in ganz Lateinamerika.',
    updated_at = NOW()
WHERE id = 'latam_hemispheric_theater';

-- 3. Drop 'reasserts' -- it pulled exactly one title, El País's "Trump
--    reasserts Washington's grip on Central America", which reads as critique
--    of US reassertion, not endorsement of the host state reclaiming control.
UPDATE narratives_v2
SET framing_keywords = array_remove(framing_keywords, 'reasserts'), updated_at = NOW()
WHERE id = 'port_control_restored';

-- 4. Two new theater cards.
INSERT INTO narratives_v2 (
    id, fn_id, display_order, stance, framing_required,
    name_en, name_de, claim_en, claim_de,
    stance_label_en, stance_label_de, actor_centroids, publishers, framing_keywords, is_active
) VALUES

('latam_theater_western_terms_hold', 'latam_hemispheric_theater', 7, 2, false,
 'The Western offer still sets the terms',
 'Das westliche Angebot gibt weiter den Ton an',
 'Across trade, minerals and infrastructure, Latin American states are still choosing rules, courts and partners anchored in the Western order -- cancelling opaque concessions, upholding regulatory control and contracting with European and North American operators -- and the pressure that follows from Beijing is read as vindication of the choice rather than a reason to reverse it.',
 'Ob Handel, Rohstoffe oder Infrastruktur: Lateinamerikanische Staaten setzen weiterhin auf Regeln, Gerichte und Partner der westlichen Ordnung -- sie annullieren intransparente Konzessionen, behaupten die regulatorische Kontrolle und vergeben Aufträge an europäische und nordamerikanische Betreiber. Der darauf folgende Druck aus Peking gilt als Bestätigung dieser Entscheidung, nicht als Grund zur Umkehr.',
 'Western-anchored rules prevail', 'Westlich verankerte Regeln setzen sich durch',
 ARRAY['AMERICAS-CENTRAL','AMERICAS-ANDEAN','AMERICAS-BRAZIL','AMERICAS-SOUTHERNCONE','AMERICAS-USA','NON-STATE-EU'],
 ARRAY['Reuters','Associated Press','AP News','Financial Times','Wall Street Journal','Bloomberg','Nikkei Asia','The Guardian','BBC News','New York Times','Washington Post','Deutsche Welle','El País','Le Monde','Euronews','EurActiv','France 24 (EN)','S&P Global','Japan Times','CNN','The Telegraph','Der Spiegel','Handelsblatt','Fox News'],
 ARRAY['ruling','court','sovereignt','control','agreement','deal','investment','partnership','de-risk','contract'],
 true),

('latam_theater_coercion_critique', 'latam_hemispheric_theater', 8, -2, false,
 'Washington coerces, Beijing is punished',
 'Washington erzwingt, Peking wird bestraft',
 'The region''s choices are not free ones: Washington converts commercial and legal processes into instruments of pressure, stripping Chinese firms of lawfully held assets and framing ordinary investment as a security threat, while presenting the result as Latin American sovereignty. What is described as de-risking is a hemispheric monopoly reasserted at the expense of the region''s own room to manoeuvre.',
 'Die Entscheidungen der Region sind keine freien: Washington macht kommerzielle und juristische Verfahren zu Druckmitteln, entzieht chinesischen Unternehmen rechtmäßig gehaltene Vermögenswerte und stellt gewöhnliche Investitionen als Sicherheitsbedrohung dar -- um das Ergebnis dann als lateinamerikanische Souveränität auszugeben. Was als De-Risking bezeichnet wird, ist ein wiederhergestelltes Monopol über die Hemisphäre auf Kosten des eigenen Handlungsspielraums der Region.',
 'Hemispheric coercion critique', 'Kritik an hemisphärischem Zwang',
 ARRAY['ASIA-CHINA','ASIA-HONGKONG','EUROPE-RUSSIA'],
 ARRAY['Global Times','People''s Daily','CGTN','China Daily','Xinhua','RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti'],
 ARRAY['cold war mentality','coercion','smear','hegemon','unilateral','interference','rights and interests','politiciz','hypocri','bullying'],
 true)

ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id, display_order = EXCLUDED.display_order,
    stance = EXCLUDED.stance, name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
    stance_label_en = EXCLUDED.stance_label_en, stance_label_de = EXCLUDED.stance_label_de,
    actor_centroids = EXCLUDED.actor_centroids, publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords, is_active = true, updated_at = NOW();

COMMIT;

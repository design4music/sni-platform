-- Great Lakes: THEATER-level narrative cards (§5.5), 2026-07-20.
--
-- The theater page renders cards only if the theater FN has its own
-- narratives_v2 rows. These are cross-cutting meta-framings; they carry no
-- bundle and match nothing directly. THEATER_ROLLUP_SQL sources each card from
-- the member atomics' title_narratives where sign(atomic.stance) =
-- sign(theater.stance) AND publisher IN the card's publishers[].
--
-- Because the match is (sign, publisher) ONLY -- never the narrative -- the
-- publisher lists below were built from a measured per-publisher, per-sign
-- roll-up rather than from assumption. Counts are uncapped, so cards of the
-- SAME SIGN must be publisher-disjoint or they double-count.
--
-- Expected: +2 card 28 titles / -2 card 38 / -1 card 4. Negative bucket
-- verified disjoint.
--
-- ---------------------------------------------------------------------------
-- TWO BLOCS ARE DELIBERATELY LEFT OFF EVERY CARD (the south_asia rule:
-- a bloc that switches sides by atomic belongs on NO card -- homeless beats
-- mislabelled).
--
--   Anadolu Agency -- 3 negative titles spread across drc_accords_stalling,
--     m23_externally_backed_offensive AND drc_sanctions_rejected. It carries
--     both the proxy-war reading and the accused party's rejection of it. On
--     the Western card its Kabila-denunciation title would be mislabelled; on
--     the regional-scepticism card its proxy-war title would be. Excluded.
--
--   Press TV -- its single negative title is "More than 200 killed in coltan
--     mine collapse in east Congo", a human-cost story, not a sovereignty
--     critique. Putting it on the regional-scepticism card to avoid an empty
--     state-media card would mislabel it. Excluded; the same collapse is
--     covered on the Western card by AP, Guardian, BBC, Le Monde and DW.
--
-- The Standard is likewise OFF the positive card: its only positive-signed
-- title is "Rwanda hits back at US sanctions" (m23_backing_charge_rejected,
-- +1), which would read as evidence that engagement is working. It appears on
-- the -1 card instead, where both its titles genuinely fit.
--
-- NOTE ON THE ABSENT STATE-MEDIA CARD. Ukraine, Arctic and us_china all carry a
-- Russia/China counter-card. This theater gets none, and that is a finding
-- rather than an omission: across 180 days RT published one DRC title, and
-- Chinese state media published NO DRC-minerals titles at all. There is no
-- Russian or Chinese narrative presence in this theater to card.
--
-- No bootstrap run needed -- the roll-up is computed live at query time.

BEGIN;

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'great_lakes_engagement_working',
    'great_lakes_theater',
    'Outside engagement is starting to bite',
    'Auswärtiges Engagement beginnt zu wirken',
    'After years in which external actors declared concern and did little, the instruments finally have teeth: a monitoring mechanism signed in Switzerland, prisoners released and humanitarian corridors agreed, financial designations placed on a neighbouring army and on a former head of state, and capital moving into Congolese mining assets rather than around them. Engagement of this kind is treated as the one lever that has moved anything.',
    'Nach Jahren, in denen äußere Akteure Besorgnis erklärten und wenig taten, haben die Instrumente endlich Wirkung: ein in der Schweiz unterzeichneter Überwachungsmechanismus, freigelassene Gefangene und vereinbarte humanitäre Korridore, Finanzlistungen gegen eine Nachbararmee und einen früheren Staatschef, und Kapital, das in kongolesische Bergbauwerte fließt statt an ihnen vorbei. Ein solches Engagement gilt als der einzige Hebel, der überhaupt etwas bewegt hat.',
    2,
    'Engagement is delivering',
    'Engagement zeigt Wirkung',
    ARRAY['AFRICA-DRC', 'AMERICAS-USA'],
    ARRAY['Mining.com', 'Bloomberg', 'S&P Global', 'OilPrice', 'The Australian', 'Egypt Today', 'France 24', 'France 24 (EN)', 'Le Monde', 'Le Figaro', 'Reuters', 'Associated Press', 'The Guardian', 'BBC', 'BBC World', 'Deutsche Welle', 'Washington Post', 'Financial Times', 'Al Jazeera', 'Swissinfo', 'ANSA', 'news.un.org', 'UN News', 'News24', 'Daily Nation', 'Punch Newspapers'],
    ARRAY['signed', 'agreement', 'progress', 'release', 'investment', 'stake', 'sanctions', 'designat', 'monitoring', 'corridor', 'accord', 'signé', 'progrès', 'investissement', 'Abkommen', 'Fortschritt', 'Investition'],
    false, 1, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'great_lakes_proxy_war_and_its_costs',
    'great_lakes_theater',
    'A cross-border war paid for by civilians',
    'Ein grenzüberschreitender Krieg, den Zivilisten bezahlen',
    'The dominant international reading treats the fighting in the east as one system rather than several problems: an insurgency sustained from across a border, a mediation track that is signed but not observed, and an extraction economy that runs through the same contested ground. What connects them is who absorbs the cost -- populations detained in captured towns, displaced across borders, killed by strikes meant for combatants, or buried in a collapsed mine on territory the armed group controls.',
    'Die vorherrschende internationale Lesart behandelt die Kämpfe im Osten als ein System, nicht als mehrere Probleme: ein von jenseits der Grenze getragener Aufstand, ein Vermittlungsweg, der unterzeichnet, aber nicht eingehalten wird, und eine Rohstoffwirtschaft, die durch dasselbe umkämpfte Gebiet läuft. Verbunden sind sie durch die Frage, wer die Kosten trägt -- Menschen, die in eroberten Städten festgehalten, über Grenzen vertrieben, von Angriffen auf Kombattanten getötet oder in einer eingestürzten Mine im Gebiet der bewaffneten Gruppe verschüttet werden.',
    -2,
    'Proxy war and human cost',
    'Stellvertreterkrieg und menschliche Kosten',
    ARRAY['AFRICA-DRC'],
    ARRAY['France 24', 'France 24 (EN)', 'Le Monde', 'Le Figaro', 'Reuters', 'Associated Press', 'The Guardian', 'BBC', 'BBC World', 'Deutsche Welle', 'Washington Post', 'Financial Times', 'The Economist', 'Al Jazeera', 'Daily Sabah', 'TRT World', 'Punch Newspapers', 'Swissinfo', 'ANSA', 'La Repubblica', 'Der Spiegel', 'Folha de S.Paulo', 'Globe and Mail', 'Wall Street Journal', 'Council on Foreign Relations', 'Janes', 'DR', 'news.un.org', 'UN News'],
    ARRAY['civilians', 'displaced', 'killed', 'abuse', 'atrocities', 'backing', 'proxy', 'stalled', 'violation', 'toxic', 'collapse', 'civils', 'déplacés', 'atrocités', 'soutien', 'éboulement', 'Zivilisten', 'Vertriebene', 'Unterstützung', 'Gräueltaten'],
    false, 2, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'great_lakes_scepticism_of_outside_fixes',
    'great_lakes_theater',
    'African scepticism about externally designed fixes',
    'Afrikanische Skepsis gegenüber extern entworfenen Lösungen',
    'Regional and African coverage is markedly cooler about solutions drafted elsewhere. The accords are reported as documents both sides accuse each other of breaking, the designations as measures the targeted governments simply reject, and the minerals arrangement as terms a neighbouring energy minister publicly contests and a Congolese figure calls constitutionally doubtful. The common thread is a question about who wrote the terms and who carries the consequences.',
    'Die regionale und afrikanische Berichterstattung ist deutlich kühler gegenüber Lösungen, die anderswo entworfen wurden. Die Abkommen erscheinen als Dokumente, deren Bruch sich beide Seiten gegenseitig vorwerfen, die Listungen als Maßnahmen, die die betroffenen Regierungen schlicht zurückweisen, und die Rohstoffvereinbarung als Konditionen, die ein Energieminister des Nachbarlands öffentlich bestreitet und ein kongolesischer Akteur für verfassungsrechtlich zweifelhaft hält. Verbindend ist die Frage, wer die Bedingungen geschrieben hat und wer die Folgen trägt.',
    -1,
    'Scepticism about outside terms',
    'Skepsis gegenüber fremden Bedingungen',
    ARRAY['AFRICA-DRC'],
    ARRAY['The Standard', 'Daily Nation', 'Daily Maverick', 'Mail & Guardian', 'News24', 'Al-Ahram'],
    ARRAY['rejects', 'denounces', 'unjustified', 'unconstitutional', 'flawed', 'clashes with', 'sovereignty', 'accusations', 'trade accusations', 'souveraineté', 'injustifié', 'Souveränität', 'ungerechtfertigt'],
    false, 3, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

COMMIT;

-- US-Russia theater: split the Kremlin stance on the bilateral channel. 2026-07-19.
--
-- THE BUG THIS FIXES IS A LABELLING BUG, not a count bug -- and it was only
-- visible by reading the titles behind the number. us_russia_washington_realism
-- ("Washington is returning to realism") held 428 titles because it was
-- framing_required=false, so it swept the ENTIRE Russian-state publisher bloc in
-- scope. But a large share of that bloc is Lavrov/Zakharova attacking the US --
-- "US actions do not fit into any international legal framework", "Rubio's
-- disingenuous statements", "West is at war with Russia, US policy unchanged
-- under Trump", "US drifting from role as objective mediator", "act of piracy".
-- Filing those under "Washington is becoming realistic" states the opposite of
-- what the source said. A card that reads "Russia says the US is coming around"
-- over headlines where Russia says the US is acting in bad faith is exactly the
-- corrosive mislabel §5 warns about.
--
-- Mechanism: the §5 three-stance device applied WITHIN one camp. Both Kremlin
-- narratives now share the Russian-state bloc and both carry
-- framing_required=true with disjoint keyword sets, so framing -- not publisher
-- -- decides which of the two contradictory Kremlin messages a title carries.
-- Titles matching neither are dropped: precision over recall (§4), and a
-- smaller correctly-labelled card beats a large mislabelled one.
--
-- Sign consequence: the new bad-faith card is -2, so the theater's negative
-- bucket now holds Russian(-2) + Western(-1). Verified publisher-disjoint
-- (Russian state vs Western/Ukrainian), so roll-up counts still partition.
-- A -2 theater card is added so those titles are not homeless at theater level.

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Kremlin stance A (+2): the US is coming around. Now framing-gated.
-- ---------------------------------------------------------------------------
UPDATE narratives_v2 SET
    framing_keywords = ARRAY[
      'ready to work','ready for','not frozen','positively','constructive','positive',
      'mutually beneficial','multipolar','equality','equal footing','respect','interests',
      'future economic ties','economic ties','investors','participation','lend them an ear',
      'congratulat','thanks','agreements in Alaska','Alaska','re-establish','reestablish',
      'resume','restore','high-level','military contacts','conversation','signals',
      'готов','взаимовыгодн','многополярн','равноправ','конструктивн','возобновл','контакт'
    ],
    framing_required = true,
    updated_at = NOW()
WHERE id = 'us_russia_washington_realism';

-- ---------------------------------------------------------------------------
-- 2. NEW Kremlin stance B (-2): Washington negotiates in bad faith
-- ---------------------------------------------------------------------------
INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_washington_bad_faith',
    'us_russia_bilateral_channel',
    'Washington talks while acting in bad faith and refusing to treat Russia as an equal',
    'Washington verhandelt, handelt dabei aber unaufrichtig und verweigert Russland den Status eines Gleichberechtigten',
    'Russian state coverage in its adversarial register: the channel exists but Washington stalls, issues ultimatums, drifts from the mediator role it claimed, presses Europe to carry the cost of containment, and pursues Russian companies commercially while talking cooperation. US policy is presented as unchanged in substance regardless of administration. Vocabulary: ultimatums, stalling, disingenuous, double standards, at war with Russia, unchanged, drifting, piracy, pushes out.',
    'Russische staatliche Berichterstattung im konfrontativen Register: Der Kanal besteht, doch Washington hinhaltet, stellt Ultimaten, entfernt sich von der beanspruchten Vermittlerrolle, drängt Europa, die Kosten der Eindämmung zu tragen, und verfolgt russische Unternehmen kommerziell, während es von Zusammenarbeit spricht. Die US-Politik gelte inhaltlich als unverändert, unabhängig von der Regierung. Vokabular: Ultimaten, Hinhalten, Doppelstandards, unverändert.',
    -2, 'Washington acts in bad faith', 'Washington handelt unaufrichtig',
    ARRAY['EUROPE-RUSSIA','AMERICAS-USA'],
    ARRAY[
      'ultimatum','stalling','stalled','stagnant','disingenuous','hypocri','double standard',
      'at war with','drifting','objective mediator','not fit','legal framework','piracy',
      'provocation','blame','accuses','accus','criticiz','criticis','slams','condemn',
      'unchanged','bear the cost','push','out of global business','energy grab','interference',
      'ультиматум','лицемер','двойны','обвин','критику','неизменн','провокац'
    ],
    true,
    ARRAY['TASS (EN)','TASS','tass.ru','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Kommersant','Izvestia','Sputnik','BelTA Russian','Rossiyskaya Gazeta','Interfax'],
    4
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

-- ---------------------------------------------------------------------------
-- 3. Theater card for the Kremlin adversarial register (-2)
-- ---------------------------------------------------------------------------
INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_theater_kremlin_grievance',
    'us_russia_theater',
    'Washington cannot be trusted to keep its side of any bargain',
    'Auf Washington ist bei keiner Vereinbarung Verlass',
    'The cross-cutting Russian state framing that runs against its own optimistic register: whatever is agreed, the US stalls, attaches ultimatums, keeps squeezing Russian companies and shifts the burden of confrontation onto Europe. Engagement is worth pursuing, but American commitments are treated as provisional.',
    'Der übergreifende russische Staatsrahmen, der seinem eigenen optimistischen Register widerspricht: Was auch vereinbart werde, die USA hinhielten, knüpften Ultimaten daran, setzten russische Unternehmen weiter unter Druck und verlagerten die Last der Konfrontation auf Europa. Gespräche lohnten sich, doch amerikanische Zusagen gälten als vorläufig.',
    -2, 'American commitments are provisional', 'Amerikanische Zusagen sind vorläufig',
    ARRAY['EUROPE-RUSSIA','AMERICAS-USA'],
    ARRAY['ultimatum','stalling','stagnant','double standard','at war with','drifting','unchanged','bear the cost','accus','ультиматум','лицемер','обвин'],
    false,
    ARRAY['TASS (EN)','TASS','tass.ru','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Kommersant','Izvestia','Sputnik','BelTA Russian','Rossiyskaya Gazeta','Interfax'],
    5
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

COMMIT;

-- US-Russia theater: narrative recalibration after reading real per-narrative
-- samples (spec §0a step 9). 2026-07-19.
--
-- First measurement exposed a severe recall asymmetry:
--     Russian-state cards   428 / 85 / 47 titles
--     Western cards           2 /  2 /  6 / 0 titles
--
-- THREE distinct causes, all found by reading titles rather than trusting counts:
--
-- 1. PUBLISHER BLOC TOO NARROW. The international mainstream actually covering
--    this theater -- Japan Times, Straits Times, Globe and Mail, Jerusalem Post,
--    Al Jazeera, Kyodo, France 24 -- was absent from every Western card, so
--    on-stance headlines ("End of U.S.-Russia nuclear pact raises fears of
--    unchecked arms race", Japan Times) matched nothing. Added as INTL bloc.
--
-- 2. FRAMING KEYWORDS DRAFTED FROM EXPECTATION, NOT CORPUS (the Australia
--    lesson: draft vocabulary from BOTH camps' real headlines). Reuters wrote
--    "New arms race looms as clock ticks down on last Russia-US nuclear treaty";
--    my list had "last remaining" and "fears of" but not "arms race" or "looms",
--    so it fell through. Keywords below are harvested from actual titles.
--
-- 3. A WHOLE CAMP WAS MISSING. A large share of sanctions coverage is Indian /
--    Global South buyer coverage -- "Never Depended On Permission", Jaishankar's
--    "they do it when it suits them", Reliance pivoting back, Bangladesh seeking
--    a diesel waiver. Its stance is neither Western-pragmatic nor pro-Kremlin:
--    it treats US permission as illegitimate to begin with and the waiver as
--    vindication of not complying. Given its own card (+1, publisher-disjoint
--    from both other positive cards).
--
-- ALSO: us_russia_treaty_constrains_only_us DEACTIVATED. The hawkish "a new
-- treaty would bind only Washington" framing returns exactly ONE title in 180
-- days and it is TASS. I drafted that stance from training-data expectation --
-- it was the shape of the 2019-2023 debate, not of the 2026 corpus, which is
-- almost uniformly "the expiry is dangerous". Same error class as the
-- us_russia_election_interference shell this build already retired. Removing a
-- stance the corpus does not support beats forcing keywords to find it.
--
-- Publisher-disjointness for the theater roll-up (§5.5) re-verified: positive
-- bucket now holds THREE cards -- Western+INTL / Russian state / Global South --
-- with no publisher in more than one. Dawn, Anadolu, TRT and Daily Sabah are
-- assigned to the Global South bloc ONLY; Al Jazeera, Japan Times, Straits
-- Times, Globe and Mail, Jerusalem Post to the INTL bloc ONLY.

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Retire the unsupported hawkish arms-control stance
-- ---------------------------------------------------------------------------
UPDATE narratives_v2 SET is_active = false, updated_at = NOW()
WHERE id = 'us_russia_treaty_constrains_only_us';

-- ---------------------------------------------------------------------------
-- 2. Arms control (+1): add INTL bloc + corpus-harvested keywords
-- ---------------------------------------------------------------------------
UPDATE narratives_v2 SET
    framing_keywords = ARRAY[
      'arms race','looms','clock ticks','uncharted','grave moment','expires','expiry',
      'expire','lapse','no more nuclear limits','no nuclear limits','without nuclear limits',
      'unconstrained','unchecked','end of','ends decades','last remaining','last Russia-US',
      'raises fears','fears of','warns','urges','negotiate new','new nuclear','close in on deal',
      'extension','predictability','verification','guardrails','opening door',
      'ausgelaufen','beendet','Obergrenzen','Abrüstungsvertrag','läuft aus','warnt','Wettrüsten',
      'désarmement','proroga','scadenza'
    ],
    publishers = publishers || ARRAY[
      'Japan Times','Straits Times','Channel NewsAsia','Nikkei Asia','Jerusalem Post',
      'Times of Israel','Bangkok Post','Kyodo News','NHK World','Al Jazeera','France 24',
      'Novinite','Yonhap','KBS World'
    ],
    updated_at = NOW()
WHERE id = 'us_russia_new_treaty_needed';

-- ---------------------------------------------------------------------------
-- 3. Sanctions relief (+1 pragmatic): corpus-harvested stance vocabulary
-- ---------------------------------------------------------------------------
UPDATE narratives_v2 SET
    framing_keywords = ARRAY[
      'market stability','supply','energy prices','easing energy','eases energy',
      'take a little pressure off','pressure off','back on market','weighs easing',
      'temporary','short-term','stranded at sea','stranded','crunches supplies',
      'vulnerable countries','ride out','avert','gambled','keeps','lifeline',
      'Marktstabilität','vorübergehend','Versorgung','Ölpreis'
    ],
    publishers = publishers || ARRAY[
      'Japan Times','Jerusalem Post','Times of Israel','Globe and Mail','Al Jazeera',
      'France 24','Novinite','Kyodo News','NHK World','Bangkok Post'
    ],
    updated_at = NOW()
WHERE id = 'us_russia_relief_pragmatic';

-- ---------------------------------------------------------------------------
-- 4. Sanctions relief (-1 critical): corpus-harvested stance vocabulary
-- ---------------------------------------------------------------------------
UPDATE narratives_v2 SET
    framing_keywords = ARRAY[
      'gift to Putin','coup for Putin','windfall','U-turn','U-Turn','rewards','defy Trump',
      'sanctions bill','unblock','splits with','clash over','self-defeating','hand Moscow',
      'give Moscow','emboldens','without concessions','no concessions','squander','critics',
      'senators','despite','blockade','pay off','fails to','won''t withstand','lost standing',
      'Geschenk','Kehrtwende','belohnt','Kritik'
    ],
    updated_at = NOW()
WHERE id = 'us_russia_relief_rewards_moscow';

-- ---------------------------------------------------------------------------
-- 5. NEW -- third-country buyer autonomy (+1, Global South bloc)
-- ---------------------------------------------------------------------------
INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_buyer_autonomy',
    'us_russia_sanctions_leverage',
    'Sovereign buyers never accepted that US permission was required',
    'Souveräne Käufer haben nie akzeptiert, dass eine US-Erlaubnis nötig wäre',
    'Indian, Turkish and wider Global South coverage treating the waivers less as American generosity than as confirmation that the restrictions were unenforceable: purchases continued through every phase, energy security is a sovereign decision, and Washington relaxes or tightens the rules according to its own needs. Vocabulary: never depended on permission, when it suits them, energy security, sovereign choice, lifeline, will continue buying.',
    'Indische, türkische und breitere Berichterstattung des Globalen Südens behandelt die Ausnahmegenehmigungen weniger als amerikanische Großzügigkeit denn als Bestätigung, dass die Beschränkungen nicht durchsetzbar waren: Die Käufe liefen in jeder Phase weiter, Energiesicherheit sei eine souveräne Entscheidung, und Washington lockere oder verschärfe die Regeln nach eigenem Bedarf. Vokabular: nie auf Erlaubnis angewiesen, Energiesicherheit, souveräne Entscheidung.',
    1, 'Buying is a sovereign choice', 'Kaufen ist eine souveräne Entscheidung',
    ARRAY['AMERICAS-USA','EUROPE-RUSSIA','ASIA-INDIA'],
    ARRAY['never depended','permission','suits them','mind his business','sovereign','energy security',
          'will continue','continue buying','keep buying','regardless','lifeline','discount',
          'national interest','our own','refiners','Reliance','crude imports','surge'],
    false,
    ARRAY['NDTV','Times of India','Hindustan Times','The Hindu','Indian Express','WION',
          'Republic TV','Business Standard','Mint','Economic Times','Firstpost','Dawn',
          'Anadolu Agency','TRT World','Daily Sabah','Al Arabiya','Al-Ahram','The News','Press TV'],
    4
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

-- ---------------------------------------------------------------------------
-- 6. Bilateral channel: Western cards. NOTE the honest asymmetry here -- Western
--    outlets overwhelmingly file these events as UKRAINE-WAR coverage, while
--    Russian state media write about the bilateral relationship as a subject in
--    its own right. Keywords are therefore kept genuinely bilateral rather than
--    widened into Ukraine vocabulary, which would just duplicate
--    ukraine_peace_negotiations. These cards stay legitimately smaller.
-- ---------------------------------------------------------------------------
UPDATE narratives_v2 SET
    framing_keywords = ARRAY[
      're-establish','reestablish','resume','resumed','high-level','military contacts',
      'military talks','channel','not frozen','bilateral ties','restore','constructive',
      'working toward','deconflict','only route','pragmatic','breakthrough','thaw',
      'ice breaks','engage','Kanal','Wiederaufnahme','konstruktiv','Annäherung'
    ],
    publishers = publishers || ARRAY[
      'Japan Times','Jerusalem Post','Times of Israel','Globe and Mail','Al Jazeera',
      'France 24','Kyodo News','NHK World','Bangkok Post','Novinite'
    ],
    updated_at = NOW()
WHERE id = 'us_russia_engagement_necessary';

UPDATE narratives_v2 SET
    framing_keywords = ARRAY[
      'legitimis','legitimiz','over their heads','sidelined','without Europe','excluded',
      'premature','rehabilitat','fatal mistake','rewards','patience wears thin','wears thin',
      'not invited','no invitation','rejects Europe','lost mediator','lost standing',
      'doubt','concession','piles pressure','pressure on Kyiv','weak','stalled','stalling',
      'legitimieren','Abseits','verfrüht','ohne Europa','Zugeständnis','Druck auf'
    ],
    updated_at = NOW()
WHERE id = 'us_russia_normalisation_premature';

-- ---------------------------------------------------------------------------
-- 7. Theater cards: mirror the bloc changes; add the Global South card so the
--    buyer-autonomy titles are not homeless at theater level.
-- ---------------------------------------------------------------------------
UPDATE narratives_v2 SET
    publishers = publishers || ARRAY[
      'Japan Times','Straits Times','Channel NewsAsia','Nikkei Asia','Jerusalem Post',
      'Times of Israel','Bangkok Post','Kyodo News','NHK World','Al Jazeera','France 24',
      'Novinite','Yonhap','KBS World','Globe and Mail'
    ],
    updated_at = NOW()
WHERE id = 'us_russia_theater_engagement_case';

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_theater_buyer_autonomy',
    'us_russia_theater',
    'Third countries treat the rivalry as something to navigate, not to join',
    'Drittstaaten betrachten die Rivalität als etwas, das zu navigieren, nicht mitzutragen ist',
    'The cross-cutting Global South framing that the US-Russia relationship is a set of conditions to be managed rather than a side to be chosen: energy purchases continue through every phase of pressure and relief, the rules are seen to move with Washington''s domestic needs, and sovereign interest rather than alignment governs the response.',
    'Der übergreifende Rahmen des Globalen Südens, wonach das Verhältnis USA-Russland Rahmenbedingungen setzt, die zu bewältigen sind, statt eine Seite, für die man sich entscheidet: Energiekäufe laufen durch alle Phasen von Druck und Lockerung weiter, die Regeln folgen erkennbar innenpolitischen Bedürfnissen Washingtons, und souveränes Interesse statt Bündnistreue bestimmt die Reaktion.',
    1, 'Navigating, not choosing sides', 'Navigieren statt Seitenwahl',
    ARRAY['AMERICAS-USA','EUROPE-RUSSIA','ASIA-INDIA'],
    ARRAY['never depended','permission','suits them','sovereign','energy security','continue buying','regardless','lifeline','national interest'],
    false,
    ARRAY['NDTV','Times of India','Hindustan Times','The Hindu','Indian Express','WION',
          'Republic TV','Business Standard','Mint','Economic Times','Firstpost','Dawn',
          'Anadolu Agency','TRT World','Daily Sabah','Al Arabiya','Al-Ahram','The News','Press TV'],
    4
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

COMMIT;

-- US-Russia theater: atomic + theater narratives (greenfield, 2026-07-19).
--
-- All three atomics are OWN-GOAL SHAPED (§5): the normally-supportive Western
-- bloc is itself split, because the friction is not "US vs Russia" but "how much
-- accommodation of Moscow is right", and Western outlets sit on BOTH sides of
-- that. Publisher coalition alone therefore cannot disambiguate stance, so each
-- atomic uses the three-stance gradient:
--     +1 Western pragmatic    (framing_required=true)  \ SAME publisher bloc,
--     -1 Western critical     (framing_required=true)  / framing separates them
--     +2 Russian state        (framing_required=false)   disjoint bloc
-- Ukrainian outlets appear ONLY in the -1 cards -- they are never pro-relief.
--
-- CHINESE STATE MEDIA DELIBERATELY GET NO CARD. Global Times/CGTN coverage here
-- is "China calls on US to resume strategic stability dialogue with Russia" --
-- i.e. urging arms control, NOT "US drives the arms race". Filing them beside
-- the Russian bloc would mislabel them. Homeless beats mislabelled
-- (south_asia_theater lesson). The rift-exploitation caveat (§5) does not apply:
-- this is not an intra-Western dispute with Russia as bystander -- Russia is a
-- principal party, so its coverage belongs on the dispute's own axis.
--
-- Theater cards (§5.5) -- publisher-DISJOINT within each sign bucket:
--     +1 Western engagement case   Western mainstream       \ positive bucket,
--     +2 Kremlin vindication       Russian state            / disjoint blocs
--     -1 Western alarm             Western mainstream + Ukrainian  (sole negative)
--
-- Reversible: INSERT ... ON CONFLICT DO UPDATE, no DELETE.

BEGIN;

-- ===========================================================================
-- A. us_russia_sanctions_leverage -- axis: is US sanctions relief justified?
-- ===========================================================================

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_relief_pragmatic',
    'us_russia_sanctions_leverage',
    'Sanctions relief is a pragmatic response to energy-market reality',
    'Sanktionslockerung ist eine pragmatische Reaktion auf die Lage am Energiemarkt',
    'Western mainstream and business coverage arguing that waivers on Russian crude were forced by supply conditions — the Iran war, stranded cargoes, refiners and importers such as India needing barrels — and that keeping oil flowing while retaining the legal architecture of sanctions is the responsible course. Vocabulary: market stability, supply, waiver, temporary, stranded at sea, short-term step.',
    'Westliche Leit- und Wirtschaftsmedien argumentieren, Ausnahmegenehmigungen für russisches Rohöl seien durch die Versorgungslage erzwungen worden — der Iran-Krieg, festsitzende Ladungen, Raffinerien und Importeure wie Indien, die Barrel benötigen — und es sei verantwortungsvoll, das Öl fließen zu lassen und zugleich das rechtliche Sanktionsgerüst zu erhalten. Vokabular: Marktstabilität, Versorgung, Ausnahmegenehmigung, vorübergehend.',
    1, 'Relief is pragmatic', 'Lockerung ist pragmatisch',
    ARRAY['AMERICAS-USA','EUROPE-RUSSIA'],
    ARRAY['market stability','supply','temporary','short-term','stranded at sea','stranded','prices soar','avoid a price','keep oil flowing','vulnerable countries','crunches supplies','ride out','Marktstabilität','vorübergehend','Versorgung','Ölpreis'],
    true,
    ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Euronews','Corriere della Sera','La Repubblica','France 24 (EN)','France 24','Tagesschau','Frankfurter Allgemeine','Globe and Mail','ABC News','MSNBC','Fox News','Die Zeit','Der Spiegel','Süddeutsche Zeitung','Handelsblatt','The Economist','Sky News','El País','Der Standard','Die Presse','Kurier','EurActiv','OilPrice','S&P Global','Straits Times','Channel NewsAsia','Nikkei Asia'],
    1
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_relief_rewards_moscow',
    'us_russia_sanctions_leverage',
    'Easing sanctions hands Moscow a windfall and squanders the West''s main lever',
    'Die Lockerung der Sanktionen verschafft Moskau unerwartete Einnahmen und verspielt den wichtigsten Hebel des Westens',
    'Western mainstream, transatlantic-critical and Ukrainian coverage arguing that the waivers transfer billions to the Russian budget while the war continues, that they were granted without reciprocal concessions, and that they split the US from European and British partners still tightening enforcement. Same publisher bloc as the pragmatic stance, so framing separates them. Vocabulary: gift to Putin, coup for Putin, windfall, U-turn, splits with, clash over, rewards.',
    'Westliche Leitmedien, transatlantisch-kritische und ukrainische Berichterstattung argumentieren, die Ausnahmen überwiesen Milliarden an den russischen Haushalt, während der Krieg weitergeht, sie seien ohne Gegenleistung gewährt worden und trennten die USA von europäischen und britischen Partnern, die die Durchsetzung weiter verschärfen. Gleicher Publisher-Block wie die pragmatische Position, daher trennt das Framing. Vokabular: Geschenk an Putin, Kehrtwende, Bruch mit.',
    -1, 'Relief rewards Moscow', 'Lockerung belohnt Moskau',
    ARRAY['AMERICAS-USA','EUROPE-RUSSIA','EUROPE-UKRAINE'],
    ARRAY['gift to Putin','coup for Putin','windfall','U-turn','rewards','splits with','clash over','self-defeating','hand Moscow','give Moscow','$10','emboldens','without concessions','no concessions','squander','critics','senators say','Geschenk','Kehrtwende','belohnt','Kritik','Milliarden für Moskau'],
    true,
    ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Euronews','Corriere della Sera','La Repubblica','France 24 (EN)','France 24','Tagesschau','Frankfurter Allgemeine','Globe and Mail','ABC News','MSNBC','Fox News','Die Zeit','Der Spiegel','Süddeutsche Zeitung','Handelsblatt','The Economist','Sky News','El País','Der Standard','Die Presse','Kurier','EurActiv','Atlantic Council','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House','Kyiv Post','Kyiv Independent','Ukrinform'],
    2
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_sanctions_illegitimate',
    'us_russia_sanctions_leverage',
    'Unilateral sanctions have failed and Washington has been forced to admit it',
    'Einseitige Sanktionen sind gescheitert, und Washington musste dies eingestehen',
    'Russian state coverage framing the waivers as proof that restrictions on Russian energy were always unworkable: the world market needs Russian barrels, buyers keep buying, and the US has quietly conceded the point while continuing to demand that Europe bear the cost of containment. Sanctions are cast as illegitimate extraterritorial coercion rather than lawful policy. Vocabulary: de-facto admitted, crucial for market, illegal, unilateral, pressure has failed, respect our interests.',
    'Russische staatliche Berichterstattung stellt die Ausnahmen als Beweis dar, dass Beschränkungen für russische Energie nie funktionierten: Der Weltmarkt brauche russische Barrel, Käufer kauften weiter, und die USA hätten dies stillschweigend eingeräumt, während sie weiter verlangten, dass Europa die Kosten der Eindämmung trage. Sanktionen gelten als illegitimer extraterritorialer Zwang. Vokabular: faktisch eingeräumt, unverzichtbar, illegal, einseitig, gescheitert.',
    2, 'Sanctions were always unworkable', 'Sanktionen waren nie tragfähig',
    ARRAY['EUROPE-RUSSIA','AMERICAS-USA'],
    ARRAY['de-facto admitted','crucial for','market needs','illegal','illegitimate','unilateral','failed','respect','interests','forced to','climb down','extraterritorial','bear the cost','ослабление санкций','незаконн','односторонн','провал'],
    false,
    ARRAY['TASS (EN)','TASS','tass.ru','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Kommersant','Izvestia','Sputnik','BelTA Russian','Rossiyskaya Gazeta','Interfax'],
    3
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

-- ===========================================================================
-- B. us_russia_bilateral_channel -- axis: is engagement with Moscow right?
-- ===========================================================================

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_engagement_necessary',
    'us_russia_bilateral_channel',
    'Keeping a working channel with Moscow is how wars are ended and accidents avoided',
    'Ein funktionierender Gesprächskanal mit Moskau beendet Kriege und verhindert Zwischenfälle',
    'Western mainstream coverage treating the restored contacts — envoy trips, the resumed high-level military channel, foreign-minister phone calls — as the ordinary machinery of great-power management: without it there is no route to a settlement, no deconfliction, and no arms-control conversation. Vocabulary: channel, deconfliction, constructive, re-establish, working toward, only route.',
    'Westliche Leitmedien behandeln die wiederhergestellten Kontakte — Reisen von Sondergesandten, der wieder aufgenommene militärische Kanal auf hoher Ebene, Telefonate der Außenminister — als das gewöhnliche Instrumentarium des Großmächtemanagements: Ohne ihn gibt es keinen Weg zu einer Regelung, keine Deeskalation und kein Gespräch über Rüstungskontrolle. Vokabular: Kanal, Deeskalation, konstruktiv, Wiederaufnahme.',
    1, 'Engagement is necessary', 'Gespräche sind notwendig',
    ARRAY['AMERICAS-USA','EUROPE-RUSSIA'],
    ARRAY['channel','re-establish','resume','constructive','working toward','deconflict','avoid','only route','pragmatic','breakthrough','progress','Kanal','Wiederaufnahme','konstruktiv','Fortschritt','Deeskalation'],
    true,
    ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Euronews','Corriere della Sera','La Repubblica','France 24 (EN)','France 24','Tagesschau','Frankfurter Allgemeine','Globe and Mail','ABC News','MSNBC','Fox News','Die Zeit','Der Spiegel','Süddeutsche Zeitung','Handelsblatt','The Economist','Sky News','El País','Der Standard','Die Presse','Kurier','EurActiv','Straits Times','Channel NewsAsia','Nikkei Asia'],
    1
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_normalisation_premature',
    'us_russia_bilateral_channel',
    'Normalising relations while the war continues legitimises the Kremlin and sidelines Europe',
    'Eine Normalisierung während des andauernden Krieges legitimiert den Kreml und stellt Europa ins Abseits',
    'Western mainstream, transatlantic-critical and Ukrainian coverage arguing that summitry and warm bilateral atmospherics — congratulation calls, G20 invitations, talk of joint investment projects — grant Moscow the status of an equal partner it has not earned, and that decisions about European security are being taken over Europe''s and Kyiv''s heads. Same publisher bloc as the engagement stance, so framing separates them. Vocabulary: legitimise, over their heads, sidelined, without Europe, premature, rehabilitation, fatal mistake.',
    'Westliche Leitmedien, transatlantisch-kritische und ukrainische Berichterstattung argumentieren, Gipfeltreffen und freundliche bilaterale Atmosphäre — Gratulationsanrufe, G20-Einladungen, Gerede über gemeinsame Investitionsprojekte — verliehen Moskau einen nicht verdienten Status als gleichwertiger Partner, und Entscheidungen über die europäische Sicherheit fielen über die Köpfe Europas und Kyjiws hinweg. Gleicher Publisher-Block wie die Engagement-Position, daher trennt das Framing. Vokabular: legitimieren, ins Abseits, verfrüht, Rehabilitierung.',
    -1, 'Normalisation is premature', 'Normalisierung ist verfrüht',
    ARRAY['AMERICAS-USA','EUROPE-RUSSIA','EUROPE-UKRAINE','NON-STATE-EU'],
    ARRAY['legitimis','legitimiz','over their heads','sidelined','without Europe','excluded','premature','rehabilitat','fatal mistake','rewards','patience wears thin','wears thin','no invitation','not invited','rejects Europe','doubt','concession','legitimieren','Abseits','verfrüht','ohne Europa','Zugeständnis'],
    true,
    ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Euronews','Corriere della Sera','La Repubblica','France 24 (EN)','France 24','Tagesschau','Frankfurter Allgemeine','Globe and Mail','ABC News','MSNBC','Fox News','Die Zeit','Der Spiegel','Süddeutsche Zeitung','Handelsblatt','The Economist','Sky News','El País','Der Standard','Die Presse','Kurier','EurActiv','Atlantic Council','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House','Kyiv Post','Kyiv Independent','Ukrinform'],
    2
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_washington_realism',
    'us_russia_bilateral_channel',
    'Washington is returning to realism and accepting a multipolar order',
    'Washington kehrt zum Realismus zurück und akzeptiert eine multipolare Ordnung',
    'Russian state coverage presenting the restored channel as overdue recognition that Russia cannot be isolated: the previous freeze is over, contacts are being rebuilt on a basis of equality, and Washington must respect Russian interests for cooperation to be mutually beneficial. Critical coverage is reserved for perceived US inconsistency — stalling, ultimatums, drifting from the mediator role. Vocabulary: multipolar, equality, respect our interests, not frozen, mutually beneficial, language of ultimatums.',
    'Russische staatliche Berichterstattung stellt den wiederhergestellten Kanal als überfällige Anerkennung dar, dass Russland nicht isoliert werden kann: Das frühere Einfrieren sei vorbei, Kontakte würden auf Grundlage der Gleichberechtigung wiederaufgebaut, und Washington müsse russische Interessen respektieren, damit die Zusammenarbeit beiderseits nützlich sei. Kritik richtet sich gegen wahrgenommene US-Inkonsequenz — Hinhalten, Ultimaten. Vokabular: multipolar, Gleichberechtigung, Respekt, gegenseitiger Nutzen.',
    2, 'Washington is becoming realistic', 'Washington wird realistisch',
    ARRAY['EUROPE-RUSSIA','AMERICAS-USA'],
    ARRAY['multipolar','equality','respect','interests','not frozen','mutually beneficial','ultimatums','stalling','objective','sovereign','многополярн','равноправ','уважать','взаимовыгодн','ультиматум'],
    false,
    ARRAY['TASS (EN)','TASS','tass.ru','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Kommersant','Izvestia','Sputnik','BelTA Russian','Rossiyskaya Gazeta','Interfax'],
    3
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

-- ===========================================================================
-- C. us_russia_arms_control -- axis: who is responsible for the collapse?
-- ===========================================================================

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_new_treaty_needed',
    'us_russia_arms_control',
    'The expiry of New START is dangerous and a successor framework must be built',
    'Das Auslaufen von New START ist gefährlich, ein Nachfolgerahmen muss geschaffen werden',
    'Western mainstream and arms-control coverage treating the February 2026 lapse of the last US-Russia warhead limits as a genuine loss — the end of inspections and data exchange, the removal of predictability — and reporting proposals for a replacement pact as a necessary corrective rather than a concession. Vocabulary: expires, grave moment, unconstrained, predictability, verification, new pact, guardrails.',
    'Westliche Leitmedien und Rüstungskontroll-Berichterstattung behandeln das Auslaufen der letzten US-russischen Sprengkopfobergrenzen im Februar 2026 als echten Verlust — das Ende von Inspektionen und Datenaustausch, den Wegfall von Berechenbarkeit — und berichten über Vorschläge für einen Nachfolgevertrag als notwendige Korrektur, nicht als Zugeständnis. Vokabular: läuft aus, Verifikation, Berechenbarkeit, Leitplanken.',
    1, 'A successor treaty is needed', 'Ein Nachfolgevertrag ist nötig',
    ARRAY['AMERICAS-USA','EUROPE-RUSSIA'],
    ARRAY['expires','expiry','grave moment','unconstrained','predictability','verification','new pact','guardrails','calls for','decades of','last remaining','fears of','warns','läuft aus','Verifikation','Berechenbarkeit','warnt'],
    true,
    ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Euronews','Corriere della Sera','La Repubblica','France 24 (EN)','France 24','Tagesschau','Frankfurter Allgemeine','Globe and Mail','ABC News','MSNBC','Die Zeit','Der Spiegel','Süddeutsche Zeitung','Handelsblatt','The Economist','Sky News','El País','Der Standard','Die Presse','Defense News','Atlantic Council','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
    1
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_treaty_constrains_only_us',
    'us_russia_arms_control',
    'A new treaty would bind Washington while Moscow modernises unchecked',
    'Ein neuer Vertrag würde Washington binden, während Moskau ungehindert modernisiert',
    'Western hawkish, defence-policy and Ukrainian coverage arguing that arms control has become one-sided: Russia has fielded novel systems outside any treaty''s scope, verification had already collapsed in practice, and a successor pact negotiated from weakness would constrain US modernisation and missile defence while legitimising Moscow. Same publisher bloc as the successor-treaty stance, so framing separates them. Vocabulary: cheating, outside the treaty, one-sided, from weakness, no verification, unenforceable, modernising.',
    'Westliche sicherheitspolitisch-harte und ukrainische Berichterstattung argumentiert, Rüstungskontrolle sei einseitig geworden: Russland habe neuartige Systeme außerhalb jedes Vertragsrahmens aufgestellt, die Verifikation sei praktisch bereits zusammengebrochen, und ein aus einer Position der Schwäche ausgehandelter Nachfolgevertrag würde die US-Modernisierung und Raketenabwehr einschränken und Moskau legitimieren. Gleicher Publisher-Block, daher trennt das Framing. Vokabular: einseitig, aus Schwäche, keine Verifikation, Modernisierung.',
    -1, 'Arms control has become one-sided', 'Rüstungskontrolle ist einseitig geworden',
    ARRAY['AMERICAS-USA','EUROPE-RUSSIA','EUROPE-UKRAINE'],
    ARRAY['cheat','violat','outside the treaty','one-sided','from weakness','no verification','unenforceable','modernis','moderniz','buildup','build-up','rejects','no need','skeptic','sceptic','doubt','einseitig','Schwäche','Modernisierung','Zweifel'],
    true,
    ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Euronews','Corriere della Sera','La Repubblica','France 24 (EN)','France 24','Tagesschau','Frankfurter Allgemeine','Globe and Mail','ABC News','Fox News','Die Zeit','Der Spiegel','Süddeutsche Zeitung','Handelsblatt','The Economist','Sky News','Die Presse','Defense News','Atlantic Council','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House','Kyiv Post','Kyiv Independent','Ukrinform'],
    2
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_us_buildup_drives_race',
    'us_russia_arms_control',
    'US missile defence and rejected proposals are what drive the new arms race',
    'US-Raketenabwehr und zurückgewiesene Vorschläge treiben das neue Wettrüsten an',
    'Russian state coverage attributing the collapse of the strategic framework to Washington: post-New START proposals were rejected, the Golden Dome missile-defence programme undermines mutual vulnerability, and Moscow presents itself as willing to observe limits if the US does the same. Novel Russian systems are framed as responses to that programme rather than as its cause. Vocabulary: rejected our proposals, Golden Dome, destabilising, will not exceed if, ready for dialogue, blames US.',
    'Russische staatliche Berichterstattung schreibt den Zusammenbruch des strategischen Rahmens Washington zu: Vorschläge nach New START seien zurückgewiesen worden, das Raketenabwehrprogramm Golden Dome untergrabe die gegenseitige Verwundbarkeit, und Moskau stelle sich als bereit dar, Obergrenzen einzuhalten, wenn die USA dies auch täten. Neue russische Systeme gelten als Antwort auf dieses Programm. Vokabular: zurückgewiesen, destabilisierend, gesprächsbereit.',
    2, 'Washington drives the arms race', 'Washington treibt das Wettrüsten',
    ARRAY['EUROPE-RUSSIA','AMERICAS-USA'],
    ARRAY['rejected','Golden Dome','destabilis','destabiliz','will not exceed','ready for','dialogue','blames','provocation','undermines','takes note','условие','отверг','готов','дестабилиз'],
    false,
    ARRAY['TASS (EN)','TASS','tass.ru','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Kommersant','Izvestia','Sputnik','BelTA Russian','Rossiyskaya Gazeta','Interfax'],
    3
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

-- ===========================================================================
-- D. THEATER-LEVEL CARDS (§5.5) -- publisher-disjoint within each sign bucket
-- ===========================================================================

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_theater_engagement_case',
    'us_russia_theater',
    'Managed engagement is the responsible way to handle a nuclear-armed adversary',
    'Gesteuerter Dialog ist der verantwortungsvolle Umgang mit einem nuklear bewaffneten Gegner',
    'The cross-cutting Western argument that the reopened channel, the energy waivers and the search for a successor arms-control framework are all instances of the same pragmatism: pressure alone did not end the war, isolation forecloses the settlement, and a nuclear peer has to be managed rather than merely punished.',
    'Das übergreifende westliche Argument, dass der wiedereröffnete Gesprächskanal, die Energie-Ausnahmen und die Suche nach einem Nachfolgerahmen für die Rüstungskontrolle Ausdruck derselben Pragmatik sind: Druck allein hat den Krieg nicht beendet, Isolation verbaut die Regelung, und ein nuklearer Ebenbürtiger muss gesteuert und nicht nur bestraft werden.',
    1, 'Managed engagement', 'Gesteuerter Dialog',
    ARRAY['AMERICAS-USA','EUROPE-RUSSIA'],
    ARRAY['channel','pragmatic','market stability','re-establish','new pact','predictability','settlement','Kanal','pragmatisch','Berechenbarkeit'],
    false,
    ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Euronews','Corriere della Sera','La Repubblica','France 24 (EN)','France 24','Tagesschau','Frankfurter Allgemeine','Globe and Mail','ABC News','MSNBC','Fox News','Die Zeit','Der Spiegel','Süddeutsche Zeitung','Handelsblatt','The Economist','Sky News','El País','Der Standard','Die Presse','Kurier','EurActiv','OilPrice','S&P Global','Straits Times','Channel NewsAsia','Nikkei Asia','Defense News','Atlantic Council','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
    1
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_theater_kremlin_vindication',
    'us_russia_theater',
    'The West''s containment strategy has failed and Russia is being dealt with as an equal',
    'Die Eindämmungsstrategie des Westens ist gescheitert, Russland wird als gleichwertig behandelt',
    'The cross-cutting Russian state framing that each strand of the relationship confirms the same conclusion: sanctions could not be sustained, isolation collapsed, and Washington is negotiating on a basis of equality it long denied. Responsibility for remaining friction — stalled talks, the lapsed treaty — is placed on US inconsistency.',
    'Der übergreifende russische Staatsrahmen, wonach jeder Strang der Beziehung dieselbe Schlussfolgerung bestätigt: Sanktionen waren nicht durchzuhalten, die Isolation brach zusammen, und Washington verhandelt auf einer Grundlage der Gleichberechtigung, die es lange verweigert hat. Die Verantwortung für verbleibende Reibung wird der US-Inkonsequenz zugeschrieben.',
    2, 'Containment has failed', 'Eindämmung ist gescheitert',
    ARRAY['EUROPE-RUSSIA','AMERICAS-USA'],
    ARRAY['equality','multipolar','failed','respect','interests','de-facto admitted','rejected','многополярн','равноправ','провал'],
    false,
    ARRAY['TASS (EN)','TASS','tass.ru','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Kommersant','Izvestia','Sputnik','BelTA Russian','Rossiyskaya Gazeta','Interfax'],
    2
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    'us_russia_theater_western_alarm',
    'us_russia_theater',
    'Accommodation is being granted without reciprocity, over the heads of Europe and Kyiv',
    'Entgegenkommen wird ohne Gegenleistung gewährt — über die Köpfe Europas und Kyjiws hinweg',
    'The cross-cutting Western-critical and Ukrainian argument that sanctions relief, summit atmospherics and a weakened arms-control position form one pattern of unreciprocated concession: Moscow gains revenue, status and strategic room while the war continues, and the allies who bear the security consequences are not at the table.',
    'Das übergreifende westlich-kritische und ukrainische Argument, dass Sanktionslockerung, Gipfelatmosphäre und eine geschwächte rüstungskontrollpolitische Position ein einziges Muster einseitiger Zugeständnisse bilden: Moskau gewinnt Einnahmen, Status und strategischen Spielraum, während der Krieg weitergeht — und die Verbündeten, die die Sicherheitsfolgen tragen, sitzen nicht mit am Tisch.',
    -1, 'Concessions without reciprocity', 'Zugeständnisse ohne Gegenleistung',
    ARRAY['AMERICAS-USA','EUROPE-RUSSIA','EUROPE-UKRAINE','NON-STATE-EU'],
    ARRAY['gift to Putin','windfall','sidelined','over their heads','without Europe','premature','one-sided','rewards','U-turn','legitimis','Geschenk','Abseits','einseitig','verfrüht'],
    false,
    ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Euronews','Corriere della Sera','La Repubblica','France 24 (EN)','France 24','Tagesschau','Frankfurter Allgemeine','Globe and Mail','ABC News','MSNBC','Fox News','Die Zeit','Der Spiegel','Süddeutsche Zeitung','Handelsblatt','The Economist','Sky News','El País','Der Standard','Die Presse','Kurier','EurActiv','Defense News','Atlantic Council','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House','Kyiv Post','Kyiv Independent','Ukrinform'],
    3
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

COMMIT;

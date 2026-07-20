-- Sahel theater: theater-level narrative cards (spec §5.5, 2026-07-20).
--
-- The theater page renders cards only if the THEATER fn has its own
-- narratives_v2 rows. It carries no bundle and never matches titles: each card
-- is sourced from the member atomics' title_narratives where
-- sign(atomic.stance) = sign(theater.stance) AND publisher in the card's list.
--
-- THE HARD RULE is publisher-disjointness WITHIN each sign bucket, because the
-- count is uncapped over (sign, publisher). Four cards, two per bucket:
--
--   +2 Russian + Chinese state    |  +1 Nigerian national press   -- disjoint
--   -2 Western mainstream         |  -1 Arab / Turkish            -- disjoint
--
-- FOUR CARDS, NOT THREE. The three-card Arctic/Ukraine pattern assumes every
-- atomic shares one axis. Here the acting camp differs by atomic and two blocs
-- carry genuinely distinct framings that would be lost if merged:
--   * Nigerian dailies (Punch, Vanguard) report the Lake Chad war as a national
--     security operation -- neither Russia's partnership frame nor the Western
--     state-failure frame. Merging them into the +2 Russia card would label
--     Nigerian army reporting as pro-Kremlin, which is false.
--   * The Arab/Turkish desks (Al Jazeera, Al Arabiya, Anadolu, TRT) carry the
--     civilian-cost and displacement angle that the Western card, dominated by
--     the state-collapse frame, does not represent.
-- korea_theater and south_asia_theater already established that a theater may
-- need more than three cards.
--
-- NO RIFT-EXPLOITATION CARD. See the atomic narratives migration: Russia is a
-- principal in this theater, not a bystander to an intra-Western split.
--
-- framing_required is irrelevant at theater level and left false. No bootstrap
-- run is needed -- the roll-up is computed live at query time.

BEGIN;

INSERT INTO narratives_v2 (id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, publishers, framing_keywords,
    framing_required, actor_centroids, display_order, is_active) VALUES

('sahel_theater_partnership_frame', 'sahel_theater',
 'A sovereign realignment that is finally fighting the real enemy',
 'Eine souveräne Neuausrichtung, die endlich den wahren Feind bekämpft',
 'The Sahel states threw out the powers that failed them, chose partners who impose no political conditions, and are now waging the counterterror campaign the West never delivered -- the criticism from Paris and Washington reflects lost influence, not concern for Sahelians.',
 'Die Sahelstaaten haben die Mächte hinausgeworfen, die an ihnen scheiterten, Partner ohne politische Auflagen gewählt und führen nun jenen Anti-Terror-Feldzug, den der Westen nie lieferte -- die Kritik aus Paris und Washington spiegelt verlorenen Einfluss, nicht Sorge um die Menschen der Sahelzone.',
 2, 'Sovereign realignment', 'Souveräne Neuausrichtung',
 ARRAY['RT','rt.com','TASS','TASS (EN)','tass.com','tass.ru','RIA Novosti','ria.ru','Kommersant','kommersant.ru','BelTA','BelTA – News','BelTA Russian','CGTN','news.cgtn.com','newsaf.cgtn.com','newsus.cgtn.com','Global Times','China Daily','China Daily - Global Edition','People''s Daily','People''s Daily Online','Xinhua','Xinhuanet Deutsch','German.people.cn'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL','EUROPE-RUSSIA'], 1, true),

('sahel_theater_regional_security_response', 'sahel_theater',
 'A regional security emergency being fought by national armies',
 'Ein regionaler Sicherheitsnotstand, den nationale Armeen bekämpfen',
 'Seen from Abuja and the Lake Chad states, this is not a great-power contest but a war of national survival against groups that raid schools, blockade towns and cross borders at will -- and the story is the army''s operations, casualties and capability gaps.',
 'Aus Sicht Abujas und der Tschadseestaaten ist dies kein Großmächtewettstreit, sondern ein Krieg ums nationale Überleben gegen Gruppen, die Schulen überfallen, Städte blockieren und nach Belieben Grenzen überschreiten -- und die Geschichte handelt von Operationen, Verlusten und Fähigkeitslücken der Armee.',
 1, 'Regional security emergency', 'Regionaler Sicherheitsnotstand',
 ARRAY['Punch','Punch Newspapers','Vanguard','Vanguard News','Premium Times Nigeria','The Nation Newspaper'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-NIGERIA','AFRICA-SAHEL'], 2, true),

('sahel_theater_state_collapse_critique', 'sahel_theater',
 'A managed collapse: military rule that delivers neither security nor politics',
 'Ein verwalteter Zusammenbruch: Militärherrschaft ohne Sicherheit und ohne Politik',
 'Four years after the coups the juntas have banned the parties, expelled the monitors and severed the partnerships -- while jihadist coalitions blockade capitals, the north slips away and the replacement patrons retreat. Sovereignty has been asserted; the state has not been rebuilt.',
 'Vier Jahre nach den Putschen haben die Juntas die Parteien verboten, die Beobachter ausgewiesen und die Partnerschaften gekappt -- während dschihadistische Koalitionen Hauptstädte blockieren, der Norden entgleitet und die neuen Schutzmächte zurückweichen. Souveränität wurde behauptet; der Staat wurde nicht wiederaufgebaut.',
 -2, 'Managed collapse', 'Verwalteter Zusammenbruch',
 ARRAY['France 24','France 24 (EN)','Le Monde','Le Figaro','Reuters','Associated Press','BBC World','Deutsche Welle','Die Zeit','Der Spiegel','Der Standard','Tagesschau','Süddeutsche Zeitung','Frankfurter Allgemeine','The Guardian','Washington Post','New York Times','The Telegraph','Sky News','Euronews','El País','El Mundo','La Repubblica','Corriere della Sera','Straits Times','Bangkok Post','WION','NDTV','The Hindu','Times of India','Janes','Kyiv Post','Novinite','News24','Daily Nation','The Standard','Republic TV','The National','Council on Foreign Relations','War on the Rocks','Military Times','Defense News','Financial Times','Bloomberg','iROZHLAS'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL','EUROPE-FRANCE'], 3, true),

('sahel_theater_civilian_cost', 'sahel_theater',
 'The population pays for every side''s campaign',
 'Die Bevölkerung zahlt für den Feldzug jeder Seite',
 'Between jihadist massacres, army airstrikes on markets and the abuses of foreign auxiliaries, civilians in the Sahel and the Lake Chad basin are being killed and displaced by all the armed actors claiming to protect them -- and no external patron has made that safer.',
 'Zwischen dschihadistischen Massakern, Luftangriffen der Armee auf Märkte und den Übergriffen ausländischer Hilfstruppen werden Zivilisten in der Sahelzone und im Tschadseebecken von allen bewaffneten Akteuren getötet und vertrieben, die vorgeben, sie zu schützen -- und keine äußere Schutzmacht hat daran etwas verbessert.',
 -1, 'Civilian cost', 'Ziviler Preis',
 ARRAY['Al Jazeera','Al-Ahram','Ahram Online','Al Arabiya','Al Arabiya English','Anadolu Agency','Anadolu Ajansı','TRT World','Daily Sabah','Gulf News','Gulf Times','Arab News','UN News','news.un.org'],
 ARRAY[]::text[], false,
 ARRAY['AFRICA-SAHEL','AFRICA-NIGERIA'], 4, true)

ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id, name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
    stance = EXCLUDED.stance, stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de, publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    display_order = EXCLUDED.display_order, is_active = true, updated_at = NOW();

COMMIT;

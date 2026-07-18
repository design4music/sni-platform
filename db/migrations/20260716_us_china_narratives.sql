-- us_china_theater: atomic + theater narratives (greenfield, Phase 2 step 6/7)
--
-- Stance axis (consistent with arctic_theater so the theater roll-up buckets
-- cleanly): sign(+) = aligned with the Western competition consensus,
-- sign(-) = counter to it. This is what makes THEATER_ROLLUP_SQL work --
-- it matches sign(atomic.stance) = sign(theater.stance) AND publisher.
--
-- Publisher-disjointness:
--   * Within an atomic, narratives sharing the Western bloc (summit +1/-1,
--     trade +1/-1) are BOTH framing_required=true with disjoint keywords --
--     the own-goal case: Western outlets voice both stances, so publisher
--     alone cannot disambiguate.
--   * Theater cards: -2 (Chinese+Russian state) and -1 (Western) share the
--     negative sign but are publisher-disjoint, so uncapped counts partition.
--     +2 and -1 share Western publishers but have opposite signs => no
--     double-count.
--
-- Framing-keyword care (eu_cohesion 2026-07-15 lesson): keywords are ILIKE
-- SUBSTRING matches, so a negation-prefixed phrase contains its own positive.
-- 'deal' as a +1 keyword would fire on 'no deals confirmed'; 'breakthrough'
-- would fire on 'no major breakthroughs'. Both are therefore ABSENT from the
-- positive lists -- only unambiguous positives ('successful', 'stabilis',
-- 'landmark') appear there.
--
-- Per user direction (2026-07-16): the AI/tech contest is framed as hard
-- COMPETITION, not as a norms/principle question. IP and espionage disputes
-- are modelled as rivals accusing each other of playing dirty, not as a moral
-- axis.

BEGIN;

-- ============================ ATOMIC: summit diplomacy ============================

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
  name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, framing_required, is_active)
VALUES
('us_china_summit_engagement_works', 'us_china_summit_diplomacy', 1, 1,
 'Engagement is stabilising the rivalry', 'Dialog stabilisiert die Rivalität',
 'Leader-level engagement is putting a floor under a dangerous rivalry',
 'Gespräche auf höchster Ebene ziehen eine Untergrenze in eine gefährliche Rivalität ein',
 'Western and allied coverage treating the Beijing summit and the follow-on invitation as a working stabilisation of the relationship: tariff reductions, restored farm and aircraft purchases, an agreed AI dialogue and guardrails, and a resumption of leader-level contact after years of drift. The claim is not that rivalry has ended but that it is being managed. Vocabulary: successful, stability, guardrails, consensus, landmark, momentum, reset, thaw, lower tariffs.',
 'Westliche und verbündete Berichterstattung deutet den Pekinger Gipfel und die anschließende Einladung als tatsächliche Stabilisierung der Beziehung: Zollsenkungen, wieder aufgenommene Agrar- und Flugzeugkäufe, ein vereinbarter KI-Dialog samt Leitplanken sowie die Rückkehr zu Kontakten auf Führungsebene. Behauptet wird nicht das Ende der Rivalität, sondern deren Steuerbarkeit. Vokabular: erfolgreich, Stabilität, Leitplanken, Konsens, historisch, Dynamik, Neustart, Zollsenkung.',
 ARRAY['AMERICAS-USA','ASIA-CHINA'],
 ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Handelsblatt','Frankfurter Allgemeine','Euronews','El País','Die Zeit','Der Spiegel','Sky News','The Economist','Süddeutsche Zeitung','Tagesschau','ABC News','France 24 (EN)','France 24','Die Presse','Der Standard','El Mundo','Corriere della Sera','Kurier','Globe and Mail','EurActiv','Fox News','MSNBC','Nikkei Asia','Straits Times','Channel NewsAsia','Japan Times','NHK World','Asahi Shimbun','KBS World','Yonhap','Kyodo News','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
 ARRAY['successful','stabilis','stabiliz','stability','guardrail','consensus','landmark','historic','momentum','reset','thaw','pragmatic','win-win','mutual respect','fruitful','lower tariffs','tariff cuts','cut tariffs','opens','opening','renews','agreed to','cooperation','erfolgreich','Stabilität','Leitplanken','Konsens','Dynamik','Zollsenkung','Zusammenarbeit'],
 true, true),

('us_china_summit_weak_hand', 'us_china_summit_diplomacy', 2, -1,
 'Washington negotiated from weakness', 'Washington verhandelte aus der Schwäche',
 'Washington left the summit with little to show for it',
 'Washington verließ den Gipfel mit wenig Vorzeigbarem',
 'Western and allied coverage — including US domestic critics across the political spectrum — reading the same summit as a poor return: no confirmed deals, commitments described by Beijing as preliminary, no movement on Iran or Taiwan, and a US president who conceded a state visit for atmospherics. This is the friendly-critic stance: the outlets voicing it are the same ones that report the engagement case, so publisher cannot separate them. Vocabulary: stalemate, few wins, no deals, preliminary, exposes, upper hand, empty-handed.',
 'Westliche und verbündete Berichterstattung — darunter US-Kritiker aus dem gesamten politischen Spektrum — liest denselben Gipfel als schwache Ausbeute: keine bestätigten Abschlüsse, von Peking als vorläufig bezeichnete Zusagen, kein Fortschritt bei Iran oder Taiwan, und ein US-Präsident, der einen Staatsbesuch für Atmosphärisches eintauschte. Dies ist die Stimme des wohlwollenden Kritikers: dieselben Medien vertreten auch die Dialog-Position, weshalb der Publisher allein nicht trennt. Vokabular: Patt, kaum Erfolge, keine Abschlüsse, vorläufig, Oberhand.',
 ARRAY['AMERICAS-USA','ASIA-CHINA'],
 ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Handelsblatt','Frankfurter Allgemeine','Euronews','El País','Die Zeit','Der Spiegel','Sky News','The Economist','Süddeutsche Zeitung','Tagesschau','ABC News','France 24 (EN)','France 24','Die Presse','Der Standard','El Mundo','Corriere della Sera','Kurier','Globe and Mail','EurActiv','Fox News','MSNBC','Nikkei Asia','Straits Times','Channel NewsAsia','Japan Times','NHK World','Asahi Shimbun','KBS World','Yonhap','Kyodo News','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
 ARRAY['stalemate','few wins','empty-handed','no deals','no commitment','no sign','without a deal','little to show','preliminary','exposes','upper hand','capitulat','concession','gave away','flat-out disaster','embarrassment','failed to','whipsaw','stumble','limits on','no major','Patt','kaum Erfolge','keine Abschlüsse','vorläufig','Oberhand','Zugeständnis','bedürftiger'],
 true, true),

('us_china_summit_new_chapter', 'us_china_summit_diplomacy', 3, -2,
 'Chinese state framing: a new chapter', 'Chinesische Staatsmedien: ein neues Kapitel',
 'Leader diplomacy opens a new chapter proving cooperation beats containment',
 'Gipfeldiplomatie eröffnet ein neues Kapitel und beweist: Kooperation schlägt Eindämmung',
 'Chinese state media framing of the summit as vindication of its preferred model for the relationship: major-power relations conducted on mutual respect and equality, "win-win" economic ties, and a rejection of rivalry as the organising frame. It is a counter to the Western competition consensus rather than a report on deliverables — the argument is that containment, export controls and tariffs are the anomaly and cooperation the norm. Vocabulary: new chapter, pragmatic cooperation, mutual respect, win-win, major-power relations, historic.',
 'Chinesische Staatsmedien deuten den Gipfel als Bestätigung ihres bevorzugten Beziehungsmodells: Großmächtebeziehungen auf Grundlage gegenseitigen Respekts und Gleichrangigkeit, „Win-win"-Wirtschaftsbeziehungen und die Ablehnung von Rivalität als Ordnungsrahmen. Es ist eine Gegenposition zum westlichen Wettbewerbskonsens, keine Ergebnisbilanz: Eindämmung, Exportkontrollen und Zölle gelten als Anomalie, Kooperation als Normalfall. Vokabular: neues Kapitel, pragmatische Kooperation, gegenseitiger Respekt, Win-win.',
 ARRAY['ASIA-CHINA','AMERICAS-USA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua'],
 ARRAY['new chapter','pragmatic cooperation','mutual respect','win-win','major-power','landmark','historic','stability','consensus','mutually beneficial','sincere','neues Kapitel','gegenseitiger Respekt'],
 false, true),

('us_china_summit_multipolar_framing', 'us_china_summit_diplomacy', 4, -2,
 'Russian state framing: a multipolar turn', 'Russische Staatsmedien: multipolare Wende',
 'The summit showed a United States bargaining from a weakening position in a multipolar world',
 'Der Gipfel zeigte die USA als Verhandlungspartner aus schwächer werdender Position in einer multipolaren Welt',
 'Russian state coverage treats US-China leader diplomacy as evidence of relative American decline and of a world no longer ordered by Washington: attention to what China withholds, to Moscow-Beijing alignment reaffirmed immediately after the summit, and to the limits of US leverage. This is third-party framing — neither an endorsement of the US position nor of China''s cooperation message — and is modelled on its own axis rather than on the summit''s success/failure axis. Vocabulary: multipolar, decline, beneficiaries, leverage, unyielding ties.',
 'Russische Staatsmedien deuten die Gipfeldiplomatie als Beleg relativen amerikanischen Machtverlusts und einer nicht mehr von Washington geordneten Welt: Aufmerksamkeit dafür, was China zurückhält, für das unmittelbar nach dem Gipfel bekräftigte Bündnis Moskau-Peking und für die Grenzen amerikanischer Druckmittel. Es ist eine Drittperspektive — weder Zustimmung zur US-Position noch zur chinesischen Kooperationsbotschaft — und wird auf einer eigenen Achse modelliert. Vokabular: multipolar, Niedergang, Nutznießer, Druckmittel.',
 ARRAY['EUROPE-RUSSIA','AMERICAS-USA','ASIA-CHINA'],
 ARRAY['TASS','TASS (EN)','tass.com','RT','Sputnik','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','Press TV'],
 ARRAY['multipolar','decline','beneficiar','leverage','unyielding','strong ties','no longer','hegemon','мнополяр','многополяр','упадок','гегемон'],
 false, true);

-- ============================ ATOMIC: trade and tariffs ============================

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
  name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, framing_required, is_active)
VALUES
('us_china_tariff_leverage', 'us_china_trade_tariffs', 1, 1,
 'Tariffs are working leverage', 'Zölle als wirksames Druckmittel',
 'Tariffs and trade probes are legitimate leverage against an unbalanced relationship',
 'Zölle und Handelsuntersuchungen sind legitime Druckmittel gegen eine unausgewogene Beziehung',
 'Western and allied coverage arguing that tariff pressure and Section 301 probes are the instrument that produced results — reciprocal tariff reductions, renewed US beef and soybean access, an aircraft order — and that they answer a durable trade deficit, subsidised overcapacity and restricted market access. Vocabulary: leverage, reciprocal, market access, overcapacity, deficit, level playing field.',
 'Westliche und verbündete Berichterstattung argumentiert, Zolldruck und Section-301-Verfahren seien das Instrument, das Ergebnisse brachte — wechselseitige Zollsenkungen, wieder geöffneter Zugang für US-Rindfleisch und Sojabohnen, eine Flugzeugbestellung — und eine Antwort auf dauerhaftes Handelsdefizit, subventionierte Überkapazitäten und beschränkten Marktzugang. Vokabular: Druckmittel, Gegenseitigkeit, Marktzugang, Überkapazität, Defizit.',
 ARRAY['AMERICAS-USA','ASIA-CHINA'],
 ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Handelsblatt','Frankfurter Allgemeine','Euronews','El País','Die Zeit','Der Spiegel','Sky News','The Economist','Süddeutsche Zeitung','Tagesschau','ABC News','France 24 (EN)','France 24','Die Presse','Der Standard','El Mundo','Corriere della Sera','Kurier','Globe and Mail','EurActiv','Fox News','MSNBC','S&P Global','Nikkei Asia','Straits Times','Channel NewsAsia','Japan Times','NHK World','Asahi Shimbun','KBS World','Yonhap','Kyodo News','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
 ARRAY['leverage','reciprocal','market access','overcapacity','deficit','level playing field','unfair','subsid','dumping','opens','renews','concession from','pressure works','Druckmittel','Gegenseitigkeit','Marktzugang','Überkapazität','Defizit','unfair'],
 true, true),

('us_china_tariff_self_harm', 'us_china_trade_tariffs', 2, -1,
 'Tariffs backfire on the US', 'Zölle schaden den USA selbst',
 'Tariff escalation costs US industry and consumers more than it wins',
 'Zolleskalation kostet US-Industrie und Verbraucher mehr, als sie einbringt',
 'Western business and mainstream coverage — and US industry itself — arguing that the tariff campaign imposes costs at home, injects legal and planning uncertainty after the Supreme Court ruling, and strengthens Beijing''s hand: automakers pressing to keep or lift restrictions on their own terms, farm exporters exposed to retaliation, and allies hedging toward China. Same publisher bloc as the leverage stance, so framing separates them. Vocabulary: chaos, uncertainty, backfire, costs, retaliation, gives Beijing.',
 'Westliche Wirtschafts- und Leitmedien — und die US-Industrie selbst — argumentieren, die Zollkampagne verursache Kosten im Inland, erzeuge nach dem Urteil des Supreme Court rechtliche und planerische Unsicherheit und stärke Peking: Autohersteller, die Beschränkungen nach eigenen Vorstellungen erhalten oder aufheben wollen, Agrarexporteure im Vergeltungsrisiko, Verbündete, die sich Richtung China absichern. Gleicher Publisher-Block wie die Druckmittel-Position, daher trennt das Framing. Vokabular: Chaos, Unsicherheit, Bumerang, Kosten, Vergeltung.',
 ARRAY['AMERICAS-USA','ASIA-CHINA'],
 ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Handelsblatt','Frankfurter Allgemeine','Euronews','El País','Die Zeit','Der Spiegel','Sky News','The Economist','Süddeutsche Zeitung','Tagesschau','ABC News','France 24 (EN)','France 24','Die Presse','Der Standard','El Mundo','Corriere della Sera','Kurier','Globe and Mail','EurActiv','Fox News','MSNBC','S&P Global','Nikkei Asia','Straits Times','Channel NewsAsia','Japan Times','NHK World','Asahi Shimbun','KBS World','Yonhap','Kyodo News','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
 ARRAY['chaos','uncertainty','backfire','plead','press Trump','warn','costs','higher prices','retaliat','countermeasure','gives Beijing','Beijing a win','turmoil','slump','reversal','hit from','profit hit','blow past','Chaos','Unsicherheit','Vergeltung','warnen'],
 true, true),

('us_china_trade_unilateralism', 'us_china_trade_tariffs', 3, -2,
 'Chinese state framing: unilateral coercion', 'Chinesische Staatsmedien: unilateraler Zwang',
 'US tariffs are unilateral coercion that damages the global trading order',
 'US-Zölle sind unilateraler Zwang, der die globale Handelsordnung beschädigt',
 'Chinese state media framing of tariffs and Section 301 probes as unilateralism and abuse of process rather than as a response to any imbalance: measures taken outside the multilateral system, harmful to all parties, and aimed at suppressing a competitor. Vocabulary: unilateral, abusing, tariff wars have no winners, bullying, global trade order, exclusive blocs.',
 'Chinesische Staatsmedien deuten Zölle und Section-301-Verfahren als Unilateralismus und Verfahrensmissbrauch statt als Reaktion auf ein Ungleichgewicht: Maßnahmen außerhalb des multilateralen Systems, schädlich für alle Seiten, gerichtet auf die Unterdrückung eines Wettbewerbers. Vokabular: unilateral, Missbrauch, Zollkriege kennen keine Gewinner, globale Handelsordnung.',
 ARRAY['ASIA-CHINA','AMERICAS-USA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua'],
 ARRAY['unilateral','abusing','abuse','no winners','bullying','global trade order','exclusive blocs','revoke','oppose','protectionis','smear','WTO','unilateralist'],
 false, true);

-- ============================ ATOMIC: export controls ============================

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
  name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, framing_required, is_active)
VALUES
('us_china_export_control_necessity', 'us_china_tech_restrictions', 1, 1,
 'Controls protect a security-critical lead', 'Kontrollen sichern einen sicherheitsrelevanten Vorsprung',
 'Restricting advanced chip access is necessary to hold a security-critical technology lead',
 'Die Beschränkung des Zugangs zu Spitzenchips ist nötig, um einen sicherheitsrelevanten Technologievorsprung zu halten',
 'Western, allied and specialist coverage treating export controls as the instrument protecting a lead with direct military relevance: entity-list additions, licensing conditions on Nvidia sales, enforcement against diversion and smuggling, and allied alignment on lithography. Vocabulary: national security, guardrails, entity list, diversion, enforcement, chokepoint, alignment.',
 'Westliche, verbündete und Fachmedien behandeln Exportkontrollen als Instrument zum Schutz eines militärisch unmittelbar relevanten Vorsprungs: Aufnahmen in die Entity List, Auflagen für Nvidia-Verkäufe, Verfolgung von Umgehung und Schmuggel sowie Abstimmung mit Verbündeten bei der Lithografie. Vokabular: nationale Sicherheit, Leitplanken, Entity List, Umgehung, Durchsetzung.',
 ARRAY['AMERICAS-USA','ASIA-CHINA'],
 ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Handelsblatt','Frankfurter Allgemeine','Euronews','El País','Die Zeit','Der Spiegel','Sky News','The Economist','Süddeutsche Zeitung','Tagesschau','ABC News','France 24 (EN)','France 24','Die Presse','Der Standard','El Mundo','Corriere della Sera','Kurier','Globe and Mail','EurActiv','Fox News','MSNBC','The Information','TechCrunch','The Verge','Ars Technica','Wired','S&P Global','Nikkei Asia','Straits Times','Channel NewsAsia','Japan Times','NHK World','Asahi Shimbun','KBS World','Yonhap','Kyodo News','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
 ARRAY['national security','security risk','guardrail','entity list','diversion','divert','smuggl','enforcement','violation','chokepoint','align','military','curb','restrict','ban','nationale Sicherheit','Leitplanken','Schmuggel'],
 false, true),

('us_china_tech_containment', 'us_china_tech_restrictions', 2, -2,
 'Chinese state framing: technological containment', 'Chinesische Staatsmedien: technologische Eindämmung',
 'Export controls are containment dressed as security, and they are failing',
 'Exportkontrollen sind als Sicherheit getarnte Eindämmung — und sie scheitern',
 'Chinese state media framing of export controls as suppression of a competitor''s legitimate development rather than as security policy: curbs on Chinese entities opposed as overreach, warnings that the measures disrupt global chip supply chains, and emphasis on domestic substitution proceeding regardless. Beijing''s own refusal of cleared H200 imports is presented as leverage rather than dependence. Vocabulary: suppression, containment, overstretch, disrupting, opposed, self-reliance.',
 'Chinesische Staatsmedien deuten Exportkontrollen als Unterdrückung der legitimen Entwicklung eines Wettbewerbers statt als Sicherheitspolitik: Beschränkungen chinesischer Unternehmen als Übergriff, Warnungen vor Störung globaler Chip-Lieferketten und Betonung der ungeachtet dessen fortschreitenden heimischen Substitution. Pekings eigene Ablehnung freigegebener H200-Importe erscheint als Druckmittel, nicht als Abhängigkeit. Vokabular: Unterdrückung, Eindämmung, Störung, Eigenständigkeit.',
 ARRAY['ASIA-CHINA','AMERICAS-USA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua'],
 ARRAY['suppress','containment','contain','overstretch','disrupt','opposed','oppose','self-reliance','indigenous','smear','politicis','politiciz','generalizing national security','hegemon','crackdown'],
 false, true);

-- ============================ ATOMIC: AI primacy ============================

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
  name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, framing_required, is_active)
VALUES
('us_china_ai_lead_contest', 'us_china_ai_primacy', 1, 1,
 'A close race the US must keep winning', 'Ein enges Rennen, das die USA halten müssen',
 'Chinese AI has closed the gap and the US lead is now contested on merit and by hard tactics',
 'Chinas KI hat aufgeholt — der US-Vorsprung wird nun sowohl fachlich als auch mit harten Mitteln bestritten',
 'Western, allied and specialist coverage of a genuinely close contest: Chinese models reaching the frontier at lower cost, Chinese firms competing for US users, and rivals on both sides using every available tactic — blacklisting, litigation, restricted access, and accusations of distillation and illicit model access. Treated as commercial and strategic competition rather than as a question of principle. Vocabulary: race, close the gap, frontier, compete, blacklist, distillation, illicit, lawsuit.',
 'Westliche, verbündete und Fachmedien beschreiben ein tatsächlich enges Rennen: chinesische Modelle erreichen die Spitze zu geringeren Kosten, chinesische Firmen werben um US-Nutzer, und beide Seiten nutzen jedes verfügbare Mittel — schwarze Listen, Klagen, Zugangssperren und Vorwürfe der Distillation und des unzulässigen Modellzugriffs. Behandelt als kommerzieller und strategischer Wettbewerb, nicht als Grundsatzfrage. Vokabular: Rennen, Aufholen, Spitze, Wettbewerb, schwarze Liste, Klage.',
 ARRAY['AMERICAS-USA','ASIA-CHINA'],
 ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Handelsblatt','Frankfurter Allgemeine','Euronews','El País','Die Zeit','Der Spiegel','Sky News','The Economist','Süddeutsche Zeitung','Tagesschau','ABC News','France 24 (EN)','France 24','Die Presse','Der Standard','El Mundo','Corriere della Sera','Kurier','Globe and Mail','EurActiv','Fox News','MSNBC','The Information','TechCrunch','The Verge','Ars Technica','Wired','Nikkei Asia','Straits Times','Channel NewsAsia','Japan Times','NHK World','Asahi Shimbun','KBS World','Yonhap','Kyodo News','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
 ARRAY['race','close the gap','closing the gap','frontier','compete','competition','rival','ahead','behind','lead','blacklist','distillation','illicit','lawsuit','sues','accuse','theft','stolen','military list','guardrail','dialogue','Rennen','aufholen','Wettbewerb','Klage'],
 false, true),

('us_china_ai_suppression', 'us_china_ai_primacy', 2, -2,
 'Chinese state framing: smears and blocked competition', 'Chinesische Staatsmedien: Verleumdung und blockierter Wettbewerb',
 'Chinese AI succeeds on merit and Washington answers with smears and blacklists',
 'Chinas KI überzeugt durch Leistung — Washington antwortet mit Verleumdung und schwarzen Listen',
 'Chinese state media framing of the AI contest as one Beijing is winning fairly and Washington is losing badly: achievements attributed to domestic research investment, US theft and distillation accusations rejected as smears, and defence blacklisting of Chinese technology firms presented as competition policy conducted by other means. Vocabulary: smear, achievements, oppose, groundless, blacklist, suppress, innovation.',
 'Chinesische Staatsmedien deuten das KI-Rennen als eines, das Peking fair gewinnt und Washington schlecht verliert: Erfolge werden heimischer Forschungsinvestition zugeschrieben, US-Vorwürfe von Diebstahl und Distillation als Verleumdung zurückgewiesen, und die Aufnahme chinesischer Technologiefirmen auf Verteidigungslisten gilt als Wettbewerbspolitik mit anderen Mitteln. Vokabular: Verleumdung, Errungenschaften, haltlos, schwarze Liste, Unterdrückung.',
 ARRAY['ASIA-CHINA','AMERICAS-USA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua'],
 ARRAY['smear','achievement','oppose','opposed','groundless','firmly','blacklist','suppress','innovation','development','slander','politicis','politiciz','unwarranted','fabricat'],
 false, true);

-- ============================ ATOMIC: critical minerals ============================

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
  name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, framing_required, is_active)
VALUES
('us_china_minerals_dependence_risk', 'us_china_critical_minerals', 1, 1,
 'Dependence is a strategic vulnerability', 'Abhängigkeit als strategische Verwundbarkeit',
 'US dependence on Chinese rare earths is a vulnerability that must be engineered away',
 'Die US-Abhängigkeit von chinesischen Seltenen Erden ist eine Verwundbarkeit, die technisch überwunden werden muss',
 'Western, allied and industry coverage treating Chinese dominance of rare-earth mining, refining and magnet production as a live strategic exposure — hence the stockpile programme, Pentagon offtake deals, allied minerals pacts with the EU and Japan, and support for non-Chinese producers. The rare-earth truce is read as temporary relief, not a settlement. Vocabulary: dominance, grip, dependence, vulnerability, stockpile, diversif, break, counter.',
 'Westliche, verbündete und Industriemedien behandeln Chinas Dominanz bei Förderung, Raffination und Magnetproduktion Seltener Erden als akute strategische Verwundbarkeit — daher das Reserveprogramm, Abnahmeverträge des Pentagon, Rohstoffpakte mit EU und Japan sowie Förderung nichtchinesischer Produzenten. Der Waffenstillstand bei Seltenen Erden gilt als Atempause, nicht als Lösung. Vokabular: Dominanz, Abhängigkeit, Verwundbarkeit, Reserve, Diversifizierung.',
 ARRAY['AMERICAS-USA','ASIA-CHINA'],
 ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Handelsblatt','Frankfurter Allgemeine','Euronews','El País','Die Zeit','Der Spiegel','Sky News','The Economist','Süddeutsche Zeitung','Tagesschau','ABC News','France 24 (EN)','France 24','Die Presse','Der Standard','El Mundo','Corriere della Sera','Kurier','Globe and Mail','EurActiv','Fox News','MSNBC','OilPrice','Mining.com','S&P Global','Nikkei Asia','Straits Times','Channel NewsAsia','Japan Times','NHK World','Asahi Shimbun','KBS World','Yonhap','Kyodo News','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
 ARRAY['dominance','dominan','grip','depend','vulnerab','stockpile','diversif','break','counter','secure','leapfrog','one crisis away','truce','curbs still bite','challenge','Dominanz','Abhängigkeit','Verwundbarkeit'],
 false, true),

('us_china_minerals_lawful_leverage', 'us_china_critical_minerals', 2, -2,
 'Chinese state framing: lawful management', 'Chinesische Staatsmedien: rechtmäßige Steuerung',
 'China''s minerals controls are lawful management and Western blocs undermine open trade',
 'Chinas Rohstoffkontrollen sind rechtmäßige Steuerung — westliche Blöcke untergraben den offenen Handel',
 'Chinese state media framing of export licensing for rare earths as normal, lawful regulation of dual-use materials rather than coercion, and of US- and EU-led minerals alliances as exclusive blocs that fragment global trade. China''s processing dominance is presented as earned industrial capability, not as a weapon. Vocabulary: lawful, regulation, dual-use, exclusive blocs, global trade order, oppose, decoupling.',
 'Chinesische Staatsmedien deuten Exportlizenzen für Seltene Erden als normale, rechtmäßige Regulierung von Dual-Use-Material statt als Zwang, und von den USA und der EU geführte Rohstoffallianzen als exklusive Blöcke, die den Welthandel fragmentieren. Chinas Dominanz in der Weiterverarbeitung gilt als erarbeitete industrielle Fähigkeit, nicht als Waffe. Vokabular: rechtmäßig, Regulierung, Dual-Use, exklusive Blöcke, Entkopplung.',
 ARRAY['ASIA-CHINA','AMERICAS-USA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua'],
 ARRAY['lawful','regulation','dual-use','exclusive blocs','global trade order','oppose','opposed','decoupling','fragment','undermine','normal','legitimate','smear'],
 false, true);

-- ============================ THEATER cards (roll-up) ============================
-- Publisher-DISJOINT within the negative sign bucket: -2 is Chinese+Russian
-- state, -1 is Western. +2 shares Western publishers with -1 but has the
-- opposite sign, so no title double-counts.

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
  name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, framing_required, is_active)
VALUES
('us_china_western_competition_consensus', 'us_china_theater', 1, 2,
 'Western competition consensus', 'Westlicher Wettbewerbskonsens',
 'Managed competition: hold the technology lead, reduce dependence, keep talking',
 'Gesteuerter Wettbewerb: Technologievorsprung halten, Abhängigkeiten senken, im Gespräch bleiben',
 'The dominant Western and allied framing across the dyad: the United States is in a long-run economic and technological contest with China that it intends to win, using export controls, tariffs, minerals diversification and allied alignment — while keeping leader-level channels open so the rivalry stays bounded. Competition is assumed; the argument is about instruments and pace.',
 'Der vorherrschende westliche und verbündete Deutungsrahmen des Verhältnisses: Die USA stehen in einem langfristigen wirtschaftlichen und technologischen Wettstreit mit China, den sie gewinnen wollen — mit Exportkontrollen, Zöllen, Rohstoffdiversifizierung und Abstimmung unter Verbündeten — und halten zugleich Kanäle auf Führungsebene offen, damit die Rivalität eingehegt bleibt. Wettbewerb gilt als gesetzt; gestritten wird über Instrumente und Tempo.',
 ARRAY['AMERICAS-USA','ASIA-CHINA'],
 ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Handelsblatt','Frankfurter Allgemeine','Euronews','El País','Die Zeit','Der Spiegel','Sky News','The Economist','Süddeutsche Zeitung','Tagesschau','ABC News','France 24 (EN)','France 24','Die Presse','Der Standard','El Mundo','Corriere della Sera','Kurier','Globe and Mail','EurActiv','Fox News','MSNBC','The Information','TechCrunch','The Verge','Ars Technica','Wired','OilPrice','Mining.com','S&P Global','Nikkei Asia','Straits Times','Channel NewsAsia','Japan Times','NHK World','Asahi Shimbun','KBS World','Yonhap','Kyodo News','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
 ARRAY['national security','leverage','race','lead','dominance','depend','entity list','guardrail','stability','align','compete','counter'],
 false, true),

('us_china_beijing_moscow_counter', 'us_china_theater', 2, -2,
 'Chinese & Russian state counter-framing', 'Chinesische & russische Gegenerzählung',
 'Containment is the anomaly: cooperation, lawful trade and a multipolar order',
 'Eindämmung ist die Anomalie: Kooperation, rechtmäßiger Handel und eine multipolare Ordnung',
 'The counter-framing carried by Chinese and Russian state media. Beijing''s line: tariffs, export controls and blacklists are unilateral coercion aimed at suppressing a competitor''s legitimate development, while cooperation and mutual respect are the natural basis of major-power relations. Moscow''s line runs on a different axis — it reads the same events as evidence of relative American decline in a multipolar world, without endorsing either side''s position.',
 'Die von chinesischen und russischen Staatsmedien getragene Gegenerzählung. Pekings Linie: Zölle, Exportkontrollen und schwarze Listen sind unilateraler Zwang zur Unterdrückung der legitimen Entwicklung eines Wettbewerbers, während Kooperation und gegenseitiger Respekt die natürliche Grundlage von Großmächtebeziehungen bilden. Moskaus Linie verläuft auf einer anderen Achse: Sie liest dieselben Ereignisse als Beleg relativen amerikanischen Machtverlusts in einer multipolaren Welt, ohne eine der beiden Positionen zu unterstützen.',
 ARRAY['ASIA-CHINA','EUROPE-RUSSIA','AMERICAS-USA'],
 ARRAY['Global Times','CGTN','China Daily','People''s Daily','Xinhua','TASS','TASS (EN)','tass.com','RT','Sputnik','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','Press TV'],
 ARRAY['unilateral','suppress','containment','smear','no winners','bullying','win-win','mutual respect','new chapter','multipolar','hegemon','oppose','lawful','global trade order'],
 false, true),

('us_china_western_engagement_critique', 'us_china_theater', 3, -1,
 'Western critique of US handling', 'Westliche Kritik am US-Vorgehen',
 'The instruments are backfiring: costs at home, allies hedging, leverage overstated',
 'Die Instrumente wirken gegen die USA: Kosten im Inland, absichernde Verbündete, überschätzte Druckmittel',
 'The self-critical strand within Western and allied coverage — the friendly critic rather than an opponent of competition. It argues the campaign is being executed badly: tariff chaos and legal uncertainty raise costs for US industry and farmers, summitry yields atmospherics rather than commitments, allies hedge toward Beijing rather than align, and China''s counter-leverage in rare earths and its refusal of cleared chip imports show the pressure runs both ways.',
 'Der selbstkritische Strang westlicher und verbündeter Berichterstattung — wohlwollende Kritik, keine Gegnerschaft zum Wettbewerb an sich. Das Vorgehen gilt als schlecht ausgeführt: Zollchaos und Rechtsunsicherheit verteuern Produktion für US-Industrie und Landwirte, Gipfel bringen Atmosphärisches statt Zusagen, Verbündete sichern sich Richtung Peking ab statt sich anzuschließen, und Chinas Gegendruck bei Seltenen Erden sowie die Ablehnung freigegebener Chip-Importe zeigen: Der Druck wirkt in beide Richtungen.',
 ARRAY['AMERICAS-USA','ASIA-CHINA'],
 ARRAY['Reuters','Bloomberg','Bloomberg.com','Financial Times','Wall Street Journal','New York Times','The New York Times','Washington Post','CNN','BBC World','The Guardian','Associated Press','NPR','Deutsche Welle','The Telegraph','Handelsblatt','Frankfurter Allgemeine','Euronews','El País','Die Zeit','Der Spiegel','Sky News','The Economist','Süddeutsche Zeitung','Tagesschau','ABC News','France 24 (EN)','France 24','Die Presse','Der Standard','El Mundo','Corriere della Sera','Kurier','Globe and Mail','EurActiv','Fox News','MSNBC','The Information','TechCrunch','The Verge','Ars Technica','Wired','OilPrice','Mining.com','S&P Global','Nikkei Asia','Straits Times','Channel NewsAsia','Japan Times','NHK World','Asahi Shimbun','KBS World','Yonhap','Kyodo News','Council on Foreign Relations','CSIS','Brookings','Carnegie Endowment','Chatham House'],
 ARRAY['chaos','uncertainty','backfire','stalemate','few wins','no deals','upper hand','gives Beijing','Beijing a win','warn','plead','costs','hedge','still bite','limits','exposes'],
 false, true);

COMMIT;

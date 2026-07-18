-- us_canada_theater atomic narratives (FN_THEATER_BUILD_SPEC §0a step 6, §5).
--
-- Publisher-bloc reality check (measured, 180d, over the 3 atomics' attributed titles):
--   * Western/Canadian mainstream is overwhelming: Globe and Mail 91, Reuters 25,
--     BBC 21, Bloomberg 19, CBC 18, AP 15, FT 14, WSJ 13, Guardian 12.
--   * The ONLY conservative outlet in the corpus is Fox News. National Post,
--     Toronto Sun, Western Standard, Rebel News, NY Post etc. are absent entirely.
--   * Russian/Chinese state ~25 titles: RT 11, Global Times 4, CGTN 3, TASS 3,
--     People's Daily 2, China Daily 2.
--
-- Two consequences that shape every narrative below:
--
-- 1. Fox News DOES push a real line here ("Canada is a small power biting the hand
--    that protects it", "Canada's prime minister refers to US economic ties as a
--    weakness", "Canada should be 'grateful' for Golden Dome"). So a US-sympathetic
--    narrative is justified -- but only ~4 of its 20 Canada titles carry it; the rest
--    is the LaGuardia crash, hockey, crime and healthcare. Every Fox-based narrative
--    is therefore framing_required=true. Publisher alone would make it a firehose
--    (the myanmar_civil_conflict failure mode).
--
-- 2. alberta_separatism_us_ties has NO sympathetic publisher bloc at all -- the
--    separatists' own outlets are not in the corpus, so all coverage comes from
--    Globe and Mail / CBC / WSJ / Bloomberg. This is the §5 own-goal shape: the
--    pro/con split CANNOT come from publisher alignment. Both the grievance and the
--    unity narratives take the SAME Western coalition with framing_required=true and
--    disjoint framing keywords.
--
-- Rift-exploitation (§5): US-Canada is an INTRA-WESTERN dispute, so RT/TASS/Global
-- Times/CGTN are not pro-Canada. Their stance is bloc-fracture and pretext-denial.
-- They get their own axis on every atomic, never the dispute's own pro/con axis.
SET client_encoding TO 'UTF8';

-- =========================================================================
-- us_canada_trade_coercion
-- =========================================================================
INSERT INTO narratives_v2 (
  id, fn_id, name_en, name_de, claim_en, claim_de,
  stance, stance_label_en, stance_label_de, display_order,
  publishers, framing_keywords, framing_required, actor_centroids, is_active
) VALUES
(
  'usca_trade_rebalancing',
  'us_canada_trade_coercion',
  'Rebalancing an unfair trading relationship',
  'Neuausrichtung einer unfairen Handelsbeziehung',
  'Tariffs are legitimate leverage to correct a trade relationship that has long favoured Canada: protected dairy under supply management, subsidised softwood exports, and a partner that has missed defence-spending benchmarks for decades while relying on guaranteed access to the American market.',
  'Zölle sind ein legitimes Druckmittel, um eine Handelsbeziehung zu korrigieren, die lange Kanada begünstigt hat: geschützte Milchwirtschaft durch Angebotssteuerung, subventionierte Nadelholzexporte und ein Partner, der seit Jahrzehnten die Verteidigungsziele verfehlt und sich zugleich auf den garantierten Zugang zum amerikanischen Markt verlässt.',
  2, 'US leverage is justified', 'US-Druck ist gerechtfertigt', 1,
  ARRAY['Fox News'],
  ARRAY['unfair','subsidiz','subsidis','protected market','supply management','freeload','grateful','biting the hand','not paying','burden','deficit','takes advantage','one-sided','unfair','Trittbrettfahrer','Subvention','einseitig','dankbar'],
  true,
  ARRAY['AMERICAS-USA'], true
),
(
  'usca_economic_coercion',
  'us_canada_trade_coercion',
  'Tariff coercion against a treaty partner',
  'Zollzwang gegen einen Vertragspartner',
  'Washington is applying tariffs, permit threats and aircraft decertification as coercion against a neighbour bound by an existing trade agreement it negotiated itself, imposing costs on producers and consumers on both sides of the border and eroding the reliability of American commitments.',
  'Washington setzt Zölle, Genehmigungsdrohungen und den Entzug von Luftfahrtzulassungen als Zwangsmittel gegen einen Nachbarn ein, der an ein selbst ausgehandeltes Handelsabkommen gebunden ist. Das belastet Produzenten und Verbraucher auf beiden Seiten der Grenze und untergräbt die Verlässlichkeit amerikanischer Zusagen.',
  -2, 'Coercion of an ally', 'Zwang gegen einen Verbündeten', 2,
  ARRAY['Globe and Mail','The Globe and Mail','CBC','Reuters','BBC World','Bloomberg','Associated Press','Financial Times','Wall Street Journal','The Guardian','New York Times','Washington Post','The Washington Post','CNN','NPR','Euronews','Deutsche Welle','Der Spiegel','El País','France 24 (EN)','France 24','Al Jazeera','NDTV','Anadolu Agency','Mining.com','OilPrice'],
  ARRAY['coercion','retaliat','threat','blackmail','ally','betray','escalat','hit back','damage','cost','job losses','Zwang','Erpressung','Verbündet','Vergeltung'],
  false,
  ARRAY['AMERICAS-CANADA'], true
),
(
  'usca_bloc_fracture',
  'us_canada_trade_coercion',
  'The Western bloc turning on itself',
  'Der westliche Block wendet sich gegen sich selbst',
  'The tariff confrontation is presented as evidence that the American-led order rests on coercion of its own partners rather than shared values, and that Washington treats allies as tributaries whenever its economic interests require it.',
  'Die Zollkonfrontation wird als Beleg dafür dargestellt, dass die amerikanisch geführte Ordnung auf Zwang gegenüber den eigenen Partnern beruht statt auf gemeinsamen Werten, und dass Washington Verbündete als Tributpflichtige behandelt, sobald es die eigenen Wirtschaftsinteressen verlangen.',
  -1, 'Western order exposed', 'Westliche Ordnung entlarvt', 3,
  ARRAY['RT','TASS (EN)','Global Times','CGTN','People''s Daily','China Daily','Xinhua','Sputnik'],
  ARRAY['hegemon','bully','vassal','double standard','hypocris','unilateral','dictate','so-called ally','Hegemon','Doppelmoral','Vasall'],
  false,
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'], true
);

-- =========================================================================
-- canada_sovereignty_pressure
-- =========================================================================
INSERT INTO narratives_v2 (
  id, fn_id, name_en, name_de, claim_en, claim_de,
  stance, stance_label_en, stance_label_de, display_order,
  publishers, framing_keywords, framing_required, actor_centroids, is_active
) VALUES
(
  'casp_continental_dependence',
  'canada_sovereignty_pressure',
  'Canada depends on American protection',
  'Kanada ist auf amerikanischen Schutz angewiesen',
  'Canada is a smaller power whose prosperity and security rest on American markets and American defence, and which is poorly placed to object when Washington sets the terms of the relationship or questions the border arrangements underpinning it.',
  'Kanada sei eine kleinere Macht, deren Wohlstand und Sicherheit auf amerikanischen Märkten und amerikanischer Verteidigung beruhen und die schlecht aufgestellt sei, um zu widersprechen, wenn Washington die Bedingungen der Beziehung setzt oder die zugrunde liegenden Grenzarrangements infrage stellt.',
  2, 'Dependence is the reality', 'Abhängigkeit ist die Realität', 1,
  ARRAY['Fox News'],
  ARRAY['grateful','small power','biting the hand','protects','depend','weakness','Golden Dome','freeload','benchmark','shield','umbrella','dankbar','abhängig','Schutzschirm'],
  true,
  ARRAY['AMERICAS-USA'], true
),
(
  'casp_sovereignty_defence',
  'canada_sovereignty_pressure',
  'Sovereignty under pressure',
  'Souveränität unter Druck',
  'Annexation and "51st state" rhetoric, the threat to withhold a jointly financed border crossing, and the withdrawn diplomatic invitation are treated as pressure on the sovereignty of an independent state, prompting a cross-party Canadian response and a public turn toward domestic purchasing and alternative trading partners.',
  'Annexionsrhetorik und Reden vom „51. Bundesstaat", die Drohung, einen gemeinsam finanzierten Grenzübergang zurückzuhalten, und die zurückgezogene diplomatische Einladung werden als Druck auf die Souveränität eines unabhängigen Staates verstanden — mit einer parteiübergreifenden kanadischen Reaktion und einer öffentlichen Hinwendung zu heimischen Käufen und alternativen Handelspartnern.',
  -2, 'Sovereignty must hold', 'Souveränität muss bestehen', 2,
  ARRAY['Globe and Mail','The Globe and Mail','CBC','Reuters','BBC World','Bloomberg','Associated Press','Financial Times','Wall Street Journal','The Guardian','New York Times','Washington Post','The Washington Post','CNN','NPR','Euronews','Deutsche Welle','Der Spiegel','El País','France 24 (EN)','France 24','Al Jazeera','NDTV','Anadolu Agency','Reforma','El Universal','Mexico News Daily'],
  ARRAY['sovereignt','independen','annex','51st state','reject','rebuff','stand up','unity','respect','Souveränität','Annexion','zurückweis'],
  false,
  ARRAY['AMERICAS-CANADA'], true
),
(
  'casp_imperial_overreach',
  'canada_sovereignty_pressure',
  'Imperial overreach in its own hemisphere',
  'Imperiale Überdehnung in der eigenen Hemisphäre',
  'Talk of absorbing a neighbouring state is presented as proof that American expansionism operates on its own continent as readily as abroad, and as grounds to dismiss Washington''s claim to defend a rules-based order or to invoke external threats as justification.',
  'Das Gerede von der Einverleibung eines Nachbarstaates wird als Beleg dafür präsentiert, dass amerikanischer Expansionismus auf dem eigenen Kontinent ebenso wirkt wie im Ausland — und als Grund, Washingtons Anspruch zurückzuweisen, eine regelbasierte Ordnung zu verteidigen oder äußere Bedrohungen als Rechtfertigung anzuführen.',
  -1, 'Expansionism exposed', 'Expansionismus entlarvt', 3,
  ARRAY['RT','TASS (EN)','Global Times','CGTN','People''s Daily','China Daily','Xinhua','Sputnik'],
  ARRAY['expansionis','imperial','annex','colonial','hypocris','double standard','so-called','rules-based','Expansionis','imperial','Doppelmoral'],
  false,
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'], true
);

-- =========================================================================
-- alberta_separatism_us_ties  (own-goal three-stance, §5)
-- The +1 and -1 narratives share the SAME Western coalition and are separated
-- ONLY by framing keywords -- there is no sympathetic publisher bloc in the corpus.
-- =========================================================================
INSERT INTO narratives_v2 (
  id, fn_id, name_en, name_de, claim_en, claim_de,
  stance, stance_label_en, stance_label_de, display_order,
  publishers, framing_keywords, framing_required, actor_centroids, is_active
) VALUES
(
  'alberta_legitimate_grievance',
  'alberta_separatism_us_ties',
  'A grievance the federation has not answered',
  'Ein Anliegen, auf das der Bund keine Antwort hat',
  'The separatist push reflects durable material grievances in a landlocked resource province: transfer payments that flow outward, federal environmental and pipeline decisions made without provincial consent, and a sense that the province''s economic weight buys it no say in Ottawa.',
  'Der separatistische Vorstoß spiegelt dauerhafte materielle Beschwerden einer rohstoffreichen Binnenprovinz: Transferzahlungen, die abfließen, föderale Umwelt- und Pipelineentscheidungen ohne Zustimmung der Provinz und das Gefühl, dass das wirtschaftliche Gewicht der Provinz ihr in Ottawa kein Mitspracherecht verschafft.',
  1, 'The grievance is real', 'Das Anliegen ist real', 1,
  ARRAY['Globe and Mail','The Globe and Mail','CBC','Reuters','BBC World','Bloomberg','Associated Press','Financial Times','Wall Street Journal','The Guardian','New York Times','Washington Post','The Washington Post','CNN','NPR','Euronews','Deutsche Welle','El País','France 24 (EN)','NDTV','Anadolu Agency','OilPrice','Mining.com'],
  ARRAY['Western alienation','equalization','equalisation','resource revenue','landlocked','grievance','frustration','neglect','ignored','left behind','oil-rich','Benachteiligung','Ausgleichszahlung','vernachlässigt'],
  true,
  ARRAY['AMERICAS-CANADA'], true
),
(
  'alberta_unity_defence',
  'alberta_separatism_us_ties',
  'A dangerous bluff, and an opening for outside pressure',
  'Ein gefährliches Bluffspiel und ein Einfallstor für Druck von außen',
  'The referendum push is treated as constitutionally doubtful and economically self-defeating, with courts, First Nations treaty holders and former prime ministers ranged against it. Contacts between separatist organisers and American officials raise a further objection: that a domestic constitutional question is being opened to an outside government with an interest in the outcome.',
  'Der Referendumsvorstoß gilt als verfassungsrechtlich zweifelhaft und wirtschaftlich selbstschädigend — Gerichte, Vertragspartner der First Nations und frühere Premierminister stellen sich dagegen. Kontakte zwischen separatistischen Organisatoren und amerikanischen Amtsträgern werfen einen weiteren Einwand auf: dass eine innerstaatliche Verfassungsfrage einer auswärtigen Regierung geöffnet wird, die ein Interesse am Ausgang hat.',
  -1, 'A threat to the federation', 'Eine Gefahr für den Bund', 2,
  ARRAY['Globe and Mail','The Globe and Mail','CBC','Reuters','BBC World','Bloomberg','Associated Press','Financial Times','Wall Street Journal','The Guardian','New York Times','Washington Post','The Washington Post','CNN','NPR','Euronews','Deutsche Welle','El País','France 24 (EN)','NDTV','Anadolu Agency','OilPrice','Mining.com'],
  ARRAY['treason','dangerous','bluff','Brexit','quash','injunction','unconstitutional','illegal','treaty rights','First Nations','warns','unity','respect Canadian sovereignty','interference','Landesverrat','Einheit','verfassungswidrig','Einmischung'],
  true,
  ARRAY['AMERICAS-CANADA'], true
),
(
  'alberta_external_amplification',
  'alberta_separatism_us_ties',
  'A fraying federation, watched from outside',
  'Ein brüchiger Bundesstaat, von außen beobachtet',
  'The secession debate is covered as a symptom of Western political decay, with the emphasis placed on the fracture itself and on the contrast between Canadian objections to outside interference and Canadian conduct elsewhere.',
  'Die Sezessionsdebatte wird als Symptom westlichen politischen Verfalls dargestellt, mit Betonung auf dem Bruch selbst und auf dem Kontrast zwischen kanadischen Einwänden gegen Einmischung von außen und kanadischem Verhalten andernorts.',
  -2, 'Symptom of Western decay', 'Symptom westlichen Verfalls', 3,
  ARRAY['RT','TASS (EN)','Global Times','CGTN','People''s Daily','China Daily','Xinhua','Sputnik'],
  ARRAY['decay','decline','crisis','hypocris','double standard','so-called','fracture','disintegrat','Verfall','Doppelmoral','Zerfall'],
  false,
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'], true
);

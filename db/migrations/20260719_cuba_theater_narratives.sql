-- Cuba theater: atomic + theater narratives (greenfield, 2026-07-19).
--
-- Follows the three-stance coercion pattern established by the sibling
-- venezuela theater (us_venezuela_relations / venezuela_sanctions_oil,
-- 2026-07-18) -- same hemisphere, same US-maximum-pressure shape, so the sign
-- convention must match or the theater roll-up (§5.5) mixes axes:
--
--   +1  the US action is justified / the fault lies with Havana   FR=true
--   -1  Western-critical: overreach, humanitarian alarm            FR=true
--   -2  anti-imperial bloc                                         FR=false
--
-- WHY framing_required=true ON BOTH WESTERN STANCES. This theater is a
-- CAUSATION DISPUTE, not a publisher-aligned pro/con: Reuters, CNN and El País
-- all publish both "the blockade caused the collapse" and "decades of
-- mismanagement caused the collapse". The publisher-coalition assumption
-- (spec §5) is therefore invalid on its own and the +1/-1 pair shares one
-- coalition, disambiguated by disjoint framing keywords. Only the -2 bloc is
-- publisher-disjoint and needs no framing gate.
--
-- NO RIFT-EXPLOITATION CARD (spec §5, contrast Arctic). That caveat is for
-- INTRA-WESTERN disputes where Russia/China are bystanders amplifying a split.
-- Here they are PRINCIPALS -- they ship the oil, Putin and Beijing issue
-- statements as parties -- exactly like China in the SCS build. Their coverage
-- belongs on the dispute's own pro/con axis, as -2.
--
-- STANCE-AMBIGUOUS KEYWORDS DELIBERATELY EXCLUDED (the eu_cohesion trap):
--   'defiance' / 'desafío' / 'Trotz' -- neutral Reuters register ("in defiance
--      of US sanctions"), appears in both camps. Cut from the lifelines +1.
--   'terrorist' / 'terrorista' / 'armed infiltration' -- this is HAVANA's
--      framing of the Florida speedboat group, not Washington's. Putting it on
--      the pro-pressure stance would have inverted those titles. Cut from the
--      military +1.
--   'tightening' / 'leverage' / 'Druck' -- descriptive, not evaluative.
--
-- No DELETE; INSERT ... ON CONFLICT. Reversible.

BEGIN;

-- ===========================================================================
-- A. cuba_embargo_sanctions -- US sanctions and blockade instruments
-- ===========================================================================
INSERT INTO narratives_v2 (id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, publishers, framing_keywords,
    framing_required, actor_centroids, display_order, is_active) VALUES
('cuba_pressure_justified', 'cuba_embargo_sanctions',
 'Economic pressure is legitimate leverage on an indicted regime',
 'Wirtschaftlicher Druck ist legitimes Druckmittel gegen ein angeklagtes Regime',
 'Sanctions, designations and the indictment of the leadership are lawful instruments against a one-party government implicated in trafficking and repression -- and Havana''s willingness to talk shows they work.',
 'Sanktionen, Listungen und die Anklage der Führung sind rechtmäßige Instrumente gegen eine Einparteienregierung, die in Schmuggel und Repression verstrickt ist -- und Havannas Gesprächsbereitschaft zeigt ihre Wirkung.',
 1, 'Legitimate leverage', 'Legitimes Druckmittel',
 ARRAY['Fox News','Jerusalem Post','Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','El País','El Mundo','Clarín','La Nación','Reforma','El Universal','Folha de S.Paulo','O Globo','O Estado de S. Paulo'],
 ARRAY['maximum pressure','brought to justice','drug trafficking','murder charges','narco','dictatorship','dictatorial','repressive regime','accountability','must go','Diktatur','gerechtfertigt','Rechenschaft','angeklagt','dictadura','narcotráfico','justicia','rendición de cuentas','régimen represivo'],
 true, ARRAY['AMERICAS-USA','AMERICAS-CUBA'], 1, true),

('cuba_sanctions_overreach', 'cuba_embargo_sanctions',
 'Extraterritorial sanctions are collective punishment',
 'Extraterritoriale Sanktionen sind Kollektivstrafe',
 'Secondary sanctions that force European shippers and hotel groups out and penalise third countries reach far beyond US jurisdiction, and the burden falls on ordinary Cubans rather than the government.',
 'Sekundärsanktionen, die europäische Reedereien und Hotelgruppen zum Rückzug zwingen und Drittstaaten bestrafen, reichen weit über die US-Jurisdiktion hinaus -- und die Last tragen gewöhnliche Kubaner, nicht die Regierung.',
 -1, 'Extraterritorial overreach', 'Extraterritoriale Übergriffigkeit',
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','UN News','El País','El Mundo','Clarín','La Nación','Reforma','El Universal','Folha de S.Paulo','O Globo','O Estado de S. Paulo','Mexico News Daily'],
 ARRAY['extraterritorial','overreach','collective punishment','secondary sanctions','third countries','unilateral','condemn','counterproductive','backfire','civilians pay','Kollektivstrafe','völkerrechtswidrig','einseitig','kontraproduktiv','verurteil','castigo colectivo','contraproducente','condena','terceros países'],
 true, ARRAY['NON-STATE-EU','AMERICAS-USA','AMERICAS-CUBA'], 2, true),

('cuba_economic_warfare', 'cuba_embargo_sanctions',
 'The blockade is economic warfare against a sovereign nation',
 'Die Blockade ist Wirtschaftskrieg gegen eine souveräne Nation',
 'Washington''s siege is an illegal act of economic aggression, condemned year after year by the UN General Assembly, designed to break a country that refuses to submit.',
 'Washingtons Belagerung ist ein illegaler Akt wirtschaftlicher Aggression, Jahr für Jahr von der UN-Generalversammlung verurteilt, um ein Land zu brechen, das sich nicht unterwirft.',
 -2, 'Economic warfare', 'Wirtschaftskrieg',
 ARRAY['TASS (EN)','TASS','RT','Lenta.ru','Izvestia','Gazeta.ru','Kommersant','CGTN','China Daily','Global Times','Press TV','Al Jazeera','Al Arabiya','Al-Ahram','Anadolu Agency','TRT World','Daily Sabah'],
 NULL, false, ARRAY['EUROPE-RUSSIA','ASIA-CHINA','AMERICAS-CUBA'], 3, true)
ON CONFLICT (id) DO UPDATE SET fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en,
 name_de=EXCLUDED.name_de, claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de,
 stance=EXCLUDED.stance, stance_label_en=EXCLUDED.stance_label_en,
 stance_label_de=EXCLUDED.stance_label_de, publishers=EXCLUDED.publishers,
 framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
 actor_centroids=EXCLUDED.actor_centroids, display_order=EXCLUDED.display_order,
 is_active=true, updated_at=NOW();

-- ===========================================================================
-- B. cuba_energy_collapse -- the causation dispute
-- ===========================================================================
INSERT INTO narratives_v2 (id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, publishers, framing_keywords,
    framing_required, actor_centroids, display_order, is_active) VALUES
('cuba_collapse_self_inflicted', 'cuba_energy_collapse',
 'Decades of mismanagement, not the blockade, emptied the grid',
 'Jahrzehnte der Misswirtschaft, nicht die Blockade, haben das Netz geleert',
 'A Soviet-era grid left unmaintained, a state-run economy that never generated hard currency and a refusal to reform are why the lights went out; external pressure only exposed a model that had already failed.',
 'Ein nie instand gehaltenes Netz aus Sowjetzeiten, eine Staatswirtschaft ohne Devisen und die Verweigerung von Reformen sind der Grund für die Dunkelheit; äußerer Druck hat nur ein längst gescheitertes Modell offengelegt.',
 1, 'Self-inflicted collapse', 'Selbstverschuldeter Zusammenbruch',
 ARRAY['Fox News','Jerusalem Post','Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','El País','El Mundo','Clarín','La Nación','Reforma','El Universal','Folha de S.Paulo','O Globo','O Estado de S. Paulo'],
 ARRAY['mismanagement','decades of','Soviet-era','ageing','aging','obsolete','decaying','state-run','central planning','self-inflicted','failed model','inefficien','Misswirtschaft','veraltet','marode','Planwirtschaft','gescheitert','mala gestión','décadas','obsolet','envejecid','modelo fallido','ineficien','ruinó'],
 true, ARRAY['AMERICAS-CUBA'], 1, true),

('cuba_collapse_humanitarian_alarm', 'cuba_energy_collapse',
 'A humanitarian emergency is unfolding whoever is to blame',
 'Eine humanitäre Notlage entfaltet sich, gleich wer schuld ist',
 'Hospitals without power, uncollected refuse, malnutrition and UN warnings of collapse describe a civilian emergency that has outrun the argument about its causes.',
 'Kliniken ohne Strom, nicht abgeholter Müll, Mangelernährung und UN-Warnungen vor einem Zusammenbruch beschreiben eine zivile Notlage, die den Streit über ihre Ursachen längst überholt hat.',
 -1, 'Humanitarian emergency', 'Humanitäre Notlage',
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','UN News','El País','El Mundo','Clarín','La Nación','Reforma','El Universal','Folha de S.Paulo','O Globo','O Estado de S. Paulo','Mexico News Daily'],
 ARRAY['humanitarian','emergency','children are dying','civilians','hospital','malnutrition','hunger','UN warns','catastroph','suffering','desperate','misery','humanitär','Notlage','Zivilisten','Katastroph','Hunger','Leid','humanitaria','emergencia','civiles','catástrofe','sufrimiento','hambre','agoniza','asfixia'],
 true, ARRAY['NON-STATE-EU','AMERICAS-CUBA'], 2, true),

('cuba_collapse_starvation_siege', 'cuba_energy_collapse',
 'Starvation by siege is a deliberate instrument of policy',
 'Aushungern durch Belagerung ist ein bewusstes Instrument der Politik',
 'Cutting a small island''s fuel until its hospitals go dark and its children go hungry is not a side effect but the objective -- collective punishment used to force political surrender.',
 'Einer kleinen Insel den Treibstoff zu nehmen, bis ihre Kliniken dunkel werden und ihre Kinder hungern, ist keine Nebenwirkung, sondern das Ziel -- Kollektivstrafe zur Erzwingung politischer Kapitulation.',
 -2, 'Starvation as a weapon', 'Aushungern als Waffe',
 ARRAY['TASS (EN)','TASS','RT','Lenta.ru','Izvestia','Gazeta.ru','Kommersant','CGTN','China Daily','Global Times','Press TV','Al Jazeera','Al Arabiya','Al-Ahram','Anadolu Agency','TRT World','Daily Sabah'],
 NULL, false, ARRAY['EUROPE-RUSSIA','ASIA-CHINA','AMERICAS-CUBA'], 3, true)
ON CONFLICT (id) DO UPDATE SET fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en,
 name_de=EXCLUDED.name_de, claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de,
 stance=EXCLUDED.stance, stance_label_en=EXCLUDED.stance_label_en,
 stance_label_de=EXCLUDED.stance_label_de, publishers=EXCLUDED.publishers,
 framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
 actor_centroids=EXCLUDED.actor_centroids, display_order=EXCLUDED.display_order,
 is_active=true, updated_at=NOW();

-- ===========================================================================
-- C. cuba_external_lifelines -- patron competition
-- ===========================================================================
INSERT INTO narratives_v2 (id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, publishers, framing_keywords,
    framing_required, actor_centroids, display_order, is_active) VALUES
('cuba_lifelines_prop_up', 'cuba_external_lifelines',
 'Outside shipments prop up a government that would otherwise have to change',
 'Lieferungen von außen stützen eine Regierung, die sich sonst ändern müsste',
 'Russian and Venezuelan cargoes and third-country aid buy time for a leadership that has refused reform, blunting the only pressure that has ever moved it.',
 'Russische und venezolanische Ladungen sowie Hilfe aus Drittstaaten verschaffen einer reformunwilligen Führung Zeit und stumpfen den einzigen Druck ab, der je etwas bewegt hat.',
 1, 'Propping up the government', 'Stützung der Regierung',
 ARRAY['Fox News','Jerusalem Post','Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','El País','El Mundo','Clarín','La Nación','Reforma','Folha de S.Paulo','O Globo','O Estado de S. Paulo'],
 ARRAY['prop up','props up','lifeline for the government','undercut','circumvent','evade','sanctions-busting','prolong','buy time','rescue','stütz','umgehen','verlängert','Rettungsanker','apuntalar','eludir','prolongar','oxígeno','rescate','respiro'],
 true, ARRAY['AMERICAS-CUBA','EUROPE-RUSSIA'], 1, true),

('cuba_lifelines_humanitarian_duty', 'cuba_external_lifelines',
 'Relief is a humanitarian obligation and third states should not be coerced',
 'Hilfe ist eine humanitäre Pflicht, und Drittstaaten dürfen nicht genötigt werden',
 'Mexico, Spain, Brazil and Canada are meeting an obligation to a population in crisis, and pressuring them to withhold fuel and food turns civilians into the instrument of a dispute between governments.',
 'Mexiko, Spanien, Brasilien und Kanada erfüllen eine Pflicht gegenüber einer Bevölkerung in der Krise; sie zum Zurückhalten von Treibstoff und Nahrung zu drängen, macht Zivilisten zum Werkzeug eines Regierungsstreits.',
 -1, 'Humanitarian obligation', 'Humanitäre Pflicht',
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','UN News','El País','El Mundo','Clarín','La Nación','Reforma','El Universal','Folha de S.Paulo','O Globo','O Estado de S. Paulo','Mexico News Daily'],
 ARRAY['humanitarian','obligation','must reach','blocked','hampers','dialogue','diplomatic path','sovereign right','solidarity','donate','relief effort','humanitär','Pflicht','Dialog','souverän','Solidarität','humanitaria','obligación','vía diplomática','diálogo','soberan','solidaridad','donar','debe llegar'],
 true, ARRAY['AMERICAS-MEXICO','EUROPE-SOUTH','AMERICAS-CUBA'], 2, true),

('cuba_lifelines_solidarity', 'cuba_external_lifelines',
 'Solidarity with a besieged island against an illegal siege',
 'Solidarität mit einer belagerten Insel gegen eine illegale Belagerung',
 'Fuel, grain and credit sent in the face of US threats are acts of principled solidarity between sovereign states, and the attempt to stop them shows the siege was never about the Cuban people.',
 'Treibstoff, Getreide und Kredite, die trotz US-Drohungen geschickt werden, sind Akte prinzipientreuer Solidarität zwischen souveränen Staaten; der Versuch, sie zu stoppen, zeigt, dass es bei der Belagerung nie um das kubanische Volk ging.',
 -2, 'Sovereign solidarity', 'Souveräne Solidarität',
 ARRAY['TASS (EN)','TASS','RT','Lenta.ru','Izvestia','Gazeta.ru','Kommersant','CGTN','China Daily','Global Times','Press TV','Al Jazeera','Al Arabiya','Al-Ahram','Anadolu Agency','TRT World','Daily Sabah'],
 NULL, false, ARRAY['EUROPE-RUSSIA','ASIA-CHINA','AMERICAS-CUBA'], 3, true)
ON CONFLICT (id) DO UPDATE SET fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en,
 name_de=EXCLUDED.name_de, claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de,
 stance=EXCLUDED.stance, stance_label_en=EXCLUDED.stance_label_en,
 stance_label_de=EXCLUDED.stance_label_de, publishers=EXCLUDED.publishers,
 framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
 actor_centroids=EXCLUDED.actor_centroids, display_order=EXCLUDED.display_order,
 is_active=true, updated_at=NOW();

-- ===========================================================================
-- D. cuba_military_coercion
-- ===========================================================================
INSERT INTO narratives_v2 (id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, publishers, framing_keywords,
    framing_required, actor_centroids, display_order, is_active) VALUES
('cuba_force_credible_threat', 'cuba_military_coercion',
 'A credible threat of force is what brought Havana to the table',
 'Eine glaubwürdige Drohung mit Gewalt hat Havanna an den Tisch gebracht',
 'Carrier deployments and reconnaissance flights are signalling, not war -- and the shift from refusal to negotiation followed them, as did Havana''s own escalatory plotting.',
 'Trägerverlegungen und Aufklärungsflüge sind Signale, kein Krieg -- und der Wechsel von Verweigerung zu Verhandlung folgte auf sie, ebenso wie Havannas eigene Eskalationspläne.',
 1, 'Credible deterrence', 'Glaubwürdige Abschreckung',
 ARRAY['Fox News','Jerusalem Post','Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','El País','El Mundo','Clarín','La Nación','Reforma','Folha de S.Paulo','O Globo','O Estado de S. Paulo'],
 ARRAY['credible','all options','military option','signal','deterren','brought to the table','drone attack','plotting','provocation','threat to the US','glaubwürdig','alle Optionen','Abschreckung','Provokation','Signal','opción militar','amenaza para','provocación','disuasión'],
 true, ARRAY['AMERICAS-USA','AMERICAS-CUBA'], 1, true),

('cuba_force_unlawful', 'cuba_military_coercion',
 'Threatening to take an island is unlawful and reckless',
 'Die Drohung, eine Insel zu nehmen, ist rechtswidrig und leichtsinnig',
 'There is no congressional authorisation, no legal basis for seizing a sovereign state, and every historical precedent from the Bay of Pigs onward points to a costly failure.',
 'Es gibt keine Ermächtigung des Kongresses, keine Rechtsgrundlage für die Inbesitznahme eines souveränen Staates, und jeder historische Präzedenzfall seit der Schweinebucht deutet auf ein teures Scheitern.',
 -1, 'Unlawful and reckless', 'Rechtswidrig und leichtsinnig',
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','UN News','El País','El Mundo','Clarín','La Nación','Reforma','El Universal','Folha de S.Paulo','O Globo','O Estado de S. Paulo','Mexico News Daily'],
 ARRAY['unlawful','illegal','without authorisation','without authorization','war powers','no congressional','Bay of Pigs','quagmire','bloodbath','reckless','rechtswidrig','ohne Mandat','Kriegsvollmachten','Schweinebucht','leichtsinnig','Blutbad','ilegal','sin autorización','Bahía de Cochinos','baño de sangre','imprudente'],
 true, ARRAY['NON-STATE-EU','AMERICAS-USA','AMERICAS-CUBA'], 2, true),

('cuba_force_imperial_aggression', 'cuba_military_coercion',
 'Gunboat diplomacy against a small neighbour is imperial aggression',
 'Kanonenbootpolitik gegen einen kleinen Nachbarn ist imperiale Aggression',
 'Moving a carrier group into the Caribbean and openly discussing seizing an island revives the crudest form of hemispheric domination, whatever pretext is offered.',
 'Eine Trägergruppe in die Karibik zu verlegen und offen über die Inbesitznahme einer Insel zu sprechen, belebt die roheste Form hemisphärischer Vorherrschaft -- unter welchem Vorwand auch immer.',
 -2, 'Imperial aggression', 'Imperiale Aggression',
 ARRAY['TASS (EN)','TASS','RT','Lenta.ru','Izvestia','Gazeta.ru','Kommersant','CGTN','China Daily','Global Times','Press TV','Al Jazeera','Al Arabiya','Al-Ahram','Anadolu Agency','TRT World','Daily Sabah'],
 NULL, false, ARRAY['EUROPE-RUSSIA','ASIA-CHINA','AMERICAS-CUBA'], 3, true)
ON CONFLICT (id) DO UPDATE SET fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en,
 name_de=EXCLUDED.name_de, claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de,
 stance=EXCLUDED.stance, stance_label_en=EXCLUDED.stance_label_en,
 stance_label_de=EXCLUDED.stance_label_de, publishers=EXCLUDED.publishers,
 framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
 actor_centroids=EXCLUDED.actor_centroids, display_order=EXCLUDED.display_order,
 is_active=true, updated_at=NOW();

-- ===========================================================================
-- E. cuba_regime_survival -- legitimacy and internal control
-- ===========================================================================
INSERT INTO narratives_v2 (id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, publishers, framing_keywords,
    framing_required, actor_centroids, display_order, is_active) VALUES
('cuba_repression_documented', 'cuba_regime_survival',
 'One-party rule holds by arresting those who protest',
 'Die Einparteienherrschaft hält sich, indem sie Protestierende verhaftet',
 'Arrests after blackout protests, political prisoners used as bargaining chips and a party that permits no alternative describe control maintained by coercion, not consent.',
 'Verhaftungen nach Protesten gegen Stromausfälle, politische Gefangene als Verhandlungsmasse und eine Partei, die keine Alternative zulässt, beschreiben Kontrolle durch Zwang, nicht durch Zustimmung.',
 1, 'Rule by repression', 'Herrschaft durch Repression',
 ARRAY['Fox News','Jerusalem Post','Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','El País','El Mundo','Clarín','La Nación','Reforma','Folha de S.Paulo','O Globo','O Estado de S. Paulo'],
 ARRAY['political prisoner','dissident','arrested','jailed','detained','crackdown','one-party','censorship','bargaining chip','repressive','politische Gefangene','inhaftiert','verhaftet','Einparteien','Zensur','Repression','preso político','disidente','detenid','encarcelad','represión','partido único','censura'],
 true, ARRAY['AMERICAS-CUBA'], 1, true),

('cuba_reform_under_siege', 'cuba_regime_survival',
 'A real opening is under way but external pressure is throttling it',
 'Eine echte Öffnung läuft, doch äußerer Druck erstickt sie',
 'The largest economic liberalisation since 1959 and the release of thousands of prisoners are genuine movement -- and the pressure campaign gives hardliners the argument that opening invites attack.',
 'Die größte wirtschaftliche Liberalisierung seit 1959 und die Freilassung Tausender Gefangener sind echte Bewegung -- und die Druckkampagne liefert Hardlinern das Argument, Öffnung lade Angriffe ein.',
 -1, 'Reform throttled by pressure', 'Reform durch Druck erstickt',
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','UN News','El País','El Mundo','Clarín','La Nación','Reforma','El Universal','Folha de S.Paulo','O Globo','O Estado de S. Paulo','Mexico News Daily'],
 ARRAY['reform','liberalis','liberaliz','opening','private sector','released','freed','pardon','largest package','genuine','Reform','Öffnung','Privatsektor','freigelassen','Begnadigung','reforma','apertura','excarcela','liberad','indulto','sector privado'],
 true, ARRAY['AMERICAS-CUBA'], 2, true),

('cuba_sovereign_resistance', 'cuba_regime_survival',
 'A sovereign people is resisting an externally engineered regime change',
 'Ein souveränes Volk widersteht einem von außen betriebenen Regimewechsel',
 'What is called repression is a state defending itself against infiltration, sabotage and an openly declared campaign to remove its government -- self-determination is the issue, not dissent.',
 'Was Repression genannt wird, ist ein Staat, der sich gegen Infiltration, Sabotage und eine offen erklärte Kampagne zum Sturz seiner Regierung verteidigt -- es geht um Selbstbestimmung, nicht um Dissens.',
 -2, 'Sovereign resistance', 'Souveräner Widerstand',
 ARRAY['TASS (EN)','TASS','RT','Lenta.ru','Izvestia','Gazeta.ru','Kommersant','CGTN','China Daily','Global Times','Press TV','Al Jazeera','Al Arabiya','Al-Ahram','Anadolu Agency','TRT World','Daily Sabah'],
 NULL, false, ARRAY['EUROPE-RUSSIA','ASIA-CHINA','AMERICAS-CUBA'], 3, true)
ON CONFLICT (id) DO UPDATE SET fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en,
 name_de=EXCLUDED.name_de, claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de,
 stance=EXCLUDED.stance, stance_label_en=EXCLUDED.stance_label_en,
 stance_label_de=EXCLUDED.stance_label_de, publishers=EXCLUDED.publishers,
 framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
 actor_centroids=EXCLUDED.actor_centroids, display_order=EXCLUDED.display_order,
 is_active=true, updated_at=NOW();

-- ===========================================================================
-- THEATER CARDS (§5.5). Roll-up matches member-atomic titles by SIGN +
-- publisher. Negative bucket (-1, -2) must be publisher-DISJOINT or counts
-- double-count: Western/Latin vs Russian/Chinese/Global-South -- disjoint.
-- The +2 card may share publishers with the -1 card: opposite signs pull
-- different-signed atomic titles, so no title is counted twice.
-- ===========================================================================
INSERT INTO narratives_v2 (id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, publishers, framing_keywords,
    framing_required, actor_centroids, display_order, is_active) VALUES
('cuba_theater_pressure_consensus', 'cuba_theater',
 'Maximum pressure is finally forcing change on a failed one-party state',
 'Maximaldruck erzwingt endlich Wandel in einem gescheiterten Einparteienstaat',
 'Sanctions, indictments and a credible military signal have done what six decades of embargo did not: brought Havana to negotiate, opened the economy and emptied the prisons -- the failure being exposed is the regime''s own.',
 'Sanktionen, Anklagen und ein glaubwürdiges militärisches Signal haben erreicht, woran sechs Jahrzehnte Embargo scheiterten: Havanna verhandelt, die Wirtschaft öffnet sich, die Gefängnisse leeren sich -- offengelegt wird das Versagen des Regimes selbst.',
 2, 'Pressure is working', 'Der Druck wirkt',
 ARRAY['Fox News','Jerusalem Post','Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','El País','El Mundo','Clarín','La Nación','Reforma','El Universal','Folha de S.Paulo','O Globo','O Estado de S. Paulo','Mexico News Daily','UN News'],
 NULL, false, ARRAY['AMERICAS-USA','AMERICAS-CUBA'], 1, true),

('cuba_theater_western_critique', 'cuba_theater',
 'The pressure campaign has become a humanitarian and legal problem of its own',
 'Die Druckkampagne ist selbst zu einem humanitären und rechtlichen Problem geworden',
 'Extraterritorial sanctions on third countries, an island without electricity or medicine, and open talk of seizing a sovereign state have moved the campaign past what its own stated aims can justify.',
 'Extraterritoriale Sanktionen gegen Drittstaaten, eine Insel ohne Strom und Medikamente und offenes Gerede über die Inbesitznahme eines souveränen Staates haben die Kampagne über das hinausgeführt, was ihre erklärten Ziele rechtfertigen.',
 -1, 'Overreach and human cost', 'Übergriffigkeit und menschliche Kosten',
 ARRAY['Reuters','Associated Press','BBC World','CNN','New York Times','Washington Post','The Guardian','NPR','MSNBC','ABC News','Sky News','The Telegraph','Bloomberg','Wall Street Journal','Financial Times','The Economist','Globe and Mail','France 24','France 24 (EN)','Euronews','Deutsche Welle','Tagesschau','Der Spiegel','Die Zeit','Le Monde','Le Figaro','Corriere della Sera','La Repubblica','Straits Times','UN News','El País','El Mundo','Clarín','La Nación','Reforma','El Universal','Folha de S.Paulo','O Globo','O Estado de S. Paulo','Mexico News Daily'],
 NULL, false, ARRAY['NON-STATE-EU','AMERICAS-CUBA'], 2, true),

('cuba_theater_anti_imperial', 'cuba_theater',
 'A siege to break a sovereign nation that refuses to submit',
 'Eine Belagerung, um eine souveräne Nation zu brechen, die sich nicht unterwirft',
 'Fuel cut off, warships offshore, a former head of state indicted and allies punished for sending aid -- this is coercion of a small country for refusing hemispheric obedience, and solidarity with it is a defence of sovereignty itself.',
 'Abgeschnittener Treibstoff, Kriegsschiffe vor der Küste, ein angeklagter früherer Staatschef und für Hilfslieferungen bestrafte Verbündete -- das ist Nötigung eines kleinen Landes für verweigerten hemisphärischen Gehorsam, und Solidarität mit ihm verteidigt die Souveränität selbst.',
 -2, 'Siege and sovereignty', 'Belagerung und Souveränität',
 ARRAY['TASS (EN)','TASS','RT','Lenta.ru','Izvestia','Gazeta.ru','Kommersant','CGTN','China Daily','Global Times','Press TV','Al Jazeera','Al Arabiya','Al-Ahram','Anadolu Agency','TRT World','Daily Sabah'],
 NULL, false, ARRAY['EUROPE-RUSSIA','ASIA-CHINA','AMERICAS-CUBA'], 3, true)
ON CONFLICT (id) DO UPDATE SET fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en,
 name_de=EXCLUDED.name_de, claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de,
 stance=EXCLUDED.stance, stance_label_en=EXCLUDED.stance_label_en,
 stance_label_de=EXCLUDED.stance_label_de, publishers=EXCLUDED.publishers,
 framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
 actor_centroids=EXCLUDED.actor_centroids, display_order=EXCLUDED.display_order,
 is_active=true, updated_at=NOW();

COMMIT;

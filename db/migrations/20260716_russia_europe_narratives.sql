-- Russia-Europe theater narratives (Phase 2, step E).
-- Atomic narratives for russia_nato_deterrence, russia_hybrid_warfare,
-- russia_airspace_incursions (russia_sanctions_regime already has narratives).
-- Plus theater-level roll-up cards on russia_europe_theater (spec sec 5.5).
-- Design authored in docs/context/RUSSIA_EUROPE_THEATER_BUILD.md.

-- ============================================================
-- russia_nato_deterrence
-- ============================================================

INSERT INTO narratives_v2 (fn_id, id, name_en, name_de, claim_en, claim_de,
  stance, stance_label_en, stance_label_de, actor_centroids, publishers,
  framing_keywords, framing_required, display_order, is_active)
VALUES
('russia_nato_deterrence', 'eastern_flank_deterrence',
 'Eastern-flank build-up is necessary deterrence against a revanchist Russia',
 'Der Ausbau der Ostflanke ist notwendige Abschreckung gegen ein revisionistisches Russland',
 'Western-mainstream and Eastern-European framing treats the post-2022 build-up on NATO''s eastern flank -- enhanced Forward Presence brigades in the Baltics, Kaliningrad-facing air policing, rearmament and rising defence budgets, reintroduced conscription in several states -- as a proportionate and overdue response to a Russian military threat that is not going away. Coverage emphasises intelligence assessments of Russian reconstitution timelines, the credibility of Article 5, and the logic of raising the cost of any future aggression. Prescription: sustain or accelerate defence-spending increases, keep forward-deployed brigades in place, invest in air and missile defence, and treat rearmament as insurance rather than provocation.',
 'Die westliche Mainstream- und osteuropäische Berichterstattung behandelt den Ausbau der NATO-Ostflanke seit 2022 -- verstärkte Vornepräsenz-Brigaden im Baltikum, Luftpolizei gegenüber Kaliningrad, Aufrüstung und steigende Verteidigungsbudgets, wiedereingeführte Wehrpflicht in mehreren Staaten -- als angemessene und überfällige Reaktion auf eine anhaltende russische Bedrohung. Die Berichterstattung betont geheimdienstliche Einschätzungen zur russischen Wiederaufrüstung, die Glaubwürdigkeit von Artikel 5 und die Logik, die Kosten künftiger Aggression zu erhöhen. Handlungsempfehlung: Verteidigungsausgaben beibehalten oder erhöhen, vorwärtsstationierte Brigaden belassen, in Luft- und Raketenabwehr investieren und Aufrüstung als Versicherung statt Provokation begreifen.',
 2, 'Eastern-flank deterrence is necessary', 'Ostflanken-Abschreckung ist notwendig',
 ARRAY['EUROPE-RUSSIA','NON-STATE-EU','NON-STATE-NATO','EUROPE-BALTIC','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-VISEGRAD','EUROPE-NORDIC'],
 ARRAY['Reuters','BBC World','Financial Times','Associated Press','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','Wall Street Journal','New York Times','Washington Post','NPR','CNN','ABC News','Military Times','Defense News','ERR News','LRT English','LSM English','Atlantic Council','Politico','Kyiv Post','The Telegraph','The Economist','EurActiv','Bloomberg'],
 ARRAY['deter','deterrence','Russian threat','defend','defend the flank','forward presence','reinforce','readiness','build-up','rearm','harden','credible defence','Abschreckung','russische Bedrohung','verstärken','Wehrhaftigkeit'],
 false, 1, true),

('russia_nato_deterrence', 'nato_encirclement_provocation',
 'NATO''s eastern build-up is aggressive encirclement driving escalation',
 'Der NATO-Ausbau im Osten ist aggressive Einkreisung, die Eskalation treibt',
 'Russian state media and allied outlets frame the same build-up as evidence of NATO aggression and encirclement: forward brigades and rearmament are read as preparation for confrontation with Russia rather than defence, conscription and rising defence budgets as militarisation of European society, and enhanced Forward Presence as breaking prior security assurances. Coverage stresses NATO''s eastward expansion since the 1990s as the root cause of the confrontation and casts Russian counter-measures as reactive. Prescription: NATO should reverse eastern deployments, halt further enlargement, and de-escalate rather than continue rearmament.',
 'Russische Staatsmedien und verbündete Sender deuten denselben Ausbau als Beweis für NATO-Aggression und Einkreisung: Vorwärtsbrigaden und Aufrüstung werden als Vorbereitung auf eine Konfrontation mit Russland statt als Verteidigung gelesen, Wehrpflicht und steigende Verteidigungsbudgets als Militarisierung der europäischen Gesellschaft, verstärkte Vornepräsenz als Bruch früherer Sicherheitszusagen. Die Berichterstattung betont die NATO-Osterweiterung seit den 1990er Jahren als eigentliche Ursache der Konfrontation und stellt russische Gegenmaßnahmen als reaktiv dar. Handlungsempfehlung: Die NATO solle die Ost-Stationierungen zurücknehmen, weitere Erweiterung stoppen und deeskalieren statt weiter aufzurüsten.',
 -2, 'NATO build-up is encirclement', 'NATO-Ausbau ist Einkreisung',
 ARRAY['EUROPE-RUSSIA','EUROPE-BELARUS'],
 ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Izvestia','Kommersant','BelTA','BelTA Russian','Press TV','CGTN','Global Times','China Daily','Xinhua'],
 ARRAY['encirclement','encircle','provocation','NATO aggression','aggressive expansion','militarization','destabilize','arms race','Cold War mentality','security guarantees broken','Einkreisung','Provokation','NATO-Aggression','Militarisierung'],
 false, 2, true),

('russia_nato_deterrence', 'militarisation_overreach',
 'Threat inflation and war-economy drift are a costly overreach',
 'Bedrohungsinflation und Kriegswirtschafts-Drift sind teurer Übereifer',
 'A skeptical Western-European current, distinct from both the Atlanticist consensus and the Kremlin counter-frame, warns that rearmament and rising defence budgets have outpaced the actual near-term Russian threat, diverting public spending from social priorities into a war economy without clear strategic benchmarks. Coverage highlights economists and politicians questioning whether conscription and brigade expansions are proportionate, and flags the risk that threat inflation becomes self-fulfilling. Framing keywords are required here because the same Western outlets that support deterrence in general also carry this internal critique -- publisher coalition alone cannot separate the two stances.',
 'Eine skeptische westeuropäische Strömung, die sich sowohl vom atlantischen Konsens als auch vom Kreml-Gegenframe unterscheidet, warnt, dass Aufrüstung und steigende Verteidigungsbudgets die tatsächliche kurzfristige russische Bedrohung überschritten haben und öffentliche Mittel ohne klare strategische Maßstäbe in eine Kriegswirtschaft umlenken. Die Berichterstattung hebt Ökonomen und Politiker hervor, die die Verhältnismäßigkeit von Wehrpflicht und Brigadenausbau infrage stellen, und warnt vor selbsterfüllender Bedrohungsinflation. Framing-Schlüsselwörter sind hier nötig, weil dieselben westlichen Medien, die Abschreckung grundsätzlich unterstützen, auch diese interne Kritik führen -- die Publisher-Koalition allein trennt die beiden Haltungen nicht.',
 -1, 'Militarisation is overreach', 'Militarisierung ist Übereifer',
 ARRAY['EUROPE-GERMANY','EUROPE-FRANCE','NON-STATE-EU','EUROPE-NORDIC'],
 ARRAY['Le Monde','El País','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','The Independent','ANSA','La Repubblica','Al Jazeera','Anadolu Agency','Channel NewsAsia'],
 ARRAY['threat inflation','war economy','militarisation','overreach','Bedrohungsinflation','Kriegswirtschaft','Militarisierung','Übereifer','defence-spending burden','Rüstungslast','disproportionate','unverhältnismäßig','alte Ängste','weckt Ängste','Angst vor Aufrüstung','fear of rearmament'],
 true, 3, true)
ON CONFLICT (id) DO UPDATE SET
 name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de, claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de,
 stance=EXCLUDED.stance, stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
 actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers, framing_keywords=EXCLUDED.framing_keywords,
 framing_required=EXCLUDED.framing_required, display_order=EXCLUDED.display_order, is_active=true, updated_at=now();

-- ============================================================
-- russia_hybrid_warfare
-- ============================================================

INSERT INTO narratives_v2 (fn_id, id, name_en, name_de, claim_en, claim_de,
  stance, stance_label_en, stance_label_de, actor_centroids, publishers,
  framing_keywords, framing_required, display_order, is_active)
VALUES
('russia_hybrid_warfare', 'hybrid_campaign_defence',
 'Russia is waging a coordinated gray-zone campaign that requires attribution and hardening',
 'Russland führt eine koordinierte Grauzonen-Kampagne, die Attribution und Härtung erfordert',
 'Western-mainstream and Baltic/Nordic press treat the pattern of undersea cable damage, GPS jamming and spoofing, arson attacks, and shadow-fleet activity as a coordinated Russian gray-zone campaign below the threshold of open war. Coverage documents the Nord Stream sabotage prosecution, shadow-fleet tanker seizures and detentions, and new national hybrid-threat centres, framing these as evidence that attribution and resilience-building are catching up to a real threat. Prescription: expand undersea infrastructure protection, tighten shadow-fleet enforcement and interdiction, invest in GPS-jamming resilience, and pursue criminal prosecution of identified saboteurs.',
 'Westliche Mainstream- und baltisch-nordische Medien behandeln das Muster aus Unterseekabel-Schäden, GPS-Störung und Spoofing, Brandanschlägen und Schattenflotten-Aktivität als koordinierte russische Grauzonen-Kampagne unterhalb der Schwelle offenen Krieges. Die Berichterstattung dokumentiert das Nord-Stream-Sabotage-Verfahren, Beschlagnahmungen und Festsetzungen von Schattenflotten-Tankern sowie neue nationale Zentren gegen hybride Bedrohungen und wertet dies als Beleg dafür, dass Attribution und Resilienzaufbau einer realen Bedrohung gerecht werden. Handlungsempfehlung: Schutz der Unterseeinfrastruktur ausbauen, Durchsetzung und Abfangen gegen die Schattenflotte verschärfen, in GPS-Störfestigkeit investieren und identifizierte Saboteure strafrechtlich verfolgen.',
 2, 'Hybrid campaign requires a hardened response', 'Hybride Kampagne erfordert gehärtete Antwort',
 ARRAY['EUROPE-RUSSIA','NON-STATE-EU','NON-STATE-NATO','EUROPE-BALTIC','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-VISEGRAD','EUROPE-NORDIC'],
 ARRAY['Reuters','BBC World','Financial Times','Associated Press','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','Wall Street Journal','New York Times','Washington Post','NPR','CNN','ABC News','Military Times','Defense News','ERR News','LRT English','LSM English','Atlantic Council','Politico','Kyiv Post','The Telegraph','The Economist','EurActiv','Bloomberg'],
 ARRAY['sabotage campaign','coordinated attack','gray-zone','hybrid warfare','Kremlin''s hand','attribution','resilience','harden','crackdown','shadow fleet','below the threshold','hybride Kriegsführung','Sabotage-Kampagne','Angriff','Härtung'],
 false, 1, true),

('russia_hybrid_warfare', 'hybrid_russophobia_denial',
 'Hybrid-threat claims are evidence-free Russophobia; shadow-fleet seizures are piracy',
 'Vorwürfe hybrider Bedrohung sind beweisfreie Russophobie; Schattenflotten-Beschlagnahmungen sind Piraterie',
 'Russian and allied state media dismiss sabotage and hybrid-threat attributions as evidence-free Russophobia, arguing that cable damage and jamming incidents are accidents, criminality, or provocations staged to justify further militarisation. Shadow-fleet tanker seizures by European navies are cast as maritime piracy and illegal interference with lawful commercial shipping under a Western sanctions regime that has no basis in international law. Prescription: release seized vessels, end shadow-fleet interdiction, and stop attributing accidents to Russia without proof.',
 'Russische und verbündete Staatsmedien weisen Sabotage- und Hybrid-Bedrohungs-Zuschreibungen als beweisfreie Russophobie zurück und argumentieren, Kabelschäden und Störvorfälle seien Unfälle, Kriminalität oder inszenierte Provokationen zur Rechtfertigung weiterer Militarisierung. Beschlagnahmungen von Schattenflotten-Tankern durch europäische Marinen werden als Piraterie und rechtswidrige Einmischung in rechtmäßigen Handelsschiffsverkehr unter einem völkerrechtlich unbegründeten westlichen Sanktionsregime dargestellt. Handlungsempfehlung: beschlagnahmte Schiffe freigeben, das Abfangen der Schattenflotte beenden und Unfälle nicht ohne Beweise Russland zuschreiben.',
 -2, 'Hybrid-threat claims are Russophobia', 'Hybrid-Vorwürfe sind Russophobie',
 ARRAY['EUROPE-RUSSIA','EUROPE-BELARUS'],
 ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Izvestia','Kommersant','BelTA','BelTA Russian','Press TV','CGTN','Global Times','China Daily','Xinhua'],
 ARRAY['Russophobia','evidence-free','unfounded accusation','witch hunt','maritime piracy','illegal seizure','staged provocation','manufactured threat','Russophobie','unbegründet','Piraterie','Vorwand'],
 false, 2, true),

('russia_hybrid_warfare', 'securitisation_caution',
 'Caution against over-attribution: accidents and criminality get mislabeled as Kremlin sabotage',
 'Vorsicht vor Über-Attribution: Unfälle und Kriminalität werden fälschlich dem Kreml zugeschrieben',
 'A cautious current within Western and European press, distinct from the pro-deterrence mainstream, warns against securitisation without evidence: anchor-dragging incidents may be genuine maritime accidents, some "saboteurs" turn out to be unrelated criminal actors, and rushing to attribute every incident to Russia risks discrediting real cases and inflaming public anxiety. Coverage calls for prosecutorial rigor and warns that over-attribution is itself a policy risk. Framing keywords are required because this critique runs in the same outlets that otherwise support hybrid-threat hardening.',
 'Eine vorsichtige Strömung innerhalb der westlichen und europäischen Presse, die sich vom abschreckungsfreundlichen Mainstream unterscheidet, warnt vor Versicherheitlichung ohne Beweise: Ankerschleifen-Vorfälle könnten echte Schifffahrtsunfälle sein, manche "Saboteure" erweisen sich als unbeteiligte Kriminelle, und die vorschnelle Zuschreibung jedes Vorfalls an Russland riskiert, echte Fälle zu diskreditieren und öffentliche Ängste zu schüren. Die Berichterstattung fordert staatsanwaltschaftliche Sorgfalt und warnt, dass Über-Attribution selbst ein politisches Risiko ist. Framing-Schlüsselwörter sind nötig, weil diese Kritik in denselben Medien läuft, die ansonsten die Härtung gegen hybride Bedrohungen unterstützen.',
 -1, 'Over-attribution risks discrediting real cases', 'Über-Attribution riskiert Diskreditierung echter Fälle',
 ARRAY['EUROPE-GERMANY','EUROPE-FRANCE','NON-STATE-EU','EUROPE-NORDIC'],
 ARRAY['Le Monde','El País','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','The Independent','ANSA','La Repubblica','Al Jazeera','Anadolu Agency','Channel NewsAsia'],
 ARRAY['no evidence','accident','over-attribution','securitisation','unproven','kein Beweis','Unfall','unbewiesen','Verdachtsfall','vorschnell','rush to judgment','voreilig'],
 true, 3, true)
ON CONFLICT (id) DO UPDATE SET
 name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de, claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de,
 stance=EXCLUDED.stance, stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
 actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers, framing_keywords=EXCLUDED.framing_keywords,
 framing_required=EXCLUDED.framing_required, display_order=EXCLUDED.display_order, is_active=true, updated_at=now();

-- ============================================================
-- russia_airspace_incursions
-- ============================================================

INSERT INTO narratives_v2 (fn_id, id, name_en, name_de, claim_en, claim_de,
  stance, stance_label_en, stance_label_de, actor_centroids, publishers,
  framing_keywords, framing_required, display_order, is_active)
VALUES
('russia_airspace_incursions', 'airspace_violation_deterrence',
 'Russia deliberately probes NATO airspace to intimidate; NATO must enforce, including shoot-down authority',
 'Russland testet gezielt den NATO-Luftraum, um einzuschüchtern; die NATO muss durchsetzen, auch mit Abschussbefugnis',
 'Western-mainstream and Baltic/Nordic press treat repeated drone and aircraft incursions into NATO airspace as deliberate Russian probing intended to test alliance resolve and respond times, not accidents. Coverage documents scrambles and intercepts, national airspace closures in Finland and Poland, and growing debate over authorising NATO forces to shoot down violating drones and aircraft. Prescription: harden air-defence and detection, invoke Article 4 consultations where warranted, and grant shoot-down authority for repeated, unambiguous violations.',
 'Westliche Mainstream- und baltisch-nordische Medien behandeln wiederholte Drohnen- und Flugzeug-Einbrüche in den NATO-Luftraum als gezielte russische Tests zur Prüfung von Bündnis-Entschlossenheit und Reaktionszeiten, nicht als Unfälle. Die Berichterstattung dokumentiert Abfangeinsätze, nationale Luftraumsperrungen in Finnland und Polen sowie die wachsende Debatte, NATO-Kräften eine Abschussbefugnis gegen eindeutig verletzende Drohnen und Flugzeuge zu erteilen. Handlungsempfehlung: Luftverteidigung und Erkennung härten, Artikel-4-Konsultationen bei Bedarf einberufen und Abschussbefugnis für wiederholte, eindeutige Verletzungen erteilen.',
 2, 'Airspace violations demand a firm response', 'Luftraumverletzungen erfordern entschlossene Antwort',
 ARRAY['EUROPE-RUSSIA','NON-STATE-EU','NON-STATE-NATO','EUROPE-BALTIC','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-VISEGRAD','EUROPE-NORDIC'],
 ARRAY['Reuters','BBC World','Financial Times','Associated Press','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','Wall Street Journal','New York Times','Washington Post','NPR','CNN','ABC News','Military Times','Defense News','ERR News','LRT English','LSM English','Atlantic Council','Politico','Kyiv Post','The Telegraph','The Economist','EurActiv','Bloomberg'],
 ARRAY['probing','testing NATO resolve','deliberate incursion','violation','scramble','shoot down','harden air defence','Article 4','alliance resolve','Luftraumverletzung','eindringen','Entschlossenheit','Abschussbefugnis'],
 false, 1, true),

('russia_airspace_incursions', 'nato_complicity_provocation',
 'NATO territory hosts and enables Ukrainian drone strikes; incursions are Western provocations, not Russian aggression',
 'NATO-Gebiet beherbergt und ermöglicht ukrainische Drohnenangriffe; Einbrüche sind westliche Provokationen, keine russische Aggression',
 'Russian and allied state media invert the airspace-incursion narrative: Baltic and NATO states are accused of allowing or facilitating Ukrainian drone operations to launch from or transit their territory against Russia, making any Russian response or protest a matter of legitimate self-defence rather than aggression. Coverage frames alleged incursions as staged provocations or false flags designed to justify further NATO militarisation, and casts Western denials of complicity as not credible. This is the schadenfreude/rift-exploitation register, not endorsement of either side''s territorial claims -- the same bloc that runs the sanctions-ineffective and hybrid-Russophobia counter-narratives here reframes the incursion story onto NATO complicity rather than contesting the facts of any single incident.',
 'Russische und verbündete Staatsmedien kehren die Luftraum-Einbruch-Erzählung um: Baltischen und NATO-Staaten wird vorgeworfen, ukrainische Drohnenoperationen von ihrem Gebiet aus gegen Russland zuzulassen oder zu ermöglichen, wodurch jede russische Reaktion oder jeder Protest legitime Selbstverteidigung statt Aggression sei. Die Berichterstattung stellt angebliche Einbrüche als inszenierte Provokationen oder False-Flag-Operationen dar, die weitere NATO-Militarisierung rechtfertigen sollen, und stellt westliche Dementis der Mitschuld als unglaubwürdig dar. Dies ist das Schadenfreude-/Rift-Exploitation-Register, keine Zustimmung zu den Gebietsansprüchen einer der Seiten -- derselbe Block, der die sanktions-wirkungslos- und hybrid-russophobie-Gegenerzählungen führt, verlagert hier die Einbruch-Geschichte auf NATO-Mitschuld statt die Fakten eines einzelnen Vorfalls zu bestreiten.',
 -2, 'NATO territory enables Ukrainian strikes', 'NATO-Gebiet ermöglicht ukrainische Angriffe',
 ARRAY['EUROPE-RUSSIA','EUROPE-BELARUS'],
 ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Izvestia','Kommersant','BelTA','BelTA Russian','Press TV','CGTN','Global Times','China Daily','Xinhua'],
 ARRAY['complicity','false flag','staged provocation','enabling','launch pad','legitimate self-defence','not credible','Komplizenschaft','Inszenierung','Vorwand','Selbstverteidigung'],
 false, 2, true),

('russia_airspace_incursions', 'escalation_risk_restraint',
 'Shoot-down authority and forward posture risk uncontrolled escalation; many incidents are accidental or overblown',
 'Abschussbefugnis und Vorwärtsstationierung riskieren unkontrollierte Eskalation; viele Vorfälle sind unfallbedingt oder überzogen',
 'A restraint-minded current within Western and European press, distinct from both the pro-deterrence mainstream and the Kremlin counter-frame, warns that authorising forces to shoot down ambiguous contacts risks a shooting incident that escalates uncontrollably, and that some reported incursions -- stray drones blown off course, weather-related radar returns -- are accidental rather than deliberate probing. Coverage calls for restraint, clearer rules of engagement, and skepticism toward worst-case framing of every incident. Framing keywords are required because this critique appears in the same outlets that otherwise support a firm response.',
 'Eine auf Zurückhaltung bedachte Strömung innerhalb der westlichen und europäischen Presse, die sich sowohl vom abschreckungsfreundlichen Mainstream als auch vom Kreml-Gegenframe unterscheidet, warnt, dass eine Abschussbefugnis gegen mehrdeutige Kontakte einen Zwischenfall riskiert, der unkontrolliert eskaliert, und dass manche gemeldeten Einbrüche -- vom Kurs abgekommene Drohnen, wetterbedingte Radarechos -- unfallbedingt statt gezielt sind. Die Berichterstattung fordert Zurückhaltung, klarere Einsatzregeln und Skepsis gegenüber Worst-Case-Deutungen jedes Vorfalls. Framing-Schlüsselwörter sind nötig, weil diese Kritik in denselben Medien erscheint, die ansonsten eine entschlossene Antwort unterstützen.',
 -1, 'Escalation risk warrants restraint', 'Eskalationsrisiko gebietet Zurückhaltung',
 ARRAY['EUROPE-GERMANY','EUROPE-FRANCE','NON-STATE-EU','EUROPE-NORDIC'],
 ARRAY['Le Monde','El País','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','The Independent','ANSA','La Repubblica','Al Jazeera','Anadolu Agency','Channel NewsAsia'],
 ARRAY['escalation risk','accidental','overblown','restraint','Eskalationsgefahr','versehentlich','überzogen','Zurückhaltung','stray drone','abgekommene Drohne','rules of engagement','Einsatzregeln'],
 true, 3, true)
ON CONFLICT (id) DO UPDATE SET
 name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de, claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de,
 stance=EXCLUDED.stance, stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
 actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers, framing_keywords=EXCLUDED.framing_keywords,
 framing_required=EXCLUDED.framing_required, display_order=EXCLUDED.display_order, is_active=true, updated_at=now();

-- ============================================================
-- Theater roll-up cards (russia_europe_theater) -- spec sec 5.5
-- No fn_anchor bundle, no bootstrap; live roll-up by (sign, publisher).
-- ============================================================

INSERT INTO narratives_v2 (fn_id, id, name_en, name_de, claim_en, claim_de,
  stance, stance_label_en, stance_label_de, actor_centroids, publishers,
  framing_keywords, framing_required, display_order, is_active)
VALUES
('russia_europe_theater', 'russia_europe_western_resolve',
 'Europe must deter, defend and sanction a revanchist Russia',
 'Europa muss ein revisionistisches Russland abschrecken, verteidigen und sanktionieren',
 'The Western consensus across the theater: eastern-flank rearmament, hybrid-threat hardening, airspace enforcement and the sanctions regime are complementary parts of one coherent response to sustained Russian pressure on European security, energy, and information space. Coverage treats deterrence, resilience, and economic pressure as mutually reinforcing rather than separate policy tracks.',
 'Der westliche Konsens über das gesamte Theater hinweg: Aufrüstung der Ostflanke, Härtung gegen hybride Bedrohungen, Luftraumdurchsetzung und Sanktionsregime sind sich ergänzende Teile einer kohärenten Antwort auf anhaltenden russischen Druck auf europäische Sicherheit, Energie und Informationsraum. Die Berichterstattung behandelt Abschreckung, Resilienz und wirtschaftlichen Druck als sich gegenseitig verstärkend statt als getrennte Politikstränge.',
 2, 'Western resolve across the board', 'Westliche Entschlossenheit auf allen Ebenen',
 ARRAY['EUROPE-RUSSIA','NON-STATE-EU','NON-STATE-NATO','EUROPE-BALTIC','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-VISEGRAD','EUROPE-NORDIC','AMERICAS-USA'],
 ARRAY['Reuters','BBC World','Financial Times','Associated Press','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','Wall Street Journal','New York Times','Washington Post','NPR','CNN','ABC News','Military Times','Defense News','ERR News','LRT English','LSM English','Atlantic Council','Politico','Kyiv Post','The Telegraph','The Economist','EurActiv','Bloomberg'],
 ARRAY['deter','defend','sanction','deterrence','resolve','coherent response','Western unity','harden','Entschlossenheit','geschlossene Antwort','Abschreckung'],
 false, 1, true),

('russia_europe_theater', 'russia_europe_kremlin_counter',
 'Western Russophobia, NATO encirclement and self-defeating sanctions manufacture a "Russia threat"',
 'Westliche Russophobie, NATO-Einkreisung und selbstschädigende Sanktionen konstruieren eine "Russland-Bedrohung"',
 'The Russian and Chinese state-media counter-frame across the theater: NATO encirclement, hybrid-threat accusations, airspace-incursion claims and the sanctions regime are all cast as manufactured or self-inflicted -- evidence-free threat inflation, illegitimate seizures, and economic self-harm -- serving a Western political need for a Russian enemy rather than responding to real Russian aggression. This bloc also runs the rift-exploitation register on intra-Western disputes rather than endorsing either side.',
 'Der russische und chinesische Staatsmedien-Gegenframe über das gesamte Theater hinweg: NATO-Einkreisung, Hybrid-Bedrohungsvorwürfe, Luftraum-Einbruch-Behauptungen und das Sanktionsregime werden allesamt als konstruiert oder selbstverschuldet dargestellt -- beweisfreie Bedrohungsinflation, rechtswidrige Beschlagnahmungen und wirtschaftliche Selbstschädigung --, die einem westlichen politischen Bedürfnis nach einem russischen Feindbild dienen, statt auf echte russische Aggression zu reagieren. Dieser Block führt zudem das Rift-Exploitation-Register bei innerwestlichen Streitigkeiten, ohne eine Seite zu unterstützen.',
 -2, 'Kremlin counter-narrative', 'Kreml-Gegenerzählung',
 ARRAY['EUROPE-RUSSIA','EUROPE-BELARUS'],
 ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Izvestia','Kommersant','BelTA','BelTA Russian','Press TV','CGTN','Global Times','China Daily','Xinhua'],
 ARRAY['manufactured threat','Russophobia','NATO encirclement','self-inflicted','evidence-free','political need for an enemy','konstruierte Bedrohung','Russophobie','Einkreisung','selbstverschuldet'],
 false, 2, true),

('russia_europe_theater', 'russia_europe_critical_restraint',
 'Threat inflation, militarisation and escalation risk: a skeptical European counter-current',
 'Bedrohungsinflation, Militarisierung und Eskalationsrisiko: eine skeptische europäische Gegenströmung',
 'A Western-European critical current, distinct from both the Atlanticist mainstream and the Kremlin counter-frame, spans the theater: rearmament and war-economy drift may be overreach, hybrid-threat attribution risks over-securitisation of accidents, and shoot-down authority over ambiguous airspace contacts risks uncontrolled escalation. This is intra-Western critique of proportionality and process, not sympathy for Russian actions.',
 'Eine westeuropäische kritische Strömung, die sich sowohl vom atlantischen Mainstream als auch vom Kreml-Gegenframe unterscheidet, zieht sich durch das gesamte Theater: Aufrüstung und Kriegswirtschafts-Drift könnten Übereifer sein, Hybrid-Bedrohungs-Attribution riskiert Über-Versicherheitlichung von Unfällen, und Abschussbefugnis gegenüber mehrdeutigen Luftraumkontakten riskiert unkontrollierte Eskalation. Dies ist innerwestliche Kritik an Verhältnismäßigkeit und Verfahren, keine Sympathie für russisches Handeln.',
 -1, 'Critical of militarisation and escalation risk', 'Kritisch gegenüber Militarisierung und Eskalationsrisiko',
 ARRAY['EUROPE-GERMANY','EUROPE-FRANCE','NON-STATE-EU','EUROPE-NORDIC'],
 ARRAY['Le Monde','El País','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','The Independent','ANSA','La Repubblica','Al Jazeera','Anadolu Agency','Channel NewsAsia'],
 ARRAY['threat inflation','overreach','over-attribution','escalation risk','disproportionate','restraint','Bedrohungsinflation','Übereifer','Eskalationsgefahr','Zurückhaltung'],
 false, 3, true)
ON CONFLICT (id) DO UPDATE SET
 name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de, claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de,
 stance=EXCLUDED.stance, stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
 actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers, framing_keywords=EXCLUDED.framing_keywords,
 framing_required=EXCLUDED.framing_required, display_order=EXCLUDED.display_order, is_active=true, updated_at=now();

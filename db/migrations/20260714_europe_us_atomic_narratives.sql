-- europe_us_theater atomic narratives (FN_THEATER_BUILD_SPEC §5).
-- Intra-Western theater -> 3-stance / 3-bloc model per atomic, publisher-DISJOINT
-- so publisher alone disambiguates stance (framing_required=false throughout):
--   +2  US-nationalist / America-First      (US-conservative press)
--   -1  Western & European mainstream        (Atlanticist-critical / pro-European)
--   -2  anti-Western rift-exploitation        (Russian + Chinese state media)
-- The -2 bloc is on the WESTERN-COHESION axis (schadenfreude at the rupture,
-- "vassals"/hypocrisy/multipolarity), NOT endorsement of either Western side --
-- the rift-exploitation caveat (§5). No own-goal/friendly-critic split needed:
-- this theater has no corruption/atrocity topic where the supportive camp turns
-- critic. Idempotent: ON CONFLICT (id) DO NOTHING.
SET client_encoding TO 'UTF8';

INSERT INTO narratives_v2
  (id, name_en, name_de, claim_en, claim_de, actor_centroids, framing_keywords,
   is_active, publishers, fn_id, display_order, stance_label_en, stance_label_de,
   stance, framing_required)
VALUES

-- ==================== transatlantic_trade ====================
(
  'trade_us_tariffs_justified',
  'US tariffs are a justified correction of unfair European trade practices',
  'US-Zölle sind eine berechtigte Korrektur unfairer europäischer Handelspraktiken',
  'America-First framing (US conservative press) holds that decades of European trade surpluses, non-tariff barriers, VAT and digital taxes have exploited the United States, and that tariffs are a legitimate, overdue tool to force fair terms and reindustrialise America. Europe is cast as a freeloading partner that must open its market or pay. Vocabulary: unfair, surplus, level playing field, reciprocal, America First, fair deal.',
  'Die America-First-Rahmung (US-konservative Presse) sieht in jahrzehntelangen europäischen Handelsüberschüssen, nichttarifären Barrieren, Mehrwert- und Digitalsteuern eine Ausbeutung der USA und in Zöllen ein legitimes, überfälliges Mittel, um faire Bedingungen zu erzwingen und Amerika zu reindustrialisieren.',
  ARRAY['AMERICAS-USA'],
  ARRAY['unfair','surplus','level playing field','reciprocal','America First','fair deal','non-tariff','freeload','rip off','reindustrial','unfaire','Überschuss'],
  true,
  ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','The Federalist','Daily Caller','Washington Times'],
  'transatlantic_trade', 1,
  'US tariffs justified (America First)',
  'US-Zölle gerechtfertigt (America First)',
  2, false
),
(
  'trade_european_defence',
  'Trump''s tariffs are economic coercion that Europe must resist with unity and countermeasures',
  'Trumps Zölle sind wirtschaftlicher Zwang, dem Europa mit Einigkeit und Gegenmaßnahmen begegnen muss',
  'Western mainstream framing treats US tariffs as damaging economic coercion against a vital ally, threatening a mutually destructive trade war, and argues Europe must respond with unity, credible counter-tariffs and a negotiated deal that protects its industries and interests. Alarm at the rupture of a decades-old partnership runs throughout. Vocabulary: coercion, trade war, retaliate, counter-tariff, unity, escalation, negotiated deal, damage.',
  'Der westliche Mainstream deutet die US-Zölle als schädlichen wirtschaftlichen Zwang gegen einen wichtigen Verbündeten, der einen zerstörerischen Handelskrieg droht, und fordert von Europa Einigkeit, glaubwürdige Gegenzölle und ein Verhandlungsergebnis, das seine Industrie und Interessen schützt.',
  ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','AMERICAS-USA'],
  ARRAY['coercion','trade war','retaliate','counter-tariff','unity','escalation','negotiated','damage','defend','Zwang','Handelskrieg','Gegenzoll','Einigkeit'],
  true,
  ARRAY['Reuters','Associated Press','BBC World','Financial Times','Wall Street Journal','New York Times','Washington Post','CNN','ABC News','NPR','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','El País','Le Monde','ANSA','EurActiv','Politico','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Bloomberg','CNBC','Channel NewsAsia','The Independent','Helsinki Times','eKathimerini'],
  'transatlantic_trade', 2,
  'European defence against US coercion',
  'Europäische Abwehr gegen US-Zwang',
  -1, false
),
(
  'trade_western_vassalage',
  'US tariffs expose how Washington milks its European "vassals" and the hollowness of the alliance',
  'US-Zölle zeigen, wie Washington seine europäischen „Vasallen" ausnimmt und wie hohl das Bündnis ist',
  'Rift-exploitation framing (Russian and Chinese state media) presents the tariff war not by taking Europe''s or Washington''s side but as proof that the US treats its "allies" as vassals to be milked, that European submission is humiliating, and that the transatlantic economic bond is fracturing to the benefit of a multipolar world. Schadenfreude at Western disunity, not endorsement of either side. Vocabulary: vassal, milk, humiliation, submission, hypocrisy, extortion, multipolar, decline of the West.',
  'Die Riss-Ausnutzungs-Rahmung (russische und chinesische Staatsmedien) ergreift weder für Europa noch für Washington Partei, sondern deutet den Zollkrieg als Beweis, dass die USA ihre „Verbündeten" wie auszunehmende Vasallen behandeln, die europäische Unterwerfung demütigend ist und das transatlantische Wirtschaftsband zugunsten einer multipolaren Welt zerbricht.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['vassal','milk','humiliation','submission','hypocrisy','extortion','multipolar','decline of the West','servant','diktat','Vasall','Demütigung','Erpressung'],
  true,
  ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','Press TV','CGTN','Global Times','China Daily','Xinhua'],
  'transatlantic_trade', 3,
  'Anti-Western rift-exploitation',
  'Anti-westliche Riss-Ausnutzung',
  -2, false
),

-- ==================== europe_us_defence_dependence ====================
(
  'defence_europe_must_pay',
  'Europe has freeloaded on US protection for decades and must finally pay its share',
  'Europa hat sich jahrzehntelang auf US-Schutz verlassen und muss endlich seinen Anteil zahlen',
  'America-First framing (US conservative press) holds that European allies have underspent on defence for decades while sheltering under the US umbrella, and that Washington is right to demand they hit higher NATO spending targets or forfeit American protection. Troop drawdowns and blunt pressure are framed as overdue accountability. Vocabulary: freeload, fair share, pay up, 5 percent, deadbeat, burden, or else.',
  'Die America-First-Rahmung (US-konservative Presse) sieht in den europäischen Verbündeten jahrzehntelange Trittbrettfahrer unter dem US-Schirm und hält es für richtig, dass Washington höhere NATO-Ausgabenziele fordert -- oder den amerikanischen Schutz entzieht. Truppenabzüge und harter Druck gelten als überfällige Rechenschaft.',
  ARRAY['AMERICAS-USA'],
  ARRAY['freeload','fair share','pay up','5 percent','deadbeat','burden','or else','delinquent','pull out','Trittbrettfahrer','fairer Anteil'],
  true,
  ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','The Federalist','Daily Caller','Washington Times'],
  'europe_us_defence_dependence', 1,
  'Europe must pay its share',
  'Europa muss seinen Anteil zahlen',
  2, false
),
(
  'defence_unreliable_america',
  'A wavering America is an unreliable protector, forcing an alarmed Europe to scramble',
  'Ein schwankendes Amerika ist ein unzuverlässiger Beschützer und zwingt ein alarmiertes Europa zum Handeln',
  'Western mainstream framing treats the fraying US security guarantee -- troop drawdowns, doubts over Article 5, transactional pressure -- as a strategic shock that leaves Europe dangerously exposed. Allies scramble to reassure Washington and raise spending to keep it engaged, while asking whether America will still come to their defence. Vocabulary: unreliable, abandon, exposed, reassure, Article 5, credibility, nervous, scramble.',
  'Der westliche Mainstream deutet die bröckelnde US-Sicherheitsgarantie -- Truppenabzüge, Zweifel an Artikel 5, transaktionalen Druck -- als strategischen Schock, der Europa gefährlich entblößt. Die Verbündeten bemühen sich, Washington zu beschwichtigen und die Ausgaben zu erhöhen, und fragen zugleich, ob Amerika noch zu ihrer Verteidigung käme.',
  ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','AMERICAS-USA'],
  ARRAY['unreliable','abandon','exposed','reassure','Article 5','credibility','nervous','scramble','guarantee','umbrella','unzuverlässig','Abzug','Artikel 5'],
  true,
  ARRAY['Reuters','Associated Press','BBC World','Financial Times','Wall Street Journal','New York Times','Washington Post','CNN','ABC News','NPR','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','El País','Le Monde','ANSA','EurActiv','Politico','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Bloomberg','CNBC','Channel NewsAsia','The Independent','LRT English','ERR News','eKathimerini'],
  'europe_us_defence_dependence', 2,
  'America the unreliable protector',
  'Amerika als unzuverlässiger Beschützer',
  -1, false
),
(
  'defence_nato_racket',
  'NATO is a crumbling Cold-War racket through which the US bleeds Europe',
  'Die NATO ist ein zerfallendes Relikt des Kalten Krieges, mit dem die USA Europa ausbluten',
  'Rift-exploitation framing (Russian and Chinese state media) casts the burden-sharing rows as proof that NATO is an obsolete Cold-War racket: Washington extracts money and arms sales from dependent Europeans while the alliance''s internal quarrels reveal its decay. Adversarial to the alliance as a whole, amplified with schadenfreude, not support for either party. Vocabulary: racket, obsolete, Cold War relic, extort, arms sales, decay, disunity, crumbling.',
  'Die Riss-Ausnutzungs-Rahmung (russische und chinesische Staatsmedien) stellt die Lastenstreitigkeiten als Beweis dar, dass die NATO ein überholtes Relikt des Kalten Krieges sei: Washington presse Geld und Waffenkäufe aus abhängigen Europäern heraus, während die internen Querelen den Verfall des Bündnisses offenbarten.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['racket','obsolete','Cold War relic','extort','arms sales','decay','disunity','crumbling','vassal','proxy','Relikt','ausbluten','überholt'],
  true,
  ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','Press TV','CGTN','Global Times','China Daily','Xinhua'],
  'europe_us_defence_dependence', 3,
  'Anti-Western rift-exploitation',
  'Anti-westliche Riss-Ausnutzung',
  -2, false
),

-- ==================== eu_strategic_autonomy ====================
(
  'autonomy_illusion',
  'European strategic autonomy is a costly fantasy that only weakens NATO',
  'Europäische strategische Autonomie ist eine teure Fantasie, die nur die NATO schwächt',
  'Skeptical framing (US conservative and Atlanticist-hawk press) mocks "strategic autonomy" and the "EU army" as a bureaucratic fantasy: Europe cannot defend itself, duplicates NATO, and should simply spend more inside the alliance rather than build rival structures that divide the West. Vocabulary: fantasy, pipe dream, duplication, cannot defend, paper army, undermine NATO, talk not troops.',
  'Die skeptische Rahmung (US-konservative und atlantisch-restriktive Presse) verspottet „strategische Autonomie" und die „EU-Armee" als bürokratische Fantasie: Europa könne sich nicht selbst verteidigen, dupliziere die NATO und solle lieber innerhalb des Bündnisses mehr ausgeben, statt rivalisierende Strukturen aufzubauen, die den Westen spalten.',
  ARRAY['AMERICAS-USA'],
  ARRAY['fantasy','pipe dream','duplication','cannot defend','paper army','undermine NATO','illusion','talk not troops','Fantasie','Illusion','Papierarmee'],
  true,
  ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','The Federalist','Daily Caller','Washington Times'],
  'eu_strategic_autonomy', 1,
  'Autonomy is an illusion',
  'Autonomie ist eine Illusion',
  2, false
),
(
  'autonomy_european_awakening',
  'Europe is finally awakening to strategic autonomy and must build its own defence',
  'Europa erwacht endlich zur strategischen Autonomie und muss seine eigene Verteidigung aufbauen',
  'Western mainstream framing treats the US retreat as the catalyst for a historic European awakening: the continent must build genuine strategic autonomy -- a defence union, industrial base, even a European deterrent -- through initiatives like ReArm Europe, to decide and defend for itself and de-risk from dependence on Washington. Broadly sympathetic to the project while debating its feasibility. Vocabulary: awakening, strategic autonomy, defence union, ReArm, sovereignty, self-reliance, wake-up call, emancipate.',
  'Der westliche Mainstream deutet den US-Rückzug als Katalysator für ein historisches europäisches Erwachen: Der Kontinent müsse echte strategische Autonomie aufbauen -- eine Verteidigungsunion, eine industrielle Basis, sogar eine europäische Abschreckung -- über Initiativen wie ReArm Europe, um selbst zu entscheiden und sich zu verteidigen.',
  ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','AMERICAS-USA'],
  ARRAY['awakening','strategic autonomy','defence union','ReArm','sovereignty','self-reliance','wake-up call','emancipate','rearm','deterrent','Erwachen','Autonomie','Verteidigungsunion'],
  true,
  ARRAY['Reuters','Associated Press','BBC World','Financial Times','Wall Street Journal','New York Times','Washington Post','CNN','ABC News','NPR','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','El País','Le Monde','ANSA','EurActiv','Politico','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Bloomberg','CNBC','Channel NewsAsia','The Independent','LRT English','ERR News','eKathimerini'],
  'eu_strategic_autonomy', 2,
  'European strategic awakening',
  'Europäisches strategisches Erwachen',
  -1, false
),
(
  'autonomy_multipolar_welcome',
  'European autonomy means the end of US hegemony and a welcome multipolar world',
  'Europäische Autonomie bedeutet das Ende der US-Hegemonie und eine willkommene multipolare Welt',
  'Rift-exploitation framing (Russian and Chinese state media) welcomes European "strategic autonomy" not out of solidarity but as the fracturing of the US-led bloc: proof that American hegemony is ending, that Europe should break free of its Atlantic vassalage, and that a multipolar order is arriving. It cheers the transatlantic split while doubting Europe will dare follow through. Vocabulary: multipolar, end of hegemony, vassalage, break free, Atlanticism dead, sovereignty, emancipation.',
  'Die Riss-Ausnutzungs-Rahmung (russische und chinesische Staatsmedien) begrüßt die europäische „strategische Autonomie" nicht aus Solidarität, sondern als Zerfall des US-geführten Blocks: als Beweis, dass die amerikanische Hegemonie ende, Europa sich aus atlantischer Vasallität lösen solle und eine multipolare Ordnung heraufziehe.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['multipolar','end of hegemony','vassalage','break free','Atlanticism','emancipation','sovereignty','declining America','Hegemonie','multipolar','Vasallität'],
  true,
  ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','Press TV','CGTN','Global Times','China Daily','Xinhua'],
  'eu_strategic_autonomy', 3,
  'Multipolar rift-exploitation',
  'Multipolare Riss-Ausnutzung',
  -2, false
),

-- ==================== europe_us_tech_sovereignty ====================
(
  'tech_eu_overreach',
  'EU tech rules are protectionist harassment of successful American companies',
  'Die EU-Techregeln sind protektionistische Schikane erfolgreicher amerikanischer Unternehmen',
  'America-First framing (US conservative press) casts the DMA, DSA and antitrust fines as protectionist, anti-innovation harassment designed to shake down US technology champions and censor American speech, justifying tariff retaliation to defend them. Vocabulary: shakedown, protectionist, harassment, censorship, anti-innovation, discriminatory, retaliate, defend our companies.',
  'Die America-First-Rahmung (US-konservative Presse) deutet DMA, DSA und Kartellstrafen als protektionistische, innovationsfeindliche Schikane, die US-Techkonzerne abkassieren und amerikanische Meinungsäußerung zensieren solle -- und rechtfertigt Zoll-Vergeltung zu ihrer Verteidigung.',
  ARRAY['AMERICAS-USA'],
  ARRAY['shakedown','protectionist','harassment','censorship','anti-innovation','discriminatory','retaliate','defend our','targeting American','Schikane','Zensur','abkassieren'],
  true,
  ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','The Federalist','Daily Caller','Washington Times'],
  'europe_us_tech_sovereignty', 1,
  'EU regulatory overreach',
  'EU-Regulierungsübergriff',
  2, false
),
(
  'tech_digital_sovereignty',
  'Europe must rein in US Big Tech and reclaim its digital sovereignty',
  'Europa muss die US-Techkonzerne bändigen und seine digitale Souveränität zurückgewinnen',
  'Western and European mainstream framing treats EU enforcement against US Big Tech -- DMA/DSA fines, antitrust probes, content and privacy rules -- as legitimate rule-of-law that Europe must uphold, and pairs it with a drive for digital sovereignty: sovereign cloud, Gaia-X and weaning public and defence systems off American providers. Vocabulary: digital sovereignty, rein in, enforce, rule of law, sovereign cloud, dependence, gatekeeper, level playing field.',
  'Der westliche und europäische Mainstream sieht in der EU-Durchsetzung gegen die US-Techkonzerne -- DMA/DSA-Strafen, Kartellverfahren, Inhalts- und Datenschutzregeln -- legitime Rechtsstaatlichkeit, die Europa wahren müsse, und verbindet sie mit dem Streben nach digitaler Souveränität: souveräne Cloud, Gaia-X und die Loslösung öffentlicher und militärischer Systeme von amerikanischen Anbietern.',
  ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','AMERICAS-USA'],
  ARRAY['digital sovereignty','rein in','enforce','rule of law','sovereign cloud','dependence','gatekeeper','level playing field','regulate','Big Tech','digitale Souveränität','Kartell'],
  true,
  ARRAY['Reuters','Associated Press','BBC World','Financial Times','Wall Street Journal','New York Times','Washington Post','CNN','ABC News','NPR','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','El País','Le Monde','ANSA','EurActiv','Politico','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Bloomberg','CNBC','Channel NewsAsia','The Independent','Ars Technica','TechCrunch'],
  'europe_us_tech_sovereignty', 2,
  'European digital sovereignty',
  'Europäische digitale Souveränität',
  -1, false
),
(
  'tech_digital_colonialism',
  'US tech dominance is a digital colonialism Europe is only now waking up to',
  'Die US-Techdominanz ist ein digitaler Kolonialismus, aus dem Europa erst jetzt erwacht',
  'Rift-exploitation framing (Russian and Chinese state media) casts American technological dominance over Europe as digital colonialism and mass surveillance, presenting the EU-US tech clash as belated European recognition of its subjugation to Silicon Valley -- while stressing Washington''s hypocrisy on "free" markets. Adversarial to US tech hegemony, not an endorsement of EU regulation as such. Vocabulary: digital colonialism, surveillance, hegemony, subjugation, hypocrisy, control, dependence, monopoly.',
  'Die Riss-Ausnutzungs-Rahmung (russische und chinesische Staatsmedien) deutet die amerikanische Technologiedominanz über Europa als digitalen Kolonialismus und Massenüberwachung und stellt den EU-US-Techkonflikt als verspätetes europäisches Erkennen seiner Unterwerfung unter das Silicon Valley dar -- unter Betonung der Heuchelei Washingtons in Sachen „freier" Märkte.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['digital colonialism','surveillance','hegemony','subjugation','hypocrisy','control','dependence','monopoly','Silicon Valley','Kolonialismus','Überwachung','Hegemonie'],
  true,
  ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','Press TV','CGTN','Global Times','China Daily','Xinhua'],
  'europe_us_tech_sovereignty', 3,
  'Anti-Western rift-exploitation',
  'Anti-westliche Riss-Ausnutzung',
  -2, false
)

ON CONFLICT (id) DO NOTHING;

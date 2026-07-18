-- Korea theater: atomic narratives (greenfield, 2026-07-16).
--
-- Publisher-coalition design, grounded in what each bloc ACTUALLY publishes in
-- this corpus rather than in its assumed alignment. Two findings shaped it:
--
-- 1. The Russian/Chinese bloc is NOT stance-saturated on the DPRK weapons
--    programme. Its Korea coverage is overwhelmingly neutral wire copy --
--    "КНДР запустила порядка 10 баллистических ракет", CGTN quoting US
--    Indo-Pacific Command verbatim, TASS (EN) reporting Seoul and Tokyo
--    reaffirming their denuclearisation commitment. Advocacy exists but is
--    thin. So nk_sovereign_deterrent is framing_required=true: without it, every
--    neutral TASS launch report would be filed as "Russia endorses the DPRK
--    arsenal", which is false. Same pattern as greenland_us_strategic_claim.
--
-- 2. There is no "US drills are a provocation" bloc. Across 180d the RU/CN
--    outlets produce 7 drill-related Korea titles, nearly all neutral ("US
--    begins large military exercise with South Korea - reports"). The only
--    stance-bearing line is Global Times', and it is a different claim:
--    Washington instrumentalises allies to contain China. That is what
--    alliance_containment_instrument says -- the honest label, not the
--    assumed one.
--
-- Own-goal / shared-coalition handling (spec section 5): korea_peninsula_deterrence
-- and inter_korean_relations both have stances that live INSIDE the same
-- Western/ROK coalition (alliance-necessary vs ROK-autonomy; engagement vs
-- Pyongyang-has-closed-the-door). Publisher alone cannot separate those, so
-- those narratives are framing_required=true with disjoint keywords. Titles
-- matching neither framing are dropped -- precision over recall.

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. north_korea_missile_program
-- ---------------------------------------------------------------------------

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, framing_required,
    actor_centroids, publishers, framing_keywords, display_order
) VALUES (
'nk_sovereign_deterrent', 'north_korea_missile_program',
'The arsenal is a sovereign deterrent that will not be traded away',
'Das Arsenal ist ein souveränes Abschreckungsmittel, das nicht verhandelbar ist',
'Sovereign-deterrent framing (Russian and Chinese state press, carrying Pyongyang''s own position) presents the nuclear and missile programme as a lawful instrument of self-defence and a settled fact: the DPRK has declared itself a nuclear state, says it will never give up that status, and treats denuclearisation demands as closed. US-led containment is described as having failed. Note this is a thin seam within the bloc''s Korea coverage, which is mostly neutral launch reporting -- hence framing-gated. Vocabulary: nuclear status, never give up, self-defence, sovereign right, geometric progression, no compromise, containment failed.',
'Die Rahmung als souveräne Abschreckung (russische und chinesische Staatspresse, die Pjöngjangs eigene Position transportiert) stellt das Nuklear- und Raketenprogramm als rechtmäßiges Mittel der Selbstverteidigung und als vollendete Tatsache dar: Die DVRK hat sich zum Atomstaat erklärt, erklärt, diesen Status niemals aufzugeben, und betrachtet Forderungen nach Denuklearisierung als erledigt. Die von den USA geführte Eindämmung wird als gescheitert beschrieben. Dies ist ein schmaler Strang innerhalb der Korea-Berichterstattung des Blocks, die überwiegend aus neutraler Berichterstattung über Raketenstarts besteht -- daher die Rahmungsbindung.',
2, 'Sovereign deterrent, not negotiable', 'Souveräne Abschreckung, nicht verhandelbar', true,
ARRAY['ASIA-NORKOREA'],
ARRAY['TASS','TASS (EN)','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','CGTN','China Daily','Global Times','People''s Daily'],
ARRAY['nuclear status','nuclear state','nuclear power status','never give up','never abandon','will never','no compromise','refuses to','refused to','self-defence','self-defense','sovereign right','geometric progression','nuclear buildup','nuclear build-up','nuclear push','failed','ядерный статус','ядерного статуса','никогда не откажется','не откажется','геометрической прогрессии','наращивании ядерных','наращивание ядерного','отказались идти на компромисс','отказались от компромисса','провалились','核保有','自卫','自衛'],
1),

('nk_proliferation_threat', 'north_korea_missile_program',
'An expanding arsenal that must be contained',
'Ein wachsendes Arsenal, das eingedämmt werden muss',
'Threat framing (Western, South Korean and Japanese mainstream plus defence-analytic outlets) treats the programme as a growing danger to the region and to the United States: ballistic launches timed against allied exercises, expanding uranium-enrichment capacity, warhead numbers, hypersonic and AI-guided systems, and the erosion of the sanctions regime. The prescription is denuclearisation through pressure, interception capability and allied coordination. Vocabulary: threat, provocation, launch, sanctions, denuclearisation, enrichment capacity, buildup, escalation.',
'Die Bedrohungsrahmung (westliche, südkoreanische und japanische Leitmedien sowie verteidigungsanalytische Fachmedien) behandelt das Programm als wachsende Gefahr für die Region und die Vereinigten Staaten: ballistische Starts mit zeitlichem Bezug zu Manövern der Verbündeten, wachsende Urananreicherungskapazität, Sprengkopfzahlen, Hyperschall- und KI-gesteuerte Systeme sowie die Erosion des Sanktionsregimes. Die Schlussfolgerung lautet Denuklearisierung durch Druck, Abfangfähigkeit und Abstimmung der Verbündeten.',
-2, 'Proliferation threat requiring containment', 'Proliferationsbedrohung, die Eindämmung erfordert', false,
ARRAY['AMERICAS-USA','ASIA-SOUTHKOREA','ASIA-JAPAN'],
ARRAY['Reuters','BBC World','Associated Press','AFP','The Guardian','Deutsche Welle','DW.com','CNN','France 24 (EN)','France 24','Euronews','Financial Times','Bloomberg','Bloomberg.com','New York Times','Washington Post','Wall Street Journal','WSJ','The Telegraph','Der Spiegel','Süddeutsche Zeitung','Le Monde','El País','El Mundo','The Economist','Sky News','NPR','ABC News','MSNBC','Channel NewsAsia','CNA','Straits Times','The Straits Times','Fox News','Yonhap','Yonhap News Agency','KBS World','KBS WORLD Radio','Korea Herald','The Korea Herald','NHK World','nhk.or.jp','Asahi Shimbun','Kyodo News','Japan Wire by KYODO NEWS','Japan Times','Nikkei Asia','CSIS','Brookings','RAND','Atlantic Council','Council on Foreign Relations','IISS','Janes','Defense News','Military Times','War on the Rocks','Beyond Parallel','Carnegie Endowment'],
ARRAY['threat','provocation','escalat','sanctions','denuclear','enrichment','warhead','buildup','build-up','Bedrohung','Provokation','Sanktionen','Anreicherung'],
2);

-- ---------------------------------------------------------------------------
-- 2. north_korea_china_patronage
-- ---------------------------------------------------------------------------

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, framing_required,
    actor_centroids, publishers, framing_keywords, display_order
) VALUES
('china_dprk_friendship', 'north_korea_china_patronage',
'Traditional friendship restored, to the benefit of regional stability',
'Wiederhergestellte traditionelle Freundschaft im Dienst regionaler Stabilität',
'Friendship framing (Chinese state media) presents the re-engagement -- Xi''s state visit, the Wang Yi mission, resumed Beijing-Pyongyang flights and rail, tributes at the Chinese People''s Volunteers cemeteries -- as the restoration of a historic bond entering a "new era", and as a contribution to peace and stability on the peninsula rather than an evasion of sanctions. Vocabulary: traditional friendship, new era, deepen cooperation, practical cooperation, steadfast, mutual development, peace and stability.',
'Die Freundschaftsrahmung (chinesische Staatsmedien) stellt die Wiederannäherung -- Xis Staatsbesuch, die Mission von Wang Yi, wieder aufgenommene Flüge und Bahnverbindungen zwischen Peking und Pjöngjang, Ehrungen auf den Friedhöfen der chinesischen Volksfreiwilligen -- als Wiederherstellung einer historischen Bindung dar, die in eine "neue Ära" eintritt, und als Beitrag zu Frieden und Stabilität auf der Halbinsel statt als Umgehung von Sanktionen.',
2, 'Friendship and regional stability', 'Freundschaft und regionale Stabilität', false,
ARRAY['ASIA-CHINA','ASIA-NORKOREA'],
ARRAY['CGTN','China Daily','Global Times','People''s Daily'],
ARRAY['friendship','new era','deepen','practical cooperation','steadfast','mutual','peace and stability','Freundschaft','neue Ära'],
1),

('beijing_shields_pyongyang', 'north_korea_china_patronage',
'Beijing''s lifeline is what keeps the pressure regime from working',
'Pekings Lebensader verhindert, dass das Druckregime wirkt',
'Patronage-critique framing (Western, South Korean and Japanese mainstream) reads the same re-engagement as the decisive hole in the sanctions regime: China keeps the North Korean economy alive, declines to press Kim on the nuclear programme even when asked to, and rebuilds leverage over Pyongyang as a card in its own competition with Washington. The restored flights, rail link and trade are read as sanctions erosion rather than neighbourliness. Vocabulary: lifeline, keeps the economy alive, declines to press, shields, leverage, grip, sanctions erosion, evasion.',
'Die Patronage-Kritik (westliche, südkoreanische und japanische Leitmedien) liest dieselbe Wiederannäherung als entscheidende Lücke im Sanktionsregime: China hält die nordkoreanische Wirtschaft am Leben, verzichtet selbst auf Nachfrage darauf, Kim zum Nuklearprogramm zu drängen, und baut Einfluss auf Pjöngjang als Karte im eigenen Wettbewerb mit Washington auf. Die wieder aufgenommenen Flüge, die Bahnverbindung und der Handel gelten als Erosion der Sanktionen statt als gute Nachbarschaft.',
-2, 'Beijing shields Pyongyang from pressure', 'Peking schirmt Pjöngjang gegen Druck ab', false,
ARRAY['AMERICAS-USA','ASIA-SOUTHKOREA','ASIA-JAPAN'],
ARRAY['Reuters','BBC World','Associated Press','AFP','The Guardian','Deutsche Welle','DW.com','CNN','France 24 (EN)','France 24','Euronews','Financial Times','Bloomberg','Bloomberg.com','New York Times','Washington Post','Wall Street Journal','WSJ','The Telegraph','Der Spiegel','Süddeutsche Zeitung','Le Monde','El País','El Mundo','The Economist','Sky News','NPR','ABC News','MSNBC','Channel NewsAsia','CNA','Straits Times','The Straits Times','Al Jazeera','Fox News','Yonhap','Yonhap News Agency','KBS World','KBS WORLD Radio','Korea Herald','The Korea Herald','NHK World','nhk.or.jp','Asahi Shimbun','Kyodo News','Japan Wire by KYODO NEWS','Japan Times','Nikkei Asia','CSIS','Brookings','RAND','Atlantic Council','Council on Foreign Relations','IISS','Janes','Beyond Parallel','Carnegie Endowment','The Australian'],
ARRAY['lifeline','alive','grip','leverage','shield','influence','pressure','evasion','rare visit','confidence','defiance','Einfluss','Druck'],
2);

-- ---------------------------------------------------------------------------
-- 3. north_korea_russia_alignment
-- ---------------------------------------------------------------------------

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, framing_required,
    actor_centroids, publishers, framing_keywords, display_order
) VALUES
('dprk_russia_comradeship', 'north_korea_russia_alignment',
'A lawful partnership between states under the same sanctions',
'Eine rechtmäßige Partnerschaft zwischen Staaten unter denselben Sanktionen',
'Partnership framing (Russian and Belarusian state press) presents the alignment as an ordinary and lawful relationship between sovereign states: treaty-based military cooperation, ministerial and parliamentary visits, a new border bridge, Lukashenko''s first visit to Pyongyang, and honours for North Korean soldiers who fought in Kursk. The deployment is framed as allied assistance in liberating Russian territory and the soldiers as heroes, not as a transaction. Vocabulary: strategic partnership, treaty, cooperation, allies, top priority, heroes, liberation of Kursk, friendship.',
'Die Partnerschaftsrahmung (russische und belarussische Staatspresse) stellt die Ausrichtung als gewöhnliche und rechtmäßige Beziehung zwischen souveränen Staaten dar: vertraglich geregelte militärische Zusammenarbeit, Besuche von Ministern und Parlamentariern, eine neue Grenzbrücke, Lukaschenkos erster Besuch in Pjöngjang und Ehrungen für nordkoreanische Soldaten, die in Kursk kämpften. Der Truppeneinsatz erscheint als Beistand von Verbündeten bei der Befreiung russischen Gebiets und die Soldaten als Helden, nicht als Gegenleistung.',
2, 'Lawful partnership of sanctioned states', 'Rechtmäßige Partnerschaft sanktionierter Staaten', false,
ARRAY['EUROPE-RUSSIA','ASIA-NORKOREA','EUROPE-BELARUS'],
ARRAY['TASS','TASS (EN)','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','BelTA Russian'],
ARRAY['partnership','cooperation','treaty','allies','ally','top priority','heroes','friendship','visit','Партнёрств','сотрудничеств','договор','союзник','героя','дружб'],
1),

('dprk_russia_blood_for_technology', 'north_korea_russia_alignment',
'Troops and shells for cash and missile technology',
'Truppen und Granaten gegen Geld und Raketentechnologie',
'Transaction framing (Western, South Korean, Japanese and Ukrainian outlets) reads the alignment as an arms-for-technology bargain that damages both theatres at once: North Korea supplies troops, shells and missiles to sustain Russia''s war and is estimated to have earned billions doing so, while Russia is suspected of paying in the military and space technology that accelerates the DPRK programme. Coverage foregrounds the human cost -- casualties in Kursk, prisoners of war, the "self-blasting" policy praised by Kim -- and the proliferation quid pro quo. Vocabulary: arms transfer, troops for cash, quid pro quo, technology transfer, casualties, prisoners of war, sanctions evasion.',
'Die Transaktionsrahmung (westliche, südkoreanische, japanische und ukrainische Medien) liest die Ausrichtung als Waffen-gegen-Technologie-Geschäft, das beide Schauplätze zugleich beschädigt: Nordkorea liefert Truppen, Granaten und Raketen zur Aufrechterhaltung des russischen Krieges und soll damit Milliarden verdient haben, während Russland im Verdacht steht, mit Militär- und Raumfahrttechnologie zu bezahlen, die das Programm der DVRK beschleunigt. Im Vordergrund stehen die menschlichen Kosten -- Verluste bei Kursk, Kriegsgefangene, die von Kim gelobte Praxis der Selbstsprengung -- und die Gegenleistung bei der Proliferation.',
-2, 'Blood-for-technology transaction', 'Blut-gegen-Technologie-Geschäft', false,
ARRAY['AMERICAS-USA','ASIA-SOUTHKOREA','EUROPE-UKRAINE','ASIA-JAPAN'],
ARRAY['Reuters','BBC World','Associated Press','AFP','The Guardian','Deutsche Welle','DW.com','CNN','France 24 (EN)','France 24','Euronews','Financial Times','Bloomberg','Bloomberg.com','New York Times','Washington Post','Wall Street Journal','WSJ','The Telegraph','Der Spiegel','Süddeutsche Zeitung','Le Monde','El País','El Mundo','The Economist','Sky News','NPR','ABC News','MSNBC','Channel NewsAsia','CNA','Straits Times','The Straits Times','Al Jazeera','Fox News','Kyiv Post','Yonhap','Yonhap News Agency','KBS World','KBS WORLD Radio','Korea Herald','The Korea Herald','NHK World','nhk.or.jp','Asahi Shimbun','Kyodo News','Japan Wire by KYODO NEWS','Japan Times','Nikkei Asia','CSIS','Brookings','RAND','Atlantic Council','Council on Foreign Relations','IISS','Janes','Defense News','Beyond Parallel','Carnegie Endowment','Anadolu Agency','UN News'],
ARRAY['troops','soldier','arms','shells','munition','earned','cash','technology','quid pro quo','casualt','prisoner','POW','killed','Truppen','Soldaten','Waffen','Technologie'],
2);

-- ---------------------------------------------------------------------------
-- 4. korea_peninsula_deterrence
--    Own-goal shape: the +2 and the -1 share the Western/ROK coalition, so both
--    are framing-gated with disjoint keywords (spec section 5).
-- ---------------------------------------------------------------------------

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, framing_required,
    actor_centroids, publishers, framing_keywords, display_order
) VALUES
('alliance_deterrence_necessary', 'korea_peninsula_deterrence',
'The alliance and its exercises are what hold deterrence together',
'Das Bündnis und seine Übungen sind das Fundament der Abschreckung',
'Deterrence framing (US and South Korean official and mainstream coverage plus defence-analytic outlets) holds that the combined force posture -- Freedom Shield and Ulchi exercises, US Forces Korea, extended deterrence and the Nuclear Consultative Group -- is what deters a nuclear-armed North and reassures Seoul and Tokyo. Reaffirmations of the US commitment, exercise readiness and alliance modernisation are treated as stabilising. Vocabulary: extended deterrence, reaffirm commitment, readiness, combined defence, alliance modernisation, reassurance.',
'Die Abschreckungsrahmung (offizielle und Mainstream-Berichterstattung aus den USA und Südkorea sowie verteidigungsanalytische Fachmedien) hält die gemeinsame Streitkräfteaufstellung -- die Übungen Freedom Shield und Ulchi, die US-Streitkräfte in Korea, die erweiterte Abschreckung und die Nukleare Konsultativgruppe -- für das, was einen atomar bewaffneten Norden abschreckt und Seoul und Tokio rückversichert. Bekräftigungen der US-Zusage, Übungsbereitschaft und die Modernisierung des Bündnisses gelten als stabilisierend.',
2, 'Deterrence posture is necessary', 'Abschreckungsdispositiv ist notwendig', true,
ARRAY['AMERICAS-USA','ASIA-SOUTHKOREA'],
ARRAY['Reuters','BBC World','Associated Press','AFP','The Guardian','Deutsche Welle','DW.com','CNN','France 24 (EN)','Euronews','Financial Times','Bloomberg','New York Times','Washington Post','Wall Street Journal','WSJ','The Telegraph','Sky News','NPR','ABC News','Channel NewsAsia','CNA','Straits Times','The Straits Times','Fox News','Yonhap','Yonhap News Agency','KBS World','KBS WORLD Radio','Korea Herald','The Korea Herald','NHK World','nhk.or.jp','Asahi Shimbun','Kyodo News','Japan Times','Nikkei Asia','CSIS','Brookings','RAND','Atlantic Council','Council on Foreign Relations','IISS','Janes','Defense News','Military Times','War on the Rocks','Beyond Parallel','Carnegie Endowment'],
ARRAY['extended deterrence','reaffirm','commitment','deterrence','readiness','combined','joint drill','military exercise','Freedom Shield','Ulchi','milestone','strengthen','bolster','RIMPAC','Abschreckung','Bekräftig'],
1),

('alliance_autonomy_strain', 'korea_peninsula_deterrence',
'Seoul is pushing for autonomy and the alliance terms are being renegotiated',
'Seoul drängt auf Eigenständigkeit und die Bündnisbedingungen werden neu verhandelt',
'Autonomy framing (South Korean and Western coverage of the same alliance) treats the relationship as under renegotiation rather than settled: the transfer of wartime operational control, Seoul''s push for a "self-reliant" defence and indigenous nuclear-powered submarines, defence cost-sharing, US commanders'' remarks that land badly in Seoul, and questions raised during the South Korean election about the terms of the alliance. It is not opposition to the alliance but pressure on its distribution of control. Distinct from the Chinese framing, which is about US intentions rather than Korean agency. Vocabulary: OPCON transfer, self-reliant defence, cost-sharing, rift, strain, questions, conditions-based, sovereignty.',
'Die Eigenständigkeitsrahmung (südkoreanische und westliche Berichterstattung über dasselbe Bündnis) behandelt das Verhältnis als neu verhandelbar statt als feststehend: die Übertragung der Operationskontrolle im Kriegsfall, Seouls Streben nach einer "eigenständigen" Verteidigung und nach eigenen atomgetriebenen U-Booten, die Teilung der Verteidigungskosten, Äußerungen von US-Kommandeuren, die in Seoul schlecht ankommen, und Fragen zu den Bündnisbedingungen im südkoreanischen Wahlkampf. Es ist keine Ablehnung des Bündnisses, sondern Druck auf die Verteilung der Kontrolle darin.',
-1, 'ROK autonomy and alliance strain', 'Eigenständigkeit Südkoreas und Bündnisbelastung', true,
ARRAY['ASIA-SOUTHKOREA'],
ARRAY['Reuters','BBC World','Associated Press','AFP','The Guardian','Deutsche Welle','DW.com','CNN','France 24 (EN)','Euronews','Financial Times','Bloomberg','New York Times','Washington Post','Wall Street Journal','WSJ','The Telegraph','Sky News','NPR','ABC News','Channel NewsAsia','CNA','Straits Times','The Straits Times','Fox News','Yonhap','Yonhap News Agency','KBS World','KBS WORLD Radio','Korea Herald','The Korea Herald','NHK World','nhk.or.jp','Asahi Shimbun','Kyodo News','Japan Times','Nikkei Asia','CSIS','Brookings','RAND','Atlantic Council','Council on Foreign Relations','IISS','Janes','Defense News','Military Times','War on the Rocks','Beyond Parallel','Carnegie Endowment','Globe and Mail','Nikkei Asia'],
ARRAY['OPCON','operational control','self-reliant','self reliance','nuclear-powered','cost','burden-sharing','rift','strain','questions','conditions-based','dagger','transfer','indigenous','proliferation concerns','eigenständig','Kosten'],
2),

('alliance_containment_instrument', 'korea_peninsula_deterrence',
'Washington treats its allies as instruments for containing China',
'Washington behandelt seine Verbündeten als Instrumente zur Eindämmung Chinas',
'Instrumentalisation framing (Chinese state media) is the only stance-bearing seam in the Russian and Chinese coverage of the alliance -- the rest is neutral wire reporting of exercises. Its claim is not that the drills provoke Pyongyang but that the United States uses South Korea as a tool in its own competition with Beijing, and that friction between Seoul and Washington -- the Yellow Sea standoff, a US commander''s "dagger" remarks -- exposes the allies'' divergent interests. Vocabulary: tools to contain China, fundamental differences, Chinese expert, US view of allies, hegemony.',
'Die Instrumentalisierungsrahmung (chinesische Staatsmedien) ist der einzige haltungstragende Strang in der russischen und chinesischen Berichterstattung über das Bündnis -- der Rest ist neutrale Agenturmeldung über Übungen. Ihre These lautet nicht, dass die Manöver Pjöngjang provozieren, sondern dass die Vereinigten Staaten Südkorea als Werkzeug im eigenen Wettbewerb mit Peking einsetzen und dass Reibungen zwischen Seoul und Washington -- der Zwischenfall im Gelben Meer, die "Dolch"-Äußerung eines US-Kommandeurs -- die auseinanderlaufenden Interessen der Verbündeten offenlegen.',
-2, 'Allies as tools of US China-containment', 'Verbündete als Werkzeuge der US-Eindämmung Chinas', true,
ARRAY['ASIA-CHINA'],
ARRAY['CGTN','China Daily','Global Times','People''s Daily','TASS','TASS (EN)','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant'],
ARRAY['contain China','containment','tools','instrument','fundamental differences','Chinese expert','hegemon','US view of allies','pretext','bloc confrontation','Eindämmung'],
3);

-- ---------------------------------------------------------------------------
-- 5. inter_korean_relations
--    Both stances live in the same ROK/Western coalition (Seoul's engagement
--    push vs Pyongyang's rejection of it are reported by the same outlets), so
--    both are framing-gated with disjoint keywords.
-- ---------------------------------------------------------------------------

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, framing_required,
    actor_centroids, publishers, framing_keywords, display_order
) VALUES
('inter_korean_engagement', 'inter_korean_relations',
'Engagement can lower tension and reopen the inter-Korean track',
'Annäherung kann Spannungen senken und den innerkoreanischen Kanal wieder öffnen',
'Engagement framing (Seoul''s government position as carried by South Korean and Western outlets) holds that the track can be reopened through unilateral de-escalation and offers: restoring the 2018 inter-Korean military agreement and its no-fly zone, easing civilian access along the border, expressing regret over drone incursions, resuming exchanges, and reading signals such as Kim Yo-jong''s statements or a less hostile constitutional revision as openings. Vocabulary: peaceful coexistence, dialogue, restore trust, improve ties, exchanges, no-fly zone, regret, ease, hope.',
'Die Annäherungsrahmung (die Position der Regierung in Seoul, transportiert von südkoreanischen und westlichen Medien) hält den Kanal für wieder zu öffnen -- durch einseitige Deeskalation und Angebote: Wiederherstellung des innerkoreanischen Militärabkommens von 2018 samt Flugverbotszone, Erleichterung des zivilen Zugangs entlang der Grenze, Bedauern über Drohneneinflüge, Wiederaufnahme des Austauschs und die Deutung von Signalen wie Äußerungen von Kim Yo-jong oder einer weniger feindseligen Verfassungsrevision als Öffnungen.',
2, 'Engagement can reopen the track', 'Annäherung kann den Kanal öffnen', true,
ARRAY['ASIA-SOUTHKOREA'],
ARRAY['Reuters','BBC World','Associated Press','AFP','The Guardian','Deutsche Welle','DW.com','CNN','France 24 (EN)','Euronews','Financial Times','Bloomberg','New York Times','Washington Post','Wall Street Journal','WSJ','The Telegraph','Sky News','NPR','ABC News','Channel NewsAsia','CNA','Straits Times','The Straits Times','Yonhap','Yonhap News Agency','KBS World','KBS WORLD Radio','Korea Herald','The Korea Herald','NHK World','nhk.or.jp','Asahi Shimbun','Kyodo News','Japan Times','Nikkei Asia','Al Jazeera','Brookings','Carnegie Endowment','Beyond Parallel'],
ARRAY['coexistence','dialogue','talks','restore','improve','exchange','no-fly zone','regret','ease','hope','trust','peaceful','revive','reinstate','wise','less hostility','engagement','Annäherung','Dialog','Gespräche'],
1),

('pyongyang_closed_the_door', 'inter_korean_relations',
'Pyongyang has formally closed the inter-Korean track',
'Pjöngjang hat den innerkoreanischen Kanal förmlich geschlossen',
'Closure framing (South Korean and Western outlets covering the same relationship) holds that the North has structurally ended the inter-Korean project rather than merely paused it: reunification references were deleted from the constitution, the South is defined as a separate and hostile state, Seoul''s diplomacy offers are publicly dismissed, and Seoul''s own unification white paper has pivoted to "two-state" coexistence. On this reading the engagement track has no counterpart. Vocabulary: drops reunification, two-state, hostile, separate state, dismisses, rejects, no interest, constitution, territory.',
'Die Abschlussrahmung (südkoreanische und westliche Medien, die dieselbe Beziehung abdecken) hält das innerkoreanische Projekt für strukturell beendet und nicht nur ausgesetzt: Verweise auf die Wiedervereinigung wurden aus der Verfassung gestrichen, der Süden wird als eigener und feindlicher Staat definiert, Gesprächsangebote aus Seoul werden öffentlich zurückgewiesen, und Seouls eigenes Weißbuch zur Wiedervereinigung ist auf eine Koexistenz zweier Staaten umgeschwenkt. In dieser Lesart fehlt dem Annäherungskurs das Gegenüber.',
-2, 'The track is structurally closed', 'Der Kanal ist strukturell geschlossen', true,
ARRAY['ASIA-NORKOREA'],
ARRAY['Reuters','BBC World','Associated Press','AFP','The Guardian','Deutsche Welle','DW.com','CNN','France 24 (EN)','Euronews','Financial Times','Bloomberg','New York Times','Washington Post','Wall Street Journal','WSJ','The Telegraph','Sky News','NPR','ABC News','Channel NewsAsia','CNA','Straits Times','The Straits Times','Yonhap','Yonhap News Agency','KBS World','KBS WORLD Radio','Korea Herald','The Korea Herald','NHK World','nhk.or.jp','Asahi Shimbun','Kyodo News','Japan Times','Nikkei Asia','Al Jazeera','Le Monde','El Mundo','Der Spiegel','Corriere della Sera'],
ARRAY['drops','dropped','drop','removes','removed','two-state','two state','hostile','separate state','dismiss','reject','no interest','constitution','territory','abandons','niente riunificazione','abandonne','streicht','feindlich'],
2);

COMMIT;

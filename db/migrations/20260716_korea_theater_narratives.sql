-- Korea theater: theater-level narrative cards (spec section 5.5).
--
-- The roll-up (THEATER_ROLLUP_SQL) sources each card's headlines from the member
-- atomics' title_narratives where sign(atomic.stance) = sign(theater.stance) AND
-- publisher IN (card.publishers). The count is uncapped over (sign, publisher),
-- so the hard rule is: cards of the SAME sign must be publisher-DISJOINT.
--
-- Partition used here -- two sign buckets, each split by bloc:
--
--   +  korea_allied_dual_track      Western + ROK + JP     (deterrence + engagement)
--   +  korea_sanctioned_bloc        Russian + Chinese + BY (sovereign deterrent,
--                                                           friendship, comradeship)
--   -  korea_hardening_threat       Western + ROK + JP     (proliferation, blood-for-tech,
--                                                           Beijing shields, autonomy
--                                                           strain, closed track)
--   -  korea_us_containment_critique Chinese + Russian     (allies as tools)
--
-- The two positives are publisher-disjoint from each other; so are the two
-- negatives. A positive and a negative may share publishers -- opposite signs
-- pull different-signed atomic titles, so no title double-counts.
--
-- NOTE ON THE WESTERN NEGATIVE CARD: it deliberately has ONE card, not two.
-- alliance_autonomy_strain is stance -1 and nk_proliferation_threat is -2, but
-- sign() collapses both to negative -- a second Western negative card would
-- double-count every title the first one already holds. Its claim is therefore
-- written broadly enough to cover both the external threat and the internal
-- renegotiation of the alliance, which is what the bucket actually contains.

BEGIN;

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de, framing_required,
    actor_centroids, publishers, framing_keywords, display_order
) VALUES

('korea_allied_dual_track', 'korea_theater',
'Hold the line, keep the door open: deterrence alongside engagement',
'Die Linie halten, die Tür offen lassen: Abschreckung und Annäherung zugleich',
'Dual-track framing (Western, South Korean and Japanese mainstream) is the allied position across the theatre: sustain the combined deterrence posture -- exercises, US Forces Korea, extended deterrence -- while Seoul simultaneously offers de-escalation to Pyongyang through the 2018 military agreement, border easing and expressions of regret over incidents. The two are presented as complementary rather than contradictory: pressure creates the conditions for talks. Vocabulary: extended deterrence, reaffirm commitment, readiness, peaceful coexistence, dialogue, restore trust, ease tensions.',
'Die Zweigleisigkeit (westliche, südkoreanische und japanische Leitmedien) ist die Position der Verbündeten im gesamten Schauplatz: das gemeinsame Abschreckungsdispositiv aufrechterhalten -- Übungen, US-Streitkräfte in Korea, erweiterte Abschreckung -- während Seoul Pjöngjang zugleich Deeskalation anbietet, über das Militärabkommen von 2018, Erleichterungen an der Grenze und Bedauern über Zwischenfälle. Beides gilt als komplementär, nicht als widersprüchlich: Druck schafft die Bedingungen für Gespräche.',
2, 'Allied deterrence and engagement', 'Abschreckung und Annäherung der Verbündeten', false,
ARRAY['AMERICAS-USA','ASIA-SOUTHKOREA','ASIA-JAPAN'],
ARRAY['Reuters','BBC World','Associated Press','AFP','The Guardian','Deutsche Welle','DW.com','CNN','France 24 (EN)','France 24','Euronews','Financial Times','Bloomberg','Bloomberg.com','New York Times','Washington Post','Wall Street Journal','WSJ','The Telegraph','Der Spiegel','Süddeutsche Zeitung','Le Monde','El País','El Mundo','The Economist','Sky News','NPR','ABC News','MSNBC','Channel NewsAsia','CNA','Straits Times','The Straits Times','Al Jazeera','Fox News','Yonhap','Yonhap News Agency','KBS World','KBS WORLD Radio','Korea Herald','The Korea Herald','NHK World','nhk.or.jp','Asahi Shimbun','Kyodo News','Japan Wire by KYODO NEWS','Japan Times','Nikkei Asia','CSIS','Brookings','RAND','Atlantic Council','Council on Foreign Relations','IISS','Janes','Defense News','Military Times','War on the Rocks','Beyond Parallel','Carnegie Endowment'],
ARRAY['extended deterrence','reaffirm','commitment','readiness','coexistence','dialogue','restore','ease','trust','engagement'],
1),

('korea_sanctioned_bloc', 'korea_theater',
'A bloc of sanctioned states drawing closer around Pyongyang',
'Ein Block sanktionierter Staaten rückt um Pjöngjang zusammen',
'Bloc framing (Russian, Belarusian and Chinese state press) presents North Korea not as an isolated pariah but as a sovereign state with partners: a nuclear status it is entitled to keep and will not trade away, a treaty-based military partnership with Moscow whose soldiers are honoured as heroes, and a restored traditional friendship with Beijing entering a "new era". Isolation is described as having failed and the relationships as lawful cooperation between states under the same sanctions, not as sanctions evasion. Vocabulary: sovereign right, nuclear status, strategic partnership, traditional friendship, new era, allies, heroes, mutual development.',
'Die Blockrahmung (russische, belarussische und chinesische Staatspresse) stellt Nordkorea nicht als isolierten Paria dar, sondern als souveränen Staat mit Partnern: mit einem Atomstatus, der ihm zusteht und den es nicht aufgeben wird, einer vertraglich geregelten Militärpartnerschaft mit Moskau, deren Soldaten als Helden geehrt werden, und einer wiederhergestellten traditionellen Freundschaft mit Peking, die in eine "neue Ära" eintritt. Die Isolation gilt als gescheitert und die Beziehungen als rechtmäßige Zusammenarbeit zwischen Staaten unter denselben Sanktionen, nicht als Sanktionsumgehung.',
2, 'Sanctioned states drawing closer', 'Sanktionierte Staaten rücken zusammen', false,
ARRAY['ASIA-NORKOREA','EUROPE-RUSSIA','ASIA-CHINA','EUROPE-BELARUS'],
ARRAY['TASS','TASS (EN)','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','BelTA Russian','CGTN','China Daily','Global Times','People''s Daily'],
ARRAY['sovereign right','nuclear status','partnership','friendship','new era','allies','heroes','cooperation','mutual'],
2),

('korea_hardening_threat', 'korea_theater',
'A hardening threat while the pressure regime frays',
'Eine sich verhärtende Bedrohung, während das Druckregime ausfranst',
'Threat framing (Western, South Korean and Japanese mainstream plus defence-analytic outlets) reads the theatre as moving the wrong way on every axis at once: the arsenal is expanding and its status declared irreversible, Russia is paying for troops and shells in ways that may accelerate the programme, Beijing''s restored lifeline blunts what remains of sanctions, Pyongyang has formally closed the inter-Korean track, and the alliance meant to answer all of this is itself renegotiating its terms -- operational control, cost-sharing and South Korea''s push for a more self-reliant defence. Vocabulary: threat, escalation, sanctions erosion, arms transfer, quid pro quo, drops reunification, OPCON transfer, self-reliant defence, strain.',
'Die Bedrohungsrahmung (westliche, südkoreanische und japanische Leitmedien sowie verteidigungsanalytische Fachmedien) liest den Schauplatz als eine Entwicklung, die sich auf allen Achsen zugleich in die falsche Richtung bewegt: Das Arsenal wächst und sein Status wird für unumkehrbar erklärt, Russland bezahlt Truppen und Granaten auf eine Weise, die das Programm beschleunigen könnte, Pekings wiederhergestellte Lebensader stumpft ab, was von den Sanktionen bleibt, Pjöngjang hat den innerkoreanischen Kanal förmlich geschlossen, und das Bündnis, das darauf antworten soll, verhandelt seine eigenen Bedingungen neu -- Operationskontrolle, Kostenteilung und Südkoreas Streben nach eigenständigerer Verteidigung.',
-2, 'Hardening threat, fraying pressure', 'Härtere Bedrohung, brüchiger Druck', false,
ARRAY['AMERICAS-USA','ASIA-SOUTHKOREA','ASIA-JAPAN','EUROPE-UKRAINE'],
ARRAY['Reuters','BBC World','Associated Press','AFP','The Guardian','Deutsche Welle','DW.com','CNN','France 24 (EN)','France 24','Euronews','Financial Times','Bloomberg','Bloomberg.com','New York Times','Washington Post','Wall Street Journal','WSJ','The Telegraph','Der Spiegel','Süddeutsche Zeitung','Le Monde','El País','El Mundo','The Economist','Sky News','NPR','ABC News','MSNBC','Channel NewsAsia','CNA','Straits Times','The Straits Times','Al Jazeera','Fox News','Kyiv Post','Yonhap','Yonhap News Agency','KBS World','KBS WORLD Radio','Korea Herald','The Korea Herald','NHK World','nhk.or.jp','Asahi Shimbun','Kyodo News','Japan Wire by KYODO NEWS','Japan Times','Nikkei Asia','CSIS','Brookings','RAND','Atlantic Council','Council on Foreign Relations','IISS','Janes','Defense News','Military Times','War on the Rocks','Beyond Parallel','Carnegie Endowment','Corriere della Sera','Globe and Mail','The Australian','Anadolu Agency','UN News'],
ARRAY['threat','escalat','sanctions','arms','quid pro quo','drops','OPCON','self-reliant','strain','grip','lifeline','irreversible'],
3),

('korea_us_containment_critique', 'korea_theater',
'US alliances on the peninsula serve the containment of China',
'US-Bündnisse auf der Halbinsel dienen der Eindämmung Chinas',
'Containment-critique framing (Chinese state media) is the only sustained adversarial line the Russian and Chinese press runs against the allied side in this theatre -- their coverage of exercises and launches is otherwise neutral wire reporting. Its claim is that Washington treats South Korea as an instrument in its competition with Beijing rather than as an ally with interests of its own, and that visible friction between Seoul and Washington exposes the divergence. It is a critique of US intentions, not a defence of Pyongyang''s. Vocabulary: tools to contain China, fundamental differences, US view of allies, hegemony, bloc confrontation.',
'Die Eindämmungskritik (chinesische Staatsmedien) ist die einzige dauerhaft gegnerische Linie, die die russische und chinesische Presse in diesem Schauplatz gegen die Seite der Verbündeten fährt -- ihre Berichterstattung über Übungen und Raketenstarts ist ansonsten neutrale Agenturmeldung. Ihre These lautet, dass Washington Südkorea als Instrument im Wettbewerb mit Peking behandelt statt als Verbündeten mit eigenen Interessen, und dass sichtbare Reibungen zwischen Seoul und Washington diese Divergenz offenlegen. Es ist eine Kritik an den Absichten der USA, keine Verteidigung derjenigen Pjöngjangs.',
-2, 'Allies as tools of China-containment', 'Verbündete als Werkzeuge der Eindämmung Chinas', false,
ARRAY['ASIA-CHINA'],
ARRAY['CGTN','China Daily','Global Times','People''s Daily','TASS','TASS (EN)','RT','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant'],
ARRAY['contain China','containment','tools','instrument','fundamental differences','hegemon','pretext','bloc confrontation'],
4);

COMMIT;

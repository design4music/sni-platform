-- Taiwan Strait theater: strip internal/mechanics language that leaked into
-- user-facing prose (Asana task 1216618489706919).
--
-- Two classes of leak:
-- 1. "Four axes run through the theater" / "tracks separately" / "This node
--    covers/tracks" -- narrator voice describing our own internal structure.
--    The atomic-FN count is an editorial judgment call, not a fixed taxonomy,
--    so committing to "four axes" in frontend prose is also substantively
--    wrong, not just stylistically off.
-- 2. Trailing "Vocabulary: ..." sentences on narrative claims, and one
--    sentence on us_commitment_firm describing framing_required matching
--    mechanics ("Shares its publisher coalition with... so framing keywords
--    are required to separate the two") -- both describe how OUR matching
--    works, not the narrative itself.
--
-- Content only changes: removed sentences, reworded connective tissue where
-- removing a lead-in broke the sentence. No claims, stances, or facts added
-- or altered.

BEGIN;

UPDATE friction_nodes SET
  description_en = 'The dispute over Taiwan''s political status and the military, diplomatic and economic contest surrounding it. Beijing claims the island as Chinese territory and has not renounced the use of force to take it; Taipei governs the island separately and rejects that claim. The contest spans Chinese military and coast guard activity around the island and the deterrence response to it; the scope and reliability of United States arms supply and security policy; political influence activity directed at Taiwan and the contest over it among the island''s parties; and Taiwan''s diplomatic recognition and participation in international organisations. The United States and Japan are parties to the security dimension without maintaining formal diplomatic relations with Taipei.',
  description_de = 'Der Streit über den politischen Status Taiwans und der militärische, diplomatische und wirtschaftliche Wettstreit darum. Peking beansprucht die Insel als chinesisches Territorium und hat dem Einsatz von Gewalt zu ihrer Einnahme nicht abgeschworen; Taipeh regiert die Insel getrennt und weist diesen Anspruch zurück. Der Wettstreit umfasst chinesische Militär- und Küstenwachaktivitäten rund um die Insel und die darauf gerichtete Abschreckung; Umfang und Verlässlichkeit der US-Waffenlieferungen und Sicherheitspolitik; die auf Taiwan gerichtete politische Einflussnahme und der Wettstreit darüber zwischen den Parteien der Insel; sowie Taiwans diplomatische Anerkennung und Teilhabe an internationalen Organisationen. Die USA und Japan sind Parteien der Sicherheitsdimension, ohne formelle diplomatische Beziehungen zu Taipeh zu unterhalten.',
  editorial_summary_en = 'The Taiwan Strait is where the People''s Republic of China''s claim to Taiwan meets the island''s separate government and the security arrangements of the United States and Japan. Beijing holds that the island is part of China and has not renounced the use of force; Taipei governs it separately, and Washington maintains unofficial relations, supplies arms under the Taiwan Relations Act, and has long declined to state explicitly whether it would intervene militarily. The contest spans aircraft, naval and coast guard activity around the island together with the exercises and Strait transits conducted in response; the scale and dependability of American arms supply, alongside Taiwan''s own defence budget and conscription debates; political influence activity directed at the island, including the party-to-party channel between the Chinese Communist Party and the Kuomintang, economic inducements, and reported espionage and disinformation; and Taiwan''s shrinking set of formal diplomatic partners, its exclusion from bodies such as the World Health Assembly, and the restrictions placed on its officials'' travel. Coverage divides along predictable lines: Western, Japanese and regional outlets describe Chinese activity as coercion of a democracy, Chinese and Russian state media describe the same activity as lawful enforcement of sovereignty against foreign interference, and a distinct strand of Western reporting questions whether American commitments will hold.',
  editorial_summary_de = 'In der Taiwanstraße trifft der Anspruch der Volksrepublik China auf Taiwan auf die eigenständige Regierung der Insel und die Sicherheitsarrangements der USA und Japans. Peking hält die Insel für einen Teil Chinas und hat dem Einsatz von Gewalt nicht abgeschworen; Taipeh regiert sie getrennt, und Washington unterhält inoffizielle Beziehungen, liefert Waffen nach dem Taiwan Relations Act und hat es lange vermieden, ausdrücklich zu erklären, ob es militärisch eingreifen würde. Der Wettstreit umfasst Luft-, See- und Küstenwachaktivitäten rund um die Insel samt der darauf folgenden Manöver und Durchfahrten; Umfang und Verlässlichkeit der amerikanischen Waffenlieferungen neben Taiwans eigenen Debatten über Verteidigungshaushalt und Wehrpflicht; die auf die Insel gerichtete politische Einflussnahme, darunter der Parteikanal zwischen der Kommunistischen Partei Chinas und der Kuomintang, wirtschaftliche Anreize sowie berichtete Spionage und Desinformation; und Taiwans schrumpfender Kreis formeller diplomatischer Partner, sein Ausschluss aus Gremien wie der Weltgesundheitsversammlung und die Beschränkungen für Reisen seiner Amtsträger. Die Berichterstattung teilt sich entlang erwartbarer Linien.'
WHERE id = 'taiwan_strait_theater';

UPDATE friction_nodes SET
  editorial_summary_en = 'Military and sub-military activity around Taiwan, and the responses to it, run on two sides. On one: sorties across the median line and into the air defence identification zone, coast guard patrols to the island''s east that Beijing characterises as regularised law enforcement, aircraft carrier movements through the Strait, and exercises that rehearse blockade and landing operations. On the other: Taiwan''s combat readiness drills, its investment in drones and asymmetric systems, and the Taiwan Strait transits conducted by American, Japanese, Canadian, Australian and European vessels, each of which draws a Chinese response. A distinct strand runs below the threshold of armed force -- undersea cable breaks affecting outlying islands, balloons, sand dredging and cyber operations -- and is often the more consequential day to day. The same events carry opposite descriptions depending on the outlet: an incursion or a routine patrol, a provocation or a lawful response.',
  editorial_summary_de = 'Die militärischen und untermilitärischen Aktivitäten rund um Taiwan und die Reaktionen darauf verlaufen auf zwei Seiten. Auf der einen: Einsätze über die Mittellinie und in die Luftverteidigungszone, Küstenwachpatrouillen östlich der Insel, die Peking als regularisierte Rechtsdurchsetzung bezeichnet, Trägerbewegungen durch die Meerenge und Manöver, die Blockade- und Landungsoperationen proben. Auf der anderen: Taiwans Bereitschaftsübungen, seine Investitionen in Drohnen und asymmetrische Systeme sowie die Durchfahrten amerikanischer, japanischer, kanadischer, australischer und europäischer Schiffe, auf die jeweils eine chinesische Reaktion folgt. Ein eigener Strang verläuft unterhalb der Schwelle bewaffneter Gewalt: Brüche von Seekabeln zu den vorgelagerten Inseln, Ballons, Sandbaggerei und Cyberoperationen. Dieselben Ereignisse werden je nach Medium gegensätzlich beschrieben.'
WHERE id = 'taiwan_military_pressure';

UPDATE friction_nodes SET
  editorial_summary_en = 'Taiwan maintains formal diplomatic relations with a small and shrinking number of states, and unofficial relations through representative offices with many more. The contest over both spans pressure on the remaining partners and the periodic switches of recognition; the blocking of Taiwanese leaders'' travel through denied overflight and transit clearances, which has curtailed presidential trips; exclusion from the World Health Assembly and ICAO; and the argument over whether United Nations General Assembly Resolution 2758 settled the island''s status, which Beijing asserts and Taipei and several Western governments dispute. Individual bilateral disputes recur -- Lithuania''s representative office and the trade consequences that followed, an office opened with Somaliland, and the responses to parliamentary delegations visiting Taipei. Naming is itself contested: whether the island is called Taiwan, Chinese Taipei, the Taiwan region or the Republic of China signals a position rather than a neutral choice.',
  editorial_summary_de = 'Taiwan unterhält formelle diplomatische Beziehungen zu einer kleinen und schrumpfenden Zahl von Staaten und inoffizielle Beziehungen über Repräsentanzen zu deutlich mehr. Der Wettstreit um beides umfasst den Druck auf die verbliebenen Partner und die zeitweiligen Anerkennungswechsel; die Blockade von Reisen taiwanischer Politiker durch verweigerte Überflug- und Transitgenehmigungen, die Präsidentenreisen beschnitten hat; den Ausschluss von der Weltgesundheitsversammlung und der ICAO; sowie den Streit darüber, ob die UN-Resolution 2758 den Status der Insel geklärt hat, was Peking behauptet und Taipeh sowie mehrere westliche Regierungen bestreiten. Einzelne bilaterale Streitfälle wiederholen sich, etwa Litauens Repräsentanz und die folgenden Handelskonsequenzen. Auch die Benennung ist umstritten und signalisiert eine Position.'
WHERE id = 'taiwan_international_recognition';

-- Theater narrative cards: drop the sentences describing how the roll-up
-- mechanism works (§5.5 internals), keep the substantive claim.
UPDATE narratives_v2 SET
  claim_en = 'The Western and regional security consensus reads the Strait as a democracy under sustained coercion -- military and grey-zone pressure, united front subversion and diplomatic isolation -- whose deterrence, arms supply and international space must be reinforced. It spans Western, Japanese and regional mainstream outlets.'
WHERE id = 'taiwan_strait_western_consensus';

UPDATE narratives_v2 SET
  claim_en = 'The Western critical register turns the same supportive coalition into a critic: it reports an American administration calling arms sales a negotiating chip, reviewing or withholding packages and declining to state a commitment, alongside Taiwan''s own stalled defence budget and contested readiness. It is criticism of Washington and of Taipei''s preparedness -- not support for Beijing''s claim.'
WHERE id = 'taiwan_strait_western_doubt';

-- Atomic narratives: drop trailing "Vocabulary: ..." lines (matching-alias
-- lists, not part of the claim) across all 9 atomic-level narratives.
UPDATE narratives_v2 SET
  claim_en = 'International-space framing (Western, Japanese and regional mainstream) treats Beijing''s pressure on Taiwan''s remaining diplomatic allies, the blocking of its leaders'' transits and overflight clearances, and its exclusion from the World Health Assembly and ICAO as coercive isolation of a functioning democracy, and defends parliamentary visits and representative offices against retaliation.'
WHERE id = 'taiwan_international_space';

UPDATE narratives_v2 SET
  claim_en = 'One-China framing (Chinese and Russian state media) holds that UN Resolution 2758 settled the island''s status, that the one-China principle commands near-universal recognition, and that "dollar diplomacy" and attempts to expand international space breach other states'' commitments and will collapse.'
WHERE id = 'one_china_consensus';

UPDATE narratives_v2 SET
  claim_en = 'Deterrence framing (Western, Japanese and regional mainstream) treats PLA sorties across the median line, coast guard "law enforcement" patrols east of the island, carrier transits and invasion-style drills as escalating coercion against a democracy -- a grey-zone campaign to normalise pressure and wear down Taiwan''s defences -- to be answered with readiness drills, allied Strait transits and deterrence.'
WHERE id = 'taiwan_coercion_deterrence';

UPDATE narratives_v2 SET
  claim_en = 'Sovereignty-enforcement framing (Chinese and Russian state media) presents patrols and drills as routine law enforcement and legitimate defence of territorial integrity in China''s own waters, triggered by "Taiwan independence" provocation and foreign meddling, with responsibility for escalation placed on Taipei and Washington.'
WHERE id = 'pla_sovereignty_enforcement';

UPDATE narratives_v2 SET
  claim_en = 'Subversion framing (Western, Japanese and regional mainstream) treats Beijing''s cultivation of the opposition, economic inducements, espionage inside the military, and cognitive-warfare and disinformation campaigns as an attempt to hollow out Taiwan''s democracy from within and secure annexation without fighting.'
WHERE id = 'united_front_subversion';

UPDATE narratives_v2 SET
  claim_en = 'Anti-separatism framing (Chinese and Russian state media) presents Beijing''s political campaign as legitimate and popular: hosting the opposition party''s delegations, offering exchanges, incentives and preferential policies to "Taiwan compatriots", denouncing "Taiwan independence" forces and their foreign backers, and casting the governing party as an unpopular obstacle serving external forces. Courtship and coercion run together here as one campaign -- inducements for the opposition alongside blacklists and warnings to separatists.'
WHERE id = 'beijing_antiseparatism_unity';

UPDATE narratives_v2 SET
  claim_en = 'Commitment-firm framing (Western and regional mainstream) reports approvals, deliveries and record arms-sale volumes, cleared backlogs and official reaffirmations that policy is unchanged, alongside Taiwan''s own budget increases and asymmetric build-up, as evidence that deterrence is being reinforced.'
WHERE id = 'us_commitment_firm';

UPDATE narratives_v2 SET
  claim_en = 'Commitment-doubt framing (the same Western and regional mainstream, in critical register) treats Taiwan as exposed by an administration that calls arms sales a negotiating chip, withholds or reviews packages, declines to state a commitment, and bargains over the island in summitry with Beijing. This is the own-goal register in which the normally supportive coalition is itself the critic -- it is criticism of Washington, not support for Beijing.'
WHERE id = 'us_commitment_doubted';

UPDATE narratives_v2 SET
  claim_en = 'Pawn framing (Chinese and Russian state media) holds that American arms sales breach the one-China principle and the joint communiqués, that Washington milks Taiwan as a "cash machine" and will abandon it when convenient, and that the governing party''s reliance on external forces is doomed.'
WHERE id = 'taiwan_us_pawn';

UPDATE narratives_v2 SET updated_at = now() WHERE fn_id LIKE 'taiwan%';

COMMIT;

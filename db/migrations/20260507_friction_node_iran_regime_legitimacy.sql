-- Friction Node: iran_regime_legitimacy_contest
-- 2026-05-07
--
-- The fat FN that captures the persistent contest over whether Iran's
-- current government has the right to exist as it does, vs whether the
-- Islamic Republic should be replaced (regime change). Spans diplomatic,
-- sanctions, soft-power and kinetic phases — the 2025-2026 war is the
-- most acute expression of a 45-year contest. Khamenei's killing,
-- Larijani's killing, the 2022-2023 protests, the MEK and Pahlavi
-- diaspora, Iran International broadcasting, Iranian elections, and the
-- regime's responses to all of these all live on this FN.
--
-- Adds:
--   1. friction_nodes row
--   2. Two NEW narratives:
--      - west_iran_regime_change_doctrine (Israel-US-Saudi all-in,
--        ideological tier — regime is illegitimate, change desirable)
--      - iran_sovereign_existence (Iran all-in, ideological tier —
--        sovereign state, anti-imperial defence)
--   3. Re-uses two existing stand-by narratives:
--      - eu_diplomatic_preservation_norm (cautious engagement, human
--        rights criticism, no formal regime-change endorsement)
--      - multipolar_systemic_alternative (sovereignty principle, anti
--        Western military adventurism)

BEGIN;

-- ============================================================
-- 1. FN entry
-- ============================================================
INSERT INTO friction_nodes (
    id, name_en, name_de,
    description_en, description_de,
    editorial_summary_en, editorial_summary_de,
    centroid_ids, topic_keywords,
    event_actor_markers, event_topic_markers, event_title_anchors,
    display_order
) VALUES (
    'iran_regime_legitimacy_contest',
    'Iran regime legitimacy contest',
    'Streit um die Legitimitaet des iranischen Regimes',
    $D$Whether Iran's current government — the Islamic Republic established in 1979 — has the right to continue existing as it does. The Western and Israeli reading frames the regime as illegitimate, brutal toward its own people, and a permanent threat that should be replaced. The Iranian reading frames the system as a sovereign religious-democratic state under permanent foreign assault. Russia, China and the broader Global South frame Western pressure as a textbook regime-change campaign violating sovereignty principles. The contest has run for 45 years through sanctions, opposition support, soft-power broadcasting, internal protest cycles and now kinetic war — all expressions of the same underlying question.$D$,
    $D$Hat Irans aktuelle Regierung — die 1979 errichtete Islamische Republik — das Recht, in ihrer jetzigen Form weiter zu existieren? Die westliche und israelische Lesart rahmt das Regime als illegitim, brutal gegenueber dem eigenen Volk und als permanente Bedrohung, die ersetzt werden sollte. Die iranische Lesart rahmt das System als souveraenen religioes-demokratischen Staat unter permanentem fremden Angriff. Russland, China und der breitere Globale Sueden rahmen westlichen Druck als lehrbuchhaften Regimewechsel-Versuch unter Verletzung von Souveraenitaetsprinzipien. Der Konflikt laeuft seit 45 Jahren durch Sanktionen, Oppositionsunterstuetzung, Soft-Power-Sendungen, interne Protestzyklen und nun kinetischen Krieg — alles Ausdruecke derselben grundlegenden Frage.$D$,
    $D$The Iran regime legitimacy contest is the foundational and most persistent contest in US-Iran and Israel-Iran relations. It is the contest under which all the other Iran contests sit — the nuclear program (FN2), the proxy network (FN3) and the kinetic episodes are operational expressions of the same underlying question of whether the Islamic Republic should continue to exist. Every escalation comes back to this. The 2022-2023 Mahsa Amini protests + crackdown gave Western actors a renewed framing of "the Iranian people deserve freedom" and revived the Pahlavi monarchist diaspora and the MEK as opposition vehicles. The 2025 and 2026 strikes on Iranian leadership — culminating in the killing of Supreme Leader Khamenei and the killing of senior advisor Larijani — were framed by Israel and the United States as a decapitation that opens space for democratic transition, and by Iran as the ultimate proof that Western intentions have always been regime change rather than nuclear non-proliferation. Russia and China amplify the sovereignty principle: no state should be subject to externally-imposed leadership change, whatever its domestic record. The European Union threads a careful needle — sustained criticism of Iranian human rights and the protest crackdown, sustained diplomatic engagement with whichever government holds power, no formal regime-change policy.$D$,
    $D$Der Streit um die Legitimitaet des iranischen Regimes ist der fundamentale und bestaendigste Konflikt in den US-iranischen und israelisch-iranischen Beziehungen. Er ist der Konflikt, unter dem alle anderen Iran-Konflikte stehen — das Atomprogramm (FN2), das Stellvertreternetz (FN3) und die kinetischen Episoden sind operative Ausdruecke derselben grundlegenden Frage. Jede Eskalation fuehrt hierher zurueck. Die Mahsa-Amini-Proteste 2022-2023 und ihre Niederschlagung gaben westlichen Akteuren den erneuerten Rahmen "das iranische Volk verdient Freiheit" und belebten die Pahlavi-Monarchie-Diaspora und die MEK als Oppositionsvehikel. Die Schlaege 2025 und 2026 auf die iranische Fuehrung — gipfelnd in der Toetung des Obersten Fuehrers Khamenei und des hochrangigen Beraters Larijani — wurden von Israel und den USA als Enthauptung gerahmt, die Raum fuer demokratischen Uebergang oeffnet, und vom Iran als ultimativer Beweis, dass westliche Absichten immer Regimewechsel waren, nicht nukleare Nichtverbreitung. Russland und China verstaerken das Souveraenitaetsprinzip: kein Staat sollte extern auferlegtem Fuehrungswechsel unterliegen. Die Europaeische Union faedelt einen vorsichtigen Pfad — anhaltende Kritik an iranischen Menschenrechten und der Niederschlagung der Proteste, anhaltendes diplomatisches Engagement mit der jeweiligen Regierung, keine formelle Regimewechsel-Politik.$D$,
    ARRAY['MIDEAST-IRAN', 'MIDEAST-ISRAEL', 'AMERICAS-USA', 'MIDEAST-SAUDI', 'NON-STATE-EU', 'EUROPE-RUSSIA', 'ASIA-CHINA'],
    ARRAY[
        -- Regime / opposition discourse
        'Islamic Republic', 'the regime', 'Iranian regime', 'mullahs',
        'regime change', 'topple', 'overthrow', 'fall of the regime',
        'Iranian opposition', 'opposition figures',
        -- Diaspora opposition vehicles
        'Pahlavi', 'Reza Pahlavi', 'Crown Prince', 'monarchist',
        'MEK', 'Mojahedin', 'Mojahedin-e Khalq', 'NCRI',
        'Maryam Rajavi', 'Iran International',
        -- Internal politics / protest cycle
        'Mahsa Amini', 'Women Life Freedom', 'Zhina',
        'Iranian protest', 'Iran protest', 'protests in Iran',
        'crackdown', 'morality police', 'hijab protest',
        'Iranian elections', 'Iran election',
        -- Leadership / succession
        'Supreme Leader', 'Ayatollah', 'Khamenei', 'Khamenei killed',
        'Khamenei dead', 'next supreme leader', 'Iranian succession',
        'Pezeshkian', 'Larijani', 'Mojtaba Khamenei',
        'Raisi',
        -- Decapitation framing
        'decapitation strike', 'regime decapitated', 'regime collapse',
        'regime change in Iran',
        -- Iranian counter-framing
        'sovereign Iran', 'Iranian sovereignty', 'foreign-backed',
        'regime change war', 'foreign interference',
        'Khomeini'
    ],
    -- Event-title gate.
    -- Anchors alone qualify: any title mentioning Khamenei or Pahlavi or
    -- MEK or Mahsa Amini is on-FN.
    -- Actor + topic catches: "Iran cracks down on protesters" etc.
    ARRAY['Iran', 'Tehran', 'Iranian'],
    ARRAY[
        'regime', 'opposition', 'protest', 'crackdown',
        'election', 'elections', 'succession',
        'supreme leader', 'ayatollah', 'morality police',
        'rally', 'dissident', 'human rights',
        'overthrow', 'topple', 'regime change',
        'martyred', 'killed in', 'eliminated'
    ],
    ARRAY[
        'Khamenei', 'Pahlavi', 'Reza Pahlavi',
        'MEK', 'Mojahedin', 'Mojahedin-e Khalq',
        'Mahsa Amini', 'Women Life Freedom',
        'Iran International',
        'Larijani', 'Mojtaba Khamenei',
        'Khomeini'
    ],
    3
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- 2a. NEW narrative: west_iran_regime_change_doctrine
-- ============================================================
INSERT INTO narratives_v2 (
    id, name_en, name_de, claim_en, claim_de,
    actor_centroids, tier, narrative_type,
    framing_keywords, topic_keywords,
    publishers, editorial_organ_publishers
) VALUES (
    'west_iran_regime_change_doctrine',
    'Western coalition: the Iranian regime is illegitimate and replaceable',
    'Westliche Koalition: das iranische Regime ist illegitim und ersetzbar',
    $D$The Israel-US-Saudi coalition describes the Islamic Republic of Iran as an illegitimate, brutal "regime" — the loaded word "regime" rather than "government" is itself the diagnostic — that "oppresses its own people", supports "terror infrastructure" abroad, and pursues nuclear weapons. The narrative holds that "the Iranian people deserve freedom" and that the regime is propped up only by repression of the women, students and ethnic minorities who would otherwise replace it. The 2022-2023 "Mahsa Amini" protests and the "Women Life Freedom" movement are framed as proof that the regime has lost its people. The diaspora opposition — "Reza Pahlavi" and the monarchist movement, "Maryam Rajavi" and the "Mojahedin-e Khalq" (MEK), "Iran International" television — are presented as legitimate alternative leadership-in-waiting. Sanctions, designation of the IRGC as a foreign terrorist organisation, and material and rhetorical support for the opposition are framed as solidarity with the Iranian people against their oppressors. The 2025 and 2026 Israeli and American strikes on Iranian leadership — including the killing of "Supreme Leader Khamenei" and "Ali Larijani" — are framed as a "decapitation" that opens space for "democratic transition" and the "fall of the Islamic Republic". The narrative explicitly does not endorse occupation or regime imposition — the prescribed model is that the Iranian people, freed from the regime's grip, will choose their own future. The narrative prescribes: maximum-pressure sanctions, support to opposition voices and broadcasting, diplomatic isolation of the regime, kinetic operations against regime apparatus where opportunity arises, and rejection of any framework that legitimises the current government as a normal interlocutor.$D$,
    $D$Die israelisch-amerikanisch-saudische Koalition beschreibt die Islamische Republik Iran als illegitimes, brutales "Regime" — das geladene Wort "Regime" statt "Regierung" ist selbst das Diagnostikum — das "sein eigenes Volk unterdrueckt", "Terror-Infrastruktur" im Ausland unterstuetzt und Nuklearwaffen anstrebt. Das Narrativ haelt fest, dass "das iranische Volk Freiheit verdient" und dass das Regime nur durch Unterdrueckung jener Frauen, Studenten und ethnischen Minderheiten gestuetzt wird, die es sonst ersetzen wuerden. Die Mahsa-Amini-Proteste 2022-2023 und die "Women Life Freedom"-Bewegung gelten als Beweis, dass das Regime sein Volk verloren hat. Die Diaspora-Opposition — "Reza Pahlavi" und die Monarchisten-Bewegung, "Maryam Rajavi" und die "Mojahedin-e Khalq" (MEK), Iran International TV — werden als legitime alternative Fuehrung im Wartestand praesentiert. Sanktionen, FTO-Designierung der IRGC und Unterstuetzung der Opposition gelten als Solidaritaet mit dem iranischen Volk. Die israelisch-amerikanischen Schlaege 2025 und 2026 auf die iranische Fuehrung — einschliesslich der Toetung des "Obersten Fuehrers Khamenei" und "Ali Larijanis" — werden als "Enthauptung" gerahmt, die Raum fuer "demokratischen Uebergang" und "Fall der Islamischen Republik" oeffnet. Das Narrativ befuerwortet ausdruecklich keine Besatzung oder aufgezwungene Regierung — das vorgeschriebene Modell ist, dass das iranische Volk, befreit vom Regime, seine eigene Zukunft waehlen wird. Verschreibung: maximaler Sanktionsdruck, Unterstuetzung von Oppositionsstimmen und -sendungen, diplomatische Isolation, kinetische Operationen gegen Regimeapparat wo Gelegenheit besteht, Ablehnung jedes Rahmens, der die gegenwaertige Regierung als normalen Gespraechspartner legitimiert.$D$,
    ARRAY['AMERICAS-USA', 'MIDEAST-ISRAEL', 'MIDEAST-SAUDI'],
    'ideological',
    'all_in',
    ARRAY[
        -- The "regime" framing itself
        'the regime', 'Iranian regime', 'Tehran regime', 'mullah regime',
        'tyrannical regime', 'brutal regime', 'oppressive regime',
        'Islamic Republic',
        -- Replacement / change framing
        'regime change', 'topple', 'overthrow', 'fall of the regime',
        'fall of the Islamic Republic', 'collapse of the regime',
        'democratic transition', 'post-regime Iran',
        'free Iran', 'liberate Iran', 'free the Iranian people',
        -- People-vs-regime
        'Iranian people deserve freedom', 'people vs the regime',
        'Iranian opposition', 'opposition leaders', 'opposition figures',
        'oppressed by the regime',
        -- Mahsa Amini / Women Life Freedom protest cycle
        'Mahsa Amini', 'Women Life Freedom', 'Zan Zendegi Azadi',
        'morality police', 'hijab protest', 'protests in Iran crushed',
        'crackdown on protesters',
        -- Diaspora opposition vehicles
        'Reza Pahlavi', 'Pahlavi', 'Crown Prince of Iran',
        'monarchist', 'monarchist opposition',
        'MEK', 'Mojahedin-e Khalq', 'NCRI', 'Maryam Rajavi',
        'Iran International',
        -- Decapitation / war framing
        'decapitation strike', 'regime decapitated', 'Khamenei killed',
        'Khamenei eliminated', 'Khamenei dead',
        'Larijani killed', 'Larijani assassinated',
        'regime collapse imminent'
    ],
    ARRAY[
        'Iran', 'Tehran', 'Iranian', 'Islamic Republic',
        'Khamenei', 'Pezeshkian', 'Pahlavi', 'MEK',
        'Mahsa Amini', 'Iran International',
        'Iranian opposition', 'protest', 'crackdown',
        'sanctions Iran', 'sanctions on Iran',
        'regime change'
    ],
    ARRAY[
        -- Israeli (always anti-regime)
        'Jerusalem Post', 'The Jerusalem Post', 'Times of Israel',
        'Haaretz', 'i24NEWS', 'JNS', 'Israel Hayom', 'Ynet',
        -- US (mainstream + conservative)
        'Fox News', 'Wall Street Journal', 'WSJ', 'New York Post',
        'CNN', 'New York Times', 'The New York Times',
        'Washington Post', 'The Washington Post',
        'Bloomberg', 'NPR', 'MSNBC', 'Associated Press',
        -- Saudi (regime-critical)
        'Arab News', 'Saudi Gazette', 'Al Arabiya', 'Al Arabiya English',
        'Asharq Al-Awsat',
        -- Pro-Western / pro-Ukraine
        'Kyiv Post'
    ],
    ARRAY[]::text[]
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- 2b. NEW narrative: iran_sovereign_existence
-- ============================================================
INSERT INTO narratives_v2 (
    id, name_en, name_de, claim_en, claim_de,
    actor_centroids, tier, narrative_type,
    framing_keywords, topic_keywords,
    publishers, editorial_organ_publishers
) VALUES (
    'iran_sovereign_existence',
    'Iran: Islamic Republic as sovereign state under permanent foreign assault',
    'Iran: Islamische Republik als souveraener Staat unter permanentem fremden Angriff',
    $D$Iran describes its political system in a framework of "religious democracy" — the "Islamic Republic" established by "Imam Khomeini" in 1979, headed by the "Supreme Leader" under the doctrine of "Velayat-e Faqih" (Guardianship of the Jurist). Western and Israeli pressure across all phases — sanctions, support for opposition, broadcasting, military action — is framed as a single 45-year imperial "regime change" campaign disguised under successive pretexts (nuclear, terrorism, human rights). The diaspora opposition is delegitimised: the "MEK" / "Mojahedin-e Khalq" is termed "Munafiqin" (the hypocrites) and "foreign-backed terrorists" responsible for thousands of Iranian deaths; the "Pahlavi pretender" Reza Pahlavi is framed as an irrelevant son of an overthrown dictator; "Iran International" is framed as Saudi-funded propaganda. The 2022-2023 protests are framed as "foreign-instigated unrest" stoked by hostile media — "rioters" rather than "protesters" — though the underlying social grievances are sometimes acknowledged. The 2025 and 2026 Israeli and American strikes on Iranian leadership are framed as "war crimes" and "state terrorism" against a sovereign government; the "martyrdom" of "Imam Khamenei" and Larijani is framed as elevating them rather than ending their authority, and as binding the Iranian nation in unity against the aggressor. Resilience framing dominates: "we will not bow", "stronger after every blow", "national unity in the face of aggression". The narrative prescribes: continued sovereignty without external concessions, military preparedness for further aggression, sustained orderly succession (the Assembly of Experts process), continued material and rhetorical pressure on Western and Israeli legitimacy, and rejection of any negotiating framework that treats the Islamic Republic as a temporary or replaceable government.$D$,
    $D$Iran beschreibt sein politisches System im Rahmen "religioeser Demokratie" — die 1979 von "Imam Khomeini" errichtete "Islamische Republik", gefuehrt vom "Obersten Fuehrer" unter der Doktrin "Velayat-e Faqih". Westlicher und israelischer Druck in allen Phasen — Sanktionen, Oppositionsunterstuetzung, Sendungen, militaerische Aktion — wird als einzige 45-jaehrige imperiale "Regimewechsel"-Kampagne unter verschiedenen Vorwaenden (nuklear, Terrorismus, Menschenrechte) gerahmt. Die Diaspora-Opposition wird delegitimiert: die "MEK"/"Mojahedin-e Khalq" gelten als "Munafiqin" (Heuchler) und "fremdfinanzierte Terroristen", verantwortlich fuer Tausende iranischer Tote; der "Pahlavi-Praetendent" Reza Pahlavi gilt als irrelevanter Sohn eines gestuerzten Diktators; "Iran International" als saudisch finanzierte Propaganda. Die Proteste 2022-2023 gelten als "fremdgeschuerte Unruhen" — "Randalierer" statt "Demonstranten" — wenngleich die unterliegenden sozialen Beschwerden manchmal anerkannt werden. Die israelisch-amerikanischen Schlaege 2025-2026 auf die iranische Fuehrung gelten als "Kriegsverbrechen" und "Staatsterrorismus" gegen eine souveraene Regierung; das "Martyrium" von "Imam Khamenei" und Larijani erhebe sie statt ihre Autoritaet zu beenden und binde die iranische Nation in Einheit gegen den Aggressor. Resilienz dominiert: "wir beugen uns nicht", "staerker nach jedem Schlag", "nationale Einheit im Angesicht der Aggression". Verschreibung: anhaltende Souveraenitaet ohne externe Zugestaendnisse, militaerische Bereitschaft fuer weitere Aggression, geordnete Nachfolge (Expertenversammlungs-Prozess), fortgesetzter materieller und rhetorischer Druck auf westliche und israelische Legitimitaet, Ablehnung jedes Verhandlungsrahmens, der die Islamische Republik als temporaere oder ersetzbare Regierung behandelt.$D$,
    ARRAY['MIDEAST-IRAN'],
    'ideological',
    'all_in',
    ARRAY[
        -- Self-designation (loaded by virtue of asserting legitimacy)
        'Islamic Republic', 'religious democracy',
        'Imam Khomeini', 'Imam Khamenei',
        'Supreme Leader', 'Ayatollah Khamenei', 'Ayatollah',
        'Velayat-e Faqih', 'Guardian Jurist',
        'Pasdaran', 'Sepah',
        -- Anti-opposition delegitimisation
        'Munafiqin', 'foreign-backed terrorists',
        'MEK terrorist', 'MEK terror',
        'Pahlavi pretender', 'son of the Shah',
        'Saudi-funded propaganda', 'Iran International propaganda',
        -- Anti-pressure framing
        'regime change war', 'imperial regime change',
        'foreign interference', 'foreign meddling',
        'foreign-instigated', 'foreign-instigated unrest',
        'rioters', 'Western-backed rioters',
        'fitnah', 'sedition',
        'color revolution', 'colour revolution',
        -- War / martyrdom framing
        'martyred', 'martyrdom', 'Sayyed',
        'Khamenei martyred', 'Imam Khamenei martyred',
        'Larijani martyred',
        'state terrorism', 'Israeli state terrorism',
        'war crimes against Iran', 'crimes against humanity Iran',
        -- Resilience
        'we will not bow', 'will not bow', 'will not surrender',
        'stronger after every blow', 'national unity', 'nation unites',
        'orderly succession', 'Assembly of Experts'
    ],
    ARRAY[
        'Iran', 'Iranian', 'Tehran',
        'Khamenei', 'Pezeshkian', 'Araghchi', 'Larijani',
        'Khomeini', 'Imam',
        'Islamic Republic', 'Supreme Leader',
        'IRGC', 'Pasdaran',
        'martyred', 'martyrdom'
    ],
    ARRAY[
        -- Iranian state media — always frame from this position
        'Press TV', 'IRNA', 'Fars News', 'Fars News Agency',
        'Tasnim News', 'Mehr News',
        -- Iran-aligned regional
        'Al Manar', 'Al Mayadeen'
    ],
    ARRAY[
        -- All publishers in this narrative are editorial organs
        'Press TV', 'IRNA', 'Fars News', 'Fars News Agency',
        'Tasnim News', 'Mehr News',
        'Al Manar', 'Al Mayadeen'
    ]
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- 3. friction_node_narratives links
-- ============================================================
INSERT INTO friction_node_narratives (fn_id, narrative_id, stance_label_en, stance_label_de, display_order) VALUES
    ('iran_regime_legitimacy_contest', 'west_iran_regime_change_doctrine',
        'Regime is illegitimate', 'Regime ist illegitim', 1),
    ('iran_regime_legitimacy_contest', 'iran_sovereign_existence',
        'Sovereign state under assault', 'Souveraener Staat unter Angriff', 2),
    ('iran_regime_legitimacy_contest', 'eu_diplomatic_preservation_norm',
        'Engage and criticise', 'Engagieren und kritisieren', 3),
    ('iran_regime_legitimacy_contest', 'multipolar_systemic_alternative',
        'Sovereignty principle', 'Souveraenitaetsprinzip', 4)
ON CONFLICT (fn_id, narrative_id) DO NOTHING;

COMMIT;

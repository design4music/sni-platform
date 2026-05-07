-- Friction Node: iran_proxy_network
-- 2026-05-07
--
-- Iran's regional armed-group network (Hezbollah / Hamas / Houthis /
-- Iraqi PMF / IRGC Quds Force) as the contested phenomenon. Two dominant
-- frames: terror infrastructure for Iranian regional projection (Israel-
-- US-Saudi) vs Axis of Resistance against Israeli/Western imperial
-- presence (Iran + allies + anti-Western coalition).
--
-- Adds:
--   1. friction_nodes row + event-title gate
--   2. Two NEW narratives:
--      - west_iran_proxy_network_threat (Israel-US-Saudi all-in)
--      - iran_axis_of_resistance (Iran all-in)
--   3. Re-uses two existing stand-by narratives:
--      - multipolar_systemic_alternative
--      - eu_diplomatic_preservation_norm
--   4. friction_node_narratives links with stance labels + display order

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
    'iran_proxy_network',
    'Iran regional proxy network',
    'Iranisches regionales Stellvertreter-Netzwerk',
    $D$Iran's network of allied armed groups across the Middle East — Hezbollah in Lebanon, Hamas in Gaza, the Houthis in Yemen, Iraqi PMF militias, and IRGC Quds Force operations — is the contested phenomenon. Western, Israeli and Saudi readings frame this as a centrally-directed terror infrastructure projecting Iranian power and threatening allied states. Iranian and anti-Western readings frame it as a legitimate Axis of Resistance against Israeli occupation of Palestinian and Lebanese territory and Western imperial presence in the region.$D$,
    $D$Irans Netzwerk verbuendeter bewaffneter Gruppen im Nahen Osten — Hisbollah im Libanon, Hamas in Gaza, die Huthis im Jemen, irakische PMF-Milizen und Operationen der IRGC-Quds-Truppe — ist das umstrittene Phaenomen. Westliche, israelische und saudische Lesarten rahmen dies als zentral gesteuerte Terror-Infrastruktur, die iranische Macht projiziert und verbuendete Staaten bedroht. Iranische und antiwestliche Lesarten rahmen es als legitime Achse des Widerstands gegen israelische Besatzung und westliche imperiale Praesenz.$D$,
    $D$Iran's regional military reach extends through allied armed groups across the Middle East. The contested phenomenon is whether this constitutes a centrally-directed terror infrastructure (the Western, Israeli and Saudi reading) or a legitimate Axis of Resistance against Israeli occupation and Western imperial presence (the Iranian and anti-Western reading). The contest has unfolded across multiple kinetic episodes: the 2006 Lebanon war, the Saudi-led intervention in Yemen since 2015, the 2024 Gaza war, the Houthi Red Sea attacks since 2023, and the wider 2025 and 2026 Israeli and American operations against Iranian assets and senior commanders. Through every escalation the framing remains: terror group needing destruction versus liberation movement needing protection. The narrative coalition is broader than for Iran's nuclear program — Western progressive solidarity with Palestinian and Lebanese civilians, pan-Arab and Muslim-world rhetoric of resistance, Russia and China amplifying anti-imperialist talking points, and the Gulf states hardening their position against Houthi attacks on their own infrastructure all enter the picture.$D$,
    $D$Irans regionale militaerische Reichweite erstreckt sich durch verbuendete bewaffnete Gruppen im Nahen Osten. Das umstrittene Phaenomen ist, ob dies eine zentral gesteuerte Terror-Infrastruktur darstellt (westliche, israelische und saudische Lesart) oder eine legitime Achse des Widerstands gegen israelische Besatzung und westliche imperiale Praesenz (iranische und antiwestliche Lesart). Der Konflikt entfaltete sich in mehreren kinetischen Episoden: Libanon-Krieg 2006, saudischer Jemen-Einsatz seit 2015, Gaza-Krieg 2024, Huthi-Angriffe im Roten Meer seit 2023 sowie die israelisch-amerikanischen Operationen 2025 und 2026 gegen iranische Vermoegenswerte und Kommandeure. Durch jede Eskalation bleibt die Rahmensetzung: Terrorgruppe, die zerstoert werden muss, gegen Befreiungsbewegung, die Schutz braucht. Die Narrativ-Koalition ist breiter als beim iranischen Atomprogramm — westliche progressive Solidaritaet mit palaestinensischen und libanesischen Zivilisten, panarabische und muslimische Widerstands-Rhetorik, Russland und China verstaerken antiimperialistische Argumente, und die Golfstaaten verhaerten ihre Position gegen Huthi-Angriffe auf eigene Infrastruktur.$D$,
    ARRAY['MIDEAST-IRAN', 'MIDEAST-ISRAEL', 'AMERICAS-USA', 'MIDEAST-SAUDI', 'MIDEAST-LEVANT', 'MIDEAST-PALESTINE', 'MIDEAST-YEMEN', 'MIDEAST-IRAQ'],
    ARRAY[
        'Hezbollah', 'Hamas', 'Houthis', 'Houthi',
        'IRGC', 'Quds Force', 'Quds',
        'Iraqi PMF', 'PMF', 'Hashd al-Shaabi',
        'Kataib Hezbollah', 'Asaib Ahl al-Haq', 'Badr Organization',
        'Iran-backed', 'Iran-aligned', 'Iran proxy', 'Iran-funded',
        'Axis of Resistance',
        'IRGC commander', 'Quds commander'
    ],
    -- Event-title gate: anchors-first (proxy group names alone qualify)
    -- plus Iran/Israel + topic words for ambiguous cases.
    ARRAY['Iran', 'Tehran', 'Israel', 'IDF', 'Saudi'],
    ARRAY['proxy', 'militia', 'terror', 'Axis of Resistance', 'Iran-backed', 'commander killed', 'commander assassin'],
    ARRAY[
        'Hezbollah', 'Hamas', 'Houthi', 'Houthis',
        'IRGC', 'Quds Force', 'Quds commander',
        'Iraqi PMF', 'Hashd al-Shaabi',
        'Kataib Hezbollah', 'Asaib Ahl al-Haq'
    ],
    2
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- 2a. NEW narrative: west_iran_proxy_network_threat
-- ============================================================
INSERT INTO narratives_v2 (
    id, name_en, name_de, claim_en, claim_de,
    actor_centroids, tier, narrative_type,
    framing_keywords, topic_keywords,
    publishers, editorial_organ_publishers
) VALUES (
    'west_iran_proxy_network_threat',
    'Western coalition: Iran proxy network as terror infrastructure',
    'Westliche Koalition: iranisches Stellvertreternetz als Terror-Infrastruktur',
    $D$The Israel-US-Saudi coalition describes the Iran-aligned regional armed-group network as an Iranian-directed "terror infrastructure". "Hezbollah" in Lebanon, "Hamas" in Gaza, the "Houthis" in Yemen, "Iraqi PMF" militias, "IRGC" Quds Force operations across the region — all are framed as proxies that Iran arms, funds, trains, and directs for power projection and attacks on allied states. Israeli operations in Gaza, the West Bank, southern Lebanon, and Syria are presented as "counterterrorism" and the legitimate exercise of "self-defence". Civilian casualties are attributed to groups using "human shields" in tunnels embedded under schools, hospitals, and residential blocks. US counter-Houthi air operations in the Red Sea and counter-PMF strikes in Iraq and Syria are framed identically. Saudi and UAE positioning has hardened markedly since the Houthi attacks on Saudi oil infrastructure and UAE air defences in 2025-2026. The narrative prescribes: sustained kinetic counterterrorism operations including assassinations of senior commanders (Soleimani, Mughniyeh, Nasrallah, Sinwar, Haniyeh, Khademi); foreign-terrorist-organisation designations; sanctions on the Iranian funding network and its banking facilitators; and rejection of any negotiation framework that legitimises these groups as political actors.$D$,
    $D$Die israelisch-amerikanisch-saudische Koalition beschreibt das iranisch ausgerichtete regionale Bewaffneten-Netz als iranisch gesteuerte "Terror-Infrastruktur". "Hisbollah" im Libanon, "Hamas" in Gaza, die "Huthis" im Jemen, "irakische PMF"-Milizen, Operationen der "IRGC"-Quds-Truppe — alle gerahmt als Stellvertreter, die Iran bewaffnet, finanziert, ausbildet und steuert. Israelische Operationen in Gaza, Westjordanland, Suedlibanon und Syrien gelten als "Terrorbekaempfung" und legitime "Selbstverteidigung". Zivile Opfer werden Gruppen zugeschrieben, die "menschliche Schutzschilde" in Tunneln unter Schulen, Krankenhaeusern und Wohnhaeusern nutzen. US-Operationen gegen Huthis im Roten Meer und gegen PMF-Stellungen in Irak und Syrien werden identisch gerahmt. Die saudische und emiratische Positionierung hat sich nach Huthi-Angriffen auf saudische Oel-Infrastruktur und VAE-Luftabwehr 2025-2026 deutlich verhaertet. Verschreibung: anhaltende kinetische Terrorbekaempfung einschliesslich Attentate auf Kommandeure (Soleimani, Mughniyeh, Nasrallah, Sinwar, Haniyeh, Khademi), FTO-Designierung der bewaffneten Gruppen, Sanktionen gegen das iranische Finanzierungsnetzwerk und Ablehnung jedes Verhandlungsrahmens, der diese Gruppen als politische Akteure legitimiert.$D$,
    ARRAY['AMERICAS-USA', 'MIDEAST-ISRAEL', 'MIDEAST-SAUDI'],
    'operational',
    'all_in',
    ARRAY[
        -- Doctrinal threat-frame vocabulary
        'terror infrastructure', 'Iran proxy network', 'Iran-backed', 'Iran-aligned',
        'human shields', 'self-defence', 'right to self-defence', 'right to defend',
        'counterterrorism', 'tunnel network', 'tunnel infrastructure',
        'FTO designation', 'foreign terrorist organisation',
        'terror financing', 'Iranian funding',
        -- Operational language for kinetic action
        'eliminated', 'commander eliminated', 'commander killed', 'targeted killing',
        'assassinated', 'assassination', 'crippled', 'degraded', 'dismantle',
        'destroy Hezbollah', 'destroy Hamas',
        -- Specific anchor vocabulary
        'October 7', 'Oct 7', 'Hamas attack', 'Hamas atrocity',
        'Iran-backed Houthi', 'Houthi attack', 'Houthi missile',
        'Soleimani', 'Mughniyeh', 'Nasrallah', 'Sinwar', 'Haniyeh', 'Khademi'
    ],
    ARRAY[
        'Hezbollah', 'Hamas', 'Houthi', 'Houthis',
        'IRGC', 'Quds', 'Iraqi PMF', 'PMF',
        'Lebanon strike', 'Lebanon war', 'Gaza war',
        'Red Sea attack', 'Red Sea shipping',
        'Iran-backed', 'Iran proxy'
    ],
    ARRAY[
        -- US (mainstream + conservative anti-Iran-proxy)
        'Fox News', 'Wall Street Journal', 'WSJ', 'New York Post',
        'CNN', 'New York Times', 'The New York Times',
        'Washington Post', 'The Washington Post',
        'Bloomberg', 'NPR', 'MSNBC', 'Associated Press',
        -- Israeli (uniformly anti-Iran-proxy)
        'Jerusalem Post', 'The Jerusalem Post', 'Times of Israel',
        'Haaretz', 'i24NEWS', 'JNS', 'Israel Hayom', 'Ynet',
        -- Saudi/UAE/Gulf — much stronger here than on nuclear because
        -- Houthi attacks on Gulf infrastructure are direct
        'Arab News', 'Saudi Gazette', 'Al Arabiya', 'Al Arabiya English',
        'Asharq Al-Awsat', 'The National', 'Khaleej Times', 'Gulf News',
        'WAM',
        -- Pro-Israel Western
        'Kyiv Post'
    ],
    ARRAY[]::text[]
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- 2b. NEW narrative: iran_axis_of_resistance
-- ============================================================
INSERT INTO narratives_v2 (
    id, name_en, name_de, claim_en, claim_de,
    actor_centroids, tier, narrative_type,
    framing_keywords, topic_keywords,
    publishers, editorial_organ_publishers
) VALUES (
    'iran_axis_of_resistance',
    'Iran-aligned: Axis of Resistance as legitimate liberation movement',
    'Iran-ausgerichtet: Achse des Widerstands als legitime Befreiungsbewegung',
    $D$Iran and its regional partners describe the network of allied armed groups as the "Axis of Resistance" — a legitimate "liberation" movement against Israeli "occupation" of Palestinian and Lebanese territory and against Western "imperial" presence in the region. Hezbollah is framed as Lebanon's defender against Israeli aggression and the only force that liberated southern Lebanon from Israeli occupation in 2000. Hamas is framed as the legitimate Palestinian resistance to occupation and the Gaza siege. The Houthis are framed as defenders of Yemen against Saudi and UAE aggression and as actors in solidarity with Palestinians under Israeli "genocide". The IRGC Quds Force, Iraqi PMF, and Syrian-aligned militias are framed as defenders of regional sovereignty against US "foreign occupation" — including the 28,500 US troops in Iraq and Syria and the 5,500 in Lebanon-region naval presence. Iranian state framing positions the support of these groups as a "moral duty" of solidarity with oppressed Muslims and as Iran's contribution to regional self-determination. Western and Israeli operations against the network — assassinations of commanders, drone strikes, the 2025-2026 escalation — are framed as "state terrorism" and "war crimes" against legitimate political-military actors. The narrative prescribes: continued material support to the network, refusal of any framework that designates these groups as terrorist, and political-diplomatic pressure for international recognition of Palestinian and Lebanese resistance rights.$D$,
    $D$Iran und seine regionalen Partner beschreiben das Netzwerk verbuendeter bewaffneter Gruppen als "Achse des Widerstands" — eine legitime "Befreiungs"-Bewegung gegen israelische "Besatzung" palaestinensischen und libanesischen Territoriums und gegen westliche "imperiale" Praesenz in der Region. Hisbollah wird als Verteidigerin Libanons gegen israelische Aggression gerahmt, als einzige Kraft, die den Suedlibanon 2000 von israelischer Besatzung befreite. Hamas wird als legitimer palaestinensischer Widerstand gegen Besatzung und Gaza-Belagerung gerahmt. Die Huthis werden als Verteidiger Jemens gegen saudische und emiratische Aggression sowie als Solidaritaets-Akteure mit Palaestinensern unter israelischem "Genozid" gerahmt. Die IRGC-Quds-Truppe, irakische PMF und syrisch-ausgerichtete Milizen gelten als Verteidiger regionaler Souveraenitaet gegen US-"Fremdbesatzung". Iranische Rahmensetzung positioniert die Unterstuetzung dieser Gruppen als "moralische Pflicht" der Solidaritaet mit unterdrueckten Muslimen. Westliche und israelische Operationen — Attentate auf Kommandeure, Drohnenschlaege, die Eskalation 2025-2026 — werden als "Staatsterrorismus" und "Kriegsverbrechen" gegen legitime politisch-militaerische Akteure gerahmt. Verschreibung: fortgesetzte materielle Unterstuetzung des Netzwerks, Ablehnung jedes Rahmens, der diese Gruppen als terroristisch designiert, und politisch-diplomatischer Druck fuer internationale Anerkennung palaestinensischer und libanesischer Widerstandsrechte.$D$,
    ARRAY['MIDEAST-IRAN', 'MIDEAST-LEVANT', 'MIDEAST-PALESTINE', 'MIDEAST-YEMEN'],
    'ideological',
    'all_in',
    ARRAY[
        -- Resistance-frame vocabulary
        'Axis of Resistance', 'legitimate resistance', 'legitimate liberation',
        'liberation movement', 'liberation struggle',
        'foreign occupation', 'Israeli occupation', 'Israeli aggression',
        'Western imperial', 'Western imperialism', 'imperial presence',
        'occupation forces', 'occupying power',
        -- Solidarity vocabulary
        'moral duty', 'solidarity with Palestine', 'solidarity with Palestinians',
        'oppressed Muslims', 'oppressed peoples',
        'martyred', 'martyr', 'martyrdom',
        -- Anti-Western reframing of Western action
        'state terrorism', 'state-sponsored terrorism', 'Israeli state terrorism',
        'war crimes', 'crimes against humanity',
        'assassinated', 'targeted killing illegal',
        -- Specific actor vocabulary as resistance
        'Hezbollah resistance', 'Hamas resistance', 'Yemeni resistance',
        'Houthi solidarity', 'Yemen solidarity with Palestine',
        'Nasrallah martyred', 'Soleimani martyred', 'Sinwar martyred'
    ],
    ARRAY[
        'Hezbollah', 'Hamas', 'Houthi', 'Houthis', 'IRGC', 'Quds',
        'Iran proxy', 'Iran-backed',
        'resistance', 'resistance group', 'resistance front',
        'Khamenei', 'Pezeshkian', 'Nasrallah', 'Soleimani', 'Sinwar', 'Haniyeh',
        'Lebanon', 'Gaza', 'Yemen', 'Palestine'
    ],
    ARRAY[
        -- Iranian state media — always frames from this position
        'Press TV', 'IRNA', 'Fars News', 'Fars News Agency',
        'Tasnim News', 'Mehr News',
        -- Hezbollah-aligned Lebanese / Pan-Arab resistance media
        'Al Manar', 'Al Mayadeen',
        -- Pan-Arab independents that broadly carry the resistance frame
        'Middle East Eye'
    ],
    ARRAY[
        -- All listed publishers are editorial organs for this narrative
        -- (state-aligned or movement-aligned, intrinsic stance).
        'Press TV', 'IRNA', 'Fars News', 'Fars News Agency',
        'Tasnim News', 'Mehr News',
        'Al Manar', 'Al Mayadeen',
        'Middle East Eye'
    ]
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- 3. friction_node_narratives links with stance labels
-- ============================================================
INSERT INTO friction_node_narratives (fn_id, narrative_id, stance_label_en, stance_label_de, display_order) VALUES
    ('iran_proxy_network', 'west_iran_proxy_network_threat',
        'Terror infrastructure', 'Terror-Infrastruktur', 1),
    ('iran_proxy_network', 'iran_axis_of_resistance',
        'Legitimate resistance', 'Legitimer Widerstand', 2),
    ('iran_proxy_network', 'eu_diplomatic_preservation_norm',
        'Preserve diplomacy', 'Diplomatie bewahren', 3),
    ('iran_proxy_network', 'multipolar_systemic_alternative',
        'Anti-imperialist solidarity', 'Antiimperialistische Solidaritaet', 4)
ON CONFLICT (fn_id, narrative_id) DO NOTHING;

COMMIT;

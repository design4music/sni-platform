-- Friction Nodes: strait_of_hormuz_sovereignty + gulf_attacks_on_arab_states
--                + iran_theater (theater grouping)
-- 2026-05-08
--
-- Two new atomic FNs completing the Iran cluster + a theater entity that
-- bundles all five Iran-cluster FNs as one map-marker equivalent.
--
-- FN5: strait_of_hormuz_sovereignty
--   Phenomenon framing per user 2026-05-08: not just maritime sovereignty
--   but specifically the asymmetric leverage Iran holds over global
--   trade — "Iran can make the world see what it usually can ignore".
--
-- FN6: gulf_attacks_on_arab_states
--   Phenomenon framing per user: Iran's asymmetric military response
--   hitting US bases / embassies / Saudi-UAE infrastructure. US stays
--   in the all-in coalition because their bases and embassies are
--   targeted (this is the asymmetric retaliation logic exposed).
--
-- FN7 (theater): iran_theater
--   member_fn_ids = the 5 atomic Iran FNs. No matching fields (theaters
--   don't match events directly — they aggregate their atomic members').

BEGIN;

-- ============================================================
-- FN5: strait_of_hormuz_sovereignty
-- ============================================================
INSERT INTO friction_nodes (
    id, fn_type, name_en, name_de,
    description_en, description_de,
    editorial_summary_en, editorial_summary_de,
    centroid_ids, topic_keywords,
    event_actor_markers, event_topic_markers, event_title_anchors,
    display_order
) VALUES (
    'strait_of_hormuz_sovereignty',
    'atomic',
    'Strait of Hormuz: sovereignty and asymmetric leverage',
    'Strasse von Hormuz: Souveraenitaet und asymmetrische Hebelwirkung',
    $D$The Strait of Hormuz is one of the most consequential maritime chokepoints in the world: roughly a fifth of global oil flows through it. The contested phenomenon is not just sovereignty over the strait, but the asymmetric leverage Iran holds — the threat of closure or maritime disruption forces the wider world to pay attention to a security file most actors would otherwise be content to ignore. The 2025-2026 escalation amplified this to a crisis point: tanker incidents, naval escort missions, US Fifth Fleet deployments, Chinese diplomatic engagement, and Iranian threats to close the strait all live here.$D$,
    $D$Die Strasse von Hormuz ist einer der folgenreichsten maritimen Engpaesse der Welt: etwa ein Fuenftel des globalen Oelflusses passiert sie. Das umstrittene Phaenomen ist nicht nur die Souveraenitaet ueber die Strasse, sondern die asymmetrische Hebelwirkung, die Iran ausuebt — die Drohung einer Schliessung oder maritimen Stoerung zwingt die Welt, einer Sicherheitsfrage Aufmerksamkeit zu schenken, die viele sonst lieber ignorieren wuerden. Die Eskalation 2025-2026 verschaerfte dies zur Krise: Tankerzwischenfaelle, Marine-Eskorten, US-Fuenfte-Flotte-Stationierungen, chinesisches diplomatisches Engagement und iranische Drohungen zur Schliessung leben hier alle.$D$,
    $D$The Strait of Hormuz contest is the clearest case in the Iran cluster of how asymmetric power works in the modern strategic system. Iran cannot match US naval power conventionally; what it can do is generate uncertainty over a chokepoint global trade depends on. Every threatened closure, every harassed tanker, every Iranian Revolutionary Guard speedboat sortie sends prices up at gas stations from California to Tokyo. The Western and Gulf reading frames freedom of navigation as a non-negotiable rule of the international system that Iran has no right to weaponise; a multinational maritime force, US Fifth Fleet escort missions, and UNCLOS provisions on international straits are the prescribed defence. The Iranian reading frames the strait as Iranian territorial waters, the threat of closure as legitimate deterrence asymmetry against superior conventional powers, and the foreign naval presence as exactly the imperial overreach Iran is defending against. China's increasing diplomatic engagement (it is now the largest buyer of Iranian crude) introduces a third position: stability over confrontation, with quiet pressure on Tehran to keep the strait open without endorsing the US enforcement model.$D$,
    $D$Der Konflikt um die Strasse von Hormuz ist der deutlichste Fall im Iran-Cluster, wie asymmetrische Macht im modernen strategischen System wirkt. Iran kann US-Marinemacht konventionell nicht matchen; was es kann, ist Unsicherheit ueber einen Engpass erzeugen, von dem der globale Handel abhaengt. Jede angedrohte Schliessung, jeder bedrangte Tanker, jeder Schnellboot-Vorstoss der Revolutionsgarde treibt Spritpreise von Kalifornien bis Tokio. Die westliche und Golf-Lesart rahmt Freiheit der Navigation als nicht verhandelbare Regel des internationalen Systems, die Iran nicht bewaffnen darf; eine multinationale Maritime-Streitmacht, US-Fuenfte-Flotte-Eskorten und UNCLOS-Bestimmungen ueber internationale Meerengen sind die vorgeschriebene Verteidigung. Die iranische Lesart rahmt die Strasse als iranische Territorialgewaesser, die Schliessungsdrohung als legitime Abschreckungsasymmetrie gegen ueberlegene konventionelle Maechte und die fremde Marinepraesenz als genau die imperiale Anmassung, gegen die Iran sich verteidigt. Chinas zunehmendes diplomatisches Engagement fuehrt eine dritte Position ein: Stabilitaet vor Konfrontation, mit leisem Druck auf Teheran, die Strasse offen zu halten, ohne das US-Durchsetzungsmodell zu billigen.$D$,
    ARRAY['MIDEAST-IRAN', 'AMERICAS-USA', 'EUROPE-UK', 'EUROPE-FRANCE', 'MIDEAST-SAUDI', 'ASIA-CHINA'],
    ARRAY[
        'Strait of Hormuz', 'Hormuz strait', 'Hormuz', 'Hormuz blockade',
        'Hormuz crisis', 'Hormuz chokepoint',
        'Persian Gulf chokepoint', 'Persian Gulf shipping',
        'Iran tanker', 'tanker harassment', 'tanker seized', 'tanker attack',
        'IRGC navy', 'IRGC speedboat',
        'Fifth Fleet', 'US Fifth Fleet',
        'freedom of navigation', 'maritime escort',
        'multinational maritime force', 'naval escort'
    ],
    ARRAY['Iran', 'IRGC', 'US', 'United States', 'UK', 'British'],
    -- Topic markers tightened: 'ship' alone matches "showmanship", 'oil'
    -- alone matches unrelated headlines. Keep specific Hormuz-relevant
    -- words.
    ARRAY['strait', 'shipping lane', 'maritime', 'tanker', 'naval', 'chokepoint', 'escort'],
    ARRAY['Strait of Hormuz', 'Hormuz', 'Persian Gulf chokepoint',
          'Fifth Fleet', 'US Fifth Fleet'],
    4
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- FN5 narratives (2 new + 2 reused)
-- ============================================================

-- west_hormuz_freedom_of_navigation
INSERT INTO narratives_v2 (
    id, name_en, name_de, claim_en, claim_de,
    actor_centroids, tier, narrative_type,
    framing_keywords, topic_keywords,
    publishers, editorial_organ_publishers
) VALUES (
    'west_hormuz_freedom_of_navigation',
    'Western coalition: free passage through Hormuz is non-negotiable',
    'Westliche Koalition: freie Durchfahrt durch Hormuz ist nicht verhandelbar',
    $D$The US-UK-France-Saudi-UAE coalition describes the Strait of Hormuz as an "international strait" governed by UNCLOS, through which "freedom of navigation" must be guaranteed regardless of Iranian sovereignty claims. Iranian harassment of tankers, IRGC speedboat sorties, and threats of closure are framed as illegal under international maritime law and as "weaponisation" of a global commons. The US "Fifth Fleet" headquartered in Bahrain, the periodic UK-French-led "multinational maritime force" deployments, and "naval escort" missions for tankers are framed as the legitimate defence of an order on which the world economy depends. The narrative explicitly refuses to recognise any Iranian veto over commercial passage: any Iranian closure attempt is treated as an act of war justifying military response. The narrative prescribes: persistent multinational naval presence, regular freedom-of-navigation operations through Iranian-claimed waters, designation of IRGC naval forces as terrorist when they harass commercial shipping, and pre-positioned military response options for any closure attempt.$D$,
    $D$Die US-UK-Frankreich-Saudi-VAE-Koalition beschreibt die Strasse von Hormuz als "internationale Meerenge" unter UNCLOS, durch die "Freiheit der Navigation" garantiert sein muss, unabhaengig von iranischen Souveraenitaetsansprueche. Iranische Tanker-Belaestigung, IRGC-Schnellboot-Vorstoesse und Schliessungsdrohungen gelten als illegal unter Seerecht und als "Bewaffnung" eines globalen Allmendeguts. Die in Bahrain stationierte US-"Fuenfte Flotte", die periodischen UK-franzoesisch gefuehrten "multinationalen Maritime-Streitkraft"-Stationierungen und "Marine-Eskorten" fuer Tanker gelten als legitime Verteidigung einer Ordnung, von der die Weltwirtschaft abhaengt. Verschreibung: anhaltende multinationale Marinepraesenz, regelmaessige Freedom-of-Navigation-Operationen durch von Iran beanspruchte Gewaesser, FTO-Designierung der IRGC-Marine bei Belaestigung kommerzieller Schifffahrt, vorbereitete militaerische Reaktion auf Schliessungsversuche.$D$,
    ARRAY['AMERICAS-USA', 'EUROPE-UK', 'EUROPE-FRANCE', 'MIDEAST-SAUDI'],
    'operational',
    'all_in',
    ARRAY[
        'freedom of navigation', 'free passage', 'free shipping',
        'international strait', 'UNCLOS', 'global commons',
        'Fifth Fleet', 'US Fifth Fleet',
        'multinational maritime force', 'naval escort',
        'maritime coalition', 'NATO maritime',
        'weaponisation of', 'weaponize the strait',
        'cannot close', 'must remain open',
        'global trade', 'energy security',
        'oil chokepoint', 'global oil supply',
        'IRGC harassment', 'tanker harassment',
        'rules-based maritime order',
        'freedom of navigation operations', 'FONOPs',
        'right to defend shipping'
    ],
    ARRAY[
        'Strait of Hormuz', 'Hormuz', 'Persian Gulf',
        'Iran tanker', 'IRGC navy', 'Fifth Fleet',
        'tanker', 'shipping', 'oil chokepoint'
    ],
    ARRAY[
        'Fox News', 'Wall Street Journal', 'WSJ', 'New York Post',
        'CNN', 'New York Times', 'The New York Times',
        'Washington Post', 'The Washington Post',
        'Bloomberg', 'NPR', 'MSNBC', 'Associated Press', 'Reuters',
        'Jerusalem Post', 'The Jerusalem Post', 'Times of Israel',
        'Haaretz', 'i24NEWS', 'JNS', 'Israel Hayom', 'Ynet',
        'Arab News', 'Saudi Gazette', 'Al Arabiya', 'Al Arabiya English',
        'Asharq Al-Awsat', 'The National', 'Khaleej Times', 'Gulf News',
        'BBC', 'BBC World', 'The Guardian', 'Financial Times',
        'Le Figaro', 'France 24', 'France 24 (EN)'
    ],
    ARRAY[]::text[]
) ON CONFLICT (id) DO NOTHING;

-- iran_hormuz_sovereign_pressure
INSERT INTO narratives_v2 (
    id, name_en, name_de, claim_en, claim_de,
    actor_centroids, tier, narrative_type,
    framing_keywords, topic_keywords,
    publishers, editorial_organ_publishers
) VALUES (
    'iran_hormuz_sovereign_pressure',
    'Iran: Hormuz as sovereign waters and deterrence asymmetry',
    'Iran: Hormuz als souveraene Gewaesser und Abschreckungsasymmetrie',
    $D$Iran describes the Strait of Hormuz as Iranian "sovereign waters" — territorial waters extending from Iran's southern coast — over which Iran has full legal authority. The threat of closure is framed not as an outlaw act but as Iran's "deterrence asymmetry" — the only credible counter to overwhelming US naval superiority and the imperial pressure regime against Iran. The "IRGC navy" patrols its own coast; foreign warships in the strait are characterised as "foreign occupation" of the Persian Gulf. The vocabulary of "global oil supply" and "free passage" is reframed as Western leverage masquerading as principle: the strait stays open because Iran chooses not to close it, not because the US Fifth Fleet enforces openness. Iran can shut the chokepoint within hours if pushed beyond a red line — and that capability is precisely what makes US-Israeli aggression deterred at the margin. The narrative prescribes: continued IRGC naval presence, periodic demonstrations of closure capability (the "30-second close" exercises), maintenance of asymmetric tools (anti-ship missiles, naval mines, fast-attack craft, drone swarms), and explicit framing of any US enforcement as casus belli.$D$,
    $D$Iran beschreibt die Strasse von Hormuz als iranische "souveraene Gewaesser" — Territorialgewaesser, die sich von Irans Suedkueste erstrecken — ueber die Iran volle rechtliche Autoritaet hat. Die Schliessungsdrohung wird nicht als Gesetzlosigkeit gerahmt, sondern als Irans "Abschreckungsasymmetrie" — die einzige glaubwuerdige Gegenmacht zu ueberwaeltigender US-Marineueberlegenheit und dem imperialen Druckregime gegen Iran. Die "IRGC-Marine" patrouilliert ihre eigene Kueste; fremde Kriegsschiffe in der Strasse gelten als "fremde Besatzung" des Persischen Golfs. Vokabular von "globaler Oelversorgung" und "freier Durchfahrt" wird als westliche Hebelwirkung umgedeutet, die sich als Prinzip ausgibt: die Strasse bleibt offen, weil Iran sie nicht schliesst, nicht weil die US-Fuenfte-Flotte Offenheit erzwingt. Iran kann den Engpass innerhalb von Stunden schliessen, wenn ueber eine rote Linie hinaus gedraengt — und diese Faehigkeit ist genau das, was US-israelische Aggression am Rand abschreckt. Verschreibung: anhaltende IRGC-Marinepraesenz, periodische Demonstrationen der Schliessungsfaehigkeit, asymmetrische Werkzeuge (Anti-Schiffs-Raketen, Seeminen, Schnellangriff-Boote, Drohnenschwaerme), und Rahmung jeder US-Durchsetzung als Casus Belli.$D$,
    ARRAY['MIDEAST-IRAN'],
    'ideological',
    'all_in',
    ARRAY[
        'sovereign waters', 'Iranian territorial waters', 'Iranian waters',
        'deterrence asymmetry', 'asymmetric deterrence',
        'IRGC navy', 'IRGC maritime',
        'Persian Gulf is Iranian',
        'foreign occupation Persian Gulf', 'foreign warships',
        'Hormuz is ours', 'closure capability',
        'red line', 'cross the red line',
        'imperial pressure regime',
        'Western maritime hegemony',
        'within hours', 'in hours we can close',
        'naval mines', 'fast attack craft', 'drone swarm',
        'anti-ship missile', 'Persian Gulf defenders'
    ],
    ARRAY[
        'Strait of Hormuz', 'Hormuz', 'Persian Gulf',
        'IRGC', 'IRGC navy', 'Tangsiri',
        'Khamenei', 'Pezeshkian', 'Iranian Navy'
    ],
    ARRAY[
        'Press TV', 'IRNA', 'Fars News', 'Fars News Agency',
        'Tasnim News', 'Mehr News',
        'Al Manar', 'Al Mayadeen'
    ],
    ARRAY[
        'Press TV', 'IRNA', 'Fars News', 'Fars News Agency',
        'Tasnim News', 'Mehr News',
        'Al Manar', 'Al Mayadeen'
    ]
) ON CONFLICT (id) DO NOTHING;

-- FN5 narrative links
INSERT INTO friction_node_narratives (fn_id, narrative_id, stance_label_en, stance_label_de, display_order) VALUES
    ('strait_of_hormuz_sovereignty', 'west_hormuz_freedom_of_navigation',
        'Free passage non-negotiable', 'Freie Durchfahrt nicht verhandelbar', 1),
    ('strait_of_hormuz_sovereignty', 'iran_hormuz_sovereign_pressure',
        'Sovereign waters and deterrence', 'Souveraene Gewaesser und Abschreckung', 2),
    ('strait_of_hormuz_sovereignty', 'eu_diplomatic_preservation_norm',
        'Preserve diplomacy', 'Diplomatie bewahren', 3),
    ('strait_of_hormuz_sovereignty', 'multipolar_systemic_alternative',
        'Anti-imperial maritime sovereignty', 'Anti-imperiale maritime Souveraenitaet', 4)
ON CONFLICT (fn_id, narrative_id) DO NOTHING;


-- ============================================================
-- FN6: gulf_attacks_on_arab_states
-- ============================================================
INSERT INTO friction_nodes (
    id, fn_type, name_en, name_de,
    description_en, description_de,
    editorial_summary_en, editorial_summary_de,
    centroid_ids, topic_keywords,
    event_actor_markers, event_topic_markers, event_title_anchors,
    display_order
) VALUES (
    'gulf_attacks_on_arab_states',
    'atomic',
    'Iranian and Houthi strikes on Gulf states and US presence',
    'Iranische und Huthi-Angriffe auf Golfstaaten und US-Praesenz',
    $D$Iranian and Houthi strikes on Saudi Arabia, the United Arab Emirates, and US bases / embassies in the Gulf are the contested phenomenon. The 2019 Aramco strike, the 2022 UAE attacks, the 2025-2026 escalated Houthi-and-Iranian-direct strikes on Gulf oil infrastructure and the Al Udeid / Al Asad / other US bases all live here. The contest is over whether such asymmetric strikes constitute legitimate retaliation against states complicit in Israeli/American operations against Iran, or state-sponsored aggression against sovereign states that demands accountability and response.$D$,
    $D$Iranische und Huthi-Angriffe auf Saudi-Arabien, die Vereinigten Arabischen Emirate und US-Basen / -Botschaften am Golf sind das umstrittene Phaenomen. Der Aramco-Angriff 2019, die VAE-Angriffe 2022, die eskalierten Huthi-und-iranisch-direkten Angriffe 2025-2026 auf Golf-Oel-Infrastruktur und die US-Basen Al Udeid / Al Asad und andere — alle leben hier. Der Konflikt geht darum, ob solche asymmetrischen Schlaege legitime Vergeltung gegen Staaten darstellen, die an israelischen/amerikanischen Operationen gegen Iran komplizenhaft sind, oder staatlich gesponserte Aggression gegen souveraene Staaten, die Rechenschaft und Reaktion erfordert.$D$,
    $D$The Gulf-attacks contest is the place where Iran's asymmetric military doctrine becomes visible to the wider world. Iran cannot fight US naval and air power conventionally; what it can do is hit US bases, US embassies, and the Gulf states whose territory hosts US presence. The 2019 Aramco strike took 5% of global oil supply offline overnight and demonstrated Iranian missile-and-drone reach against the most heavily-defended air-defence networks in the region. The 2025-2026 escalation extended this logic across multiple targets: Iranian and Houthi strikes on Saudi pipelines, UAE air-defence systems, US Al Udeid base in Qatar, US bases in Iraq and Syria. The Western and Gulf reading frames these strikes as state-sponsored aggression against sovereign nations and US service members; the response framework is sanctions, military retaliation, and international condemnation. The Iranian and Houthi reading frames them as legitimate retaliation: Saudi Arabia and the UAE host US forces actively striking Iran, and the US bases in the region are the launch points for those operations. Under that logic, the bases and the host states are legitimate targets for asymmetric response — a response proportionate to the disproportionate conventional advantage the other side enjoys.$D$,
    $D$Der Gulf-Angriffe-Konflikt ist die Stelle, wo Irans asymmetrische Militaerdoktrin fuer die weitere Welt sichtbar wird. Iran kann US-Marine- und -Luftmacht konventionell nicht bekaempfen; was es kann, ist US-Basen, US-Botschaften und die Golfstaaten treffen, deren Territorium US-Praesenz beherbergt. Der Aramco-Angriff 2019 nahm ueber Nacht 5% der globalen Oelversorgung offline und demonstrierte iranische Raketen-und-Drohnen-Reichweite gegen die am schwersten verteidigten Luftabwehrnetze der Region. Die Eskalation 2025-2026 erweiterte diese Logik ueber mehrere Ziele: iranische und Huthi-Angriffe auf saudische Pipelines, VAE-Luftabwehrsysteme, US-Al-Udeid-Basis in Katar, US-Basen in Irak und Syrien. Die westliche und Golf-Lesart rahmt diese Schlaege als staatlich gesponserte Aggression gegen souveraene Nationen und US-Soldaten; der Reaktionsrahmen ist Sanktionen, militaerische Vergeltung, internationale Verurteilung. Die iranische und Huthi-Lesart rahmt sie als legitime Vergeltung: Saudi-Arabien und die VAE beherbergen US-Streitkraefte, die aktiv Iran angreifen, und die US-Basen in der Region sind die Startpunkte fuer diese Operationen. Unter dieser Logik sind die Basen und die Gaststaaten legitime Ziele fuer asymmetrische Reaktion.$D$,
    ARRAY['MIDEAST-IRAN', 'MIDEAST-ISRAEL', 'AMERICAS-USA', 'MIDEAST-SAUDI', 'MIDEAST-YEMEN'],
    ARRAY[
        'Aramco strike', 'Aramco attack', 'Saudi Aramco',
        'Abqaiq', 'Khurais',
        'UAE attack', 'UAE intercepts', 'UAE air defence', 'UAE air defences',
        'Al Udeid', 'Al Asad', 'US base in Iraq', 'US base in Syria',
        'US embassy', 'US bases',
        'Iranian missile', 'Iranian drone', 'Iranian missile attack',
        'Houthi missile', 'Houthi drone', 'Houthi attack',
        'asymmetric retaliation', 'asymmetric strike',
        'Saudi oil infrastructure', 'Saudi pipeline',
        'attacks on Saudi', 'attacks on UAE',
        'Iran-backed Houthi'
    ],
    ARRAY['Iran', 'Iranian', 'IRGC', 'Houthi', 'Houthis'],
    ARRAY['attack', 'strike', 'missile', 'drone', 'air defence',
          'air defense', 'oil infrastructure', 'base', 'embassy',
          'pipeline', 'refinery'],
    ARRAY[
        'Aramco', 'Abqaiq', 'Khurais',
        'Al Udeid', 'Al Asad',
        'UAE air defences', 'UAE air defense',
        'Houthi attack', 'Houthi missile', 'Houthi drone'
    ],
    5
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- FN6 narratives (2 new + reuse iran_axis_of_resistance + EU + multipolar)
-- ============================================================

-- west_gulf_aggression_response
INSERT INTO narratives_v2 (
    id, name_en, name_de, claim_en, claim_de,
    actor_centroids, tier, narrative_type,
    framing_keywords, topic_keywords,
    publishers, editorial_organ_publishers
) VALUES (
    'west_gulf_aggression_response',
    'US-Israel-Saudi-UAE: Iranian and Houthi strikes are state-sponsored aggression',
    'US-Israel-Saudi-VAE: iranische und Huthi-Schlaege sind staatlich gesponserte Aggression',
    $D$The US-Israel-Saudi-UAE coalition describes the Iranian and Houthi strikes on Gulf states and US presence as "state-sponsored aggression" against sovereign nations. The 2019 Aramco strike, the 2022 UAE attacks, the 2025-2026 strikes on Saudi pipelines, UAE air-defence systems, and US bases are framed as Iran-directed acts of war that demand accountability. US service members killed at Tower 22, at Al Udeid, at Al Asad — each death is framed as an unacceptable cost requiring proportionate response. Saudi Arabia and the UAE are framed as victims of Iranian terror — sovereign Arab states attacked on their own territory by Iranian-backed forces. Houthi attacks on Saudi airspace and oil infrastructure are framed not as Yemeni civil war but as Iranian regional projection through proxy. The narrative explicitly rejects the asymmetric-deterrence framing as moral equivalence: hosting US bases is not complicity, and US-Israeli operations against Iran do not justify Iranian retaliation against third parties. The narrative prescribes: military retaliation against Iranian and Houthi leadership and capability, sustained sanctions on Iranian missile and drone programs, FTO designation of the Houthi movement, and integrated Gulf-Israeli air-defence cooperation as a force multiplier.$D$,
    $D$Die US-Israel-Saudi-VAE-Koalition beschreibt die iranischen und Huthi-Schlaege auf Golfstaaten und US-Praesenz als "staatlich gesponserte Aggression" gegen souveraene Nationen. Der Aramco-Angriff 2019, die VAE-Angriffe 2022, die Schlaege 2025-2026 auf saudische Pipelines, VAE-Luftabwehrsysteme und US-Basen werden als iranisch gesteuerte Kriegsakte gerahmt, die Rechenschaft erfordern. US-Soldaten, getoetet bei Tower 22, Al Udeid, Al Asad — jeder Tod ist ein inakzeptabler Preis, der verhaeltnismaessige Antwort erfordert. Saudi-Arabien und die VAE werden als Opfer iranischen Terrors gerahmt. Huthi-Angriffe auf saudischen Luftraum und Oel-Infrastruktur gelten nicht als jemenitischer Buergerkrieg, sondern als iranische regionale Projektion durch Stellvertreter. Das Narrativ lehnt die asymmetrische-Abschreckungs-Rahmung als moralische Aequivalenz ab: das Beherbergen von US-Basen ist keine Komplizenschaft, und US-israelische Operationen gegen Iran rechtfertigen keine iranische Vergeltung gegen Dritte. Verschreibung: militaerische Vergeltung gegen iranische und Huthi-Fuehrung und -Faehigkeit, anhaltende Sanktionen auf iranische Raketen- und Drohnenprogramme, FTO-Designierung der Huthi-Bewegung, und integrierte Golf-israelische Luftabwehrkooperation als Kraftmultiplikator.$D$,
    ARRAY['AMERICAS-USA', 'MIDEAST-ISRAEL', 'MIDEAST-SAUDI'],
    'operational',
    'all_in',
    ARRAY[
        'state-sponsored aggression', 'state-sponsored attack',
        'Iranian aggression', 'Iranian state-sponsored',
        'attack on sovereign nation', 'attack on sovereign Arab',
        'sovereign Arab states attacked',
        'US service members killed', 'service members killed',
        'Tower 22', 'Al Udeid', 'Al Asad', 'attack on US base',
        'attack on US embassy',
        'unacceptable cost', 'demands response', 'demands accountability',
        'proportionate response', 'must be held accountable',
        'Iranian terror', 'Iran-backed terror',
        'Iranian regional projection', 'projection through proxy',
        'integrated air defence', 'Saudi-Israeli cooperation',
        'FTO designation Houthi',
        'Houthi terror', 'Houthi aggression',
        'Aramco strike', 'attacks on Saudi infrastructure',
        'attacks on UAE'
    ],
    ARRAY[
        'Iran', 'Iranian', 'IRGC', 'Houthi', 'Houthis',
        'Saudi', 'Saudi Arabia', 'Aramco', 'UAE', 'Emirates',
        'Al Udeid', 'Al Asad', 'Tower 22',
        'US base', 'US embassy', 'attack', 'strike'
    ],
    ARRAY[
        'Fox News', 'Wall Street Journal', 'WSJ', 'New York Post',
        'CNN', 'New York Times', 'The New York Times',
        'Washington Post', 'The Washington Post',
        'Bloomberg', 'NPR', 'MSNBC', 'Associated Press', 'Reuters',
        'Jerusalem Post', 'The Jerusalem Post', 'Times of Israel',
        'Haaretz', 'i24NEWS', 'JNS', 'Israel Hayom', 'Ynet',
        'Arab News', 'Saudi Gazette', 'Al Arabiya', 'Al Arabiya English',
        'Asharq Al-Awsat', 'The National', 'Khaleej Times', 'Gulf News',
        'WAM', 'Kyiv Post'
    ],
    ARRAY[]::text[]
) ON CONFLICT (id) DO NOTHING;

-- iran_asymmetric_retaliation_doctrine
INSERT INTO narratives_v2 (
    id, name_en, name_de, claim_en, claim_de,
    actor_centroids, tier, narrative_type,
    framing_keywords, topic_keywords,
    publishers, editorial_organ_publishers
) VALUES (
    'iran_asymmetric_retaliation_doctrine',
    'Iran and allies: asymmetric retaliation against complicit states is legitimate',
    'Iran und Verbuendete: asymmetrische Vergeltung gegen komplizenhafte Staaten ist legitim',
    $D$Iran and the Houthis describe their strikes on Saudi Arabia, the UAE, and US bases as "legitimate retaliation" — a proportionate asymmetric response to disproportionate conventional aggression. Saudi Arabia and the UAE are framed as "complicit Gulf states" whose territory hosts US forces actively striking Iran, Lebanon, and Yemen; under this framing, those states are not innocent third parties but active participants in the regional war on resistance. US bases in the region — Al Udeid, Al Asad, Camp Arifjan, the Fifth Fleet headquarters — are framed as the "launch points" for Western aggression and therefore legitimate targets. Houthi missile and drone attacks on Saudi oil infrastructure are framed as "Yemeni resistance" plus "Palestine solidarity" — punishing Saudi participation in the Yemen war and forcing the world to feel the cost of supporting Israeli operations in Gaza. The asymmetric calculus is explicit: Iran cannot match US conventional power, so it must impose costs at the points where the West is exposed. Targeting Aramco's Abqaiq facility removed 5% of global oil supply overnight in 2019; that capability is precisely the deterrent the West has tried to deny Iran for decades. The narrative prescribes: continued asymmetric strikes calibrated to deterrence (not full-scale war), Houthi Red Sea pressure to economically punish Israeli supporters, IRGC and Quds Force operations against US bases, and explicit messaging that any escalation by the West will be answered at higher cost.$D$,
    $D$Iran und die Huthis beschreiben ihre Schlaege auf Saudi-Arabien, die VAE und US-Basen als "legitime Vergeltung" — eine verhaeltnismaessige asymmetrische Antwort auf unverhaeltnismaessige konventionelle Aggression. Saudi-Arabien und die VAE werden als "komplizenhafte Golfstaaten" gerahmt, deren Territorium US-Streitkraefte beherbergt, die aktiv Iran, Libanon und Jemen angreifen; unter dieser Rahmung sind diese Staaten nicht unschuldige Dritte, sondern aktive Teilnehmer am regionalen Krieg gegen den Widerstand. US-Basen in der Region — Al Udeid, Al Asad, Camp Arifjan, das Fuenfte-Flotte-Hauptquartier — gelten als "Startpunkte" fuer westliche Aggression und damit legitime Ziele. Huthi-Raketen- und Drohnenangriffe auf saudische Oel-Infrastruktur gelten als "jemenitischer Widerstand" plus "Palestina-Solidaritaet". Die asymmetrische Logik ist explizit: Iran kann US-konventionelle Macht nicht matchen, also muss es Kosten an den Punkten verursachen, wo der Westen exponiert ist. Verschreibung: fortgesetzte asymmetrische Schlaege, Huthi-Druck im Roten Meer, IRGC- und Quds-Truppe-Operationen gegen US-Basen, explizite Botschaft, dass Eskalation zu hoeheren Kosten beantwortet wird.$D$,
    ARRAY['MIDEAST-IRAN', 'MIDEAST-YEMEN'],
    'ideological',
    'all_in',
    ARRAY[
        'legitimate retaliation', 'legitimate response',
        'asymmetric retaliation', 'asymmetric response',
        'asymmetric warfare', 'asymmetric deterrence',
        'proportionate response', 'proportionate to aggression',
        'complicit Gulf states', 'complicit states', 'host states',
        'launch points', 'staging ground',
        'US base as legitimate target', 'US bases are targets',
        'response to aggression', 'eye for an eye',
        'Yemeni resistance', 'Houthi solidarity', 'Palestine solidarity',
        'punishing Saudi participation',
        'imposing costs', 'cost imposition',
        'cannot match conventional', 'asymmetric calculus',
        'Aramco strike successful', 'global oil offline',
        'higher cost', 'will be answered'
    ],
    ARRAY[
        'Iran', 'Iranian', 'IRGC', 'Quds', 'Houthi', 'Houthis',
        'Aramco', 'Saudi', 'UAE',
        'US base', 'Al Udeid', 'Al Asad',
        'attack', 'strike', 'missile', 'drone'
    ],
    ARRAY[
        'Press TV', 'IRNA', 'Fars News', 'Fars News Agency',
        'Tasnim News', 'Mehr News',
        'Al Manar', 'Al Mayadeen',
        'Middle East Eye'
    ],
    ARRAY[
        'Press TV', 'IRNA', 'Fars News', 'Fars News Agency',
        'Tasnim News', 'Mehr News',
        'Al Manar', 'Al Mayadeen',
        'Middle East Eye'
    ]
) ON CONFLICT (id) DO NOTHING;

-- FN6 narrative links
INSERT INTO friction_node_narratives (fn_id, narrative_id, stance_label_en, stance_label_de, display_order) VALUES
    ('gulf_attacks_on_arab_states', 'west_gulf_aggression_response',
        'State-sponsored aggression', 'Staatlich gesponserte Aggression', 1),
    ('gulf_attacks_on_arab_states', 'iran_asymmetric_retaliation_doctrine',
        'Legitimate asymmetric retaliation', 'Legitime asymmetrische Vergeltung', 2),
    ('gulf_attacks_on_arab_states', 'iran_axis_of_resistance',
        'Resistance solidarity', 'Widerstands-Solidaritaet', 3),
    ('gulf_attacks_on_arab_states', 'eu_diplomatic_preservation_norm',
        'De-escalation', 'Deeskalation', 4),
    ('gulf_attacks_on_arab_states', 'multipolar_systemic_alternative',
        'Anti-imperial framing', 'Anti-imperiale Rahmung', 5)
ON CONFLICT (fn_id, narrative_id) DO NOTHING;


-- ============================================================
-- FN7: iran_theater (theater grouping)
-- ============================================================
INSERT INTO friction_nodes (
    id, fn_type, name_en, name_de,
    description_en, description_de,
    editorial_summary_en, editorial_summary_de,
    centroid_ids, member_fn_ids,
    display_order
) VALUES (
    'iran_theater',
    'theater',
    'Iran (war, regime, nuclear, proxy network, Hormuz, Gulf strikes)',
    'Iran (Krieg, Regime, Nuklear, Stellvertreter-Netzwerk, Hormuz, Golf-Schlaege)',
    $D$The Iran theater bundles five atomic friction nodes that share Iran as their common subject. Each is a distinct contested phenomenon, but they form one strategic system: the Iranian state's right to exist as it does (regime), what its nuclear program may legitimately be (nuclear), what its regional armed-group network may legitimately do (proxy), what control it may legitimately assert over the Strait of Hormuz (Hormuz), and what asymmetric retaliation it may legitimately conduct against complicit states (Gulf strikes). Together they constitute the Iran question of the contemporary international system.$D$,
    $D$Das Iran-Theater buendelt fuenf atomare Friction Nodes, die Iran als gemeinsames Subjekt haben. Jeder ist ein eigenstaendiges umstrittenes Phaenomen, aber zusammen bilden sie ein strategisches System: das Recht des iranischen Staates auf Existenz, was sein Atomprogramm sein darf, was sein regionales Bewaffneten-Netz tun darf, welche Kontrolle ueber die Strasse von Hormuz, welche asymmetrische Vergeltung gegen komplizenhafte Staaten. Zusammen bilden sie die Iran-Frage des zeitgenoessischen internationalen Systems.$D$,
    $D$Five atomic friction nodes bundled as one theater because Iran is the common subject across all of them. The map marker for this theater sits over Iran. Clicking it expands to the constituent atomic FNs: nuclear program (the 45-year file), regime legitimacy (the foundational right-to-exist contest), regional proxy network (Hezbollah / Hamas / Houthis / Iraqi PMF), Strait of Hormuz (asymmetric maritime leverage), and Gulf attacks (asymmetric kinetic retaliation). Each of these has its own coalitions, narratives, and event flow; together they describe the strategic system Western and Israeli planners think of as "the Iran problem" and Iranian planners think of as "the Iran question". The theater concept is curated, not emergent — these five FNs were judged to share Iran as their subject through editorial decision, not because of automatic centroid overlap.$D$,
    $D$Fuenf atomare Friction Nodes als ein Theater gebuendelt, weil Iran das gemeinsame Subjekt aller ist. Der Kartenmarker fuer dieses Theater liegt ueber Iran. Klicken erweitert auf die konstituierenden atomaren FNs: Atomprogramm (die 45-jaehrige Akte), Regime-Legitimitaet (der grundlegende Existenzrecht-Konflikt), regionales Stellvertreter-Netzwerk (Hisbollah / Hamas / Huthis / irakische PMF), Strasse von Hormuz (asymmetrische maritime Hebelwirkung) und Golf-Angriffe (asymmetrische kinetische Vergeltung). Jeder hat eigene Koalitionen, Narrative und Ereignisfluss; zusammen beschreiben sie das strategische System, das westliche und israelische Planer als "das Iran-Problem" und iranische Planer als "die Iran-Frage" verstehen. Das Theater-Konzept ist kuratiert, nicht emergent.$D$,
    ARRAY['MIDEAST-IRAN', 'MIDEAST-ISRAEL', 'AMERICAS-USA', 'MIDEAST-SAUDI',
          'NON-STATE-EU', 'MIDEAST-LEVANT', 'MIDEAST-PALESTINE',
          'MIDEAST-YEMEN', 'MIDEAST-IRAQ', 'EUROPE-RUSSIA', 'ASIA-CHINA',
          'EUROPE-UK', 'EUROPE-FRANCE'],
    ARRAY['iran_nuclear_program',
          'iran_proxy_network',
          'iran_regime_legitimacy_contest',
          'strait_of_hormuz_sovereignty',
          'gulf_attacks_on_arab_states'],
    1
) ON CONFLICT (id) DO NOTHING;

COMMIT;

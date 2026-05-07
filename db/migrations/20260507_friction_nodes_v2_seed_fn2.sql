-- Seed FN2 Iran nuclear program: 1 friction node + 5 narratives + 5 links.
-- 2026-05-07
-- Idempotent via ON CONFLICT DO NOTHING. Re-runnable on local + Render.
-- Narrative claims live in markdown drafts at out/fn2_narrative_drafts.md;
-- the SQL below is the canonical insertion. Edit content in SQL going forward.

BEGIN;

-- ============================================================
-- friction_nodes : Iran nuclear program
-- ============================================================
INSERT INTO friction_nodes (
    id, name_en, name_de, description_en, description_de,
    centroid_ids, topic_keywords, display_order
) VALUES (
    'iran_nuclear_program',
    'Iran nuclear program',
    'Iranisches Atomprogramm',
    $D$Iran's enrichment program, breakout time, advanced-centrifuge counts, and IAEA inspection access are simultaneously read as proximate to a weapon (existential-threat read), as a sovereign civilian-energy and deterrence-hedge program (Iranian self-frame), as a diplomatic problem requiring engagement (E3 frame), and as a hedging variable in regional security (Gulf frame). The contested phenomenon is the same set of technical-political facts; incompatible prescriptions follow from incompatible frames.$D$,
    $D$Das iranische Anreicherungsprogramm, die Breakout-Zeit, der Bestand fortgeschrittener Zentrifugen und der IAEO-Zugang werden gleichzeitig als Annaeherung an eine Waffe gelesen, als souveraenes ziviles Energie- und Abschreckungs-Hedge-Programm, als diplomatisches Problem und als regionalpolitische Variable. Dieselben technisch-politischen Fakten, unvereinbare Verschreibungen.$D$,
    ARRAY['MIDEAST-IRAN', 'MIDEAST-ISRAEL', 'AMERICAS-USA', 'MIDEAST-SAUDI', 'NON-STATE-EU'],
    ARRAY['Iran nuclear', 'Natanz', 'Fordow', 'Arak', 'enrichment', 'IAEA Iran', 'JCPOA', 'breakout time', 'centrifuge', 'weapons-grade', 'Bushehr'],
    1
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- narratives_v2 : the 5-narrative cast for FN2
-- ============================================================

-- 1) Western coalition: Iran nuclear as existential threat (N3 split, nuclear half)
INSERT INTO narratives_v2 (id, name_en, name_de, claim_en, claim_de, actor_centroids, tier, narrative_type, framing_keywords, topic_keywords) VALUES (
    'west_iran_nuclear_threat',
    'Western coalition: Iran nuclear as existential threat',
    'Westliche Koalition: Iran-Atomprogramm als Existenzbedrohung',
    $D$The Israel-US-Saudi coalition describes Iran's enrichment program as an "existential threat" that warrants "preemptive" military action if necessary. Iranian advances at Natanz and Fordow — 60% enrichment levels, advanced IR-6 / IR-9 centrifuge cascades, reduced "breakout time" estimates — are framed as evidence of intent to "weaponize". The Israeli position rests on the "Begin doctrine" (no hostile regional power may acquire nuclear weapons) and the broader principle of "prevention not deterrence". The US position escalates from "maximum pressure" sanctions and naval deployments to direct strikes on Iranian assets where the breakout window narrows. The narrative prescribes denial of capability through sanctions, sabotage (Stuxnet legacy, Mossad operations against scientists, plant accidents), and where necessary preemptive military strikes on enrichment facilities; explicitly rejects diplomatic frameworks that grant Iran any continuing enrichment capability.$D$,
    $D$Die israelisch-amerikanisch-saudische Koalition beschreibt Irans Anreicherungsprogramm als "Existenzbedrohung", die noetigenfalls "praeventives" militaerisches Handeln rechtfertigt. Iranische Fortschritte in Natanz und Fordow gelten als Beweis fuer Waffenabsicht. Die israelische Position stuetzt sich auf die "Begin-Doktrin" und das Prinzip der "Praevention statt Abschreckung". Die US-Position eskaliert von "maximalem Druck" bis zu direkten Schlaegen, wenn das Breakout-Fenster schrumpft. Verschreibung: Faehigkeitsverweigerung durch Sanktionen, Sabotage und noetigenfalls praeventive Schlaege; explizite Ablehnung diplomatischer Rahmen, die Iran fortgesetzte Anreicherungsfaehigkeit zugestehen.$D$,
    ARRAY['AMERICAS-USA', 'MIDEAST-ISRAEL', 'MIDEAST-SAUDI'],
    'operational',
    'all_in',
    ARRAY['existential threat', 'preemptive strike', 'maximum pressure', 'breakout time', 'weapons-grade', 'Begin doctrine', 'prevention not deterrence', 'all options on table', 'weapons program', 'denial of capability', 'Natanz strike'],
    ARRAY['Iran nuclear', 'Natanz', 'Fordow', 'enrichment', 'IAEA Iran', 'centrifuge', 'IRGC', 'Mossad', 'sanctions Iran']
) ON CONFLICT (id) DO NOTHING;

-- 2) Iran: nuclear program as sovereign right and deterrence hedge (NEW all-in)
INSERT INTO narratives_v2 (id, name_en, name_de, claim_en, claim_de, actor_centroids, tier, narrative_type, framing_keywords, topic_keywords) VALUES (
    'iran_nuclear_sovereign_right',
    'Iran: nuclear program as sovereign right and deterrence hedge',
    'Iran: Atomprogramm als souveraenes Recht und Abschreckungsabsicherung',
    $D$Iran describes its nuclear program in a framework of sovereign right and lawful deterrence. Enrichment activity at Natanz and Fordow is characterised as a "peaceful civilian nuclear program" and an exercise of Iran's rights as an "NPT signatory" under "Article IV". The supreme leader's standing "fatwa against nuclear weapons" is invoked as the religious-juridical foundation — nuclear weapons are forbidden under Iranian Islamic doctrine, and the program is therefore civilian by definition. Progressive non-compliance with JCPOA limits is framed as legitimate response to the "American withdrawal" of 2018 and the "snapback" of sanctions; "we honored the deal" is the standing claim. The Israeli campaign of "sabotage", "assassinations of scientists", and plant accidents is termed "aggression" and "state terrorism". American "maximum pressure" is "collective punishment" of the Iranian people; deeper enrichment is the proportionate "deterrence hedge" against credible US-Israeli threats, with Iraq and Libya as cautionary cases of regimes that abandoned deterrence and were destroyed. The narrative prescribes continued enrichment as leverage, demands sanctions relief and US security guarantee as preconditions for any new agreement, and rejects all frameworks that would deny Iran the right to a complete nuclear fuel cycle.$D$,
    $D$Iran beschreibt sein Atomprogramm im Rahmen souveraenen Rechts und rechtmaessiger Abschreckung. Anreicherung in Natanz und Fordow gilt als "friedliches ziviles Nuklearprogramm" und Wahrnehmung iranischer Rechte als "NPT-Unterzeichnerstaat" unter "Artikel IV". Die fortbestehende "Fatwa des Obersten Fuehrers gegen Nuklearwaffen" wird als religioes-juristische Grundlage angefuehrt. Die schrittweise Abkehr von JCPOA-Grenzen ist legitime Antwort auf den "amerikanischen Ausstieg" 2018; "wir haben das Abkommen eingehalten" ist die stehende Behauptung. Israelische Sabotage und Attentate auf Wissenschaftler werden als "Aggression" und "Staatsterrorismus" bezeichnet. Amerikanischer "maximaler Druck" ist "kollektive Bestrafung"; tiefere Anreicherung ist die verhaeltnismaessige "Abschreckungsabsicherung". Verschreibung: fortgesetzte Anreicherung als Hebel, Sanktionserleichterung und US-Sicherheitsgarantie als Vorbedingungen, Ablehnung jedes Rahmens, der Iran den vollstaendigen Brennstoffkreislauf verweigert.$D$,
    ARRAY['MIDEAST-IRAN'],
    'ideological',
    'all_in',
    ARRAY['peaceful civilian nuclear program', 'NPT Article IV', 'sovereign enrichment', 'Khamenei fatwa', 'fatwa against nuclear weapons', 'we honored the deal', 'American withdrawal', 'JCPOA betrayed', 'maximum pressure failure', 'collective punishment', 'deterrence hedge', 'Israeli aggression', 'state terrorism', 'Iraq Libya cautionary'],
    ARRAY['Iran nuclear', 'Natanz', 'Fordow', 'Bushehr', 'IAEA Iran', 'JCPOA', 'enrichment', 'centrifuge', 'Khamenei', 'Pezeshkian', 'Araghchi', 'Vienna talks']
) ON CONFLICT (id) DO NOTHING;

-- 3) EU/E3 diplomatic preservation norm (NEW generic stand-by)
INSERT INTO narratives_v2 (id, name_en, name_de, claim_en, claim_de, actor_centroids, tier, narrative_type, framing_keywords, topic_keywords) VALUES (
    'eu_diplomatic_preservation_norm',
    'EU/E3 diplomatic preservation norm',
    'EU/E3-Norm der diplomatischen Bewahrung',
    $D$The European Union and the E3 (France, Germany, United Kingdom) describe their default posture across major confrontations in a framework of "diplomatic preservation" — diplomatic channels, multilateral frameworks, and negotiated agreements should be preserved even under pressure to abandon them. On Iran nuclear: the "snapback" mechanism, "Vienna talks", "JCPOA-plus" proposals, continuous engagement despite enrichment escalation. On Russia-Ukraine: "Normandy Format" and post-2022 negotiation contingencies. On Israel-Palestine: "two-state solution" orthodoxy and ICJ/ICC engagement. On China-Taiwan: "strategic ambiguity" combined with "dialogue" advocacy. The framing language is portable: "preserve diplomacy", "diplomatic off-ramp", "engage rather than isolate", "multilateral framework", "international law", "de-escalation", "return to negotiations". The narrative explicitly registers concern about adversary behaviour but rejects unilateral military escalation as response, preferring calibrated pressure within multilateral mechanisms. Prescription: sustained diplomatic effort, preservation of multilateral institutions, opposition to unilateral action that breaks established frameworks, and the EU as indispensable convening power.$D$,
    $D$Die Europaeische Union und die E3 (Frankreich, Deutschland, Vereinigtes Koenigreich) beschreiben ihre Standardhaltung in zentralen Konfrontationen im Rahmen der "diplomatischen Bewahrung". Beim Iran-Atom: "Snapback", "Wiener Gespraeche", "JCPOA-Plus", fortgesetzte Anbindung trotz Anreicherungseskalation. Bei Russland-Ukraine: "Normandie-Format". Bei Israel-Palaestina: "Zwei-Staaten-Loesung". Die Rahmensprache ist portabel: "Diplomatie bewahren", "diplomatischer Ausweg", "einbinden statt isolieren", "multilateraler Rahmen", "Voelkerrecht", "Deeskalation". Sorgen ueber Verhalten von Gegenspielern werden ausdruecklich registriert, einseitige militaerische Eskalation aber als Antwort abgelehnt. Verschreibung: anhaltende diplomatische Bemuehung, Bewahrung multilateraler Institutionen, Widerspruch gegen einseitige Aktionen, EU-Rolle als unverzichtbare Konvenierungsmacht.$D$,
    ARRAY['NON-STATE-EU', 'EUROPE-FRANCE', 'EUROPE-GERMANY', 'EUROPE-UK'],
    'ideological',
    'stand_by',
    ARRAY['preserve diplomacy', 'diplomatic off-ramp', 'multilateral framework', 'engage rather than isolate', 'de-escalation', 'return to negotiations', 'snapback', 'JCPOA-plus', 'Vienna talks', 'Normandy Format', 'two-state solution', 'strategic ambiguity', 'international law', 'EU as convener'],
    ARRAY['EU diplomacy', 'Borrell', 'Kallas', 'E3', 'Macron diplomacy', 'Scholz diplomacy', 'Starmer diplomacy', 'EU statement', 'Vienna', 'Astana', 'Doha talks', 'dialogue']
) ON CONFLICT (id) DO NOTHING;

-- 4) Multipolar systemic alternative (NEW stand-by, post-N5 split)
INSERT INTO narratives_v2 (id, name_en, name_de, claim_en, claim_de, actor_centroids, tier, narrative_type, framing_keywords, topic_keywords) VALUES (
    'multipolar_systemic_alternative',
    'Multipolar systemic alternative to US-led order',
    'Multipolare systemische Alternative zur US-gefuehrten Ordnung',
    $D$China, Russia, Iran, the DPRK, and aligned Global South states describe US foreign policy through objection to American structural primacy. American security policy is termed "hegemony", "unilateralism", "imperialism", and "Cold War mentality". US sanctions are "collective punishment" affecting populations rather than governments. The alliance architecture (NATO, AUKUS, Quad, Indo-Pacific bilaterals) is "encirclement" and "containment" of rising powers. Military interventions abroad are "regime change"; forward deployments and bases on other states' soil are "foreign occupation". The narrative prescribes multipolarity (BRICS+ expansion, Russia-China-Iran-DPRK strategic alignment, dollar de-dependence, Global South solidarity) as the corrective. On Iran nuclear specifically: enrichment is a "sovereign right" of a state under hostile sanctions and Israeli threat; US-Israeli pressure is hegemonic interference and the actual escalator. (Iran-specific resistance vocabulary — Axis of Resistance, legitimate liberation — is captured in the separate `iran_axis_of_resistance` narrative not relevant to this FN.)$D$,
    $D$China, Russland, Iran, die DVRK und verbuendete Global-South-Staaten beschreiben die US-Aussenpolitik durch Einspruch gegen amerikanische strukturelle Vorrangstellung. Amerikanische Sicherheitspolitik gilt als "Hegemonie", "Unilateralismus", "Imperialismus" und "Kalter-Kriegs-Mentalitaet". US-Sanktionen sind "kollektive Bestrafung". Die Buendnisarchitektur (NATO, AUKUS, Quad) ist "Einkreisung" und "Eindaemmung" aufstrebender Maechte. Militaerische Interventionen sind "Regimewechsel"; vorgeschobene Stationierungen sind "fremde Besatzung". Verschreibung: Multipolaritaet (BRICS+, Russland-China-Iran-DVRK-Ausrichtung, Dollar-Abhaengigkeitsabbau, Global-South-Solidaritaet) als Korrektiv. Beim Iran-Atom: Anreicherung als "souveraenes Recht" eines Staates unter feindlichen Sanktionen; US-israelischer Druck als hegemoniale Einmischung und tatsaechlicher Eskalator.$D$,
    ARRAY['ASIA-CHINA', 'EUROPE-RUSSIA', 'MIDEAST-IRAN', 'ASIA-NORKOREA'],
    'ideological',
    'stand_by',
    ARRAY['US hegemony', 'unilateralism', 'imperialism', 'Cold War mentality', 'collective punishment', 'regime change', 'foreign occupation', 'multipolar', 'BRICS', 'Global South', 'sovereign right', 'anti-sanctions', 'dollar de-dependence', 'encirclement'],
    ARRAY['US bases', 'sanctions', 'AUKUS', 'Quad', 'NATO encirclement', 'BRICS expansion', 'dollar', 'Cuba sanctions', 'Venezuela sanctions', 'Iran sanctions', 'Russia sanctions']
) ON CONFLICT (id) DO NOTHING;

-- 5) Gulf regional de-escalation (transferred from N21, all_in toward Gulf-specific FNs)
INSERT INTO narratives_v2 (id, name_en, name_de, claim_en, claim_de, actor_centroids, tier, narrative_type, framing_keywords, topic_keywords) VALUES (
    'gulf_regional_de_escalation',
    'Gulf regional de-escalation and hedging',
    'Golf-regionale Deeskalation und Absicherung',
    $D$Saudi Arabia and Gulf states describe regional security in a framework of "stability over confrontation" that diverges in important respects from the Israel-US confrontational position toward Iran. Gulf prosperity is framed as dependent on regional "de-escalation": the Saudi-Iran rapprochement brokered by China in 2023, diplomatic exits from the Yemen war, normalisation steps with Syria, and economic openings via "IMEC" and trade corridors. The narrative explicitly does NOT rule out Iranian threats — Houthi attacks on Saudi oil infrastructure, Iranian-linked maritime incidents, Iraqi PMF strikes — but frames the response as "hedging" rather than confrontation. On Iran nuclear specifically: post-2023 Saudi operational positioning prefers diplomatic channels over endorsement of preemptive military action; public concern about enrichment is registered but is not the dominant Saudi posture. The narrative prescribes alliance frameworks and missile-defence integration alongside dialogue with Tehran, multipolar diplomatic positioning (closer to BRICS, China, Russia without breaking US ties), and Vision 2030 economic transformation that reduces oil-revenue dependence on regional crises.$D$,
    $D$Saudi-Arabien und die Golfstaaten beschreiben regionale Sicherheit im Rahmen "Stabilitaet vor Konfrontation", was in wichtigen Punkten von der israelisch-amerikanischen Iran-Konfrontationsposition abweicht. Golf-Wohlstand wird als abhaengig von regionaler "Deeskalation" gerahmt: die 2023 von China vermittelte saudisch-iranische Annaeherung, diplomatische Ausstiege aus dem Jemen-Krieg, Normalisierungsschritte mit Syrien, wirtschaftliche Oeffnungen via "IMEC". Iranische Bedrohungen werden nicht ausgeschlossen, aber die Antwort wird als "Absicherung" statt Konfrontation gerahmt. Beim Iran-Atom: post-2023 saudische operative Position bevorzugt diplomatische Kanaele gegenueber Befuerwortung praeventiver militaerischer Aktion. Verschreibung: Buendnisrahmen und Raketenabwehrintegration neben Dialog mit Teheran, multipolare diplomatische Positionierung, Vision-2030-Wirtschaftstransformation.$D$,
    ARRAY['MIDEAST-SAUDI'],
    'operational',
    'stand_by',
    ARRAY['Gulf de-escalation', 'Saudi-Iran rapprochement', 'Vision 2030', 'IMEC', 'hedging', 'regional stability', 'Yemen exit', 'Syria normalisation', 'multipolar Gulf'],
    ARRAY['Saudi Arabia', 'UAE', 'Gulf', 'Iran rapprochement', 'Yemen', 'Houthis', 'IMEC', 'BRICS', 'MBS']
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- friction_node_narratives : link FN2 to its 5-narrative cast with stance labels
-- ============================================================
INSERT INTO friction_node_narratives (fn_id, narrative_id, stance_label_en, stance_label_de, display_order) VALUES
    ('iran_nuclear_program', 'west_iran_nuclear_threat',         'Existential threat',                'Existenzbedrohung',                 1),
    ('iran_nuclear_program', 'iran_nuclear_sovereign_right',     'Sovereign right',                   'Souveraenes Recht',                 2),
    ('iran_nuclear_program', 'eu_diplomatic_preservation_norm',  'Preserve diplomacy',                'Diplomatie bewahren',               3),
    ('iran_nuclear_program', 'multipolar_systemic_alternative',  'Anti-sanctions / sovereign right',  'Anti-Sanktionen / souveraenes Recht', 4),
    ('iran_nuclear_program', 'gulf_regional_de_escalation',      'Regional hedging',                  'Regionale Absicherung',             5)
ON CONFLICT (fn_id, narrative_id) DO NOTHING;

COMMIT;

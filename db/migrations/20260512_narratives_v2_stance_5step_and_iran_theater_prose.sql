-- Convert narratives_v2.stance from text (support|criticism|neutral) to
-- smallint -2..+2 (mirroring outlet_entity_stance.stance), and rewrite
-- the two iran_theater narratives whose prose was inherited from the
-- old cross-cluster strategic-narrative library and is no longer
-- theater-specific.

BEGIN;

-- 1. Stance scale upgrade.
ALTER TABLE narratives_v2 DROP CONSTRAINT IF EXISTS narratives_v2_stance_check;
ALTER TABLE narratives_v2 ADD COLUMN stance_new smallint;

UPDATE narratives_v2 SET stance_new = CASE id
    WHEN 'west_iran_regime_change_doctrine'  THEN -2
    WHEN 'west_iran_nuclear_threat'          THEN -2
    WHEN 'west_iran_proxy_network_threat'    THEN -2
    WHEN 'west_gulf_aggression_response'     THEN -2
    WHEN 'west_hormuz_freedom_of_navigation' THEN -1
    WHEN 'eu_diplomatic_preservation_norm'   THEN  0
    WHEN 'multipolar_systemic_alternative'   THEN  1
    WHEN 'iran_hormuz_sovereign_pressure'    THEN  1
    WHEN 'iran_sovereign_existence'          THEN  2
    WHEN 'iran_nuclear_sovereign_right'      THEN  2
    WHEN 'iran_axis_of_resistance'           THEN  2
    WHEN 'iran_gulf_resistance_solidarity'   THEN  2
END;

ALTER TABLE narratives_v2 DROP COLUMN stance;
ALTER TABLE narratives_v2 RENAME COLUMN stance_new TO stance;
ALTER TABLE narratives_v2 ADD CONSTRAINT narratives_v2_stance_check
    CHECK (stance IS NULL OR (stance >= -2 AND stance <= 2));
COMMENT ON COLUMN narratives_v2.stance IS
    '5-step reader-facing stance toward the narrative''s actor: -2 strong criticism, -1 criticism, 0 neutral, +1 support, +2 strong support. Mirrors outlet_entity_stance.stance.';

-- 2. EU/E3 narrative — strip non-Iran content (Ukraine, Taiwan, Israel-Palestine).
UPDATE narratives_v2 SET
    name_en = 'EU/E3 diplomatic engagement on Iran',
    name_de = 'EU/E3 diplomatische Iran-Strategie',
    claim_en =
        'The European Union and the E3 (France, Germany, United Kingdom) frame their Iran posture around preserving diplomatic channels while applying calibrated pressure on enrichment and proliferation. The vocabulary is "JCPOA preservation", "Vienna talks", "snapback mechanism", "IAEA safeguards", "diplomatic off-ramp", "engage rather than isolate", "return to compliance", and "calibrated pressure". The narrative explicitly registers concern about enrichment escalation, ballistic-missile transfers, and IAEA cooperation, but rejects unilateral military strikes as the answer — preferring sustained diplomacy under multilateral institutions. Prescription: keep talks alive, threaten snapback as leverage rather than execution, and position the EU as the indispensable convening power between Washington and Tehran.',
    claim_de =
        'Die Europaeische Union und die E3 (Frankreich, Deutschland, Grossbritannien) gestalten ihre Iran-Politik um den Erhalt diplomatischer Kanaele bei gleichzeitig kalibriertem Druck auf Anreicherung und Proliferation. Das Vokabular: "JCPOA-Erhalt", "Wiener Gespraeche", "Snapback-Mechanismus", "IAEA-Sicherheitsmassnahmen", "diplomatische Ausfahrt", "engagieren statt isolieren", "Rueckkehr zur Einhaltung", "kalibrierter Druck". Das Narrativ benennt explizit Anreicherungs-Eskalation, Raketentransfers und IAEA-Kooperation als Probleme, lehnt jedoch unilateraere Militaerschlaege als Antwort ab und bevorzugt nachhaltige Diplomatie ueber multilaterale Institutionen. Vorschrift: Gespraeche am Leben erhalten, Snapback als Druckmittel statt als Vollzug einsetzen und die EU als unverzichtbare Vermittlerin zwischen Washington und Teheran positionieren.'
WHERE id = 'eu_diplomatic_preservation_norm';

-- 3. Multipolar narrative — strip Russia-Ukraine, Taiwan, NATO-encirclement.
UPDATE narratives_v2 SET
    name_en = 'Multipolar sovereignty backing for Iran',
    name_de = 'Multipolare Souveraenitaetsdeckung fuer Iran',
    claim_en =
        'China, Russia, the DPRK, and Global South commentary frame the Iran confrontation as US-Israeli "hegemony" and "interference" against a sovereign state. The argument: enrichment is a legitimate "sovereign right" under hostile sanctions and standing military threat from Israel; the actual escalator is American-Israeli pressure, not Iranian conduct. The vocabulary is "sovereignty", "unilateralism", "collective punishment via sanctions", "diktat", "imperialism", "BRICS solidarity", "Global South", and "dollar de-dependence". The narrative is not Iranian self-defence (that lives in iran_sovereign_existence) — it is the external multipolar voice that legitimises Iran''s position by framing Western pressure as systemic aggression. Prescription: Russia-China-Iran-DPRK alignment as counterweight, BRICS+ expansion, sanctions relief through multipolar institutions, and rejection of Washington''s right to set the terms.',
    claim_de =
        'China, Russland, die DVRK und Kommentatoren des Globalen Suedens rahmen die Iran-Konfrontation als US-israelische "Hegemonie" und "Einmischung" gegen einen souveraenen Staat. Die Argumentation: Anreicherung ist ein legitimes "souveraenes Recht" unter feindlichen Sanktionen und permanenter israelischer Militaerdrohung; der eigentliche Eskalator ist amerikanisch-israelischer Druck, nicht iranisches Verhalten. Das Vokabular: "Souveraenitaet", "Unilateralismus", "Kollektivstrafe durch Sanktionen", "Diktat", "Imperialismus", "BRICS-Solidaritaet", "Globaler Sueden", "Dollar-Entkopplung". Das Narrativ ist keine iranische Selbstverteidigung (diese lebt in iran_sovereign_existence) — es ist die externe multipolare Stimme, die Irans Position durch die Rahmung westlichen Drucks als systemische Aggression legitimiert. Vorschrift: Russland-China-Iran-DVRK-Allianz als Gegengewicht, BRICS+-Erweiterung, Sanktionsentlastung durch multipolare Institutionen, Zurueckweisung von Washingtons Anspruch, die Bedingungen zu setzen.'
WHERE id = 'multipolar_systemic_alternative';

COMMIT;

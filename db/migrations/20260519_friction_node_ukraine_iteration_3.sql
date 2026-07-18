-- Ukraine theater iteration 3: split peace_negotiations narratives into three.
-- 2026-05-19
--
-- Editorial review surfaced that I conflated Russian maximalist demands
-- (all SMO objectives — denazification, demilitarisation, neutral status,
-- recognition of annexed territories, lifted sanctions, returned assets)
-- with Trump's frontline-freeze framework (line-of-contact freeze plus
-- Ukrainian neutrality but no endorsement of Russian maximalist goals).
--
-- Putting TASS + Fox News in the same cohort was wrong. They support
-- different settlement endpoints even when both criticise the Ukrainian
-- maximalist position. Split into three distinct narratives.

BEGIN;

-- ============================================================
-- 1. Clean slate for peace narratives
-- ============================================================

-- title_narratives doesn't cascade; clear first
DELETE FROM title_narratives
WHERE narrative_id IN ('just_peace_no_concessions','pragmatic_freeze_settlement');

DELETE FROM narratives_v2
WHERE id IN ('just_peace_no_concessions','pragmatic_freeze_settlement');

-- ============================================================
-- 2. Insert three replacement narratives
-- ============================================================

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('ukrainian_maximalist_peace', 'ukraine_peace_negotiations', 1, 2,
 'Ukrainian maximalist demands', 'Ukrainische Maximalforderungen',
 'Just peace requires full Russian withdrawal to 1991 borders with NATO-backed security guarantees',
 'Gerechter Frieden erfordert vollen russischen Rueckzug zu Grenzen von 1991 mit NATO-gestuetzten Sicherheitsgarantien',
 'Ukrainian maximalist framing (Ukrainian press + Western mainstream + Eastern European hawks + EU centrists, with internal disagreement chiefly from Hungary and Slovakia) holds that just peace requires full Russian withdrawal to internationally recognised 1991 borders, NATO accession or equivalent binding security guarantees, accountability mechanisms for war crimes, and reparations funded through seized Russian sovereign assets. Vocabulary: just peace, territorial integrity, 1991 borders, NATO accession, security guarantees, accountability, no appeasement, reparations, war crimes tribunal. Coverage rejects any framework that legitimises territorial losses, frames the 2014 Crimea precedent as proof that frozen conflicts invite further aggression, and emphasises Ukrainian society''s rejection of compromise terms. Prescription: continue military pressure until Russian retreat; refuse settlement frameworks that recognise annexations; pre-condition negotiations on Russian withdrawal.',
 'Ukrainische Maximalrahmung (ukrainische Medien + westlicher Mainstream + osteuropaeische Falken + EU-Zentristen, mit internen Differenzen vor allem aus Ungarn und der Slowakei) haelt fest, dass gerechter Frieden vollen russischen Rueckzug zu international anerkannten Grenzen von 1991, NATO-Beitritt oder gleichwertige verbindliche Sicherheitsgarantien, Rechenschaftsmechanismen fuer Kriegsverbrechen und Reparationen aus beschlagnahmtem russischen Staatsvermoegen erfordere. Vokabular: gerechter Frieden, territoriale Integritaet, Grenzen von 1991, NATO-Beitritt, Sicherheitsgarantien, Rechenschaft, keine Beschwichtigung, Reparationen, Kriegsverbrechertribunal. Berichterstattung lehnt jeden Rahmen ab, der territoriale Verluste legitimiert, rahmt den Krim-Praezedenzfall 2014 als Beleg, dass eingefrorene Konflikte weitere Aggression provozieren, und betont die Ablehnung von Kompromissbedingungen in der ukrainischen Gesellschaft. Vorschrift: militaerischen Druck bis zum russischen Rueckzug fortsetzen; Beilegungsrahmen ablehnen, die Annexionen anerkennen; Verhandlungen an russischen Rueckzug vor-konditionieren.',
 ARRAY['EUROPE-UKRAINE','EUROPE-UK','EUROPE-BALTIC','EUROPE-VISEGRAD','EUROPE-FRANCE','EUROPE-GERMANY'],
 ARRAY['Kyiv Post','Reuters','Bloomberg','Financial Times','BBC World','The Guardian','The Telegraph','Le Monde','Le Figaro','Frankfurter Allgemeine','Süddeutsche Zeitung','Der Spiegel','Die Zeit','Tagesschau','Deutsche Welle','La Repubblica','Corriere della Sera','ANSA','El País','Die Presse','ERR News','LRT English','LSM English','Atlantic Council','Associated Press','The Economist','EurActiv','iROZHLAS','Novinite'],
 ARRAY['just peace','territorial integrity','1991 borders','NATO accession','security guarantees','accountability','no appeasement','reparations','war crimes tribunal','rule of law','frozen conflict trap','reward aggression','full withdrawal'],
 true),

('russian_maximalist_peace', 'ukraine_peace_negotiations', 2, -2,
 'Russian maximalist demands (SMO objectives)', 'Russische Maximalforderungen (SMO-Ziele)',
 'Settlement must complete all SMO objectives: denazification, demilitarisation, neutrality, recognised annexations, lifted sanctions',
 'Beilegung muss alle SMO-Ziele vollenden: Entnazifizierung, Entmilitarisierung, Neutralitaet, anerkannte Annexionen, aufgehobene Sanktionen',
 'Russian maximalist framing (Russian state press + Belarusian state) holds that any settlement must address the root causes of the war by achieving all stated objectives of the special military operation. The framework: complete denazification of Ukrainian leadership and institutions, demilitarisation of the Ukrainian Armed Forces to defined caps, formal constitutional neutrality (no NATO accession ever, no foreign bases), formal international recognition of all four annexed regions (Donetsk, Luhansk, Zaporizhzhia, Kherson) plus Crimea within their claimed administrative boundaries, full restoration of Russian-language rights, complete lifting of all sanctions, return of all frozen sovereign assets, and a binding US/NATO commitment to no further eastern expansion. Vocabulary: SMO objectives, root causes, denazification, demilitarisation, constitutional neutrality, recognised borders, Russian-speaking rights, sanctions lifted, frozen assets returned, NATO non-expansion guarantee, multipolar settlement. Prescription: any settlement that does not deliver these objectives is unacceptable; negotiations are useful only as a venue to achieve them; military operations continue until objectives are met or accepted at the negotiating table.',
 'Russische Maximalrahmung (russische Staatsmedien + belarussische Staatsmedien) haelt fest, dass jede Beilegung die Grundursachen des Krieges adressieren und alle erklaerten Ziele der militaerischen Spezialoperation erreichen muesse. Das Rahmenwerk: vollstaendige Entnazifizierung der ukrainischen Fuehrung und Institutionen, Entmilitarisierung der ukrainischen Streitkraefte auf festgelegte Obergrenzen, formale verfassungsrechtliche Neutralitaet (kein NATO-Beitritt jemals, keine auslaendischen Basen), formale internationale Anerkennung aller vier annektierten Regionen (Donezk, Luhansk, Saporischschja, Cherson) plus Krim innerhalb ihrer beanspruchten Verwaltungsgrenzen, volle Wiederherstellung russischer Sprachrechte, vollstaendige Aufhebung aller Sanktionen, Rueckgabe allen eingefrorenen Staatsvermoegens und verbindliche US/NATO-Verpflichtung zu keiner weiteren Osterweiterung. Vokabular: SMO-Ziele, Grundursachen, Entnazifizierung, Entmilitarisierung, verfassungsrechtliche Neutralitaet, anerkannte Grenzen, russische Sprachrechte, aufgehobene Sanktionen, zurueckgegebenes Vermoegen, NATO-Nichterweiterungs-Garantie, multipolare Beilegung. Vorschrift: jede Beilegung ohne diese Ziele ist unannehmbar; Verhandlungen sind nur als Ort sinnvoll, sie zu erreichen; Militaeroperationen werden fortgesetzt, bis Ziele erreicht oder am Verhandlungstisch akzeptiert sind.',
 ARRAY['EUROPE-RUSSIA','EUROPE-BELARUS'],
 ARRAY['TASS','TASS (EN)','tass.com','RT','Lenta.ru','lenta.ru','Gazeta.ru','gazeta.ru','Kommersant','Izvestia','RIA Novosti','BelTA','BelTA Russian','Press TV'],
 ARRAY['SMO objectives','root causes','denazification','demilitarisation','constitutional neutrality','recognised borders','Russian-speaking rights','sanctions lifted','frozen assets returned','NATO non-expansion','multipolar settlement','our people','brotherly people','no NATO accession ever'],
 true),

('frontline_freeze_settlement', 'ukraine_peace_negotiations', 3, -1,
 'Frontline freeze (Anchorage track)', 'Einfrieren der Frontlinie (Anchorage-Spur)',
 'End the killing through frozen line of contact + Ukrainian neutrality, without endorsing Russian maximalist goals',
 'Toeten beenden durch eingefrorene Beruehrungslinie + ukrainische Neutralitaet, ohne russische Maximalziele zu billigen',
 'Frontline-freeze framing (Trump-aligned American press + Hungarian/Slovak-aligned EU + Turkish + Indian + Chinese + Brazilian + broader Global South) holds that the war is unwinnable for either side at acceptable cost and that a pragmatic settlement requires freezing the line of contact, formalising Ukrainian neutrality (no NATO accession), building a multilateral security guarantee structure outside NATO, lifting sanctions in phases tied to verified compliance, and allowing refugee return. Crucially, this position does NOT endorse Russian maximalist objectives — no demilitarisation of the Ukrainian Armed Forces, no denazification framework, no formal international recognition of annexed territories (de facto control accepted, de jure recognition deferred). The framework is closer to a Korean armistice than to a Russian victory. The Anchorage track (sometimes "spirit of Anchorage") refers to Trump-Putin diplomatic efforts to crystallise this position. Vocabulary: freeze, line of contact, Anchorage framework, neutrality (not demilitarisation), multilateral security, end the killing, Korean armistice, phased sanctions relief, sustainable peace, end the war. Prescription: immediate freeze; Istanbul-style talks; Ukrainian constitutional neutrality with security backstops outside NATO; phased sanctions relief tied to compliance.',
 'Frontlinien-Einfrierungs-Rahmung (Trump-orientierte amerikanische Medien + ungarisch/slowakisch-orientierte EU + tuerkisch + indisch + chinesisch + brasilianisch + breiterer Global South) haelt fest, dass der Krieg fuer beide Seiten zu akzeptablen Kosten nicht gewinnbar sei und eine pragmatische Beilegung Einfrieren der Beruehrungslinie, Formalisierung ukrainischer Neutralitaet (kein NATO-Beitritt), Aufbau multilateraler Sicherheitsgarantie-Struktur ausserhalb der NATO, phasenweise Sanktionserleichterung an verifizierte Einhaltung gebunden und Fluechtlingsrueckkehr erfordere. Entscheidend: diese Position billigt NICHT russische Maximalziele — keine Entmilitarisierung der ukrainischen Streitkraefte, kein Entnazifizierungsrahmen, keine formale internationale Anerkennung annektierter Territorien (de-facto-Kontrolle akzeptiert, de-jure-Anerkennung aufgeschoben). Der Rahmen ist naeher am koreanischen Waffenstillstand als an einem russischen Sieg. Die Anchorage-Spur (manchmal "Geist von Anchorage") verweist auf Trump-Putin-Diplomatie zur Verfestigung dieser Position. Vokabular: Einfrieren, Beruehrungslinie, Anchorage-Rahmen, Neutralitaet (nicht Entmilitarisierung), multilaterale Sicherheit, Toeten beenden, koreanischer Waffenstillstand, phasenweise Sanktionserleichterung, nachhaltiger Frieden, Krieg beenden. Vorschrift: sofortiges Einfrieren; Istanbul-Stil-Gespraeche; ukrainische verfassungsrechtliche Neutralitaet mit Sicherheitsabsicherungen ausserhalb der NATO; phasenweise Sanktionserleichterung an Einhaltung gebunden.',
 ARRAY['AMERICAS-USA','ASIA-CHINA','ASIA-INDIA','MIDEAST-TURKEY','AMERICAS-BRAZIL','NON-STATE-EU'],
 ARRAY['Fox News','Global Times','CGTN','China Daily','Hindustan Times','Times of India','NDTV','The Hindu','WION','Dawn','Express Tribune','TRT World','Daily Sabah','Anadolu Agency','O Globo','Bangkok Post','BRICS Info','News24'],
 ARRAY['freeze','line of contact','current lines','Anchorage framework','spirit of Anchorage','neutrality','multilateral security','end the killing','Korean armistice','phased sanctions relief','sustainable peace','end the war','realistic settlement','negotiated end','de facto recognition'],
 true);

-- ============================================================
-- 3. Sanity check
-- ============================================================

DO $$
DECLARE
    n_nar integer;
BEGIN
    SELECT COUNT(*) INTO n_nar FROM narratives_v2 WHERE fn_id = 'ukraine_peace_negotiations';
    IF n_nar <> 3 THEN
        RAISE EXCEPTION 'ukraine_peace_negotiations should have 3 narratives, got %', n_nar;
    END IF;
END $$;

COMMIT;

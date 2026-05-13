-- Sudan civil war seed: 1 standalone atomic FN + 3 narratives + 1 fn_anchor.
-- 2026-05-13
--
-- Standalone atomic FN (no theater wrapper) — Sudan is single-axis (RSF vs army);
-- volume too thin (~620 titles/180d) to subdivide. See docs/context/SUDAN_FN_SPEC.md.
-- Stance is toward the Sudanese state / army as primary actor.
--
-- Anchor bundle follows FN_ANCHOR_VOCABULARY_SPEC.md with one documented
-- exception: `Sudan` / `Sudanese` country tokens included because centroid
-- scope spans backer centroids (Egypt, Gulf, Saudi, Chad-pending, Ethiopia-pending,
-- NON-STATE-EU) where Sudan-the-word is the discriminating frame marker.

BEGIN;

-- ============================================================
-- 1. friction_nodes row
-- ============================================================

INSERT INTO friction_nodes (id, name_en, name_de, description_en, description_de,
    editorial_summary_en, editorial_summary_de, centroid_ids, fn_type, member_fn_ids,
    is_active, display_order)
VALUES

('sudan_civil_war', 'Sudan civil war', 'Sudanesischer Buergerkrieg',
 'The war between the Sudanese army (SAF) under General al-Burhan and the Rapid Support Forces (RSF) paramilitary under Hemedti, ignited 15 April 2023. Coverage clusters around three framings: legitimate-state counter-insurgency, humanitarian / genocide catastrophe (El Fasher, Darfur, Kordofan, hospital strikes, famine), and external-backer contest (UAE accused of arming the RSF, Egypt and Saudi Arabia backing the army).',
 'Der Krieg zwischen der sudanesischen Armee (SAF) unter General al-Burhan und der paramilitaerischen Rapid Support Forces (RSF) unter Hemedti, ausgebrochen am 15. April 2023. Drei Rahmungen: legitime staatliche Aufstandsbekaempfung, humanitaere Katastrophe / Genozid (Al-Faschir, Darfur, Kordofan, Angriffe auf Krankenhaeuser, Hungersnot) und Konflikt um auslaendische Unterstuetzer (Vorwuerfe gegen die VAE wegen Bewaffnung der RSF, Aegypten und Saudi-Arabien hinter der Armee).',
 'The Sudan war has produced the world''s largest current displacement crisis (~12M displaced) and a UN-evidenced genocide finding in El Fasher, yet remains underreported. Contest: pan-Arab Egyptian and Saudi outlets emphasise state legitimacy and Brotherhood/Islamist risk inside the army; UN, Western humanitarian and pan-Arab non-aligned outlets emphasise civilian casualties, drone strikes on hospitals, and famine; investigative international and Turkish/Iranian state media critique Gulf and Ethiopian arms flows to the RSF.',
 'Der Sudan-Krieg hat die weltweit groesste aktuelle Vertreibungskrise (~12 Mio.) und einen UN-belegten Genozid-Befund in Al-Faschir hervorgebracht, bleibt aber unterberichtet. Kontest: panarabische aegyptische und saudische Medien betonen Staats-Legitimitaet und Bruderschaft-/Islamisten-Risiko in der Armee; UN, westliche humanitaere und panarabische nicht-ausgerichtete Medien betonen zivile Opfer, Drohnenangriffe auf Krankenhaeuser und Hungersnot; investigative internationale sowie tuerkische und iranische Staatsmedien kritisieren Waffenlieferungen aus dem Golf und Aethiopien an die RSF.',
 ARRAY['MIDEAST-SUDAN','MIDEAST-EGYPT','MIDEAST-GULF','MIDEAST-SAUDI'],
 'atomic', NULL, true, 40);

-- ============================================================
-- 2. fn_anchor bundle in taxonomy_v3
-- ============================================================

INSERT INTO taxonomy_v3 (item_raw, aliases, is_active, taxonomy_function, linked_id) VALUES

('sudan_civil_war fn_anchor',
 jsonb_build_object(
   'en', jsonb_build_array(
     'Sudan','Sudanese','RSF','Sudanese army','Sudan army','Burhan','al-Burhan',
     'Hemedti','Hemeti','Hemetti','Dagalo','Janjaweed','Rapid Support',
     'El Fasher','al-Fasher','Al-Fashir','el-Fasher','Darfur','Kordofan',
     'Khartoum','Port Sudan','Omdurman','Wad Madani','Nyala','El Geneina','Geneina',
     'Gezira','Jeddah talks','paramilitary','Janjaweed'),
   'de', jsonb_build_array(
     'Sudan-Krieg','sudanesische Armee','Buergerkrieg im Sudan','Schnelle Eingreiftruppe',
     'Dschandschawid','Al-Faschir','Khartum','Hungersnot','Voelkermord','Paramilitaer'),
   'es', jsonb_build_array(
     'guerra de Sudan','ejercito sudanes','Fuerzas de Apoyo Rapido','El-Fasher',
     'Jartum','hambruna','paramilitar'),
   'fr', jsonb_build_array(
     'guerre au Soudan','armee soudanaise','Forces de soutien rapide','FSR',
     'el-Facher','el-Fasher','Darfour','Khartoum','Port-Soudan','paramilitaire'),
   'it', jsonb_build_array(
     'guerra in Sudan','esercito sudanese','Forze di Supporto Rapido','El-Fasher',
     'Darfur','Khartoum','paramilitare'),
   'ru', jsonb_build_array(
     'Судан','суданская армия','Силы быстрой поддержки','СБП','Бурхан',
     'Хемедти','Хеметти','Дагало','Джанджавид','Эль-Фашер','Дарфур','Кордофан',
     'Хартум','Порт-Судан','Омдурман','голод','геноцид','ополченцы'),
   'hi', jsonb_build_array(
     'सूडान','रैपिड सपोर्ट फोर्सेज','सूडानी सेना','बुरहान','हमदान दगालो',
     'अल-फाशेर','दारफुर','कोरडोफान','खारतूम','जनसंहार','अकाल'),
   'zh', jsonb_build_array(
     '苏丹','苏丹内战','苏丹军队','快速支援部队','布尔汉','赫梅蒂','达加洛',
     '法希尔','达尔富尔','科尔多凡','喀土穆','苏丹港','饥荒','种族灭绝'),
   'ar', jsonb_build_array(
     'السودان','السودانية','السوداني','قوات الدعم السريع','الدعم السريع',
     'حميدتي','دقلو','البرهان','الجيش السوداني','الجنجويد',
     'الفاشر','دارفور','كردفان','الخرطوم','بورتسودان','أم درمان','ود مدني',
     'نيالا','الجنينة','مجاعة','إبادة'),
   'ja', jsonb_build_array(
     'スーダン','スーダン内戦','スーダン軍','RSF','即応支援部隊','ブルハン',
     'ヘメティ','ダガロ','ダルフール','ハルツーム','コルドファン','エル・ファシャー',
     '飢饉','ジェノサイド')
 ),
 true, 'fn_anchor', 'sudan_civil_war');

-- ============================================================
-- 3. Narratives (3)
-- ============================================================

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('sudan_state_legitimacy', 'sudan_civil_war', 1, 2,
 'Legitimate state vs paramilitary', 'Legitimer Staat gegen Paramilitaer',
 'Sudan''s army is the constitutional state defending against an RSF mutiny',
 'Sudans Armee ist der verfassungsmaessige Staat gegen eine RSF-Meuterei',
 'Pan-Arab Egyptian, Saudi, and Turkish-state coverage frames the Sudanese army as the constitutional state defending against an armed mutiny by the RSF. The vocabulary: "constitutional authority", "armed rebellion", "RSF paramilitary mutiny", "territorial integrity", "national army", "counter-insurgency", "Burhan as legitimate sovereign". Islamist / Brotherhood elements within the army are treated as a manageable internal matter relative to the existential RSF threat. Prescription: international support for the Sudanese government, sanctions on RSF backers, no negotiations that legitimise RSF as a co-equal party.',
 'Panarabische aegyptische, saudische und tuerkische Staatsberichterstattung rahmt die sudanesische Armee als verfassungsmaessigen Staat gegen einen bewaffneten Aufstand der RSF. Vokabular: "verfassungsmaessige Autoritaet", "bewaffnete Rebellion", "RSF-paramilitaerische Meuterei", "territoriale Integritaet", "Nationalarmee", "Aufstandsbekaempfung", "Burhan als legitimer Souveraen". Islamistische / Bruderschafts-Elemente innerhalb der Armee gelten als kontrollierbares internes Thema gegenueber der existenziellen RSF-Bedrohung. Vorschrift: internationale Unterstuetzung der sudanesischen Regierung, Sanktionen gegen RSF-Unterstuetzer, keine Verhandlungen, die die RSF als gleichberechtigte Partei legitimieren.',
 ARRAY['MIDEAST-EGYPT','MIDEAST-SAUDI'],
 ARRAY['Al-Ahram','Al Arabiya','Arab News','Egypt Today','Khaleej Times','Daily Sabah','Anadolu Agency','The National'],
 ARRAY['constitutional authority','armed rebellion','RSF paramilitary','territorial integrity','national army','counter-insurgency','legitimate sovereign'],
 true),

('sudan_humanitarian_catastrophe', 'sudan_civil_war', 2, -1,
 'Humanitarian catastrophe and genocide', 'Humanitaere Katastrophe und Genozid',
 'Both sides commit atrocities; RSF violence in Darfur amounts to genocide',
 'Beide Seiten begehen Gewalttaten; RSF-Gewalt in Darfur kommt einem Genozid gleich',
 'UN, Western humanitarian, and pan-Arab non-aligned outlets frame the Sudan war as a humanitarian catastrophe with genocide-level violence concentrated in Darfur and El Fasher. Evidence: 12M displaced, induced famine via siege and aid blockade, systematic ethnic violence by RSF against Masalit and other African communities, hospital and aid-convoy strikes, UN investigative findings of genocide in El Fasher. The vocabulary: "genocide", "famine", "starvation as a weapon", "hospital strikes", "displaced", "mass atrocity", "Darfur ethnic cleansing", "civilian protection". Prescription: immediate ceasefire, unimpeded humanitarian access, accountability via ICC, neither side has a legitimate path to total victory.',
 'UN, westliche humanitaere und panarabische nicht-ausgerichtete Medien rahmen den Sudan-Krieg als humanitaere Katastrophe mit Gewalt auf Genozid-Niveau in Darfur und Al-Faschir. Belege: 12 Mio. Vertriebene, herbeigefuehrte Hungersnot durch Belagerung und Hilfsblockade, systematische ethnische Gewalt der RSF gegen Masalit und andere afrikanische Gemeinschaften, Angriffe auf Krankenhaeuser und Hilfskonvois, UN-Untersuchungen zu Genozid in Al-Faschir. Vokabular: "Genozid", "Hungersnot", "Aushungern als Waffe", "Angriffe auf Krankenhaeuser", "Vertriebene", "Massenverbrechen", "ethnische Saeuberung in Darfur", "Zivilschutz". Vorschrift: sofortiger Waffenstillstand, ungehinderter humanitaerer Zugang, Rechenschaft per IStGH, keine Seite hat einen legitimen Weg zum Totalsieg.',
 ARRAY['NON-STATE-EU','EUROPE-FRANCE','EUROPE-GERMANY','EUROPE-UK','AMERICAS-USA'],
 ARRAY['UN News','BBC World','Deutsche Welle','France 24 (EN)','Le Monde','The Guardian','Reuters','Associated Press','NPR','Sky News','Tagesschau','Al Jazeera','Financial Times'],
 ARRAY['genocide','famine','starvation','hospital strike','displaced','mass atrocity','Darfur','El Fasher','civilian protection','ICC'],
 true),

('sudan_proxy_war_critique', 'sudan_civil_war', 3, -2,
 'UAE-backed proxy war', 'Stellvertreterkrieg mit Unterstuetzung der VAE',
 'Sudan war is sustained by UAE arms to RSF; Egypt/Saudi back the army',
 'Sudan-Krieg wird durch VAE-Waffen an die RSF aufrechterhalten; Aegypten und Saudi-Arabien stuetzen die Armee',
 'Investigative international and Turkish/Iranian state media frame the Sudan war as "the world''s worst proxy war": the RSF is sustained by UAE arms transferred via Chad and Ottilien Ethiopian routes; Russian Africa Corps / Wagner extracts gold from RSF-held territories; Egypt and Saudi backing of the army is the counter-axis. External powers, not Sudanese choice, drive the war''s length. The vocabulary: "proxy war", "UAE arms", "Wagner gold", "Chad transit", "weapons pipeline", "Gulf interference". Prescription: international sanctions on RSF backers, transparency on arms flows, condition Gulf relationships on Sudan stance.',
 'Investigative internationale sowie tuerkische und iranische Staatsmedien rahmen den Sudan-Krieg als "weltweit schlimmsten Stellvertreterkrieg": die RSF werde durch VAE-Waffen ueber Tschad und aethiopische Routen versorgt; Russlands Africa Corps / Wagner foerdere Gold aus RSF-Gebieten; aegyptisch-saudische Stuetzung der Armee bilde die Gegenachse. Externe Maechte, nicht sudanesische Entscheidung, verlaengern den Krieg. Vokabular: "Stellvertreterkrieg", "VAE-Waffen", "Wagner-Gold", "Tschad-Transit", "Waffenpipeline", "Golf-Einmischung". Vorschrift: internationale Sanktionen gegen RSF-Unterstuetzer, Transparenz ueber Waffenfluesse, Golf-Beziehungen an Sudan-Position knuepfen.',
 ARRAY['MIDEAST-GULF','EUROPE-RUSSIA'],
 ARRAY['Al Jazeera','Anadolu Agency','TRT World','Daily Sabah','Press TV','Times of Israel','Deutsche Welle','Reuters','Wall Street Journal','Le Monde','Financial Times'],
 ARRAY['proxy war','UAE arms','Wagner','Chad transit','weapons pipeline','Gulf interference','Africa Corps','RSF backers'],
 true);

-- ============================================================
-- 4. Sanity check
-- ============================================================

DO $$
DECLARE
    n_fn integer; n_nar integer; n_anchor integer;
BEGIN
    SELECT COUNT(*) INTO n_fn FROM friction_nodes WHERE id = 'sudan_civil_war';
    SELECT COUNT(*) INTO n_nar FROM narratives_v2 WHERE fn_id = 'sudan_civil_war';
    SELECT COUNT(*) INTO n_anchor FROM taxonomy_v3
        WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'sudan_civil_war';
    IF n_fn <> 1 OR n_nar <> 3 OR n_anchor <> 1 THEN
        RAISE EXCEPTION 'Sudan FN sanity check failed: friction_nodes=%, narratives=%, fn_anchors=% (expected 1/3/1)',
            n_fn, n_nar, n_anchor;
    END IF;
END $$;

COMMIT;

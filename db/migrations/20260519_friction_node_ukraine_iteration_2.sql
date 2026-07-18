-- Ukraine theater iteration 2: corruption anchor tightening + "full-scale" framing relocation.
-- 2026-05-19
--
-- Two editorial fixes from review:
--
-- 1. ukraine_official_corruption anchor caught generic-verb false positives
--    ("arrest", "raid", "fraud", "investigation", "audit", "charge") that
--    matched espionage and grain-theft stories. Tightened to corruption-
--    specific atoms + institutional acronyms only. Also dropped transient
--    political leader names per spec rule 4.
--
-- 2. "Full-scale war/invasion" is a Western/Ukrainian narrative construct.
--    Russia's framing is precisely that the operation is limited in scope
--    and methods. Moved the framing-loaded vocabulary out of neutral
--    description text into narrative-level framing_keywords, where stance
--    is properly attached. Theater description uses neutral "Russia-Ukraine
--    war (initiated 24 February 2022)".

BEGIN;

-- ============================================================
-- 1. Tighten ukraine_official_corruption fn_anchor
-- ============================================================

UPDATE taxonomy_v3
SET aliases = jsonb_build_object(
   'en', jsonb_build_array(
     'NABU','SAP','SAPO','HACC','VAKS','NACP','ARMA','PGO','SBI','DBR',
     'corruption','bribery','bribe','embezzlement','kickback',
     'indictment','indicted','prosecution','prosecuted','convicted','conviction',
     'anti-corruption','transparency',
     'defence procurement','defense procurement','procurement scandal','procurement fraud',
     'asset declaration','illicit enrichment','undeclared assets',
     'asset recovery','asset seizure','asset forfeiture',
     'EU conditionality','IMF conditionality','reform progress','reform track',
     'High Anti-Corruption Court','Anti-Corruption Action Centre','AntAC'),
   'de', jsonb_build_array(
     'NABU','SAP','HACC','NACP','ARMA',
     'Korruption','Bestechung','Schmiergeld','Unterschlagung','Veruntreuung',
     'Anklageerhebung','Verurteilung','Antikorruption','Transparenz',
     'Ruestungsbeschaffung','Beschaffungsskandal','Vermoegenserklaerung',
     'Vermoegensrueckfuehrung','EU-Konditionalitaet','IWF-Konditionalitaet',
     'Reformfortschritt','Antikorruptionsgericht','Antikorruptionsbuero'),
   'es', jsonb_build_array(
     'NABU','SAP','HACC','NACP',
     'corrupcion','soborno','malversacion','desfalco',
     'acusacion','condena','anticorrupcion','transparencia',
     'adquisicion de defensa','escandalo de adquisicion','declaracion de patrimonio',
     'enriquecimiento ilicito','condicionalidad de la UE','condicionalidad del FMI',
     'progreso de reforma','tribunal anticorrupcion','oficina anticorrupcion'),
   'fr', jsonb_build_array(
     'NABU','SAP','HACC','NACP',
     'corruption','pot-de-vin','detournement','malversation',
     'mise en examen','condamnation','anti-corruption','anticorruption','transparence',
     'marche public de defense','scandale de marche','declaration de patrimoine',
     'enrichissement illicite','conditionnalite de l''UE','conditionnalite du FMI',
     'progres de reforme','tribunal anticorruption','bureau anticorruption'),
   'it', jsonb_build_array(
     'NABU','SAP','HACC','NACP',
     'corruzione','tangente','appropriazione indebita','peculato',
     'rinvio a giudizio','condanna','anticorruzione','trasparenza',
     'appalto della difesa','scandalo appalti','dichiarazione patrimoniale',
     'arricchimento illecito','condizionalita UE','condizionalita FMI',
     'progresso di riforma','tribunale anticorruzione','ufficio anticorruzione'),
   'ru', jsonb_build_array(
     'НАБУ','САП','ВАКС','НАЗК','АРМА',
     'коррупция','взятка','взяточничество','хищение','растрата','откат',
     'антикоррупция','антикоррупционный','прозрачность',
     'оборонзаказ','госзакупки','закупочный скандал','коррупционный скандал',
     'декларация о доходах','незаконное обогащение','необъявленные активы',
     'возврат активов','конфискация активов',
     'условия ЕС','условия МВФ','прогресс реформ',
     'антикоррупционный суд','антикоррупционное бюро'),
   'hi', jsonb_build_array(
     'NABU','SAP','HACC','NACP',
     'भ्रष्टाचार','रिश्वत','गबन','घोटाला',
     'भ्रष्टाचार विरोधी','पारदर्शिता',
     'रक्षा खरीद','खरीद घोटाला','संपत्ति घोषणा','अवैध संवर्धन',
     'भ्रष्टाचार विरोधी न्यायालय','भ्रष्टाचार विरोधी ब्यूरो'),
   'zh', jsonb_build_array(
     'NABU','SAP','HACC','NACP',
     '腐败','贪腐','贪污','受贿','行贿','挪用公款','回扣',
     '反腐败','反腐','透明度',
     '国防采购','采购丑闻','腐败丑闻','资产申报','非法致富',
     '欧盟条件','国际货币基金组织条件','改革进展',
     '反腐败法院','反腐败局'),
   'ar', jsonb_build_array(
     'NABU','SAP','HACC','NACP',
     'فساد','رشوة','اختلاس','عمولة','نهب',
     'مكافحة الفساد','شفافية',
     'مشتريات دفاعية','فضيحة مشتريات','فضيحة فساد','اقرار ذمة مالية',
     'اثراء غير مشروع','استرداد اصول','مصادرة اصول',
     'شروط الاتحاد الاوروبي','شروط صندوق النقد','تقدم الاصلاح',
     'محكمة مكافحة الفساد','مكتب مكافحة الفساد'),
   'ja', jsonb_build_array(
     'NABU','SAP','HACC','NACP',
     '汚職','収賄','贈収賄','横領','着服','キックバック',
     '反汚職','透明性',
     '防衛調達','調達スキャンダル','汚職スキャンダル','資産申告','違法蓄財',
     'EU条件','IMF条件','改革の進展',
     '反汚職裁判所','反汚職局')
 )
WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'ukraine_official_corruption';

-- ============================================================
-- 2. Neutralize theater description ("full-scale" -> date anchor)
-- ============================================================

UPDATE friction_nodes
SET description_en = 'The Russia-Ukraine war (initiated 24 February 2022) and its surrounding contest of framings: battlefield operations, Western military and economic aid, peace negotiations, anti-corruption investigations of Ukrainian officials, and the sanctions regime on Russia. The scope of the war itself is contested vocabulary — Ukrainian/Western framing as full-scale invasion versus Russian framing as a limited special military operation. Coverage spans Ukrainian, Russian, Western mainstream, Eastern European, and Global South press with sharply divergent vocabularies for the same events.',
    description_de = 'Der russisch-ukrainische Krieg (begonnen am 24. Februar 2022) und sein umgebender Rahmungs-Wettstreit: Gefechtsoperationen, westliche militaerische und wirtschaftliche Hilfe, Friedensverhandlungen, Anti-Korruptionsermittlungen gegen ukrainische Beamte und das Sanktionsregime gegen Russland. Der Umfang des Krieges selbst ist umkaempftes Vokabular — ukrainisch-westliche Rahmung als voll entfaltete Invasion gegenueber russischer Rahmung als begrenzte militaerische Spezialoperation. Berichterstattung umfasst ukrainische, russische, westliche, osteuropaeische und Global-South-Medien mit stark divergierenden Vokabularen fuer dieselben Ereignisse.'
WHERE id = 'ukraine_war_theater';

-- ============================================================
-- 3. Move "full-scale invasion" framing into narrative cells
-- ============================================================

-- Ukrainian/Western maximalist narrative gains "full-scale" vocabulary
UPDATE narratives_v2
SET framing_keywords = framing_keywords || ARRAY[
    'full-scale invasion','full-scale war','all-out war','total war',
    'unprovoked full-scale','war of aggression'
  ]
WHERE id = 'ukraine_resistance_solidarity';

-- Russian SMO narrative gains the explicit "limited scope" vocabulary
UPDATE narratives_v2
SET framing_keywords = framing_keywords || ARRAY[
    'limited operation','targeted operation','restraint in scope',
    'not full-scale','partial mobilisation','our people','brotherly people',
    'fraternal nation'
  ]
WHERE id = 'russia_special_military_operation';

-- ============================================================
-- 4. Sanity check
-- ============================================================

DO $$
DECLARE
    n_anchor_langs integer; n_fkw_solidarity integer; n_fkw_smo integer;
BEGIN
    SELECT jsonb_array_length(aliases->'en')
      INTO n_anchor_langs
      FROM taxonomy_v3
      WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'ukraine_official_corruption';
    IF n_anchor_langs IS NULL OR n_anchor_langs < 20 THEN
        RAISE EXCEPTION 'Corruption anchor tighten lost too many EN entries (got %)', n_anchor_langs;
    END IF;

    SELECT array_length(framing_keywords,1) INTO n_fkw_solidarity
      FROM narratives_v2 WHERE id = 'ukraine_resistance_solidarity';
    SELECT array_length(framing_keywords,1) INTO n_fkw_smo
      FROM narratives_v2 WHERE id = 'russia_special_military_operation';
    IF n_fkw_solidarity < 17 OR n_fkw_smo < 19 THEN
        RAISE EXCEPTION 'Framing keyword update failed: solidarity=%, smo=%',
            n_fkw_solidarity, n_fkw_smo;
    END IF;
END $$;

COMMIT;

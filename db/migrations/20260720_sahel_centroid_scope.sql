-- AFRICA-SAHEL centroid scope fix (2026-07-20), companion to
-- 20260720_sahel_theater_structure.sql.
--
-- Measured against 180d: of 1,105 titles carrying AFRICA-SAHEL, ~30% are
-- off-theater, and the largest single cause is that the centroid claims three
-- coastal West African states that are not part of this conflict.
--
--   Senegal  196 titles -- only 4 have ANY Sahel-security link. The rest is the
--            Sonko/Faye leadership row, IMF/undisclosed-debt, the anti-gay law,
--            and the AFCON hosting dispute. Senegal is a coastal democracy with
--            no junta and no insurgency.
--   Guinea    68 titles -- Equatorial Guinea (papal tour), Papua New Guinea,
--            and bauxite/gold export economics.
--   Gambia    -- same class, no Sahel-security coverage at all.
--
-- These move to AFRICA-WEST, which already holds Ghana / Ivory Coast / Benin /
-- Togo / Liberia / Sierra Leone / Cape Verde / Cameroon and was simply missing
-- them. No FN outside this theater uses AFRICA-SAHEL or AFRICA-WEST, so the
-- blast radius is limited to title labelling.
--
-- 'Guinea' IS DELIBERATELY NOT ADDED TO AFRICA-WEST. Bare 'Guinea' also matches
-- Equatorial Guinea (Central Africa) and Papua New Guinea (Oceania) -- moving it
-- would import a known collision into a clean centroid rather than fix it.
-- AFRICA-WEST already carries 'Gulf of Guinea' as a distinct alias. Guinea-
-- Conakry needs its own decision; only the unambiguous capital is added here.
-- Left as an open item.
--
-- 'AES' is replaced by its spelled-out forms. Bare 'AES' resolved to the AES
-- Corp utility in 11 of 14 matches (BlackRock/EQT $33.4bn buyout, AES Galabovo
-- power plant, "US Premarket Movers: AES"). The spelled-out Alliance name is
-- what actually appears in on-topic French coverage.
--
-- NOT FIXED HERE, recorded for the record:
--   * 'Niger' matching Nigerian geography (Niger State / Niger Delta / Niger
--     Bridge, ~39 titles from Punch and Vanguard) is genuine whole-word
--     ambiguity between the country and Nigerian internal toponyms. It cannot
--     be fixed at centroid level without losing Niger the country. Handled in
--     the atomics' bundles instead.
--   * 'mali' matching Serbo-Croatian "mali" (= small), 23 titles in hr/sl/ca.
--     An EN alias reaching cross-language titles is a matcher-level issue, out
--     of scope. Neutralised in practice by bundle purity -- "Tramp najavio
--     suspenziju poreza" cannot match JNIM/Kidal/junta vocabulary.
--
-- This migration re-labels NOTHING retroactively: titles already carrying
-- AFRICA-SAHEL keep it. It corrects labelling going forward. The current 180d
-- window is protected by bundle purity instead -- no Sahel atomic carries
-- Senegal or Guinea vocabulary.
--
-- jsonb_path_query_array + filter is used so the drop is by exact string and a
-- typo silently removes nothing rather than corrupting the array.

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. AFRICA-SAHEL A: drop Senegal / Guinea / Gambia and their capitals.
-- ---------------------------------------------------------------------------
UPDATE taxonomy_v3
SET aliases = jsonb_build_object(
        'en', jsonb_path_query_array(aliases->'en', '$[*] ? (@ != "Senegal" && @ != "Guinea" && @ != "The Gambia" && @ != "Dakar" && @ != "Conakry" && @ != "Banjul")'),
        'fr', jsonb_path_query_array(aliases->'fr', '$[*] ? (@ != "Sénégal" && @ != "Guinée" && @ != "Gambie")'),
        'ar', jsonb_path_query_array(aliases->'ar', '$[*] ? (@ != "السنغال" && @ != "غينيا" && @ != "غامبيا" && @ != "داكار" && @ != "كوناكري" && @ != "بانجول")'),
        'ru', jsonb_path_query_array(aliases->'ru', '$[*] ? (@ != "Сенегал" && @ != "Гвинея" && @ != "Гамбия" && @ != "Дакар" && @ != "Конакри" && @ != "Банджул")'),
        'zh', jsonb_path_query_array(aliases->'zh', '$[*] ? (@ != "塞内加尔" && @ != "几内亚" && @ != "冈比亚" && @ != "达喀尔" && @ != "科纳克里" && @ != "班珠尔")'),
        'ja', jsonb_path_query_array(aliases->'ja', '$[*] ? (@ != "セネガル" && @ != "ギニア" && @ != "ガンビア" && @ != "ダカール" && @ != "コナクリ" && @ != "バンジュール")'),
        'hi', jsonb_path_query_array(aliases->'hi', '$[*] ? (@ != "सेनेगल" && @ != "गिनी" && @ != "गाम्बिया" && @ != "डकार" && @ != "कोनाक्री" && @ != "बंजुल")')
    ),
    updated_at = NOW()
WHERE centroid_id = 'AFRICA-SAHEL'
  AND item_raw = 'AFRICA-SAHEL A: Geographic & Identity Anchors';

-- ---------------------------------------------------------------------------
-- 2. AFRICA-WEST A: adopt Senegal / Gambia + unambiguous capitals.
--    'Guinea' withheld deliberately (see header).
-- ---------------------------------------------------------------------------
UPDATE taxonomy_v3
SET aliases = jsonb_set(
        jsonb_set(aliases, '{en}',
            (aliases->'en') || '["Senegal","The Gambia","Dakar","Banjul","Conakry"]'::jsonb),
        '{fr}',
            (aliases->'fr') || '["Sénégal","Gambie"]'::jsonb),
    updated_at = NOW()
WHERE centroid_id = 'AFRICA-WEST'
  AND item_raw = 'AFRICA-WEST A: Geographic & Identity Anchors';

-- ---------------------------------------------------------------------------
-- 3. AFRICA-SAHEL C: bare 'AES' -> spelled-out Alliance forms.
-- ---------------------------------------------------------------------------
UPDATE taxonomy_v3
SET aliases = jsonb_set(aliases, '{en}',
        jsonb_path_query_array(aliases->'en', '$[*] ? (@ != "AES")')
        || '["Alliance of Sahel States","Confederation of Sahel States"]'::jsonb),
    updated_at = NOW()
WHERE centroid_id = 'AFRICA-SAHEL'
  AND item_raw = 'AFRICA-SAHEL C: Regional Blocs, Missions & External Operations';

UPDATE taxonomy_v3
SET aliases = jsonb_set(aliases, '{fr}',
        (aliases->'fr') || '["Alliance des États du Sahel","Confédération AES"]'::jsonb),
    updated_at = NOW()
WHERE centroid_id = 'AFRICA-SAHEL'
  AND item_raw = 'AFRICA-SAHEL C: Regional Blocs, Missions & External Operations';

COMMIT;

-- ROOT FIX: OCEANIA-PAPUANEWGUINEA centroid_anchor was 97% garbage.
--
-- Non-English centroid aliases match by pure SUBSTRING (normalize_text + the
-- substring path in pipeline/phase_2/match_centroids.py) -- no word-boundary
-- protection, which is structurally impossible for CJK. The Japanese alias
-- `ラエ` (Lae, a PNG city) is only two katakana, and is a substring of:
--     イスラエル  (Israel)      -> 362 titles
--     バラエティー (variety)     -> TV entertainment titles
-- Measured on local: 390 titles carried OCEANIA-PAPUANEWGUINEA, only 13 were
-- about PNG. titles_v3.matched_aliases literally contains "ラエ" on the Israel
-- ones, which is how this was confirmed rather than inferred.
--
-- This is vocab-spec rule 6b ("no short/generic non-English aliases") violated
-- inside a centroid_anchor. The rule is written for fn_anchor bundles but applies
-- identically here -- same matching path.
--
-- Dropped: `ラエ` (ja), `لاي` (ar, 1 hit: an Iranian-forces statement),
--          `लाए` (hi, 0 hits but it is the common Hindi word "brought").
-- KEPT: the EN `Lae` (ASCII goes through a \bLae\b word-boundary regex, so it is
-- safe), plus `Лаэ` (ru) and `莱城` (zh), both measured at 0 collisions.
--
-- Approved by the user 2026-07-17 (taxonomy change + bulk UPDATE on titles_v3).
-- Found during the australia_theater build: pacific_island_contest was being
-- polluted with Israel/Iran events, because the event gate has two SEPARATE
-- EXISTS clauses -- one member title supplies the centroid, a DIFFERENT one
-- matches an alias.
--
-- The wider class (4,813 unaudited short non-EN centroid aliases, plus an
-- unexplained ~60% pollution of OCEANIA-POLYNESIA whose tags come from no alias
-- at all) is tracked separately -- NOT fixed here.
SET client_encoding TO 'UTF8';

-- (1) Remove the colliding aliases from the anchor.
UPDATE taxonomy_v3 SET
  aliases = jsonb_set(
              jsonb_set(
                jsonb_set(aliases, '{ja}', (aliases->'ja') - 'ラエ'),
                '{ar}', (aliases->'ar') - 'لاي'),
              '{hi}', (aliases->'hi') - 'लाए'),
  updated_at = NOW()
WHERE taxonomy_function = 'centroid_anchor'
  AND linked_id = 'OCEANIA-PAPUANEWGUINEA';

-- (2) Strip the bogus tag from already-matched titles. match_centroids.py has no
--     --reprocess path, so this is a targeted UPDATE rather than a re-run.
--     Only rows where NO surviving PNG alias matches are touched; the 13 real PNG
--     titles keep their tag. Two rows are left with an empty centroid_ids array --
--     both are genuinely out-of-scope (an Iranian-forces statement, a TV Tokyo
--     variety-show story) and empty is a valid "no match / out of scope" state
--     (1,718 such rows already exist).
UPDATE titles_v3 SET
  centroid_ids = array_remove(centroid_ids, 'OCEANIA-PAPUANEWGUINEA'),
  matched_aliases = matched_aliases - 'ラエ' - 'لاي',
  updated_at = NOW()
WHERE centroid_ids @> ARRAY['OCEANIA-PAPUANEWGUINEA']
  AND NOT (
    title_display ~ '\m(Papua|Moresby|Lae|Bougainville)\M'
    OR title_display ~* 'Bismarck Sea|Torres Strait'
    OR title_display ILIKE ANY (ARRAY[
      '%パプアニューギニア%','%ポートモレスビー%','%ブーゲンビル%','%ビスマルク海%','%トレス海峡%',
      '%Папуа%','%Порт-Морсби%','%Лаэ%','%Бугенвиль%','%Море Бисмарка%','%Торресов пролив%',
      '%بابوا غينيا الجديدة%','%بورت مورسبي%','%بوغانفيل%','%بحر بسمارك%','%مضيق توريس%',
      '%पापुआ न्यू गिनी%','%पोर्ट मोरेस्बी%','%बोगेनविल%','%बिस्मार्क सागर%','%टॉरेस जलडमरूमध्य%',
      '%巴布亚新几内亚%','%莫尔兹比港%','%莱城%','%布干维尔%','%俾斯麦海%','%托雷斯海峡%'
    ])
  );

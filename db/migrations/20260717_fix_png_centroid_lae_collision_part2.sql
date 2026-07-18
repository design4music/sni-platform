-- Completes 20260717_fix_png_centroid_lae_collision.sql. Statement (1) -- the
-- anchor prune -- committed; statement (2) failed because titles_v3.matched_aliases
-- is JSONB, not text[], so array_remove() does not apply. The jsonb `-` operator
-- removes a matching array element instead. Statement (1) is not repeated.
SET client_encoding TO 'UTF8';

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

-- Centroid anchors: weapon names are not country anchors (2026-07-11)
-- See generator docstring. Root cause of the phantom EUROPE-UKRAINE /
-- EUROPE-GERMANY tags on Iran/Gulf Patriot coverage, Starlink product
-- news, etc. Includes the title reset for Phase 2 rematch; on Render the
-- daemon's matching slot picks the reset titles up automatically.
BEGIN;

UPDATE taxonomy_v3 SET aliases = '{"en": ["Neptune missile", "Stugna-P", "Bohdana", "Baba Yaga"], "ru": ["Нептун", "Стугна-П", "Богдана", "Баба-Яга"]}'::jsonb WHERE id = 'f7762b03-3743-4803-8d2e-00f072e536d5';

UPDATE taxonomy_v3 SET aliases = '{"ar": ["ليوبارد 2", "آيريس-تي", "PzH 2000", "غيبارد"], "en": ["Rheinmetall", "Leopard 2", "IRIS-T", "PzH 2000", "Gepard"], "hi": ["लियोपार्ड 2", "आईरिस-टी", "PzH 2000", "गेपार्ड"], "ja": ["レオパルト2", "IRIS-T", "PzH2000", "ゲパルト", "ドイツ再軍備"], "ru": ["Leopard 2", "IRIS-T", "PzH 2000", "Gepard", "перевооружение Бундесвера"], "zh": ["豹2坦克", "IRIS-T防空系统", "PzH 2000", "猎豹防空坦克", "德国重新武装"]}'::jsonb WHERE id = 'fce73cc5-2652-4bc5-8dba-d712410e945d';

UPDATE titles_v3
   SET processing_status = 'pending', updated_at = NOW()
 WHERE pubdate_utc > NOW() - INTERVAL '180 days'
   AND matched_aliases ?| ARRAY['patriot','himars','starlink','bayraktar','leopard','atacms','storm shadow','scalp','патриот','байрактар','леопард','старлинк','باتريوت','पैट्रियट','パトリオット','爱国者系统']::text[];

COMMIT;

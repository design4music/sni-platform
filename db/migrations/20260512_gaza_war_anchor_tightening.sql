-- Tighten gaza_war fn_anchor: replace standalone 'ceasefire' (in every
-- language) with Gaza/Hamas compounds. The centroid filter catches pure-
-- Iran titles, but titles mentioning Israel AND Iran (where Israel is
-- merely contextual to an Iran-ceasefire story) sneak past — fixed by
-- requiring ceasefire to be tied to Gaza/Hamas explicitly.
-- Also tighten 'hostages' standalone for the same reason.
-- 2026-05-12

BEGIN;

UPDATE taxonomy_v3
SET aliases = jsonb_build_object(
    'ar', jsonb_build_array(
        'غزة','الحرب على غزة','حماس','رفح','خان يونس',
        'الجيش الإسرائيلي في غزة','مجاعة غزة','اونروا',
        -- compound ceasefire / truce terms
        'وقف إطلاق النار في غزة','هدنة غزة','هدنة حماس','اتفاق وقف إطلاق النار غزة',
        -- compound hostages
        'الأسرى في غزة','أسرى حماس'
    ),
    'de', jsonb_build_array(
        'Gaza','Gaza-Krieg','Gazastreifen','Hamas','Rafah','Khan Younis',
        'Hungersnot Gaza','UNRWA','Hilfsgüter Gaza','Sinwar',
        -- compound Waffenstillstand / Geiseln
        'Waffenstillstand Gaza','Gaza-Waffenstillstand','Hamas Waffenstillstand',
        'Gaza-Geiseln','Geiseln in Gaza','Hamas-Geiseln'
    ),
    'en', jsonb_build_array(
        'Gaza','Gaza war','Gaza Strip','Hamas','Rafah','Khan Younis',
        'famine Gaza','UNRWA','aid Gaza','Sinwar','October 7','7 October',
        'Hamas tunnels','Hamas leadership','Yahya Sinwar','Mohammed Deif','Haniyeh',
        -- compound ceasefire / hostages
        'Gaza ceasefire','Hamas ceasefire','Gaza truce','Hamas truce',
        'hostage deal','two-stage deal','Gaza hostages','Hamas hostages','Israeli hostages'
    ),
    'es', jsonb_build_array(
        'Gaza','Franja de Gaza','Hamás','Rafah','hambruna Gaza','UNRWA',
        'alto el fuego Gaza','alto el fuego en Gaza','tregua Gaza',
        'rehenes en Gaza','rehenes de Hamás'
    ),
    'fr', jsonb_build_array(
        'Gaza','bande de Gaza','Hamas','Rafah','famine Gaza','UNRWA',
        'cessez-le-feu à Gaza','cessez-le-feu Gaza','trêve Gaza',
        'otages à Gaza','otages du Hamas'
    ),
    'hi', jsonb_build_array(
        'गाजा','हमास','रफह',
        'गाजा युद्धविराम','गाजा बंधक'
    ),
    'it', jsonb_build_array(
        'Gaza','striscia di Gaza','Hamas','Rafah','carestia Gaza','UNRWA',
        'cessate il fuoco a Gaza','tregua Gaza',
        'ostaggi a Gaza','ostaggi di Hamas'
    ),
    'ja', jsonb_build_array(
        'ガザ','ガザ地区','ハマス','ラファ',
        'ガザ停戦','ガザの停戦','ハマスの人質','ガザの人質'
    ),
    'ru', jsonb_build_array(
        'Газа','сектор Газа','ХАМАС','Рафах','голод в Газе','БАПОР','Синвар',
        'прекращение огня в Газе','перемирие в Газе',
        'заложники в Газе','заложники ХАМАС'
    ),
    'zh', jsonb_build_array(
        '加沙','加沙地带','哈马斯','拉法','加沙饥荒','辛瓦尔',
        '加沙停火','哈马斯停火','加沙人质','哈马斯人质'
    )
)
WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'gaza_war';

COMMIT;

-- Israel theater seed: 1 theater + 4 atomic FNs + 12 narratives + 5 fn_anchor bundles.
-- 2026-05-12
--
-- Architecture follows the iran_theater pattern (D-075..D-079):
--   * Theater FN carries broad cross-FN narratives (Israeli self-defense,
--     Palestinian framing, EU two-state pathway, multipolar anti-Israel
--     alignment).
--   * Atomic FNs are theater-scoped — each carries a pro/con narrative
--     pair from its specific lens.
--   * Stance is toward Israel (the theater's primary actor). Iran/Hezbollah
--     framings register as -1 / -2 in this theater even though they read
--     as +1 / +2 in iran_theater.

BEGIN;

-- ============================================================
-- 1. Theater + atomic friction_nodes
-- ============================================================

INSERT INTO friction_nodes (id, name_en, name_de, description_en, description_de,
    editorial_summary_en, editorial_summary_de, centroid_ids, fn_type, member_fn_ids,
    is_active, display_order)
VALUES
('israel_theater', 'Israel in regional confrontation', 'Israel in regionalen Konflikten',
 'Israel''s multi-front security posture: the Gaza war with Hamas, the northern border with Hezbollah, direct exchanges with Iran, and the West Bank settlement question. Coverage clusters around right-of-self-defense framing on one side and disproportionate-force / occupation framing on the other.',
 'Israels Sicherheitslage an mehreren Fronten: Krieg gegen die Hamas in Gaza, Nordgrenze mit der Hisbollah, direkter Schlagabtausch mit dem Iran und die Siedlungsfrage im Westjordanland. Die Berichterstattung pendelt zwischen Selbstverteidigungs-Rahmung auf der einen und Besatzungs- / Verhaeltnismaessigkeits-Kritik auf der anderen Seite.',
 'Israel''s confrontations cluster around four operational surfaces — Gaza, Lebanon, Iran direct, and the West Bank — each carrying its own pro/con stance pair. The umbrella narratives above run across them: Israeli existential self-defense, Palestinian genocide / humanitarian framing, EU two-state pathway, and multipolar anti-Israel alignment.',
 'Israels Konflikte gliedern sich in vier operative Felder — Gaza, Libanon, Iran-Direktkonfrontation, Westjordanland — jeweils mit eigenem Pro/Kontra-Paar. Die uebergreifenden Narrative dieser Konfliktzone: israelische Existenzverteidigung, palaestinensische Genozid-/Humanitaer-Rahmung, EU-Zweistaaten-Linie und multipolare Anti-Israel-Stimmen.',
 ARRAY['MIDEAST-ISRAEL','MIDEAST-PALESTINE','MIDEAST-LEVANT','MIDEAST-IRAN','MIDEAST-GULF','AMERICAS-USA','EUROPE-UK','EUROPE-FRANCE','EUROPE-GERMANY','NON-STATE-EU'],
 'theater', ARRAY['gaza_war','israel_lebanon_border','israel_iran_strikes','west_bank_settlements'],
 true, 20),

('gaza_war', 'Gaza war', 'Gaza-Krieg',
 'The Hamas-Israel war triggered by the 7 October 2023 attacks: IDF ground operations, hostage diplomacy, humanitarian conditions, Rafah, ceasefire pressure. Narrative contest between Hamas-destruction imperatives and humanitarian / proportionality critique.',
 'Der Krieg zwischen Hamas und Israel seit dem 7. Oktober 2023: IDF-Bodenoperationen, Geisel-Diplomatie, humanitaere Lage, Rafah, Druck auf einen Waffenstillstand. Narrativer Wettstreit zwischen der Forderung, die Hamas zu zerschlagen, und Kritik an humanitaeren Folgen und Verhaeltnismaessigkeit.',
 'Gaza is the most intensively covered Mideast surface of the past year. Israeli sources frame the war as a non-negotiable response to October 7 and a hostage rescue. Pan-Arab and pro-Palestinian outlets emphasize civilian death tolls, displacement, blockade conditions, and the legal-genocide question now before the ICJ.',
 'Gaza ist die meistberichtete Nahost-Front des vergangenen Jahres. Israelische Quellen rahmen den Krieg als nicht verhandelbare Antwort auf den 7. Oktober und als Geiselrettung. Panarabische und propalaestinensische Medien betonen zivile Opfer, Vertreibung, Blockade und die Genozid-Frage vor dem IGH.',
 ARRAY['MIDEAST-ISRAEL','MIDEAST-PALESTINE','AMERICAS-USA','MIDEAST-LEVANT','MIDEAST-EGYPT'],
 'atomic', NULL, true, 21),

('israel_lebanon_border', 'Israel-Lebanon border', 'Grenze Israel-Libanon',
 'Cross-border conflict between the IDF and Hezbollah along the northern Israeli border: rocket exchanges, targeted strikes in Beirut, displacement on both sides, UNIFIL''s role, and the status of UN Resolution 1701.',
 'Grenzkonflikt zwischen IDF und Hisbollah entlang der israelischen Nordgrenze: Raketenbeschuss, gezielte Schlaege in Beirut, Vertreibung auf beiden Seiten, Rolle der UNIFIL und Status der UN-Resolution 1701.',
 'Hezbollah opened a "support front" in October 2023 and intensified in 2024-2026. Israeli framing treats the border as a self-defense theater requiring Hezbollah''s push north of the Litani; Hezbollah and allied outlets frame it as part of the regional resistance front and present Israeli strikes as collective punishment of Lebanon.',
 'Die Hisbollah eroeffnete im Oktober 2023 eine "Unterstuetzungsfront" und intensivierte 2024-2026. Israelische Quellen rahmen die Grenze als Selbstverteidigungs-Front mit der Forderung, die Hisbollah nordwaerts vom Litani zurueckzudraengen; Hisbollah-nahe Medien sehen den Widerstand als regional und werten israelische Schlaege als Kollektivstrafe gegen den Libanon.',
 ARRAY['MIDEAST-ISRAEL','MIDEAST-LEVANT','MIDEAST-IRAN'],
 'atomic', NULL, true, 22),

('israel_iran_strikes', 'Israel-Iran direct strikes', 'Direkte Schlagabtausche Israel-Iran',
 'Direct kinetic exchange between Israel and Iran: April 2024 Iranian missile/drone wave, Israeli retaliations on Iranian air defenses, the October 2024 strike, Iranian retaliation, and Israeli strikes on Iranian nuclear / IRGC assets.',
 'Direkter militaerischer Schlagabtausch zwischen Israel und Iran: iranische Raketen-/Drohnen-Welle im April 2024, israelische Vergeltung gegen iranische Luftabwehr, der Angriff im Oktober 2024, iranische Antwortschlaege und israelische Schlaege gegen iranische Nuklear-/IRGC-Ziele.',
 'The Iran-Israel war moved from shadow to overt in April 2024 and has continued through 2025-2026 in escalating cycles. Israeli sources frame it as defensive / preemptive action against an existential nuclear-armed enemy; Iranian and aligned sources frame Israeli strikes as aggression and Iranian retaliation as legitimate state self-defense within the UN Charter.',
 'Der iranisch-israelische Krieg verlagerte sich im April 2024 aus dem Verdeckten ins Offene und setzt sich 2025-2026 in eskalierenden Zyklen fort. Israelische Quellen rahmen ihn als defensive bzw. praeventive Massnahme gegen einen existenziellen nuklear bewaffneten Gegner; iranische und verbuendete Quellen werten israelische Schlaege als Aggression und iranische Vergeltung als legitime staatliche Selbstverteidigung im Rahmen der UN-Charta.',
 ARRAY['MIDEAST-ISRAEL','MIDEAST-IRAN','AMERICAS-USA'],
 'atomic', NULL, true, 23),

('west_bank_settlements', 'West Bank settlements', 'Siedlungen im Westjordanland',
 'Israeli settlement expansion in the West Bank, settler violence, IDF operations in Jenin / Nablus, Palestinian Authority dysfunction, and the recurring two-state pathway question.',
 'Israelische Siedlungserweiterung im Westjordanland, Siedlergewalt, IDF-Operationen in Dschenin und Nablus, Funktionskrise der Palaestinensischen Autonomiebehoerde und die wiederkehrende Frage nach einer Zweistaatenloesung.',
 'The West Bank is the slow-burn surface of the Israeli-Palestinian conflict — high-intensity coverage when settler violence spikes or IDF raids escalate, but always present. Israeli right-wing framing emphasizes biblical Judea-Samaria sovereignty; Palestinian / international human rights framing emphasizes occupation, settler impunity, and apartheid-system arguments now appearing in mainstream Western coverage.',
 'Das Westjordanland ist die latente Front des israelisch-palaestinensischen Konflikts — hohe Berichterstattungs-Intensitaet bei Siedlergewalt oder IDF-Razzien, aber stets praesent. Die israelische Rechte rahmt biblische Judaea-und-Samaria-Souveraenitaet; palaestinensische und internationale Menschenrechts-Stimmen betonen Besatzung, Straflosigkeit von Siedlern und (zunehmend auch im westlichen Mainstream) Apartheid-Argumente.',
 ARRAY['MIDEAST-ISRAEL','MIDEAST-PALESTINE','AMERICAS-USA','NON-STATE-EU'],
 'atomic', NULL, true, 24);

-- ============================================================
-- 2. fn_anchor bundles in taxonomy_v3
-- (Multi-lingual surface vocabulary; analyst should expand via the
--  deepseek extractor on Render corpus before going live.)
-- ============================================================

INSERT INTO taxonomy_v3 (item_raw, aliases, is_active, taxonomy_function, linked_id) VALUES

('israel_theater fn_anchor',
 jsonb_build_object(
   'ar', jsonb_build_array('إسرائيل','اسرائيل','تل أبيب','نتنياهو','الجيش الإسرائيلي','غزة','حماس','حزب الله','الضفة الغربية','الأقصى','الحرب على غزة','إيران واسرائيل','جيش الدفاع'),
   'de', jsonb_build_array('Israel','Tel Aviv','Netanjahu','Netanyahu','israelische Armee','IDF','Gaza','Hamas','Hisbollah','Westjordanland','Iran','Krieg in Gaza','Geiseln','Siedlungen'),
   'en', jsonb_build_array('Israel','Israeli','Tel Aviv','Netanyahu','IDF','Gaza','Hamas','Hezbollah','West Bank','Iran-Israel','hostages','Knesset','Israeli army','Israeli strikes','Israeli forces','Mossad','Shin Bet','Iron Dome','Ben Gvir','Smotrich','Gallant','Katz','Likud'),
   'es', jsonb_build_array('Israel','israelí','Tel Aviv','Netanyahu','FDI','Gaza','Hamás','Hezbolá','Cisjordania','rehenes'),
   'fr', jsonb_build_array('Israël','israélien','Tel Aviv','Nétanyahou','Tsahal','Gaza','Hamas','Hezbollah','Cisjordanie','otages'),
   'hi', jsonb_build_array('इज़राइल','इज़राइली','गाजा','हमास','हिज़्बुल्लाह'),
   'it', jsonb_build_array('Israele','israeliano','Tel Aviv','Netanyahu','IDF','Gaza','Hamas','Hezbollah','Cisgiordania','ostaggi'),
   'ja', jsonb_build_array('イスラエル','テルアビブ','ネタニヤフ','ガザ','ハマス','ヒズボラ'),
   'ru', jsonb_build_array('Израиль','Тель-Авив','Нетаньяху','ЦАХАЛ','Газа','ХАМАС','Хезболла','Хизбалла','Западный берег','заложники'),
   'zh', jsonb_build_array('以色列','特拉维夫','内塔尼亚胡','加沙','哈马斯','真主党','约旦河西岸')
 ),
 true, 'fn_anchor', 'israel_theater'),

('gaza_war fn_anchor',
 jsonb_build_object(
   'ar', jsonb_build_array('غزة','الحرب على غزة','حماس','رفح','خان يونس','الجيش الإسرائيلي في غزة','وقف إطلاق النار','مجاعة غزة','اونروا','الأسرى','هدنة'),
   'de', jsonb_build_array('Gaza','Gaza-Krieg','Gazastreifen','Hamas','Rafah','Khan Younis','Waffenstillstand','Geiseln','Hungersnot Gaza','UNRWA','Hilfsgüter Gaza','Sinwar'),
   'en', jsonb_build_array('Gaza','Gaza war','Gaza Strip','Hamas','Rafah','Khan Younis','ceasefire','hostages','famine Gaza','UNRWA','aid Gaza','Sinwar','October 7','7 October','Hamas tunnels','Hamas leadership','Yahya Sinwar','Mohammed Deif','Haniyeh','two-stage deal','hostage deal'),
   'es', jsonb_build_array('Gaza','Franja de Gaza','Hamás','Rafah','alto el fuego','rehenes','hambruna Gaza','UNRWA'),
   'fr', jsonb_build_array('Gaza','bande de Gaza','Hamas','Rafah','cessez-le-feu','otages','famine Gaza','UNRWA'),
   'hi', jsonb_build_array('गाजा','हमास','रफह','युद्धविराम','बंधक'),
   'it', jsonb_build_array('Gaza','striscia di Gaza','Hamas','Rafah','cessate il fuoco','ostaggi','carestia Gaza','UNRWA'),
   'ja', jsonb_build_array('ガザ','ガザ地区','ハマス','ラファ','停戦','人質'),
   'ru', jsonb_build_array('Газа','сектор Газа','ХАМАС','Рафах','прекращение огня','заложники','голод в Газе','БАПОР','Синвар'),
   'zh', jsonb_build_array('加沙','加沙地带','哈马斯','拉法','停火','人质','加沙饥荒','辛瓦尔')
 ),
 true, 'fn_anchor', 'gaza_war'),

('israel_lebanon_border fn_anchor',
 jsonb_build_object(
   'ar', jsonb_build_array('حزب الله','جنوب لبنان','لبنان','بيروت','الضاحية','الليطاني','اليونيفيل','نصرالله','الجبهة الشمالية','المقاومة الإسلامية'),
   'de', jsonb_build_array('Hisbollah','Hezbollah','Libanon','Beirut','Südlibanon','Litani','UNIFIL','Nasrallah','Nordfront','israelisch-libanesische Grenze'),
   'en', jsonb_build_array('Hezbollah','Hizbullah','Lebanon','Beirut','southern Lebanon','Litani','UNIFIL','Nasrallah','Naim Qassem','Hezbollah strikes','northern front','Israeli-Lebanese border','Dahieh','Resolution 1701','UNSCR 1701','Galilee','northern Israel'),
   'es', jsonb_build_array('Hezbolá','Hezbollah','Líbano','Beirut','sur del Líbano','Litani','FINUL','Nasrallah','frente norte'),
   'fr', jsonb_build_array('Hezbollah','Liban','Beyrouth','sud du Liban','Litani','FINUL','Nasrallah','front nord','frontière israélo-libanaise'),
   'hi', jsonb_build_array('हिज़्बुल्लाह','लेबनान','बेरूत','नसरल्लाह'),
   'it', jsonb_build_array('Hezbollah','Libano','Beirut','sud del Libano','Litani','UNIFIL','Nasrallah','fronte nord'),
   'ja', jsonb_build_array('ヒズボラ','レバノン','ベイルート','ナスララ','南レバノン'),
   'ru', jsonb_build_array('Хезболла','Хизбалла','Ливан','Бейрут','юг Ливана','Литани','ВСООНЛ','Насралла','северный фронт'),
   'zh', jsonb_build_array('真主党','黎巴嫩','贝鲁特','南黎巴嫩','利塔尼','纳斯鲁拉')
 ),
 true, 'fn_anchor', 'israel_lebanon_border'),

('israel_iran_strikes fn_anchor',
 jsonb_build_object(
   'ar', jsonb_build_array('إيران واسرائيل','الضربات الإيرانية','الرد الإسرائيلي','الحرس الثوري','عملية الوعد الصادق','صواريخ بالستية','الدفاع الإيراني','هجوم إيراني على إسرائيل','الضربة الإسرائيلية على إيران','الردع','إسرائيل تقصف إيران'),
   'de', jsonb_build_array('Iran-Israel','iranische Angriffe','israelische Vergeltung','Revolutionsgarden','IRGC','ballistische Raketen','Drohnen aus Iran','Operation Wahres Versprechen','israelischer Schlag gegen Iran','iranischer Angriff auf Israel'),
   'en', jsonb_build_array('Iran Israel','Iranian strikes on Israel','Israeli strikes on Iran','IRGC','Revolutionary Guard','Operation True Promise','ballistic missiles Iran','Iranian drones','Iran retaliation','Israeli retaliation','Natanz','Fordow','Iranian air defense','Israeli air force Iran','Pezeshkian','Khamenei response','direct war Iran Israel'),
   'es', jsonb_build_array('Irán Israel','ataques iraníes','represalia israelí','Guardia Revolucionaria','misiles balísticos','ataque israelí a Irán','ataque iraní a Israel'),
   'fr', jsonb_build_array('Iran Israël','frappes iraniennes','riposte israélienne','Gardiens de la Révolution','missiles balistiques','frappes israéliennes sur l''Iran'),
   'hi', jsonb_build_array('ईरान इज़राइल','ईरानी हमले','इज़राइली हमला ईरान'),
   'it', jsonb_build_array('Iran Israele','attacchi iraniani','rappresaglia israeliana','Guardia Rivoluzionaria','missili balistici','attacco israeliano all''Iran'),
   'ja', jsonb_build_array('イラン イスラエル','イランの攻撃','イスラエルの報復','革命防衛隊','弾道ミサイル'),
   'ru', jsonb_build_array('Иран Израиль','удары Ирана по Израилю','израильские удары по Ирану','КСИР','баллистические ракеты Иран','операция Истинное обещание','ответ Ирана','ответ Израиля'),
   'zh', jsonb_build_array('伊朗 以色列','伊朗袭击以色列','以色列袭击伊朗','革命卫队','弹道导弹','真实承诺行动')
 ),
 true, 'fn_anchor', 'israel_iran_strikes'),

('west_bank_settlements fn_anchor',
 jsonb_build_object(
   'ar', jsonb_build_array('الضفة الغربية','المستوطنات','جنين','نابلس','الخليل','عنف المستوطنين','الاحتلال','السلطة الفلسطينية','حل الدولتين','اقتحامات'),
   'de', jsonb_build_array('Westjordanland','Westbank','Siedlungen','Siedler','Dschenin','Jenin','Nablus','Hebron','Siedlergewalt','Besatzung','Palaestinensische Autonomiebehoerde','Zweistaatenloesung','Annexion'),
   'en', jsonb_build_array('West Bank','settlements','settler violence','Jenin','Nablus','Hebron','outposts','occupation','Palestinian Authority','two-state','Judea Samaria','E1','Area C','annexation','settler attack','settler raid','Mahmoud Abbas','PA'),
   'es', jsonb_build_array('Cisjordania','asentamientos','colonos','violencia de colonos','Jenin','Nablus','ocupación','Autoridad Palestina','solución de dos Estados'),
   'fr', jsonb_build_array('Cisjordanie','colonies','colons','violence des colons','Jénine','Naplouse','occupation','Autorité palestinienne','solution à deux États'),
   'hi', jsonb_build_array('वेस्ट बैंक','बस्तियाँ','जेनिन','नब्लस'),
   'it', jsonb_build_array('Cisgiordania','insediamenti','coloni','violenza dei coloni','Jenin','Nablus','occupazione','Autorità Palestinese','soluzione a due Stati'),
   'ja', jsonb_build_array('ヨルダン川西岸','入植地','入植者','ジェニン','ナブルス','占領','二国家解決'),
   'ru', jsonb_build_array('Западный берег','Западного берега','поселения','поселенцы','насилие поселенцев','Дженин','Наблус','оккупация','Палестинская автономия','двух государств'),
   'zh', jsonb_build_array('约旦河西岸','定居点','定居者','杰宁','纳布卢斯','占领','两国方案')
 ),
 true, 'fn_anchor', 'west_bank_settlements');

-- ============================================================
-- 3. Narratives (12 total) — see comment block at top for stance scheme.
-- ============================================================

-- ---------- 3a. Theater-level narratives (4) ----------

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('israel_existential_self_defense', 'israel_theater', 1, 2,
 'Existential self-defense', 'Existenzielle Selbstverteidigung',
 'Israel: existential self-defense against multi-front Iran-led axis',
 'Israel: existenzielle Selbstverteidigung gegen eine vom Iran gefuehrte Mehrfrontenachse',
 'Israeli sources and pro-Israel commentary frame the post-October 7 conflict as a multi-front fight for survival against an Iran-orchestrated axis (Hamas, Hezbollah, Houthis, Shia militias). The October 7 attacks, hostage situation, ongoing Hezbollah rocket fire, Houthi Red Sea attacks, and direct Iranian missile/drone waves are read as components of a single coordinated assault. The vocabulary is "right of self-defense", "October 7", "hostages", "axis of resistance / Iranian axis", "Iron Sword", "northern front", "preemption", "deterrence restoration". Prescription: dismantle Hamas, push Hezbollah north of the Litani, restore deterrence against Iran, free the hostages.',
 'Israelische Quellen und pro-israelische Kommentatoren rahmen den Konflikt seit dem 7. Oktober als Mehrfrontenkampf ums Ueberleben gegen eine vom Iran gelenkte Achse (Hamas, Hisbollah, Houthi, schiitische Milizen). Der 7. Oktober, die Geiseln, anhaltender Raketenbeschuss der Hisbollah, Houthi-Angriffe im Roten Meer und direkte iranische Raketen-/Drohnen-Wellen werden als Teile eines koordinierten Angriffs gelesen. Vokabular: "Selbstverteidigungsrecht", "7. Oktober", "Geiseln", "iranische Achse", "Eiserne Schwerter", "Nordfront", "Praevention", "Wiederherstellung der Abschreckung". Vorschrift: Hamas zerschlagen, Hisbollah nordwaerts vom Litani draengen, Abschreckung gegenueber Iran wiederherstellen, Geiseln befreien.',
 ARRAY['MIDEAST-ISRAEL','AMERICAS-USA'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Fox News','Israel Hayom','The Jerusalem Post','Arutz Sheva','Ynetnews'],
 ARRAY['right of self-defense','October 7','7 October','hostages','axis of resistance','Iranian axis','Iron Sword','northern front','deterrence','preemption','existential','Hamas terror','antisemitism','never again','Iron Dome','Holocaust survivors','dismantle Hamas','liberate hostages'],
 true),

('palestine_genocide_framing', 'israel_theater', 2, -2,
 'Genocide and dispossession', 'Genozid und Vertreibung',
 'Pan-Arab / pro-Palestinian: Israel commits systemic violence against Palestinians',
 'Panarabisch / propalaestinensisch: Israel veruebt systemische Gewalt an Palaestinensern',
 'Al Jazeera, TRT World, Press TV, Palestinian outlets, and increasingly broad international human-rights commentary frame Israeli military operations across Gaza, Lebanon, and the West Bank as systemic violence amounting to genocide, ethnic cleansing, or apartheid. Evidence cited: civilian death tolls, famine conditions in Gaza, displacement, settlement expansion, the ICJ genocide case, ICC arrest warrants. The vocabulary is "genocide", "apartheid", "ethnic cleansing", "siege", "collective punishment", "occupation", "settler-colonial", "open-air prison", "Nakba continues". Prescription: immediate ceasefire, end of the siege, accountability via ICC/ICJ, end of US military aid, recognition of Palestinian statehood.',
 'Al Jazeera, TRT World, Press TV, palaestinensische und zunehmend internationale Menschenrechts-Stimmen rahmen israelische Operationen in Gaza, Libanon und Westjordanland als systemische Gewalt — als Genozid, ethnische Saeuberung oder Apartheid. Argumente: zivile Opferzahlen, Hunger in Gaza, Vertreibung, Siedlungserweiterung, IGH-Genozidklage, IStGH-Haftbefehle. Vokabular: "Genozid", "Apartheid", "ethnische Saeuberung", "Belagerung", "Kollektivstrafe", "Besatzung", "Siedler-Kolonialismus", "fortgesetzte Nakba". Vorschrift: sofortiger Waffenstillstand, Ende der Belagerung, Rechenschaft via IStGH/IGH, Ende der US-Militaerhilfe, Anerkennung Palaestinas.',
 ARRAY['MIDEAST-PALESTINE','MIDEAST-LEVANT','MIDEAST-IRAN','MIDEAST-GULF','MIDEAST-TURKEY'],
 ARRAY['Al Jazeera','Press TV','TRT World','Anadolu Agency','Daily Sabah','Al-Ahram','Arab News','Fars News','IRNA','Al Arabiya','Khaleej Times','Gulf News'],
 ARRAY['genocide','apartheid','ethnic cleansing','siege','collective punishment','occupation','settler-colonial','Nakba','famine','starvation','war crimes','ICJ','ICC','massacre','displaced','displacement','illegal occupation','open-air prison'],
 true),

('eu_two_state_pathway', 'israel_theater', 3, 0,
 'EU/E3 two-state pathway', 'EU/E3 Zweistaaten-Linie',
 'EU/E3 two-state framework: condemn excesses on both sides, preserve the negotiated horizon',
 'EU/E3 Zweistaaten-Rahmen: Exzesse auf beiden Seiten verurteilen, die Verhandlungsperspektive bewahren',
 'European Union and E3 (France, Germany, United Kingdom) coverage frames the Israeli-Palestinian conflict around preserving a negotiated two-state pathway. The position is genuinely two-sided: condemn Hamas''s October 7 attacks AND condemn disproportionate Israeli force in Gaza; defend Israeli existence AND defend Palestinian self-determination; sanction settler violence AND maintain security cooperation with the IDF. The vocabulary is "two-state solution", "international humanitarian law", "proportionality", "civilian protection", "settlement expansion is illegal under international law", "negotiated political horizon", "Abraham Accords extension". Prescription: sustained diplomatic pressure on all parties, humanitarian corridors, sanctions on extremist settlers, support for the Palestinian Authority and reformed governance.',
 'Die EU und die E3 (Frankreich, Deutschland, Grossbritannien) rahmen den israelisch-palaestinensischen Konflikt um den Erhalt eines verhandelten Zweistaatenpfads. Position genuin doppelseitig: Verurteilung der Hamas-Angriffe vom 7. Oktober UND Verurteilung unverhaeltnismaessiger israelischer Gewalt in Gaza; Verteidigung israelischer Existenz UND palaestinensischer Selbstbestimmung; Sanktionen gegen Siedlergewalt UND Aufrechterhaltung der Sicherheitskooperation mit der IDF. Vokabular: "Zweistaatenloesung", "humanitaeres Voelkerrecht", "Verhaeltnismaessigkeit", "Schutz von Zivilisten", "Siedlungserweiterung ist voelkerrechtswidrig", "Verhandlungsperspektive", "Abraham-Abkommen". Vorschrift: nachhaltiger diplomatischer Druck auf alle Parteien, humanitaere Korridore, Sanktionen gegen extremistische Siedler, Unterstuetzung einer reformierten Palaestinensischen Autonomiebehoerde.',
 ARRAY['NON-STATE-EU','EUROPE-FRANCE','EUROPE-GERMANY','EUROPE-UK'],
 ARRAY['The Guardian','Le Monde','El País','Tagesschau','Deutsche Welle','Die Zeit','Euronews','Frankfurter Allgemeine','Corriere della Sera','La Repubblica','Sky News','Financial Times','BBC World','Reuters','Associated Press','France 24','France 24 (EN)','Handelsblatt','El Mundo'],
 ARRAY['two-state solution','two-state','international humanitarian law','proportionality','civilian protection','settlement expansion','Abraham Accords','negotiated solution','political horizon','UN Resolution 242','UN Resolution 1701','calibrated pressure','de-escalation','restraint','ceasefire negotiations'],
 true),

('multipolar_anti_israel_alignment', 'israel_theater', 4, -1,
 'Multipolar anti-Israel alignment', 'Multipolare Anti-Israel-Stimmen',
 'Russia / China / Global South: Israel as US-backed colonial outlier',
 'Russland / China / Globaler Sueden: Israel als US-gestuetzte koloniale Ausnahme',
 'Russian, Chinese, and Global South commentary frames Israel as a US-backed colonial project whose actions violate the UN Charter and international law. The argument: Israel''s actions in Gaza, Lebanon, and the West Bank are not isolated security responses but expressions of the same US-led "unipolar" hegemony Russia and China oppose worldwide; sanctions evasion via the Abraham Accords; weaponized impunity at the UN Security Council via US veto. The vocabulary is "unipolar hegemony", "US-Israeli collusion", "veto power abuse", "double standards", "BRICS solidarity with Palestine", "South African ICJ case", "Global South coalition". Prescription: BRICS+ recognition of Palestine, Russia-China-Iran coordination on sanctions / pressure, dollar de-dependence, UN Security Council reform.',
 'Russische, chinesische und Stimmen des Globalen Suedens rahmen Israel als US-gestuetztes Kolonialprojekt, dessen Handeln gegen die UN-Charta und das Voelkerrecht verstoesst. Argumentation: Israels Vorgehen in Gaza, Libanon und Westjordanland sei keine isolierte Sicherheitsantwort, sondern Ausdruck derselben US-gefuehrten "unipolaren" Hegemonie, gegen die sich Russland und China weltweit stellen; Straflosigkeit per US-Veto im Sicherheitsrat. Vokabular: "unipolare Hegemonie", "US-israelische Komplizenschaft", "Vetomissbrauch", "doppelte Standards", "BRICS-Solidaritaet mit Palaestina", "IGH-Klage Suedafrikas", "Koalition des Globalen Suedens". Vorschrift: BRICS+-Anerkennung Palaestinas, Russland-China-Iran-Koordination bei Sanktionen, Dollar-Entkopplung, Reform des UN-Sicherheitsrats.',
 ARRAY['EUROPE-RUSSIA','ASIA-CHINA','MIDEAST-IRAN','ASIA-SOUTHASIA'],
 ARRAY['RT','TASS (EN)','CGTN','China Daily','Press TV','Fars News','IRNA','Anadolu Agency','Daily Sabah','TRT World','Al Mayadeen','Granma','Telesur','WION','NDTV','Hindustan Times'],
 ARRAY['unipolar hegemony','US-Israeli collusion','double standards','veto abuse','BRICS solidarity','Global South','South African ICJ','Global South coalition','UNGA recognition','impunity','colonial outpost','US imperialism','Western hypocrisy','sanctions diktat','UN reform'],
 true);

-- ---------- 3b. gaza_war narratives (2) ----------

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('israel_dismantle_hamas', 'gaza_war', 1, 2,
 'Dismantle Hamas, free hostages', 'Hamas zerschlagen, Geiseln befreien',
 'Israel: war is non-negotiable until Hamas is dismantled and hostages freed',
 'Israel: der Krieg ist nicht verhandelbar, bis die Hamas zerschlagen und die Geiseln befreit sind',
 'Israeli sources frame the Gaza war as a non-negotiable response to October 7 with two operational goals: dismantling Hamas as a military and governing entity, and returning all hostages. Civilian casualties are attributed to Hamas use of human shields and the tunnel network beneath civilian infrastructure. The vocabulary is "Hamas terror", "October 7 worst attack on Jews since the Holocaust", "hostages", "tunnels beneath hospitals", "human shields", "complete victory", "the day after Hamas". Prescription: continue military operations until Hamas military and governing capability is eliminated, hostage deals only on Israeli terms, no Palestinian Authority return to Gaza without reform.',
 'Israelische Quellen rahmen den Gaza-Krieg als nicht verhandelbare Antwort auf den 7. Oktober mit zwei Zielen: Zerschlagung der Hamas als militaerische und herrschende Einheit und Rueckkehr aller Geiseln. Zivile Opfer werden der Nutzung menschlicher Schutzschilde durch die Hamas und dem Tunnelsystem unter ziviler Infrastruktur zugeschrieben. Vokabular: "Hamas-Terror", "7. Oktober schlimmster Angriff auf Juden seit dem Holocaust", "Geiseln", "Tunnel unter Krankenhaeusern", "menschliche Schutzschilde", "vollstaendiger Sieg", "der Tag danach". Vorschrift: militaerische Operationen bis zur Beseitigung der militaerischen und herrschenden Kapazitaet der Hamas fortsetzen, Geiseldeals nur zu israelischen Bedingungen, keine Rueckkehr der Palaestinensischen Autonomiebehoerde nach Gaza ohne Reform.',
 ARRAY['MIDEAST-ISRAEL','AMERICAS-USA'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Israel Hayom','Fox News','Arutz Sheva','Ynetnews'],
 ARRAY['Hamas terror','October 7','7 October','hostages','human shields','tunnels','Sinwar','dismantle Hamas','complete victory','Israeli right to defend','Iron Sword','Gaza tunnels','Hamas hospitals'],
 true),

('gaza_humanitarian_catastrophe', 'gaza_war', 2, -2,
 'Humanitarian catastrophe and genocide', 'Humanitaere Katastrophe und Genozid',
 'Pan-Arab / pro-Palestinian: Israel''s Gaza campaign is humanitarian catastrophe and genocide',
 'Panarabisch / propalaestinensisch: Israels Gaza-Feldzug ist humanitaere Katastrophe und Genozid',
 'Pan-Arab outlets, Press TV, TRT, and pro-Palestinian commentary frame the Gaza war as a humanitarian catastrophe and, in many cases, a genocide. Evidence cited: civilian death toll exceeding 40,000 with majority women and children, near-total displacement of the population, induced famine via aid blockade, systematic destruction of hospitals, universities, mosques, churches, and water/sanitation infrastructure, the ICJ genocide case brought by South Africa, ICC arrest warrants for Netanyahu and Gallant. The vocabulary is "genocide", "famine", "starvation as a weapon", "Rafah massacre", "Khan Younis massacre", "hospital strikes", "aid convoy targeting", "ICJ genocide ruling", "displaced", "open-air prison". Prescription: immediate and unconditional ceasefire, full humanitarian access, accountability via international law, end US military aid to Israel.',
 'Panarabische Medien, Press TV, TRT und propalaestinensische Kommentatoren rahmen den Gaza-Krieg als humanitaere Katastrophe und vielfach als Genozid. Argumente: zivile Todeszahl ueber 40.000, mehrheitlich Frauen und Kinder, fast vollstaendige Vertreibung der Bevoelkerung, herbeigefuehrte Hungersnot durch Hilfsblockade, systematische Zerstoerung von Krankenhaeusern, Universitaeten, Moscheen, Kirchen und Wasser-/Sanitaerinfrastruktur, IGH-Genozidklage Suedafrikas, IStGH-Haftbefehle gegen Netanjahu und Gallant. Vokabular: "Genozid", "Hungersnot", "Aushungern als Waffe", "Massaker von Rafah", "Massaker von Khan Younis", "Angriffe auf Krankenhaeuser", "Beschuss von Hilfslieferungen", "IGH-Genozidurteil", "Vertriebene", "Freiluft-Gefaengnis". Vorschrift: sofortiger und bedingungsloser Waffenstillstand, vollstaendiger humanitaerer Zugang, Rechenschaft per Voelkerrecht, Ende der US-Militaerhilfe an Israel.',
 ARRAY['MIDEAST-PALESTINE','MIDEAST-LEVANT','MIDEAST-IRAN','MIDEAST-EGYPT','MIDEAST-GULF'],
 ARRAY['Al Jazeera','Press TV','TRT World','Anadolu Agency','Daily Sabah','Al-Ahram','Arab News','Fars News','IRNA','Al Arabiya','Khaleej Times','Gulf News','Al Mayadeen','Middle East Eye','Egypt Today'],
 ARRAY['genocide','famine','starvation','Rafah massacre','Khan Younis massacre','hospital strike','aid convoy','displaced','open-air prison','war crimes','collective punishment','ICJ','ICC','Netanyahu warrant','starvation as weapon','siege of Gaza','UNRWA','aid blocked','humanitarian catastrophe'],
 true);

-- ---------- 3c. israel_lebanon_border narratives (2) ----------

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('israel_self_defense_north', 'israel_lebanon_border', 1, 2,
 'Restore northern security', 'Sicherheit im Norden wiederherstellen',
 'Israel: push Hezbollah north of the Litani; restore northern security',
 'Israel: Hisbollah nordwaerts vom Litani zurueckdraengen, Sicherheit im Norden wiederherstellen',
 'Israeli sources frame the northern border conflict as a self-defense theater triggered by Hezbollah''s October 8 "support front" and rocket fire that displaced ~60,000 Israelis from the Galilee. Operational goal: restore UN Resolution 1701 by force, push Hezbollah north of the Litani, eliminate its precision-guided missile arsenal and senior command. Beirut strikes on Hezbollah leadership (including Nasrallah) are presented as legitimate decapitation operations. The vocabulary is "Hezbollah aggression", "northern displaced", "Litani", "1701 enforcement", "precision-guided missile project", "deterrence restored", "decapitation strike". Prescription: continue military pressure until Hezbollah accepts withdrawal from the border zone; reject any diplomatic settlement that leaves Hezbollah''s arsenal in place.',
 'Israelische Quellen rahmen den Nordgrenzkonflikt als Selbstverteidigungs-Front, ausgeloest durch die Hisbollah-"Unterstuetzungsfront" vom 8. Oktober und Raketenbeschuss, der rund 60.000 Israelis aus Galilaea vertrieb. Operatives Ziel: Umsetzung der UN-Resolution 1701 mit Gewalt, Hisbollah nordwaerts des Litani, Beseitigung des Praezisions-Raketenarsenals und der Fuehrung. Schlaege gegen die Hisbollah-Fuehrung in Beirut (darunter Nasrallah) gelten als legitime Enthauptungs-Operationen. Vokabular: "Hisbollah-Aggression", "Vertriebene im Norden", "Litani", "Durchsetzung der 1701", "Praezisions-Raketenprogramm", "wiederhergestellte Abschreckung", "Enthauptungsschlag". Vorschrift: militaerischen Druck fortsetzen, bis die Hisbollah den Rueckzug aus der Grenzzone akzeptiert; jede diplomatische Loesung ablehnen, die ihr Arsenal belaesst.',
 ARRAY['MIDEAST-ISRAEL','AMERICAS-USA'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Israel Hayom','Fox News','Arutz Sheva','Ynetnews'],
 ARRAY['Hezbollah aggression','northern displaced','Litani','1701','UNSCR 1701','precision-guided','decapitation','Nasrallah eliminated','Galilee','northern Israel','rocket fire','deterrence'],
 true),

('hezbollah_resistance_north', 'israel_lebanon_border', 2, -2,
 'Resistance against Israeli aggression', 'Widerstand gegen israelische Aggression',
 'Hezbollah and aligned: northern front as legitimate solidarity resistance',
 'Hisbollah und verbuendet: Nordfront als legitimer Solidaritaets-Widerstand',
 'Hezbollah-aligned outlets (Al Mayadeen, Press TV, Al-Akhbar) and pan-Arab commentary frame the northern front as legitimate solidarity resistance with Gaza. Hezbollah''s rocket fire is presented as proportionate pressure on the IDF to ease Gaza operations; Israeli strikes on Beirut suburbs are framed as collective punishment of Lebanon and assassinations of resistance leadership. The vocabulary is "support front", "solidarity with Gaza", "Israeli aggression on Lebanon", "Beirut massacre", "Dahieh", "martyrs of the resistance", "victory of the resistance". Prescription: continue military pressure on Israel until Gaza ceasefire; reject Lebanese state cooperation with Israeli security demands; preserve Hezbollah as the de facto deterrent against Israel.',
 'Hisbollah-nahe Medien (Al Mayadeen, Press TV, Al-Akhbar) und panarabische Stimmen rahmen die Nordfront als legitimen Solidaritaets-Widerstand mit Gaza. Hisbollah-Raketenbeschuss gilt als verhaeltnismaessiger Druck auf die IDF zur Entlastung Gazas; israelische Schlaege auf Beiruter Vororte gelten als Kollektivstrafe gegen den Libanon und Liquidierungen der Widerstandsfuehrung. Vokabular: "Unterstuetzungsfront", "Solidaritaet mit Gaza", "israelische Aggression gegen den Libanon", "Massaker in Beirut", "Dahieh", "Maertyrer des Widerstands", "Sieg des Widerstands". Vorschrift: militaerischen Druck auf Israel fortsetzen, bis ein Gaza-Waffenstillstand erreicht ist; libanesische Staatskooperation mit israelischen Sicherheitsforderungen ablehnen; Hisbollah als faktische Abschreckung gegen Israel erhalten.',
 ARRAY['MIDEAST-LEVANT','MIDEAST-IRAN'],
 ARRAY['Al Jazeera','Press TV','Al Mayadeen','Fars News','IRNA','Anadolu Agency','TRT World','Daily Sabah','Middle East Eye'],
 ARRAY['support front','solidarity with Gaza','Israeli aggression','Beirut massacre','Dahieh','martyrs','resistance victory','Lebanese sovereignty','collective punishment','assassinations','aggression on Lebanon'],
 true);

-- ---------- 3d. israel_iran_strikes narratives (2) ----------

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('israel_preemptive_strike_doctrine', 'israel_iran_strikes', 1, 2,
 'Preemptive defense against Iran', 'Praeventive Verteidigung gegen Iran',
 'Israel: preemptive and reactive strikes against an existential nuclear-bound enemy',
 'Israel: praeventive und reaktive Schlaege gegen einen existenziellen, nuklear strebenden Gegner',
 'Israeli sources frame direct exchanges with Iran as preemptive and reactive self-defense against an enemy openly committed to Israel''s destruction and pursuing nuclear weapons capability. The Begin Doctrine (strike a nuclear adversary before it can strike you) is the operational principle. Targets are presented as legitimate military: IRGC command, air defense, missile production, nuclear-related sites. Iranian missile/drone waves are framed as failed Iranian aggression neutralized by Iron Dome / Arrow / David''s Sling and US/UK/French/Jordanian air defense cooperation. The vocabulary is "Begin Doctrine", "preemption", "existential nuclear threat", "deterrence restoration", "Iron Dome", "Arrow 3", "regional defense coalition", "Iran''s axis cut down". Prescription: continue degrading Iranian nuclear, IRGC, and proxy capabilities; reject diplomatic engagement that leaves Iran a nuclear threshold state.',
 'Israelische Quellen rahmen direkte Schlagabtausche mit dem Iran als praeventive und reaktive Selbstverteidigung gegen einen Gegner, der offen Israels Zerstoerung anstrebt und Nuklearwaffenfaehigkeit verfolgt. Die Begin-Doktrin (einen nuklearen Gegner zuerst treffen) ist das operative Prinzip. Ziele gelten als legitim militaerisch: IRGC-Kommando, Luftabwehr, Raketenproduktion, nuklear-nahe Anlagen. Iranische Raketen-/Drohnen-Wellen werden als gescheiterte iranische Aggression dargestellt, neutralisiert durch Iron Dome, Arrow und David''s Sling sowie US-/UK-/franzoesische und jordanische Luftabwehr-Kooperation. Vokabular: "Begin-Doktrin", "Praevention", "existenzielle nukleare Bedrohung", "Wiederherstellung der Abschreckung", "Iron Dome", "Arrow 3", "regionale Verteidigungskoalition". Vorschrift: iranische Nuklear-, IRGC- und Stellvertreter-Kapazitaeten weiter abbauen; diplomatische Loesungen ablehnen, die den Iran als Nuklear-Schwellenstaat belassen.',
 ARRAY['MIDEAST-ISRAEL','AMERICAS-USA'],
 ARRAY['Jerusalem Post','Times of Israel','The Times of Israel','i24NEWS','Israel Hayom','Fox News','Arutz Sheva','Ynetnews'],
 ARRAY['Begin Doctrine','preemption','existential nuclear threat','Iron Dome','Arrow 3','David''s Sling','regional defense coalition','IRGC neutralized','Iranian missiles intercepted','deterrence restored','nuclear threat eliminated'],
 true),

('iran_legitimate_retaliation_doctrine', 'israel_iran_strikes', 2, -2,
 'Iran''s legitimate state self-defense', 'Legitime staatliche Selbstverteidigung Irans',
 'Iran-aligned: Iranian retaliation is legitimate state self-defense under the UN Charter',
 'Iran-orientiert: iranische Vergeltung ist legitime staatliche Selbstverteidigung gemaess der UN-Charta',
 'Iranian and aligned outlets (Press TV, Fars, IRNA, Al Mayadeen, RT, CGTN, TRT World) frame Iranian missile and drone strikes on Israel as legitimate state self-defense under Article 51 of the UN Charter, responding to Israeli aggression (consulate strike in Damascus, assassinations of IRGC and Hezbollah leadership on Iranian and allied soil, strikes on Iranian air defenses and nuclear-related sites). Operation True Promise is celebrated as the first direct Iranian strike on Israel that established a new deterrence equation. The vocabulary is "Operation True Promise", "Article 51", "legitimate retaliation", "deterrence restored", "Zionist regime", "axis of resistance", "Israeli aggression", "consulate attack", "martyrs of the IRGC". Prescription: maintain the new strike-for-strike equation; continue building axis-of-resistance coordination; develop nuclear deterrence capability if necessary.',
 'Iranische und verbuendete Medien (Press TV, Fars, IRNA, Al Mayadeen, RT, CGTN, TRT World) rahmen iranische Raketen- und Drohnenangriffe auf Israel als legitime staatliche Selbstverteidigung gemaess Artikel 51 der UN-Charta — als Antwort auf israelische Aggression (Konsulatsschlag in Damaskus, Liquidierung von IRGC- und Hisbollah-Fuehrung auf iranischem und verbuendetem Boden, Schlaege gegen iranische Luftabwehr und nuklear-nahe Anlagen). "Operation Wahres Versprechen" gilt als erster direkter iranischer Schlag gegen Israel, der eine neue Abschreckungsgleichung etablierte. Vokabular: "Operation Wahres Versprechen", "Artikel 51", "legitime Vergeltung", "wiederhergestellte Abschreckung", "zionistisches Regime", "Achse des Widerstands", "israelische Aggression", "Konsulatsangriff", "Maertyrer des IRGC". Vorschrift: die neue Schlag-gegen-Schlag-Gleichung aufrechterhalten; den Aufbau einer Achsen-Koordination fortsetzen; nukleare Abschreckungs-Kapazitaet bei Bedarf entwickeln.',
 ARRAY['MIDEAST-IRAN','MIDEAST-LEVANT'],
 ARRAY['Press TV','Fars News','IRNA','Al Mayadeen','Al Jazeera','RT','TASS (EN)','CGTN','TRT World','Anadolu Agency'],
 ARRAY['Operation True Promise','Article 51','legitimate retaliation','Zionist regime','axis of resistance','Israeli aggression','consulate attack','IRGC martyrs','deterrence','new equation','strike for strike','Iranian self-defense'],
 true);

-- ---------- 3e. west_bank_settlements narratives (2) ----------

INSERT INTO narratives_v2 (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
    name_en, name_de, claim_en, claim_de, actor_centroids, publishers, framing_keywords, is_active)
VALUES

('judea_samaria_sovereignty', 'west_bank_settlements', 1, 1,
 'Judea-Samaria sovereignty', 'Souveraenitaet ueber Judaea und Samaria',
 'Israeli right: Jewish sovereignty over biblical Judea-Samaria',
 'Israelische Rechte: juedische Souveraenitaet ueber das biblische Judaea-Samaria',
 'Israeli right-wing outlets and settlement-movement commentary frame the West Bank as biblical Judea-Samaria — historically and legally part of the Jewish national home rather than "occupied territory". Settler communities are presented as the natural population restoration; IDF operations in Jenin and Nablus are counter-terrorism against Hamas/Islamic Jihad infrastructure; settler-Palestinian friction is reduced to extremist outliers or framed as defensive against Palestinian terror. The vocabulary is "Judea and Samaria", "biblical heartland", "Jewish indigeneity", "counter-terror raid", "Hamas in the West Bank", "PA failed state", "applied sovereignty", "Levin reform", "Smotrich plan". Prescription: extend Israeli civil law over Area C, expand settlement construction, abandon the two-state framework, treat the PA as a security risk to be replaced.',
 'Israelische rechte Medien und siedlungsnahe Kommentatoren rahmen das Westjordanland als biblisches Judaea-und-Samaria — historisch und rechtlich Teil der juedischen Heimstaette, nicht "besetztes Gebiet". Siedlungen gelten als natuerliche Wiederbesiedlung; IDF-Operationen in Dschenin und Nablus als Anti-Terror gegen Hamas/Islamischen Dschihad; Siedler-Palaestinenser-Reibungen werden auf Einzelne reduziert oder als Verteidigung gegen palaestinensischen Terror gerahmt. Vokabular: "Judaea und Samaria", "biblisches Kernland", "juedische Indigenitaet", "Anti-Terror-Razzia", "Hamas im Westjordanland", "PA als gescheiterter Staat", "angewandte Souveraenitaet", "Levin-Reform", "Smotrich-Plan". Vorschrift: israelisches Zivilrecht auf Gebiet C ausdehnen, Siedlungsbau erweitern, Zweistaaten-Rahmen verlassen, die PA als Sicherheitsrisiko behandeln.',
 ARRAY['MIDEAST-ISRAEL'],
 ARRAY['Jerusalem Post','Israel Hayom','Arutz Sheva','i24NEWS','Times of Israel','The Times of Israel'],
 ARRAY['Judea and Samaria','biblical heartland','Jewish indigeneity','counter-terror raid','Hamas in West Bank','PA failed state','applied sovereignty','Smotrich plan','Ben Gvir','outpost legalization','settler communities','Hamas Jenin','Hamas Nablus'],
 true),

('west_bank_apartheid_framing', 'west_bank_settlements', 2, -2,
 'Occupation, settler violence, apartheid', 'Besatzung, Siedlergewalt, Apartheid',
 'Palestinian / international human rights: occupation, settler impunity, apartheid system',
 'Palaestinensisch / internationale Menschenrechte: Besatzung, Straflosigkeit von Siedlern, Apartheid-System',
 'Palestinian outlets, Al Jazeera, and increasingly international human rights commentary (Amnesty, HRW, B''Tselem) frame Israeli control of the West Bank as an illegal occupation now operating as an apartheid system. Settler violence is presented as systemic and state-enabled; IDF raids on Jenin and Nablus as collective punishment of Palestinian civilian populations; settlement expansion as land theft prohibited under the Fourth Geneva Convention. The vocabulary is "occupation", "apartheid", "settler-colonial", "ethnic cleansing", "illegal under international law", "settler pogrom", "annexation by stealth", "Area C land theft", "ICJ advisory opinion on occupation". Prescription: end the occupation, dismantle settlements, accountability for settler violence, recognition of Palestinian statehood within 1967 borders.',
 'Palaestinensische Medien, Al Jazeera und zunehmend internationale Menschenrechts-Stimmen (Amnesty, HRW, B''Tselem) rahmen die israelische Kontrolle ueber das Westjordanland als illegale Besatzung, die als Apartheid-System operiert. Siedlergewalt gilt als systemisch und staatlich ermoeglicht; IDF-Razzien in Dschenin und Nablus als Kollektivstrafe gegen Zivilbevoelkerung; Siedlungserweiterung als Landraub im Sinne der Vierten Genfer Konvention. Vokabular: "Besatzung", "Apartheid", "Siedler-Kolonialismus", "ethnische Saeuberung", "voelkerrechtswidrig", "Siedler-Pogrom", "schleichende Annexion", "Landraub in Gebiet C", "IGH-Gutachten zur Besatzung". Vorschrift: Besatzung beenden, Siedlungen aufloesen, Rechenschaft fuer Siedlergewalt, Anerkennung Palaestinas in den Grenzen von 1967.',
 ARRAY['MIDEAST-PALESTINE','MIDEAST-LEVANT','MIDEAST-GULF','NON-STATE-EU'],
 ARRAY['Al Jazeera','Press TV','TRT World','Anadolu Agency','Daily Sabah','Al-Ahram','Arab News','The Guardian','Middle East Eye','Al Mayadeen'],
 ARRAY['occupation','apartheid','settler-colonial','ethnic cleansing','illegal under international law','settler pogrom','annexation by stealth','Area C','land theft','ICJ advisory','settler violence','PA','collective punishment','Geneva Convention'],
 true);

-- ============================================================
-- 4. Sanity checks before commit
-- ============================================================

DO $$
DECLARE
    n_fn integer; n_nar integer; n_anchor integer;
BEGIN
    SELECT COUNT(*) INTO n_fn FROM friction_nodes WHERE id IN
        ('israel_theater','gaza_war','israel_lebanon_border','israel_iran_strikes','west_bank_settlements');
    SELECT COUNT(*) INTO n_nar FROM narratives_v2 WHERE fn_id IN
        ('israel_theater','gaza_war','israel_lebanon_border','israel_iran_strikes','west_bank_settlements');
    SELECT COUNT(*) INTO n_anchor FROM taxonomy_v3
        WHERE taxonomy_function = 'fn_anchor' AND linked_id IN
        ('israel_theater','gaza_war','israel_lebanon_border','israel_iran_strikes','west_bank_settlements');
    IF n_fn <> 5 OR n_nar <> 12 OR n_anchor <> 5 THEN
        RAISE EXCEPTION 'Sanity check failed: israel_theater friction_nodes=%, narratives=%, fn_anchors=% (expected 5/12/5)',
            n_fn, n_nar, n_anchor;
    END IF;
END $$;

COMMIT;

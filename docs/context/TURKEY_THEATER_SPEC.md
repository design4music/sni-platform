# Turkey Theater — Build Spec

**Date drafted**: 2026-05-13
**Status**: Draft for review. No DB writes yet.
**Pattern**: Follows `iran_theater` / `israel_theater` / `syria_theater`
(D-075..D-079, 2026-05-12; Syria spec 2026-05-13).

## Why now

Turkey is the densest non-Iran / non-Israel Middle East signal we
have but the stories are diffuse and none of them are currently
covered by a friction node. The corpus carries roughly 3,200 titles
and 1,200 promoted events touching `MIDEAST-TURKEY` over the last 180
days, spread across four distinct surfaces:

- Erdogan as a regional broker (Gaza peace board, Iran ceasefire,
  Zelensky visit, Sisi rapprochement, US-Iran nuclear talks venue)
- Domestic democratic backsliding (Imamoglu trial, CHP corruption
  probes, journalist arrests, protest waves)
- The Kurdish question, refracted through Turkey rather than Syria
  (PKK disarmament process, DEM Party talks, Imrali, cross-border
  strikes on YPG/SDF, "terror-free Türkiye")
- Iran war spillover (Iranian missile over Turkish airspace, NATO
  Patriot deployment to Malatya, Erdogan opposing US-Israel strikes
  on Iran)

Each surface has visible publisher cohort alignment (Turkish state
desk / pan-Arab / Western liberal / Israeli right). None of them
slot cleanly into an existing FN. Without a Turkey theater the
Turkey centroid sits as a high-volume blind spot in the friction
node map.

Top entities in Turkey-marked titles (180d):

- Persons: ERDOGAN (304), FIDAN (44), Imamoglu (15 surface mentions)
- Orgs: NATO (92), PKK (28), CHP (10)
- Places: Istanbul (171), Black Sea (77), Gaza (73), Ankara (45),
  Cyprus (48), Malatya / Patriot (18)

Top publishers in Turkey-marked titles (180d, local DB):

- Turkish state desk: Daily Sabah (401), Anadolu Agency (246), TRT World (58)
- DACH cohort (diaspora-driven beat): Frankfurter Allgemeine (373),
  Kurier (354), Tagesschau (275), Handelsblatt (271), Die Zeit (241),
  Süddeutsche Zeitung (221), Der Standard (213), Die Presse (203),
  Der Spiegel (155), Deutsche Welle (24)
- Pan-Arab: Al Jazeera (76), Al Arabiya (72), Al-Ahram (57),
  Egypt Today (19), The National (14), Khaleej Times
- Israeli: Jerusalem Post (71), Times of Israel (55), Haaretz (19), i24NEWS
- Greek / Cypriot / Bulgarian neighbour: eKathimerini (73),
  Cyprus Mail (33), Novinite (18)
- Russian: TASS (EN) (37), Lenta.ru (20)
- Anglo wire baseline: Reuters, Bloomberg, BBC, France 24 (EN), AP

Top promoted Turkey events (180d, from prompt context plus local
corpus check):

- 46 srcs — "Three gunmen killed in shooting near Israeli consulate
  in Istanbul"
- 27 srcs — "NATO air defenses shoot down a missile from Iran over
  Turkey"
- 20 srcs — "Tanker carrying Russian oil hit by naval drone in
  Black Sea"
- 16 srcs — "Zelensky visits Turkey for security talks with Erdogan"
- 15 srcs — "Trump invites foreign leaders to Gaza peace board"
- 13 srcs — "Egypt and Turkey leaders meet to strengthen ties"
- 12 srcs — "Turkish opposition mayor goes on trial"
- 10 srcs — "Turkey deploys US Patriot system after Iranian missile
  strikes"
- 9 srcs — "Student kills nine in second Turkish school shooting"
- 9 srcs — "Erdogan tells Putin Turkey opposes attacks on Iran"

## Theater shape

```
turkey_theater (catch-all, fn_type='theater')
   |
   +-- turkey_mediator_role        Erdogan as regional broker / two-faced player
   +-- turkey_democratic_backsliding   Imamoglu trial, CHP probes, journalist arrests
   +-- turkey_kurdish_question     PKK disarmament process, DEM Party, anti-SDF ops
   +-- turkey_iran_war_spillover   Iranian missile over Turkey, NATO Patriots, Erdogan-Putin call
```

Four atomic FNs were chosen because they correspond to four distinct
publisher cohort alignments and four separate pro/con narrative
contests. Each has enough volume in the corpus to support a
two-narrative split (each >100 titles, >30 events in spot checks).

Rejected candidates and why:

- `istanbul_security_incidents` (Israeli consulate shooting, school
  shootings) — high volume on one or two days but no narrative
  contest. The consulate event reads partly as Israel-Turkey relations
  (already inside `turkey_mediator_role`'s remit) and partly as
  domestic terrorism. Surfaces well as theater-level event under
  `turkey_theater`, not its own atomic FN.
- `turkey_russia_relations` / Black Sea — bilateral exists but most
  signal is Ukraine-side (drone strikes on Russian oil terminals),
  not Turkey-anchored. Erdogan-Putin call on Iran already attaches
  to `turkey_iran_war_spillover` and `turkey_mediator_role`. Tartus /
  Khmeimim base future already attaches to `syria_theater`. Park.
- `turkey_aegean_cyprus_eastmed` — Cyprus 48 mentions, Aegean 6, F-35
  8, S-400 1. Real signal but thin. The Greek / Cypriot cohort is
  visible (eKathimerini 73, Cyprus Mail 33) but the contest doesn't
  shake the wider narrative map. Park for future spec.
- `turkey_economy_lira` — material domestically but the corpus filters
  most of it out as financial-page coverage that doesn't attach to
  the geopolitical contest. Park.

The theater catch-all carries broader framings that span all four
atomic FNs: Turkey as rising independent regional power vs. Turkey
as unreliable NATO ally; the diaspora dimension (especially in DACH
press coverage); foreign-policy autonomy framing.

## FN definitions

### `turkey_theater` (theater, catch-all)

- **Name (EN)**: Turkey as contested regional power
- **Name (DE)**: Tuerkei als umkaempfte Regionalmacht
- **fn_type**: `theater`
- **member_fn_ids**: `[turkey_mediator_role, turkey_democratic_backsliding,
  turkey_kurdish_question, turkey_iran_war_spillover]`
- **centroid_ids**: `[MIDEAST-TURKEY, MIDEAST-LEVANT, MIDEAST-IRAN,
  MIDEAST-ISRAEL, MIDEAST-EGYPT, MIDEAST-SAUDI, MIDEAST-GULF,
  MIDEAST-IRAQ, AMERICAS-USA, EUROPE-RUSSIA, EUROPE-UKRAINE,
  EUROPE-GERMANY, EUROPE-GREECE, NON-STATE-EU, NON-STATE-NATO]`
- **What it carries**: cross-cutting framings about Turkey's
  strategic positioning — independent middle-power posture, NATO
  ally reliability question, diaspora-related diplomacy with
  Germany and Austria, Istanbul terror incidents that don't fit
  any single atomic FN, the school shooting wave.

### `turkey_mediator_role` (atomic)

- **Name (EN)**: Turkey as regional mediator
- **Name (DE)**: Tuerkei als regionaler Vermittler
- **centroid_ids**: `[MIDEAST-TURKEY, MIDEAST-IRAN, MIDEAST-ISRAEL,
  MIDEAST-EGYPT, MIDEAST-GULF, MIDEAST-SAUDI, AMERICAS-USA,
  EUROPE-RUSSIA, EUROPE-UKRAINE]`
- **What it covers**: Erdogan's positioning as broker on Gaza
  (peace-board membership offered by Trump), Iran-US nuclear talks
  (originally proposed for Turkey, moved to Oman), Ukraine-Russia
  (Zelensky's Istanbul visit, grain corridor history),
  Egypt-Turkey rapprochement (Sisi visits, LNG / economic bloc),
  Saudi-Iran understandings echoed in Fidan diplomacy. Fidan as
  named diplomat appears in 44 titles. Narrative contest: legitimate
  balanced mediator vs. opportunistic two-faced player exploiting
  every side.

### `turkey_democratic_backsliding` (atomic)

- **Name (EN)**: Turkish domestic democratic backsliding
- **Name (DE)**: Demokratische Ruecklaeufigkeit in der Tuerkei
- **centroid_ids**: `[MIDEAST-TURKEY, EUROPE-GERMANY, NON-STATE-EU]`
- **What it covers**: Imamoglu trial (15+ title surface, "Erdogan
  challenger", "landmark trial", "thousands rally"), broader CHP
  corruption probes (Ankara chair detained, Izmir municipality
  bribery, multi-mayor detentions framed by state desk as anti-graft,
  by Western press as political persecution), journalist arrests
  (DW correspondent arrested), protest waves a year after Imamoglu's
  arrest. The DACH cohort treats this as a centrepiece story
  because of diaspora interest. Narrative contest: Western liberal
  critique of authoritarian drift vs. domestic regime defence as
  legal anti-corruption process.

### `turkey_kurdish_question` (atomic)

- **Name (EN)**: Turkey-side Kurdish question
- **Name (DE)**: Kurdische Frage aus tuerkischer Sicht
- **centroid_ids**: `[MIDEAST-TURKEY, MIDEAST-LEVANT, MIDEAST-IRAQ]`
- **What it covers**: PKK disarmament process, DEM Party (HDP
  successor) negotiations with Erdogan, Ocalan / Imrali messaging
  from prison, the "terror-free Türkiye" framing, cross-border
  Turkish operations against SDF / YPG in northeast Syria,
  PKK-headquarters strikes in northern Iraq. **Distinct from
  `syria_kurdish_question`**: that FN is Syria-bounded and centres
  on Damascus-SDF reunification with the new Syrian government as
  the contested act. This FN centres on the Turkey-side framing —
  PKK as terror, disarmament as the precondition for any political
  process, cross-border anti-YPG strikes as legitimate counter-terror.
  Publisher cohorts are different (Daily Sabah / Anadolu / TRT vs.
  Al Jazeera / DW / BBC), and the title vocabulary is too —
  Daily Sabah writes "PKK/YPG terrorists" where Western press
  writes "Kurdish-led forces". The same headline can attribute to
  both FNs only if the publisher is in both cohorts and the title
  matches both anchor bundles.

### `turkey_iran_war_spillover` (atomic)

- **Name (EN)**: Iran-war spillover into Turkey
- **Name (DE)**: Auswirkungen des Iran-Kriegs auf die Tuerkei
- **centroid_ids**: `[MIDEAST-TURKEY, MIDEAST-IRAN, AMERICAS-USA,
  NON-STATE-NATO]`
- **What it covers**: Iranian ballistic missile intercepted over
  Turkish airspace by NATO air defence, US Patriot system
  redeployment to Malatya (and from Ramstein per TASS reporting),
  Erdogan's public opposition to US-Israel strikes on Iran,
  Erdogan-Putin call about Iran, Erdogan-Trump conversations about
  Iran ceasefire and Venezuela. Distinct from `israel_iran_strikes`
  (direct Iran-Israel exchange) and from `iran_theater` (Iran's own
  posture) — this FN is about the *Turkey-side consequences* and
  Erdogan's positioning. Narrative contest: NATO solidarity /
  legitimate territorial defence vs. Turkey choosing the wrong side
  by criticising US-Israel action.

## Narrative slots (proposed, 11 total)

Stance is **toward Turkey under Erdogan** as the theater's primary
actor, following the iran_theater / israel_theater convention.

### Theater-level (3 narratives)

| id | stance | name | one-line frame |
|---|---:|---|---|
| `turkey_independent_middle_power` | +2 | Turkey as independent middle power | Turkey under Erdogan has earned regional stature through balanced diplomacy across Gaza, Iran, Ukraine, and Egypt; should be respected as a NATO ally with autonomous foreign policy. |
| `turkey_unreliable_ally_warning` | -2 | Unreliable NATO ally warning | Erdogan's Turkey is a hostile or unreliable NATO partner — courting Russia, opposing US-Israel Iran action, hosting Hamas leaders, undermining EU accession criteria; treat accordingly. |
| `turkey_eu_engagement_pragmatic` | 0 | EU pragmatic engagement | EU/E3 frame: engage Turkey on migration, energy, Black Sea security and economic ties while continuing to flag democratic backsliding and Cyprus / Aegean disputes; calibrated rather than confrontational. |

Publisher cohorts:
- `turkey_independent_middle_power`: Daily Sabah, Anadolu Agency,
  TRT World, Al-Ahram (post-rapprochement Egyptian state line),
  Al Jazeera (sympathetic), Khaleej Times, TASS (EN) (Russia
  appreciating any non-aligned NATO state)
- `turkey_unreliable_ally_warning`: Jerusalem Post, Times of Israel,
  i24NEWS, Arutz Sheva, Fox News, eKathimerini, Cyprus Mail
- `turkey_eu_engagement_pragmatic`: Tagesschau, Deutsche Welle,
  Die Zeit, Frankfurter Allgemeine, Süddeutsche Zeitung, Der Standard,
  Die Presse, Der Spiegel, Handelsblatt, Le Monde, Financial Times,
  Reuters, BBC World, Euronews

### `turkey_mediator_role` (2 narratives)

| id | stance | name | frame |
|---|---:|---|---|
| `turkey_legitimate_broker` | +2 | Legitimate balanced broker | Erdogan's simultaneous channels to Trump, Putin, Pezeshkian, Zelensky, Sisi, and the Gulf are exactly the convening capacity the region needs; the Istanbul venue for Iran-US talks, the Gaza peace board membership, the Egypt rapprochement all evidence Turkey's indispensable role. |
| `turkey_two_faced_opportunist` | -2 | Opportunistic two-faced player | Erdogan plays every side — Hamas patron while courting the Gaza peace board, NATO member while opposing US-Israel action on Iran, Ukraine ally while preserving Russian energy and tourism ties. The "mediator" framing is a vanity project that buys influence without delivering deliverables. |

Publishers (legitimate broker): Daily Sabah, Anadolu Agency, TRT
World, Al-Ahram, Egypt Today, Khaleej Times, Arab News, Al Jazeera,
TASS (EN)
Publishers (two-faced opportunist): Jerusalem Post, Times of Israel,
i24NEWS, Arutz Sheva, Haaretz (critical), eKathimerini, Cyprus Mail,
Fox News, The National (sceptical UAE line)

### `turkey_democratic_backsliding` (2 narratives)

| id | stance | name | frame |
|---|---:|---|---|
| `turkey_authoritarian_drift_critique` | -2 | Authoritarian drift critique | The Imamoglu trial, mass CHP detentions, journalist arrests and crackdown on opposition mayors are the dismantling of Turkish democracy — an Erdogan move to neutralise his strongest 2028 challenger and consolidate one-man rule. |
| `turkey_anti_graft_legalism_defense` | +2 | Anti-graft legal process defence | Investigations and trials against CHP officials and the Imamoglu indictment are legitimate anti-corruption proceedings handled by independent courts; Western press and pro-FETÖ commentary frame routine legal action as political persecution to delegitimise the elected government. |

Publishers (authoritarian drift critique): Tagesschau, Deutsche
Welle, Die Zeit, Frankfurter Allgemeine, Süddeutsche Zeitung,
Der Standard, Die Presse, Der Spiegel, Kurier, BBC World, Reuters,
Associated Press, Le Monde, Bangkok Post, France 24 (EN)
Publishers (anti-graft defence): Daily Sabah, Anadolu Agency, TRT
World

### `turkey_kurdish_question` (2 narratives)

| id | stance | name | frame |
|---|---:|---|---|
| `pkk_terror_full_disarmament` | +2 | PKK as terror, full disarmament required | The PKK and its Syrian YPG / SDF affiliates are a unified terrorist organisation; the only acceptable political process is full disarmament and dissolution; cross-border operations against YPG positions in Syria and PKK leadership in Iraq are legitimate counter-terrorism; "terror-free Türkiye" is the binding state doctrine. |
| `kurdish_political_rights_critique` | -1 | Kurdish political rights critique | Turkey's anti-PKK framing collapses legitimate Kurdish political representation (DEM Party, HDP heritage) into terror designation; YPG / SDF in Syria are democratic partners against ISIS, not PKK affiliates; Ocalan's Imrali messaging shows willingness for political resolution that Ankara repeatedly rejects; cross-border strikes risk regional escalation. |

Publishers (PKK terror): Daily Sabah, Anadolu Agency, TRT World
Publishers (Kurdish rights critique): Al Jazeera, BBC World,
Deutsche Welle, France 24 (EN), Reuters, Associated Press,
Times of Israel (qualified — sees SDF as partner), Jerusalem Post

### `turkey_iran_war_spillover` (2 narratives)

| id | stance | name | frame |
|---|---:|---|---|
| `nato_solidarity_territorial_defense` | +1 | NATO solidarity and territorial defence | Iran's ballistic missile crossing Turkish airspace was an act of aggression intercepted by NATO; the Patriot redeployment to Malatya is legitimate alliance solidarity; Erdogan's call for de-escalation is responsible great-power behaviour, not appeasement. |
| `turkey_wrong_side_on_iran` | -1 | Turkey on the wrong side of the Iran war | By publicly opposing US-Israel strikes on Iran, telling Putin Turkey is against attacks on Iran, and offering Istanbul as a US-Iran venue, Erdogan is shielding the Iranian regime from accountability; NATO solidarity should be unequivocal. |

Publishers (NATO solidarity): Daily Sabah, Anadolu Agency, TRT
World, Reuters, Associated Press, Defense News, Bloomberg, France 24
(EN), Novinite, Tagesschau, Deutsche Welle, Kyiv Post
Publishers (Turkey wrong side): Jerusalem Post, Times of Israel,
i24NEWS, Arutz Sheva, Fox News, eKathimerini, Cyprus Mail, WION

## fn_anchor vocabulary (first-pass; expand via deepseek extractor)

**Rules**: every bundle below follows
[`FN_ANCHOR_VOCABULARY_SPEC.md`](FN_ANCHOR_VOCABULARY_SPEC.md) —
4 pillars (own-side actors, sub-centroid geography, relevant systems,
domain actions), shortest unique form, atoms not phrases, no
third-party leaders (no Trump, Zelensky, Putin, Netanyahu even though
they appear constantly in Turkey events — they belong to other FNs'
sides), no country-name repetition (no `Turkey` / `Turkish` since
`centroid_ids` handles it), Latin-script duplicates only in `en`.
Bundles below are starter seeds — analyst should run
`scripts/extract_fn_anchor_via_deepseek.py` against the Render corpus
before going live, exactly as iran_theater and israel_theater were
built. Target languages: EN, DE, ES, IT, FR, RU, HI, ZH, AR, JA.

```text
turkey_theater
  Pillar 1 (own-side actors): Erdogan, Fidan, AKP, MHP
  Pillar 2 (sub-centroid geography): Istanbul, Ankara, Bosphorus,
    Anatolia, Malatya
  Pillar 3 (relevant systems): NATO, Turkic Council, Organization of
    Turkic States
  Pillar 4 (domain actions): diaspora, accession, presidential decree

  en: Erdogan, Fidan, AKP, MHP, Istanbul, Ankara, Bosphorus,
      Anatolia, Türkiye, Turkic Council, Organization of Turkic
      States, EU accession, diaspora
  de: Tuerkei-Politik, Erdogan, Diaspora, EU-Beitritt, tuerkische
      Aussenpolitik
  es: política turca, diáspora turca, adhesión a la UE
  fr: politique turque, diaspora turque, adhésion à l'UE
  it: politica turca, diaspora turca, adesione all'UE
  ru: Эрдоган, Фидан, Стамбул, Анкара, Босфор, тюркский совет,
      турецкая диаспора
  ar: إردوغان, فيدان, إسطنبول, أنقرة, البوسفور, مجلس الدول التركية,
      الجالية التركية, تركيا
  hi: एर्दोआन, इस्तांबुल, अंकारा, तुर्किये
  zh: 埃尔多安, 伊斯坦布尔, 安卡拉, 博斯普鲁斯, 突厥国家组织
  ja: エルドアン, イスタンブール, アンカラ, ボスポラス, テュルク評議会

turkey_mediator_role
  Pillar 1: Erdogan, Fidan
  Pillar 2: Istanbul, Dolmabahce
  Pillar 3: peace board, Gaza board, Astana process, grain corridor,
    Black Sea grain initiative, Abraham line, Antalya forum
  Pillar 4: mediator, broker, host, convene, summit, talks, ceasefire
    push, shuttle diplomacy, rapprochement

  en: Erdogan, Fidan, mediator, broker, host, convene, summit,
      shuttle diplomacy, rapprochement, peace board, Gaza board,
      board of peace, Astana, grain corridor, Antalya forum,
      Istanbul venue, Dolmabahce
  de: Vermittler, Vermittlung, Mittler, Gastgeber, Annaeherung,
      Gipfel, Gespraeche, Getreidekorridor, Astana-Format
  es: mediador, mediación, anfitrión, cumbre, conversaciones,
      acercamiento, corredor de granos
  fr: médiateur, médiation, hôte, sommet, pourparlers, rapprochement,
      corridor céréalier
  it: mediatore, mediazione, ospite, vertice, colloqui,
      riavvicinamento, corridoio del grano
  ru: посредник, посредничество, принимающая сторона, саммит,
      переговоры, сближение, зерновой коридор, астанинский формат
  ar: وسيط, وساطة, مضيف, قمة, محادثات, تقارب, ممر الحبوب,
      مجلس السلام, مسار أستانا
  hi: मध्यस्थ, मध्यस्थता, मेजबान, शिखर वार्ता, बातचीत
  zh: 调解者, 调停, 东道主, 峰会, 会谈, 和解, 粮食走廊, 阿斯塔纳进程
  ja: 仲介者, 仲介, 開催, 首脳会談, 協議, 和解, 穀物回廊, アスタナ協議

turkey_democratic_backsliding
  Pillar 1: Imamoglu, CHP, DEM Party, FETÖ, Gulen, Bahceli, Ozel
  Pillar 2: Istanbul, Silivri (prison), Ankara, Izmir
  Pillar 3: indictment, corruption probe, trial, press card
    revocation, social media restriction, RTÜK
  Pillar 4: detain, arrest, jail, sentence, ban, dismiss, raid,
    protest, rally, press freedom, judicial independence

  en: Imamoglu, CHP, Ozel, Yavas, DEM Party, HDP, Silivri,
      indictment, corruption probe, opposition mayor, opposition
      crackdown, press freedom, RTÜK, social media ban, rally,
      protest, journalist arrested, judicial independence
  de: Imamoglu, CHP, DEM-Partei, Oppositionsbuergermeister,
      Pressefreiheit, Justizunabhaengigkeit, Korruptionsverfahren,
      Anklage, Verhaftung, Demonstration, Razzia
  es: Imamoglu, partido CHP, alcalde opositor, libertad de prensa,
      independencia judicial, procesamiento, detención, protesta
  fr: Imamoglu, CHP, maire d'opposition, liberté de la presse,
      indépendance de la justice, inculpation, arrestation,
      manifestation
  it: Imamoglu, CHP, sindaco d'opposizione, libertà di stampa,
      indipendenza della magistratura, incriminazione, arresto,
      protesta
  ru: Имамоглу, НРП, ДЕМ, оппозиционный мэр, свобода прессы,
      независимость суда, обвинение, арест, протест, митинг
  ar: إمام أوغلو, حزب الشعب الجمهوري, حزب ديم, عمدة المعارضة,
      حرية الصحافة, استقلال القضاء, لائحة اتهام, اعتقال, احتجاج
  hi: इमामोग्लू, सीएचपी, विपक्षी मेयर, प्रेस की स्वतंत्रता,
      न्यायिक स्वतंत्रता
  zh: 伊马姆奥卢, 共和人民党, 反对派市长, 新闻自由, 司法独立,
      起诉, 抗议, 拘留
  ja: イマモール, 共和人民党, 野党市長, 報道の自由, 司法の独立,
      起訴, 逮捕, 抗議

turkey_kurdish_question
  Pillar 1: PKK, YPG, SDF, DEM Party, HDP, Ocalan, Mazloum Abdi,
    Bahceli (PKK-disarmament initiator), Karasu
  Pillar 2: Diyarbakir, Hakkari, Sirnak, Qandil, Imrali, Tal Rifaat,
    Manbij, Kobani
  Pillar 3: terror-free Türkiye, disarmament process, peace process,
    Imrali talks, cross-border operation, Operation Claw, Euphrates
    Shield
  Pillar 4: disarm, dissolve, lay down arms, designate, amnesty,
    delisting, raid, airstrike, ground operation

  en: PKK, YPG, SDF, DEM Party, HDP, Ocalan, Mazloum, Abdi, Imrali,
      Qandil, Diyarbakir, Hakkari, terror-free, terror-free Türkiye,
      disarmament, lay down arms, peace process, Imrali process,
      cross-border operation, Operation Claw, Euphrates Shield,
      Tal Rifaat, Manbij, Kobani
  de: PKK, YPG, SDF, DEM-Partei, HDP, Oecalan, Diyarbakir, Imrali,
      terrorfreie Tuerkei, Entwaffnung, Friedensprozess,
      grenzueberschreitende Operation, Operation Klaue
  es: PKK, YPG, FDS, partido DEM, HDP, Ocalan, Imrali, desarme,
      proceso de paz, operación transfronteriza
  fr: PKK, YPG, FDS, parti DEM, HDP, Ocalan, Imrali, désarmement,
      processus de paix, opération transfrontalière
  it: PKK, YPG, SDF, partito DEM, HDP, Ocalan, Imrali, disarmo,
      processo di pace, operazione transfrontaliera
  ru: РПК, YPG, СДС, ДЕМ, ХДП, Оджалан, Имралы, Кандиль, Диярбакыр,
      разоружение, мирный процесс, трансграничная операция,
      операция Коготь
  ar: حزب العمال الكردستاني, ي ب ك, قسد, حزب ديم, حزب الشعوب
      الديمقراطي, أوجلان, إيمرالي, قنديل, ديار بكر, نزع السلاح,
      عملية المخلب, عملية درع الفرات, عملية عبر الحدود
  hi: पीकेके, वाईपीजी, एसडीएफ, ओजलान, इमराली, निरस्त्रीकरण,
      शांति प्रक्रिया
  zh: 库尔德工人党, 人民保护部队, 叙利亚民主力量, 厄贾兰, 伊姆拉勒,
      解除武装, 和平进程, 跨境行动, 利爪行动
  ja: クルド労働者党, YPG, シリア民主軍, オジャラン, イムラル,
      武装解除, 和平プロセス, 越境作戦

turkey_iran_war_spillover
  Pillar 1: Erdogan, Fidan, Hakan Fidan, Turkish General Staff
  Pillar 2: Malatya, Kurecik, Incirlik, southeastern border, Van
  Pillar 3: NATO Patriot, Patriot system, AN/TPY-2, NATO air defence,
    AWACS, Article 5, Ramstein
  Pillar 4: deploy, redeploy, intercept, shoot down, airspace
    violation, de-escalation, ceasefire call

  en: Erdogan, Fidan, NATO Patriot, Patriot system, NATO air
      defence, NATO air defense, AN/TPY-2, Kurecik radar, Malatya,
      Incirlik, AWACS, Article 5, airspace violation, intercept,
      shoot down, de-escalation, Iranian missile, Iranian drone,
      ballistic missile overflight, Ramstein
  de: NATO-Patriot, Patriot-System, NATO-Luftabwehr, Kurecik-Radar,
      Malatya, Incirlik, Artikel 5, Luftraumverletzung, Abfangen,
      Deeskalation, iranische Rakete, iranische Drohne, Ramstein
  es: Patriot de la OTAN, sistema Patriot, defensa aérea de la OTAN,
      Kurecik, Malatya, Incirlik, Artículo 5, violación del espacio
      aéreo, interceptación, desescalada, misil iraní
  fr: Patriot de l'OTAN, système Patriot, défense aérienne de
      l'OTAN, Kurecik, Malatya, Incirlik, article 5, violation de
      l'espace aérien, interception, désescalade, missile iranien
  it: Patriot NATO, sistema Patriot, difesa aerea NATO, Kurecik,
      Malatya, Incirlik, articolo 5, violazione dello spazio aereo,
      intercettazione, de-escalation, missile iraniano
  ru: Patriot НАТО, система Patriot, ПВО НАТО, Куреджик, Малатья,
      Инджирлик, статья 5, нарушение воздушного пространства,
      перехват, деэскалация, иранская ракета, иранский дрон,
      Рамштайн
  ar: باتريوت الناتو, منظومة باتريوت, الدفاع الجوي للناتو, كوريجك,
      ملاطية, إنجرليك, المادة الخامسة, انتهاك المجال الجوي,
      اعتراض, تهدئة, صاروخ إيراني, طائرة مسيرة إيرانية
  hi: नाटो पैट्रियट, पैट्रियट प्रणाली, नाटो वायु रक्षा, मलात्या,
      अनुच्छेद 5, हवाई क्षेत्र उल्लंघन, अवरोधन, ईरानी मिसाइल
  zh: 北约爱国者, 爱国者系统, 北约防空, 库雷吉克, 马拉蒂亚, 因吉尔利克,
      第五条款, 领空侵犯, 拦截, 降级, 伊朗导弹, 伊朗无人机
  ja: NATOパトリオット, パトリオット, NATO防空, クレジク, マラティヤ,
      インジルリク, 第5条, 領空侵犯, 迎撃, デエスカレーション,
      イランのミサイル
```

## Open questions before SQL

1. **Mediator vs theater overlap**: `turkey_mediator_role` carries a
   lot of cross-cutting signal (Gaza board, Iran-US talks, Zelensky
   visit, Sisi rapprochement). Risk that it cannibalises the theater
   catch-all. Mitigation: anchor bundle for `turkey_mediator_role`
   centres on diplomatic verbs (`mediator`, `broker`, `host`, `summit`,
   `shuttle`) and the named diplomatic concepts; the theater catch-all
   stays on Turkey-as-actor framings without the diplomatic verbs.
   Bootstrap order matters — atomic FNs first, theater second
   (catch-all exclusion already enforced).

2. **`turkey_kurdish_question` vs `syria_kurdish_question` overlap**:
   The PKK / YPG / SDF entities surface on both. The Syria FN is
   centroid-bounded to MIDEAST-LEVANT / TURKEY / IRAQ / USA, and the
   Turkey FN to MIDEAST-TURKEY / LEVANT / IRAQ. Centroid overlap
   alone won't separate them. The split is meant to be enforced by
   anchor vocabulary and publisher cohort:
   - Turkey FN anchor includes Imrali, Ocalan, "terror-free Türkiye",
     DEM Party, Operation Claw, cross-border operation, Qandil.
   - Syria FN anchor includes AANES, Rojava, Hasakah, Qamishli,
     Sheikh Maqsoud, Aleppo Kurds.
   - Where a title hits both bundles AND the publisher is in both
     narrative cohorts, attribution to both FNs is the correct outcome
     under the 1-to-1 narrative model — the same title can attach to
     two narratives on two different FNs. Audit a sample after
     bootstrap to confirm cross-attribution counts look reasonable
     (target: <20% of Turkey-FN titles also attached to Syria-FN
     narratives).

3. **DACH cohort dominance**: Frankfurter Allgemeine, Kurier,
   Tagesschau, Handelsblatt, Die Zeit, Süddeutsche, Der Standard,
   Die Presse, Der Spiegel together produce >2,000 Turkey-marked
   titles (180d) — far more than any other cohort. Many of these are
   diaspora / business stories that don't carry stance. Risk that
   the `turkey_eu_engagement_pragmatic` and
   `turkey_authoritarian_drift_critique` narratives over-attribute
   on volume. Mitigation: tight anchor vocab for these narratives
   (Imamoglu, CHP, Pressefreiheit), and post-bootstrap audit of the
   sample headlines on the brick.

4. **Turkish-language publishers absent from corpus**: the corpus
   covers Daily Sabah, Anadolu Agency, TRT World for Turkish state
   desk, but no Cumhuriyet / Sözcü / Hürriyet / BirGün / Bianet for
   the Turkish opposition / liberal / Kurdish-press view. The
   `turkey_authoritarian_drift_critique` and
   `kurdish_political_rights_critique` narratives have to lean on
   Western liberal publishers as proxies. This is honest — that's
   what the corpus contains — but worth flagging if Turkish-language
   ingestion expands later.

5. **Black Sea / NATO eastern flank — theater or atomic?**: 77 Black
   Sea mentions in Turkey-marked titles. Most are Ukrainian drone
   attacks on Russian oil terminals (Novorossiysk, CPC) which sit
   primarily on the Ukraine war surface, not Turkey's. Turkey's own
   Black Sea moves (drone strikes on tankers, Montreux Convention,
   F-16 deployments to Cyprus' occupied north) are sparse. Keep on
   theater catch-all for now; reconsider if a future spec for the
   Ukraine war creates a `black_sea_naval_war` atomic that needs to
   cross-list MIDEAST-TURKEY.

6. **Stance values**: theater carries +2 / -2 / 0 (mirror of
   iran_theater) plus the spillover FN uses +1 / -1 rather than
   +2 / -2 because the Turkey-side framing on Iran is genuinely
   milder than the direct Iran-Israel framing. Open for review.

## Build order (suggested)

1. **Review this spec.** Adjust atomic FN decomposition + narrative
   roster + Kurdish question scope versus the Syria spec.
2. **Anchor extraction.** Run
   `scripts/extract_fn_anchor_via_deepseek.py` for each of the 5
   fn_anchor bundles against the Render corpus. Hand-edit the
   outputs to drop third-party leader names (Trump, Putin, Zelensky,
   Netanyahu) which will absolutely show up because they appear in
   the headlines about Erdogan.
3. **Publisher cohort calibration.** Run
   `scripts/calibrate_narrative_keywords.py` per narrative against
   the Render corpus, especially for the DACH-heavy narratives
   where over-attribution is the main risk.
4. **Write migration**:
   `db/migrations/20260514_friction_node_turkey_theater_seed.sql`
   mirroring `20260512_israel_theater_seed.sql` and
   `20260513_friction_node_syria_theater_seed.sql` (theater + 4
   atomic FNs + 5 fn_anchor bundles + 11 narratives + sanity check
   DO block). Apply locally first.
5. **Bootstrap locally**:
   `python scripts/bootstrap_friction_node.py --fn-id <each id>`.
   Run atomic FNs first, theater last (catch-all exclusion). Inspect
   per-narrative match counts. Goal: each pro/con narrative ≥80
   titles, ≥30 events. If thinner, widen anchor or publisher set;
   if too broad (>2,000), tighten anchor.
6. **Cross-FN audit**: count titles attributing to both
   `turkey_kurdish_question` and `syria_kurdish_question` narratives.
   If cross-attribution exceeds ~20% of Turkey-FN titles, tighten
   the Turkey anchor to bias toward Turkey-side framing vocabulary.
7. **Sanity-check pages**: `/en/friction-nodes/turkey_theater` plus
   each atomic FN. Check brick hues, sample headlines on-frame,
   country pills, activity charts credible. Spot-check the
   `turkey_authoritarian_drift_critique` brick for Imamoglu-trial
   coverage actually showing up.
8. **Push to Render**: apply migration on Render, run bootstrap on
   Render, bust frontend cache. Same protocol as israel_theater /
   syria_theater deploys.

## Expected DecisionLog entry

```yaml
- id: D-08x
  date: 2026-05-14
  type: data-model
  status: accepted
  title: Seed Turkey theater (regional broker + backsliding) — 4 atomic FNs + 11 narratives
  rationale:
    - MIDEAST-TURKEY centroid carries ~3,200 titles / ~1,200 promoted events (180d)
      currently unattributed to any friction node
    - Four distinct narrative contests visible in publisher cohort data:
      mediator role, democratic backsliding, Kurdish question (Turkey-side framing),
      Iran-war spillover
    - Cross-listing protocol with syria_kurdish_question handled via anchor vocab,
      not centroid alone
  scope:
    - friction_nodes: turkey_theater (theater), turkey_mediator_role,
      turkey_democratic_backsliding, turkey_kurdish_question, turkey_iran_war_spillover
    - narratives_v2: 11 narratives (3 theater + 2 per atomic FN)
    - taxonomy_v3: 5 fn_anchor bundles
  consequences:
    - Turkey coverage moves from unattributed to a four-surface contested theater
    - Resolves overlap with Syria theater by anchor vocabulary split, not centroid
    - Establishes a pattern for non-state-actor-anchored theaters (Turkey is an
      actor across many centroids, not a static conflict zone)
```

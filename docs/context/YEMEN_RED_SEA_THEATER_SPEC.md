# Yemen / Red Sea Theater — Build Spec

**Date drafted**: 2026-05-13
**Status**: Draft for review. No DB writes yet.
**Pattern**: Follows `iran_theater` / `israel_theater` / `syria_theater`
(D-075..D-08x, 2026-05-12..13).

## Why now

The `MIDEAST-YEMEN` centroid carries 571 titles and 165 promoted
events over the past 180 days. No friction node currently attributes
this surface — `iran_proxy_network` is centroid-locked to
`MIDEAST-IRAN`, so Yemen-centroid-only titles never attach.

Top promoted Yemen events (180d, by source count):

- 26 srcs — "Yemen's Houthis launch missile attacks on Israel,
  entering regional conflict"
- 16 srcs — "Houthis launch missile attacks on Israel, opening new
  front in conflict"
- 9 srcs — "Saudi-led coalition strikes southern Yemen after
  separatist leader skips talks"
- 7 srcs — "Houthis, Hezbollah and Iran launch coordinated attack on
  Israel"
- 6 srcs — "Iran threatens to block key shipping lanes if US naval
  blockade continues"
- 4 srcs — "Houthi attacks on Israel raise new Red Sea shipping
  concerns" / "Saudi Arabia reports missile, drone attacks on Red
  Sea port, key refinery"
- 3 srcs — "Maersk resumes shipping through Red Sea after ceasefire" /
  "Yemeni southern separatists in Riyadh announce disputed
  disbanding of STC"

Publisher signal in Yemen-tagged 180d corpus (n ≥ 8): Al-Ahram (73),
Al Arabiya (68), Al Jazeera (53), Press TV (38), Jerusalem Post (36),
Times of Israel (32), Anadolu Agency (31), Reuters (14), Arab News
(11), The National (11), CGTN (10), Deutsche Welle (10), France 24
(10), i24NEWS (9), Daily Sabah (9), Egypt Today (9), France 24 (EN)
(9), TASS (EN) (8), Bloomberg (8). Distinct cohorts visible: Saudi/
pan-Arab Sunni, resistance/Iran-aligned, Israeli/pro-Israel, Western
mainstream, Russia/multipolar, Asian shipping desk (Nikkei, Straits
Times, NDTV, WION).

## Theater shape

```
yemen_red_sea_theater (catch-all, fn_type='theater')
   |
   +-- red_sea_shipping_security    Houthi attacks on commercial shipping,
   |                                Bab al-Mandab chokepoint, Operation
   |                                Prosperity Guardian / EU Aspides
   |
   +-- houthi_strikes_on_israel     Houthi ballistic/drone attacks on Israel
   |                                from Yemeni soil, joint ops with Iran
   |                                and Hezbollah
   |
   +-- saudi_houthi_war             Saudi-led coalition vs Houthi / Ansar
                                    Allah, Aden government legitimacy,
                                    STC (UAE-backed) separatism in the south
```

Three atomic FNs chosen because the data shows three distinct
publisher cohorts and three distinct framing axes:

- Red Sea shipping is a Western-shipping-desk + Israeli + Iran-aligned
  contest about freedom of navigation.
- Houthi-Israel strikes are a fourth-front extension of the Gaza/Iran
  war with its own pro/con publisher split.
- The Saudi-Houthi war (and its STC sub-arc) is an intra-Arab
  legitimacy contest dominated by Saudi / Egyptian state outlets vs
  pan-Arab critics.

The catch-all theater carries the broader Iran-axis framing of Yemen
as the "fourth front" of the regional war, plus the humanitarian /
WFP collapse narrative which is too thin (~2 events) to justify its
own atomic FN.

### What this theater does NOT cover (boundary decisions)

- **Strait of Hormuz** stays in `iran_theater /
  strait_of_hormuz_sovereignty`. Bab al-Mandab is the Red Sea
  chokepoint and is distinct.
- **IRGC / Quds Force / proxy network framing on Iranian soil**
  stays in `iran_theater / iran_proxy_network` (centroid IRAN only).
  Yemen-centroid-only Houthi titles will not attribute to
  `iran_proxy_network` — the centroid gate segregates them
  automatically. We do NOT need to police this with vocabulary.
- **Saudi mining-jobs ads** (Mining.com, ~12 titles) are corpus noise
  from a publisher that surfaces in `MIDEAST-SAUDI` for unrelated
  reasons. Publisher cohort excludes them.

## FN definitions

### `yemen_red_sea_theater` (theater, catch-all)

- **Name (EN)**: Yemen and the Red Sea front
- **Name (DE)**: Jemen und die Front am Roten Meer
- **fn_type**: `theater`
- **member_fn_ids**: `[red_sea_shipping_security,
  houthi_strikes_on_israel, saudi_houthi_war]`
- **centroid_ids**: `[MIDEAST-YEMEN, MIDEAST-SAUDI, MIDEAST-GULF,
  MIDEAST-EGYPT, MIDEAST-IRAN, MIDEAST-ISRAEL, AMERICAS-USA,
  EUROPE-UK, AFRICA-HORN]`
- **Description (EN)**: Yemen has become the fourth operational front
  of the regional war: Houthi missile and drone attacks on Israel,
  threats against Bab al-Mandab shipping, the long-running Saudi-led
  coalition war with the Ansar Allah movement, and the southern STC
  separatist contest. Coverage clusters around resistance-axis
  framing on one side and Saudi-Sunni-stabilisation framing on the
  other, with Western shipping desks treating the Red Sea as a freedom-
  of-navigation problem.
- **Description (DE)**: Jemen ist zur vierten Front des regionalen
  Krieges geworden: Houthi-Raketen und -Drohnen gegen Israel,
  Drohungen gegen die Schifffahrt am Bab al-Mandab, der anhaltende
  Krieg der saudisch gefuehrten Koalition mit der Ansar-Allah-
  Bewegung und der suedliche STC-Separatistenstreit. Die
  Berichterstattung pendelt zwischen Widerstandsachse-Rahmung
  einerseits und saudisch-sunnitischer Stabilisierungs-Rahmung
  andererseits; westliche Schifffahrts-Redaktionen behandeln das
  Rote Meer als Frage der freien Seefahrt.
- **Editorial summary (EN)**: Yemen sits on the southern jaw of the
  Red Sea, hosts a movement (Ansar Allah / the Houthis) that
  coordinates operationally with Iran and Hezbollah, and remains a
  contested state — UN-recognised government in Aden, UAE-backed
  STC separatists, de facto Houthi authority in Sanaa. Narratives
  split four ways: Saudi-Egyptian state media as Iran-proxy
  destabilisation, resistance-axis outlets as fourth-front Gaza
  solidarity, Western shipping desks as freedom-of-navigation, and
  Israeli outlets as Iran-axis kinetic problem (including the
  reported Somaliland-base exploration).
- **Editorial summary (DE)**: Jemen liegt am suedlichen Kiefer des
  Roten Meeres, beherbergt eine mit Iran und Hisbollah operativ
  koordinierende Bewegung (Ansar Allah / Houthi) und bleibt ein
  umstrittener Staat — UN-anerkannte Regierung in Aden, VAE-
  gestuetzte STC-Separatisten, faktische Houthi-Herrschaft in
  Sanaa. Narrative spalten vierfach: saudisch-aegyptisch als
  iranische Stellvertreter-Destabilisierung, Widerstandsachse als
  vierte Front Gaza-Solidaritaet, westliche Schifffahrts-
  Redaktionen als Frage der freien Seefahrt, israelische Medien
  als kinetisches Iran-Achsen-Problem (mit berichteter Somaliland-
  Basis-Sondierung).

### `red_sea_shipping_security` (atomic)

- **Name (EN)**: Red Sea and Bab al-Mandab shipping security
- **Name (DE)**: Sicherheit der Schifffahrt am Roten Meer und Bab al-
  Mandab
- **centroid_ids**: `[MIDEAST-YEMEN, MIDEAST-SAUDI, MIDEAST-GULF,
  MIDEAST-EGYPT, AMERICAS-USA, EUROPE-UK, AFRICA-HORN]`
- **Description (EN)**: Houthi attacks on commercial vessels
  transiting the Bab al-Mandab strait and the southern Red Sea; US-
  UK-led Operation Prosperity Guardian, EU naval Operation Aspides;
  the rerouting of container traffic around the Cape of Good Hope;
  Maersk and other shippers' on-again-off-again returns;
  reported Israeli exploration of a Somaliland base.
- **Description (DE)**: Houthi-Angriffe auf Handelsschiffe in der
  Meerenge Bab al-Mandab und im suedlichen Roten Meer; US-britische
  Operation Prosperity Guardian, EU-Marineoperation Aspides;
  Umleitung des Containerverkehrs um das Kap der Guten Hoffnung;
  schwankende Rueckkehr von Maersk und anderen Reedereien;
  berichtete israelische Sondierung einer Basis in Somaliland.
- **Editorial summary (EN)**: Distinct from the Strait of Hormuz
  contest (which sits in `iran_theater`), Bab al-Mandab is a Yemen-
  side chokepoint moving roughly 12% of global trade and 30% of
  container traffic. Western shipping desks and Israeli outlets
  converge on "freedom of navigation must be defended"; resistance
  outlets defend Houthi targeting as Gaza pressure or argue the
  Saudi-Yanbu workaround's limits. "Double blockade" (Hormuz + Bab
  al-Mandab) is a recurring 2026 motif in Asian shipping coverage
  (Nikkei, Straits Times, Korea Herald).
- **Editorial summary (DE)**: Anders als der Hormus-Streit (im
  `iran_theater`) ist Bab al-Mandab ein Jemen-seitiger Engpass mit
  rund 12% des Welthandels und 30% des Containerverkehrs. Westliche
  Schifffahrts-Redaktionen und israelische Medien teilen die
  "Freiheit der Seefahrt muss geschuetzt werden"-Rahmung;
  Widerstands-Stimmen verteidigen Houthi-Schlaege als Gaza-
  Pression oder weisen auf die Grenzen der saudischen Yanbu-
  Ausweichroute hin. Die "doppelte Blockade" (Hormus + Bab al-
  Mandab) ist ein wiederkehrendes Motiv 2026 in asiatischen
  Schifffahrts-Medien.

### `houthi_strikes_on_israel` (atomic)

- **Name (EN)**: Houthi strikes on Israel
- **Name (DE)**: Houthi-Schlaege gegen Israel
- **centroid_ids**: `[MIDEAST-YEMEN, MIDEAST-ISRAEL, MIDEAST-IRAN]`
- **Description (EN)**: Houthi ballistic missile and drone attacks
  on Israeli territory (Tel Aviv, Ben Gurion airport, Eilat),
  declared as joint operations with Iran and Hezbollah; Israeli
  retaliation in Yemen; intercepts; the question of whether the
  Houthis acted on Tehran's direction or independently.
- **Description (DE)**: Houthi-Raketen und -Drohnenangriffe auf
  israelisches Gebiet (Tel Aviv, Flughafen Ben Gurion, Eilat),
  erklaert als gemeinsame Operationen mit Iran und Hisbollah;
  israelische Vergeltung in Jemen; Abfaenge; die Frage, ob die
  Houthi auf Teheraner Weisung oder unabhaengig handeln.
- **Editorial summary (EN)**: The corpus's strongest Yemen signal
  (top promoted event = 26 sources). Israeli outlets frame Houthi
  strikes as Iran-orchestrated multi-front aggression demanding
  kinetic answers (Hodeidah port, Sanaa airport, reported
  Somaliland-base agreement). Resistance outlets present the same
  strikes as legitimate Gaza solidarity under unified axis-of-
  resistance command. FN boundary: "Houthi missile hits Tel Aviv"
  attributes here; "Houthi attack on Galaxy Leader" attributes to
  `red_sea_shipping_security`.
- **Editorial summary (DE)**: Das staerkste Jemen-Signal im Korpus
  (Top-Event mit 26 Quellen). Israelische Medien rahmen Houthi-
  Schlaege als iranisch orchestrierte Mehrfronten-Aggression mit
  kinetischer Antwort (Hafen Hodeida, Flughafen Sanaa, berichtete
  Somaliland-Basis-Vereinbarung). Widerstands-Medien praesentieren
  dieselben Schlaege als legitime Gaza-Solidaritaet unter
  einheitlichem Widerstandsachsen-Kommando. FN-Grenze: "Houthi-
  Rakete trifft Tel Aviv" hier; "Houthi-Angriff auf Galaxy Leader"
  in `red_sea_shipping_security`.

### `saudi_houthi_war` (atomic)

- **Name (EN)**: Saudi-led coalition vs Houthi war and southern
  STC separatism
- **Name (DE)**: Krieg der saudisch gefuehrten Koalition gegen die
  Houthi und suedlicher STC-Separatismus
- **centroid_ids**: `[MIDEAST-YEMEN, MIDEAST-SAUDI, MIDEAST-GULF,
  MIDEAST-EGYPT]`
- **Description (EN)**: The long-running war between the Saudi-led
  Arab coalition (Coalition to Restore Legitimacy in Yemen) backing
  the internationally-recognised Presidential Leadership Council in
  Aden, the Houthi / Ansar Allah authority in Sanaa, and the UAE-
  backed Southern Transitional Council (STC). Covers the 2026 STC
  dissolution / disputed disbanding, separatist leader flight,
  coalition strikes in southern Yemen, and Saudi reconstruction
  pledges.
- **Description (DE)**: Der anhaltende Krieg zwischen der saudisch
  gefuehrten arabischen Koalition (Koalition zur Wiederherstellung
  der Legitimitaet im Jemen) zur Stuetzung des international
  anerkannten Praesidialen Fuehrungsrats in Aden, der Houthi-
  / Ansar-Allah-Autoritaet in Sanaa und des von den VAE
  unterstuetzten Suedlichen Uebergangsrats (STC). Umfasst die
  STC-Aufloesung 2026, die Flucht des Separatistenfuehrers,
  Koalitionsschlaege im Sueden und saudische Wiederaufbau-
  Zusagen.
- **Editorial summary (EN)**: The intra-Arab leg of the Yemen
  story, dominated by Saudi-Egyptian state press (Al-Ahram, Al
  Arabiya). Narrative split is *not* the Iran-axis split — it's
  Saudi-coalition legitimacy framing vs. pan-Arab critique of
  southern fragmentation and STC dissolution. The 2026 STC self-
  dissolution and the separatist leader's flight to the UAE (with
  Saudi accusations against Abu Dhabi) opens a thin but real Gulf-
  bloc fissure the corpus is starting to surface.
- **Editorial summary (DE)**: Der innerarabische Strang der Jemen-
  Geschichte, dominiert von der saudisch-aegyptischen Staatspresse
  (Al-Ahram, Al Arabiya). Die Spaltung ist *nicht* die Iran-Achsen-
  Spaltung — es geht um saudisch-koalitionaere Legitimitaets-
  Rahmung gegen panarabische Kritik an der suedlichen
  Fragmentierung und STC-Aufloesung. Die STC-Selbstaufloesung 2026
  und die Flucht des Separatistenfuehrers in die VAE (mit
  saudischen Vorwuerfen gegen Abu Dhabi) oeffnet einen duennen,
  aber realen Riss im Golf-Block.

## Narrative slots (proposed, 9 total)

Stance is **toward the Houthi / Ansar Allah authority in Sanaa** as
the theater's primary actor. This mirrors the iran_theater convention
(stance toward Iran) — the Houthis are the actor whose actions
trigger every contested narrative in the theater. Saudi-Sunni framing
that opposes the Houthis registers as -1 / -2 here; resistance-axis
framing that defends the Houthis registers as +1 / +2.

### Theater-level (3 narratives)

| id | stance | name (EN) | name (DE) | frame |
|---|---:|---|---|---|
| `houthis_fourth_front_solidarity` | +2 | Fourth-front solidarity | Vierte Front: Solidaritaet | Resistance / Iran-aligned: Houthi attacks on Israel and Red Sea shipping are legitimate solidarity-with-Gaza pressure under a unified axis-of-resistance command; the Yemeni movement has the right to extend the war until Gaza ceasefire holds. |
| `iran_proxy_destabilisation` | -2 | Iranian proxy destabilising the region | Iranischer Stellvertreter destabilisiert die Region | Saudi / Egyptian state + Israeli + pro-Western: Houthis are an Iranian-armed proxy that has hijacked the Yemeni state, threatens Arab order, and must be militarily defeated; STC fracture is one symptom. |
| `western_pragmatic_navigation` | 0 | Western pragmatic navigation framing | Westliche pragmatische Schifffahrts-Rahmung | EU / E3 / US shipping-desk mainstream: the Houthi problem is primarily a freedom-of-navigation problem requiring coalition naval pressure (Prosperity Guardian, Aspides) and a Gaza ceasefire that removes the Houthis' stated casus belli; humanitarian impact in Yemen is a parallel concern, not primary frame. |

Publishers — `houthis_fourth_front_solidarity`: Press TV, Al Jazeera,
Al Mayadeen, Fars News, IRNA, TRT World, Anadolu Agency, Daily Sabah,
CGTN, TASS (EN), RT.
Publishers — `iran_proxy_destabilisation`: Al-Ahram, Al Arabiya,
Arab News, The National, Khaleej Times, Gulf News, Egypt Today,
Jerusalem Post, Times of Israel, The Times of Israel, i24NEWS,
Fox News, Haaretz.
Publishers — `western_pragmatic_navigation`: Reuters, Associated
Press, AFP, BBC World, France 24, France 24 (EN), Deutsche Welle,
Tagesschau, Financial Times, Bloomberg, Wall Street Journal,
The Guardian, Le Monde, Nikkei Asia, Straits Times.

### `red_sea_shipping_security` (2 narratives)

| id | stance | name (EN) | name (DE) | frame |
|---|---:|---|---|---|
| `freedom_of_navigation_defense` | -1 | Freedom of navigation must be defended | Schutz der freien Seefahrt | Western shipping-desk + Israeli + Saudi: Houthi attacks on commercial vessels violate UNCLOS freedom-of-navigation rights and global trade order; Operation Prosperity Guardian, EU Aspides, and US Fifth Fleet operations are necessary and lawful; Saudi Yanbu rerouting and reported Somaliland base are pragmatic adaptations. |
| `houthi_naval_pressure_legitimate` | +2 | Naval pressure is legitimate Gaza solidarity | Maritimer Druck als legitime Gaza-Solidaritaet | Resistance-axis: Houthi targeting of Israel-linked shipping is a legitimate non-state form of pressure tied explicitly to a Gaza ceasefire; Western naval coalitions and reported Israeli outposts in Somaliland are imperial overreach into Yemeni and Arab maritime sovereignty. |

Publishers (freedom of navigation): Reuters, Associated Press, AFP,
BBC World, France 24, France 24 (EN), Financial Times, Bloomberg,
Wall Street Journal, Nikkei Asia, Straits Times, Korea Herald,
Jerusalem Post, Times of Israel, Fox News, Al Arabiya, Al-Ahram,
The National, Daily Mirror, OilPrice

Publishers (naval pressure legitimate): Press TV, Al Jazeera, Al
Mayadeen, Fars News, IRNA, TRT World, Anadolu Agency, Daily Sabah,
CGTN, TASS (EN)

### `houthi_strikes_on_israel` (2 narratives)

| id | stance | name (EN) | name (DE) | frame |
|---|---:|---|---|---|
| `houthi_resistance_strikes_legitimate` | +2 | Solidarity strikes on Israel are legitimate | Solidaritaetsschlaege gegen Israel sind legitim | Resistance-axis: Houthi missile and drone attacks on Israel are legitimate solidarity action with Gaza, coordinated with Iran and Hezbollah under a single axis-of-resistance command, deepening Israeli vulnerability and establishing a new deterrence equation. |
| `houthi_iranian_proxy_aggression` | -2 | Iranian proxy aggression on Israel | Iranische Stellvertreter-Aggression gegen Israel | Israeli + pro-Israel + Saudi-aligned: Houthi strikes are Iranian-orchestrated proxy aggression demanding kinetic response on Yemeni soil (Hodeidah port, Sanaa airport, Houthi leadership) plus expanded regional partnerships (Somaliland base, deeper Gulf cooperation) to interdict Iranian weapons pipelines. |

Publishers (resistance strikes legitimate): Press TV, Fars News,
IRNA, Al Mayadeen, Al Jazeera, TRT World, Anadolu Agency, Daily
Sabah, CGTN, TASS (EN)

Publishers (Iranian proxy aggression): Jerusalem Post, Times of
Israel, The Times of Israel, i24NEWS, Israel Hayom, Fox News, Arutz
Sheva, Haaretz, Al-Ahram, Al Arabiya, Arab News

### `saudi_houthi_war` (2 narratives)

Note: stance is **toward the Houthis** (the theater primary actor),
not toward Saudi Arabia. A narrative defending Saudi-coalition
intervention against the Houthis reads as -2 here; defence of Houthi
control or critique of coalition action reads positively.

| id | stance | name (EN) | name (DE) | frame |
|---|---:|---|---|---|
| `saudi_coalition_legitimacy_restoration` | -2 | Restoring Yemeni legitimacy | Wiederherstellung jemenitischer Legitimitaet | Saudi / Egyptian / pan-Arab Sunni: the Saudi-led coalition is restoring the internationally-recognised Yemeni government; Houthi rule in Sanaa is an Iran-backed coup; STC self-dissolution and southern unification under the Presidential Leadership Council are necessary; UAE-backed separatism was a destabilising mistake. |
| `houthi_authority_legitimate_resistance` | +2 | Sanaa government is legitimate national authority | Regierung in Sanaa als legitime nationale Autoritaet | Resistance-axis + critical pan-Arab: the de facto Sanaa authority represents Yemeni national resistance to Saudi and Western intervention; the Saudi-led coalition is an aggressor that has destroyed Yemeni infrastructure; the STC was a UAE-backed colonial project whose collapse exposes coalition failure. |

Publishers (coalition legitimacy): Al-Ahram, Al Arabiya, Arab News,
The National, Khaleej Times, Gulf News, Egypt Today, Daily Sabah,
Anadolu Agency

Publishers (Houthi authority legitimate): Press TV, Al Jazeera, Al
Mayadeen, Fars News, IRNA

## fn_anchor vocabulary (first-pass; expand via deepseek extractor)

**Rules**: every bundle below follows
[`FN_ANCHOR_VOCABULARY_SPEC.md`](FN_ANCHOR_VOCABULARY_SPEC.md) —
4 pillars (own-side actors, sub-centroid geography, relevant
systems, domain actions), shortest unique form, atoms not phrases,
no third-party leaders, no country-name repetition, Latin-script
duplicates only in `en`. The bundles below are starter seeds —
analyst should run `scripts/extract_fn_anchor_via_deepseek.py`
against the Render corpus before going live, exactly as
iran_theater / israel_theater / syria_theater were built. Target
languages: EN, DE, ES, IT, FR, RU, HI, ZH, AR, JA.

**Latin-collapse note**: tokens like `Houthi`, `Ansar Allah`, `Aden`,
`Sanaa`, `Bab al-Mandab`, `Red Sea`, `STC`, `Maersk`, `Tel Aviv`,
`Ben Gurion`, `Eilat`, `Aspides`, `Yanbu`, `Galaxy Leader`, `UNCLOS`,
`UKMTO`, `Marib`, `Taiz`, `Saada`, `Shabwa`, `Hadhramaut` spell
identically across EN / ES / IT / FR (often DE too) — per spec they
appear ONLY in `en`. Per-language lists below carry strictly the
tokens that change spelling.

```text
yemen_red_sea_theater
  (Pillar 1: own-side actors — the Houthi movement + Yemeni state
   organs. Pillar 2: Yemen sub-geography. Pillar 3: relevant
   systems. Pillar 4: kept thin; atomic FNs carry domain actions.)

  en: Houthi, Houthis, Ansar Allah, Sanaa, Aden, Hodeidah, Hodeida,
      Hudaydah, Bab al-Mandab, Bab el-Mandeb, Red Sea, Gulf of Aden,
      Socotra, Presidential Leadership Council, PLC, Saudi-led
      coalition, Coalition to Restore Legitimacy, STC, Southern
      Transitional Council, al-Houthi, Abdul Malik al-Houthi,
      al-Mashat
  de: Huthi, Huthis, Rotes Meer, Golf von Aden, Sokotra,
      Praesidialer Fuehrungsrat, saudisch gefuehrte Koalition,
      arabische Koalition, Suedlicher Uebergangsrat
  es: hutíes, hutí, Ansar Alá, Saná, Adén, Mar Rojo, golfo de Adén,
      Sócotra, Consejo de Liderazgo Presidencial, coalición árabe,
      Consejo de Transición del Sur
  fr: mer Rouge, golfe d'Aden, Conseil de direction présidentiel,
      coalition arabe, Conseil de transition du Sud
  it: Mar Rosso, golfo di Aden, Consiglio di guida presidenziale,
      coalizione araba, Consiglio di transizione del Sud
  ar: الحوثيون, الحوثي, أنصار الله, صنعاء, عدن, الحديدة,
      باب المندب, البحر الأحمر, خليج عدن, سقطرى,
      مجلس القيادة الرئاسي, التحالف بقيادة السعودية, التحالف العربي,
      المجلس الانتقالي الجنوبي, عبد الملك الحوثي, مهدي المشاط
  ru: хуситы, Ансар Аллах, Сана, Аден, Ходейда, Баб-эль-Мандеб,
      Красное море, Аденский залив, Сокотра, Президентский совет,
      аравийская коалиция, Южный переходный совет,
      Абдул-Малик аль-Хуси
  hi: हूती, अंसार अल्लाह, सना, अदन, होदेइदा, बाब अल-मंदब,
      लाल सागर, अदन की खाड़ी, राष्ट्रपति नेतृत्व परिषद,
      सऊदी नेतृत्व वाला गठबंधन, दक्षिणी संक्रमणकालीन परिषद
  zh: 胡塞, 胡塞武装, 安萨尔安拉, 萨那, 亚丁, 荷台达, 曼德海峡,
      红海, 亚丁湾, 索科特拉, 总统领导委员会, 沙特领导的联军,
      南方过渡委员会, 阿卜杜勒-马利克·胡塞
  ja: フーシ, フーシ派, アンサール・アッラー, サヌア, アデン,
      ホデイダ, バブ・エル・マンデブ, 紅海, アデン湾, ソコトラ,
      大統領指導評議会, サウジアラビア主導の連合, 南部暫定評議会
```

```text
red_sea_shipping_security
  (Pillar 1 thin — Houthi/Sanaa stay on parent. Pillar 2: maritime
   sub-geography. Pillar 3: named operations + shipping
   organisations. Pillar 4: maritime actions.)

  en: Bab al-Mandab, Bab el-Mandeb, Red Sea, Gulf of Aden, Suez,
      Suez Canal, Yanbu, Operation Prosperity Guardian, Aspides,
      Combined Maritime Forces, CMF, Fifth Fleet, USS Eisenhower,
      USS Truman, UKMTO, Galaxy Leader, Maersk, MSC, container
      ship, tanker, vessel, cargo ship, merchant ship,
      anti-ship missile, anti-ship ballistic, UNCLOS, freedom of
      navigation, rerouting, Cape of Good Hope
  de: Rotes Meer, Golf von Aden, Sues, Sueskanal, Fuenfte Flotte,
      Containerschiff, Frachtschiff, Handelsschiff,
      Antischiffsrakete, ballistische Antischiffsrakete,
      freie Seefahrt, Umleitung, Kap der Guten Hoffnung
  es: Mar Rojo, golfo de Adén, canal de Suez, Quinta Flota,
      portacontenedores, petrolero, carguero, buque mercante,
      misil antibuque, libertad de navegación, desvío,
      Cabo de Buena Esperanza
  fr: mer Rouge, golfe d'Aden, canal de Suez, Cinquième Flotte,
      porte-conteneurs, pétrolier, cargo, navire marchand,
      missile antinavire, liberté de navigation, déroutement,
      cap de Bonne-Espérance
  it: Mar Rosso, golfo di Aden, canale di Suez, Quinta Flotta,
      portacontainer, petroliera, mercantile, nave commerciale,
      missile antinave, libertà di navigazione, deviazione,
      Capo di Buona Speranza
  ar: باب المندب, البحر الأحمر, خليج عدن, السويس, قناة السويس,
      ينبع, عملية حارس الازدهار, عملية أسبيدس, الأسطول الخامس,
      ماسك, مايرسك, ناقلة, سفينة شحن, سفينة تجارية,
      صاروخ مضاد للسفن, حرية الملاحة, إعادة التوجيه,
      رأس الرجاء الصالح
  ru: Баб-эль-Мандеб, Красное море, Аденский залив, Суэц,
      Суэцкий канал, Янбу, операция Страж процветания,
      операция Аспидес, Пятый флот, контейнеровоз, танкер,
      грузовое судно, торговое судно, противокорабельная ракета,
      свобода судоходства, переадресация, мыс Доброй Надежды
  hi: बाब अल-मंदब, लाल सागर, अदन की खाड़ी, स्वेज नहर, यनबू,
      प्रॉस्पेरिटी गार्डियन, पाँचवाँ बेड़ा, कंटेनर जहाज,
      टैंकर, मालवाहक, व्यापारी जहाज, जहाज-रोधी मिसाइल,
      नौवहन की स्वतंत्रता, मार्ग परिवर्तन, उत्तमाशा अंतरीप
  zh: 曼德海峡, 红海, 亚丁湾, 苏伊士运河, 延布,
      繁荣卫士行动, 阿斯皮迪斯行动, 第五舰队, 银河领袖号, 马士基,
      集装箱船, 油轮, 货船, 商船, 反舰导弹, 反舰弹道导弹,
      航行自由, 改道, 好望角
  ja: バブ・エル・マンデブ, 紅海, アデン湾, スエズ運河, ヤンブー,
      繁栄の守護者作戦, アスピデス作戦, 第五艦隊,
      ギャラクシー・リーダー, マースク, コンテナ船, タンカー,
      貨物船, 商船, 対艦ミサイル, 対艦弾道ミサイル,
      航行の自由, 迂回, 喜望峰
```

```text
houthi_strikes_on_israel
  (Pillar 1 thin — Houthi command on parent. Pillar 2: Yemen launch
   geography + Israeli target geography. Pillar 3: Houthi missile /
   drone systems specific to this front. Pillar 4: strike-on-Israel
   actions.)

  en: Tel Aviv, Ben Gurion, Eilat, Ramon airport, Palestine-2,
      Toofan, Burkan, Quds-1, Quds-2, Quds-3, Hatem, joint
      operation, fourth front, fourth arena, support front,
      Yemen front, ballistic missile from Yemen, drone from Yemen,
      Yemeni missile
  de: Flughafen Ramon, Drohne aus Jemen, jemenitische Rakete,
      gemeinsame Operation, vierte Front, Unterstuetzungsfront,
      Jemen-Front
  es: aeropuerto Ramón, misil balístico yemení, dron desde Yemen,
      operación conjunta, cuarto frente, frente yemení
  fr: Tel-Aviv, Ben Gourion, aéroport Ramon, missile balistique
      yéménite, drone depuis le Yémen, opération conjointe,
      quatrième front, front yéménite
  it: aeroporto Ramon, missile balistico yemenita, drone dallo
      Yemen, operazione congiunta, quarto fronte, fronte yemenita
  ar: تل أبيب, بن غوريون, إيلات, مطار رامون,
      صاروخ باليستي يمني, صاروخ فلسطين, طوفان, بركان, قدس, حاتم,
      طائرة مسيرة من اليمن, عملية مشتركة, الجبهة الرابعة,
      جبهة المساندة, الجبهة اليمنية
  ru: Тель-Авив, Бен-Гурион, Эйлат, аэропорт Рамон,
      баллистическая ракета Йемен, Туфан, Буркан, ракета Кудс,
      беспилотник из Йемена, йеменская ракета, совместная операция,
      четвертый фронт, йеменский фронт
  hi: तेल अवीव, बेन गुरियन, इलात, रामोन हवाई अड्डा,
      यमनी बैलिस्टिक मिसाइल, यमन से ड्रोन, संयुक्त ऑपरेशन,
      चौथा मोर्चा, यमनी मोर्चा
  zh: 特拉维夫, 本古里安, 埃拉特, 拉蒙机场, 也门弹道导弹, 飓风,
      火山导弹, 圣城导弹, 也门无人机, 联合行动, 第四战线,
      也门支援前线, 也门前线
  ja: テルアビブ, ベングリオン, エイラート, ラモン空港,
      イエメン弾道ミサイル, ブルカン, クッズ・ミサイル,
      イエメンからのドローン, 共同作戦, 第四戦線, イエメン戦線
```

```text
saudi_houthi_war
  (Pillar 1: STC + coalition + Aden government actors. Pillar 2:
   southern Yemen sub-geography. Pillar 3: Riyadh / Stockholm /
   Hodeidah agreements. Pillar 4: intra-Yemen war actions. Houthi
   / Sanaa stay on parent.)

  en: STC, Southern Transitional Council, Mukalla, Marib, Taiz,
      Saada, Hadhramaut, Hadramaut, Shabwa, Giants Brigades,
      Joint Forces, Tareq Saleh, al-Zubaidi, al-Alimi,
      Presidential Leadership Council, PLC, Riyadh Agreement,
      Stockholm Agreement, Hodeidah Agreement, southern Yemen,
      reconstruction, separatist, separatists, dissolves STC,
      STC dissolution, coalition strikes
  de: Suedlicher Uebergangsrat, Gemeinsame Kraefte,
      Praesidialer Fuehrungsrat, Riad-Abkommen, Stockholm-Abkommen,
      Hodeida-Abkommen, Suedjemen, Wiederaufbau,
      STC-Aufloesung, Separatisten, Koalitionsschlaege
  es: Consejo de Transición del Sur, Brigadas de los Gigantes,
      Fuerzas Conjuntas, Consejo de Liderazgo Presidencial,
      Acuerdo de Riad, Acuerdo de Estocolmo, Acuerdo de Hodeida,
      sur de Yemen, reconstrucción, disolución del STC,
      separatistas, ataques de la coalición
  fr: Conseil de transition du Sud, Brigades des Géants,
      Forces conjointes, Conseil de direction présidentiel,
      accord de Riyad, accord de Stockholm, accord de Hodeïda,
      sud du Yémen, reconstruction, dissolution du STC,
      séparatistes, frappes de la coalition
  it: Consiglio di transizione del Sud, Brigate dei Giganti,
      Forze Congiunte, Consiglio di guida presidenziale,
      Accordo di Riad, Accordo di Stoccolma, Accordo di Hodeida,
      Yemen meridionale, ricostruzione, dissoluzione dell'STC,
      separatisti, attacchi della coalizione
  ar: المجلس الانتقالي الجنوبي, المكلا, مأرب, تعز, صعدة,
      حضرموت, شبوة, ألوية العمالقة, القوات المشتركة, طارق صالح,
      عيدروس الزبيدي, الزبيدي, رشاد العليمي, العليمي,
      مجلس القيادة الرئاسي, اتفاق الرياض, اتفاق ستوكهولم,
      اتفاق الحديدة, جنوب اليمن, إعمار, حل المجلس الانتقالي,
      الانفصاليون, ضربات التحالف
  ru: ЮПС, Южный переходный совет, Мукалла, Мариб, Таиз, Саада,
      Хадрамаут, Шабва, бригады Гигантов, Объединенные силы,
      Тарик Салех, аль-Зубейди, аль-Алими,
      Президентский совет, Эр-Риядское соглашение,
      Стокгольмское соглашение, соглашение по Ходейде, южный Йемен,
      восстановление, роспуск ЮПС, сепаратисты, удары коалиции
  hi: एसटीसी, दक्षिणी संक्रमणकालीन परिषद, मुकल्ला, मारिब,
      ताइज़, सादा, हदरामौत, शबवा, जायंट्स ब्रिगेड,
      संयुक्त बल, राष्ट्रपति नेतृत्व परिषद, रियाद समझौता,
      स्टॉकहोम समझौता, होदेइदा समझौता, दक्षिणी यमन,
      पुनर्निर्माण, एसटीसी विघटन, अलगाववादी, गठबंधन के हमले
  zh: 南方过渡委员会, 穆卡拉, 马里卜, 塔伊兹, 萨达, 哈德拉毛,
      舍卜瓦, 巨人旅, 联合部队, 总统领导委员会, 利雅得协议,
      斯德哥尔摩协议, 荷台达协议, 南也门, 重建,
      南方过渡委员会解散, 分裂分子, 联军袭击
  ja: 南部暫定評議会, ムカッラ, マアリブ, タイズ, サアダ,
      ハドラマウト, シャブワ, ジャイアンツ旅団, 統合軍,
      大統領指導評議会, リヤド合意, ストックホルム合意,
      ホデイダ合意, 南イエメン, 再建, STC解散, 分離主義者,
      連合軍の攻撃
```

## Open questions before SQL

1. **Houthi-Israel front vs. iran_proxy_network overlap.** Verified
   that `iran_proxy_network.centroid_ids = ['MIDEAST-IRAN']`, so a
   Yemen-centroid-only title cannot double-attribute. Titles tagged
   `[MIDEAST-YEMEN, MIDEAST-IRAN]` (31 in 180d) may dual-attribute if
   they match both anchor bundles AND both publisher cohorts — under
   1-to-1 they will attach to whichever narrative's full conjunction
   fires. Acceptable.

2. **STC as standalone FN?** The southern STC self-dissolution arc is
   real but tightly entangled with Saudi-coalition framing — most
   Al-Ahram and Al Arabiya coverage treats it as a subplot of the
   Saudi-led intervention rather than a standalone surface. Keep
   bundled inside `saudi_houthi_war` for v1. If 2026 evolution
   produces a sustained Saudi-UAE rift cohort, promote later.

3. **Humanitarian / WFP collapse — no atomic FN.** Corpus surfaces
   only 2-3 humanitarian-focused events (WFP suspension, UN 2026
   crisis warning). Too thin for its own FN; held on theater
   editorial summary and inside `western_pragmatic_navigation` as a
   parallel concern. Revisit when corpus depth justifies it.

4. **Stance anchor — Houthis or coalition?** Spec anchors stance to
   the **Houthi / Ansar Allah authority in Sanaa** because the
   Houthis are the *active* actor across all three atomic FNs (they
   strike Israel, they target shipping, they hold Sanaa against the
   coalition). Saudi-coalition legitimacy framing therefore registers
   as -2 under "stance toward Houthis". This mirrors `iran_theater`
   (stance toward Iran) more than `israel_theater` (stance toward
   Israel). Confirm the convention is acceptable here — the
   alternative would be stance toward the PLC government in Aden,
   which would flip every sign and read less naturally given who
   drives the news.

5. **`AFRICA-HORN` centroid inclusion** for `red_sea_shipping_security`
   and `yemen_red_sea_theater`. The Somaliland-base and Eritrea-coast
   subplot does surface (the IDF / Somaliland deal reported by
   Jerusalem Post), but volume is thin. Including AFRICA-HORN widens
   scope slightly without over-promising — those titles will
   attribute only if they also match Yemen anchor vocabulary. Open
   for review.

## Build order (suggested)

1. **Review this spec.** Adjust atomic FN decomposition + narrative
   roster if needed (especially Open Q4 stance anchor).
2. **Anchor extraction.** Run
   `scripts/extract_fn_anchor_via_deepseek.py` for each of the 4
   fn_anchor bundles against the Render corpus. Hand-edit per
   `FN_ANCHOR_VOCABULARY_SPEC.md` pre-commit checklist.
3. **Publisher cohort calibration.** Run
   `scripts/calibrate_narrative_keywords.py` per narrative against
   the Render corpus to surface vocabulary the analyst draft missed.
4. **Write migration**:
   `db/migrations/20260514_friction_node_yemen_red_sea_theater_seed.sql`
   mirroring `20260512_israel_theater_seed.sql` (theater + 3 atomic
   FNs + 4 fn_anchor bundles + 9 narratives + sanity check DO
   block). Apply locally first.
5. **Bootstrap locally**:
   `python scripts/bootstrap_friction_node.py --fn-id <each id>`.
   Inspect per-narrative match counts. Goal: each pro/con narrative
   ≥80 titles, ≥30 events. Yemen corpus is thinner than Levant —
   if a narrative attributes <50 titles, widen anchor or publisher
   set per the runbook's "Common diagnosis" SQL.
6. **Sanity-check pages**: `/en/friction-nodes/yemen_red_sea_theater`
   plus each atomic FN. Check brick hues, sample headlines on-frame,
   country pills, activity charts credible.
7. **Push to Render**: apply migration on Render, run bootstrap on
   Render, bust frontend cache. Same protocol as israel_theater /
   syria_theater deploys.

## Expected DecisionLog entry

```yaml
- id: D-08x
  date: 2026-05-13
  type: data-model
  status: accepted
  title: Seed Yemen / Red Sea theater — 3 atomic FNs + 9 narratives
  rationale:
    - MIDEAST-YEMEN centroid holds 571 titles / 165 promoted events (180d) with no FN attribution
    - Narrative contests visible in publisher data: Houthi strikes on Israel (top event 26 srcs),
      Red Sea shipping security, Saudi-Houthi war + southern STC arc
    - iran_proxy_network (centroid MIDEAST-IRAN only) does not absorb Yemen-centroid titles;
      this theater is the right home
  scope:
    - friction_nodes: yemen_red_sea_theater (theater), red_sea_shipping_security,
      houthi_strikes_on_israel, saudi_houthi_war
    - narratives_v2: 9 narratives (3 theater + 2 per atomic FN)
    - taxonomy_v3: 4 fn_anchor bundles
  consequences:
    - Yemen coverage moves from unattributed to a contested theater surface
    - Establishes the third theater (after Israel, Syria) and completes the southern
      Red Sea / Iran-axis triangle alongside iran_theater
```

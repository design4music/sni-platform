# Syria Theater — Build Spec

**Date drafted**: 2026-05-13
**Status**: Draft for review. No DB writes yet.
**Pattern**: Follows `iran_theater` / `israel_theater` (D-075..D-079, 2026-05-12).

## Why now

Levant centroid carries ~5,000 titles over the past 180 days. The
`israel_lebanon_border` FN claims ~1,300 of these. The remaining
~3,700 Levant titles are dominated by post-Assad Syria — a strategic
surface no current FN covers. The narrative contests inside it are
sharp and publisher-aligned in a way that maps cleanly onto the FN
architecture.

Top entities in Syria-marked Levant titles (180d):

- Places: Syria (127), Aleppo (102), Damascus (42), Hasakah (15),
  Raqqa (13)
- Orgs: SDF (150), YPG (57), ISIS (49), Islamic_State (19), PKK (15),
  Hezbollah (16)
- Persons: TRUMP (21), PUTIN (16), ERDOGAN (15), ASSAD (13),
  al-SHARAA (12+12)

Top promoted Syria events (by source count, 180d):

- 38 srcs — "Syrian government and Kurdish-led forces agree to
  immediate ceasefire"
- 30 srcs — "Syrian government and Kurdish-led forces agree to a
  four-day ceasefire"
- 25 srcs — "Israel intensifies strikes in Lebanon and Syria,
  targeting Hezbollah and Syrian army"
- 23 srcs — "Syrian army advances into Kurdish-held areas"
- 22 srcs — "US military begins moving ISIS detainees from Syria to
  Iraq"
- 19 srcs — "US launches large-scale retaliatory strikes against
  Islamic State in Syria"
- 16 srcs — "Zelensky visits Syria for first time to discuss
  security"
- 9 srcs — "Saudi Arabia signs major investment deals with Syria"

## Theater shape

```
syria_theater (catch-all, fn_type='theater')
   |
   +-- syria_kurdish_question     SDF / YPG vs Damascus vs Turkey-PKK frame
   +-- syria_israeli_strikes      Israeli strikes on Syrian govt + Hezbollah residue
   +-- syria_counter_terror       US-led ISIS strikes, detainee transfers, AQ leaders
   +-- syria_recognition_and_normalisation   Arab + Western + Russia/Ukraine handshakes with al-Sharaa
```

Four atomic FNs were chosen because they correspond to the four
distinct publisher cohorts visible in the data (Turkish state /
pan-Arab / Israeli / Western counter-terror desk) and each has its
own pro/con narrative axis. The catch-all theater carries the
governance-legitimacy narratives that don't sit cleanly inside any
single atomic FN.

## FN definitions

### `syria_theater` (theater, catch-all)

- **Name (EN)**: Syria in post-Assad transition
- **Name (DE)**: Syrien im Uebergang nach Assad
- **fn_type**: `theater`
- **member_fn_ids**: `[syria_kurdish_question, syria_israeli_strikes,
  syria_counter_terror, syria_recognition_and_normalisation]`
- **centroid_ids**: `[MIDEAST-LEVANT, MIDEAST-TURKEY, MIDEAST-IRAN,
  MIDEAST-ISRAEL, MIDEAST-GULF, MIDEAST-SAUDI, MIDEAST-IRAQ,
  AMERICAS-USA, EUROPE-RUSSIA]`
- **What it carries**: governance-legitimacy debate around the
  HTS-led government under al-Sharaa, broad framings that span all
  atomic FNs, Russian base future at Tartus/Khmeimim, refugee return
  question, reconstruction money.

### `syria_kurdish_question` (atomic)

- **Name (EN)**: Kurdish self-administration in northeastern Syria
- **Name (DE)**: Kurdische Selbstverwaltung in Nordostsyrien
- **centroid_ids**: `[MIDEAST-LEVANT, MIDEAST-TURKEY, MIDEAST-IRAQ,
  AMERICAS-USA]`
- **What it covers**: SDF / YPG control of NE Syria, Damascus
  attempts to reunify, Aleppo offensive and ceasefires, Hasakah/
  Raqqa governance, Turkey's anti-PKK framing of SDF, the US's
  partnership with SDF in counter-ISIS operations.

### `syria_israeli_strikes` (atomic)

- **Name (EN)**: Israeli strikes on Syrian targets
- **Name (DE)**: Israelische Schlaege gegen syrische Ziele
- **centroid_ids**: `[MIDEAST-LEVANT, MIDEAST-ISRAEL, MIDEAST-IRAN]`
- **What it covers**: Israeli strikes inside Syria on Hezbollah
  logistics, residual IRGC positions, and increasingly Syrian army
  assets after the Assad fall. Distinct from `israel_iran_strikes`
  (direct Israel-Iran exchange) and `israel_lebanon_border`
  (cross-Litani conflict). The buffer-zone question south of
  Damascus.

### `syria_counter_terror` (atomic)

- **Name (EN)**: Counter-ISIS operations and residual terrorism
- **Name (DE)**: Anti-IS-Operationen und verbliebener Terrorismus
- **centroid_ids**: `[MIDEAST-LEVANT, MIDEAST-IRAQ, AMERICAS-USA,
  EUROPE-UK, EUROPE-FRANCE]`
- **What it covers**: US-led coalition strikes on ISIS in Syria, UK/
  French/Italian troop presence at Erbil (cross-listed with Iraq
  CTM events), detainee transfers from SDF custody to Iraq,
  prison-break events, al-Qaeda leadership strikes.

### `syria_recognition_and_normalisation` (atomic)

- **Name (EN)**: International recognition and normalisation with
  the new Syrian government
- **Name (DE)**: Internationale Anerkennung und Normalisierung mit
  der neuen syrischen Regierung
- **centroid_ids**: `[MIDEAST-LEVANT, MIDEAST-SAUDI, MIDEAST-GULF,
  MIDEAST-EGYPT, MIDEAST-TURKEY, AMERICAS-USA, EUROPE-UK,
  EUROPE-GERMANY, EUROPE-FRANCE, EUROPE-RUSSIA, EUROPE-UKRAINE,
  NON-STATE-EU]`
- **What it covers**: every flavour of handshake with al-Sharaa.
  Arab side: Saudi investment, Gulf recognition trajectories, Arab
  League re-engagement, Egypt-Turkey rapprochement. Western side:
  US sanctions easing, EU/E3 calibrated engagement, Charles III /
  Merz / Macron meetings. Russia/Ukraine side: Putin holding on to
  Tartus/Khmeimim through negotiation, Zelensky's Damascus visit
  for security talks. The shared substance is the *act of engaging*
  — the contest is whether engagement stabilises Syria or
  legitimises a former al-Qaeda operative.

## Narrative slots (proposed, 11 total)

Stance is **toward the new Syrian (HTS-led) government** as the
theater's primary actor, following the iran_theater / israel_theater
convention.

### Theater-level (3 narratives)

| id | stance | name | one-line frame |
|---|---:|---|---|
| `syria_legitimate_transition` | +2 | Legitimate Syrian transition | New Syrian government under al-Sharaa is a legitimate post-Assad transition; international community should engage and lift sanctions. |
| `syria_jihadist_takeover_warning` | -2 | Jihadist takeover warning | HTS is rebranded al-Qaeda; the new government is unstable, sectarian against Alawites/Christians/Druze, and a long-term security threat. |
| `russia_iran_loss_lament` | -1 | Multipolar lament: Russia-Iran lose Syria | Russia and Iran frame the fall of Assad and Western/Turkish backing of the new government as a setback for the multipolar order. |

Publisher cohorts:
- `syria_legitimate_transition`: Anadolu, Daily Sabah, TRT World, Al
  Jazeera, Arab News, The National, Khaleej Times, Reuters (mixed)
- `syria_jihadist_takeover_warning`: Jerusalem Post, Times of
  Israel, i24NEWS, Arutz Sheva, Fox News, Press TV (oddly aligned),
  Fars News, IRNA
- `russia_iran_loss_lament`: RT, TASS (EN), Press TV, Fars News,
  IRNA, Al Mayadeen

### `syria_kurdish_question` (2 narratives)

| id | stance | name | frame |
|---|---:|---|---|
| `kurdish_self_administration` | -1 | Kurdish self-administration is legitimate | SDF-led Autonomous Administration of North and East Syria represents a multi-ethnic democratic experiment; partner against ISIS; should be protected from Turkish and Damascus pressure. |
| `damascus_territorial_reunification` | +2 | Reunify Syrian territory | The new Syrian government must restore central authority over all Syrian territory including the northeast; SDF is a separatist project backed by external powers. |

(Note: stance is toward the new Damascus government. Kurdish-self-
admin framing reads as -1 here even though it might read as +1 in a
hypothetical future kurdish theater.)

Publishers (Kurdish): Al Jazeera, France 24 (EN), BBC World, Deutsche
Welle, Reuters, Wall Street Journal, Haaretz
Publishers (Damascus reunification): Anadolu, Daily Sabah, TRT World,
SANA, Al-Ahram

### `syria_israeli_strikes` (2 narratives)

| id | stance | name | frame |
|---|---:|---|---|
| `israeli_strikes_on_syria_legitimate` | -1 | Israeli strikes on Syria are legitimate self-defense | Israel must continue striking residual Hezbollah logistics, Iranian assets, and Syrian army positions threatening the Golan / northern border. |
| `syrian_sovereignty_under_israeli_aggression` | +2 | Defend Syrian sovereignty against Israeli aggression | Israeli strikes on Syrian government targets violate Syrian sovereignty and undermine the transition; the buffer zone south of Damascus is illegal occupation. |

Publishers (Israeli strikes legitimate): Jerusalem Post, Times of
Israel, i24NEWS, Israel Hayom, Fox News
Publishers (Syrian sovereignty): SANA, Al Jazeera, Anadolu, Press TV
(post-Assad now defends Damascus against Israel), Al Mayadeen

### `syria_counter_terror` (2 narratives)

| id | stance | name | frame |
|---|---:|---|---|
| `coalition_counter_isis_necessary` | 0 | Coalition counter-ISIS presence is necessary | US, UK, French and Italian forces operating against ISIS residue in Syria and Iraq are necessary; SDF custody of ~10,000 ISIS detainees and the prison-break risk requires sustained Western engagement. |
| `foreign_military_withdrawal_demand` | +1 | Foreign forces should leave Syria | Western military presence violates Syrian sovereignty; counter-ISIS operations should transfer to the new Syrian government and Iraq; detainees should be transferred to national jurisdictions. |

Publishers (coalition necessary): Reuters, AP, BBC World, France 24,
Jerusalem Post, Fox News
Publishers (withdrawal): Anadolu, TRT World, Press TV, TASS (EN), RT,
SANA

### `syria_recognition_and_normalisation` (2 narratives)

| id | stance | name | frame |
|---|---:|---|---|
| `international_engagement_pragmatic` | +2 | International engagement is pragmatic and stabilising | Arab investment, Western sanctions easing, and Russia/Ukraine security talks all serve the same goal: pull Syria out of the Iranian orbit, fund reconstruction, and stabilise the Levant. Realism over purity tests. |
| `recognition_legitimises_jihadists` | -2 | Recognition legitimises a jihadist government | Every handshake — Saudi investment, Charles III meeting al-Sharaa, Merz / Macron diplomacy, Putin's base-preservation deal, Zelensky's Damascus trip — whitewashes a former al-Qaeda operative and rewards extremism. The image of world leaders shaking the hand of a designated terrorist is itself the harm. |

Publishers (pragmatic engagement): Arab News, The National, Khaleej
Times, Gulf News, Al-Ahram, Anadolu, Daily Sabah, Reuters, BBC
World, Financial Times, Le Monde, Tagesschau, Deutsche Welle,
TASS (EN), Ukrinform
Publishers (legitimisation critique): Jerusalem Post, Times of
Israel, i24NEWS, Israel Hayom, Arutz Sheva, Fox News, Press TV,
Fars News, IRNA, Al Mayadeen, plus Western conservative voices
(Telegraph, Spectator, Daily Mail) when they appear in corpus

## fn_anchor vocabulary (first-pass; expand via deepseek extractor)

**Rules**: every bundle below follows
[`FN_ANCHOR_VOCABULARY_SPEC.md`](FN_ANCHOR_VOCABULARY_SPEC.md) —
4 pillars (own-side actors, sub-centroid geography, relevant systems,
domain actions), shortest unique form, atoms not phrases, no
third-party leaders, no country-name repetition, Latin-script
duplicates only in `en`. The bundles below are starter seeds —
analyst should run `scripts/extract_fn_anchor_via_deepseek.py`
against the Render corpus before going live, exactly as iran_theater
and israel_theater were built. Target languages: EN, DE, ES, IT, FR,
RU, HI, ZH, AR, JA.

```text
syria_theater
  en: Syria, Syrian, Damascus, al-Sharaa, Sharaa, Jolani, HTS,
      transitional government, post-Assad, Bashar al-Assad, SANA,
      Tartus, Khmeimim
  ar: سوريا, سورية, دمشق, الشرع, الجولاني, هيئة تحرير الشام,
      حكومة سوريا الجديدة, الأسد, سانا
  de: Syrien, syrisch, Damaskus, al-Sharaa, Dschulani, HTS,
      Uebergangsregierung, post-Assad
  ru: Сирия, Дамаск, аш-Шараа, аль-Джулани, ХТШ, постасадовский,
      Башар Асад, Тартус, Хмеймим
  tr: Suriye, Şam, eş-Şara, Cülani, HTŞ, Esad sonrası

syria_kurdish_question
  en: SDF, YPG, PKK, Rojava, AANES, Autonomous Administration,
      Kurdish-led forces, Hasakah, Hasaka, Qamishli, Raqqa,
      Aleppo Kurds, Sheikh Maqsoud, Mazloum, Abdi
  ar: قسد, الإدارة الذاتية, الأكراد, روج آفا, شمال شرق سوريا,
      الحسكة, القامشلي, الرقة
  de: SDF, YPG, PKK, Rojava, Selbstverwaltung Nordostsyrien,
      Kurdische Streitkraefte, Hasaka, Kamischli, Rakka
  tr: YPG, PKK, ÖSO, kuzey Suriye, Hasekê, Kobanê, Münbiç
  ru: СДС, YPG, РПК, Рожава, курдские силы, Хасеке, Камышлы, Ракка

syria_israeli_strikes
  en: Israeli strikes Syria, Israel Syria, strikes near Damascus,
      buffer zone Syria, Golan buffer, IDF Syria, Israeli airstrike
      Damascus, T-4 base
  ar: غارات إسرائيلية على سوريا, الجولان, المنطقة العازلة,
      ضربات إسرائيلية في دمشق, قاعدة تي-4
  de: israelische Angriffe auf Syrien, Pufferzone Syrien, Golan-
      Pufferzone, IDF Syrien
  ru: израильские удары по Сирии, буферная зона Сирия, Голаны

syria_counter_terror
  en: ISIS Syria, Islamic State Syria, ISIS detainees, al-Hol,
      al-Roj, ISIS prison, al-Qaeda Syria, Hurras al-Din,
      coalition strikes, Operation Inherent Resolve, US troops Syria
  ar: داعش في سوريا, تنظيم الدولة, معتقلو داعش, الهول, الروج,
      القاعدة في سوريا, التحالف الدولي
  de: IS Syrien, Islamischer Staat Syrien, IS-Haeftlinge, al-Hol,
      al-Qaida Syrien, Koalitionsschlaege
  ru: ИГИЛ Сирия, ИГ Сирия, заключенные ИГИЛ, аль-Холь, аль-Каида
      Сирия, удары коалиции

syria_recognition_and_normalisation
  Pattern follows existing FNs: (a) core actors of the new Syrian
  government, (b) diplomacy / recognition concept vocab, (c)
  Damascus-anchored engagement phrases. NO third-party leader
  names — centroid_ids already enforces the geographic gate, and
  the FN must stay open to future visitors. If a head of state
  meets al-Sharaa next month, "Damascus summit" / "Damascus visit"
  / "met al-Sharaa" catches it without enumerating who.

  en: al-Sharaa, Sharaa, Ahmad al-Sharaa, Ahmed al-Sharaa,
      al-Jolani, Jolani, al-Jawlani, Abu Mohammad al-Jolani,
      HTS, Hayat Tahrir al-Sham, Syrian transitional government,
      Syrian interim government, transitional authorities,
      new Syrian government, transitional Syria, post-Assad Syria,
      normalisation with Syria, normalization with Syria,
      recognise Syria, recognize Syria, Syria recognition,
      lift sanctions on Syria, ease sanctions on Syria,
      sanctions relief Syria, delisting HTS, remove from terror
      list, terrorist designation Syria, Arab League, Arab League
      Syria, GCC, Gulf Cooperation Council, reconstruction Syria,
      Syria reconstruction, investment deal Syria, Syria
      investment, met al-Sharaa, meeting with al-Sharaa,
      met Sharaa, Damascus visit, visit to Damascus, Damascus
      summit, Damascus talks, talks with Damascus, deal with
      Damascus, agreement with Damascus, delegation to Damascus,
      embassy reopened, reopens embassy in Damascus, ambassador
      to Syria, ambassador to Damascus, normalising ties with
      Syria, restoring relations with Syria
  ar: الشرع, أحمد الشرع, الجولاني, أبو محمد الجولاني,
      هيئة تحرير الشام, الحكومة السورية الانتقالية, الحكومة
      السورية الجديدة, السلطات الانتقالية, التطبيع مع سوريا,
      الاعتراف بسوريا, رفع العقوبات عن سوريا, تخفيف العقوبات
      السورية, شطب هيئة تحرير الشام, الجامعة العربية, إعادة
      إعمار سوريا, الاستثمار في سوريا, زيارة دمشق, لقاء مع
      الشرع, محادثات دمشق, اتفاق مع دمشق, إعادة فتح السفارة
      في دمشق, سفير لدى سوريا
  de: al-Sharaa, al-Scharaa, al-Dscholani, al-Jolani,
      Hayat Tahrir al-Sham, HTS, syrische Uebergangsregierung,
      neue syrische Regierung, Uebergangsbehoerden,
      Normalisierung mit Syrien, Anerkennung Syrien, Aufhebung
      Sanktionen Syrien, Lockerung der Sanktionen Syrien,
      Streichung von HTS, Terrorlisten-Streichung, Arabische
      Liga, Wiederaufbau Syrien, Investitionen Syrien,
      Damaskus-Besuch, Besuch in Damaskus, Damaskus-Gipfel,
      Damaskus-Gespraeche, Treffen mit al-Sharaa, Abkommen mit
      Damaskus, Wiedereroeffnung Botschaft Damaskus, Botschafter
      in Damaskus
  ru: аш-Шараа, Ахмад аш-Шараа, аль-Джулани,
      Хайят Тахрир аш-Шам, ХТШ, переходное правительство Сирии,
      сирийские переходные власти, новая сирийская власть,
      нормализация с Сирией, признание Сирии, снятие санкций с
      Сирии, ослабление санкций Сирия, исключение ХТШ из списка
      террористов, Лига арабских государств, восстановление
      Сирии, инвестиции в Сирию, визит в Дамаск, встреча с
      аш-Шараа, переговоры в Дамаске, переговоры с Дамаском,
      соглашение с Дамаском, открытие посольства в Дамаске,
      посол в Дамаске
  tr: eş-Şara, Ahmed eş-Şara, Culani, Cülani,
      Heyet Tahrir eş-Şam, HTŞ, Suriye gecis hukumeti,
      Suriye gecis idaresi, yeni Suriye yonetimi, Suriye ile
      normallesme, Suriye tanima, Suriye yaptirimlari
      kaldirildi, Suriye yaptirimlari hafifletildi, HTŞ listeden
      cikarildi, Arap Birligi, Suriye yeniden yapilanma, Sam
      ziyareti, Sam zirvesi, Sam gorusmeleri, eş-Şara ile
      gorusme, Sam ile anlasma, Sam buyukelcisi
  ar (Syria-tagged news): سانا, SANA
  uk: визнання Сирії, нормалізація з Сирією, переговори в
      Дамаску, візит у Дамаск
```

## Open questions before SQL

1. **Israeli strikes on Syria vs israel_iran_strikes overlap**: An
   Israeli strike on an Iranian/Hezbollah target inside Syria
   matches both `syria_israeli_strikes` and existing
   `israel_iran_strikes`. Under 1-to-1, a title can attach to
   multiple narratives only if it's published by an outlet in both
   cohorts and matches both fn_anchor bundles. The natural split:
   `israel_iran_strikes` covers Iran-Israel direct exchange
   (Iranian soil, Iranian retaliation, Operation True Promise);
   `syria_israeli_strikes` covers strikes inside Syrian territory.
   Anchor vocabulary should reinforce this — `syria_israeli_strikes`
   bundle requires "Syria" / "Damascus" / "buffer zone" wording.

2. **Counter-terror cross-CTM scope**: French / Italian soldier
   events in Iraq's Kurdistan are technically about Iraq's coverage
   but read naturally as Syria-counter-ISIS content. Including
   MIDEAST-IRAQ in `syria_counter_terror.centroid_ids` is justified
   here (the Erbil base supports SDF logistics). This widens scope
   slightly beyond a pure Syria FN — acceptable trade.

3. **Kurdish question scope**: At spec time we keep this Syria-
   bounded. A future `turkey_kurdish_question` FN (cross-listed
   centroids TURKEY + LEVANT + IRAQ) could attach the Turkey-side
   PKK / HDP / Imrali narratives without overlap, since the
   publisher cohorts and framing are different. Park for Turkey
   theater build.

4. **Russia / Iran loss narrative — theater or no?**: Currently
   placed on theater. Alternative: a dedicated `syria_russia_iran_
   exit` atomic FN covering Tartus base future + IRGC presence
   collapse. Data volume probably too thin to justify a dedicated
   FN for the first build — keep on theater.

5. **Stance values**: theater carries a +2/-2/-1 trio rather than
   the +2/0/-2 spread used by iran_theater. This is consistent
   with israel_theater (which has -2..+2 trio across four
   narratives) and reflects that the Russia/Iran-axis framing here
   is mild-negative rather than full opposition. Open for review.

## Build order (suggested)

1. **Review this spec.** Adjust atomic FN decomposition + narrative
   roster if needed.
2. **Anchor extraction.** Run
   `scripts/extract_fn_anchor_via_deepseek.py` for each of the 5
   fn_anchor bundles against the Render corpus. Hand-edit the
   outputs.
3. **Publisher cohort calibration.** Run
   `scripts/calibrate_narrative_keywords.py` per narrative against
   the Render corpus to surface vocabulary the analyst draft
   missed.
4. **Write migration**:
   `db/migrations/20260513_friction_node_syria_theater_seed.sql`
   mirroring `20260512_israel_theater_seed.sql` (theater + 4 atomic
   FNs + 5 fn_anchor bundles + 11 narratives + sanity check DO
   block). Apply locally first.
5. **Bootstrap locally**:
   `python scripts/bootstrap_friction_node.py --fn-id <each id>`.
   Inspect per-narrative match counts. Goal: each pro/con narrative
   ≥80 titles, ≥30 events. If thinner, widen anchor or publisher
   set.
6. **Sanity-check pages**: `/en/friction-nodes/syria_theater` plus
   each atomic FN. Check brick hues, sample headlines on-frame,
   country pills, activity charts credible.
7. **Push to Render**: apply migration on Render, run bootstrap on
   Render, bust frontend cache. Same protocol as israel_theater
   deploy.

## Expected DecisionLog entry

```yaml
- id: D-08x
  date: 2026-05-13
  type: data-model
  status: accepted
  title: Seed Syria theater (post-Assad transition) — 4 atomic FNs + 11 narratives
  rationale:
    - Levant centroid holds ~3,700 unattributed titles dominated by post-Assad Syria
    - Narrative contests visible in publisher data: SDF/Kurdish question, Israeli strikes,
      counter-ISIS presence, Arab normalisation
  scope:
    - friction_nodes: syria_theater (theater), syria_kurdish_question, syria_israeli_strikes,
      syria_counter_terror, syria_recognition_and_normalisation
    - narratives_v2: 11 narratives (3 theater + 2 per atomic FN)
    - taxonomy_v3: 5 fn_anchor bundles
  consequences:
    - Syria coverage moves from unattributed to a contested theater surface
    - Establishes pattern for next theaters (Yemen / Red Sea, Turkey, Sudan)
```

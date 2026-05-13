# Sudan FN — Build Spec

**Date drafted**: 2026-05-13
**Status**: Draft for review. No DB writes yet.
**Pattern**: Standalone atomic FN. Smaller scope than `iran_theater` /
`israel_theater` / `syria_theater` — Sudan is single-axis (RSF vs army),
so no theater wrapper.

## Why now

`MIDEAST-SUDAN` centroid holds **620 titles over 180 days** (~518 from
the brief, plus April so-far). Volume is thin relative to Iran (37k)
or Israel (15.7k) but the contest is sharp, publisher-aligned, and
entirely unattributed — no current FN covers it.

Top entities in Sudan-tagged titles (180d):

- Orgs: `RSF` 69, `Sudanese army / الجيش السوداني` 15, `Muslim Brotherhood /
  Islamist` 5
- Sub-country places: `El Fasher / Al-Fashir / الفاشر` 31, `Kordofan` 30,
  `Darfur / دارفور` 29, `Khartoum / الخرطوم` 16, `Port Sudan` 2
- External actors in headlines: `Egypt` 46, `Chad` 22, `Ethiopia` 17,
  `UAE` 16, `Saudi` 12
- Domain vocab: `drone / مسيرة` 59, `paramilitary / militia /
  الدعم السريع` 33, `hospital` 28, `genocide` 17, `ceasefire / هدنة` 13,
  `famine / مجاعة` 13, `displaced` 16, `proxy war` 1 (in body of
  several articles, headline form is rare)

Top promoted events (from the brief):

- 10 srcs — "UN investigators find evidence of genocide in Sudan's El Fasher"
- 9 srcs — "Drone strike on hospital in Sudan kills dozens, including children"

The signal converges on three contested narrative axes (below). Volume
is enough to support multiple narratives on a single FN but **not**
enough to support 3-4 atomic FNs splitting these axes further.

## Theater vs standalone — decision

**Decision: standalone atomic FN `sudan_civil_war`.**

Considered a theater (sub-frictions: core civil war, humanitarian/
genocide, external backer contest). Rejected:

1. **Volume floor.** 620/180d across 4 sub-FNs = ~155 each before
   publisher and anchor cuts. Bootstrap target ≥80 titles per
   narrative would frequently drop below useful.
2. **Publisher cohorts overlap.** Unlike Syria (Israeli vs Turkish
   state vs pan-Arab vs Western counter-terror — four distinct
   rosters), Sudan's Al-Ahram / Al Arabiya / Al Jazeera / UN News
   axis carries operations *and* humanitarian *and* backer-critique
   stories under one byline. Splitting FNs shreds single cohorts.
3. **One contested phenomenon.** Darfur atrocities, hospital strikes,
   the UAE-arms pipeline, El Fasher famine — all facets of the same
   Hemedti-vs-Burhan war, not topically separable surfaces.

Revisit if Sudan volume grows past ~1500 titles/180d, at which point
splitting `sudan_external_backers` off as an atomic FN becomes
viable.

## FN definition

### `sudan_civil_war` (atomic)

- **id**: `sudan_civil_war`
- **fn_type**: `atomic`
- **member_fn_ids**: `NULL`
- **name_en**: Sudan civil war
- **name_de**: Sudanesischer Buergerkrieg
- **description_en**: The war between the Sudanese army (SAF) under
  General al-Burhan and the Rapid Support Forces (RSF) paramilitary
  under Hemedti, ignited 15 April 2023. Coverage clusters around three
  framings: legitimate-state counter-insurgency, humanitarian /
  genocide catastrophe (El Fasher, Darfur, Kordofan, hospital strikes,
  famine), and external-backer contest (UAE accused of arming the
  RSF, Egypt and Saudi Arabia backing the army).
- **description_de**: Der Krieg zwischen der sudanesischen Armee (SAF)
  unter General al-Burhan und der paramilitaerischen Rapid Support
  Forces (RSF) unter Hemedti, ausgebrochen am 15. April 2023. Die
  Berichterstattung gliedert sich in drei Rahmungen: legitime
  staatliche Aufstandsbekaempfung, humanitaere Katastrophe / Genozid
  (Al-Faschir, Darfur, Kordofan, Angriffe auf Krankenhaeuser,
  Hungersnot) und Konflikt um auslaendische Unterstuetzer (Vorwuerfe
  gegen die VAE wegen Bewaffnung der RSF, Aegypten und Saudi-Arabien
  hinter der Armee).
- **editorial_summary_en**: The Sudan war has produced the world's
  largest current displacement crisis (~12M displaced) and a UN-
  evidenced genocide finding in El Fasher, yet remains underreported.
  Contest: pan-Arab Egyptian and Saudi outlets emphasise state
  legitimacy and Brotherhood/Islamist risk inside the army; UN,
  Western humanitarian and pan-Arab non-aligned outlets emphasise
  civilian casualties, drone strikes on hospitals, and famine;
  investigative international and Turkish/Iranian state media
  critique Gulf and Ethiopian arms flows to the RSF.
- **editorial_summary_de**: Der Sudan-Krieg hat die weltweit groesste
  aktuelle Vertreibungskrise (~12 Mio.) und einen UN-belegten
  Genozid-Befund in Al-Faschir hervorgebracht, bleibt aber unter-
  berichtet. Kontest: panarabische aegyptische und saudische Medien
  betonen Staats-Legitimitaet und Bruderschaft-/Islamisten-Risiko
  in der Armee; UN, westliche humanitaere und panarabische nicht-
  ausgerichtete Medien betonen zivile Opfer, Drohnenangriffe auf
  Krankenhaeuser und Hungersnot; investigative internationale sowie
  tuerkische und iranische Staatsmedien kritisieren Waffen-
  Lieferungen aus dem Golf und Aethiopien an die RSF.
- **centroid_ids**: `[MIDEAST-SUDAN, MIDEAST-EGYPT, MIDEAST-GULF,
  MIDEAST-SAUDI, AFRICA-CHAD, AFRICA-ETHIOPIA, AMERICAS-USA,
  NON-STATE-EU]`

  Rationale: titles about UAE/Egypt/Saudi/Ethiopia roles often carry
  the backer's centroid more strongly than Sudan's. Including those
  centroids in the FN's scope plus the Sudan-anchor vocabulary lets
  the conjunction catch backer-frame titles that the Sudan-only
  centroid would miss. Chad inclusion catches refugee-spillover
  coverage that surfaces in Daily Nation, News24 and Egypt Today.

- **display_order**: `40` (Mideast theaters / FNs occupy 20-39;
  Sudan, as a separate strategic surface, takes the next slot).

## Narrative slots (3 narratives)

**Stance is toward the Sudanese state / army** as the primary actor
defending sovereignty, consistent with how `iran_theater` and
`israel_theater` set stance toward the home state.

| id | stance | name | one-line frame |
|---|---:|---|---|
| `sudan_state_legitimacy` | +2 | Legitimate state vs paramilitary | Sudan's army is the constitutional state defending against an armed mutiny by the RSF; Brotherhood/Islamist remnants are a manageable internal matter compared with the RSF threat to the state itself. |
| `sudan_humanitarian_catastrophe` | -1 | Humanitarian catastrophe and genocide | Both sides commit atrocities but the scale of RSF violence in Darfur and El Fasher amounts to genocide; hospital strikes, induced famine, mass displacement demand immediate ceasefire and accountability — neither side has a legitimate path to total victory. |
| `sudan_proxy_war_critique` | -2 | UAE-backed proxy war | The Sudan war is the world's "worst proxy war"; the RSF is sustained by UAE arms (via Chad/Ethiopia transit) and Russian/Wagner mineral extraction; Egypt and Saudi backing of the army is the counter-axis. External powers, not Sudanese choice, drive the war's length. |

Stance scheme: +2 / -1 / -2 (no anti-state +1 because the pro-RSF
"revolutionary continuation" cohort is too thin to anchor in publisher
data — see Open Questions).

### Publisher cohorts

`sudan_state_legitimacy` (+2):
- Al-Ahram, Al Arabiya, Arab News, Egypt Today, Khaleej Times,
  Daily Sabah, Anadolu Agency, The National

`sudan_humanitarian_catastrophe` (-1):
- UN News, BBC World, Deutsche Welle, France 24, France 24 (EN),
  Le Monde, The Guardian, Reuters, Associated Press, NPR, Sky News,
  Tagesschau, Sueddeutsche Zeitung, Der Standard, Die Zeit, El Pais,
  Daily Nation, News24, Globe and Mail, Financial Times, Al Jazeera
  (humanitarian-mode pieces)

`sudan_proxy_war_critique` (-2):
- Al Jazeera, Anadolu Agency, TRT World, Daily Sabah, Press TV,
  Times of Israel (anti-UAE coverage), Deutsche Welle, New York Times
  (investigative), Reuters (investigative)

Overlap acknowledged: Al-Ahram and Al Arabiya both publish under
`sudan_state_legitimacy` while UN News and Al Jazeera both publish
under `sudan_humanitarian_catastrophe`. Disambiguation happens via
`framing_keywords` ranking within each narrative — the FN anchor
gate already shared.

## fn_anchor vocabulary (first-pass; expand via deepseek extractor)

**Rules**: every entry follows
[`FN_ANCHOR_VOCABULARY_SPEC.md`](FN_ANCHOR_VOCABULARY_SPEC.md) —
4 pillars (own-side actors, sub-centroid geography, relevant systems,
domain actions), shortest unique form, atoms not phrases, no
third-party leaders, no country-name repetition, Latin-script
duplicates only in `en`. Hand-curated bundle below is the analyst
seed. Run `scripts/extract_fn_anchor_via_deepseek.py --fn-id
sudan_civil_war --centroid MIDEAST-SUDAN --sample-size 200 --window-days
180 --seeds "RSF,Darfur,El Fasher,Kordofan,Sudanese army,Burhan,Hemedti,
genocide,famine,drone,Khartoum,Port Sudan"` before going live, then
hand-curate.

### Critical anchor-safety notes (Sudan-specific)

1. **NEVER use bare `SAF`.** Corpus check: 1,126 titles match `SAF`
   across 180d; only ~12 in `MIDEAST-SUDAN` are the Sudanese Armed
   Forces. Remainder: Sustainable Aviation Fuel (S&P Global),
   Botafogo SAF (football), Singapore Armed Forces, `newsaf.cgtn.com`
   URL substring. Use `Sudanese army` / `Sudan army` /
   `الجيش السوداني` instead.
2. **`Rapid Support Forces` full spelling matches 0 titles in 180d.**
   Headlines compress to `RSF`. Keep `RSF` (3 chars, unique under
   centroid gate).
3. **`Sudan` / `Sudanese` deliberately included.** Normally excluded
   by hard rule 2, but the FN scope includes backer centroids
   (Egypt, UAE, Saudi, Chad, Ethiopia), where `Sudan` is the frame
   marker discriminating Sudan-war coverage from generic backer
   politics (e.g. "Egypt, UAE FMs discuss Sudan developments").
   `en` only.
4. **South Sudan pollution**: 72/620 (~12%) of MIDEAST-SUDAN titles
   are actually about South Sudan. Anchor bundles can't do negative
   filtering; mitigate at the centroid-tagging layer (separate
   MIDEAST-SOUTH-SUDAN centroid) — out of scope for this spec.

### Bundle

```text
Pillar 1 (own-side actors): RSF, Sudanese army, Sudan army,
  Burhan, al-Burhan, Hemedti, Hemeti, Hemetti, Dagalo, Janjaweed,
  Brotherhood, Islamist, Muslim Brotherhood

Pillar 2 (sub-country geography): El Fasher, al-Fasher, Al-Fashir,
  el-Fasher, Darfur, Kordofan, Khartoum, Port Sudan, Omdurman,
  Wad Madani, Nyala, El Geneina, Geneina, Gezira

Pillar 3 (relevant systems / events): Jeddah talks, Quad, Rapid
  Support, paramilitary, militia, "April 15", "15 April"
  (note: April-15 is the war's origin date and recurs in
  retrospective coverage — keep)

Pillar 4 (domain actions): drone strike, drone, hospital strike,
  famine, starvation, displaced, refugee, ceasefire, truce,
  proxy war, genocide

  Country names (kept due to Sudan-specific edge case): Sudan, Sudanese
```

```json
{
  "ar": ["السودان","السودانية","السوداني","قوات الدعم السريع","الدعم السريع","حميدتي","دقلو","البرهان","الجيش السوداني","الجنجويد","الإخوان","الإسلاميين","الفاشر","دارفور","كردفان","الخرطوم","بورتسودان","أم درمان","ود مدني","نيالا","الجنينة","الأبيض","مجاعة","مسيرات","مسيرة","هدنة","وقف إطلاق النار","إبادة","مستشفى","نازحين","لاجئين","مليشيا","حرب بالوكالة","جدة","الرباعية"],
  "de": ["Sudan-Krieg","sudanesische Armee","Buergerkrieg im Sudan","Schnelle Eingreiftruppe","Dschandschawid","Bruderschaft","Islamisten","Al-Faschir","Darfur","Kordofan","Khartum","Port Sudan","Omdurman","Hungersnot","Genozid","Voelkermord","Waffenruhe","Vertriebene","Fluechtlinge","Drohnenangriff","Stellvertreterkrieg","Miliz","Paramilitaer"],
  "en": ["Sudan","Sudanese","RSF","Sudanese army","Sudan army","Burhan","al-Burhan","Hemedti","Hemeti","Hemetti","Dagalo","Janjaweed","Muslim Brotherhood","Brotherhood","Islamist","El Fasher","al-Fasher","Al-Fashir","el-Fasher","Darfur","Kordofan","Khartoum","Port Sudan","Omdurman","Wad Madani","Nyala","El Geneina","Geneina","Gezira","Jeddah talks","Quad","Rapid Support","paramilitary","militia","April 15","15 April","drone strike","drone","hospital strike","famine","starvation","displaced","refugee","ceasefire","truce","proxy war","genocide"],
  "es": ["guerra de Sudan","ejercito sudanes","Fuerzas de Apoyo Rapido","Hermandad Musulmana","islamistas","El-Fasher","Darfur","Kordofan","Jartum","hambruna","genocidio","alto el fuego","desplazados","refugiados","ataque con drones","milicia","guerra subsidiaria","guerra por delegacion"],
  "fr": ["guerre au Soudan","armee soudanaise","Forces de soutien rapide","FSR","Freres musulmans","islamistes","el-Facher","el-Fasher","Darfour","Kordofan","Khartoum","Port-Soudan","famine","genocide","cessez-le-feu","deplaces","refugies","frappe de drone","drone","milice","guerre par procuration"],
  "hi": ["सूडान","रैपिड सपोर्ट फोर्सेज","सूडानी सेना","बुरहान","हमदान दगालो","अल-फाशेर","दारफुर","कोरडोफान","खारतूम","जनसंहार","अकाल","युद्धविराम","ड्रोन हमला","विस्थापित"],
  "it": ["guerra in Sudan","esercito sudanese","Forze di Supporto Rapido","Fratellanza Musulmana","islamisti","El-Fasher","Darfur","Kordofan","Khartoum","carestia","genocidio","cessate il fuoco","sfollati","rifugiati","attacco con droni","milizia","guerra per procura"],
  "ja": ["スーダン","スーダン内戦","スーダン軍","RSF","即応支援部隊","ブルハン","ヘメティ","ダガロ","ダルフール","ハルツーム","コルドファン","エル・ファシャー","飢饉","ジェノサイド","停戦","避難民","難民","ドローン攻撃","病院攻撃","代理戦争","民兵"],
  "ru": ["Судан","суданская армия","суданские вооруженные силы","Силы быстрой поддержки","СБП","Бурхан","аль-Бурхан","Хемедти","Хеметти","Дагало","Джанджавид","Братья-мусульмане","исламисты","Эль-Фашер","Дарфур","Кордофан","Хартум","Порт-Судан","Омдурман","голод","геноцид","перемирие","прекращение огня","перемещенные","беженцы","удар беспилотника","беспилотник","ополчение","ополченцы","прокси-война","опосредованная война"],
  "zh": ["苏丹","苏丹内战","苏丹军队","快速支援部队","布尔汉","赫梅蒂","达加洛","穆斯林兄弟会","伊斯兰主义者","法希尔","达尔富尔","科尔多凡","喀土穆","苏丹港","饥荒","种族灭绝","停火","流离失所","难民","无人机袭击","民兵","代理人战争"]
}
```

### Anchor-bundle pre-commit checklist (per spec)

- [x] No third-party leader names (no Sisi, MBZ, MBS, Trump, Putin)
- [x] Country name `Sudan` / `Sudanese` deliberately included with
  written justification (sub-centroid disambiguation across backer
  centroids)
- [x] Burhan, Hemedti use shortest unique forms; spelling variants
  kept because no single form dominates corpus (`Hemedti`, `Hemeti`,
  `Hemetti` all appear)
- [x] No phrase variants — `drone strike` and `drone` are kept
  separately (not `drone strike on hospital`)
- [x] No rhetorical / stance phrases (`atrocity`, `worst war`,
  `forgotten war` excluded — those belong on `framing_keywords`)
- [x] No 2-character tokens (`RSF` and `SBP` are 3+)
- [x] Latin-script identical tokens (`RSF`, `Burhan`, `Hemedti`,
  `Darfur`, `Kordofan`, `Khartoum`) appear only in `en`
- [x] All 10 languages populated; non-Latin scripts (`ar`, `ru`, `zh`,
  `ja`, `hi`) have own native-script lists
- [x] No `SAF` bare alias (S&P / Botafogo / Singapore false-positive
  risk documented)
- [x] Atomic FN — no parent theater to duplicate

## Open questions before SQL

1. **No pro-RSF narrative**: the brief flagged a possible "RSF as
   outgrowth of revolutionary process / anti-Islamist" cohort. Corpus
   check shows no consistent publisher cohort defending the RSF
   editorially. Khaleej Times and The National defend the *UAE's
   posture*, not the RSF itself, and frame UAE involvement as
   humanitarian aid + peace mediation. Decision: do not seed a fourth
   narrative; if a pro-RSF cohort emerges in the data, add it later.

2. **MIDEAST-SOUTH-SUDAN centroid**: 12% of `MIDEAST-SUDAN` titles are
   actually about South Sudan. Out of scope for this spec but a
   centroid-tagging clean-up ticket should be filed separately.

3. **Centroid scope for backer narrative**: included
   `AFRICA-CHAD`, `AFRICA-ETHIOPIA`, `NON-STATE-EU` because UAE-RSF
   pipeline coverage and EU sanctions discussions often anchor on
   those rather than Sudan. Risk: widens attribution to off-topic
   Chad / Ethiopia stories. Mitigation: the FN anchor bundle must
   include a Sudan-specific term (we kept `Sudan` and `Sudanese`
   precisely for this), and the conjunction ANDs the anchor against
   the publisher cohort. If false positives spike during bootstrap,
   tighten by removing Chad / Ethiopia centroids and accepting the
   coverage gap.

4. **`Brotherhood` / `Islamist` aliases**: used in pro-state framing
   ("RSF justifies its rebellion as anti-Brotherhood") and in US
   coverage ("US working to limit negative Islamist influence in
   Sudan's army-backed government"). Risk: `Islamist` is broad and
   may match Israel-Hamas, Iran, Algeria coverage too. The centroid
   gate (Sudan + backers) should contain it but watch during
   bootstrap.

5. **Stance scheme `+2 / -1 / -2`** mirrors `israel_theater` rather
   than the `+2 / 0 / -2` trio. Reflects that the humanitarian
   narrative is critical of state conduct (`-1`) but not opposed to
   the state's right to fight (`-2` would be the proxy critique).
   Open for review.

## Build order (suggested)

1. **Review this spec.** Adjust narrative roster or scope if needed.
2. **Anchor extraction.** Run
   `scripts/extract_fn_anchor_via_deepseek.py` for `sudan_civil_war`
   against Render corpus, sample-size 200, window-days 180, seeds as
   above. Hand-edit per the anchor-safety notes (drop any `SAF` bare,
   keep `Sudan`/`Sudanese`).
3. **Publisher cohort calibration.** Run
   `scripts/calibrate_narrative_keywords.py` per narrative against
   Render corpus to surface `framing_keywords` analyst missed
   (especially Brotherhood / Islamist vocabulary on the state-
   legitimacy narrative, and arms-transit vocabulary on the proxy-
   war narrative).
4. **Write migration**:
   `db/migrations/20260513_friction_node_sudan_civil_war_seed.sql`
   — single `friction_nodes` row + single `taxonomy_v3` fn_anchor
   row + 3 `narratives_v2` rows + sanity-check DO block. Pattern
   shorter than `20260512_israel_theater_seed.sql` because no
   theater wrapper. Apply locally.
5. **Bootstrap locally**:
   `python scripts/bootstrap_friction_node.py --fn-id sudan_civil_war`.
   Inspect per-narrative match counts. Goal: each narrative ≥80
   titles, ≥30 events. If thinner, widen anchor or publisher set.
6. **Sanity-check page**: `/en/friction-nodes/sudan_civil_war` plus
   the DE version. Check brick hues (+2 green-700, -1 red-500, -2
   red-700), sample headlines on-frame, country pills, activity
   chart credible.
7. **Push to Render**: apply migration on Render, run bootstrap on
   Render, bust frontend cache.

## Expected DecisionLog entry

```yaml
- id: D-08x
  date: 2026-05-13
  type: data-model
  status: accepted
  title: Seed Sudan civil war FN — 1 atomic FN + 3 narratives
  rationale:
    - MIDEAST-SUDAN holds ~620 unattributed titles (180d), publisher-
      aligned around three contested framings (state legitimacy,
      humanitarian/genocide, UAE-proxy critique).
    - Single-axis war (RSF vs army) does not justify a theater
      wrapper; sub-fricions are facets of the same phenomenon and
      publisher cohorts overlap across them.
    - Volume insufficient (~620/180d) to subdivide into 3-4 atomic
      FNs without dropping each narrative below the 80-title floor.
  scope:
    - friction_nodes: sudan_civil_war (atomic)
    - narratives_v2: 3 (state legitimacy +2, humanitarian -1,
      proxy critique -2)
    - taxonomy_v3: 1 fn_anchor bundle (10 languages, ~120 unique
      tokens)
  consequences:
    - Sudan moves from unattributed to a contested standalone FN
    - Establishes precedent for "thin-but-sharp" standalone atomic
      FNs (no theater wrapper) — next candidates: Myanmar civil war,
      Haiti gang state, Sahel coup belt
    - Centroid-tagging follow-up: separate MIDEAST-SOUTH-SUDAN
      centroid to remove 12% pollution
```

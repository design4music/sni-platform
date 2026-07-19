# FN Anchor Vocabulary — Spec

**Status**: evergreen reference. Read before drafting any `fn_anchor`
bundle. Supersedes the orphan draft at `docs/fn_anchor_vocabulary_spec.md`.

**Why this exists**: the same five mistakes keep showing up in
hand-drafted bundles (enumerating third-party leaders, repeating
phrase variants, restating the actor country, ignoring shortest-form
substring matching, blanket-translating Latin-script words into every
European language). This spec fixes them once.

## What a bundle is for

A friction node's `fn_anchor` bundle is the vocabulary that answers
one question for any incoming title or event:

> "Is this title topically about this FN's phenomenon?"

The bundle is **country-neutral**. The actor's country is already
established by `friction_nodes.centroid_ids` matching `titles_v3.centroid_ids`
(Phase 2.1 attribution). The bundle's job is to identify the
*phenomenon*, not the country.

## The attribution conjunction

A title attributes to a narrative iff ALL of:

1. `titles_v3.publisher_name` ∈ `narratives_v2.publishers`
2. `titles_v3.centroid_ids` && `friction_nodes.centroid_ids`
3. `titles_v3.title_display` ILIKE `'%' || alias || '%'` for at least
   one alias in the FN's `fn_anchor` bundle (any language)

Event attribution is the same shape against `events_v3.title`.

The conjunction is what makes single-word aliases like `visit`, `talks`,
or `summit` safe — they're cross-filtered by publisher cohort + centroid.

## Matching semantics — verified

- Match: `ILIKE '%alias%'` against `title_display` / `e.title`.
- Case-insensitive. Substring. Whitespace and punctuation literal.
- Shortest-form rule: `Sharaa` matches `al-Sharaa`, `Ahmad al-Sharaa`,
  `Sharaa's`. No need to enumerate prefix variants.
- Order rule: `Damascus visit` and `visit to Damascus` BOTH require
  the literal substring "Damascus visit" — so phrase forms are
  brittle. Use the atoms (`Damascus`, `visit`) instead and let the
  conjunction sort it out.
- False-positive risk for very short tokens: an alias like `IS` is
  contained in `Israel`, `this`, `crisis` → never use 2-character
  generic tokens. Acronyms are fine when they're 3+ characters and
  unique in context.

## The 4 pillars

Every bundle is built from these four pillars. Each language list
is a flat array — pillars are a *mental* organisation, not stored
structure.

### Pillar 1 — People and organisations of the FN's own side

The actors *internal* to the phenomenon. Their leaders, command,
movements, parties, agencies.

- ✓ Iran nuclear: `Fakhrizadeh`, `Salehi`, `AEOI`, `IAEA`
- ✓ Iran proxies: `IRGC`, `Quds Force`, `Hezbollah`, `Nasrallah`,
  `Sinwar`, `Houthi`
- ✓ Syria recognition: `Sharaa`, `Jolani`, `HTS`, `Hayat Tahrir al-Sham`
- ✗ NOT third-party leaders who appear in headlines about the FN:
  no `Trump`, `Macron`, `Merz`, `Zelensky`, `Putin`, `Charles III`
  in any FN bundle. They surface as `persons` in `title_labels`
  regardless; they don't belong in the topic gate.

### Pillar 2 — Specific geography *inside* the centroid

Sub-country locations: cities, regions, neighbourhoods,
installations, facilities, bases, transit chokepoints. Specific
places *inside* the actor's centroid — the centroid already locates
the country, so the bundle's job is to name the sub-country
geography of the phenomenon.

- ✓ Iran nuclear: `Natanz`, `Fordow`, `Arak`, `Bushehr`, `Parchin`
- ✓ Hormuz: `Strait of Hormuz`, `Bandar Abbas`, `Qeshm`, `Larak`
- ✓ Syria theater: `Damascus`, `Tartus`, `Khmeimim`, `Aleppo`
- ✓ Israel-Lebanon: `Beirut`, `southern Lebanon`, `Litani`, `Dahieh`,
  `Galilee`
- ✗ NOT country names or adjectives — `Iran`, `Syria`, `Iranian`,
  `Syrian`, `Lebanon` (when it IS the centroid). These are handled
  by `centroid_ids`. Adding them inflates noise without helping
  attribution.
- Edge: when an FN's primary actor sits inside a multi-country
  centroid (e.g. `MIDEAST-LEVANT` covers SY/LB/JO), the *country
  name itself* becomes legitimate sub-centroid geography
  (`Lebanon`, `Syria` are both useful inside `MIDEAST-LEVANT`).
  Centroid filter alone can't disambiguate; the bundle helps.

### Pillar 3 — Highly relevant systems / programs / events

Named weapons systems, treaties, doctrines, operations, agreements
whose mention strongly implies the FN's phenomenon.

- ✓ Iran nuclear: `JCPOA`, `NPT`, `Vienna talks`, `snapback`, `centrifuge`,
  `enrichment`, `uranium`, `weapons-grade`, `IR-6`
- ✓ Israel-Iran strikes: `Operation True Promise`, `Iron Dome`,
  `Arrow`, `David's Sling`
- ✓ Israel-Lebanon: `Resolution 1701`, `UNIFIL`, `Litani`
- ✓ Hormuz: `UNCLOS`, `freedom of navigation`, `Fifth Fleet`
- ✗ NOT generic news vocabulary — `war`, `attack`, `crisis`, `threat`,
  `condemnation`. Doesn't discriminate.

### Pillar 4 — Domain actions / processes

Verbs and concept nouns describing *what happens* in this FN.
Atomic components, not phrases.

- ✓ Recognition / normalisation: `normalisation`, `recognition`,
  `recognise`, `sanctions lifted`, `delisting`, `reconstruction`,
  `embassy`, `ambassador`, `visit`, `talks`, `summit`, `delegation`,
  `deal`, `agreement`
- ✓ Strikes: `strike`, `airstrike`, `missile`, `drone`, `retaliation`,
  `interceptor`, `ballistic`
- ✓ Nuclear: `enrichment`, `breakout`, `centrifuge`
- ✗ NOT rhetorical stance phrases — `existential threat`, `regime change`,
  `weaponisation`. Stance belongs in `narratives_v2.framing_keywords`,
  not the FN topic gate.
- ✗ NOT phrase variants — `Damascus visit`, `Damascus talks`,
  `Damascus summit` is wrong. Use `Damascus`, `visit`, `talks`,
  `summit` separately and let the conjunction filter.

## Hard rules

1. **One concept = one shortest alias.** `Sharaa` not `al-Sharaa /
   Sharaa / Ahmad al-Sharaa`. Substring match catches the prefixed
   variants.
2. **No country-name repetition.** `centroid_ids` handles it.
   `government`, not `Syrian government`.
3. **No phrase variants — atoms only.** `Damascus`, `visit`, `summit`
   — never `Damascus visit`, `visit to Damascus`, `Damascus summit`.
4. **No third-party leaders.** They're not part of the FN's own
   side. Tomorrow's visitor changes; the FN doesn't.
5. **No rhetorical / stance vocabulary.** That's
   `narratives_v2.framing_keywords`.
6. **No 2-character tokens.** Substring match makes them dangerous
   (`IS` ⊂ `Israel`).
6b. **No short/generic non-English aliases.** Non-English aliases (any
   language but `en`) match via substring with no word-boundary
   protection (see `ALIAS_MATCH_OTHER_SQL` in
   `scripts/bootstrap_friction_node.py`) -- English gets boundary
   protection, other languages don't and structurally can't (German
   compounds words with no separator, so a boundary regex would silently
   stop matching real compounds even with correct spelling). This is safe
   for long, specific words but the same collision risk as rule 6 applies
   to short/generic ones -- avoid them the same way you'd avoid a 2-char
   English token.
6c. **Write non-English aliases in native orthography, not ASCII
   transliteration.** `Fluechtlinge` never matches real text using
   `Flüchtlinge` -- it's a literal character mismatch, not a boundary
   issue. Same for stripped Spanish/French/Italian accents
   (`corrupcion` vs `corrupción`, `negociation` vs `négociation`). Write
   `ä ö ü ß`, `á é í ó ú ñ`, `à â ç é è ê ë î ï ô ù û ü`, etc. directly.
7. **Atomic FN bundles do not duplicate their parent theater bundle**
   — the conjunction lets either match qualify; duplication only
   inflates the file.

## Language coverage

Target 10 languages — the active ingest set:

`en, de, es, it, fr, ru, hi, zh, ar, ja`

### Latin-script duplicate rule

If a token's spelling is **identical across European Latin-script
languages**, include it only in `en`. Don't repeat the same string
in `de`, `es`, `it`, `fr`. Examples that go EN-only:

- All Latin-character proper names that don't change spelling:
  `Sharaa`, `Jolani`, `Sinwar`, `Netanyahu`, `Nasrallah`, `Hamas`,
  `Hezbollah`, `Houthi`, `SDF`, `YPG`, `PKK`, `HTS`, `IDF`, `IRGC`,
  `JCPOA`, `IAEA`, `NPT`, `UNIFIL`, `OPEC`
- Latin-character place names that are identical or near-identical:
  `Gaza`, `Aleppo`, `Hormuz`, `Tartus` (DE differs: `Damaskus` /
  `Beirut` same as EN / `Riad` differs / `Mossul` differs)

Rule of thumb: if a German, French, Italian, Spanish reader of your
draft `en` list would type the *same string* in their language, skip
that language for the token.

Tokens that DO need translation (typical):

- Common nouns (`government`, `Regierung`, `gobierno`, `governo`)
- Verbs (`visit`, `Besuch`, `visita`, `visite`)
- Concept words (`reconstruction`, `Wiederaufbau`, `reconstrucción`)

Non-Latin-script languages (`ar`, `ru`, `zh`, `ja`, `hi`) **always**
get their own list because the script differs. No collapse there.

## Workflow (corpus-driven)

The four-step process. Run for every new FN.

**Model assignment** (learned from the `eu_cohesion_theater` build,
2026-07-15 — see `project_eu_cohesion_theater` memory for the full
session). The steps split cleanly into two kinds: *mechanical*
(follow a checklist against known facts — cheap model is fine) and
*judgment* (read ambiguous real-world output and decide what it
means — reasoning depth earns its cost here). Concretely:

| Step | Model | Why |
|---|---|---|
| 1. Seed selection | **Sonnet** | Picking obvious topic words once you know the phenomenon. |
| 2. Run extractor | **Sonnet** (or no LLM — it's a script) | Mechanical script invocation. |
| 3. Human curation | **Opus** for the *drop/keep calls*, Sonnet-OK for *applying* a decided rule | The 7 hard rules are checklist-mechanical, but deciding whether an alias is a real leak or benign co-occurrence is not: auditing `eu_right_realignment`, `Bardella` showed 84% "%foreign" against `MIDEAST-LEVANT`, and every one of those titles *also* carried `FRANCE` — reading the auditor's raw percentage without checking co-occurrence would have wrongly dropped a precise anchor. That kind of "does this number actually mean what it looks like" check is where a shallower pass tends to accept a plausible-looking metric instead of verifying it. |
| 4. Apply | **Sonnet** | Script invocation, idempotent, no judgment. |
| Verify (row exists) | **Sonnet** | Simple SQL check. |

If you're delegating step 3 to a subagent, hand it the auditor's
*samples*, not just the percentages — the judgment call needs the
actual headline text, not the summary statistic.

### Step 1 — Seed selection (5 minutes) `[Sonnet]`

Pick 5–20 high-confidence topic words that pre-filter the corpus
to titles plausibly about this FN. For Syria recognition:
`Sharaa, Jolani, HTS, normalisation, recognition, reconstruction,
sanctions, ambassador, embassy, Damascus`. Doesn't need to be
exhaustive — just enough to gather a sample.

### Step 2 — Run the extractor `[Sonnet]`

```bash
python scripts/extract_fn_anchor_via_deepseek.py \
    --fn-id <fn_slug> \
    --centroid <PRIMARY_CENTROID> \
    --sample-size 200 \
    --window-days 365 \
    --seeds <comma,separated,seeds>
```

It pulls a publisher-balanced sample, runs Deepseek against this
spec's rules, auto-collapses Latin-script duplicates, writes
`out/extraction/<fn_id>__<timestamp>.json` (bundle proposal) and
`.corpus.md` (the sample).

### Step 3 — Human curation `[Opus for drop/keep judgment; Sonnet OK once decided]`

Open the JSON. Apply the 4-pillar lens and the 7 hard rules. Typical
edits:

- Drop off-topic terms that aren't unique to this FN.
- Drop any third-party leader names that slipped through.
- Drop phrase variants — keep the atoms.
- Drop the actor country name and its adjective.
- Canonicalise spellings (`Ispahan` → `Isfahan` with `Esfahan` as
  alternate).
- Add high-precision anchors the corpus sample missed (treaties,
  dormant infrastructure, key historical figures).

Save as `out/extraction/<fn_id>__curated.json`.

**PAUSE POINT (manual-switch fallback)**: if you can't delegate this
step to a subagent (e.g. it's a long back-and-forth in the main
conversation and switching would lose context), this is where to stop
and run `/model claude-opus-4-8` before continuing, then switch back
to Sonnet after the curated JSON is saved.

### Step 4 — Apply `[Sonnet]`

```bash
python scripts/apply_fn_anchor_bundle.py --json out/extraction/<fn_id>__curated.json   # dry-run
python scripts/apply_fn_anchor_bundle.py --json out/extraction/<fn_id>__curated.json \
    --mode apply --emit-sql db/migrations/<date>_<theater>_bundles.sql
```

Idempotent — re-running replaces the bundle's aliases for the same
FN.

**Always pass `--emit-sql`.** This script writes to whatever DB the
environment points at — in practice always local — so the bundle does
NOT travel with the theater's migrations. Skipping this is how Render
ended up with **46 of 121 active atomics carrying no bundle** (audit,
2026-07-18). An atomic with no bundle matches nothing, so a bootstrap
against it silently returns zero events and reads as a failed build
rather than a missing input.

`--emit-sql` appends, so one file accumulates a whole theater's bundles,
and it works in dry-run too (generate the deploy SQL without writing to
any DB). Commit that file alongside the theater's other migrations.

Also: **the curated JSON itself must be committed** — `out/` is
gitignored, so it needs `git add -f`. The deploy runbook names these
JSONs as structural content with git as the source of truth, but as of
2026-07-18 only 16 of 100 on disk were tracked.

### Verify `[Sonnet]`

```sql
SELECT jsonb_object_keys(aliases) AS lang,
       jsonb_array_length(aliases->jsonb_object_keys(aliases)) AS n
FROM taxonomy_v3
WHERE linked_id = '<fn_id>' AND taxonomy_function = 'fn_anchor';
```

## Pre-commit checklist

Walk this before applying ANY hand-edited bundle:

- [ ] No third-party leader names anywhere (Pillar 1: own-side actors only)
- [ ] No actor country name or adjective (Pillar 2: handled by centroid_ids)
- [ ] No phrase variants (Pillar 4: atoms only)
- [ ] Each name uses shortest unique form (`Sharaa` not `al-Sharaa`)
- [ ] No rhetorical / stance phrases (those live on `narratives_v2.framing_keywords`)
- [ ] No 2-character tokens
- [ ] Latin-script identical tokens appear ONLY in `en`
- [ ] All 10 languages have at least one entry where the script differs
  (`ar`, `ru`, `zh`, `ja`, `hi` should never be empty)
- [ ] Atomic FN doesn't restate its parent theater's anchors

## Worked example — Syria recognition (Pillar-by-pillar)

```text
Pillar 1 (own-side actors):
  Sharaa, Jolani, HTS, Hayat Tahrir al-Sham, SANA

Pillar 2 (specific geography of the phenomenon):
  Damascus, Tartus, Khmeimim
  (Syria, Syrian — excluded, handled by centroid)

Pillar 3 (relevant systems / programs):
  Arab League, GCC, terror list, terrorist designation,
  transitional government, interim government

Pillar 4 (domain actions):
  normalisation, recognition, recognise, sanctions, lifted,
  easing, relief, delisting, reconstruction, investment, deal,
  agreement, talks, summit, visit, delegation, embassy,
  ambassador, restoring relations

Latin-collapse output (en only): all Pillar 1 names except SANA
  (uppercase), Damascus, Tartus, Khmeimim, HTS, Arab League, GCC

Per-language translation needed: Pillar 4 verbs, plus
  `transitional government`, `terror list`, `reconstruction`
```

## DON'T examples — common drafting mistakes

```text
✗ Charles al-Sharaa          (third-party leader; will rot)
✗ Zelensky Damascus          (third-party leader)
✗ Syrian government          (country name redundant with centroid)
✗ Damascus visit             (phrase; use "Damascus" + "visit")
✗ visit to Damascus          (phrase variant)
✗ al-Sharaa                  (use shortest: "Sharaa")
✗ Ahmad al-Sharaa            (use shortest: "Sharaa")
✗ existential nuclear threat (rhetorical stance; not topic gate)
✗ regime change              (rhetorical stance)
✗ IS                         (2-char token; ⊂ "Israel", "this", "crisis")
✗ Iran                       (country handled by centroid_ids)
```

## Related

- Theater build methodology (archetypes, prune loop, real-coverage
  calibration): [`FN_THEATER_BUILD_SPEC.md`](FN_THEATER_BUILD_SPEC.md)
- Runbook: [`FRICTION_NODES_RUNBOOK.md`](FRICTION_NODES_RUNBOOK.md)
- Bootstrap (matching code): `scripts/bootstrap_friction_node.py`
  (lines 117-147 events, 205-231 titles)
- Extractor: `scripts/extract_fn_anchor_via_deepseek.py`
- Apply tool: `scripts/apply_fn_anchor_bundle.py`
- Worked example in progress: [`SYRIA_THEATER_SPEC.md`](SYRIA_THEATER_SPEC.md)
- Asana evergreen: https://app.asana.com/1/1211666582649030/project/1211666445056038/task/1214763644818654

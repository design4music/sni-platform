# Russia-Europe Theater — Phase 2 Build Brief

**Status**: working brief for the `russia_europe_theater` greenfield build,
2026-07-16. Structure approved by user (Phase 1). Follow
`docs/context/FN_THEATER_BUILD_SPEC.md` §0a. Work is LOCAL and reversible;
Render promotion is a separate authorized step.

**Model plan (user wants to minimise Opus).** Opus locked the structure +
this design. Sonnet executes steps A–D + F mechanically. Return to Opus only
for: bundle drop/keep audit (step C, if the auditor flags surprises) and the
final measure/sample-read (step G). All narrative *design* is already made
below — Sonnet just encodes it to SQL.

---

## Approved structure (4 atomics)

| atomic | phenomenon | archetype | primary_target |
|---|---|---|---|
| `russia_nato_deterrence` (KEEP, rebuild bundle) | Eastern-flank military posture: NATO build-up, rearmament, conscription, nuclear signalling, force deployments | multilateral | null |
| `russia_hybrid_warfare` (NEW, flagship) | gray-zone: sabotage, undersea cables, shadow fleet, GPS jamming, espionage/subversion | multilateral | null |
| `russia_airspace_incursions` (NEW) | aerial boundary-probing + the mirror counter-accusation that NATO/Baltic soil hosts Ukrainian strikes | multilateral | null |
| `russia_sanctions_regime` (KEEP as-is; centroid widened) | sanctions ON Russia + enforcement, shadow-fleet oil cap, frozen assets, energy phase-out | target-centric (RUS) | EUROPE-RUSSIA |

Retired (deactivated): `baltic_security`, `russia_gas_leverage`.
Structure migration: `db/migrations/20260716_russia_europe_restructure.sql`.

Boundary (no collision): `europe_us_theater` = transatlantic (target USA);
`arctic_theater` = High North; `ukraine_war_theater` = gated on EUROPE-UKRAINE;
`eu_cohesion_theater` = EU-internal politics. Kremlin party-influence
(Orbán/Fico) stays with eu_cohesion by user decision; covert active-measures
(spy nets, disinfo ops) live inside `russia_hybrid_warfare`.

---

## Step order (Sonnet)

- **A.** Apply structure migration via `python scripts/safe_db_migrate.py db/migrations/20260716_russia_europe_restructure.sql` (auto-backup). Verify the 4-member theater + 2 deactivations.
- **B.** Build 3 bundles (deterrence rebuild, hybrid, airspace) from the seeds + KEEP/DROP below. Sanctions bundle already exists — leave it. Draft → `out/extraction/<fn>__curated.json` → `apply_fn_anchor_bundle.py`.
- **C.** Audit each new/rebuilt bundle: `PYTHONIOENCODING=utf-8 python scripts/audit_fn_anchor_aliases.py --fn-id <fn> --window-days 180 --samples 1 --min-n 1`. Drop leak-class aliases confirmed by samples. **If the auditor surprises you (a high-%foreign core anchor), PAUSE for Opus.**
- **D.** Attribute: `python scripts/bootstrap_friction_node.py --fn-id <fn> --window-days 180` for all 4 atomics (run in background; ~2 min each).
- **E.** Encode narratives (design below) as a migration, then re-run `bootstrap` to fill `title_narratives`.
- **F.** Completeness fields (description_en/_de, editorial_summary_en/_de, name_de) on theater + all atomics. Neutral, factual, evergreen prose (see the FN-descriptions-neutral memory).
- **G.** `[Opus]` Measure: leak%, within-group overlap, per-narrative + per-card counts; read sample titles per narrative. Then revalidate cache.

---

## Bundle seeds + KEEP/DROP guidance

All bundles: 10 langs (`en de es it fr ru hi zh ja ar`), 4-pillar, native
orthography, no country names, no third-party leaders, no stance phrases.
These are **multilateral** atomics (no target gate except sanctions) — so
**alias purity is the only lever**. Lean on fixed nouns/toponyms/named
incidents; avoid generic verbs and shared equipment.

### `russia_nato_deterrence`
Seeds: `Eastern flank, Kaliningrad, Suwalki, tripwire, battlegroup, forward presence, Baltic air policing, deterrence, rearmament, conscription, defence spending, war economy, Zapad, Steadfast Defender, Baltic Sentry, brigade`
- KEEP: named exercises (`Zapad`, `Steadfast Defender`, `Iron Wolf`, `Baltic Sentry`), toponyms (`Kaliningrad`, `Suwalki`), posture nouns (`tripwire`, `battlegroup`, `forward presence`, `eFP`, `Eastern flank`, `rearmament`, `conscription`, `war economy`, `defence spending`).
- DROP: weapon systems (`Iskander`, `Patriot`, `HIMARS`, `F-35` — leak to aid/Ukraine), generic (`war`, `attack`, `threat`, `troops` alone), third-party leaders (`Rutte`, `SACEUR` name).

### `russia_hybrid_warfare`
Seeds: `sabotage, undersea cable, subsea cable, shadow fleet, tanker, Nord Stream, Druzhba, GPS jamming, spoofing, arson, espionage, saboteur, hybrid warfare, gray zone, active measures, disinformation, Gulf of Finland, Baltic Sea, anchor-dragging, Eagle S`
- KEEP: `sabotage`, `undersea/subsea cable`, `shadow fleet`, `dark fleet`, `anchor-dragging`, `GPS jamming`, `spoofing`, `arson`, `Nord Stream`, `Druzhba`, `Eagle S`, `saboteur`, `espionage`, `active measures`, maritime toponyms (`Gulf of Finland`, `Baltic Sea`).
- DROP: bare `drone` (floods from Ukraine), `attack`, `threat`, `hybrid` alone (→ "hybrid cars/navy" — require `hybrid warfare`/`hybrid threat`), `pipeline` alone (→ commercial energy), `tanker` alone is borderline (keep only with `shadow`/`sanctioned` — or accept and let sanctions target gate not apply here; audit it).

### `russia_airspace_incursions`
Seeds: `airspace, incursion, airspace violation, scramble, intercept, shoot down, Article 4, no-fly, MiG, air defence, jet, Poland airspace, Estonia airspace`
- KEEP: `airspace`, `incursion`, `airspace violation`, `scramble`, `intercept`, `shoot down`, `Article 4`, `no-fly`, `air defence` (paired by centroid). The NATO-complicity counter-accusation is captured in the **−2 narrative framing_keywords**, NOT the topic bundle.
- DROP: bare `drone`, `missile`, aircraft type names that leak (`Su-24` ok-ish; audit), `attack`, `strike` (→ Ukraine long-range war).

---

## Narrative design (encode verbatim; step E)

Three reusable publisher blocs (kept publisher-DISJOINT so stance routes cleanly):

- **BLOC_WEST_MAIN** (+2 / pro-NATO): `Reuters, BBC World, Financial Times, Associated Press, The Guardian, Deutsche Welle, Euronews, France 24 (EN), Wall Street Journal, New York Times, Washington Post, NPR, CNN, ABC News, Military Times, Defense News, ERR News, LRT English, LSM English, Atlantic Council, Politico, Kyiv Post, The Telegraph, The Economist, EurActiv, Bloomberg`
- **BLOC_RU_CN_STATE** (−2 / adversary): `RT, TASS, TASS (EN), tass.com, Sputnik, RIA Novosti, Lenta.ru, lenta.ru, Gazeta.ru, gazeta.ru, Izvestia, Kommersant, BelTA, BelTA Russian, Press TV, CGTN, Global Times, China Daily, Xinhua`
- **BLOC_WEST_CRIT** (−1 / skeptic): `Le Monde, El País, Der Spiegel, Süddeutsche Zeitung, Frankfurter Allgemeine, Die Zeit, The Independent, ANSA, La Repubblica, Al Jazeera, Anadolu Agency, Channel NewsAsia`

Rule: `+2/−2` narratives `framing_required=false` (dominant disjoint blocs).
`−1` narratives `framing_required=true` (minority critical takes need a framing
signal so neutral continental coverage isn't mislabeled as critique).
`actor_centroids` = the atomic's centroid set. All bilingual (name_en/de,
claim_en/de, stance_label_en/de), framing_keywords multilingual flat array.

### `russia_nato_deterrence`
1. `eastern_flank_deterrence` +2 BLOC_WEST_MAIN — Eastern-flank build-up is a necessary response to the Russian military threat; deterrence, rearmament, forward presence.
2. `nato_encirclement_provocation` −2 BLOC_RU_CN_STATE — NATO build-up on Russia's borders is aggressive encirclement driving escalation.
3. `militarisation_overreach` −1 BLOC_WEST_CRIT, framing_required — threat inflation and war-economy drift; costly overreach. keywords: `threat inflation, war economy, militarisation, Aufrüstung, Kriegswirtschaft, Bedrohungsinflation, defence-spending burden, overreach`.

### `russia_hybrid_warfare`
1. `hybrid_campaign_defence` +2 BLOC_WEST_MAIN — Russia is waging a coordinated sabotage/gray-zone campaign; attribution + hardening essential.
2. `hybrid_russophobia_denial` −2 BLOC_RU_CN_STATE — hybrid-threat claims are evidence-free Russophobia/pretext; shadow-fleet seizures are maritime piracy.
3. `securitisation_caution` −1 BLOC_WEST_CRIT, framing_required — caution against over-attribution; accidents/criminality mislabeled as Kremlin sabotage. keywords: `no evidence, accident, over-attribution, securitisation, Verdachtsfall, kein Beweis, unbewiesen`.

### `russia_airspace_incursions`
1. `airspace_violation_deterrence` +2 BLOC_WEST_MAIN — Russia deliberately violates NATO airspace to probe/intimidate; NATO must enforce, incl. shoot-down authority.
2. `nato_complicity_provocation` −2 BLOC_RU_CN_STATE — **the mirror frame**: NATO/Baltic states host and enable Ukrainian drone strikes from/through their soil; incursions are Western provocations or false-flags risking wider war. keywords: `provocation, false flag, Ukrainian drones from, staging ground, complicity, провокация, NATO territory`.
3. `escalation_risk_restraint` −1 BLOC_WEST_CRIT, framing_required — shoot-down authority + forward posture risk uncontrolled escalation; incidents often accidental/overblown. keywords: `escalation risk, accidental, overblown, Eskalationsgefahr, versehentlich, restraint`.

### `russia_sanctions_regime` — ALREADY COMPLETE
Keep existing `tighten_and_seize` (+2) / `sanctions_ineffective_and_backfiring` (−2).
(Optional later: a −1 Western sanctions-fatigue card — not required; theater −1 card already fed by the three atomics above.)

### Theater roll-up cards (`fn_id = russia_europe_theater`) — §5.5
Publisher-DISJOINT within the negative bucket (RU_CN vs WEST_CRIT). No bundle, no bootstrap; live roll-up.
1. `russia_europe_western_resolve` +2 BLOC_WEST_MAIN — Europe must deter, defend and sanction a revanchist Russia.
2. `russia_europe_kremlin_counter` −2 BLOC_RU_CN_STATE — Western Russophobia, NATO encirclement and sanctions self-harm manufacture a "Russia threat"; rift-exploitation.
3. `russia_europe_critical_restraint` −1 BLOC_WEST_CRIT — threat inflation, militarisation and escalation risk: a skeptical European counter-current.

---

## Real-coverage evidence (why this carve)

Promoted-event theme sizing (2026, theater centroids): hybrid/sabotage/cable
~1,160 + shadow-fleet/tanker ~748 (dominant, was homeless); NATO deterrence
~2,750; sanctions ~2,450; airspace/drone incursions ~470; gas = defunct
coercion frame (Nord Stream→hybrid, LNG phase-out→sanctions, refinery
crisis→Ukraine). Samples read: Nord Stream war-crime trial (Germany),
UK/Sweden shadow-fleet interceptions, Gulf of Finland cable cuts, Estonia/
Finland/Poland airspace closures, Germany hybrid-threat centre, "Baltic states
reject Russian claim they allowed airspace for Ukraine strikes."

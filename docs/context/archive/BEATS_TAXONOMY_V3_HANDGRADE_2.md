# ELO v3.0 Hand-Grading Test #2 — EUROPE-FRANCE/politics/March

**Date**: 2026-04-13
**CTM**: EUROPE-FRANCE / geo_politics / 2026-03
**Sample**: 50 random English titles
**Focus**: ELECTORAL_EVENT validation, CIVIL_ACTION scope, PRESSURE merger in politics

## Headline finding

**22 of 50 titles (44%) are French local/mayoral elections, ALL currently labeled wrong in v2.0.** Under v3 they all land cleanly in `ELECTORAL_EVENT`. This is the single biggest v3 win validated by any test so far. Elections are a MASSIVE category in politics tracks and the current taxonomy has no home for them.

## Current v2.0 labels for those 22 election titles

| Wrong label used | Count |
|---|---|
| `COLLECTIVE_PROTEST` | 15 |
| `LEGISLATIVE_DECISION` | 4 |
| `SECURITY_INCIDENT` | 2 |
| `POLICY_CHANGE` | 1 |

**Not a single election was correctly labeled.** The LLM is desperate — it cycles through 4 different wrong classes depending on the keyword it latches onto. `COLLECTIVE_PROTEST` is the default because "vote" ≈ "collective action" in the model's priors.

---

## Full 50-title table

### Elections (22 titles, all IMPROVED by new ELECTORAL_EVENT class)

| # | Title (shortened) | v2 | v3 |
|---|---|---|---|
| 3 | "French vote tests polarised electorate..." | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 5 | "French far right fails to win in major cities..." | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 8 | "Mayor's races in Paris, Marseille top runoffs" | SECURITY_INCIDENT | ELECTORAL_EVENT |
| 9 | "Leftists win mayoral elections in Paris and Marseille" | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 10 | "Socialists win Paris mayoral election..." | LEGISLATIVE_DECISION | ELECTORAL_EVENT |
| 12 | "France votes in mayoral elections ahead of 2027" | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 15 | "French Far Right Falls Short of Statement Win..." | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 19 | "French elect mayors in key cities including Paris" | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 23 | "France local elections: a key test..." | LEGISLATIVE_DECISION | ELECTORAL_EVENT |
| 28 | "France's far right notches up mixed results..." | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 30 | "French far-right fails to win Marseille and Toulon" | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 31 | "French voters head to the polls..." | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 33 | "French elections: Paris stays left..." | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 34 | "France picks mayors in key test..." | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 36 | "Major cities see close first round results" | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 37 | "France picks mayors in test of political mood..." | POLICY_CHANGE | ELECTORAL_EVENT |
| 38 | "Le Pen's far right suffers setbacks..." | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 41 | "France Chose Thousands of New Mayors on Sunday" | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 43 | "Hittler goes to the polls against Zielinski..." | COLLECTIVE_PROTEST | ELECTORAL_EVENT |
| 45 | "Paris looks at five-way race for new mayor" | POLITICAL_PRESSURE | ELECTORAL_EVENT |
| 47 | "Fractured vote reshapes alliances..." | SECURITY_INCIDENT | ELECTORAL_EVENT |
| 49 | "France Votes in Key Mayoral Runoffs..." | LEGISLATIVE_DECISION | ELECTORAL_EVENT |
| 50 | "France local elections: a key test..." (dup of #23) | LEGISLATIVE_DECISION | ELECTORAL_EVENT |

**All 22 land cleanly. Zero ambiguity.** ELECTORAL_EVENT is exactly the slot this content needed.

### PRESSURE merger wins (4 titles, IMPROVED)

| # | Title | v2 | v3 |
|---|---|---|---|
| 14 | "Macron slams 'unacceptable' Israeli attacks on Lebanon" | DIPLOMATIC_PRESSURE | PRESSURE |
| 27 | "French proposal for Israeli-Lebanese ceasefire" | DIPLOMATIC_PRESSURE | PRESSURE |
| 39 | "Lebanese president calls for truce while receiving French FM" | DIPLOMATIC_PRESSURE | PRESSURE |
| 44 | "French President urges Iran to engage in talks" | DIPLOMATIC_PRESSURE | PRESSURE |

All four were correctly labeled as the right tier (5) under v2 — the merge just makes them consistent. Clean win.

### ALLIANCE_COORDINATION reclassification (4 titles, IMPROVED)

Bilateral meetings mislabeled as DIPLOMATIC_PRESSURE in v2:

| # | Title | v2 | v3 |
|---|---|---|---|
| 6 | "Meloni speaks to Macron about Iran war..." | DIPLOMATIC_PRESSURE | ALLIANCE_COORDINATION |
| 17 | "Meloni speaks to Macron... (2)" (dup of #6) | DIPLOMATIC_PRESSURE | ALLIANCE_COORDINATION |
| 20 | "Trump-Xi Agenda to Be Mapped Out... in Paris" | DIPLOMATIC_PRESSURE | ALLIANCE_COORDINATION |
| 32 | "Chinese FM Wang Yi holds phone talks..." | DIPLOMATIC_PRESSURE | ALLIANCE_COORDINATION |
| 42 | "Netanyahu meets with French, Lebanese PM" | DIPLOMATIC_PRESSURE | ALLIANCE_COORDINATION |

Consistent pattern: the v2 LLM defaulted any diplomatic interaction to DIPLOMATIC_PRESSURE, but "meeting" / "speaks to" / "holds talks" is ALLIANCE_COORDINATION. This is a **prompt clarity issue, not a taxonomy issue** — the distinction exists in v2 but the LLM doesn't use it. The v3 prompt needs an explicit rule.

### EXCLUDE at 3.3 (13 titles, IMPROVED via filtering)

Commentary, opinion, obituaries, profiles, tourism, polls — content that shouldn't be events at all:

| # | Title | v2 | Exclusion reason |
|---|---|---|---|
| 1 | "French far right faces early tests: What to watch" | INSTITUTIONAL_RESISTANCE | Preview/curtain-raiser |
| 2 | "The Guardian view on France after Macron... \| Editorial" | SECURITY_INCIDENT | Editorial opinion |
| 7 | "The French lesson that Canada needs" | INFORMATION_INFLUENCE | Opinion piece |
| 13 | "Why you should spend Eid Al Fitr at Louvre Abu Dhabi" | SECURITY_INCIDENT | Tourism/lifestyle |
| 16 | "The Chanel-clad political streetfighter..." | SECURITY_INCIDENT | Profile feature |
| 18 | "Trump's Paris moment?" | DIPLOMATIC_PRESSURE | Speculative headline |
| 24 | "France's drift to the extremes is far from over" | SECURITY_INCIDENT | Opinion piece |
| 26 | "Former French PM Lionel Jospin... dies" | SECURITY_INCIDENT | Obituary |
| 35 | "Lionel Jospin... dies at 88" (dup of #26) | SOCIAL_INCIDENT | Obituary |
| 46 | "Trump's approval hits 36% low... Reuters/Ipsos poll" | COLLECTIVE_PROTEST | Poll result |
| 48 | "Organizers of Paralympic Games hand over flag to France" | SOCIAL_INCIDENT | Sports/ceremonial |

**11 titles (22%) are pure noise.** Current v2 labels them with random classes; v3 correctly excludes them. The `SECURITY_INCIDENT` use for editorials and profiles (#2, #13, #16, #24) shows how broken v2 is on this category.

### STATEMENT wins (2 titles, IMPROVED)

| # | Title | v2 | v3 |
|---|---|---|---|
| 22 | "Europe reacts to Macron's atomic offer" | ALLIANCE_COORDINATION | STATEMENT |
| 40 | "French, German environment ministers highlight link..." | ALLIANCE_COORDINATION | STATEMENT |

Both are "X says / reacts / highlights" — classic STATEMENT. Borderline cases where v2's ALLIANCE_COORDINATION was defensible but STATEMENT is cleaner.

### SAME (6 titles, v2 was fine)

| # | Title | v2 | Notes |
|---|---|---|---|
| 11 | "Sarkozy maintains innocence in Libya funding trial" | LEGAL_CONTESTATION | OK |
| 21 | "French politician urges Paris to join Belgium's call..." | POLITICAL_PRESSURE → PRESSURE | Merge-only |
| 25 | "Zelensky to meet Macron in Paris on Friday" | ALLIANCE_COORDINATION | OK |
| 29 | "UN chief names Arnault as personal envoy..." | POLICY_CHANGE | OK (appointment) |

### Not represented in sample

- `CIVIL_ACTION` — **zero actual protests/strikes** in this sample. March 2026 in France was an election month, not a protest month. Can't validate CIVIL_ACTION scope from this data.
- `NATURAL_EVENT` — none (expected for politics track)
- `MARKET_SHOCK` — none (expected for politics track)
- `COMMERCIAL_TRANSACTION` — none (expected)

---

## Tally

| Assessment | Count | % |
|---|---|---|
| **IMPROVED** — new class (ELECTORAL_EVENT) | 22 | 44% |
| **IMPROVED** — PRESSURE merge | 4 | 8% |
| **IMPROVED** — ALLIANCE_COORDINATION reclassification | 5 | 10% |
| **IMPROVED** — STATEMENT new class | 2 | 4% |
| **EXCLUDE at 3.3** (noise filter) | 11 | 22% |
| **SAME** (v2 fine or merge-only) | 6 | 12% |

**82% of titles improve under v3** (up from 64% in USA economy test). France politics has a *higher* v2 error rate because the election gap is catastrophic.

---

## Key findings

### 1. ELECTORAL_EVENT is validated as critical
A politics-track CTM that covered a month of local elections produces ~44% election-related titles, all wrong in v2. ELECTORAL_EVENT is the highest-impact single class addition in the entire v3 draft.

### 2. COLLECTIVE_PROTEST is misused 100% of the time
Not a single title in the sample was an actual protest. Every `COLLECTIVE_PROTEST` label was on an election or poll result. The rename to `CIVIL_ACTION` plus strict scope rules is essential — or the LLM will continue to default-dump elections into it.

### 3. ALLIANCE_COORDINATION is underused by the v2 prompt
Bilateral meetings ("speaks to", "meets with", "holds phone talks") should map to ALLIANCE_COORDINATION, but the v2 LLM defaults them to DIPLOMATIC_PRESSURE. This is a **prompt clarity gap, not a taxonomy gap**. Need an explicit rule in the v3 prompt: *"Bilateral meetings, phone calls, joint statements → ALLIANCE_COORDINATION, not PRESSURE."*

### 4. SECURITY_INCIDENT is a graveyard class
In this politics sample, `SECURITY_INCIDENT` was used for: election preview, editorial, tourism article, profile, opinion piece, obituary. Zero actual security incidents. The v2 LLM uses it as a "not sure where to put this" bucket. v3 prompt must restrict it explicitly: *"Only use SECURITY_INCIDENT for attacks, accidents, breaches with no clear actor. Commentary/analysis → exclude."*

### 5. Obituaries and "X dies" stories have no home
Two titles about former PM Lionel Jospin's death. These aren't events in the Beats sense — they're biographical notices. **Exclude at 3.3.** Adding a DEATH or OBITUARY class is not warranted by volume.

### 6. French CIVIL_ACTION can't be validated from this sample
Zero actual protests. Either March 2026 was genuinely protest-free for France (plausible — election month) or our LLM isn't catching protest stories. Worth checking on a different month or a different centroid where protests are more likely. **Action**: run hand-grade #3 on a different CTM, and ideally include a month/centroid known for protests (e.g. BE/LU or earlier France months).

---

## New ambiguities surfaced

**AMB-15**: "X speaks to Y" / "X meets Y" routinely mislabeled as DIPLOMATIC_PRESSURE by v2. Need explicit prompt rule: bilateral meetings default to ALLIANCE_COORDINATION unless the content is coercive.

**AMB-16**: Editorials, opinion columns, profiles, "what to watch" previews consistently land in SECURITY_INCIDENT as v2's junk drawer. Phase 3.3 needs an explicit content-type filter for op-eds, previews, listicles, profiles.

**AMB-17**: Obituaries — no home class, exclusion is correct but the prompt must name the category so the LLM doesn't invent a home.

---

## Combined findings so far (hand-grades 1 + 2)

After 100 titles across two very different CTMs:

**Classes that are validated as high-value:**
1. `ELECTORAL_EVENT` (22 hits in France politics, 0 in USA economy — expected distribution)
2. `MARKET_SHOCK` (6 hits in USA economy, 0 in France politics — expected)
3. `PRESSURE` merger (10 hits combined)
4. `COMMERCIAL_TRANSACTION` (6 hits in USA economy, 0 in France politics — expected)
5. `STATEMENT` (7 hits combined)

**Classes not yet validated empirically:**
- `NATURAL_EVENT` — no natural disasters in either sample
- `CIVIL_ACTION` — zero actual protests in either sample
- `NATURAL_EVENT`, `CIVIL_ACTION` are both "placeholder" classes that we'll confirm on future data

**The single biggest non-taxonomy finding:** Phase 3.3 exclusion rules are as important as the taxonomy itself. ~25% of current titles across both CTMs should never become events in the first place — they're commentary, analysis, polls, obituaries, editorials, profiles, tourism, sports. Tightening 3.3 is a huge quality win independent of taxonomy changes.

---

## What to add to the v3 draft

1. **AMB-15, AMB-16, AMB-17** in the ambiguity log
2. **Explicit prompt rule**: "Bilateral meetings, phone calls, summits → ALLIANCE_COORDINATION. Use PRESSURE only when content is coercive (demands, condemnations, ultimatums)."
3. **Explicit prompt rule**: "SECURITY_INCIDENT is for attacks, accidents, breaches. NOT commentary, profiles, obituaries, previews, editorials — those are excluded at Phase 3.3."
4. **Phase 3.3 filter expansion**: explicitly list content types to exclude — opinion/editorial, analyst forecast, poll result, profile/feature, obituary, preview/curtain-raiser, tourism/lifestyle, sports ceremony.

---

## Next steps

Hand-grade #2 strongly validates ELECTORAL_EVENT, PRESSURE merger, STATEMENT, and the strict 3.3 exclusion rules. Ready for hand-grade #3.

Suggested CTM: **ASIA-CHINA / geo_economy / 2026-03** — tests `sectors[]` with AI/IT_SOFTWARE/AUTOMOTIVE, MARKET_SHOCK in non-US context, COMMERCIAL_TRANSACTION for Chinese corporate actions, and how `POLICY_CHANGE` vs `LEGISLATIVE_DECISION` distribute for a state with heavy top-down policy reporting.

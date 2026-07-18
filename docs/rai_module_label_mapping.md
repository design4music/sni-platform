# RAI Analytical Label → Module Mapping

## Overview

Events receive 1-3 analytical labels during Phase 4.5a (event summary generation).
Labels are from a fixed taxonomy and deterministically activate RAI analysis modules.
No LLM call needed at analysis time — zero latency module selection.

## Core Modules (always included)

| Module | Name |
|---|---|
| CL-0 | Narrative Contextualization and Framing Assessment |
| NL-3 | Competing Narratives Contrast |
| SL-8 | Systemic Blind Spots and Vulnerabilities |

## Label Taxonomy (8 labels)

### `conflict_military`
**Triggers on:** Wars, strikes, military operations, casualties, weapons, escalation
**Modules:**
- CL-6: Material Impact Grounding
- FL-7: Risk Context Adjustment
- NL-1: Cause-Effect Chain Analysis
- SL-1: Power and Incentive Mapping

### `conflict_diplomatic`
**Triggers on:** Negotiations, sanctions, treaties, alliances, summits, ceasefires
**Modules:**
- CL-5: Evaluative Symmetry Enforcement
- FL-11: Action-Statement Coherence Audit
- NL-7: Legal and Institutional Legitimacy Audit
- SL-4: Function and Purpose Analysis

### `power_institutional`
**Triggers on:** Elections, governance, judicial actions, corruption, scandals, policy
**Modules:**
- CL-4: Moral and Strategic Fusion Detection
- FL-9: Toxic Label Audit
- SL-1: Power and Incentive Mapping
- SL-2: Institutional Behavior and Enforcement Patterns

### `economic_leverage`
**Triggers on:** Sanctions, trade wars, markets, resources, debt, commodities
**Modules:**
- FL-4: Strategic Relevance and Selection
- FL-5: Scale and Proportion Calibration
- SL-1: Power and Incentive Mapping
- NL-6: Narrative Gaps

### `information_control`
**Triggers on:** Propaganda, media freedom, censorship, disinformation, platform control
**Modules:**
- FL-2: Asymmetrical Amplification Awareness
- FL-3: Source Independence Audit
- CL-7: Coverage Ecosystem Diagnosis
- SL-6: Feedback Systems and Loop Control

### `identity_mobilization`
**Triggers on:** Ethnic/religious tension, historical grievance, protest, nationalism
**Modules:**
- NL-4: Identity, Memory, and Group Interest Framing
- NL-5: Allegory, Analogy, and Symbol Injection
- SL-3: Identity and Memory Exploitation
- CL-3: Narrative Stack Tracking

### `sovereignty_violation`
**Triggers on:** Territorial disputes, invasions, regime change, foreign intervention
**Modules:**
- CL-6: Material Impact Grounding
- NL-7: Legal and Institutional Legitimacy Audit
- FL-11: Action-Statement Coherence Audit
- SL-8: Systemic Blind Spots and Vulnerabilities (already in core, reinforced)

### `humanitarian`
**Triggers on:** Refugees, aid, human rights, civilian harm, displacement
**Modules:**
- FL-5: Scale and Proportion Calibration
- FL-6: Neglected Primary Speech Recognition
- CL-5: Evaluative Symmetry Enforcement
- NL-6: Narrative Gaps

## How It Works

1. **Phase 4.5a** (event summary): LLM picks 1-3 labels from the 8-label set based on event summary + title sample
2. **DB column**: `events_v3.analytical_labels TEXT[]`
3. **RAI analysis**: Union all module sets from the event's labels + 3 core modules → typically 6-8 modules
4. **Dedup**: Some modules appear in multiple labels (e.g. SL-1 in three labels) — only included once

## Examples

| Event | Labels | Total modules |
|---|---|---|
| Iran strikes / Khamenei killed | `conflict_military`, `sovereignty_violation` | CL-0, CL-6, FL-7, FL-11, NL-1, NL-3, NL-7, SL-1, SL-8 = 9 |
| Epstein DOJ review | `power_institutional` | CL-0, CL-4, FL-9, NL-3, SL-1, SL-2, SL-8 = 7 |
| Trump-EU tariff threat | `economic_leverage`, `conflict_diplomatic` | CL-0, CL-5, FL-4, FL-5, FL-11, NL-3, NL-6, NL-7, SL-1, SL-4, SL-8 = 11 (cap at 8-9?) |
| Hong Kong protest crackdown | `identity_mobilization`, `sovereignty_violation` | CL-0, CL-3, CL-6, FL-11, NL-3, NL-4, NL-5, NL-7, SL-3, SL-8 = 10 (cap at 8-9?) |
| Gaza humanitarian crisis | `conflict_military`, `humanitarian` | CL-0, CL-5, CL-6, FL-5, FL-6, FL-7, NL-1, NL-3, NL-6, SL-1, SL-8 = 11 (cap?) |

## Open Questions

- **Max module cap**: When labels union to 10+ modules, should we cap at 8-9 and prioritize? If so, priority = core > first label's modules > second label's modules?
- **Prompt budget**: With optimized prompt format (~2K chars for modules), 8 modules ≈ 4K chars module block. May need to keep module descriptions compact.
- **Sibling groups**: Use union of all sibling events' labels? Or label the group separately?
- **CTM-level analysis**: CTMs span many events — aggregate labels by frequency?

# Event Importance Scoring -- Design Document

**Date:** 2026-03-08
**Status:** Implemented (v1)
**Problem:** The pipeline treats all titles equally. The top 1-2% of genuinely significant stories deserve special treatment: tighter clustering, more cognitive power, higher visibility.

---

## Importance Signals

### Tier 1 -- Mechanical, zero-cost (available at Phase 2-3.1 time)

**1. Multi-source velocity**
Same story appearing from many publishers within a short time window (hours, not days). A 160-dead-children story hits 50 outlets in 2 hours. A routine political statement gets 3-5.

**2. Multi-centroid convergence**
Title matches many geographic centroids. A regional trade deal hits 2-3. A potential WW3 trigger hits 10+.

**3. Action class severity**
Already extracted as T1-T7 action classes. T2 (MILITARY_OPERATION, LAW_ENFORCEMENT_OPERATION) and T7 (SECURITY_INCIDENT, SOCIAL_INCIDENT) with high source counts = almost certainly significant.

**4. Cross-track resonance**
When the same signals (persons, places, orgs) appear simultaneously across Security, Diplomacy, Economy tracks for the same centroid, something big is happening.

### Tier 2 -- Derived from Phase 3.1 labels, cheap

**5. Casualty/scale language in titles**
Mechanical keyword scan for magnitude indicators: numbers + (killed/dead/wounded/displaced/destroyed/collapsed/crashed), "state of emergency", "martial law", "declaration of war", "invasion", "coup". Requires new extraction field.

**6. Actor escalation**
When the actor is a head of state (US_EXECUTIVE, RU_EXECUTIVE) + action class is T2 (military) or T4 (STRATEGIC_REALIGNMENT), this is structurally significant regardless of source count.

**7. Novel entity combinations**
Entities that have never appeared together before in the DB (e.g., US + Iran + MILITARY_OPERATION + a new place name) signal a new development, not routine coverage.

### Tier 3 -- Requires new lightweight computation

**8. Source diversity**
Not just count but diversity. 50 titles from 50 different publishers across 10 languages = genuinely important. 50 titles from 3 publishers = amplification.

**9. Signal density**
Titles about genuinely important events tend to be entity-rich (multiple persons, orgs, places in one title). Routine stories name one actor.

---

## What Changes for High-Importance Events

- **A.** Lower JOIN_THRESHOLD for high-importance clusters (tighter matching, less leakage)
- **B.** Dedicated LLM pass for high-importance clusters (re-examine membership, split/merge with more care)
- **C.** Priority in Phase 4.1 consolidation (high-importance events become anchors first, attracting fragments)
- **D.** UI treatment (pinning, visual weight, alerts)
- **E.** More aggressive catchall rescue (really try to pull related titles out of catchalls into the important cluster)

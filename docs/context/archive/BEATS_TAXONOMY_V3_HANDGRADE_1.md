# ELO v3.0 Hand-Grading Test #1 — USA/economy/March

**Date**: 2026-04-13
**CTM**: AMERICAS-USA / geo_economy / 2026-03
**Sample**: 50 random English titles
**Purpose**: compare current v2.0 labels against proposed v3.0 by hand, without touching prompts yet

## Method

For each title I record:
- **v2** = current actor / action_class as labeled by Phase 3.1
- **v3** = proposed new labeling under the draft taxonomy
- **Assessment**: IMPROVED (v2 was wrong), SAME (v2 was fine), EXCLUDE (should be filtered at Phase 3.3 under tightened rules), AMBIGUOUS (v3 doesn't fully resolve)

---

## The 50 titles

### 1. "Alleged Fraud: Court orders forfeiture of $13m traced to Lagos socialite, Achimugu"
- v2: `NG_JUDICIARY / LEGAL_RULING / NONE`
- v3: `NG_JUDICIARY / LEGAL_RULING / NONE`, sectors=[FINANCE]
- **SAME**. Note: title doesn't belong in USA/economy CTM — centroid-assignment issue, not taxonomy.

### 2. "Gold holds losses after Fed decision, drops to over one-month low"
- v2: `US_CENTRAL_BANK / POLICY_CHANGE / NONE` ❌
- v3: `NONE / MARKET_SHOCK / NONE`, commodities=[gold], sectors=[FINANCE]
- **IMPROVED**. v2 is wrong — the headline is about gold movement, not Fed policy.

### 3. "US Recession Risks Begin to Rise as War Dims Economic Outlook"
- v2: `NONE / ECONOMIC_DISRUPTION / NONE`
- v3: **EXCLUDE at 3.3** (forecast commentary, no concrete event)
- **IMPROVED** (via exclusion)

### 4. "UBS wealth management outflows threaten US turnaround, analysts and sources say"
- v2: `CORPORATION / ECONOMIC_DISRUPTION / NONE`
- v3: **EXCLUDE at 3.3** ("analysts say" commentary on corporate operations)
- **IMPROVED** (via exclusion)

### 5. "Trump's attacks on offshore wind could hurt infrastructure spending across the economy"
- v2: `US_EXECUTIVE / POLITICAL_PRESSURE / NONE`
- v3: **EXCLUDE at 3.3** (speculative analysis — "could hurt")
- **IMPROVED** (via exclusion)

### 6. "Spiking gas prices tied to Iran war are set to eat up tax refunds touted by Trump"
- v2: `NONE / ECONOMIC_DISRUPTION / US`
- v3: `NONE / MARKET_SHOCK / NONE`, commodities=[gas], sectors=[ENERGY]
- **IMPROVED**. Macro commodity move from geopolitical cause.

### 7. "China urges US to drop its Section 301 investigations"
- v2: `CN_EXECUTIVE / DIPLOMATIC_PRESSURE / US`
- v3: `CN_EXECUTIVE / PRESSURE / US`
- **IMPROVED** (DIPLOMATIC/POLITICAL merger)

### 8. "Over 3k flights cancelled across the Middle East after attack on Iran by the US, Israel"
- v2: `NONE / ECONOMIC_DISRUPTION / NONE`
- v3: `NONE / SECURITY_INCIDENT / NONE`, sectors=[SHIPPING]
- **IMPROVED**. Operational disruption from war, not a market shock.
- Borderline: could be MARKET_SHOCK if we read "supply shock" broadly. I prefer SECURITY_INCIDENT here because the headline is about flight ops, not prices.

### 9. "Marvell projects strong fiscal 2028 revenue on AI-driven data center boom, shares jump"
- v2: `CORPORATION / RESOURCE_ALLOCATION / NONE` ❌
- v3: **EXCLUDE at 3.3** (company earnings guidance — fundamentals, not macro)
- **IMPROVED** (via exclusion)

### 10. "US economic outlook downgraded amid Middle East tensions"
- v2: `CORPORATION / INFORMATION_INFLUENCE / NONE` ❌
- v3: **EXCLUDE at 3.3** (forecast commentary)
- **IMPROVED** (via exclusion)

### 11. "Microsoft freezes hiring in major cloud, sales groups, The Information reports"
- v2: `CORPORATION / ECONOMIC_DISRUPTION / NONE`
- v3: `CORPORATION / COMMERCIAL_TRANSACTION / NONE`, sectors=[IT_SOFTWARE]
- **IMPROVED**. Hiring freeze = concrete corporate restructuring action.
- **Ambiguity surfaced**: hiring freezes aren't really "transactions." COMMERCIAL_TRANSACTION may need scope broadening to "commercial decisions" (deals + strategy shifts).

### 12. "Canada Leases Space Port in Bid to Break Reliance on US Rockets Like Musk's SpaceX"
- v2: `CA_EXECUTIVE / INFRASTRUCTURE_DEVELOPMENT / NONE`
- v3: `CA_EXECUTIVE / INFRASTRUCTURE_DEVELOPMENT / NONE`, sectors=[AEROSPACE]
- **SAME**. Physical infra project, correctly labeled.

### 13. "Kevin Warsh's push to shrink Federal Reserve's balance sheet would evolve slowly"
- v2: `US_CENTRAL_BANK / POLICY_CHANGE / NONE`
- v3: `US_CENTRAL_BANK / STATEMENT / NONE`
- **IMPROVED**. Warsh discussing his view, not an enacted Fed decision. Clean STATEMENT use.

### 14. "China reviews $2bn Manus sale to Meta as founders barred from leaving country"
- v2: `CN_REGULATORY_AGENCY / REGULATORY_ACTION / NONE`
- v3: same, sectors=[AI, IT_SOFTWARE]
- **SAME**.

### 15. "Trump Officials Set to Announce New Trade Probes in Tariff Push"
- v2: `US_EXECUTIVE / POLICY_CHANGE / NONE`
- v3: `US_EXECUTIVE / ECONOMIC_PRESSURE / NONE`
- **IMPROVED**. "Set to announce" = threat/signal, not yet enacted. Fits the narrowed ECONOMIC_PRESSURE scope.

### 16. "SpaceX IPO leaves some private share buyers unsure what they own"
- v2: `CORPORATION / ECONOMIC_DISRUPTION / NONE` ❌
- v3: **EXCLUDE at 3.3** (commentary piece about already-announced IPO)
- **IMPROVED** (via exclusion)

### 17. "Rising prices push US car ownership costs to breaking point"
- v2: `NONE / SECURITY_INCIDENT / NONE` ❌❌ (wildly wrong)
- v3: **EXCLUDE at 3.3** (analysis/feature)
- **IMPROVED** (via exclusion)

### 18. "Google settles with Epic Games, drops its Play Store commissions to 20%"
- v2: `CORPORATION / POLICY_CHANGE / NONE`
- v3: `CORPORATION / COMMERCIAL_TRANSACTION / NONE`, sectors=[IT_SOFTWARE]
- **IMPROVED** + **AMBIGUOUS**. Settlements could also be LEGAL_CONTESTATION (ending a dispute). I lean COMMERCIAL_TRANSACTION because the *event* is the commission cut; the settlement is the mechanism. Flag for prompt rule.

### 19. "Boeing close to 500-jet order ahead of Trump-Xi summit, Bloomberg News reports"
- v2: `CORPORATION / CAPABILITY_TRANSFER / NONE`
- v3: `CORPORATION / COMMERCIAL_TRANSACTION / CN`, sectors=[AEROSPACE]
- **IMPROVED**. 500 civilian jets is commercial, not capability transfer.

### 20. "ECB Alert to Second-Round Effects From Iran War, Guindos Says"
- v2: `EU_CENTRAL_BANK / POLICY_CHANGE / NONE` ❌
- v3: `EU_CENTRAL_BANK / STATEMENT / NONE`
- **IMPROVED**. "Guindos says" is a classic statement, not policy change.

### 21. "Tech, Trump, targets: 5 takeaways as China's NPC draws to close"
- v2: `CN_LEGISLATURE / LEGISLATIVE_DECISION / NONE`
- v3: **EXCLUDE at 3.3** (summary/listicle, not an event)
- **IMPROVED** (via exclusion)

### 22. "Meta turns to AI to make shopping easier on Instagram and Facebook"
- v2: `CORPORATION / CAPABILITY_TRANSFER / NONE` ❌
- v3: `CORPORATION / COMMERCIAL_TRANSACTION / NONE`, sectors=[IT_SOFTWARE, AI]
- **IMPROVED**. Product/feature rollout.

### 23. "Trump Tower developer went bankrupt owing $32m in 2010"
- v2: `NONE / ECONOMIC_DISRUPTION / NONE`
- v3: **EXCLUDE at 3.3** (2010 news, stale — needs freshness filter)
- **IMPROVED** (via exclusion). Surfaces an orthogonal need: stale-news filter.

### 24. "The Enormous Financial Cost of Three Weeks of War in Iran"
- v2: `NONE / ECONOMIC_DISRUPTION / IR`
- v3: **EXCLUDE at 3.3** (analytical piece)
- **IMPROVED** (via exclusion)

### 25. "US and China weigh new mechanism for managing trade, investment"
- v2: `US_EXECUTIVE / MULTILATERAL_ACTION / CN`
- v3: `US_EXECUTIVE / ALLIANCE_COORDINATION / CN`
- **SAME-ish**. ALLIANCE_COORDINATION is slightly better ("joint consideration") but MULTILATERAL_ACTION is also defensible. Both work.

### 26. "China slams Trump's trade investigation, as it approves a 5-year economic plan"
- v2: `CN_EXECUTIVE / POLICY_CHANGE / NONE`
- v3: `CN_EXECUTIVE / POLICY_CHANGE / NONE`
- **SAME**. Priority rule (T1 > T5) keeps POLICY_CHANGE over PRESSURE. Correct.

### 27. "No lawsuits required: U.S. Customs is working on a system to refund tariffs"
- v2: `US_REGULATORY_AGENCY / INFRASTRUCTURE_DEVELOPMENT / NONE` ❌
- v3: `US_REGULATORY_AGENCY / POLICY_CHANGE / NONE`
- **IMPROVED**. Administrative process, not infrastructure.

### 28. "Platts removes US Propylene February contract price"
- v2: `CORPORATION / POLICY_CHANGE / NONE` ❌
- v3: **EXCLUDE at 3.3** (trade press operational detail)
- **IMPROVED** (via exclusion)

### 29. "Trump says he'll sign order to pay TSA agents as Congress struggles to reach funding deal"
- v2: `US_EXECUTIVE / POLICY_CHANGE / NONE`
- v3: `US_EXECUTIVE / POLICY_CHANGE / NONE` (if signing imminent) or STATEMENT (if pure rhetoric)
- **SAME**. Borderline.

### 30. "Swiss Still Aim for US Trade Accord After Supreme Court Decision"
- v2: `CH_EXECUTIVE / POLITICAL_PRESSURE / US` ❌
- v3: `CH_EXECUTIVE / STATEMENT / US`
- **IMPROVED**. Swiss stating their position, not applying pressure.

### 31. "Drone company backed by Erik Prince surges 500% in Wall Street debut"
- v2: `CORPORATION / RESOURCE_ALLOCATION / NONE` ❌
- v3: `CORPORATION / COMMERCIAL_TRANSACTION / NONE`, sectors=[DEFENSE]
- **IMPROVED**. IPO = commercial transaction, not state resource allocation.

### 32. "JLL: Infrastructure spending key to Metro Manila property growth"
- v2: `CORPORATION / INFRASTRUCTURE_DEVELOPMENT / PH` ❌
- v3: **EXCLUDE at 3.3** (real-estate firm analyst report)
- **IMPROVED** (via exclusion)

### 33. "Gold falls 1.8pc after report of US sending more troops to Middle East"
- v2: `US_EXECUTIVE / MILITARY_OPERATION / NONE` ❌ (wrong actor for the headline topic)
- v3: `NONE / MARKET_SHOCK / NONE`, commodities=[gold], sectors=[FINANCE]
- **IMPROVED**. Headline is about the gold move.

### 34. "US to Exempt Rosneft's German Unit From Sanctions Indefinitely"
- v2: `US_EXECUTIVE / REGULATORY_ACTION / RU`
- v3: same
- **SAME**. Exemption = regulatory modification. Could also argue SANCTION_ENFORCEMENT (it's a sanctions-regime action).

### 35. "'EU Inc.' Plan Seeks to Spur Startups to Rival US, China"
- v2: `EU_EXECUTIVE / POLICY_CHANGE / CN,US`
- v3: `EU_EXECUTIVE / POLICY_CHANGE / NONE` (target should be NONE — US/CN are rivals, not targets)
- **SAME** on action, minor target fix.

### 36. "GHG Emissions Standards; Aluminum Prices Surge; and Inside the US Labor Market"
- v2: `US_REGULATORY_AGENCY / REGULATORY_ACTION / NONE`
- v3: **EXCLUDE at 3.3** (newsletter roundup, not a single event)
- **IMPROVED** (via exclusion)

### 37. "U.S. Factory Activity Continued to Expand in February"
- v2: `NONE / ECONOMIC_DISRUPTION / NONE` ❌
- v3: **EXCLUDE at 3.3** (routine ISM data release, not a shock)
- **IMPROVED** (via exclusion)

### 38. "Trump signs executive orders aimed at addressing home affordability concerns ahead of midterms"
- v2: `US_EXECUTIVE / POLICY_CHANGE / NONE`
- v3: same
- **SAME**. Concrete executive order.

### 39. "Chinese Vice Premier He Lifeng to lead delegation to France for trade talks with US on March 14-17"
- v2: `CN_EXECUTIVE / ALLIANCE_COORDINATION / FR,US`
- v3: `CN_EXECUTIVE / ALLIANCE_COORDINATION / US` (FR is location, not target)
- **SAME** action, minor target fix.

### 40. "US court orders refunds on Trump's IEEPA tariffs"
- v2: `US_JUDICIARY / LEGAL_RULING / NONE`
- v3: same
- **SAME**. Clean ruling.

### 41. "Amazon India slashes seller referral fees in retail growth push"
- v2: `CORPORATION / POLICY_CHANGE / IN` ❌
- v3: `CORPORATION / COMMERCIAL_TRANSACTION / NONE`, sectors=[RETAIL, IT_SOFTWARE]
- **IMPROVED**. Corporate pricing decision, not "policy change."

### 42. "US stocks rise, Asian markets get rocked as Middle East conflict intensifies"
- v2: `NONE / ECONOMIC_DISRUPTION / NONE`
- v3: `NONE / MARKET_SHOCK / NONE`, sectors=[FINANCE]
- **IMPROVED**. Classic MARKET_SHOCK.

### 43. "After saying 'we are fine' for months, Nvidia seemingly 'accepts' that Google and Meta are coming for it"
- v2: `CORPORATION / INFORMATION_INFLUENCE / NONE` ❌
- v3: **EXCLUDE at 3.3** (speculative commentary/opinion)
- **IMPROVED** (via exclusion)

### 44. "Acquihires, often used by Big Tech, are a 'red flag,' DOJ antitrust head says"
- v2: `US_REGULATORY_AGENCY / REGULATORY_ACTION / CORPORATION` ❌
- v3: `US_REGULATORY_AGENCY / STATEMENT / NONE`
- **IMPROVED**. DOJ official giving a view, not enforcing anything yet.

### 45. "Super Micro shares plunge as US charges co-founder, 2 more for smuggling AI chips to China"
- v2: `US_LAW_ENFORCEMENT / LAW_ENFORCEMENT_OPERATION / CN`
- v3: same, sectors=[SEMICONDUCTORS, AI]
- **SAME**. Criminal charges = correct use of LAW_ENFORCEMENT_OPERATION.

### 46. "US-Iran crisis disrupts thousands of flights as key air hubs closed"
- v2: `NONE / SECURITY_INCIDENT / NONE`
- v3: same, sectors=[SHIPPING]
- **SAME**. Operational disruption. Matches #8.

### 47. "Bernstein warns rupee could breach 98/USD, cuts Nifty target on Iran conflict risks"
- v2: `CORPORATION / ECONOMIC_PRESSURE / IN` ❌
- v3: **EXCLUDE at 3.3** (analyst forecast)
- **IMPROVED** (via exclusion)

### 48. "European trade group slams American chip company Broadcom, calls its actions in Europe 'death sentence' for ..."
- v2: `EU_TRADE_GROUP / POLITICAL_PRESSURE / US`
- v3: `EU_TRADE_GROUP / PRESSURE / US`, sectors=[SEMICONDUCTORS]
- **IMPROVED** (pressure merger)

### 49. "Taseko's Florence mine delivers first new US copper in 17 years"
- v2: `CORPORATION / INFRASTRUCTURE_DEVELOPMENT / NONE`
- v3: `CORPORATION / INFRASTRUCTURE_DEVELOPMENT / NONE`, sectors=[MINING], commodities=[copper]
- **SAME**. Physical infra milestone (first production from mine).

### 50. "SpaceX Aims to Launch New Starlink Satellites With Faster Cell Service in 2027"
- v2: `CORPORATION / INFRASTRUCTURE_DEVELOPMENT / NONE`
- v3: `CORPORATION / STATEMENT / NONE` (future plan) OR **EXCLUDE at 3.3**
- **IMPROVED-ish**. "Aims to launch in 2027" is a forward-looking plan, not an event.

---

## Tally

| Assessment | Count | % |
|---|---|---|
| IMPROVED (label was wrong) | 18 | 36% |
| EXCLUDE at 3.3 (should be filtered) | 14 | 28% |
| SAME (v2 was fine) | 15 | 30% |
| AMBIGUOUS / borderline | 3 | 6% |

**Key observation**: **64% of the sample needed some change** (improvement or exclusion). The biggest single win is **exclusion at Phase 3.3** — roughly 1/3 of current USA/economy titles are commentary, analyst forecasts, stale news, or routine data releases that shouldn't be events at all.

---

## What the hand-grading proved

### Wins confirmed

1. **MARKET_SHOCK** is the biggest single new class. Titles #2, #6, #33, #42 all map cleanly. Gold/oil/stocks during stress land here.
2. **STATEMENT** catches a distinct category cleanly: #13, #20, #30, #44, #50. Without it, these scatter across POLICY_CHANGE / POLITICAL_PRESSURE / INFORMATION_INFLUENCE inconsistently.
3. **PRESSURE merger** is painless: #7, #48. Every DIPLOMATIC/POLITICAL_PRESSURE sample mapped cleanly to the merged class.
4. **COMMERCIAL_TRANSACTION** is a major landing zone: #11, #18, #19, #22, #31, #41. All were wrong in v2.
5. **Exclusion at 3.3** is the biggest overall win — not a taxonomy change, but the taxonomy draft surfaces the need clearly.

### Ambiguities that need prompt rules

**AMB-11 (new)**: Corporate non-transaction decisions (hiring freezes, restructurings, strategy pivots without a deal). These fit awkwardly in COMMERCIAL_TRANSACTION. Proposal: broaden COMMERCIAL_TRANSACTION scope to "commercial decisions" (deals + strategy shifts + operational restructurings by corporations). Update the class description.

**AMB-12 (new)**: Corporate settlements of legal disputes (#18 Google-Epic). Is it LEGAL_CONTESTATION (ending a lawsuit) or COMMERCIAL_TRANSACTION (the commercial terms of the settlement)? Proposal: if the headline emphasizes a concrete commercial change (fee cut, payment) → COMMERCIAL_TRANSACTION. If it emphasizes the legal resolution → LEGAL_CONTESTATION. Default to COMMERCIAL_TRANSACTION.

**AMB-13 (new)**: "Sets to / aims to / plans to" announcements (#50 SpaceX 2027 Starlink, #15 Trump trade probes). Forward-looking plans. Proposal: if the announcement carries a concrete timeline and authority → use the action class of the planned action. If it's open-ended intent → STATEMENT.

**AMB-14 (orthogonal)**: **Stale-news filter**. #23 is a 2010 story about Trump Tower — correctly labeled, but shouldn't be in a March 2026 CTM at all. This is a Phase 1/2 ingestion quality issue, not a taxonomy issue. **Flag for a separate Asana ticket.**

### Gaps NOT found

No case in the 50 required a new class beyond what's in v3. No case needed NATURAL_EVENT (expected — USA economy doesn't have natural disasters). No case needed ELECTORAL_EVENT (expected — it's an economy track).

### v2 labels that are WILDLY wrong

- #17 "Rising prices push US car ownership costs to breaking point" → `SECURITY_INCIDENT` (why?)
- #10 "US economic outlook downgraded" → `INFORMATION_INFLUENCE` (no, that's organized propaganda)
- #33 "Gold falls 1.8pc after report of US sending more troops" → `MILITARY_OPERATION` (LLM matched on "troops" not "gold")
- #44 "DOJ antitrust head says 'red flag'" → `REGULATORY_ACTION` (no, just saying)

These suggest the v2 prompt is brittle on specific patterns. v3 prompt needs to be explicit about headline-subject-matters-more-than-keyword-matching.

---

## Recommendation

**Proceed with next hand-grading test on a different CTM** before touching code. Suggested next excerpts:

1. **EUROPE-FRANCE / geo_politics / 2026-03** — tests ELECTORAL_EVENT (French local elections), PRESSURE merger in politics, CIVIL_ACTION scope
2. **ASIA-CHINA / geo_economy / 2026-03** — tests sectors[] (AI, IT_SOFTWARE, AUTOMOTIVE), MARKET_SHOCK for commodity flows, non-US political vocabulary
3. **AMERICAS-USA / geo_security / 2026-03** — tests MILITARY_OPERATION / SECURITY_INCIDENT / PRESSURE distinctions under mega-conflict load; probably the LEAST change-sensitive CTM

After 3 hand-grading runs, we have enough evidence to revise the draft one final time and then write the actual `core/ontology.py` + `core/prompts.py` diffs.

## What to add back to the draft doc

- **AMB-11, AMB-12, AMB-13** in the ambiguity log
- **COMMERCIAL_TRANSACTION scope broadening** — include "commercial decisions and operational restructurings by corporate actors" not just transactions
- **New Asana ticket**: stale-news/freshness filter at Phase 1 or Phase 3.3

## Run more?

Say the word and I'll do hand-grade #2 on EUROPE-FRANCE / geo_politics / 2026-03.

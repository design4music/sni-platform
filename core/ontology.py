"""
Event Label Ontology (ELO) v3.0

Defines the complete ontology for structured event labeling:
- ACTION_CLASSES: 7-tier action hierarchy (T1-T7)
- DOMAINS: 7 thematic domains
- CONTROLLED_ACTORS: 17 institution types
- PRIORITY_RULES: Text block for LLM prompt guidance

Label format: PRIMARY_ACTOR -> ACTION_CLASS -> DOMAIN (-> OPTIONAL_TARGET)

v3.0 changes (2026-04-13, see docs/context/BEATS_TAXONOMY_V3_DRAFT.md):
- ADDED: ELECTORAL_EVENT (T1), COMMERCIAL_TRANSACTION (T3), STATEMENT (T5), NATURAL_EVENT (T7)
- MERGED: POLITICAL_PRESSURE + DIPLOMATIC_PRESSURE -> PRESSURE (T5)
- RENAMED: COLLECTIVE_PROTEST -> CIVIL_ACTION (T6), ECONOMIC_DISRUPTION -> MARKET_SHOCK (T7)
- DROPPED: SOCIAL_INCIDENT (scope absorbed by CIVIL_ACTION/NATURAL_EVENT/SECURITY_INCIDENT)
- NARROWED definitions: RESOURCE_ALLOCATION (state only), INFRASTRUCTURE_DEVELOPMENT (physical/digital infra),
  POLICY_CHANGE (government only), ECONOMIC_PRESSURE (threats only, vs SANCTION_ENFORCEMENT for enacted),
  INFORMATION_INFLUENCE (organized ops only)

v3.0.1 (2026-04-13, same day — after 99-title pilot review):
- MERGED: LEGAL_RULING + LEGAL_CONTESTATION -> LEGAL_ACTION (T1). The procedural
  split (suit filing vs court decision) was a source of LLM confusion; Beats
  treats both as one lane anyway.
- Prompt rules added to Phase 3.1 NON_STRATEGIC scope: routine govt statistics
  (CPI/GDP/jobs releases), trade probes go to REGULATORY_ACTION not LEGAL,
  non-English content classified by meaning not language.

Total count: 24 classes (was 25 in v3.0 draft, 23 in v2.0 original).
"""

ONTOLOGY_VERSION = "ELO_v3.0.1"

# =============================================================================
# ACTION CLASSES - 7-tier hierarchy (higher tier wins in priority)
# =============================================================================

# Tier 1: FORMAL DECISION - Binding institutional outputs
ACTION_CLASSES_T1 = {
    "LEGAL_ACTION": "Legal proceedings: lawsuits filed, appeals, injunctions, court rulings, dismissals, verdicts, judgments. One lane covering the full arc of a legal fight.",
    "LEGISLATIVE_DECISION": "Law/resolution passage or rejection",
    "POLICY_CHANGE": "Government executive/regulatory policy adoption",
    "REGULATORY_ACTION": "Licensing, approval, certification, trade probes (Section 301/232), anti-dumping investigations",
    "ELECTORAL_EVENT": "Elections, referendums, primaries, vote-driven transitions",
}

# Tier 2: COERCIVE ENFORCEMENT - Use of force or coercive power
ACTION_CLASSES_T2 = {
    "MILITARY_OPERATION": "Armed force deployment, strikes, exercises",
    "LAW_ENFORCEMENT_OPERATION": "Arrests, raids, border enforcement",
    "SANCTION_ENFORCEMENT": "Enacted sanctions: seizures, imposed tariffs, trade restrictions",
}

# Tier 3: RESOURCE & CAPABILITY - Material commitments
ACTION_CLASSES_T3 = {
    "RESOURCE_ALLOCATION": "State budgets, aid, sovereign funding",
    "INFRASTRUCTURE_DEVELOPMENT": "Physical/digital infra: ports, rail, grids, data centers, pipelines, cables",
    "CAPABILITY_TRANSFER": "Arms sales, tech transfer, training between governments",
    "COMMERCIAL_TRANSACTION": "Corporate deals: M&A, IPOs, fundraising, contracts, product launches, market exits, restructurings",
}

# Tier 4: COORDINATION - Multi-party alignment
ACTION_CLASSES_T4 = {
    "ALLIANCE_COORDINATION": "Bilateral meetings, calls, summits, joint statements (2 parties)",
    "STRATEGIC_REALIGNMENT": "Partnership shifts, bloc formation/exit",
    "MULTILATERAL_ACTION": "UN/IGO resolutions, treaty negotiations (3+ parties or IGO)",
}

# Tier 5: PRESSURE & INFLUENCE - Non-binding pressure
ACTION_CLASSES_T5 = {
    "PRESSURE": "Verbal coercion: demands, ultimatums, condemnations, recalls, notes",
    "ECONOMIC_PRESSURE": "Financial threats: tariff warnings, sanction threats, funding freeze threats",
    "STATEMENT": "Non-coercive statements by named figures/institutions: speeches, interviews, forecasts, op-eds, 'X says Y'",
    "INFORMATION_INFLUENCE": "Organized propaganda, disinformation ops, state media campaigns",
}

# Tier 6: CONTESTATION - Resistance and opposition
ACTION_CLASSES_T6 = {
    "INSTITUTIONAL_RESISTANCE": "Vetoes, filibusters, procedural blocks",
    "CIVIL_ACTION": "Demonstrations, strikes, rallies, walkouts, civil disobedience",
}

# Tier 7: INCIDENTS - Last resort (no clear institutional actor)
ACTION_CLASSES_T7 = {
    "SECURITY_INCIDENT": "Attacks, accidents, breaches without clear actor",
    "NATURAL_EVENT": "Floods, quakes, fires, storms, epidemics, famines, tsunamis",
    "MARKET_SHOCK": "Macro-driven asset/commodity/currency moves (>=2 sigma), directionless",
}

# Combined set of all action classes
ACTION_CLASSES = {
    **ACTION_CLASSES_T1,
    **ACTION_CLASSES_T2,
    **ACTION_CLASSES_T3,
    **ACTION_CLASSES_T4,
    **ACTION_CLASSES_T5,
    **ACTION_CLASSES_T6,
    **ACTION_CLASSES_T7,
}

# Tier lookup for priority resolution
ACTION_CLASS_TIERS = {}
for ac in ACTION_CLASSES_T1:
    ACTION_CLASS_TIERS[ac] = 1
for ac in ACTION_CLASSES_T2:
    ACTION_CLASS_TIERS[ac] = 2
for ac in ACTION_CLASSES_T3:
    ACTION_CLASS_TIERS[ac] = 3
for ac in ACTION_CLASSES_T4:
    ACTION_CLASS_TIERS[ac] = 4
for ac in ACTION_CLASSES_T5:
    ACTION_CLASS_TIERS[ac] = 5
for ac in ACTION_CLASSES_T6:
    ACTION_CLASS_TIERS[ac] = 6
for ac in ACTION_CLASSES_T7:
    ACTION_CLASS_TIERS[ac] = 7


# =============================================================================
# DOMAINS - 7 thematic domains
# =============================================================================

DOMAINS = [
    "GOVERNANCE",  # Domestic politics, elections, legislation
    "ECONOMY",  # Trade, finance, markets, fiscal policy
    "SECURITY",  # Military, defense, terrorism, crime
    "FOREIGN_POLICY",  # Diplomacy, international relations
    "SOCIETY",  # Social issues, demographics, migration
    "TECHNOLOGY",  # Tech policy, cyber, innovation
    "MEDIA",  # Information, press, communications
]


# =============================================================================
# INDUSTRIES - Closed vocabulary for economic/industrial entity tagging (ELO v3.0.1)
# =============================================================================
# Distinct from DOMAINS (above) and the per-title SECTOR/SUBJECT fields used
# for track routing. INDUSTRIES[] is a multi-value tag on title_labels that
# captures which industries a title is materially about. Populated by the LLM
# only when the content is materially about a specific industry's activity.

INDUSTRIES = {
    "AEROSPACE": "Aircraft, satellites, space launch, military aerospace",
    "AI": "AI labs, frontier models, training infra, GPU datacenters when AI-specific",
    "AUTOMOTIVE": "Car manufacturers, ICE/ICEV/EV vehicles excluding battery tech",
    "BIOTECH": "Biotechnology firms, gene therapy, medical devices",
    "DEFENSE": "Arms manufacturers, defense contractors, weapons systems",
    "ENERGY": "Oil, gas, nuclear, electricity broadly",
    "FINANCE": "Banks, funds, markets, insurance, crypto, payments",
    "FOOD_AGRI": "Food, agriculture, agri commodities, fertilizers",
    "GREEN_TECH": "EV batteries, solar, wind, hydrogen, grid storage",
    "IT_SOFTWARE": "Software companies, cloud, SaaS, platforms (excluding AI and media)",
    "MEDIA": "News media, social platforms, streaming (strategic stories only - ownership, regulation, influence, censorship)",
    "MINING": "Metals, rare earths, minerals extraction",
    "PHARMA": "Drugs, medical devices, healthcare systems",
    "RETAIL": "Consumer retail, e-commerce commerce (not ads)",
    "SEMICONDUCTORS": "Chips, foundries, EDA tools, memory",
    "SHIPPING": "Maritime, logistics, ports, freight, aviation freight",
    "TELECOMS": "Carriers, 5G, undersea cables, satellites, broadband",
    "OTHER": "Does not fit any of the above industries",
}


def get_industries_for_prompt() -> str:
    """Format industries for LLM prompt."""
    lines = []
    for ind, desc in INDUSTRIES.items():
        lines.append("  - {}: {}".format(ind, desc))
    return "\n".join(lines)


def validate_industry(industry: str) -> bool:
    return industry in INDUSTRIES


# =============================================================================
# CONTROLLED ACTORS - 17 institution types
# =============================================================================

CONTROLLED_ACTORS = {
    # State Institutions
    "STATE_EXECUTIVE": "President, PM, cabinet, executive agencies",
    "STATE_LEGISLATURE": "Parliament, congress, legislative bodies",
    "STATE_JUDICIARY": "Courts, tribunals, judicial bodies",
    "CENTRAL_BANK": "Monetary authority, reserve bank",
    "REGULATORY_AGENCY": "Independent regulators, commissions",
    "ARMED_FORCES": "Military, defense forces, national guard",
    "INTELLIGENCE_SERVICE": "Intelligence agencies, security services",
    "LAW_ENFORCEMENT": "Police, border patrol, customs",
    # International Organizations
    "IGO": "Intergovernmental organization (UN, EU, AU, etc.)",
    "INTERNATIONAL_COURT": "ICJ, ICC, ECHR, WTO dispute body",
    # Non-State Actors
    "POLITICAL_PARTY": "Registered political parties",
    "CORPORATION": "Business entities, companies",
    "NGO": "Non-governmental organizations, civil society",
    "LABOR_UNION": "Trade unions, worker organizations",
    "MEDIA_OUTLET": "News organizations, broadcasters",
    "ARMED_GROUP": "Militias, rebel groups, terrorist orgs",
    # Collective
    "POPULATION": "General public, protesters, voters (collective action)",
}


# =============================================================================
# PRIORITY RULES - Embedded in LLM prompt
# =============================================================================

PRIORITY_RULES = """
PRIORITY RULES:

1. TIER: lower tier wins (T1>T2>T3>T4>T5>T6>T7). Court ruling beats protest; military op beats pressure.

2. ENACTED > THREATENED. "Imposes tariff"->SANCTION_ENFORCEMENT. "Threatens tariff"->ECONOMIC_PRESSURE. "Signs bill"->LEGISLATIVE_DECISION. "Proposes bill"->STATEMENT or LEGISLATIVE_DECISION if passage imminent.

3. CONCRETE > ABSTRACT. "Arrests 10"->LAW_ENFORCEMENT_OPERATION. "Investigates group"->STATEMENT. "Deploys troops"->MILITARY_OPERATION. "Considers deployment"->STATEMENT.

4. ASPIRATIONAL LANGUAGE -> STATEMENT. Keywords: vows, pledges, says, hopes, sets sight, plans, aims, warns, urges, eyes, seeks -- unless tied to an enacted decision. Named figure OR institution attribution required.

5. ELECTIONS -> ELECTORAL_EVENT ALWAYS. Votes, runoffs, primaries, mayoral/parliamentary/presidential elections, results, transitions by vote. NEVER use CIVIL_ACTION or LEGISLATIVE_DECISION for elections.

6. BILATERAL vs MULTILATERAL. "X speaks to Y", "X meets Y", "X holds talks with Y" -> ALLIANCE_COORDINATION (2 parties). MULTILATERAL_ACTION only for 3+ parties or IGO (UN/NATO/WTO/G7). Meetings/calls are NEVER PRESSURE unless content is coercive.

7. CORPORATE vs STATE.
   - State + budget/aid -> RESOURCE_ALLOCATION
   - Corporate deals, M&A, IPOs, product launches, restructurings, hiring changes -> COMMERCIAL_TRANSACTION
   - Corporation + POLICY_CHANGE is an error; use COMMERCIAL_TRANSACTION
   - Corporation + INFRASTRUCTURE_DEVELOPMENT valid ONLY for physical/digital infra (data centers, mines, factories, pipelines, cables)

8. MARKET_SHOCK (directionless, macro-driven only).
   - Gold/oil/wheat/currency surging or crashing on war, sanctions, Fed, supply shock -> MARKET_SHOCK
   - Routine company-specific stock moves -> sector=NON_STRATEGIC
   - Pair with commodities[] (gold/oil/CNY/USD) where relevant

9. CIVIL_ACTION: only organized collective civil action (demonstrations, strikes, walkouts, civil disobedience, rallies). NOT elections, NOT polls, NOT mayoral wins.

10. T7 INCIDENTS = last resort. Known actor -> MILITARY/LAW_ENFORCEMENT. Unknown actor or accident -> SECURITY_INCIDENT. Natural cause -> NATURAL_EVENT. SECURITY_INCIDENT is NOT a fallback for commentary/profiles/obituaries (those -> sector=NON_STRATEGIC).

11. ACTOR: individuals -> institutions. "Biden signs" -> US_EXECUTIVE. "Powell speaks" -> US_CENTRAL_BANK. Country prefix for state (US_, RU_, CN_, FR_, DE_). IGOs bare (UN, NATO, EU). Corporations by name or CORPORATION.

12. LEGAL_ACTION covers the whole legal arc: suits filed, appeals, injunctions, rulings, dismissals, verdicts, judgments. One lane. "Judge dismisses X" -> LEGAL_ACTION. "24 states sue Y" -> LEGAL_ACTION. Both are the same fight.

13. TRADE PROBES (Section 301, Section 232, anti-dumping investigations, CFIUS reviews, forced-labor probes) -> REGULATORY_ACTION, NOT LEGAL_ACTION. These are administrative/regulatory instruments, not lawsuits.

14. ROUTINE GOVERNMENT STATISTICS (CPI, GDP, jobs/employment reports, trade balances, forex reserves, factory activity, credit numbers) -> sector=NON_STRATEGIC unless the release is described as a shock: "fastest in X years", "worst since 2008", "collapses", "record". No named actor "said" a statistic; do not label as STATEMENT.

15. NON-ENGLISH HEADLINES: classify by the content's meaning, not the language. A Japanese or Arabic headline about a legitimate commercial event is COMMERCIAL_TRANSACTION with sector=ECONOMY, not NON_STRATEGIC. Language is never a reason to mark NON_STRATEGIC.
"""


# =============================================================================
# TARGET NORMALIZATION RULES - For consistent clustering
# =============================================================================

TARGET_RULES = """
TARGET NORMALIZATION (CRITICAL FOR CLUSTERING):

1. COUNTRIES -> ISO 2-LETTER CODE:
   - France, French government, FR_EXECUTIVE -> FR
   - China, Beijing, Chinese -> CN
   - Iran, Tehran, Iranian -> IR
   - India, New Delhi -> IN
   - Denmark, Danish -> DK
   - Greenland -> GL (special case, use GL not DK)

2. REGIONS -> CANONICAL NAME:
   - Europe, European nations, EU countries, European countries -> EU
   - European Union institutions -> EU
   - NATO members, NATO allies -> NATO
   - BRICS nations -> BRICS
   - G7 countries -> G7

3. MULTI-TARGET -> COMMA-SEPARATED CODES (alphabetical):
   - "sanctions on Russia and China" -> CN,RU
   - "aid to Ukraine and Israel" -> IL,UA
   - Maximum 3 targets; if more, use most prominent

4. INSTITUTIONS AS TARGETS -> ACTOR FORMAT:
   - "pressure on the Fed" -> US_CENTRAL_BANK
   - "criticism of Congress" -> US_LEGISLATURE
   - "sanctions on Russian military" -> RU_ARMED_FORCES

5. DESCRIPTIVE PHRASES -> CORE ENTITY ONLY:
   - "Iran's trading partners" -> IR (the action is about Iran)
   - "countries opposing Greenland takeover" -> null (too vague, omit target)
   - "European allies" -> EU

6. TERRITORIES/DISPUTES:
   - Taiwan -> TW
   - Greenland -> GL
   - Gaza, Palestinian territories -> PS
   - Crimea, Donbas -> UA (contested, use internationally recognized)

7. TARGET IS REQUIRED. Use "NONE" WHEN:
   - Target is vague ("various countries", "the world")
   - Target is the same as actor's country (domestic policy)
   - No clear external target exists

COMMON MAPPINGS:
   EU_COUNTRIES, EUROPEAN_NATIONS, EUROPE -> EU
   FRANCE, FR_EXECUTIVE, FRENCH -> FR
   IRAN, IRANIAN, TEHRAN -> IR
   GREENLAND, DANISH_TERRITORY -> GL
   CHINA, CHINESE, BEIJING -> CN
   RUSSIA, RUSSIAN, MOSCOW, KREMLIN -> RU
"""


def get_target_rules_for_prompt() -> str:
    """Return target normalization rules for LLM prompt."""
    return TARGET_RULES


# =============================================================================
# GEO ALIAS MAPPINGS - For mechanical bucket inference
# =============================================================================

# Maps common geographic aliases to ISO codes
# Used when alias appears but target wasn't extracted
GEO_ALIAS_TO_ISO = {
    # Territories
    "greenland": "GL",
    "taiwan": "TW",
    "gaza": "PS",
    # Major countries (lowercase)
    "china": "CN",
    "chinese": "CN",
    "beijing": "CN",
    "russia": "RU",
    "russian": "RU",
    "moscow": "RU",
    "kremlin": "RU",
    "india": "IN",
    "indian": "IN",
    "france": "FR",
    "french": "FR",
    "macron": "FR",
    "germany": "DE",
    "german": "DE",
    "japan": "JP",
    "japanese": "JP",
    "korea": "KR",
    "korean": "KR",
    "iran": "IR",
    "iranian": "IR",
    "tehran": "IR",
    "venezuela": "VE",
    "venezuelan": "VE",
    "cuba": "CU",
    "cuban": "CU",
    "mexico": "MX",
    "mexican": "MX",
    "canada": "CA",
    "canadian": "CA",
    "brazil": "BR",
    "brazilian": "BR",
    "denmark": "DK",
    "danish": "DK",
    "uk": "UK",
    "britain": "UK",
    "british": "UK",
    # Regional blocs
    "europe": "EU",
    "european": "EU",
    "nato": "NATO",
    "mercosur": "MERCOSUR",
}


# =============================================================================
# PROMPT BUILDING HELPERS
# =============================================================================


def get_action_classes_for_prompt() -> str:
    """Format action classes for LLM prompt."""
    lines = []

    lines.append("T1 - FORMAL DECISION (highest priority):")
    for ac, desc in ACTION_CLASSES_T1.items():
        lines.append("  - {}: {}".format(ac, desc))

    lines.append("\nT2 - COERCIVE ENFORCEMENT:")
    for ac, desc in ACTION_CLASSES_T2.items():
        lines.append("  - {}: {}".format(ac, desc))

    lines.append("\nT3 - RESOURCE & CAPABILITY:")
    for ac, desc in ACTION_CLASSES_T3.items():
        lines.append("  - {}: {}".format(ac, desc))

    lines.append("\nT4 - COORDINATION:")
    for ac, desc in ACTION_CLASSES_T4.items():
        lines.append("  - {}: {}".format(ac, desc))

    lines.append("\nT5 - PRESSURE & INFLUENCE:")
    for ac, desc in ACTION_CLASSES_T5.items():
        lines.append("  - {}: {}".format(ac, desc))

    lines.append("\nT6 - CONTESTATION:")
    for ac, desc in ACTION_CLASSES_T6.items():
        lines.append("  - {}: {}".format(ac, desc))

    lines.append("\nT7 - INCIDENTS (last resort):")
    for ac, desc in ACTION_CLASSES_T7.items():
        lines.append("  - {}: {}".format(ac, desc))

    return "\n".join(lines)


def get_domains_for_prompt() -> str:
    """Format domains for LLM prompt."""
    return ", ".join(DOMAINS)


def get_actors_for_prompt() -> str:
    """Format controlled actors for LLM prompt."""
    lines = []
    for actor, desc in CONTROLLED_ACTORS.items():
        lines.append("  - {}: {}".format(actor, desc))
    return "\n".join(lines)


def validate_action_class(action_class: str) -> bool:
    """Check if action_class is valid."""
    return action_class in ACTION_CLASSES


def validate_domain(domain: str) -> bool:
    """Check if domain is valid."""
    return domain in DOMAINS


def get_action_class_tier(action_class: str) -> int:
    """Get the tier number for an action class (1-7, or 99 if invalid)."""
    return ACTION_CLASS_TIERS.get(action_class, 99)


# =============================================================================
# POLARITY CLASSIFICATION - Cooperative / Conflictual / Neutral
# =============================================================================

ACTION_CLASS_POLARITY = {
    # Cooperative (6)
    "ALLIANCE_COORDINATION": "COOPERATIVE",
    "MULTILATERAL_ACTION": "COOPERATIVE",
    "INFRASTRUCTURE_DEVELOPMENT": "COOPERATIVE",
    "RESOURCE_ALLOCATION": "COOPERATIVE",
    "CAPABILITY_TRANSFER": "COOPERATIVE",
    "COMMERCIAL_TRANSACTION": "COOPERATIVE",
    # Conflictual (6)
    "MILITARY_OPERATION": "CONFLICTUAL",
    "LAW_ENFORCEMENT_OPERATION": "CONFLICTUAL",
    "SANCTION_ENFORCEMENT": "CONFLICTUAL",
    "SECURITY_INCIDENT": "CONFLICTUAL",
    "ECONOMIC_PRESSURE": "CONFLICTUAL",
    "CIVIL_ACTION": "CONFLICTUAL",
    # Neutral (11)
    "LEGAL_ACTION": "NEUTRAL",
    "LEGISLATIVE_DECISION": "NEUTRAL",
    "POLICY_CHANGE": "NEUTRAL",
    "REGULATORY_ACTION": "NEUTRAL",
    "ELECTORAL_EVENT": "NEUTRAL",
    "STRATEGIC_REALIGNMENT": "NEUTRAL",
    "PRESSURE": "NEUTRAL",
    "STATEMENT": "NEUTRAL",
    "INFORMATION_INFLUENCE": "NEUTRAL",
    "INSTITUTIONAL_RESISTANCE": "NEUTRAL",
    "NATURAL_EVENT": "NEUTRAL",
    "MARKET_SHOCK": "NEUTRAL",
}

# Ensure every action class has a polarity
assert set(ACTION_CLASS_POLARITY.keys()) == set(
    ACTION_CLASSES.keys()
), "ACTION_CLASS_POLARITY must cover all action classes"


def get_polarity(action_class: str) -> str:
    """Get polarity for an action class. Returns 'NEUTRAL' for unknown."""
    return ACTION_CLASS_POLARITY.get(action_class, "NEUTRAL")

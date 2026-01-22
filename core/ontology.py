"""
Event Label Ontology (ELO) v2.0

Defines the complete ontology for structured event labeling:
- ACTION_CLASSES: 7-tier action hierarchy (T1-T7)
- DOMAINS: 7 thematic domains
- CONTROLLED_ACTORS: 17 institution types
- PRIORITY_RULES: Text block for LLM prompt guidance

Label format: PRIMARY_ACTOR -> ACTION_CLASS -> DOMAIN (-> OPTIONAL_TARGET)
"""

ONTOLOGY_VERSION = "ELO_v2.0"

# =============================================================================
# ACTION CLASSES - 7-tier hierarchy (higher tier wins in priority)
# =============================================================================

# Tier 1: FORMAL DECISION - Binding institutional outputs
ACTION_CLASSES_T1 = {
    "LEGAL_RULING": "Court/tribunal binding decision",
    "LEGISLATIVE_DECISION": "Law/resolution passage or rejection",
    "POLICY_CHANGE": "Executive/regulatory policy adoption",
    "REGULATORY_ACTION": "Licensing, approval, certification decisions",
}

# Tier 2: COERCIVE ENFORCEMENT - Use of force or coercive power
ACTION_CLASSES_T2 = {
    "MILITARY_OPERATION": "Armed force deployment, strikes, exercises",
    "LAW_ENFORCEMENT_OPERATION": "Arrests, raids, border enforcement",
    "SANCTION_ENFORCEMENT": "Asset seizure, trade restriction implementation",
}

# Tier 3: RESOURCE & CAPABILITY - Material commitments
ACTION_CLASSES_T3 = {
    "RESOURCE_ALLOCATION": "Budget, funding, aid disbursement",
    "INFRASTRUCTURE_DEVELOPMENT": "Construction, deployment of physical systems",
    "CAPABILITY_TRANSFER": "Arms sales, tech transfer, training provision",
}

# Tier 4: COORDINATION - Multi-party alignment
ACTION_CLASSES_T4 = {
    "ALLIANCE_COORDINATION": "Joint statements, collective decisions",
    "STRATEGIC_REALIGNMENT": "Partnership shifts, bloc formation/exit",
    "MULTILATERAL_ACTION": "UN/IGO resolutions, treaty negotiations",
}

# Tier 5: PRESSURE & INFLUENCE - Non-binding pressure
ACTION_CLASSES_T5 = {
    "POLITICAL_PRESSURE": "Demands, ultimatums, diplomatic notes",
    "ECONOMIC_PRESSURE": "Tariff threats, investment warnings",
    "DIPLOMATIC_PRESSURE": "Ambassador recalls, recognition changes",
    "INFORMATION_INFLUENCE": "Propaganda campaigns, disinformation ops",
}

# Tier 6: CONTESTATION - Resistance and opposition
ACTION_CLASSES_T6 = {
    "LEGAL_CONTESTATION": "Lawsuits, appeals, injunctions filed",
    "INSTITUTIONAL_RESISTANCE": "Vetoes, filibusters, procedural blocks",
    "COLLECTIVE_PROTEST": "Demonstrations, strikes, civil disobedience",
}

# Tier 7: INCIDENTS - Last resort (no clear institutional actor)
ACTION_CLASSES_T7 = {
    "SECURITY_INCIDENT": "Attacks, accidents, breaches without clear actor",
    "SOCIAL_INCIDENT": "Riots, disasters, mass events",
    "ECONOMIC_DISRUPTION": "Market crashes, supply shocks, defaults",
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
PRIORITY RULES FOR LABEL SELECTION:

1. TIER PRIORITY: Lower tier number wins (T1 > T2 > T3 > T4 > T5 > T6 > T7)
   - If a title describes both a court ruling (T1) and protests (T6), use LEGAL_RULING
   - If military operation (T2) with diplomatic pressure (T5), use MILITARY_OPERATION

2. FORMAL > INFORMAL: Binding decisions beat non-binding statements
   - Passed legislation > proposed legislation
   - Signed treaty > treaty negotiations
   - Court ruling > legal filing

3. CONCRETE > ABSTRACT: Specific actions beat general developments
   - "Approves $50B aid package" > "Discusses aid options"
   - "Arrests 10 suspects" > "Investigates crime ring"

4. CAPABILITY CHANGE > INTENT: Material change beats stated intention
   - "Deploys troops" > "Threatens deployment"
   - "Signs contract" > "Considers purchase"

5. CONTESTATION ONLY IF MAIN STORY: Use T6 only if resistance IS the event
   - Protest as main event -> COLLECTIVE_PROTEST
   - Protest mentioned alongside policy -> use the policy action class

6. INCIDENT AS LAST RESORT: Use T7 only when no clear institutional actor
   - Known actor attack -> MILITARY_OPERATION or LAW_ENFORCEMENT_OPERATION
   - Unknown actor/accident -> SECURITY_INCIDENT

7. ACTOR ABSTRACTION: Individuals -> Institutions
   - "Biden signs" -> US_EXECUTIVE
   - "Putin orders" -> RU_EXECUTIVE
   - "Fed Chair announces" -> US_CENTRAL_BANK

ACTOR FORMAT: Use country prefix for state actors
   - US_EXECUTIVE, RU_ARMED_FORCES, CN_LEGISLATURE, EU_REGULATORY_AGENCY
   - For IGOs: UN, NATO, EU, AU, ASEAN (no country prefix)
   - For corporations: Use company name or CORPORATION if generic
"""


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

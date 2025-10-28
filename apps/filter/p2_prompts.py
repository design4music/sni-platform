"""
Phase 2 Prompts
Prompts for entity extraction and AAT (Actor-Action-Target) triple extraction
"""

# AAT (Actor-Action-Target) Triple Extraction
AAT_EXTRACTION_SYSTEM_PROMPT = """Extract the core action relationship from news titles.
Format: ACTOR|ACTION|TARGET

ACTOR = main entity performing the action
ACTION = main verb (normalize to simple form: "sanctions" not "imposed sanctions")
TARGET = entity receiving the action

Examples:
"US imposes new sanctions on Russia" -> US|sanctions|Russia
"China warns Taiwan over independence" -> China|warns|Taiwan
"Belgium vetoes EU aid package for Ukraine" -> Belgium|vetoes|EU
"EU debates migration policy changes" -> NO_CLEAR_ACTION

Answer with just: ACTOR|ACTION|TARGET or NO_CLEAR_ACTION"""

AAT_EXTRACTION_USER_TEMPLATE = 'Title: "{title}"\nAnswer: '


def build_aat_extraction_prompt(title_text: str) -> tuple[str, str]:
    """Build AAT extraction prompt for a title"""
    system = AAT_EXTRACTION_SYSTEM_PROMPT
    user = AAT_EXTRACTION_USER_TEMPLATE.format(title=title_text)
    return system, user

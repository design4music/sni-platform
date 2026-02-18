"""Shared LLM utilities for pipeline modules."""

import json
import re


def extract_json(text):
    """Extract JSON from LLM response text.

    Tries: direct parse, markdown code blocks, raw JSON object.
    """
    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError("Failed to parse LLM response as JSON")


# --- Post-processing: fix LLM training-data role hallucinations ---

# Leaders whose roles DeepSeek gets wrong due to training cutoff.
# Map: regex pattern -> replacement. Applied to all LLM prose output.
_ROLE_FIXES = [
    # Trump: inaugurated Jan 2025, DeepSeek says "Former President"
    (
        re.compile(
            r"\bFormer\s+(?:U\.?S\.?\s+)?President\s+(Donald\s+)?Trump", re.IGNORECASE
        ),
        lambda m: (
            ("President %sTrump" % m.group(1)) if m.group(1) else "President Trump"
        ),
    ),
]

# Merz: became Chancellor May 2025. DeepSeek uses many phrasings:
#   PREFIX:     "opposition leader Friedrich Merz"
#   APPOSITIVE: "Friedrich Merz, leader of the opposition CDU,"
#   REVERSE:    "Germany's opposition leader, Friedrich Merz,"
# Keywords that signal a wrong Merz role:
_MERZ_BAD_KEYWORDS = (
    r"opposition|conservative\s+leader|CDU\s+(?:leader|chief|head)|Union\s+leader"
)

# Pattern A: bad_role + name ("opposition leader Friedrich Merz")
_MERZ_PREFIX = re.compile(
    r"\b(?:"
    r"(?:German\s+)?(?:opposition|conservative)\s+(?:leader|figure|politician)"
    r"|(?:leader|head|chief)\s+of\s+(?:Germany'?s?\s+)?(?:the\s+)?(?:main\s+)?opposition(?:\s+party)?(?:\s+(?:the\s+)?CDU)?"
    r"|(?:a\s+)?(?:leading\s+)?German\s+(?:opposition\s+)?politician"
    r"|(?:CDU|Union)\s+(?:leader|chief|head)"
    r"|politician"
    r")\s+",
    re.IGNORECASE,
)

# Pattern B: "Friedrich Merz, <appositive with bad keywords>," -> "Chancellor Friedrich Merz,"
_MERZ_APPOSITIVE = re.compile(
    r"(Friedrich\s+Merz)\s*,\s*[^,]*?(?:" + _MERZ_BAD_KEYWORDS + r")[^,]*,",
    re.IGNORECASE,
)

# Pattern C: "Germany's opposition leader, Friedrich Merz," -> "Chancellor Friedrich Merz,"
_MERZ_REVERSE = re.compile(
    r"(?:Germany'?s?\s+)?opposition\s+leader\s*,\s*(Friedrich\s+Merz)",
    re.IGNORECASE,
)


def fix_role_hallucinations(text):
    """Fix incorrect roles injected by LLM training data."""
    if not text:
        return text
    for pattern, replacement in _ROLE_FIXES:
        text = pattern.sub(replacement, text)
    # Merz pattern B: appositive "Friedrich Merz, the opposition leader,"
    text = _MERZ_APPOSITIVE.sub(r"Chancellor \1,", text)
    # Merz pattern C: reverse "Germany's opposition leader, Friedrich Merz"
    text = _MERZ_REVERSE.sub(r"Chancellor \1", text)
    # Merz pattern A: prefix "opposition leader Friedrich Merz"
    text = re.sub(
        _MERZ_PREFIX.pattern + r"(Friedrich\s+Merz)",
        r"Chancellor \1",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        _MERZ_PREFIX.pattern + r"(Merz)(?!\w)",
        r"Chancellor \1",
        text,
        flags=re.IGNORECASE,
    )
    return text

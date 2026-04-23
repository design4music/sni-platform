"""Shared LLM utilities for pipeline modules."""

import asyncio
import json
import re
import time

# --- Rate limit handling ---


def check_rate_limit(response, attempt=0):
    """Sleep and return True if response is a 429 rate limit. Sync version.

    Uses Retry-After header if present, otherwise exponential backoff
    starting at 5s (5, 15, 45s for attempts 0, 1, 2).
    Also backs off on 502/503/504 (transient server errors).
    """
    if response.status_code == 429 or response.status_code in (502, 503, 504):
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            wait = int(retry_after)
        else:
            wait = 5 * (3**attempt)  # 5, 15, 45
        print(
            "HTTP %d, backing off %ds (attempt %d)..."
            % (response.status_code, wait, attempt + 1)
        )
        time.sleep(wait)
        return True
    return False


async def async_check_rate_limit(response, attempt=0):
    """Sleep and return True if response is a 429 rate limit. Async version.

    Uses Retry-After header if present, otherwise exponential backoff
    starting at 5s (5, 15, 45s for attempts 0, 1, 2).
    Also backs off on 502/503/504 (transient server errors).
    """
    if response.status_code == 429 or response.status_code in (502, 503, 504):
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            wait = int(retry_after)
        else:
            wait = 5 * (3**attempt)  # 5, 15, 45
        print(
            "HTTP %d, backing off %ds (attempt %d)..."
            % (response.status_code, wait, attempt + 1)
        )
        await asyncio.sleep(wait)
        return True
    return False


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

# Localized titles per leader. DE uses the natural German title so we
# don't end up with "Chancellor Merz" (English word) inside German prose.
_TITLES = {
    "en": {"trump": "President", "merz": "Chancellor", "carney": "Prime Minister"},
    "de": {"trump": "Präsident", "merz": "Bundeskanzler", "carney": "Premierminister"},
}


def _trump_fix_factory(locale):
    title = _TITLES[locale]["trump"]

    def _sub(m):
        return (
            ("%s %sTrump" % (title, m.group(1))) if m.group(1) else "%s Trump" % title
        )

    return _sub


# Trump: inaugurated Jan 2025, DeepSeek says "Former President"
_TRUMP_FORMER = re.compile(
    r"\bFormer\s+(?:U\.?S\.?\s+)?President\s+(Donald\s+)?Trump", re.IGNORECASE
)

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

# Carney: PM of Canada since March 2025. DeepSeek defaults to his prior
# roles (Bank of Canada 2008-2013, Bank of England 2013-2020, central
# banker, Liberal leader) or outright fabricates (Foreign Minister).
# Keywords that signal a wrong Carney role:
_CARNEY_BAD_KEYWORDS = (
    r"(?:former|ex-?)\s+(?:Bank\s+of\s+(?:Canada|England)\s+)?[Gg]overnor"
    r"|(?:former|ex-?)\s+[Gg]overnor\s+of\s+the\s+Bank\s+of\s+(?:Canada|England)"
    r"|(?:former|ex-?)\s+central\s+banker"
    r"|(?:Canada'?s?|Canadian)\s+(?:former|ex-?)\s+central\s+banker"
    r"|(?:Canadian|Canada'?s?)\s+Foreign\s+Minister"
    r"|Liberal(?:\s+Party)?\s+(?:leader|chief|head)"
    r"|opposition\s+leader"
)

# Pattern A: bad_role + name ("Former Bank of Canada governor Mark Carney")
_CARNEY_PREFIX = re.compile(
    r"\b(?:"
    r"(?:former|ex-?)\s+(?:Bank\s+of\s+(?:Canada|England)\s+)?[Gg]overnor(?:\s+of\s+the\s+Bank\s+of\s+(?:Canada|England))?"
    r"|(?:former|ex-?)\s+central\s+banker"
    r"|(?:Canadian|Canada'?s?)\s+Foreign\s+Minister"
    r"|Liberal(?:\s+Party)?\s+(?:leader|chief|head)"
    r")\s+",
    re.IGNORECASE,
)

# Pattern B: "Mark Carney, <appositive with bad keywords>,"
_CARNEY_APPOSITIVE = re.compile(
    r"(Mark\s+Carney)\s*,\s*(?:the\s+)?[^,]*?(?:" + _CARNEY_BAD_KEYWORDS + r")[^,]*,",
    re.IGNORECASE,
)

# Pattern C: "Canada's former central banker, Mark Carney" -> "Prime Minister Mark Carney"
_CARNEY_REVERSE = re.compile(
    r"(?:Canada'?s?|Canadian)?\s*(?:former|ex-?)\s+(?:central\s+banker|Bank\s+of\s+(?:Canada|England)\s+[Gg]overnor)\s*,\s*(Mark\s+Carney)",
    re.IGNORECASE,
)

# --- German-language Merz patterns (pure-DE prose, no English leaks) ---
# Real DE hallucinations from Render look like:
#   "Friedrich Merz, der Vorsitzende der größten Oppositionspartei,"
#   "Friedrich Merz, der Vorsitzende der oppositionellen CDU,"
#   "Deutschlands Oppositionsführer Friedrich Merz"
_MERZ_DE_APPOSITIVE = re.compile(
    r"(Friedrich\s+Merz)\s*,\s*(?:der|die|des)\s+[^,]*?"
    r"(?:Opposition|Oppositionsführer|Oppositionspartei|oppositionell|CDU[-\s](?:Chef|Vorsitzender|Fraktionschef)|konservativ)"
    r"[^,]*,",
    re.IGNORECASE,
)
_MERZ_DE_REVERSE = re.compile(
    r"(?:Deutschlands\s+)?Oppositionsführer\s+(Friedrich\s+Merz)",
    re.IGNORECASE,
)

# --- German-language Carney patterns ---
# E.g. "Mark Carney, der ehemalige Gouverneur der Bank of Canada,"
_CARNEY_DE_APPOSITIVE = re.compile(
    r"(Mark\s+Carney)\s*,\s*(?:der|die|des)\s+[^,]*?"
    r"(?:ehemalig\w*\s+(?:Gouverneur|Zentralbankchef|Notenbankchef|Chef\s+der\s+Bank\s+of\s+(?:Canada|England)|Bank[-\s]of[-\s](?:Canada|England)[-\s]Chef)"
    r"|(?:Kanadas\s+)?Außenminister"
    r"|Liberale[rn]?\s+(?:Parteichef|Chef|Vorsitzend\w*))"
    r"[^,]*,",
    re.IGNORECASE,
)
_CARNEY_DE_PREFIX = re.compile(
    r"\b(?:"
    r"ehemalig\w*\s+(?:Gouverneur|Zentralbankchef|Notenbankchef)(?:\s+der\s+Bank\s+of\s+(?:Canada|England))?"
    r"|(?:Kanadas\s+)?Außenminister"
    r"|Liberale[rn]?\s+(?:Parteichef|Chef|Vorsitzend\w*)"
    r")\s+",
    re.IGNORECASE,
)

# DE Trump: "ehemaligen US-Präsidenten Donald Trump" / "Ex-Präsident Trump"
# Consumes a leading article when present so the replacement doesn't
# orphan "des" / "den" in front of the new nominative "Präsident".
_TRUMP_DE_FORMER = re.compile(
    r"\b(?:(?:der|den|des|dem|einem?)\s+)?(?:ehemalig\w*|Ex-)\s*(?:US-)?Präsident(?:en|s)?\s+(Donald\s+)?Trump",
    re.IGNORECASE,
)


def fix_role_hallucinations(text, locale="en"):
    """Fix incorrect roles injected by LLM training data.

    locale controls the title word ('en' -> Chancellor/President/Prime
    Minister, 'de' -> Bundeskanzler/Präsident/Premierminister). Pass
    'de' when cleaning German prose; the English default stays the
    right choice for English output.
    """
    if not text:
        return text
    if locale not in _TITLES:
        locale = "en"
    titles = _TITLES[locale]
    merz_title = titles["merz"]
    carney_title = titles["carney"]

    # Trump
    text = _TRUMP_FORMER.sub(_trump_fix_factory(locale), text)
    # Merz pattern B: appositive "Friedrich Merz, the opposition leader,"
    text = _MERZ_APPOSITIVE.sub(r"%s \1," % merz_title, text)
    # Merz pattern C: reverse "Germany's opposition leader, Friedrich Merz"
    text = _MERZ_REVERSE.sub(r"%s \1" % merz_title, text)
    # Merz pattern A: prefix "opposition leader Friedrich Merz"
    text = re.sub(
        _MERZ_PREFIX.pattern + r"(Friedrich\s+Merz)",
        r"%s \1" % merz_title,
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        _MERZ_PREFIX.pattern + r"(Merz)(?!\w)",
        r"%s \1" % merz_title,
        text,
        flags=re.IGNORECASE,
    )
    # Carney pattern B: appositive "Mark Carney, former governor of the Bank of Canada,"
    text = _CARNEY_APPOSITIVE.sub(r"%s \1," % carney_title, text)
    # Carney pattern C: reverse "Canada's former central banker, Mark Carney"
    text = _CARNEY_REVERSE.sub(r"%s \1" % carney_title, text)
    # Carney pattern A: prefix "Former Bank of Canada governor Mark Carney"
    text = re.sub(
        _CARNEY_PREFIX.pattern + r"(Mark\s+Carney)",
        r"%s \1" % carney_title,
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        _CARNEY_PREFIX.pattern + r"(Carney)(?!\w)",
        r"%s \1" % carney_title,
        text,
        flags=re.IGNORECASE,
    )

    if locale == "de":
        # Pure-DE prose: catch German phrasings the English patterns miss.
        text = _TRUMP_DE_FORMER.sub(
            lambda m: (
                ("Präsident %sTrump" % m.group(1)) if m.group(1) else "Präsident Trump"
            ),
            text,
        )
        text = _MERZ_DE_APPOSITIVE.sub(r"%s \1," % merz_title, text)
        text = _MERZ_DE_REVERSE.sub(r"%s \1" % merz_title, text)
        text = _CARNEY_DE_APPOSITIVE.sub(r"%s \1," % carney_title, text)
        text = re.sub(
            _CARNEY_DE_PREFIX.pattern + r"(Mark\s+Carney)",
            r"%s \1" % carney_title,
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            _CARNEY_DE_PREFIX.pattern + r"(Carney)(?!\w)",
            r"%s \1" % carney_title,
            text,
            flags=re.IGNORECASE,
        )
        # Cleanup: a prior backfill left English titles in DE prose.
        # Swap them for the German equivalents. Idempotent.
        text = re.sub(
            r"\bChancellor\s+(Friedrich\s+)?Merz\b", r"Bundeskanzler \1Merz", text
        )
        text = re.sub(
            r"\bPrime\s+Minister\s+(Mark\s+)?Carney\b",
            r"Premierminister \1Carney",
            text,
        )
        text = re.sub(r"\bPresident\s+(Donald\s+)?Trump\b", r"Präsident \1Trump", text)

    return text


# --- Context-aware: fix title that dropped the subject name ---
# E.g. title "Former Bank of Canada governor says ..." where the
# summary references Carney. The regex-only fix in fix_role_hallucinations
# can't touch this because the name isn't in the title.
_BANK_GOV_TITLE_EN = re.compile(
    r"(?:former|ex-?)\s+(?:Bank\s+of\s+(?:Canada|England)\s+)?[Gg]overnor"
    r"(?:\s+of\s+the\s+Bank\s+of\s+(?:Canada|England))?",
    re.IGNORECASE,
)
_BANK_GOV_TITLE_DE = re.compile(
    r"[Ee]hemalig\w*\s+(?:"
    r"Gouverneur|Zentralbankchef|Notenbankchef"
    r"|Bank[-\s]of[-\s](?:Canada|England)[-\s]Chef"
    r")"
    r"(?:\s+der\s+Bank\s+of\s+(?:Canada|England))?",
    re.IGNORECASE,
)


def fix_title_with_context(title, summary, locale="en"):
    """Fix headline-style titles that drop the subject name.

    When the title contains a former-governor phrase (classic Carney
    LLM hallucination) AND the summary references "Carney", replace
    the phrase with the correct PM title in the title. Safe because
    the summary reference anchors the subject.
    """
    if not title or not summary:
        return title
    if "Carney" not in summary:
        return title
    pattern = _BANK_GOV_TITLE_DE if locale == "de" else _BANK_GOV_TITLE_EN
    if not pattern.search(title):
        return title
    carney = _TITLES.get(locale, _TITLES["en"])["carney"]
    return pattern.sub("%s Mark Carney" % carney, title, count=1)

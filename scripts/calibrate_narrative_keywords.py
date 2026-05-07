"""Narrative keyword calibration helper.

Given a narrative_id and a list of primary-source publishers for that
narrative's coalition, scan their headlines for FN-topic matches and
surface candidate framing_keywords + topic_keywords the analyst can
review and selectively adopt.

This is curation infrastructure, NOT a pipeline component. Run
interactively when:
  - a new narrative is added
  - coverage shifts noticeably (new actors, new framing)
  - a narrative looks empty in the perspectives view despite real coverage

Usage:
  python scripts/calibrate_narrative_keywords.py \\
      --narrative iran_nuclear_sovereign_right \\
      --publishers "Press TV,IRNA,Fars News,Tasnim News" \\
      --window-days 180

Output:
  - Markdown report to stdout: candidate phrases + named entities,
    ranked by recurrence, with sample headlines.
  - SQL UPDATE template you can edit and run after review.

Convention: matches the project's keyword model where topic_keywords
serve FN-relevance + coalition gating, framing_keywords carry the
loaded vocabulary diagnostic. See docs/concept_friction_nodes_and_narratives_v2.md
section 7.5 for the methodology.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

# Stop-tokens we never want to suggest as framing keywords. Lowercased.
STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "of",
    "in",
    "on",
    "at",
    "to",
    "for",
    "with",
    "by",
    "from",
    "as",
    "into",
    "and",
    "or",
    "but",
    "if",
    "then",
    "than",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "they",
    "them",
    "their",
    "there",
    "here",
    "what",
    "which",
    "who",
    "whom",
    "whose",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "very",
    "can",
    "will",
    "just",
    "should",
    "now",
    "says",
    "say",
    "said",
    "according",
    "amid",
    "after",
    "before",
    "during",
    "over",
    "under",
    "about",
    "against",
    "between",
    "through",
    "ap",
    "afp",
    "reuters",
    "english",
}

# Named-entity-ish: short capitalised tokens we promote to topic_keyword
# candidates rather than framing_keyword candidates.
NAMED_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:[-’'][A-Z][a-z]+)?\b")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--narrative", required=True, help="narrative_id from narratives_v2")
    p.add_argument(
        "--publishers",
        required=True,
        help="comma-separated list of publisher_name values (exact match) — the coalition's primary sources",
    )
    p.add_argument(
        "--window-days",
        type=int,
        default=180,
        help="how far back to scan (default 180)",
    )
    p.add_argument(
        "--min-recur",
        type=int,
        default=2,
        help="minimum recurrence to surface a phrase (default 2)",
    )
    p.add_argument(
        "--top-phrases",
        type=int,
        default=40,
        help="max phrase candidates to show (default 40)",
    )
    p.add_argument(
        "--top-entities",
        type=int,
        default=20,
        help="max named-entity candidates (default 20)",
    )
    return p.parse_args()


def fetch_narrative(cur, narrative_id: str) -> dict:
    cur.execute(
        "SELECT id, name_en, framing_keywords, topic_keywords, actor_centroids "
        "FROM narratives_v2 WHERE id = %s",
        (narrative_id,),
    )
    row = cur.fetchone()
    if not row:
        raise SystemExit(f"narrative_id={narrative_id} not found")
    return row


def fetch_titles(
    cur, publishers: list[str], topic_keywords: list[str], window_days: int
) -> list[dict]:
    """Headlines from the given publishers that touch any topic_keyword."""
    if not topic_keywords:
        # Fall back to all headlines from these publishers (less useful but valid).
        cur.execute(
            "SELECT title_display, publisher_name, pubdate_utc::date AS d "
            "FROM titles_v3 WHERE publisher_name = ANY(%s) "
            "AND pubdate_utc > NOW() - (%s || ' days')::interval "
            "ORDER BY pubdate_utc DESC",
            (publishers, str(window_days)),
        )
    else:
        # Topic-filtered: title must mention at least one topic_keyword.
        cur.execute(
            """
            SELECT title_display, publisher_name, pubdate_utc::date AS d
            FROM titles_v3 t
            WHERE publisher_name = ANY(%s)
              AND pubdate_utc > NOW() - (%s || ' days')::interval
              AND EXISTS (
                  SELECT 1 FROM unnest(%s::text[]) kw
                  WHERE t.title_display ILIKE '%%' || kw || '%%'
              )
            ORDER BY pubdate_utc DESC
            """,
            (publishers, str(window_days), topic_keywords),
        )
    return cur.fetchall()


def normalize(s: str) -> str:
    """Lowercase + strip quotes/punctuation that creates spurious n-gram variants."""
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"[\"«»()\\[\\]]", " ", s)
    return s


def extract_phrases(titles: list[dict], existing_kw: set[str]) -> Counter:
    """Count 2- and 3-word phrases, lowercased, excluding pure stopword runs.
    Excludes phrases already in existing_kw (case-insensitive).
    """
    counts: Counter = Counter()
    existing_lower = {k.lower() for k in existing_kw}
    for row in titles:
        text = normalize(row["title_display"]).lower()
        # Tokenise on non-word boundaries; keep words 2+ chars.
        tokens = [t for t in re.findall(r"[a-z][a-z0-9'-]+", text) if len(t) >= 2]
        for n in (2, 3):
            for i in range(len(tokens) - n + 1):
                ngram = tokens[i : i + n]
                # Skip if all tokens are stopwords (low signal).
                if all(t in STOPWORDS for t in ngram):
                    continue
                # Skip if the phrase starts or ends with a stopword AND is 2-gram (often artifacts).
                if n == 2 and (ngram[0] in STOPWORDS or ngram[-1] in STOPWORDS):
                    continue
                # Skip if the 3-gram has stopwords at both ends (also low signal).
                if n == 3 and ngram[0] in STOPWORDS and ngram[-1] in STOPWORDS:
                    continue
                phrase = " ".join(ngram)
                if phrase in existing_lower:
                    continue
                counts[phrase] += 1
    return counts


def extract_named_entities(titles: list[dict], existing_kw: set[str]) -> Counter:
    """Capitalised tokens that look like names — places, officials, organisations.
    Uses raw (cased) form; excludes stopwords + already-existing topic keywords.
    """
    counts: Counter = Counter()
    existing_lower = {k.lower() for k in existing_kw}
    for row in titles:
        text = normalize(row["title_display"])
        # Find capitalised tokens of length >= 3.
        for m in NAMED_PATTERN.findall(text):
            if len(m) < 3:
                continue
            if m.lower() in STOPWORDS:
                continue
            if m.lower() in existing_lower:
                continue
            counts[m] += 1
    return counts


def find_sample_headlines(titles: list[dict], phrase: str, n: int = 3) -> list[str]:
    """Headlines containing the phrase (case-insensitive substring), most recent first."""
    out = []
    needle = phrase.lower()
    for row in titles:
        if needle in row["title_display"].lower():
            out.append(
                f'"{row["title_display"]}" — {row["publisher_name"]} ({row["d"]})'
            )
            if len(out) >= n:
                break
    return out


def render_report(
    narrative: dict,
    publishers: list[str],
    titles: list[dict],
    phrase_counts: Counter,
    entity_counts: Counter,
    args: argparse.Namespace,
) -> str:
    lines = []
    lines.append(f"# Calibration: `{narrative['id']}`")
    lines.append("")
    lines.append(f"**Narrative**: {narrative['name_en']}")
    lines.append(
        f"**Coalition (actor_centroids)**: `{', '.join(narrative['actor_centroids'])}`"
    )
    lines.append(f"**Publishers scanned**: {', '.join(publishers)}")
    lines.append(f"**Window**: last {args.window_days} days")
    lines.append(f"**Topic-matched titles**: {len(titles)}")
    lines.append(
        f"**Existing framing_keywords**: {len(narrative['framing_keywords'] or [])}"
    )
    lines.append(
        f"**Existing topic_keywords**: {len(narrative['topic_keywords'] or [])}"
    )
    lines.append("")

    # Phrase candidates (framing_keywords).
    top_phrases = [
        (p, c)
        for (p, c) in phrase_counts.most_common(args.top_phrases)
        if c >= args.min_recur
    ]
    lines.append(
        f"## Phrase candidates ({len(top_phrases)} above min-recur={args.min_recur})"
    )
    lines.append("")
    lines.append(
        "These are 2-3 word recurring phrases not already in the keyword set. Review and add the ones that carry the framing (the coalition's loaded vocabulary). Skip phrases that could appear in neutral coverage."
    )
    lines.append("")
    lines.append("| count | phrase | sample headlines |")
    lines.append("|---|---|---|")
    for phrase, count in top_phrases:
        samples = find_sample_headlines(titles, phrase, n=2)
        sample_text = "<br>".join(samples) if samples else "—"
        lines.append(f"| {count} | `{phrase}` | {sample_text} |")
    lines.append("")

    # Named-entity candidates (topic_keywords).
    top_entities = [
        (e, c)
        for (e, c) in entity_counts.most_common(args.top_entities)
        if c >= args.min_recur
    ]
    lines.append(
        f"## Named-entity candidates ({len(top_entities)} above min-recur={args.min_recur})"
    )
    lines.append("")
    lines.append(
        "Capitalised tokens not already in topic_keywords. Add officials, programs, sites, or organisations that identify this coalition or its key infrastructure."
    )
    lines.append("")
    lines.append("| count | entity |")
    lines.append("|---|---|")
    for entity, count in top_entities:
        lines.append(f"| {count} | `{entity}` |")
    lines.append("")

    # SQL UPDATE template.
    lines.append("## SQL UPDATE template (review before running)")
    lines.append("")
    lines.append(
        "Edit the arrays below to keep ONLY the keywords you've reviewed and approved. Then run on local + Render."
    )
    lines.append("")
    lines.append("```sql")
    lines.append("UPDATE narratives_v2 SET")
    lines.append("  framing_keywords = framing_keywords || ARRAY[")
    for phrase, _ in top_phrases[:15]:
        lines.append(f"    '{phrase}',  -- review")
    lines.append("  ]::text[],")
    lines.append("  topic_keywords = topic_keywords || ARRAY[")
    for entity, _ in top_entities[:10]:
        lines.append(f"    '{entity}',  -- review")
    lines.append("  ]::text[],")
    lines.append("  updated_at = now()")
    lines.append(f"WHERE id = '{narrative['id']}';")
    lines.append("```")
    lines.append("")
    lines.append(
        "After UPDATE: re-run `scripts/bootstrap_fn2_demo_links.sql` (or the equivalent for the FN this narrative belongs to) and verify the new match counts via the perspectives view."
    )

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    publishers = [p.strip() for p in args.publishers.split(",") if p.strip()]

    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            narrative = fetch_narrative(cur, args.narrative)
            titles = fetch_titles(
                cur, publishers, narrative["topic_keywords"] or [], args.window_days
            )
            existing = set(
                (narrative["framing_keywords"] or [])
                + (narrative["topic_keywords"] or [])
            )
            phrase_counts = extract_phrases(titles, existing)
            entity_counts = extract_named_entities(titles, existing)
            print(
                render_report(
                    narrative, publishers, titles, phrase_counts, entity_counts, args
                )
            )
    finally:
        conn.close()


if __name__ == "__main__":
    main()

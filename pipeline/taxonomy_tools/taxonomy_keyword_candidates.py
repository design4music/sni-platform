"""
Taxonomy Tools - Keyword Candidates (EN) for Taxonomy Enrichment / Mini-Clustering

This is an enhanced variant of oos_keyword_candidates.py that can run in two modes:
- mode=oos      : like the original (prioritizes OOS leakage)
- mode=taxonomy : prioritizes high-signal phrases for clustering (bigrams/trigrams + collocations)

No DB writes. Outputs JSON only.

Usage examples:
  python taxonomy_keyword_candidates.py --since-hours 168 --mode taxonomy --top 200
  python taxonomy_keyword_candidates.py --since-hours 168 --mode taxonomy --ngram-max 3 --min-total-support 3
"""

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from common import get_db_connection, normalize_text

# Start from your existing stopwords/boilerplate but expand aggressively for finance/news glue.
STOPWORDS_EN = {
    # articles/pronouns/etc
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "should",
    "could",
    "may",
    "might",
    "must",
    "can",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "their",
    "them",
    "we",
    "us",
    "our",
    "you",
    "your",
    "they",
    "what",
    "which",
    "who",
    "when",
    "where",
    "why",
    "how",
    "more",
    "most",
    "other",
    "some",
    "such",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "after",
    "before",
    "because",
    "if",
    "then",
    "about",
    "into",
    "through",
    "during",
    "between",
    "under",
    "again",
    "once",
    "here",
    "there",
    "out",
    "up",
    "down",
    "off",
    "over",
    # headline glue / reporting verbs
    "says",
    "said",
    "told",
    "according",
    "report",
    "reports",
    "reported",
    "announced",
    "announce",
    "urges",
    "warns",
    "warn",
    "calls",
    "call",
    "seeks",
    "seek",
    "asks",
    "ask",
    "plans",
    "plan",
    # content wrappers
    "news",
    "update",
    "breaking",
    "latest",
    "live",
    "video",
    "photo",
    "watch",
    "read",
    "via",
    "explainer",
    "analysis",
    "opinion",
    "interview",
    "feature",
    # finance/news generic glue (critical!)
    "price",
    "prices",
    "market",
    "markets",
    "stock",
    "stocks",
    "shares",
    "futures",
    "index",
    "indexes",
    "today",
    "week",
    "month",
    "year",
    "record",
    "records",
    "high",
    "highs",
    "low",
    "lows",
    "rises",
    "rise",
    "falls",
    "fall",
    "gains",
    "gain",
    "drops",
    "drop",
    "slips",
    "slip",
    "surges",
    "surge",
    "higher",
    "lower",
    "ahead",
    "amid",
    "after",
    "before",
    "as",
    "with",
    "on",
    "in",
    "at",
    "to",
    "from",
}

TIME_BOILERPLATE = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    "yesterday",
    "tomorrow",
    "tonight",
    "morning",
    "afternoon",
    "evening",
    "night",
}
ALL_STOPWORDS = STOPWORDS_EN | TIME_BOILERPLATE

# Domain anchors that tend to produce high-value clustering phrases.
# This is intentionally small and can be tuned.
DOMAIN_ANCHORS = {
    "tariff",
    "tariffs",
    "trade",
    "deal",
    "agreement",
    "export",
    "imports",
    "import",
    "controls",
    "restriction",
    "restrictions",
    "sanction",
    "sanctions",
    "retaliation",
    "dual",
    "use",
    "chip",
    "chips",
    "semiconductor",
    "semiconductors",
    "drill",
    "drills",
    "exercise",
    "exercises",
    "military",
    "naval",
    "maritime",
    "reserve",
    "reserves",
    "central",
    "bank",
    "fed",
    "federal",
    "probe",
    "investigation",
    "rare",
    "earth",
    "mining",
    "infrastructure",
    "supply",
    "chain",
    "shipment",
    "port",
    "gold",
    "silver",
    "bullion",
    "commodity",
    "commodities",
    "oil",
    "gas",
    "summit",
    "envoy",
    "minister",
    "diplomat",
    "diplomats",
    "junta",
}


def extract_titlecase_phrases(original_title: str) -> set[str]:
    """2+ consecutive TitleCase words → likely proper names; used for filtering."""
    titlecase_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"
    out = set()
    for m in re.finditer(titlecase_pattern, original_title):
        out.add(normalize_text(m.group(0)))
    return out


def tokenize(normalized_title: str) -> list[str]:
    cleaned = normalized_title.replace("'", "")
    return cleaned.split()


def is_valid_token(t: str, min_len: int) -> bool:
    if len(t) < min_len:
        return False
    if t.isdigit():
        return False
    if t in ALL_STOPWORDS:
        return False
    # remove pure punctuation artifacts
    if not re.search(r"[a-z]", t):
        return False
    return True


def extract_ngrams(tokens: list[str], min_n: int, max_n: int) -> list[str]:
    ngrams = []
    L = len(tokens)
    for n in range(min_n, max_n + 1):
        for i in range(L - n + 1):
            ngrams.append(" ".join(tokens[i : i + n]))
    return ngrams


def is_valid_ngram(ngram: str) -> bool:
    toks = ngram.split()
    if not toks:
        return False
    # reject if starts/ends with stopword/time
    if toks[0] in ALL_STOPWORDS or toks[-1] in ALL_STOPWORDS:
        return False
    # reject if too many numeric tokens inside
    if sum(tok.isdigit() for tok in toks) >= 1:
        return False
    return True


def load_taxonomy_aliases_en() -> set[str]:
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT aliases FROM taxonomy_v3 WHERE is_active = true AND taxonomy_function = 'centroid_anchor'"
        )
        rows = cur.fetchall()
    conn.close()

    aliases_en = set()
    for (aliases,) in rows:
        if not aliases or not isinstance(aliases, dict):
            continue
        for a in aliases.get("en", []):
            aliases_en.add(normalize_text(a))
    return aliases_en


def load_titles_en(since_hours: int) -> list[tuple[str, str, bool]]:
    """Returns (title_id, title_display, is_oos)."""
    conn = get_db_connection()
    cutoff = datetime.utcnow() - timedelta(hours=since_hours)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title_display, processing_status
            FROM titles_v3
            WHERE created_at >= %s
              AND detected_language = 'en'
            ORDER BY created_at DESC
            """,
            (cutoff,),
        )
        rows = cur.fetchall()
    conn.close()
    out = []
    for tid, tdisp, status in rows:
        out.append((tid, tdisp, status == "out_of_scope"))
    return out


def pmi_like(
    ngram: str,
    ngram_count: int,
    uni_counts: Counter,
    total_unis: int,
    total_ngrams: int,
) -> float:
    """
    PMI-like score for bigrams/trigrams:
    score = log( P(ngram) / Π P(word) )
    Uses unigram counts as approximation.
    """
    toks = ngram.split()
    if len(toks) < 2:
        return 0.0
    p_ng = ngram_count / max(1, total_ngrams)
    denom = 1.0
    for w in toks:
        denom *= (
            (uni_counts[w] / max(1, total_unis))
            if uni_counts[w]
            else (1.0 / max(1, total_unis))
        )
    return math.log((p_ng / max(1e-12, denom)) + 1e-12)


def analyze(
    titles,
    taxonomy_aliases,
    mode: str,
    min_total_support: int,
    min_oos_support: int,
    ngram_min: int,
    ngram_max: int,
    min_len: int,
    top_n: int,
):
    # Counts
    support_all = Counter()
    support_oos = Counter()
    examples = defaultdict(list)

    # For collocations
    uni_counts = Counter()
    total_unis = 0
    total_ngrams = 0

    # Pass 1: collect counts
    for _, title_display, is_oos in titles:
        titlecase_phrases = extract_titlecase_phrases(title_display)
        norm = normalize_text(title_display)
        toks = tokenize(norm)

        valid = [t for t in toks if is_valid_token(t, min_len)]
        if not valid:
            continue

        # per-title uniqueness (avoid overweighting repeated tokens in one title)
        seen_ngrams = set()
        grams = extract_ngrams(valid, min_n=ngram_min, max_n=ngram_max)
        for g in grams:
            if g in seen_ngrams:
                continue
            seen_ngrams.add(g)

            if g in taxonomy_aliases:
                continue
            if g in titlecase_phrases:
                continue
            if not is_valid_ngram(g):
                continue

            support_all[g] += 1
            if is_oos:
                support_oos[g] += 1
            if len(examples[g]) < 5:
                examples[g].append(title_display)

        # unigram counts for PMI-like scoring
        for w in set(valid):
            uni_counts[w] += 1
            total_unis += 1
        total_ngrams += len(seen_ngrams)

    # Pass 2: score + filter
    candidates = []
    for g, cnt in support_all.items():
        oos_cnt = support_oos.get(g, 0)

        # base filters
        if cnt < min_total_support:
            continue
        if mode == "oos" and oos_cnt < min_oos_support:
            continue

        toks = g.split()
        n = len(toks)

        # Domain anchor boost: if any token is in DOMAIN_ANCHORS
        anchor_hits = sum(1 for w in toks if w in DOMAIN_ANCHORS)

        # taxonomy mode: require at least one strategic anchor
        if mode == "taxonomy" and anchor_hits == 0:
            continue

        # PMI-like collocation score only meaningful for n>=2
        pmi = pmi_like(g, cnt, uni_counts, total_unis, total_ngrams)

        # Generic penalty: if all tokens are short/common-ish (heuristic)
        # (we already removed many via stopwords, but keep an extra guard)
        generic_penalty = 0.0
        if n == 1 and toks[0] in {"america", "american", "trump", "us", "usa", "u.s"}:
            generic_penalty = 5.0

        # scoring
        if mode == "oos":
            score = (
                (2.0 * oos_cnt)
                + (0.3 * cnt)
                + (0.2 * max(0.0, pmi))
                + (0.5 * anchor_hits)
                - generic_penalty
            )
        else:
            # taxonomy mode: focus on usable clustering phrases
            score = (
                (1.0 * cnt)
                + (1.2 * max(0.0, pmi))
                + (1.0 * anchor_hits)
                - generic_penalty
            )

        candidates.append(
            {
                "token": g,
                "support_all": cnt,
                "support_oos": oos_cnt,
                "len": n,
                "anchor_hits": anchor_hits,
                "pmi_like": round(pmi, 4),
                "score": round(score, 4),
                "examples": examples.get(g, [])[:3],
            }
        )

    # sort: taxonomy favors phrases and score; oos favors oos leakage
    if mode == "oos":
        candidates.sort(
            key=lambda x: (
                -x["support_oos"],
                -x["support_all"],
                -x["len"],
                -x["score"],
                x["token"],
            )
        )
    else:
        candidates.sort(
            key=lambda x: (-x["score"], -x["len"], -x["support_all"], x["token"])
        )

    return candidates[:top_n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since-hours", type=int, default=168)
    ap.add_argument("--mode", choices=["oos", "taxonomy"], default="taxonomy")
    ap.add_argument("--min-total-support", type=int, default=3)
    ap.add_argument("--min-oos-support", type=int, default=2)
    ap.add_argument("--ngram-min", type=int, default=2)
    ap.add_argument("--ngram-max", type=int, default=3)
    ap.add_argument("--min-length", type=int, default=4)
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--output-dir", default="out/oos_reports")
    args = ap.parse_args()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("Loading taxonomy aliases (EN)...")
    tax = load_taxonomy_aliases_en()
    print(f"Loaded {len(tax)} aliases")

    print(f"Loading EN titles since {args.since_hours}h...")
    titles = load_titles_en(args.since_hours)
    print(f"Loaded {len(titles)} titles; OOS={sum(1 for *_,o in titles if o)}")

    if not titles:
        print("No titles. Exit.")
        return

    cands = analyze(
        titles=titles,
        taxonomy_aliases=tax,
        mode=args.mode,
        min_total_support=args.min_total_support,
        min_oos_support=args.min_oos_support,
        ngram_min=args.ngram_min,
        ngram_max=args.ngram_max,
        min_len=args.min_length,
        top_n=args.top,
    )

    report = {
        "run": {
            "mode": args.mode,
            "since_hours": args.since_hours,
            "min_total_support": args.min_total_support,
            "min_oos_support": args.min_oos_support,
            "ngram_max": args.ngram_max,
            "min_length": args.min_length,
            "timestamp": datetime.utcnow().isoformat(),
        },
        "totals": {
            "titles_all": len(titles),
            "titles_oos": sum(1 for *_, o in titles if o),
        },
        "candidates": cands,
    }

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    outfile = outdir / f"keyword_candidates_{args.mode}_en_{ts}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Wrote {outfile}")
    print("Top 20:")
    for c in cands[:20]:
        print(
            f"  {c['token'][:40]:40s} score={c['score']:7.2f} all={c['support_all']:4d} pmi={c['pmi_like']:6.2f} anchors={c['anchor_hits']}"
        )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
classical_phrase_extractor.py

Goal:
  Classical extraction helpers for clustering:
    1) YAKE keyphrases (if available)
    2) RAKE keyphrases (lightweight built-in)
    3) Entities (spaCy if available; else simple fallback)
    4) Verb/action family tagging (deterministic)

Usage examples:
  python classical_phrase_extractor.py --since-hours 168 --limit 5000 --top 100
  python classical_phrase_extractor.py --month 2026-01 --centroid AMERICAS-USA --track geo_economy --top 150
  python classical_phrase_extractor.py --ctm-id <uuid> --top 200

Environment:
  DATABASE_URL or PG* vars (same as your other scripts).

Outputs:
  taxonomy_tools/out/classical_extract_<timestamp>.json
"""

import argparse
import datetime as dt
import json
import os
import re
from collections import Counter, defaultdict

from common import get_db_connection

# Optional dependencies
try:
    import psycopg2
except Exception:
    psycopg2 = None

try:
    import yake  # pip install yake
except Exception:
    yake = None

try:
    import spacy  # python -m spacy download en_core_web_sm
except Exception:
    spacy = None


# -----------------------------
# Normalization / tokenization
# -----------------------------
STOPWORDS_EN = {
    # minimal; extend as needed
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "at",
    "by",
    "from",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "it",
    "its",
    "their",
    "his",
    "her",
    "they",
    "them",
    "this",
    "that",
    "these",
    "those",
    "over",
    "under",
    "after",
    "before",
    "today",
    "live",
    "update",
    "says",
    "said",
    "say",
    "report",
    "reports",
    "reported",
    "explainer",
    "why",
    "how",
    "what",
    "record",
    "high",
    "hits",
    "rises",
    "falls",
    "edges",
    "higher",
    "lower",
    "ahead",
    "amid",
    "market",
    "markets",
    "stock",
    "stocks",
    "news",
}

PUNCT_RE = re.compile(r"[^\w\s\-]+", re.UNICODE)
WS_RE = re.compile(r"\s+", re.UNICODE)


def normalize_text(s: str) -> str:
    s = s.strip()
    s = s.replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-")
    s = s.lower()
    s = PUNCT_RE.sub(" ", s)
    s = WS_RE.sub(" ", s).strip()
    return s


def tokenize(s: str) -> list[str]:
    s = normalize_text(s)
    toks = [t for t in s.split() if t and t not in STOPWORDS_EN and len(t) >= 2]
    return toks


def extract_ngrams(tokens: list[str], n_min: int = 2, n_max: int = 3) -> list[str]:
    out = []
    L = len(tokens)
    for n in range(n_min, n_max + 1):
        for i in range(L - n + 1):
            g = " ".join(tokens[i : i + n])
            out.append(g)
    return out


# -----------------------------
# Verb / Action patterning
# -----------------------------
ACTION_FAMILIES = {
    # coercion / restriction
    "coercion": [
        r"\bsanction(s|ed|ing)?\b",
        r"\bembargo(es|ed)?\b",
        r"\bban(s|ned|ning)?\b",
        r"\brestrict(s|ed|ing)?\b",
        r"\bblacklist(s|ed|ing)?\b",
        r"\bseize(s|d|ing)?\b",
        r"\bdetain(s|ed|ing)?\b",
        r"\bconfiscat(e|es|ed|ing)\b",
        r"\bexport control(s)?\b",
        r"\btariff(s)?\b",
        r"\bdut(y|ies)\b",
        r"\bcountermeasure(s)?\b",
        r"\bretaliat(e|es|ed|ing)\b",
    ],
    # trade flow
    "trade_flow": [
        r"\bexport(s|ed|ing)?\b",
        r"\bimport(s|ed|ing)?\b",
        r"\bship(s|ped|ping)?\b",
        r"\bsupply\b",
        r"\bdeliver(y|ies)\b",
        r"\bpurchase(s|d|ing)?\b",
        r"\bsale(s)?\b",
        r"\bdeal(s)?\b",
        r"\bagreement(s)?\b",
    ],
    # production / capacity
    "production": [
        r"\bproduce(s|d|ing)?\b",
        r"\boutput\b",
        r"\bproduction\b",
        r"\brefiner(y|ies)\b",
        r"\bdrill(s|ed|ing)?\b",
        r"\bcapacity\b",
        r"\bfield(s)?\b",
        r"\boffshore\b",
        r"\bonshore\b",
    ],
    # transport / maritime
    "maritime": [
        r"\btanker(s)?\b",
        r"\bvessel(s)?\b",
        r"\bship(s)?\b",
        r"\bport(s)?\b",
        r"\bmaritime\b",
        r"\bstrait(s)?\b",
        r"\bseaborne\b",
    ],
    # prices / markets
    "prices_market": [
        r"\bprice(s)?\b",
        r"\bmarket(s)?\b",
        r"\bfutures\b",
        r"\bspot\b",
        r"\brally\b",
        r"\brecord\b",
        r"\byield(s)?\b",
    ],
}


def detect_actions(title: str) -> list[str]:
    t = normalize_text(title)
    hits = []
    for fam, patterns in ACTION_FAMILIES.items():
        for pat in patterns:
            if re.search(pat, t):
                hits.append(fam)
                break
    return hits


# -----------------------------
# Entities extraction
# -----------------------------
COUNTRY_LIKE = {
    # tiny fallback seed; extend or wire to your centroid list if you want
    "usa",
    "u.s",
    "united states",
    "china",
    "russia",
    "iran",
    "venezuela",
    "cuba",
    "canada",
    "uk",
    "taiwan",
    "india",
    "germany",
    "france",
    "european union",
    "eu",
}


def extract_entities_spacy(titles: list[str]) -> list[list[str]]:
    # best effort: use en_core_web_sm if present
    nlp = None
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        return [extract_entities_fallback(x) for x in titles]

    out = []
    for s in titles:
        doc = nlp(s)
        ents = []
        for ent in doc.ents:
            if ent.label_ in {"PERSON", "ORG", "GPE", "NORP", "PRODUCT"}:
                txt = ent.text.strip()
                if len(txt) >= 2:
                    ents.append(txt)
        out.append(list(dict.fromkeys(ents))[:12])
    return out


def extract_entities_fallback(title: str) -> list[str]:
    # fallback: grab capitalized sequences + a few country-like patterns
    ents = []
    # capitalized phrases
    cap = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b", title)
    ents.extend(cap)
    # country-like via simple substring checks
    low = normalize_text(title)
    for c in COUNTRY_LIKE:
        if c in low:
            ents.append(c.upper() if c in {"usa", "eu", "uk"} else c.title())
    # de-dup + cap count
    uniq = []
    seen = set()
    for e in ents:
        e2 = e.strip()
        if not e2:
            continue
        k = e2.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(e2)
    return uniq[:12]


# -----------------------------
# RAKE (lightweight)
# -----------------------------
def rake_phrases(text: str, min_words: int = 2, max_words: int = 4) -> list[str]:
    """
    Very small RAKE-like extractor:
      - split on stopwords
      - score phrases by word frequency/degree
    """
    norm = normalize_text(text)
    words = norm.split()

    # split into candidate phrases
    phrases = []
    cur = []
    for w in words:
        if w in STOPWORDS_EN or len(w) < 2:
            if cur:
                phrases.append(cur)
                cur = []
        else:
            cur.append(w)
    if cur:
        phrases.append(cur)

    # filter by length
    phrases = [p for p in phrases if min_words <= len(p) <= max_words]
    if not phrases:
        return []

    # word freq and degree
    freq = Counter()
    deg = Counter()
    for p in phrases:
        unique = p
        length = len(unique)
        for w in unique:
            freq[w] += 1
            deg[w] += length - 1

    # word scores
    wscore = {}
    for w in freq:
        wscore[w] = (deg[w] + freq[w]) / float(freq[w])

    # phrase scores
    scored = []
    for p in phrases:
        score = sum(wscore[w] for w in p)
        scored.append((" ".join(p), score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in scored[:10]]


# -----------------------------
# DB access (similar spirit)
# -----------------------------


def fetch_titles(
    conn,
    since_hours=None,
    month=None,
    ctm_id=None,
    centroid=None,
    track=None,
    limit=5000,
):
    """
    Fetch titles for phrase extraction.

    Args:
        ctm_id: Direct CTM UUID (highest priority)
        centroid: Centroid ID like 'AMERICAS-USA'
        track: Track like 'geo_economy'
        month: Month string like '2026-01'
        since_hours: Alternative to month - fetch recent titles
        limit: Max titles to return
    """
    cur = conn.cursor()

    # If CTM ID provided, use it directly
    if ctm_id:
        sql = """
            SELECT t.id::text, t.title_display, t.pubdate_utc::text
            FROM titles_v3 t
            WHERE t.id IN (
                SELECT DISTINCT a.title_id FROM title_assignments a WHERE a.ctm_id = %s
            )
            ORDER BY t.pubdate_utc DESC
            LIMIT %s
        """
        cur.execute(sql, (ctm_id, int(limit)))

    # If centroid + track + month provided
    elif centroid and track and month:
        sql = """
            SELECT t.id::text, t.title_display, t.pubdate_utc::text
            FROM titles_v3 t
            WHERE t.id IN (
                SELECT DISTINCT a.title_id
                FROM title_assignments a
                WHERE a.centroid_id = %s
                  AND a.track = %s
            )
              AND to_char(t.pubdate_utc, 'YYYY-MM') = %s
              AND t.processing_status = 'assigned'
            ORDER BY t.pubdate_utc DESC
            LIMIT %s
        """
        cur.execute(sql, (centroid, track, month, int(limit)))

    # If since_hours provided (recent titles)
    elif since_hours is not None:
        sql = """
            SELECT t.id::text, t.title_display, t.pubdate_utc::text
            FROM titles_v3 t
            WHERE t.processing_status = 'assigned'
              AND t.pubdate_utc >= (NOW() - INTERVAL '%s hours')
            ORDER BY t.pubdate_utc DESC
            LIMIT %s
        """
        cur.execute(sql, (int(since_hours), int(limit)))

    else:
        raise ValueError(
            "Must provide ctm_id, or (centroid + track + month), or since_hours"
        )

    rows = cur.fetchall()
    return [{"id": r[0], "title": r[1], "pubdate_utc": r[2]} for r in rows]


# -----------------------------
# Analysis
# -----------------------------
def analyze_titles(title_rows, top_n=100, ngram_min=2, ngram_max=3, min_support=3):
    titles = [r["title"] for r in title_rows]
    examples = defaultdict(list)

    # 1) YAKE (if available)
    yake_out = Counter()
    if yake is not None:
        kw = yake.KeywordExtractor(
            lan="en", n=3, top=30
        )  # 1-3 grams; we will filter lengths
        for t in titles:
            for phrase, score in kw.extract_keywords(t):
                p = normalize_text(phrase)
                wcount = len(p.split())
                if wcount < ngram_min or wcount > ngram_max:
                    continue
                if any(w in STOPWORDS_EN for w in p.split()):
                    continue
                yake_out[p] += 1
                if len(examples[p]) < 3:
                    examples[p].append(t)

    # 2) RAKE (built-in)
    rake_out = Counter()
    for t in titles:
        for p in rake_phrases(t, min_words=ngram_min, max_words=min(4, ngram_max)):
            p = normalize_text(p)
            if len(p.split()) < ngram_min or len(p.split()) > ngram_max:
                continue
            rake_out[p] += 1
            if len(examples[p]) < 3:
                examples[p].append(t)

    # 3) N-gram frequency (baseline, n>=2 only)
    ngram_out = Counter()
    for t in titles:
        toks = tokenize(t)
        for g in extract_ngrams(toks, n_min=ngram_min, n_max=ngram_max):
            # hard reject punctuation artefacts (should be clean already)
            if re.search(r"[,:|]", g):
                continue
            ngram_out[g] += 1
            if len(examples[g]) < 3:
                examples[g].append(t)

    # 4) Entities
    entity_out = Counter()
    if spacy is not None:
        ent_lists = extract_entities_spacy(titles)
    else:
        ent_lists = [extract_entities_fallback(t) for t in titles]

    for t, ents in zip(titles, ent_lists):
        for e in ents:
            e_norm = e.strip()
            if len(e_norm) < 3:
                continue
            entity_out[e_norm] += 1

    # 5) Actions
    action_out = Counter()
    for t in titles:
        for fam in detect_actions(t):
            action_out[fam] += 1

    def pack(counter: Counter, label: str):
        items = []
        for k, v in counter.most_common():
            if v < min_support:
                continue
            items.append(
                {
                    "phrase": k,
                    "support": v,
                    "examples": examples.get(k, [])[:3],
                    "source": label,
                }
            )
            if len(items) >= top_n:
                break
        return items

    report = {
        "meta": {
            "title_count": len(titles),
            "ngram_min": ngram_min,
            "ngram_max": ngram_max,
            "min_support": min_support,
            "yake_available": yake is not None,
            "spacy_available": spacy is not None,
        },
        "keyphrases": {
            "yake": pack(yake_out, "yake"),
            "rake": pack(rake_out, "rake"),
            "ngram_freq": pack(ngram_out, "ngram_freq"),
        },
        "entities": [
            {"entity": k, "support": v}
            for k, v in entity_out.most_common(top_n)
            if v >= min_support
        ],
        "actions": [
            {"action_family": k, "support": v} for k, v in action_out.most_common()
        ],
    }
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since-hours", type=int, default=None)
    ap.add_argument("--month", type=str, default=None)  # e.g. 2026-01
    ap.add_argument("--ctm-id", type=str, default=None)
    ap.add_argument(
        "--centroid", type=str, default=None
    )  # centroid_key e.g. AMERICAS-USA
    ap.add_argument("--track", type=str, default=None)  # track key e.g. geo_economy
    ap.add_argument("--limit", type=int, default=5000)

    ap.add_argument("--top", type=int, default=150)
    ap.add_argument("--ngram-min", type=int, default=2)
    ap.add_argument("--ngram-max", type=int, default=3)
    ap.add_argument("--min-support", type=int, default=3)

    ap.add_argument("--out", type=str, default=None)

    args = ap.parse_args()

    if psycopg2 is None:
        raise SystemExit(
            "psycopg2 is required for DB mode. Install it or adapt fetch to your local file input."
        )

    conn = get_db_connection()
    rows = fetch_titles(
        conn,
        since_hours=args.since_hours,
        month=args.month,
        ctm_id=args.ctm_id,
        centroid=args.centroid,
        track=args.track,
        limit=args.limit,
    )
    conn.close()

    report = analyze_titles(
        rows,
        top_n=args.top,
        ngram_min=args.ngram_min,
        ngram_max=args.ngram_max,
        min_support=args.min_support,
    )

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = args.out or f"taxonomy_tools/out/classical_extract_{ts}.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Wrote: {out_path}")
    print(f"Titles analyzed: {report['meta']['title_count']}")
    print(
        f"YAKE available: {report['meta']['yake_available']} | spaCy available: {report['meta']['spacy_available']}"
    )


if __name__ == "__main__":
    main()

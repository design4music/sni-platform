"""Standalone inspector — no shared imports, just runs Variant E on the
Security CTM and prints all clusters of size >= 4."""

import io
import re
import sys

import psycopg2

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from collections import Counter  # noqa: E402

RENDER = "postgresql://maxgenrih55:DGiBGNv89pGtRsaj5Ys2fCN4DFMEmCUb@dpg-d5uem563jp1c739ufrsg-a.frankfurt-postgres.render.com/sni_v2"
HF_PERSONS = {"TRUMP", "BIDEN", "PUTIN", "ZELENSKY", "XI"}
HF_ORGS = {"PENTAGON", "IDF", "NATO", "FBI", "CIA", "UN", "EU", "WHITE HOUSE"}
NGRAM_STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "in",
    "on",
    "at",
    "for",
    "with",
    "and",
    "or",
    "but",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "have",
    "has",
    "had",
    "as",
    "by",
    "from",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "his",
    "her",
    "their",
    "our",
    "your",
    "my",
}
STRONG_MIN = 2  # entity must be present in >= 2 titles to count as strong


def extract_entities(t):
    ents = set()
    for sig_type in ("persons", "orgs", "places", "named_events"):
        for v in t.get(sig_type) or []:
            n = v.upper() if sig_type == "persons" else v
            if sig_type == "persons" and n in HF_PERSONS:
                continue
            if sig_type == "orgs" and n in HF_ORGS:
                continue
            ents.add(f"{sig_type}:{n}")
    return ents


def compute_ngrams(text):
    text = (text or "").lower()
    text = re.sub(r"[^\w\s]", " ", text)
    words = [w for w in text.split() if w not in NGRAM_STOPWORDS and len(w) > 1]
    return {" ".join(words[i : i + 3]) for i in range(len(words) - 2)}


def strong_entities(cluster):
    n = len(cluster["titles"])
    if n == 1:
        # Singletons: every entity counts (otherwise nothing seeds merges)
        return set(cluster["entity_counts"].keys())
    return {e for e, c in cluster["entity_counts"].items() if c >= STRONG_MIN}


def can_merge(a, b):
    if a["entity_counts"] and b["entity_counts"]:
        common = strong_entities(a) & strong_entities(b)
        if common:
            return ("entity", sorted(common))
    if a["ngrams"] is None:
        a["ngrams"] = set().union(
            *(compute_ngrams(t["title_display"]) for t in a["titles"])
        )
    if b["ngrams"] is None:
        b["ngrams"] = set().union(
            *(compute_ngrams(t["title_display"]) for t in b["titles"])
        )
    if a["ngrams"] and b["ngrams"]:
        common = a["ngrams"] & b["ngrams"]
        if common:
            return ("ngram", sorted(common)[:3])
    return None


def cluster_variant_e(titles):
    cs = []
    for t in titles:
        ents = extract_entities(t)
        cs.append({"titles": [t], "entity_counts": Counter(ents), "ngrams": None})
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(cs):
            j = i + 1
            while j < len(cs):
                m = can_merge(cs[i], cs[j])
                if m:
                    cs[i]["titles"].extend(cs[j]["titles"])
                    cs[i]["entity_counts"] += cs[j]["entity_counts"]
                    if cs[j]["ngrams"]:
                        if cs[i]["ngrams"] is None:
                            cs[i]["ngrams"] = set()
                        cs[i]["ngrams"] |= cs[j]["ngrams"]
                    cs.pop(j)
                    changed = True
                else:
                    j += 1
            i += 1
    return cs


def load(conn, ctm, date):
    cur = conn.cursor()
    cur.execute(
        """SELECT t.id, t.title_display, t.publisher_name,
                  tl.persons, tl.orgs, tl.places, tl.named_events
             FROM event_v3_titles evt
             JOIN events_v3 e ON e.id = evt.event_id
             JOIN titles_v3 t ON t.id = evt.title_id
             LEFT JOIN title_labels tl ON tl.title_id = t.id
            WHERE e.ctm_id = %s AND e.date = %s::date AND e.merged_into IS NULL
            ORDER BY t.pubdate_utc""",
        (ctm, date),
    )
    return [
        {
            "id": r[0],
            "title_display": r[1] or "",
            "publisher": r[2] or "",
            "persons": r[3] or [],
            "orgs": r[4] or [],
            "places": r[5] or [],
            "named_events": r[6] or [],
        }
        for r in cur.fetchall()
    ]


def main():
    conn = psycopg2.connect(RENDER, connect_timeout=30)
    ts = load(conn, "dd6f66aa-c362-42e9-a9dc-bc9ef9d95b35", "2026-04-29")
    try:
        print(f"{len(ts)} titles")
        clusters = cluster_variant_e(ts)
        for c in sorted(clusters, key=lambda c: -len(c["titles"])):
            if len(c["titles"]) < 4:
                continue
            cnt = Counter()
            for t in c["titles"]:
                for e in extract_entities(t):
                    cnt[e] += 1
            spine = cnt.most_common(1)[0][0] if cnt else "(ngram-only)"
            print(f'\nsize={len(c["titles"]):3}  spine={spine}')
            for t in c["titles"][:6]:
                print(f'  {t["title_display"][:95]}')
    finally:
        conn.close()


if __name__ == "__main__":
    main()

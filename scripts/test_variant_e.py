"""Variant E test: drop industries + require shared bridge entity to be
"strong" in BOTH clusters (present in >= ceil(0.3 * size), min 2 for
non-singletons). Singletons keep current behavior so seed merges work.
"""

import io
import math
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from collections import Counter  # noqa: E402

import psycopg2  # noqa: E402

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
STRONG_FRACTION = 0.3
STRONG_MIN = 2


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
        return cluster["entity_counts"].keys() | set()
    threshold = max(STRONG_MIN, math.ceil(n * STRONG_FRACTION))
    return {e for e, c in cluster["entity_counts"].items() if c >= threshold}


def can_merge_v_e(a, b):
    """Variant E: shared entity must be strong in BOTH clusters."""
    if a["entity_counts"] and b["entity_counts"]:
        a_strong = strong_entities(a)
        b_strong = strong_entities(b)
        common = a_strong & b_strong
        if common:
            return ("entity_strong", sorted(common))
    # Ngram fallback unchanged
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
            return ("ngram", sorted(common)[:5])
    return None


def can_merge_current(a, b):
    """Current: any shared entity OR shared ngram."""
    if a["entities"] and b["entities"]:
        if a["entities"] & b["entities"]:
            return True
    if a["ngrams"] is None:
        a["ngrams"] = set().union(
            *(compute_ngrams(t["title_display"]) for t in a["titles"])
        )
    if b["ngrams"] is None:
        b["ngrams"] = set().union(
            *(compute_ngrams(t["title_display"]) for t in b["titles"])
        )
    if a["ngrams"] and b["ngrams"]:
        return bool(a["ngrams"] & b["ngrams"])
    return False


def cluster_current(titles):
    """Current algorithm — drop industries baseline (Variant A)."""
    cs = []
    for t in titles:
        cs.append(
            {
                "titles": [t],
                "entities": extract_entities(t),
                "ngrams": None,
            }
        )
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(cs):
            j = i + 1
            while j < len(cs):
                if can_merge_current(cs[i], cs[j]):
                    cs[i]["titles"].extend(cs[j]["titles"])
                    cs[i]["entities"] |= cs[j]["entities"]
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


def cluster_variant_e(titles):
    """Variant E: strong-entity rule."""
    cs = []
    for t in titles:
        ents = extract_entities(t)
        cs.append(
            {
                "titles": [t],
                "entity_counts": Counter(ents),
                "ngrams": None,
            }
        )
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(cs):
            j = i + 1
            while j < len(cs):
                m = can_merge_v_e(cs[i], cs[j])
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
    out = [
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
    cur.close()
    return out


def show(label, clusters):
    print(f"\n  {label}: {len(clusters)} clusters")
    for c in sorted(clusters, key=lambda c: -len(c["titles"]))[:6]:
        size = len(c["titles"])
        if size < 3:
            continue
        # Pick spine: most common entity
        cnt = Counter()
        for t in c["titles"]:
            for e in extract_entities(t):
                cnt[e] += 1
        spine = cnt.most_common(1)[0][0] if cnt else "(ngram-only)"
        print(f"    size={size:3d}  spine={spine}")
        for t in c["titles"][:3]:
            print(f"        {t['title_display'][:90]}")


def main():
    conn = psycopg2.connect(RENDER, connect_timeout=30)
    targets = [
        ("8e9a06ce-524d-4e70-8429-9ed964654519", "2026-04-28", "UAE leaves OPEC"),
        (
            "dd6f66aa-c362-42e9-a9dc-bc9ef9d95b35",
            "2026-04-29",
            "USA/Politics Charles-Merz",
        ),
        (
            "0daae61d-4992-4773-b4be-f95f5b740b34",
            "2026-05-02",
            "USA/Security 5000 troops",
        ),
        (
            "2cfa6687-cc88-4300-8461-b7139c84a9fb",
            "2026-05-01",
            "USA/Economy ChatGPT/Apple",
        ),
    ]
    for ctm, date, label in targets:
        print("\n" + "=" * 80)
        print(f"{label}  ({ctm} / {date})")
        ts = load(conn, ctm, date)
        print(f"  {len(ts)} titles")
        if not ts:
            continue
        show("CURRENT (industries dropped, no strong rule)", cluster_current(ts))
        show(
            "VARIANT E (industries dropped + strong-entity rule)", cluster_variant_e(ts)
        )
    conn.close()


if __name__ == "__main__":
    main()

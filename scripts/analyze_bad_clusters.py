"""For each suspect CTM, run the clusterer and DIAGNOSE what bridges
unrelated titles. Goal: understand exactly which entity caused a bad
merge so we can decide whether the entity should be filtered.

For each cluster larger than 1 title, we report:
  - Cluster spine + size
  - First few titles
  - The bridging entity for each merge step (the shared token)
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import re  # noqa: E402
from collections import Counter  # noqa: E402

import psycopg2  # noqa: E402

RENDER_URL = (
    "postgresql://maxgenrih55:DGiBGNv89pGtRsaj5Ys2fCN4DFMEmCUb@"
    "dpg-d5uem563jp1c739ufrsg-a.frankfurt-postgres.render.com/sni_v2"
)

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


def extract_entities(title, drop_industries=True):
    ents = set()
    sig_types = ["persons", "orgs", "places", "named_events"]
    if not drop_industries:
        sig_types.append("industries")
    for sig_type in sig_types:
        for v in title.get(sig_type) or []:
            normalized = v.upper() if sig_type == "persons" else v
            if sig_type == "persons" and normalized in HF_PERSONS:
                continue
            if sig_type == "orgs" and normalized in HF_ORGS:
                continue
            ents.add(f"{sig_type}:{normalized}")
    return ents


def compute_ngrams(text):
    text = (text or "").lower()
    text = re.sub(r"[^\w\s]", " ", text)
    words = [w for w in text.split() if w not in NGRAM_STOPWORDS and len(w) > 1]
    return {" ".join(words[i : i + 3]) for i in range(len(words) - 2)}


def cluster_with_history(titles, drop_industries=True):
    """Cluster via single-link, but ALSO record the bridging entity for
    every merge so we can diagnose what chained things together."""
    clusters = []
    for t in titles:
        clusters.append(
            {
                "titles": [t],
                "entities": extract_entities(t, drop_industries),
                "ngrams": None,  # lazy
                "merges": [],  # list of (left_titles_sample, right_titles_sample, bridge)
            }
        )

    def get_ngrams(c):
        if c["ngrams"] is None:
            grams = set()
            for t in c["titles"]:
                grams |= compute_ngrams(t["title_display"])
            c["ngrams"] = grams
        return c["ngrams"]

    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(clusters):
            j = i + 1
            while j < len(clusters):
                a, b = clusters[i], clusters[j]
                bridge = None
                if a["entities"] and b["entities"]:
                    common = a["entities"] & b["entities"]
                    if common:
                        bridge = ("entity", sorted(common))
                if not bridge:
                    ng_a = (
                        get_ngrams(a)
                        if (not a["entities"]) or (not b["entities"])
                        else None
                    )
                    ng_b = (
                        get_ngrams(b)
                        if (not a["entities"]) or (not b["entities"])
                        else None
                    )
                    if ng_a and ng_b:
                        common = ng_a & ng_b
                        if common:
                            bridge = ("ngram", sorted(common)[:5])
                if bridge:
                    # Record the merge with samples
                    a["merges"].append(
                        {
                            "left_sample": a["titles"][0]["title_display"][:70],
                            "right_sample": b["titles"][0]["title_display"][:70],
                            "bridge_kind": bridge[0],
                            "bridge_value": bridge[1],
                        }
                    )
                    a["titles"].extend(b["titles"])
                    a["entities"] |= b["entities"]
                    if b["ngrams"]:
                        if a["ngrams"] is None:
                            a["ngrams"] = set()
                        a["ngrams"] |= b["ngrams"]
                    a["merges"].extend(b["merges"])
                    clusters.pop(j)
                    changed = True
                else:
                    j += 1
            i += 1
    return clusters


def load_ctm_titles(conn, ctm_id, date):
    cur = conn.cursor()
    cur.execute(
        """SELECT t.id, t.title_display, t.publisher_name,
                  tl.persons, tl.orgs, tl.places, tl.named_events, tl.industries
             FROM event_v3_titles evt
             JOIN events_v3 e ON e.id = evt.event_id
             JOIN titles_v3 t ON t.id = evt.title_id
             LEFT JOIN title_labels tl ON tl.title_id = t.id
            WHERE e.ctm_id = %s AND e.date = %s::date AND e.merged_into IS NULL
            ORDER BY t.pubdate_utc""",
        (ctm_id, date),
    )
    out = []
    for r in cur.fetchall():
        out.append(
            {
                "id": r[0],
                "title_display": r[1] or "",
                "publisher": r[2] or "",
                "persons": r[3] or [],
                "orgs": r[4] or [],
                "places": r[5] or [],
                "named_events": r[6] or [],
                "industries": r[7] or [],
            }
        )
    cur.close()
    return out


def diagnose(conn, ctm_id, date, label):
    print(f"\n{'=' * 80}\n{label}\nCTM {ctm_id}  date {date}")
    titles = load_ctm_titles(conn, ctm_id, date)
    print(f"  {len(titles)} titles loaded")
    if not titles:
        return
    clusters = cluster_with_history(titles, drop_industries=True)
    by_size = sorted(clusters, key=lambda c: -len(c["titles"]))
    print(f"  → {len(clusters)} clusters with industries dropped")

    # Focus on suspicious clusters (size >= 5, mixed-looking)
    for ci, c in enumerate(by_size[:6], 1):
        size = len(c["titles"])
        if size < 3:
            continue
        # Pick spine
        counter = Counter()
        for t in c["titles"]:
            for e in extract_entities(t):
                counter[e] += 1
        spine = counter.most_common(1)[0][0] if counter else "(ngram-fallback)"
        print(f"\n  --- Cluster #{ci}: size={size}, spine={spine} ---")
        for t in c["titles"][:6]:
            print(f"      [{t['publisher'][:18]:18s}] {t['title_display'][:90]}")
        if size > 6:
            print(f"      ... and {size - 6} more")

        # Show the bridges that formed this cluster
        if c["merges"]:
            print(f"      ── BRIDGES ({len(c['merges'])} merge events) ──")
            # Show distinct bridge values
            bridge_counter = Counter()
            for m in c["merges"]:
                for v in m["bridge_value"]:
                    bridge_counter[(m["bridge_kind"], v)] += 1
            for (kind, val), n in bridge_counter.most_common(8):
                marker = "ENT" if kind == "entity" else "NGM"
                print(f"      {marker}  ×{n:2d}  {val}")


def main():
    conn = psycopg2.connect(RENDER_URL, connect_timeout=30)
    try:
        # Suspects from the auto-find earlier
        targets = [
            (
                "8e9a06ce-524d-4e70-8429-9ed964654519",
                "2026-04-28",
                "Saudi Arabia / Energy (UAE leaves OPEC)",
            ),
            (
                "dd6f66aa-c362-42e9-a9dc-bc9ef9d95b35",
                "2026-04-29",
                "USA / Politics (Charles state visit)",
            ),
            (
                "0daae61d-4992-4773-b4be-f95f5b740b34",
                "2026-05-02",
                "USA / Security (5000 troops Germany)",
            ),
            (
                "717a8d6c-ce46-476c-a338-6caf063bd3af",
                "2026-04-28",
                "USA / Economy (OpenAI IPO)",
            ),
            (
                "2cfa6687-cc88-4300-8461-b7139c84a9fb",
                "2026-05-01",
                "USA / Economy (May 1, the original)",
            ),
        ]
        for ctm_id, date, label in targets:
            diagnose(conn, ctm_id, date, label)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

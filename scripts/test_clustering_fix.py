"""Dry-run test of the proposed clustering fix.

Loads titles for given CTMs from Render, runs the CURRENT clustering
algorithm and a PROPOSED variant side-by-side, prints comparative
clusters. No DB writes.

Variants:
  A: drop `industries` from the discriminating-entities set
  B: A + add OPEC/IMF to HIGH_FREQ_ORGS
  C: B + add ORBAN/NETANYAHU/VANCE/MERZ/MELONI/LULA/STARMER/CHARLES/MUSK
     to HIGH_FREQ_PERSONS

Usage:
  python scripts/test_clustering_fix.py            # default CTMs
  python scripts/test_clustering_fix.py <ctm_id>   # specific CTM
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))

RENDER_URL = (
    "postgresql://maxgenrih55:DGiBGNv89pGtRsaj5Ys2fCN4DFMEmCUb@"
    "dpg-d5uem563jp1c739ufrsg-a.frankfurt-postgres.render.com/sni_v2"
)

# Existing filters from core/config.py
HF_PERSONS_CURRENT = {"TRUMP", "BIDEN", "PUTIN", "ZELENSKY", "XI"}
HF_ORGS_CURRENT = {"PENTAGON", "IDF", "NATO", "FBI", "CIA", "UN", "EU", "WHITE HOUSE"}

# Proposed extensions
HF_ORGS_PROPOSED = HF_ORGS_CURRENT | {"OPEC", "IMF"}
HF_PERSONS_PROPOSED = HF_PERSONS_CURRENT | {
    "ORBAN",
    "NETANYAHU",
    "VANCE",
    "MERZ",
    "MELONI",
    "LULA",
    "STARMER",
    "CHARLES",
    "MUSK",
}

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


def extract_entities(title, drop_industries, hf_orgs, hf_persons):
    """Build the discriminating-entity set for one title."""
    ents = set()
    sig_types = ["persons", "orgs", "places", "named_events"]
    if not drop_industries:
        sig_types.append("industries")
    for sig_type in sig_types:
        for v in title.get(sig_type) or []:
            normalized = v.upper() if sig_type == "persons" else v
            if sig_type == "persons" and normalized in hf_persons:
                continue
            if sig_type == "orgs" and normalized in hf_orgs:
                continue
            ents.add("{}:{}".format(sig_type, normalized))
    return ents


def compute_ngrams(titles):
    grams = set()
    for t in titles:
        text = (t.get("title_display") or "").lower()
        text = re.sub(r"[^\w\s]", " ", text)
        words = [w for w in text.split() if w not in NGRAM_STOPWORDS and len(w) > 1]
        for i in range(len(words) - 2):
            grams.add(" ".join(words[i : i + 3]))
    return grams


def can_merge(a, b):
    if a["entities"] and b["entities"]:
        return bool(a["entities"] & b["entities"])
    if a.get("ngrams") is None:
        a["ngrams"] = compute_ngrams(a["titles"])
    if b.get("ngrams") is None:
        b["ngrams"] = compute_ngrams(b["titles"])
    if a["ngrams"] and b["ngrams"]:
        return bool(a["ngrams"] & b["ngrams"])
    return False


def cluster(titles, drop_industries, hf_orgs, hf_persons):
    clusters = []
    for t in titles:
        clusters.append(
            {
                "titles": [t],
                "entities": extract_entities(t, drop_industries, hf_orgs, hf_persons),
                "ngrams": None,
            }
        )
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(clusters):
            j = i + 1
            while j < len(clusters):
                if can_merge(clusters[i], clusters[j]):
                    clusters[i]["titles"].extend(clusters[j]["titles"])
                    clusters[i]["entities"] |= clusters[j]["entities"]
                    if clusters[j].get("ngrams"):
                        if clusters[i].get("ngrams") is None:
                            clusters[i]["ngrams"] = set()
                        clusters[i]["ngrams"] |= clusters[j]["ngrams"]
                    clusters.pop(j)
                    changed = True
                else:
                    j += 1
            i += 1
    return clusters


def dominant_entity(titles, drop_industries, hf_orgs, hf_persons):
    counter = Counter()
    sig_types = ["persons", "orgs", "places", "named_events"]
    if not drop_industries:
        sig_types.append("industries")
    for t in titles:
        for sig_type in sig_types:
            for v in t.get(sig_type) or []:
                normalized = v.upper() if sig_type == "persons" else v
                if sig_type == "persons" and normalized in hf_persons:
                    continue
                if sig_type == "orgs" and normalized in hf_orgs:
                    continue
                counter["{}:{}".format(sig_type, normalized)] += 1
    if not counter:
        return "(none)"
    return counter.most_common(1)[0][0]


def load_titles_by_date(conn, ctm_id, target_date):
    """Load all titles for a (ctm, single date) — matches production
    cluster_by_day_beat which clusters per-day."""
    cur = conn.cursor()
    cur.execute(
        """SELECT t.id, t.title_display, t.publisher_name,
                  tl.persons, tl.orgs, tl.places, tl.named_events, tl.industries
             FROM event_v3_titles evt
             JOIN events_v3 e ON e.id = evt.event_id
             JOIN titles_v3 t ON t.id = evt.title_id
             LEFT JOIN title_labels tl ON tl.title_id = t.id
            WHERE e.ctm_id = %s
              AND e.date = %s::date
              AND e.merged_into IS NULL
            ORDER BY t.pubdate_utc""",
        (ctm_id, target_date),
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


def print_clusters(clusters, label, hf_orgs, hf_persons, drop_industries):
    print(f"\n----- {label}: {len(clusters)} clusters -----")
    by_size = sorted(clusters, key=lambda c: -len(c["titles"]))
    for i, c in enumerate(by_size[:8], 1):
        dom = dominant_entity(c["titles"], drop_industries, hf_orgs, hf_persons)
        print(f"  Cluster #{i}  size={len(c['titles']):3d}  spine={dom}")
        for t in c["titles"][:5]:
            ttl = (t["title_display"] or "")[:90]
            print(f"      [{t['publisher'][:18]:18s}] {ttl}")
        if len(c["titles"]) > 5:
            print(f"      ... and {len(c['titles']) - 5} more")
    if len(by_size) > 8:
        rest = sum(len(c["titles"]) for c in by_size[8:])
        print(f"  + {len(by_size) - 8} smaller clusters covering {rest} titles")


def run_test(conn, ctm_id, date):
    print("=" * 80)
    print(f"CTM {ctm_id}  date {date}")
    titles = load_titles_by_date(conn, ctm_id, date)
    print(f"  {len(titles)} titles loaded")
    if not titles:
        return

    # Current behavior
    current = cluster(
        titles,
        drop_industries=False,
        hf_orgs=HF_ORGS_CURRENT,
        hf_persons=HF_PERSONS_CURRENT,
    )
    print_clusters(
        current,
        "CURRENT (industries kept)",
        HF_ORGS_CURRENT,
        HF_PERSONS_CURRENT,
        drop_industries=False,
    )

    # Variant A
    variant_a = cluster(
        titles,
        drop_industries=True,
        hf_orgs=HF_ORGS_CURRENT,
        hf_persons=HF_PERSONS_CURRENT,
    )
    print_clusters(
        variant_a,
        "A: drop industries",
        HF_ORGS_CURRENT,
        HF_PERSONS_CURRENT,
        drop_industries=True,
    )

    # Variant B
    variant_b = cluster(
        titles,
        drop_industries=True,
        hf_orgs=HF_ORGS_PROPOSED,
        hf_persons=HF_PERSONS_CURRENT,
    )
    print_clusters(
        variant_b,
        "B: A + filter OPEC/IMF",
        HF_ORGS_PROPOSED,
        HF_PERSONS_CURRENT,
        drop_industries=True,
    )

    # Variant C
    variant_c = cluster(
        titles,
        drop_industries=True,
        hf_orgs=HF_ORGS_PROPOSED,
        hf_persons=HF_PERSONS_PROPOSED,
    )
    print_clusters(
        variant_c,
        "C: B + filter Orban/Netanyahu/Vance/etc",
        HF_ORGS_PROPOSED,
        HF_PERSONS_PROPOSED,
        drop_industries=True,
    )


def find_suspect_ctms(conn, limit=5):
    """Find recent CTMs with high-source-count single events — likely the
    over-clustered ones."""
    cur = conn.cursor()
    cur.execute(
        """SELECT e.ctm_id, e.date::text, e.source_batch_count, cv.label, c.track,
                  e.id, LEFT(COALESCE(e.title, ''), 80) AS title
             FROM events_v3 e
             JOIN ctm c ON c.id = e.ctm_id
             JOIN centroids_v3 cv ON cv.id = c.centroid_id
            WHERE e.is_promoted = true
              AND e.merged_into IS NULL
              AND e.date >= CURRENT_DATE - INTERVAL '7 days'
              AND e.source_batch_count >= 30
            ORDER BY e.source_batch_count DESC
            LIMIT %s""",
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ctm", help="Specific CTM id to test (with --date)")
    parser.add_argument("--date", help="Date for --ctm (YYYY-MM-DD)")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-find suspect CTMs from recent activity",
    )
    args = parser.parse_args()

    conn = psycopg2.connect(RENDER_URL, connect_timeout=30)
    try:
        if args.ctm and args.date:
            run_test(conn, args.ctm, args.date)
        elif args.auto:
            suspects = find_suspect_ctms(conn)
            print(f"Found {len(suspects)} suspect CTMs (recent, large clusters):\n")
            for ctm_id, date, src, label, track, eid, title in suspects:
                print(f"  {ctm_id}  {date}  {label} / {track}  src={src}  {title}")
            for ctm_id, date, src, label, track, eid, title in suspects:
                run_test(conn, ctm_id, date)
        else:
            # Default: known-bad ChatGPT/Apple cluster
            run_test(conn, "2cfa6687-cc88-4300-8461-b7139c84a9fb", "2026-05-01")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

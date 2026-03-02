"""
Event Saga Chaining

Links events that are the same ongoing story within and across months/tracks
using IDF-weighted tag overlap + title word Dice similarity.

Same-track pairs: threshold 0.35 (intra-month + cross-month)
Cross-track pairs: threshold 0.38 (same centroid, different tracks)

Usage:
    python -m pipeline.phase_4.chain_event_sagas --dry-run
    python -m pipeline.phase_4.chain_event_sagas --centroid-id MIDEAST-IRAN
    python -m pipeline.phase_4.chain_event_sagas --track geo_domestic
    python -m pipeline.phase_4.chain_event_sagas --same-threshold 0.35 --cross-threshold 0.38
"""

import argparse
import math
import sys
import uuid
from collections import Counter
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config  # noqa: E402

SAME_TRACK_THRESHOLD = 0.35
CROSS_TRACK_THRESHOLD = 0.38

STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "and",
        "or",
        "with",
        "as",
        "by",
        "is",
        "are",
        "its",
        "but",
        "not",
        "over",
        "after",
        "from",
        "amid",
        "says",
        "said",
        "new",
        "has",
        "have",
        "will",
        "been",
        "be",
        "it",
        "that",
        "this",
        "was",
        "were",
        "they",
        "he",
        "she",
        "his",
        "her",
        "their",
        "than",
        "more",
        "up",
        "out",
        "about",
        "into",
        "could",
        "would",
        "also",
        "may",
        "can",
    }
)


def get_db_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def title_words(title):
    """Lowercase, remove stopwords and possessives."""
    if not title:
        return set()
    words = set()
    for w in title.lower().split():
        w = w.strip(".,;:!?\"'()[]")
        if w.endswith("'s"):
            w = w[:-2]
        if w and w not in STOPWORDS and len(w) > 1:
            words.add(w)
    return words


def dice(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    return 2 * len(set_a & set_b) / (len(set_a) + len(set_b))


def compute_score(ev_a, ev_b, tag_idf=None):
    """Return (score, tag_overlap) between two events."""
    tags_a = set(ev_a["tags"])
    tags_b = set(ev_b["tags"])
    shared = tags_a & tags_b
    tag_overlap = len(shared)

    if tag_idf and shared:
        weighted_shared = sum(tag_idf.get(t, 1.0) for t in shared)
        weighted_total = sum(tag_idf.get(t, 1.0) for t in tags_a) + sum(
            tag_idf.get(t, 1.0) for t in tags_b
        )
        tag_dice = 2 * weighted_shared / weighted_total if weighted_total else 0.0
    else:
        tag_dice = (
            2 * tag_overlap / (len(tags_a) + len(tags_b)) if (tags_a or tags_b) else 0.0
        )

    words_a = title_words(ev_a["title"])
    words_b = title_words(ev_b["title"])
    title_dice = dice(words_a, words_b)

    score = 0.5 * tag_dice + 0.5 * title_dice
    return score, tag_overlap


def build_tag_idf(all_events):
    """Compute IDF weights for tags within a centroid bucket.

    IDF = log(N / df) / log(N), normalized to 0..1 range.
    Tags appearing in every event get weight ~0, rare tags get weight ~1.
    """
    n = len(all_events)
    if n <= 1:
        return {}
    doc_freq = Counter()
    for ev in all_events:
        for tag in set(ev["tags"]):
            doc_freq[tag] += 1
    log_n = math.log(n)
    return {tag: math.log(n / df) / log_n for tag, df in doc_freq.items()}


# -- Data fetching -----------------------------------------------------------


def fetch_centroids(conn, centroid_id=None):
    """Fetch centroids that have 2+ tagged non-catchall events."""
    sql = """
        SELECT c.centroid_id, COUNT(*) as event_count
        FROM events_v3 e
        JOIN ctm c ON e.ctm_id = c.id
        WHERE e.tags IS NOT NULL AND array_length(e.tags, 1) > 0
          AND e.is_catchall = false
    """
    params = []
    if centroid_id:
        sql += " AND c.centroid_id = %s"
        params.append(centroid_id)
    sql += """
        GROUP BY c.centroid_id
        HAVING COUNT(*) >= 2
        ORDER BY c.centroid_id
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_centroid_events(conn, centroid_id, track=None):
    """Fetch all tagged events for a centroid, ordered by source count DESC."""
    sql = """
        SELECT e.id, e.title, e.tags, e.saga, e.source_batch_count,
               c.track, TO_CHAR(c.month, 'YYYY-MM') as month
        FROM events_v3 e
        JOIN ctm c ON e.ctm_id = c.id
        WHERE c.centroid_id = %s
          AND e.tags IS NOT NULL AND array_length(e.tags, 1) > 0
          AND e.is_catchall = false
    """
    params = [centroid_id]
    if track:
        sql += " AND c.track = %s"
        params.append(track)
    sql += " ORDER BY e.source_batch_count DESC"
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


# -- Core chaining -----------------------------------------------------------


def chain_centroid_events(
    events, tag_idf, same_threshold, cross_threshold, track_filter=None
):
    """Chain similar events within a centroid.

    Events must be sorted by source_batch_count DESC (largest = best anchor).
    Same-track pairs use same_threshold, cross-track pairs use cross_threshold.
    If track_filter is set, only same-track comparisons are made.
    """
    updates = []
    matches = []

    for i, ev in enumerate(events):
        best_score, best_overlap, best_match = 0, 0, None
        for j in range(i):
            anchor = events[j]
            same_track = anchor["track"] == ev["track"]
            if track_filter and not same_track:
                continue
            threshold = same_threshold if same_track else cross_threshold
            score, overlap = compute_score(anchor, ev, tag_idf)
            if overlap >= 2 and score >= threshold and score > best_score:
                best_score = score
                best_overlap = overlap
                best_match = anchor

        if best_match:
            matches.append(
                {
                    "centroid_id": ev.get("centroid_id", ""),
                    "ev_track": ev["track"],
                    "match_track": best_match["track"],
                    "ev_month": ev["month"],
                    "match_month": best_match["month"],
                    "ev_title": ev["title"],
                    "match_title": best_match["title"],
                    "score": best_score,
                    "tag_overlap": best_overlap,
                    "cross_track": best_match["track"] != ev["track"],
                }
            )

            # Saga assignment: prefer existing saga from anchor
            if best_match["saga"]:
                saga_id = best_match["saga"]
            elif ev["saga"]:
                saga_id = ev["saga"]
            else:
                saga_id = str(uuid.uuid4())
            if not best_match["saga"]:
                best_match["saga"] = saga_id
                updates.append((best_match["id"], saga_id))
            if not ev["saga"]:
                ev["saga"] = saga_id
                updates.append((ev["id"], saga_id))

    return updates, matches


# -- CLI ---------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Chain events into sagas (same-track + cross-track)"
    )
    parser.add_argument("--centroid-id", help="Filter to specific centroid")
    parser.add_argument(
        "--track", help="Filter to specific track (disables cross-track chaining)"
    )
    parser.add_argument(
        "--same-threshold",
        type=float,
        default=SAME_TRACK_THRESHOLD,
        help="Same-track threshold (default %.2f)" % SAME_TRACK_THRESHOLD,
    )
    parser.add_argument(
        "--cross-threshold",
        type=float,
        default=CROSS_TRACK_THRESHOLD,
        help="Cross-track threshold (default %.2f)" % CROSS_TRACK_THRESHOLD,
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print matches without writing"
    )
    args = parser.parse_args()

    conn = get_db_connection()
    centroids = fetch_centroids(conn, args.centroid_id)
    print("Centroids with 2+ tagged events: %d" % len(centroids))

    total_updates = []
    all_matches = []

    for cent in centroids:
        cid = cent["centroid_id"]
        events = fetch_centroid_events(conn, cid, args.track)
        if len(events) < 2:
            continue
        tag_idf = build_tag_idf(events)
        updates, matches = chain_centroid_events(
            events,
            tag_idf,
            args.same_threshold,
            args.cross_threshold,
            track_filter=args.track,
        )
        # Attach centroid_id for logging
        for m in matches:
            m["centroid_id"] = cid
        total_updates.extend(updates)
        all_matches.extend(matches)

    # Print matches sorted by score
    all_matches.sort(key=lambda m: m["score"], reverse=True)
    same_count = sum(1 for m in all_matches if not m["cross_track"])
    cross_count = sum(1 for m in all_matches if m["cross_track"])
    print(
        "\nMatches found: %d (same-track: %d, cross-track: %d)"
        % (len(all_matches), same_count, cross_count)
    )

    for m in all_matches[:50]:
        xtrack = " [CROSS-TRACK]" if m["cross_track"] else ""
        print(
            "  [%.2f] overlap=%d  %s / %s -> %s%s"
            % (
                m["score"],
                m["tag_overlap"],
                m["centroid_id"],
                m["ev_track"],
                m["match_track"],
                xtrack,
            )
        )
        print(
            "    %s (%s): %s" % (m["match_month"], m["match_track"], m["match_title"])
        )
        print("    %s (%s): %s" % (m["ev_month"], m["ev_track"], m["ev_title"]))

    if len(all_matches) > 50:
        print("  ... and %d more" % (len(all_matches) - 50))

    # Dedupe updates (same event might appear multiple times)
    seen = {}
    for event_id, saga_id in total_updates:
        seen[event_id] = saga_id
    deduped = list(seen.items())

    print("\nEvents to update: %d" % len(deduped))

    if args.dry_run:
        print("Dry run -- no changes written.")
        conn.close()
        return

    if not deduped:
        conn.close()
        return

    with conn.cursor() as cur:
        for event_id, saga_id in deduped:
            cur.execute(
                "UPDATE events_v3 SET saga = %s WHERE id = %s", [saga_id, event_id]
            )
    conn.commit()
    print("Updated %d events." % len(deduped))
    conn.close()


if __name__ == "__main__":
    main()

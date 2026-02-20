"""
Event Saga Chaining

Links events that are the same ongoing story across months using
tag overlap + title word Dice similarity.

Usage:
    python -m pipeline.phase_4.chain_event_sagas --dry-run
    python -m pipeline.phase_4.chain_event_sagas --centroid-id MIDEAST-IRAN --track geo_domestic
    python -m pipeline.phase_4.chain_event_sagas --threshold 0.35
"""

import argparse
import sys
import uuid
from collections import defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config  # noqa: E402

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


def compute_score(ev_a, ev_b):
    """Return (score, tag_overlap) between two events."""
    tags_a = set(ev_a["tags"])
    tags_b = set(ev_b["tags"])
    tag_overlap = len(tags_a & tags_b)
    tag_dice = (
        2 * tag_overlap / (len(tags_a) + len(tags_b)) if (tags_a or tags_b) else 0.0
    )

    words_a = title_words(ev_a["title"])
    words_b = title_words(ev_b["title"])
    title_dice = dice(words_a, words_b)

    score = 0.5 * tag_dice + 0.5 * title_dice
    return score, tag_overlap


def fetch_pairs(conn, centroid_id=None, track=None):
    """Fetch (centroid_id, track) pairs that have events in 2+ months."""
    sql = """
        SELECT c.centroid_id, c.track
        FROM events_v3 e
        JOIN ctm c ON e.ctm_id = c.id
        WHERE e.tags IS NOT NULL AND array_length(e.tags, 1) > 0
          AND e.is_catchall = false
    """
    params = []
    if centroid_id:
        sql += " AND c.centroid_id = %s"
        params.append(centroid_id)
    if track:
        sql += " AND c.track = %s"
        params.append(track)
    sql += """
        GROUP BY c.centroid_id, c.track
        HAVING COUNT(DISTINCT TO_CHAR(c.month, 'YYYY-MM')) >= 2
        ORDER BY c.centroid_id, c.track
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_events(conn, centroid_id, track):
    """Fetch events for a centroid+track, ordered by month then size."""
    sql = """
        SELECT e.id, e.title, e.tags, e.saga, TO_CHAR(c.month, 'YYYY-MM') as month
        FROM events_v3 e
        JOIN ctm c ON e.ctm_id = c.id
        WHERE c.centroid_id = %s AND c.track = %s
          AND e.tags IS NOT NULL AND array_length(e.tags, 1) > 0
          AND e.is_catchall = false
        ORDER BY c.month, e.source_batch_count DESC
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, [centroid_id, track])
        return cur.fetchall()


def chain_pair(earlier_events, later_events, threshold):
    """Match later-month events to best earlier-month candidate. Returns list of (event_id, saga_id) updates."""
    updates = []
    matches = []

    for later in later_events:
        best_score, best_overlap, best_earlier = 0, 0, None
        for earlier in earlier_events:
            score, overlap = compute_score(earlier, later)
            if overlap >= 2 and score >= threshold and score > best_score:
                best_score = score
                best_overlap = overlap
                best_earlier = earlier
        if best_earlier:
            matches.append((later, best_earlier, best_score, best_overlap))

    for later, earlier, score, overlap in matches:
        if earlier["saga"]:
            saga_id = earlier["saga"]
        elif later["saga"]:
            saga_id = later["saga"]
        else:
            saga_id = str(uuid.uuid4())
        if not earlier["saga"]:
            earlier["saga"] = saga_id
            updates.append((earlier["id"], saga_id))
        if not later["saga"]:
            later["saga"] = saga_id
            updates.append((later["id"], saga_id))

    return updates, matches


def main():
    parser = argparse.ArgumentParser(
        description="Chain events into sagas across months"
    )
    parser.add_argument("--centroid-id", help="Filter to specific centroid")
    parser.add_argument("--track", help="Filter to specific track")
    parser.add_argument(
        "--threshold", type=float, default=0.3, help="Minimum score (default 0.3)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print matches without writing"
    )
    args = parser.parse_args()

    conn = get_db_connection()
    pairs = fetch_pairs(conn, args.centroid_id, args.track)
    print("Pairs with events in 2+ months: %d" % len(pairs))

    total_updates = []
    all_matches = []

    for pair in pairs:
        events = fetch_events(conn, pair["centroid_id"], pair["track"])
        # Group by month
        by_month = defaultdict(list)
        for ev in events:
            by_month[ev["month"]].append(ev)

        months = sorted(by_month.keys())
        for i in range(1, len(months)):
            earlier = by_month[months[i - 1]]
            later = by_month[months[i]]
            updates, matches = chain_pair(earlier, later, args.threshold)
            total_updates.extend(updates)
            for later_ev, earlier_ev, score, overlap in matches:
                all_matches.append(
                    {
                        "centroid": pair["centroid_id"],
                        "track": pair["track"],
                        "earlier_month": months[i - 1],
                        "later_month": months[i],
                        "earlier_title": earlier_ev["title"],
                        "later_title": later_ev["title"],
                        "score": score,
                        "tag_overlap": overlap,
                    }
                )

    # Print matches sorted by score
    all_matches.sort(key=lambda m: m["score"], reverse=True)
    print("\nMatches found: %d" % len(all_matches))
    for m in all_matches[:50]:
        print(
            "  [%.2f] overlap=%d  %s / %s"
            % (m["score"], m["tag_overlap"], m["centroid"], m["track"])
        )
        print("    %s: %s" % (m["earlier_month"], m["earlier_title"]))
        print("    %s: %s" % (m["later_month"], m["later_title"]))

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

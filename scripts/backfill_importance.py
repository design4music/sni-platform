"""Backfill importance scores for existing title_labels and events_v3 rows."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config
from core.importance import score_event, score_title


def backfill_titles(conn):
    """Score all title_labels rows missing importance_score."""
    cur = conn.cursor()
    cur.execute(
        """SELECT tl.title_id, t.title_display, t.centroid_ids,
                  tl.action_class, tl.actor,
                  tl.persons, tl.orgs, tl.places, tl.commodities,
                  tl.policies, tl.systems, tl.named_events
           FROM title_labels tl
           JOIN titles_v3 t ON t.id = tl.title_id
           WHERE tl.importance_score IS NULL"""
    )
    rows = cur.fetchall()
    print("Titles to score: {}".format(len(rows)))

    batch = []
    for i, r in enumerate(rows):
        tid = str(r[0])
        signals = {
            "persons": r[5] or [],
            "orgs": r[6] or [],
            "places": r[7] or [],
            "commodities": r[8] or [],
            "policies": r[9] or [],
            "systems": r[10] or [],
            "named_events": r[11] or [],
        }
        score, components = score_title(r[1], r[2] or [], r[3], r[4], signals)
        batch.append((score, json.dumps(components), tid))

        if len(batch) >= 500:
            _flush_title_batch(cur, batch)
            conn.commit()
            print("  scored {} / {}".format(i + 1, len(rows)), flush=True)
            batch = []

    if batch:
        _flush_title_batch(cur, batch)
        conn.commit()

    print("Title scoring complete: {} rows".format(len(rows)))


def _flush_title_batch(cur, batch):
    for score, components, tid in batch:
        cur.execute(
            """UPDATE title_labels
               SET importance_score = %s, importance_components = %s
               WHERE title_id = %s""",
            (score, components, tid),
        )


def backfill_events(conn):
    """Score all events_v3 rows missing importance_score."""
    cur = conn.cursor()
    cur.execute(
        """SELECT id FROM events_v3
           WHERE importance_score IS NULL AND is_catchall = FALSE"""
    )
    event_ids = [str(r[0]) for r in cur.fetchall()]
    print("Events to score: {}".format(len(event_ids)))

    for i, eid in enumerate(event_ids):
        cur.execute(
            """SELECT tl.importance_score, t.publisher_name, t.detected_language,
                      t.pubdate_utc, ta.track
               FROM event_v3_titles evt
               JOIN titles_v3 t ON t.id = evt.title_id
               LEFT JOIN title_labels tl ON tl.title_id = t.id
               LEFT JOIN title_assignments ta ON ta.title_id = t.id
               WHERE evt.event_id = %s""",
            (eid,),
        )
        rows = [
            {
                "importance_score": r[0],
                "publisher_name": r[1],
                "detected_language": r[2],
                "pubdate_utc": r[3],
                "track": r[4],
            }
            for r in cur.fetchall()
        ]
        if not rows:
            continue

        score, components = score_event(rows)
        cur.execute(
            """UPDATE events_v3
               SET importance_score = %s, importance_components = %s
               WHERE id = %s""",
            (score, json.dumps(components), eid),
        )

        if (i + 1) % 200 == 0:
            conn.commit()
            print("  scored {} / {}".format(i + 1, len(event_ids)), flush=True)

    conn.commit()
    print("Event scoring complete: {} rows".format(len(event_ids)))


def main():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    backfill_titles(conn)
    backfill_events(conn)
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()

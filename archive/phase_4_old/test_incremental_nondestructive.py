"""
Test: Verify incremental clustering is non-destructive.

Snapshots events before and after process_ctm_for_daemon(), then asserts:
- Zero events destroyed (same IDs preserved)
- LLM fields (title, summary, tags) unchanged on preserved events
- Title link counts increase or stay same
- New events (if any) have title=NULL (queued for Phase 4.5a)

Usage:
    python pipeline/phase_4/test_incremental_nondestructive.py --ctm-id <id>
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from core.config import config
from pipeline.phase_4.incremental_clustering import (
    get_ctm_info,
    process_ctm_for_daemon,
)


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def snapshot_events(conn, ctm_id):
    """Snapshot all events for a CTM."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT e.id, e.title, e.summary, e.tags, e.source_batch_count,
               (SELECT COUNT(*) FROM event_v3_titles evt WHERE evt.event_id = e.id) as link_count
        FROM events_v3 e
        WHERE e.ctm_id = %s
        """,
        (ctm_id,),
    )
    events = {}
    for row in cur.fetchall():
        events[str(row[0])] = {
            "title": row[1],
            "summary": row[2],
            "tags": row[3],
            "source_batch_count": row[4],
            "link_count": row[5],
        }
    return events


def run_test(ctm_id):
    conn = get_connection()

    ctm_info = get_ctm_info(conn, ctm_id)
    if not ctm_info:
        print("CTM not found: {}".format(ctm_id))
        conn.close()
        return False

    centroid_id = ctm_info["centroid_id"]
    track = ctm_info["track"]
    print("Testing CTM: {} / {}".format(centroid_id, track))

    # Snapshot BEFORE
    before = snapshot_events(conn, ctm_id)
    print("Before: {} events".format(len(before)))

    # Run incremental clustering
    written = process_ctm_for_daemon(conn, ctm_id, centroid_id, track)
    print("process_ctm_for_daemon returned: {} new events".format(written))

    # Snapshot AFTER
    after = snapshot_events(conn, ctm_id)
    print("After: {} events".format(len(after)))

    # Analyze
    before_ids = set(before.keys())
    after_ids = set(after.keys())

    preserved = before_ids & after_ids
    destroyed = before_ids - after_ids
    created = after_ids - before_ids

    print("\n--- RESULTS ---")
    print("Events preserved: {}".format(len(preserved)))
    print("Events destroyed: {}".format(len(destroyed)))
    print("Events created:   {}".format(len(created)))

    # Check destruction
    ok = True
    if destroyed:
        print("\nFAIL: {} events were destroyed!".format(len(destroyed)))
        for eid in sorted(destroyed):
            ev = before[eid]
            print("  {} - {}".format(eid[:8], ev["title"] or "(no title)"))
        ok = False
    else:
        print("\nPASS: Zero events destroyed")

    # Check LLM fields unchanged on preserved events
    llm_changed = 0
    for eid in preserved:
        b = before[eid]
        a = after[eid]
        if (
            b["title"] != a["title"]
            or b["summary"] != a["summary"]
            or b["tags"] != a["tags"]
        ):
            llm_changed += 1
            if llm_changed <= 3:
                print(
                    "  LLM changed on {}: title={} -> {}".format(
                        eid[:8], repr(b["title"])[:40], repr(a["title"])[:40]
                    )
                )

    if llm_changed:
        print("FAIL: LLM fields changed on {} preserved events".format(llm_changed))
        ok = False
    else:
        print("PASS: LLM fields unchanged on all preserved events")

    # Check link counts
    link_decreased = 0
    link_increased = 0
    for eid in preserved:
        b_count = before[eid]["link_count"]
        a_count = after[eid]["link_count"]
        if a_count < b_count:
            link_decreased += 1
        elif a_count > b_count:
            link_increased += 1

    if link_decreased:
        print("FAIL: Title link count decreased on {} events".format(link_decreased))
        ok = False
    else:
        print(
            "PASS: Title link counts stable or increased ({} grew)".format(
                link_increased
            )
        )

    # Check new events have title=NULL
    new_with_title = 0
    for eid in created:
        if after[eid]["title"] is not None:
            new_with_title += 1

    if new_with_title:
        print(
            "WARN: {} new events already have title (expected NULL)".format(
                new_with_title
            )
        )
    elif created:
        print(
            "PASS: All {} new events have title=NULL (queued for 4.5a)".format(
                len(created)
            )
        )

    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    conn.close()
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test incremental clustering is non-destructive"
    )
    parser.add_argument("--ctm-id", required=True, help="CTM ID to test")
    args = parser.parse_args()

    success = run_test(args.ctm_id)
    sys.exit(0 if success else 1)

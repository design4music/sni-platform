"""
Upload a rebuilt centroid from local DB to remote.

Uploads: events_v3, event_v3_titles, updated title_labels (sector/subject), signal_aliases.

Usage:
    python -m pipeline.phase_4.upload_centroid --centroid EUROPE-FRANCE --month 2026-03-01
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")

import psycopg2

from core.config import config

REMOTE_DSN = (
    "postgresql://maxgenrih55:DGiBGNv89pGtRsaj5Ys2fCN4DFMEmCUb"
    "@dpg-d5uem563jp1c739ufrsg-a.frankfurt-postgres.render.com/sni_v2"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--centroid", required=True)
    parser.add_argument("--month", default="2026-03-01")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    lconn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    rconn = psycopg2.connect(REMOTE_DSN)
    lcur = lconn.cursor()
    rcur = rconn.cursor()

    # Get CTM IDs
    lcur.execute(
        "SELECT id, track FROM ctm WHERE centroid_id = %s AND month = %s",
        (args.centroid, args.month),
    )
    ctms = [(str(r[0]), r[1]) for r in lcur.fetchall()]
    print("CTMs: %d" % len(ctms))

    # Count local events
    all_ctm_ids = [c[0] for c in ctms]
    lcur.execute(
        "SELECT count(*), count(*) FILTER (WHERE NOT is_catchall) "
        "FROM events_v3 WHERE ctm_id = ANY(%s::uuid[])",
        (all_ctm_ids,),
    )
    total, emerged = lcur.fetchone()
    print("Local events: %d total, %d emerged" % (total, emerged))

    if args.dry_run:
        print("DRY RUN -- would upload %d events" % total)
        lconn.close()
        rconn.close()
        return

    t0 = time.time()

    # 1. Clean remote events for these CTMs
    print("Cleaning remote events...", flush=True)
    for ctm_id, track in ctms:
        rcur.execute(
            "DELETE FROM event_strategic_narratives WHERE event_id IN "
            "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
            (ctm_id,),
        )
        rcur.execute(
            "DELETE FROM event_v3_titles WHERE event_id IN "
            "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
            (ctm_id,),
        )
        rcur.execute(
            "UPDATE events_v3 SET merged_into = NULL WHERE merged_into IN "
            "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
            (ctm_id,),
        )
        rcur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    rconn.commit()

    # 2. Upload events
    print("Uploading events...", flush=True)
    lcur.execute(
        """SELECT id, ctm_id, source_batch_count, date, first_seen, last_active,
                  title, title_de, summary, summary_de, tags,
                  event_type, bucket_key, is_catchall,
                  importance_score, summary_source_count
           FROM events_v3 WHERE ctm_id = ANY(%s::uuid[])""",
        (all_ctm_ids,),
    )
    events = lcur.fetchall()
    for ev in events:
        rcur.execute(
            """INSERT INTO events_v3 (id, ctm_id, source_batch_count, date, first_seen,
                last_active, title, title_de, summary, summary_de, tags,
                event_type, bucket_key, is_catchall,
                importance_score, summary_source_count, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())""",
            ev,
        )
    rconn.commit()
    print("  %d events uploaded" % len(events))

    # 3. Upload event_v3_titles
    print("Uploading title links...", flush=True)
    lcur.execute(
        "SELECT event_id, title_id FROM event_v3_titles "
        "WHERE event_id IN (SELECT id FROM events_v3 WHERE ctm_id = ANY(%s::uuid[]))",
        (all_ctm_ids,),
    )
    links = lcur.fetchall()
    for link in links:
        rcur.execute(
            "INSERT INTO event_v3_titles (event_id, title_id) "
            "VALUES (%s, %s) ON CONFLICT DO NOTHING",
            link,
        )
    rconn.commit()
    print("  %d title links uploaded" % len(links))

    # 4. Upload updated title_labels (sector + subject)
    print("Uploading sector/subject labels...", flush=True)
    title_ids = list(set(link[1] for link in links))
    batch = 2000
    updated = 0
    for i in range(0, len(title_ids), batch):
        chunk = title_ids[i : i + batch]
        lcur.execute(
            "SELECT title_id, sector, subject FROM title_labels "
            "WHERE title_id = ANY(%s::uuid[]) AND sector IS NOT NULL",
            (chunk,),
        )
        for r in lcur.fetchall():
            rcur.execute(
                "UPDATE title_labels SET sector = %s, subject = %s WHERE title_id = %s",
                (r[1], r[2], r[0]),
            )
            updated += 1
        rconn.commit()
    print("  %d labels updated" % updated)

    lconn.close()
    rconn.close()
    print("\nDone in %.0fs." % (time.time() - t0))


if __name__ == "__main__":
    main()

"""Full-pipeline rerun for a single CTM under ELO v3.0.1.

Destructive: wipes title_labels, title_assignments, events_v3, event_families
for the CTM's titles, then re-runs Phase 3.1 -> 3.3 -> 4 -> 4.1a -> 4.1 -> 4.1b -> 4.5a.

Backups: title_labels rows are saved to a per-CTM backup table before deletion.

Usage:
  python out/beats_reextraction/rerun_ctm_full_pipeline.py EUROPE-BALTIC geo_security 2026-03
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg2

from core.config import get_config
from pipeline.phase_3_1.extract_labels import process_titles as phase31_extract
from pipeline.phase_3_3.assign_tracks_mechanical import SECTOR_TO_TRACK
from pipeline.phase_4.generate_daily_brief_4_5d import process_ctm as phase45d_brief
from pipeline.phase_4.incremental_clustering import recluster_ctm
from pipeline.phase_4.merge_same_day_events import process_ctm as phase40b_merge
from pipeline.phase_4.promote_and_describe_4_5a import process_ctm as phase45a_promote


def assign_tracks_for_title_ids(title_ids):
    """Targeted version of Phase 3.3 mechanical assignment.

    Only processes the given title_id list, regardless of the global queue.
    Mirrors pipeline.phase_3_3.assign_tracks_mechanical.process_batch logic.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t.id, t.centroid_ids, tl.sector, t.pubdate_utc
        FROM titles_v3 t
        JOIN title_labels tl ON tl.title_id = t.id
        WHERE t.id = ANY(%s::uuid[])
          AND t.centroid_ids IS NOT NULL
          AND tl.sector IS NOT NULL
        """,
        (title_ids,),
    )
    rows = cur.fetchall()
    assigned = rejected = 0
    for title_id, centroid_ids, sector, pubdate in rows:
        if sector == "NON_STRATEGIC":
            cur.execute(
                "UPDATE titles_v3 SET processing_status = 'blocked_llm' WHERE id = %s",
                (title_id,),
            )
            rejected += 1
            continue
        track = SECTOR_TO_TRACK.get(sector, "geo_politics")
        month = pubdate.strftime("%Y-%m-01") if pubdate else "2026-01-01"
        for centroid_id in centroid_ids or []:
            if centroid_id.startswith("SYS-"):
                continue
            cur.execute(
                "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s AND month = %s",
                (centroid_id, track, month),
            )
            ctm_row = cur.fetchone()
            if ctm_row:
                ctm_id_local = ctm_row[0]
            else:
                cur.execute(
                    "INSERT INTO ctm (centroid_id, track, month, title_count) "
                    "VALUES (%s, %s, %s, 0) RETURNING id",
                    (centroid_id, track, month),
                )
                ctm_id_local = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO title_assignments (title_id, centroid_id, track, ctm_id) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (title_id, centroid_id, track, ctm_id_local),
            )
            cur.execute(
                "UPDATE ctm SET title_count = title_count + 1 WHERE id = %s",
                (ctm_id_local,),
            )
        assigned += 1
    conn.commit()
    conn.close()
    print(
        f"  Phase 3.3 (targeted): {assigned} assigned, {rejected} rejected, {len(rows)} total"
    )


def get_conn():
    cfg = get_config()
    return psycopg2.connect(
        host=cfg.db_host,
        port=cfg.db_port,
        database=cfg.db_name,
        user=cfg.db_user,
        password=cfg.db_password,
    )


def header(label):
    print()
    print("=" * 70)
    print(label)
    print("=" * 70)


def main():
    if len(sys.argv) != 4:
        print("Usage: rerun_ctm_full_pipeline.py <centroid_id> <track> <YYYY-MM>")
        sys.exit(1)

    centroid_id, track, month = sys.argv[1], sys.argv[2], sys.argv[3]
    month_first = f"{month}-01"
    backup_table = (
        "beats_backup_"
        + centroid_id.lower().replace("-", "_")
        + "_"
        + track
        + "_"
        + month.replace("-", "_")
    )

    t0 = time.time()
    header(f"FULL PIPELINE RERUN: {centroid_id} / {track} / {month}")

    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()

    # 1. Find the CTM
    cur.execute(
        "SELECT id, title_count FROM ctm WHERE centroid_id=%s AND track=%s AND month=%s",
        (centroid_id, track, month_first),
    )
    row = cur.fetchone()
    if not row:
        print(f"No CTM found for {centroid_id}/{track}/{month}")
        return
    ctm_id, title_count_before = row
    print(f"CTM id: {ctm_id}")
    print(f"title_count (before): {title_count_before}")

    # 2. Identify the title set assigned to this CTM
    cur.execute(
        "SELECT title_id::text FROM title_assignments WHERE ctm_id = %s",
        (ctm_id,),
    )
    title_ids = [r[0] for r in cur.fetchall()]
    print(f"titles in CTM (from title_assignments): {len(title_ids)}")

    # Recovery path: if title_assignments was already deleted by a prior failed
    # run, source the title set from the backup table instead.
    if not title_ids:
        cur.execute(
            "SELECT to_regclass(%s)",
            (backup_table,),
        )
        if cur.fetchone()[0]:
            cur.execute(f"SELECT title_id::text FROM {backup_table}")
            title_ids = [r[0] for r in cur.fetchall()]
            print(f"  recovered {len(title_ids)} title_ids from backup table")

    if not title_ids:
        print("Nothing to do (no assignments and no backup).")
        return

    # 3. Backup title_labels (skip if already backed up - recovery scenario)
    header("STEP 1/9: Backup title_labels")
    cur.execute("SELECT to_regclass(%s)", (backup_table,))
    if cur.fetchone()[0]:
        cur.execute(f"SELECT COUNT(*) FROM {backup_table}")
        existing = cur.fetchone()[0]
        print(f"  Backup table already exists with {existing} rows - keeping it")
    else:
        cur.execute(
            f"CREATE TABLE {backup_table} AS SELECT * FROM title_labels WHERE title_id = ANY(%s::uuid[])",
            (title_ids,),
        )
        cur.execute(f"SELECT COUNT(*) FROM {backup_table}")
        print(f"  Backed up {cur.fetchone()[0]} rows to {backup_table}")
    conn.commit()

    # 4. Delete title_assignments + title_labels
    header("STEP 2/9: Delete title_labels + title_assignments")
    cur.execute(
        "DELETE FROM title_assignments WHERE title_id = ANY(%s::uuid[])",
        (title_ids,),
    )
    print(f"  Deleted {cur.rowcount} title_assignments")
    cur.execute(
        "DELETE FROM title_labels WHERE title_id = ANY(%s::uuid[])",
        (title_ids,),
    )
    print(f"  Deleted {cur.rowcount} title_labels")
    # Reset processing_status: any title that was 'blocked_llm' under v2 deserves
    # a fresh chance under v3.0.1 (the new prompt may classify it differently).
    cur.execute(
        "UPDATE titles_v3 SET processing_status = 'assigned' "
        "WHERE id = ANY(%s::uuid[]) AND processing_status = 'blocked_llm'",
        (title_ids,),
    )
    if cur.rowcount:
        print(f"  Reset {cur.rowcount} titles from blocked_llm -> assigned")
    conn.commit()

    # 5. Delete events for the CTM (we will recluster fresh)
    header("STEP 3/9: Delete events_v3 + event_families for CTM")
    cur.execute(
        "DELETE FROM event_v3_titles WHERE event_id IN (SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    print(f"  Deleted {cur.rowcount} event_v3_titles links")
    cur.execute(
        "DELETE FROM event_strategic_narratives WHERE event_id IN (SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    print(f"  Deleted {cur.rowcount} narrative matches")
    # Break FK: events_v3.family_id -> event_families.id
    cur.execute("UPDATE events_v3 SET family_id = NULL WHERE ctm_id = %s", (ctm_id,))
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    print(f"  Deleted {cur.rowcount} events_v3")
    cur.execute("DELETE FROM event_families WHERE ctm_id = %s", (ctm_id,))
    print(f"  Deleted {cur.rowcount} event_families")
    cur.execute(
        "UPDATE ctm SET title_count_at_clustering = NULL, last_aggregated_at = NULL, "
        "title_count_at_aggregation = NULL, last_summary_at = NULL, event_count_at_summary = NULL "
        "WHERE id = %s",
        (ctm_id,),
    )
    conn.commit()
    conn.close()

    # 6. Phase 3.1 — re-extract labels
    header(f"STEP 4/9: Phase 3.1 — re-extract labels for {len(title_ids)} titles")
    t = time.time()
    result = phase31_extract(
        max_titles=len(title_ids) + 100,
        batch_size=25,
        concurrency=8,
        title_ids_filter=title_ids,
    )
    print(f"  Result: {result}  ({time.time()-t:.0f}s)")

    # 7. Phase 3.3 — targeted mechanical track assignment for our title set only
    header("STEP 5/9: Phase 3.3 — targeted track assignment")
    t = time.time()
    assign_tracks_for_title_ids(title_ids)
    print(f"  ({time.time()-t:.0f}s)")

    # 7b. Refresh ctm.title_count to reflect new title_assignments
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE ctm SET title_count = (SELECT COUNT(*) FROM title_assignments WHERE ctm_id = %s) WHERE id = %s",
        (ctm_id, ctm_id),
    )
    cur.execute("SELECT title_count FROM ctm WHERE id = %s", (ctm_id,))
    new_count = cur.fetchone()[0]
    conn.commit()
    conn.close()
    print(f"  ctm.title_count after re-routing: {new_count} (was {title_count_before})")

    # 8. Phase 4 — recluster from scratch
    header("STEP 6/8: Phase 4 — recluster (D-056 day-beat)")
    t = time.time()
    recluster_ctm(ctm_id, dry_run=False)
    print(f"  ({time.time()-t:.0f}s)")

    # Phase 4.0b — same-day entity+Dice merge (mechanical, no LLM)
    header("STEP 7/10: Phase 4.0b — same-day merge")
    t = time.time()
    stats_merge = phase40b_merge(str(ctm_id))
    print(f"  {stats_merge}  ({time.time()-t:.0f}s)")

    # Phase 4.5a — promote top-N clusters/day + LLM title/description (EN+DE)
    import asyncio

    header("STEP 8/10: Phase 4.5a — promote + describe (EN+DE)")
    t = time.time()
    stats_45a = asyncio.run(phase45a_promote(str(ctm_id)))
    print(f"  {stats_45a}  ({time.time()-t:.0f}s)")

    # Phase 4.5-day — daily thematic brief (EN+DE) with 1-day cross-month lookback
    header("STEP 9/10: Phase 4.5-day — daily brief")
    t = time.time()
    stats_45d = asyncio.run(phase45d_brief(str(ctm_id)))
    print(f"  {stats_45d}  ({time.time()-t:.0f}s)")

    # 13. Final stats
    header("FINAL STATS")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT title_count FROM ctm WHERE id = %s", (ctm_id,))
    print(f"  ctm.title_count: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    print(f"  events_v3:       {cur.fetchone()[0]}")
    cur.execute(
        "SELECT COUNT(*) FROM events_v3 WHERE ctm_id = %s AND is_promoted = true",
        (ctm_id,),
    )
    print(f"  promoted:        {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM daily_briefs WHERE ctm_id = %s", (ctm_id,))
    print(f"  daily_briefs:    {cur.fetchone()[0]}")
    cur.execute(
        "SELECT COUNT(*) FROM title_labels WHERE title_id = ANY(%s::uuid[]) AND sector = 'NON_STRATEGIC'",
        (title_ids,),
    )
    print(f"  NON_STRATEGIC titles: {cur.fetchone()[0]}")
    cur.execute(
        "SELECT COUNT(*) FROM title_labels WHERE title_id = ANY(%s::uuid[]) AND industries IS NOT NULL AND array_length(industries,1) > 0",
        (title_ids,),
    )
    print(f"  titles with industries[]: {cur.fetchone()[0]}")
    conn.close()

    print()
    print(f"Total wall: {time.time()-t0:.0f}s")
    print(f"Backup table: {backup_table}")


if __name__ == "__main__":
    main()

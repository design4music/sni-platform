"""Step 1 of Feb full reprocess: finish v3.0.1 labeling for remaining titles.

State before: some Feb titles have v3.0.1 labels (from the aborted per-CTM
reprocess), some still only have v2 labels or duplicate rows.

This script:
  1. Finds Feb title_ids that lack any v3.0.1 label row.
  2. Deletes their existing title_labels rows (any version) so Phase 3.1
     inserts fresh without creating duplicates.
  3. Calls Phase 3.1 process_titles(title_ids_filter=...) in batches,
     using the same prompts/concurrency as the live daemon.

After this, every Feb title has exactly one v3.0.1 label row. Dedup of
remaining Feb title_labels (for titles that already had v3.0.1 via the
aborted run but may have duplicate rows) is handled by a separate
cleanup query at the end.

Usage:
    python scripts/finish_feb_labels.py
    python scripts/finish_feb_labels.py --batch 500 --limit 1000  # test
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2

from core.config import config
from pipeline.phase_3_1.extract_labels import process_titles

MONTH = "2026-02-01"
LOG_PATH_BASE = Path("out/2026_02_reprocess/label_finish.log")
LOG_PATH = LOG_PATH_BASE  # overridden per-shard in main()


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def log(msg):
    stamp = time.strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8", errors="replace") as f:
        f.write(line + "\n")


def find_titles_needing_v3(conn) -> list[str]:
    """Feb titles that don't have any ELO_v3.0.1 label row."""
    cur = conn.cursor()
    cur.execute(
        """SELECT DISTINCT t.id::text
             FROM titles_v3 t
             JOIN title_assignments ta ON ta.title_id = t.id
             JOIN ctm c ON c.id = ta.ctm_id
            WHERE c.month = %s
              AND NOT EXISTS (
                SELECT 1 FROM title_labels tl
                 WHERE tl.title_id = t.id AND tl.label_version = 'ELO_v3.0.1'
              )""",
        (MONTH,),
    )
    return [r[0] for r in cur.fetchall()]


def wipe_labels_for(conn, title_ids: list[str]):
    """Delete all title_labels rows for these titles so Phase 3.1 inserts fresh."""
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM title_labels WHERE title_id = ANY(%s::uuid[])",
        (title_ids,),
    )
    n = cur.rowcount
    conn.commit()
    return n


def dedup_labels(conn) -> int:
    """Collapse duplicate title_labels for Feb titles — keep one per title,
    preferring ELO_v3.0.1 over v2. Removes the duplicate rows the aborted
    run created."""
    cur = conn.cursor()
    cur.execute(
        """WITH feb_titles AS (
             SELECT DISTINCT t.id
               FROM titles_v3 t
               JOIN title_assignments ta ON ta.title_id = t.id
               JOIN ctm c ON c.id = ta.ctm_id
              WHERE c.month = %s
           ),
           ranked AS (
             SELECT tl.ctid,
                    ROW_NUMBER() OVER (
                      PARTITION BY tl.title_id
                      ORDER BY CASE WHEN tl.label_version='ELO_v3.0.1' THEN 0 ELSE 1 END,
                               tl.created_at DESC NULLS LAST
                    ) AS rnk
               FROM title_labels tl
               JOIN feb_titles ft ON ft.id = tl.title_id
           )
           DELETE FROM title_labels
            WHERE ctid IN (SELECT ctid FROM ranked WHERE rnk > 1)""",
        (MONTH,),
    )
    n = cur.rowcount
    conn.commit()
    return n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--batch", type=int, default=500, help="Titles per Phase 3.1 call"
    )
    parser.add_argument(
        "--concurrency", type=int, default=5, help="LLM concurrency per batch call"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Cap total titles (test mode)"
    )
    parser.add_argument(
        "--shard-idx",
        type=int,
        default=0,
        help="Shard index (0..N-1) for parallel runs. Each shard owns a disjoint title subset.",
    )
    parser.add_argument(
        "--shard-count",
        type=int,
        default=1,
        help="Total shard count. Default 1 = no sharding.",
    )
    args = parser.parse_args()

    # Per-shard log file so parallel processes don't clobber each other
    global LOG_PATH
    if args.shard_count > 1:
        LOG_PATH = LOG_PATH_BASE.with_name(
            f"{LOG_PATH_BASE.stem}.shard{args.shard_idx}of{args.shard_count}.log"
        )

    conn = get_conn()

    # Pre-dedup only on first shard (idempotent at SQL level but avoids
    # redundant work). Others can skip.
    if args.shard_idx == 0:
        log("Pre-dedup Feb title_labels...")
        dedup_count = dedup_labels(conn)
        log(f"  collapsed {dedup_count} duplicate rows")

    # Find titles still needing v3.0.1 (snapshot at shard start)
    ids = find_titles_needing_v3(conn)
    total = len(ids)

    # Apply sharding: each process takes every Nth id starting at shard_idx
    if args.shard_count > 1:
        ids = ids[args.shard_idx :: args.shard_count]
        log(
            f"Shard {args.shard_idx}/{args.shard_count}: "
            f"{len(ids)} titles (of {total} total needing v3.0.1)"
        )

    if args.limit:
        ids = ids[: args.limit]
    log(f"Titles needing v3.0.1 labels: {total} (processing {len(ids)})")

    if not ids:
        log("Nothing to do.")
        return

    # Wipe their existing labels so Phase 3.1 inserts fresh
    wiped = wipe_labels_for(conn, ids)
    log(f"Wiped {wiped} existing label rows for {len(ids)} titles")
    conn.close()

    # Run Phase 3.1 in chunks. process_titles handles internal batching +
    # concurrency within each call; we chunk so progress logs appear.
    t_start = time.time()
    processed = 0
    chunk_size = args.batch
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i : i + chunk_size]
        t = time.time()
        log(f"[{i}/{len(ids)}] Phase 3.1 chunk of {len(chunk)} titles...")
        try:
            result = process_titles(
                max_titles=len(chunk),
                batch_size=25,
                concurrency=args.concurrency,
                title_ids_filter=chunk,
            )
            processed += result.get("processed", len(chunk))
            elapsed = time.time() - t
            log(
                f"  done in {elapsed:.0f}s "
                f"(success={result.get('successful', '?')} failed={result.get('failed', '?')})"
            )
        except Exception as e:
            log(f"  chunk failed: {e}")

    # Final dedup pass only on shard 0 (the others may still be running;
    # dedup is idempotent and any shard can do it at the very end).
    if args.shard_idx == 0:
        conn = get_conn()
        log("Post-run dedup (shard 0 only)...")
        final_dedup = dedup_labels(conn)
        log(f"  collapsed {final_dedup} rows")

    total_elapsed = time.time() - t_start
    log(
        f"\nDone. Processed {processed}/{len(ids)} titles in {total_elapsed / 60:.1f} min"
    )


if __name__ == "__main__":
    main()

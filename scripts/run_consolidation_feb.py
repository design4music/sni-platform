"""Batch run Phase 4.1 consolidation across all Feb 2026 CTMs."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import psycopg2

from core.config import config
from pipeline.phase_4.consolidate_topics import process_ctm


def main():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, centroid_id, track, title_count
        FROM ctm
        WHERE TO_CHAR(month, 'YYYY-MM') = '2026-02' AND is_frozen = false
          AND title_count >= 3
          AND EXISTS (
              SELECT 1 FROM events_v3 e
              WHERE e.ctm_id = ctm.id AND e.topic_core IS NULL AND e.is_catchall = false
          )
        ORDER BY title_count DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    total = len(rows)
    print("=== Phase 4.1 Batch: {} CTMs ===".format(total), flush=True)
    start = time.time()

    for i, (ctm_id, centroid, track, tc) in enumerate(rows, 1):
        t0 = time.time()
        print(
            "\n[{}/{}] {} / {} ({} titles)".format(i, total, centroid, track, tc),
            flush=True,
        )
        try:
            process_ctm(ctm_id=ctm_id, dry_run=False)
        except Exception as e:
            print("  ERROR: {}".format(e), flush=True)
        elapsed = time.time() - t0
        print("  done in {:.1f}s".format(elapsed), flush=True)

    total_time = time.time() - start
    print(
        "\n=== BATCH COMPLETE: {} CTMs in {:.0f}s ({:.1f}m) ===".format(
            total, total_time, total_time / 60
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()

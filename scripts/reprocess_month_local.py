"""Full pipeline reprocess for a given month on the local DB.

For each CTM of the target month (smallest first), runs the complete rerun
pipeline: Phase 3.1 label re-extraction -> 3.3 track assignment -> 4
incremental clustering -> 4.0b same-day merge -> 4.5a promote+describe
(LLM prose EN+DE) -> 4.5d daily briefs. The rerun script is destructive
per-CTM: it wipes title_labels, title_assignments, events_v3 for the
CTM, backs up title_labels to a named backup table, then re-runs from
scratch.

Intended for past (frozen) months that need to be brought inline with
the current v3.0.1 + day-centric pipeline. Assumes titles_v3 + ctm rows
for the month already exist locally.

Usage:
    python scripts/reprocess_month_local.py --month 2026-02-01
    python scripts/reprocess_month_local.py --month 2026-02 --limit 3  # smoke test
    python scripts/reprocess_month_local.py --month 2026-02 --skip-nonempty

Safety:
    - Backups are auto-created per CTM (beats_backup_<centroid>_<track>_<month>).
    - Writes per-CTM progress to out/<month>_reprocess/run.log.
    - One CTM failure does not abort others.
    - Kill-safe: rerun on the same month reuses existing backups and resumes.
"""

import argparse
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2

from core.config import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--month", required=True, help="Month start, e.g. 2026-02-01 (or 2026-02)"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Cap CTMs processed (test mode)"
    )
    parser.add_argument(
        "--skip-nonempty",
        action="store_true",
        help="Skip CTMs that already have events (default: reprocess everything)",
    )
    args = parser.parse_args()

    month_start = args.month if len(args.month) > 7 else f"{args.month}-01"
    month_short = month_start[:7]

    log_dir = Path("out") / f"{month_short.replace('-', '_')}_reprocess"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "run.log"

    def log(msg):
        stamp = time.strftime("%H:%M:%S")
        line = f"[{stamp}] {msg}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()
    where_extra = (
        "AND NOT EXISTS (SELECT 1 FROM events_v3 e WHERE e.ctm_id = c.id)"
        if args.skip_nonempty
        else ""
    )
    cur.execute(
        f"""SELECT c.id, c.centroid_id, c.track, c.title_count
             FROM ctm c
             WHERE c.month=%s AND c.title_count > 1
               {where_extra}
             ORDER BY c.title_count ASC, c.centroid_id""",
        (month_start,),
    )
    ctms = cur.fetchall()
    conn.close()

    if args.limit:
        ctms = ctms[: args.limit]

    log(f"Reprocess {month_short}: {len(ctms)} CTMs (smallest first)")

    # Import the rerun driver here so reconnects happen inside each CTM call
    from out.beats_reextraction.rerun_ctm_full_pipeline import main as rerun_main

    done = 0
    failed = 0
    t_start = time.time()

    for idx, (ctm_id, centroid, track, tcount) in enumerate(ctms, 1):
        label = f"{centroid}/{track}"
        t = time.time()
        log(
            f"[{idx}/{len(ctms)}] START {label} "
            f"(ctm_id={str(ctm_id)[:8]}, titles={tcount})"
        )
        try:
            sys.argv = ["rerun", centroid, track, month_short]
            rerun_main()
            done += 1
            log(f"[{idx}/{len(ctms)}] DONE  {label} in {time.time() - t:.0f}s")
        except SystemExit:
            done += 1
        except Exception as e:
            failed += 1
            log(f"[{idx}/{len(ctms)}] FAIL  {label}: {e}")
            log(traceback.format_exc())

    total = time.time() - t_start
    log(f"\nAll done. {done} succeeded, {failed} failed in {total / 60:.1f} min")


if __name__ == "__main__":
    main()

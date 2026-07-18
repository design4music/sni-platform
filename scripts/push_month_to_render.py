"""Push a fully-reprocessed month from local DB to Render.

Thin CLI wrapper around the per-CTM push logic in
out/beats_reextraction/push_april_to_render.py. Reuses helper functions
(push_ctm, preflights, column lists, connections) for consistency with
the April push that already ran successfully.

Per-CTM transaction on Render:
  - DELETE Render's daily_briefs + event_v3_titles + event_strategic_narratives
    + events_v3 + title_labels + title_assignments
    that belong to this CTM's titles
  - INSERT the local versions in FK-correct order
FK order: title_labels, title_assignments, events_v3, event_v3_titles,
daily_briefs. titles_v3 + ctm rows already on Render (UUIDs shared).

Safety:
  - One transaction per CTM — failure localizes and rolls back.
  - Pre-flight verifies Render schema (events_v3.is_promoted, daily_briefs
    table).
  - Pre-flight verifies local has prose.
  - Processes smallest-first so a limit=N smoke test hits small CTMs.

Usage:
    python scripts/push_month_to_render.py --month 2026-02-01
    python scripts/push_month_to_render.py --month 2026-02-01 --limit 1
    python scripts/push_month_to_render.py --month 2026-02-01 --dry-run
"""

import argparse
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2
import psycopg2.extras

from out.beats_reextraction.push_april_to_render import (
    local_conn,
    preflight_local,
    preflight_render,
    push_ctm,
    render_conn,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--month", required=True, help="Month start, YYYY-MM or YYYY-MM-DD"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Push only N CTMs (test)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Inspect, no writes")
    args = parser.parse_args()

    month_start = args.month if len(args.month) > 7 else f"{args.month}-01"

    src = local_conn()
    src.set_session(readonly=True)
    src_cur = src.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    dst = render_conn() if not args.dry_run else None

    try:
        if dst:
            dst_cur = dst.cursor()
            print("[preflight] Verifying Render schema...")
            preflight_render(dst_cur)
            dst_cur.close()

        print(f"[preflight] Verifying local {month_start} has prose...")
        preflight_local(src_cur, month_start)

        # Enumerate CTMs in local order (smallest first for a forgiving start)
        src_cur.execute(
            """SELECT id::text, centroid_id, track, title_count
                 FROM ctm WHERE month=%s
                ORDER BY title_count ASC, centroid_id""",
            (month_start,),
        )
        ctms = src_cur.fetchall()
        if args.limit:
            ctms = ctms[: args.limit]

        print(f"[main] Pushing {len(ctms)} CTMs for {month_start} to Render...")
        t0 = time.time()
        ok = 0
        fail = 0
        totals = {"labels": 0, "assignments": 0, "events": 0, "links": 0, "briefs": 0}

        for idx, row in enumerate(ctms, 1):
            label = f"{row['centroid_id']}/{row['track']}"
            t = time.time()
            try:
                stats = push_ctm(src_cur, dst, row["id"], label, dry_run=args.dry_run)
                for k, v in stats.items():
                    totals[k] += v
                elapsed = time.time() - t
                print(
                    f"[{idx}/{len(ctms)}] OK    {label} "
                    f"(ev={stats['events']} lab={stats['labels']} br={stats['briefs']}) "
                    f"{elapsed:.1f}s",
                    flush=True,
                )
                ok += 1
            except Exception as e:
                fail += 1
                print(f"[{idx}/{len(ctms)}] FAIL  {label}: {e}", flush=True)
                traceback.print_exc()
                try:
                    src.rollback()
                except Exception:
                    pass
                if dst:
                    try:
                        dst.rollback()
                    except Exception:
                        pass

        total = time.time() - t0
        print()
        print(f"Done: {ok} ok, {fail} failed in {total / 60:.1f} min")
        print(f"Totals: {totals}")

    finally:
        src.close()
        if dst:
            dst.close()


if __name__ == "__main__":
    main()

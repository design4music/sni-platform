"""Full (non-incremental) re-attribution of every active friction node.

Why not refresh_all_active(incremental=False): that runs all ~157 FNs in ONE
transaction. Against Render that is a multi-hour transaction -- a single
dropped connection loses everything, and it holds locks throughout. This
driver does the same work per-FN with its own commit, so it is resumable and
each FN lands independently.

Atomics run before theaters: theater title attribution excludes titles already
claimed by an atomic (link_titles), so atomics must be current first.

Usage:
  python scripts/full_rebuild_fn_attribution.py                 # all active
  python scripts/full_rebuild_fn_attribution.py --only a,b,c    # subset
  python scripts/full_rebuild_fn_attribution.py --skip-done     # resume
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config  # noqa: E402
from scripts.bootstrap_friction_node import (  # noqa: E402
    FNConfigError,
    fetch_narratives,
    link_events,
    link_titles,
)

WINDOW_DAYS = 180


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--window-days", type=int, default=WINDOW_DAYS)
    p.add_argument("--only", default=None, help="comma-separated fn ids")
    p.add_argument(
        "--skip-done",
        action="store_true",
        help="skip FNs whose attribution was already rebuilt in this session "
        "(event_friction_nodes.created_at within the last 2 hours)",
    )
    return p.parse_args()


def main():
    args = parse_args()
    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    conn.autocommit = False

    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, name_en, fn_type, centroid_ids, primary_target
                 FROM friction_nodes
                WHERE is_active = true
                ORDER BY (fn_type = 'theater'), id"""
        )
        fns = [dict(r) for r in cur.fetchall()]
    conn.commit()

    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        fns = [f for f in fns if f["id"] in want]

    print("FNs to rebuild: %d (window=%dd)" % (len(fns), args.window_days), flush=True)
    t0 = time.time()
    done = skipped = failed = 0

    for i, fn in enumerate(fns, 1):
        fid = fn["id"]
        try:
            with conn.cursor() as cur:
                if args.skip_done:
                    cur.execute(
                        """SELECT max(created_at) > now() - interval '2 hours' AS fresh
                             FROM event_friction_nodes WHERE fn_id = %s""",
                        (fid,),
                    )
                    row = cur.fetchone()
                    if row and row["fresh"]:
                        print(
                            "[%d/%d] %-42s SKIP (fresh)" % (i, len(fns), fid),
                            flush=True,
                        )
                        skipped += 1
                        conn.commit()
                        continue

                narratives = fetch_narratives(cur, fid)
                n_ev = 0
                if fn.get("fn_type") != "theater":
                    n_ev = link_events(cur, fn, args.window_days)
                counts = link_titles(cur, fn, narratives, args.window_days)
            conn.commit()
            n_ti = sum(counts.values()) if counts else 0
            print(
                "[%d/%d] %-42s ev=%-6d ti=%-6d (%.0fs)"
                % (i, len(fns), fid, n_ev, n_ti, time.time() - t0),
                flush=True,
            )
            done += 1
        except FNConfigError as e:
            conn.rollback()
            print("[%d/%d] %-42s SKIP: %s" % (i, len(fns), fid, e), flush=True)
            skipped += 1
        except Exception as e:  # keep going; each FN is independent
            conn.rollback()
            print(
                "[%d/%d] %-42s FAIL: %s" % (i, len(fns), fid, repr(e)[:140]), flush=True
            )
            failed += 1

    conn.close()
    print(
        "\ndone=%d skipped=%d failed=%d in %.1f min"
        % (done, skipped, failed, (time.time() - t0) / 60),
        flush=True,
    )


if __name__ == "__main__":
    main()

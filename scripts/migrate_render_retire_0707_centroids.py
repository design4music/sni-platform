"""Retire the 53 over-granular 2026-07-07 centroids on RENDER (production).

Local was done by db/migrations/20260723_retire_0707_centroids.sql, but Render
diverges: the pipeline labeled real data on these centroids there. This script
does the FULL production migration, which local's did not need:

  1. Export a targeted rollback bundle (the 53 centroid rows, every affected
     titles_v3 / title_assignments / config row) to db/backups/ -- enough to
     reconstruct if anything is wrong.
  2. Remap titles_v3.centroid_ids (~15.6k rows): each dropped centroid -> its
     regional group, order-preserving, deduped. NON-STATE armed-group entries
     (no group) are dropped.
  3. Remap config: friction_nodes.centroid_ids, narratives_v2.actor_centroids
     (incl. the EUROPE-GREECE->EUROPE-SOUTH typo fix), strategic_assets.
  4. DEACTIVATE the 53 centroids (is_active = false). NOT a DELETE: deleting
     centroids_v3 cascades ctm -> events_v3 -> all event children (~2,617 events
     under these 89 ctm clusters, plus attribution) -- documented in
     DB_CASCADE_MAP.md as platform-destroying. Deactivation matches the
     established precedent (the ASIA-PACIFIC-* rows in this batch are already
     is_active=false). Derived ctm/centroid_summaries/title_assignments are left
     as harmless inactive-centroid debt; the pipeline moves to the group.
  5. Verify no ACTIVE reference remains, then COMMIT.

ALL of it runs in ONE transaction. Default is DRY-RUN: it performs every step,
prints the verification, then ROLLS BACK. Pass --execute to COMMIT.

Reads the Render DSN from env RENDER_DB (never hardcode / commit the secret).

Usage:
  RENDER_DB=postgresql://... python scripts/migrate_render_retire_0707_centroids.py
  RENDER_DB=postgresql://... python scripts/migrate_render_retire_0707_centroids.py --execute
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / "db" / "backups"

# ISO -> preferred group when the country sits in several (mirrors the local
# migration's choices so both DBs land identically).
PREF = {
    "DJ": "AFRICA-HORN",
    "ER": "AFRICA-HORN",
    "SO": "AFRICA-HORN",
    "GY": "AMERICAS-CARIBBEAN",
}
BATCH = 2000


def new_array(arr, remap, drop):
    """Order-preserving, deduped remap of one centroid array; drops None."""
    out = []
    for x in arr or []:
        t = remap.get(x, x) if x in drop else x
        if t and t not in out:
            out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--execute", action="store_true", help="COMMIT (default: dry-run + rollback)"
    )
    args = ap.parse_args()
    dsn = os.environ.get("RENDER_DB")
    if not dsn:
        sys.exit("set RENDER_DB env var to the Render DSN")

    conn = psycopg2.connect(dsn, cursor_factory=RealDictCursor, connect_timeout=30)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute(
        "SELECT id, iso_codes FROM centroids_v3 WHERE created_at::date = '2026-07-07'"
    )
    drop_rows = cur.fetchall()
    drop = {r["id"] for r in drop_rows}
    print("07-07 centroids to retire: %d" % len(drop))

    # remap: iso -> smallest non-dropped group centroid (single-country ones are
    # all in `drop`, so this resolves to the regional group); NON-STATE -> None
    cur.execute(
        "SELECT id, iso_codes FROM centroids_v3 WHERE cardinality(iso_codes) > 1 AND id <> ALL(%s)",
        (list(drop),),
    )
    groups = [(r["id"], set(r["iso_codes"])) for r in cur.fetchall()]
    remap = {}
    for r in drop_rows:
        iso = r["iso_codes"]
        if not iso:
            remap[r["id"]] = None
            continue
        iso = iso[0]
        if iso in PREF:
            remap[r["id"]] = PREF[iso]
            continue
        cands = sorted(
            [(g, s) for g, s in groups if iso in s], key=lambda h: (len(h[1]), h[0])
        )
        remap[r["id"]] = cands[0][0] if cands else None
    print(
        "remap targets built (%d -> group, %d dropped-to-none)"
        % (sum(1 for v in remap.values() if v), sum(1 for v in remap.values() if not v))
    )

    # ---- 1. targeted rollback export ----
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    bundle = {
        "centroids": [
            dict(r)
            for r in _q(
                cur, "SELECT * FROM centroids_v3 WHERE id = ANY(%s)", (list(drop),)
            )
        ]
    }
    for tbl, col, arr in [
        ("titles_v3", "centroid_ids", True),
        ("title_assignments", "centroid_id", False),
        ("friction_nodes", "centroid_ids", True),
        ("narratives_v2", "actor_centroids", True),
        ("strategic_assets", "centroid_ids", True),
    ]:
        op = "&&" if arr else "="
        rhs = "%s::text[]" if arr else "ANY(%s)"
        rows = _q(cur, f"SELECT * FROM {tbl} WHERE {col} {op} {rhs}", (list(drop),))
        bundle[tbl] = [_jsonable(dict(r)) for r in rows]
    bpath = BACKUP_DIR / f"render_0707_rollback_{ts}.json"
    bpath.write_text(json.dumps(bundle, indent=1, default=str), encoding="utf-8")
    print(
        "rollback bundle -> %s  (titles=%d, assignments=%d, fns=%d, assets=%d)"
        % (
            bpath,
            len(bundle["titles_v3"]),
            len(bundle["title_assignments"]),
            len(bundle["friction_nodes"]),
            len(bundle["strategic_assets"]),
        )
    )

    # ---- 2. remap titles_v3.centroid_ids (batched within the txn) ----
    cur.execute(
        "SELECT id, centroid_ids FROM titles_v3 WHERE centroid_ids && %s::text[]",
        (list(drop),),
    )
    tit = cur.fetchall()
    updates = [(new_array(r["centroid_ids"], remap, drop), r["id"]) for r in tit]
    for i in range(0, len(updates), BATCH):
        execute_values(
            cur,
            "UPDATE titles_v3 t SET centroid_ids = d.arr::text[] FROM (VALUES %s) AS d(arr, id) WHERE t.id = d.id::uuid",
            [(u[0], str(u[1])) for u in updates[i : i + BATCH]],
        )
    print("titles_v3.centroid_ids remapped: %d rows" % len(updates))

    # ---- 3. config remaps ----
    def remap_arr_table(tbl, col, extra=None):
        cur.execute(
            f"SELECT id, {col} FROM {tbl} WHERE {col} && %s::text[]", (list(drop),)
        )
        n = 0
        for r in cur.fetchall():
            arr = new_array(r[col], remap, drop)
            if extra:
                arr = [extra.get(x, x) for x in arr]
            cur.execute(f"UPDATE {tbl} SET {col} = %s WHERE id = %s", (arr, r["id"]))
            n += 1
        return n

    nf = remap_arr_table("friction_nodes", "centroid_ids")
    na = remap_arr_table("strategic_assets", "centroid_ids")
    # narratives: the 53 remap + the EUROPE-GREECE typo, in one pass
    cur.execute(
        "SELECT id, actor_centroids FROM narratives_v2 WHERE actor_centroids && %s::text[] OR 'EUROPE-GREECE' = ANY(actor_centroids)",
        (list(drop),),
    )
    nn = 0
    for r in cur.fetchall():
        arr = new_array(r["actor_centroids"], remap, drop)
        arr = ["EUROPE-SOUTH" if x == "EUROPE-GREECE" else x for x in arr]
        deduped = []
        for x in arr:
            if x not in deduped:
                deduped.append(x)
        cur.execute(
            "UPDATE narratives_v2 SET actor_centroids = %s WHERE id = %s",
            (deduped, r["id"]),
        )
        nn += 1
    print(
        "config remapped: friction_nodes=%d, strategic_assets=%d, narratives_v2=%d"
        % (nf, na, nn)
    )

    # ---- 4. deactivate the 53 (NOT delete -- see module docstring) ----
    cur.execute(
        "UPDATE centroids_v3 SET is_active = false, updated_at = now() WHERE id = ANY(%s)",
        (list(drop),),
    )
    print("centroids_v3 deactivated: %d" % cur.rowcount)

    # ---- 5. verify no ACTIVE reference remains ----
    # titles/config must no longer TAG the 53 (attribution correctness). Derived
    # ctm/summaries/title_assignments may still reference them -- that is the
    # intentional inactive debt, not a failure.
    problems = []
    for tbl, col in [
        ("titles_v3", "centroid_ids"),
        ("friction_nodes", "centroid_ids"),
        ("narratives_v2", "actor_centroids"),
        ("strategic_assets", "centroid_ids"),
    ]:
        cur.execute(
            f"SELECT count(*) n FROM {tbl}, unnest({col}) u WHERE u = ANY(%s)",
            (list(drop),),
        )
        n = cur.fetchone()["n"]
        if n:
            problems.append("%s.%s still tags %d" % (tbl, col, n))
    cur.execute(
        "SELECT count(*) n FROM centroids_v3 WHERE id = ANY(%s) AND is_active",
        (list(drop),),
    )
    if cur.fetchone()["n"]:
        problems.append("some of the 53 still active")
    if problems:
        print("\nVERIFY FAILED:")
        for p in problems:
            print("  " + p)
        conn.rollback()
        sys.exit("rolled back -- verification failed")
    print("\nverify OK: the 53 are inactive and no longer tag any title/config row")

    if args.execute:
        conn.commit()
        print("\n=== COMMITTED to Render ===")
    else:
        conn.rollback()
        print("\n=== DRY-RUN: rolled back. Re-run with --execute to commit. ===")
    conn.close()


def _q(cur, sql, params):
    cur.execute(sql, params)
    return cur.fetchall()


def _jsonable(d):
    return {
        k: (
            str(v)
            if not isinstance(v, (str, int, float, bool, list, dict, type(None)))
            else v
        )
        for k, v in d.items()
    }


if __name__ == "__main__":
    main()

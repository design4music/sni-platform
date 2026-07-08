"""Compute fn_asset_evidence: news-evidence links between theater FNs and
strategic assets (D-090 mechanism 2 made mechanical).

Rule: a (theater, asset) link exists when >= MIN_TITLES_90D headlines in
the last 90 days match one of the asset's aliases (ILIKE substring, same
semantics as fn_anchor) AND carry a centroid overlapping the theater's
centroid_ids. Links appear when coverage appears and decay as it ages out
-- no manual curation, and every link carries counts + sample titles as
citation.

The table is DERIVED and rebuilt wholesale each run inside one
transaction (the DELETE below is safe: nothing here is source data).

Run:  python scripts/compute_fn_asset_evidence.py          # rebuild
      python scripts/compute_fn_asset_evidence.py --qc     # alias QC report, no writes
"""

import argparse
import os
import time

import psycopg2
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WINDOW_DAYS = 90
MIN_TITLES_90D = 5
SAMPLE_N = 5
QC_TOP_N = 40
QC_MIN_ALIAS_LEN = 5

# Great-power centroids appear as ambient tags on coverage of every major
# crisis, so "title tagged AMERICAS-USA" says nothing about a US-identity
# theater. Theaters whose identity centroid is ambient fall back to
# BILATERAL matching (both of the first two centroids on the title) or,
# with no second centroid, attribution-only.
AMBIENT_CENTROIDS = ("AMERICAS-USA", "ASIA-CHINA", "EUROPE-RUSSIA")


def connect():
    load_dotenv(os.path.join(ROOT, ".env"))
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def load_aliases(cur):
    cur.execute(
        """
        SELECT id, jsonb_array_elements_text(meta->'aliases')
        FROM strategic_assets
        WHERE is_active AND jsonb_array_length(coalesce(meta->'aliases','[]'::jsonb)) > 0
        """
    )
    return cur.fetchall()  # [(asset_id, alias), ...]


def make_tmp_aliases(cur, pairs):
    # DROP IF EXISTS guards the daemon's long-lived pooled connection: a
    # prior aborted run could leave the temp table around and CREATE would
    # then fail with "already exists".
    cur.execute("DROP TABLE IF EXISTS tmp_asset_aliases")
    cur.execute("CREATE TEMP TABLE tmp_asset_aliases (asset_id text, alias text)")
    cur.executemany(
        "INSERT INTO tmp_asset_aliases VALUES (%s, %s)",
        pairs,
    )


def qc_report(cur, pairs):
    """Ungated per-alias hit counts so dangerous generics can be pruned
    via registry `aliases:` overrides before they pollute the links."""
    make_tmp_aliases(cur, pairs)
    cur.execute(
        f"""
        SELECT al.asset_id, al.alias, count(t.id) AS hits
        FROM tmp_asset_aliases al
        LEFT JOIN titles_v3 t
          ON t.pubdate_utc > now() - interval '{WINDOW_DAYS} days'
         AND t.title_display ILIKE '%%' || al.alias || '%%'
        GROUP BY al.asset_id, al.alias
        ORDER BY hits DESC
        """
    )
    rows = cur.fetchall()
    print(
        f"-- alias QC: {len(rows)} aliases, top {QC_TOP_N} by ungated {WINDOW_DAYS}d hits:"
    )
    for asset_id, alias, hits in rows[:QC_TOP_N]:
        print(f"   {hits:6d}  {alias:40s} ({asset_id})")
    short = [(a, al) for a, al, _ in rows if len(al) < QC_MIN_ALIAS_LEN]
    if short:
        print(
            f"-- FLAG: {len(short)} aliases shorter than {QC_MIN_ALIAS_LEN} chars (substring hazard):"
        )
        for asset_id, alias in short:
            print(f"   {alias!r} ({asset_id})")


def rebuild(cur, pairs):
    make_tmp_aliases(cur, pairs)
    t0 = time.time()
    # Stage 1: alias -> title hits, materialized once. This is the expensive
    # ILIKE scan; done standalone the planner handles it in minutes. Folding
    # the theater join into the same statement made the planner grind for
    # 20+ minutes on the same data (observed 2026-07-07).
    cur.execute("DROP TABLE IF EXISTS tmp_hits")
    cur.execute(
        f"""
        CREATE TEMP TABLE tmp_hits AS
        SELECT DISTINCT al.asset_id, t.id AS title_id, t.pubdate_utc, t.centroid_ids
        FROM tmp_asset_aliases al
        JOIN titles_v3 t
          ON t.pubdate_utc > now() - interval '{WINDOW_DAYS} days'
         AND t.title_display ILIKE '%%' || al.alias || '%%'
        """
    )
    cur.execute("ANALYZE tmp_hits")
    cur.execute("SELECT count(*) FROM tmp_hits")
    n_hits = cur.fetchone()[0]
    print(f"OK stage 1: {n_hits} alias-title hits in {time.time()-t0:.1f}s", flush=True)

    # Stage 2: link hits to theaters. Two gates, union'd:
    #  (a) attribution -- the title is in the theater's own attributed
    #      coverage (title_narratives via narratives_v2.fn_id, matching the
    #      theater itself or a member atomic). Highest precision; only
    #      exists where narrative machinery is live.
    #  (b) identity centroid -- the title carries the theater's identity
    #      centroid (primary_target, else centroid_ids[1]). Fallback for
    #      theaters without narratives. Deliberately NOT the full
    #      centroid_ids participant list: great-power participant tags
    #      (US/China/Russia) linked Hormuz to nearly every theater when
    #      the full list was used (observed on first rebuild).
    t1 = time.time()
    cur.execute("DELETE FROM fn_asset_evidence")
    cur.execute(
        f"""
        INSERT INTO fn_asset_evidence
          (fn_id, asset_id, n_titles_30d, n_titles_90d, last_seen, sample_title_ids)
        SELECT fn_id, asset_id,
               count(*) FILTER (WHERE pubdate_utc > now() - interval '30 days'),
               count(*),
               max(pubdate_utc)::date,
               (array_agg(title_id ORDER BY pubdate_utc DESC))[1:{SAMPLE_N}]
        FROM (
          SELECT fn.id AS fn_id, h.asset_id, h.title_id, h.pubdate_utc
          FROM tmp_hits h
          JOIN title_narratives tn ON tn.title_id = h.title_id
          JOIN narratives_v2 nv ON nv.id = tn.narrative_id
          JOIN friction_nodes fn
            ON fn.fn_type = 'theater' AND fn.is_active
           AND (nv.fn_id = fn.id OR nv.fn_id = ANY(fn.member_fn_ids))
          UNION
          SELECT fn.id, h.asset_id, h.title_id, h.pubdate_utc
          FROM tmp_hits h
          JOIN friction_nodes fn
            ON fn.fn_type = 'theater' AND fn.is_active
           AND CASE
                 WHEN COALESCE(fn.primary_target, fn.centroid_ids[1]) NOT IN {AMBIENT_CENTROIDS}
                   THEN COALESCE(fn.primary_target, fn.centroid_ids[1]) = ANY(h.centroid_ids)
                 WHEN array_length(fn.centroid_ids, 1) >= 2
                   THEN fn.centroid_ids[1] = ANY(h.centroid_ids)
                    AND fn.centroid_ids[2] = ANY(h.centroid_ids)
                 ELSE false
               END
        ) hits
        GROUP BY fn_id, asset_id
        HAVING count(*) >= {MIN_TITLES_90D}
        """
    )
    n = cur.rowcount
    print(f"OK stage 2: aggregated in {time.time()-t1:.1f}s", flush=True)
    print(f"OK fn_asset_evidence rebuilt: {n} links in {time.time()-t0:.1f}s")
    cur.execute(
        """
        SELECT e.fn_id, e.asset_id, e.n_titles_30d, e.n_titles_90d
        FROM fn_asset_evidence e ORDER BY e.n_titles_90d DESC LIMIT 12
        """
    )
    print("-- top links:")
    for fn_id, asset_id, n30, n90 in cur.fetchall():
        print(f"   {n90:5d} (30d: {n30:4d})  {fn_id:28s} -> {asset_id}")
    return n


def rebuild_evidence(conn):
    """Daemon entry point: rebuild fn_asset_evidence on an existing
    connection and commit. Returns the link count."""
    with conn.cursor() as cur:
        pairs = load_aliases(cur)
        n = rebuild(cur, pairs)
    conn.commit()
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qc", action="store_true", help="alias QC report only, no writes")
    args = ap.parse_args()

    conn = connect()
    cur = conn.cursor()
    pairs = load_aliases(cur)
    print(f"OK {len(pairs)} aliases across active assets")
    if args.qc:
        qc_report(cur, pairs)
        conn.rollback()
    else:
        rebuild(cur, pairs)
        conn.commit()
    conn.close()


if __name__ == "__main__":
    main()

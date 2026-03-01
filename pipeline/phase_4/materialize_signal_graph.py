"""Materialize signal co-occurrence graph into mv_signal_graph table.

Replaces the expensive 7-CTE self-join edges query in the frontend
with a simple PK lookup on pre-computed JSONB.

Part of the mv_* materialization pattern (see also: materialize_centroid_signals.py).
"""

import argparse
import json
import sys
import time
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

SIGNAL_COLUMNS = [
    "persons",
    "orgs",
    "places",
    "commodities",
    "policies",
    "systems",
    "named_events",
]
PER_TYPE = 5


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def _build_nodes_sql(date_clause, per_type):
    """Top N signals per type -- same as getTopSignalsAll."""
    parts = []
    for col in SIGNAL_COLUMNS:
        parts.append(
            "SELECT '%s' as signal_type, val as value, "
            "COUNT(DISTINCT evt.event_id)::int as event_count "
            "FROM events_v3 e "
            "JOIN event_v3_titles evt ON evt.event_id = e.id "
            "JOIN title_labels tl ON tl.title_id = evt.title_id "
            "CROSS JOIN LATERAL unnest(tl.%s) AS val "
            "WHERE %s AND e.is_catchall = false "
            "GROUP BY val ORDER BY event_count DESC LIMIT %d"
            % (col, col, date_clause, per_type)
        )
    return " UNION ALL ".join("(%s)" % p for p in parts)


def _build_edges_sql(date_clause, per_type):
    """Co-occurrence edges between top signals."""
    top_ctes = []
    for col in SIGNAL_COLUMNS:
        top_ctes.append(
            "top_%s AS ("
            "SELECT '%s'::text as signal_type, val as value "
            "FROM events_v3 e "
            "JOIN event_v3_titles evt ON evt.event_id = e.id "
            "JOIN title_labels tl ON tl.title_id = evt.title_id "
            "CROSS JOIN LATERAL unnest(tl.%s) AS val "
            "WHERE %s AND e.is_catchall = false "
            "GROUP BY val ORDER BY COUNT(DISTINCT evt.event_id) DESC LIMIT %d"
            ")" % (col, col, col, date_clause, per_type)
        )

    all_top_union = " UNION ALL ".join(
        "SELECT * FROM top_%s" % col for col in SIGNAL_COLUMNS
    )

    unnest_lateral = " UNION ALL ".join(
        "SELECT '%s'::text as sig_type, unnest(COALESCE(tl.%s, '{}')) as value"
        % (col, col)
        for col in SIGNAL_COLUMNS
    )

    return """
        WITH %s,
        all_top AS (%s),
        event_sigs AS (
            SELECT DISTINCT evt.event_id, expanded.sig_type as signal_type, expanded.value
            FROM event_v3_titles evt
            JOIN title_labels tl ON tl.title_id = evt.title_id
            JOIN events_v3 e ON e.id = evt.event_id
            CROSS JOIN LATERAL (%s) expanded(sig_type, value)
            WHERE %s AND e.is_catchall = false
              AND EXISTS (SELECT 1 FROM all_top WHERE all_top.signal_type = expanded.sig_type AND all_top.value = expanded.value)
        )
        SELECT a.value as source, b.value as target,
               a.signal_type as source_type, b.signal_type as target_type,
               COUNT(DISTINCT a.event_id)::int as weight
        FROM event_sigs a
        JOIN event_sigs b ON a.event_id = b.event_id
          AND (a.value, a.signal_type) < (b.value, b.signal_type)
        GROUP BY source, target, source_type, target_type
        HAVING COUNT(DISTINCT a.event_id) >= 3
        ORDER BY weight DESC
    """ % (
        ",\n".join(top_ctes),
        all_top_union,
        unnest_lateral,
        date_clause,
    )


def materialize(period=None):
    """Compute and upsert signal graph.

    Args:
        period: 'rolling' (default) or a month string like '2026-02'.
    """
    if period is None:
        period = "rolling"

    conn = get_connection()
    try:
        # Disable JIT for this heavy query
        with conn.cursor() as cur:
            cur.execute("SET jit = off")

        start = time.time()

        if period == "rolling":
            date_clause = "e.date >= CURRENT_DATE - INTERVAL '30 days'"
        else:
            date_clause = (
                "e.date >= '%s-01'::date AND e.date < ('%s-01'::date + INTERVAL '1 month')"
                % (period, period)
            )

        # Compute nodes
        with conn.cursor() as cur:
            cur.execute(_build_nodes_sql(date_clause, PER_TYPE))
            node_rows = cur.fetchall()

        nodes = [
            {"signal_type": r[0], "value": r[1], "event_count": r[2]} for r in node_rows
        ]

        # Compute edges
        with conn.cursor() as cur:
            cur.execute(_build_edges_sql(date_clause, PER_TYPE))
            edge_rows = cur.fetchall()

        edges = [
            {
                "source": r[0],
                "target": r[1],
                "source_type": r[2],
                "target_type": r[3],
                "weight": r[4],
            }
            for r in edge_rows
        ]

        # Upsert
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO mv_signal_graph (period, nodes, edges, updated_at)
                   VALUES (%s, %s, %s, NOW())
                   ON CONFLICT (period) DO UPDATE
                   SET nodes = EXCLUDED.nodes, edges = EXCLUDED.edges, updated_at = NOW()""",
                (period, json.dumps(nodes), json.dumps(edges)),
            )
        conn.commit()

        elapsed = time.time() - start
        print(
            "  %s: %d nodes, %d edges (%.1fs)"
            % (period, len(nodes), len(edges), elapsed)
        )
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Materialize signal co-occurrence graph"
    )
    parser.add_argument(
        "--period",
        default="rolling",
        help="'rolling' (default) or a month like '2026-02'",
    )
    args = parser.parse_args()
    materialize(period=args.period)


if __name__ == "__main__":
    main()

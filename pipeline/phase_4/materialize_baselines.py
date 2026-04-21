"""Materialize centroid baseline metrics + deviation detection into mv_centroid_baselines.

Per centroid per week (Monday-truncated):
- Computes current week metrics from mv_event_triples
- Computes rolling 12-week baseline (excluding current week)
- Flags deviations when |z| > 2

Depends on mv_event_triples being populated first.
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

MIN_BASELINE_WEEKS = 4  # Skip deviation flagging with fewer weeks


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


# Get weekly aggregates per centroid from mv_event_triples
WEEKLY_STATS_SQL = """
    SELECT
        centroid_id,
        DATE_TRUNC('week', first_seen)::date AS week,
        COUNT(DISTINCT event_id)::int AS event_count,
        AVG(importance_avg)::float AS mean_importance,
        SUM(CASE WHEN polarity = 'COOPERATIVE' THEN title_count ELSE 0 END)::int AS coop_titles,
        SUM(CASE WHEN polarity = 'CONFLICTUAL' THEN title_count ELSE 0 END)::int AS conf_titles,
        COUNT(DISTINCT actor)::int AS actor_diversity
    FROM mv_event_triples
    WHERE first_seen IS NOT NULL
    GROUP BY centroid_id, DATE_TRUNC('week', first_seen)
    ORDER BY centroid_id, week
"""

# Top actors per centroid per week
TOP_ACTORS_SQL = """
    SELECT
        centroid_id,
        DATE_TRUNC('week', first_seen)::date AS week,
        actor,
        SUM(title_count)::int AS total_titles
    FROM mv_event_triples
    WHERE first_seen IS NOT NULL
    GROUP BY centroid_id, DATE_TRUNC('week', first_seen), actor
    ORDER BY centroid_id, week, total_titles DESC
"""


def _zscore(val, mean, stddev):
    """Compute z-score, returns 0 if stddev is 0."""
    if stddev == 0 or stddev is None:
        return 0.0
    return (val - mean) / stddev


def _mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def _stddev(values):
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return variance**0.5


def materialize(all_weeks=False):
    """Compute baselines and deviations for all centroids."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            start = time.time()

            # Load weekly stats
            cur.execute(WEEKLY_STATS_SQL)
            weekly_rows = cur.fetchall()

            # Load top actors
            cur.execute(TOP_ACTORS_SQL)
            actor_rows = cur.fetchall()

            # Organize by centroid -> week
            centroid_weeks = defaultdict(dict)
            for cid, week, event_count, mean_imp, coop, conf, actor_div in weekly_rows:
                week_str = str(week)
                centroid_weeks[cid][week_str] = {
                    "event_count": event_count,
                    "mean_importance": mean_imp or 0.0,
                    "coop_titles": coop,
                    "conf_titles": conf,
                    "actor_diversity": actor_div,
                }

            # Top actors per centroid per week
            centroid_actors = defaultdict(lambda: defaultdict(list))
            for cid, week, actor, total in actor_rows:
                week_str = str(week)
                centroid_actors[cid][week_str].append((actor, total))

            # Compute baselines and deviations
            upsert_rows = []
            for cid, weeks_data in centroid_weeks.items():
                sorted_weeks = sorted(weeks_data.keys())
                actors_data = centroid_actors[cid]

                for i, week in enumerate(sorted_weeks):
                    current = weeks_data[week]

                    # Rolling 12-week baseline (excluding current)
                    baseline_weeks = sorted_weeks[max(0, i - 12) : i]
                    baseline_data = [weeks_data[w] for w in baseline_weeks]

                    # Current week metrics
                    coop = current["coop_titles"]
                    conf = current["conf_titles"]
                    polarity_ratio = coop / (coop + conf) if (coop + conf) > 0 else 0.5
                    top_5_actors = [a for a, _ in actors_data.get(week, [])[:5]]

                    metrics = {
                        "event_count": current["event_count"],
                        "mean_importance": round(current["mean_importance"], 4),
                        "polarity_ratio": round(polarity_ratio, 4),
                        "top_actors": top_5_actors,
                        "actor_diversity": current["actor_diversity"],
                    }

                    # Deviation detection
                    deviations = None
                    if len(baseline_data) >= MIN_BASELINE_WEEKS:
                        bl_events = [d["event_count"] for d in baseline_data]
                        bl_importance = [d["mean_importance"] for d in baseline_data]
                        bl_polarity = []
                        for d in baseline_data:
                            c_c = d["coop_titles"]
                            c_f = d["conf_titles"]
                            bl_polarity.append(
                                c_c / (c_c + c_f) if (c_c + c_f) > 0 else 0.5
                            )

                        # Collect baseline top-20 actors
                        bl_top20 = set()
                        for w in baseline_weeks:
                            for a, _ in actors_data.get(w, [])[:20]:
                                bl_top20.add(a)

                        flags = []
                        # Event count
                        z_events = _zscore(
                            current["event_count"], _mean(bl_events), _stddev(bl_events)
                        )
                        if z_events > 2:
                            flags.append(
                                {
                                    "type": "event_count_spike",
                                    "z": round(z_events, 2),
                                    "current": current["event_count"],
                                    "baseline_mean": round(_mean(bl_events), 1),
                                }
                            )
                        elif z_events < -2:
                            flags.append(
                                {
                                    "type": "event_count_drop",
                                    "z": round(z_events, 2),
                                    "current": current["event_count"],
                                    "baseline_mean": round(_mean(bl_events), 1),
                                }
                            )

                        # Importance surge
                        z_imp = _zscore(
                            current["mean_importance"],
                            _mean(bl_importance),
                            _stddev(bl_importance),
                        )
                        if abs(z_imp) > 2:
                            flags.append(
                                {
                                    "type": "importance_surge",
                                    "z": round(z_imp, 2),
                                    "current": round(current["mean_importance"], 4),
                                    "baseline_mean": round(_mean(bl_importance), 4),
                                }
                            )

                        # Polarity shift
                        z_pol = _zscore(
                            polarity_ratio, _mean(bl_polarity), _stddev(bl_polarity)
                        )
                        if abs(z_pol) > 2:
                            flags.append(
                                {
                                    "type": "polarity_shift",
                                    "z": round(z_pol, 2),
                                    "current": round(polarity_ratio, 4),
                                    "baseline_mean": round(_mean(bl_polarity), 4),
                                }
                            )

                        # New actor detection
                        for actor in top_5_actors:
                            if actor not in bl_top20:
                                flags.append({"type": "new_actor", "actor": actor})

                        if flags:
                            deviations = flags

                    upsert_rows.append(
                        (
                            cid,
                            week,
                            json.dumps(metrics),
                            json.dumps(deviations) if deviations else None,
                        )
                    )

            # Upsert — rows persist across runs; each run refreshes only
            # the weeks it recomputes. History survives even if upstream
            # mv_event_triples is pruned or retention-trimmed.
            if upsert_rows:
                for row in upsert_rows:
                    cur.execute(
                        """INSERT INTO mv_centroid_baselines (centroid_id, week, metrics, deviations, updated_at)
                           VALUES (%s, %s, %s::jsonb, %s::jsonb, NOW())
                           ON CONFLICT (centroid_id, week) DO UPDATE SET
                               metrics = EXCLUDED.metrics,
                               deviations = EXCLUDED.deviations,
                               updated_at = NOW()""",
                        row,
                    )

            conn.commit()
            elapsed = time.time() - start
            print(
                "Done: %d centroid-weeks computed (%.1fs)" % (len(upsert_rows), elapsed)
            )
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Materialize centroid baselines")
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_weeks",
        help="Recompute all weeks (default behavior)",
    )
    args = parser.parse_args()
    materialize(all_weeks=args.all_weeks)


if __name__ == "__main__":
    main()

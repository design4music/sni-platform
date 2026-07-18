"""
Exploration script for mechanical event clustering using Phase 3.5 labels.

Run: python pipeline/phase_4/explore_label_clustering.py

Experiments with different clustering strategies:
1. Perfect match (4/4): actor + action_class + domain + target
2. 3/4 match: actor + action_class + domain (ignore target variations)
3. 2/4 match: actor + action_class only
4. Combined: labels + matched_aliases intersection
5. Spike detection: daily anomaly detection vs baseline
"""

import os
from collections import defaultdict

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "sni"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def print_section(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def explore_perfect_match(cur, min_cluster_size=3):
    """Cluster by exact (actor, action_class, domain, target) match."""
    print_section("PERFECT MATCH CLUSTERS (4/4 params)")
    print("Minimum cluster size: %d" % min_cluster_size)
    print()

    cur.execute(
        """
        SELECT actor, action_class, domain, COALESCE(target, '-'), COUNT(*) as cnt
        FROM title_labels
        GROUP BY actor, action_class, domain, target
        HAVING COUNT(*) >= %s
        ORDER BY cnt DESC
        LIMIT 30
    """,
        (min_cluster_size,),
    )

    clusters = cur.fetchall()
    total_clustered = sum(r[4] for r in clusters)

    for row in clusters:
        print("  %3d | %s -> %s -> %s -> %s" % (row[4], row[0], row[1], row[2], row[3]))

    print()
    print("Clusters found: %d" % len(clusters))
    print("Total titles in clusters: %d" % total_clustered)
    return clusters


def explore_3_of_4_match(cur, min_cluster_size=5):
    """Cluster by (actor, action_class, domain), ignoring target variations."""
    print_section("3/4 MATCH CLUSTERS (ignore target)")
    print("Minimum cluster size: %d" % min_cluster_size)
    print()

    cur.execute(
        """
        SELECT actor, action_class, domain, COUNT(*) as cnt,
               COUNT(DISTINCT COALESCE(target, '-')) as unique_targets
        FROM title_labels
        GROUP BY actor, action_class, domain
        HAVING COUNT(*) >= %s
        ORDER BY cnt DESC
        LIMIT 30
    """,
        (min_cluster_size,),
    )

    clusters = cur.fetchall()
    total_clustered = sum(r[3] for r in clusters)

    for row in clusters:
        print(
            "  %3d titles, %2d targets | %s -> %s -> %s"
            % (row[3], row[4], row[0], row[1], row[2])
        )

    print()
    print("Clusters found: %d" % len(clusters))
    print("Total titles in clusters: %d" % total_clustered)
    return clusters


def explore_target_breakdown(cur, actor, action_class, domain):
    """Show target breakdown for a specific (actor, action_class, domain)."""
    print_section("TARGET BREAKDOWN: %s -> %s -> %s" % (actor, action_class, domain))

    cur.execute(
        """
        SELECT COALESCE(target, '-') as tgt, COUNT(*) as cnt
        FROM title_labels
        WHERE actor = %s AND action_class = %s AND domain = %s
        GROUP BY target
        ORDER BY cnt DESC
    """,
        (actor, action_class, domain),
    )

    for row in cur.fetchall():
        print("  %3d | %s" % (row[1], row[0]))


def explore_spike_detection(cur, baseline_days=7, spike_threshold=2.0):
    """Detect daily spikes vs baseline for each label pattern."""
    print_section("SPIKE DETECTION (threshold: %.1fx baseline)" % spike_threshold)
    print()

    # Calculate baseline (avg per day over last N days)
    cur.execute(
        """
        WITH daily_counts AS (
            SELECT
                DATE(t.pubdate_utc) as day,
                tl.actor, tl.action_class, tl.domain,
                COUNT(*) as cnt
            FROM title_labels tl
            JOIN titles_v3 t ON t.id = tl.title_id
            GROUP BY DATE(t.pubdate_utc), tl.actor, tl.action_class, tl.domain
        ),
        baselines AS (
            SELECT
                actor, action_class, domain,
                AVG(cnt) as avg_daily,
                STDDEV(cnt) as stddev_daily
            FROM daily_counts
            GROUP BY actor, action_class, domain
            HAVING COUNT(*) >= 3  -- need at least 3 days for baseline
        )
        SELECT
            dc.day, dc.actor, dc.action_class, dc.domain, dc.cnt,
            b.avg_daily,
            dc.cnt / NULLIF(b.avg_daily, 0) as spike_ratio
        FROM daily_counts dc
        JOIN baselines b ON dc.actor = b.actor
            AND dc.action_class = b.action_class
            AND dc.domain = b.domain
        WHERE dc.cnt / NULLIF(b.avg_daily, 0) >= %s
        ORDER BY dc.day DESC, spike_ratio DESC
    """,
        (spike_threshold,),
    )

    spikes = cur.fetchall()
    print("Date       | Count | Avg  | Ratio | Pattern")
    print("-" * 70)
    for row in spikes[:30]:
        print(
            "%s | %5d | %4.1f | %4.1fx | %s -> %s -> %s"
            % (row[0], row[4], row[5], row[6], row[1], row[2], row[3])
        )

    print()
    print("Total spikes detected: %d" % len(spikes))
    return spikes


def explore_label_plus_aliases(cur, min_cluster_size=3):
    """Cluster by combining labels with matched_aliases."""
    print_section("LABELS + MATCHED_ALIASES COMBINED")
    print("Minimum cluster size: %d" % min_cluster_size)
    print()

    # Get titles with both labels and aliases
    cur.execute(
        """
        SELECT
            tl.actor, tl.action_class, tl.domain, COALESCE(tl.target, '-'),
            t.matched_aliases,
            t.id, t.title_display
        FROM title_labels tl
        JOIN titles_v3 t ON t.id = tl.title_id
        WHERE t.matched_aliases IS NOT NULL AND t.matched_aliases != '[]'::jsonb
    """
    )

    # Build clusters: (label_key, frozenset(aliases)) -> titles
    clusters = defaultdict(list)
    for row in cur.fetchall():
        actor, action, domain, target, aliases, title_id, title = row
        label_key = (actor, action, domain, target)
        alias_set = frozenset(aliases) if aliases else frozenset()
        cluster_key = (label_key, alias_set)
        clusters[cluster_key].append((title_id, title))

    # Filter and sort by size
    valid_clusters = [(k, v) for k, v in clusters.items() if len(v) >= min_cluster_size]
    valid_clusters.sort(key=lambda x: -len(x[1]))

    total_titles = sum(len(v) for _, v in valid_clusters)

    print("Top clusters (label + aliases must match):")
    for (label_key, aliases), titles in valid_clusters[:20]:
        safe_aliases = sorted([a for a in aliases if str(a).isascii()])
        print(
            "  %3d | %s -> %s -> %s -> %s"
            % (len(titles), label_key[0], label_key[1], label_key[2], label_key[3])
        )
        print("       aliases: %s" % safe_aliases)

    print()
    print("Clusters found: %d" % len(valid_clusters))
    print("Total titles in clusters: %d" % total_titles)
    return valid_clusters


def explore_unknown_actors(cur):
    """Analyze UNKNOWN actor patterns for ontology improvement."""
    print_section("UNKNOWN ACTOR ANALYSIS (Ontology Improvement)")
    print()

    cur.execute(
        """
        SELECT
            t.matched_aliases, tl.action_class, tl.domain,
            COUNT(*) as cnt
        FROM title_labels tl
        JOIN titles_v3 t ON t.id = tl.title_id
        WHERE tl.actor = 'UNKNOWN'
        GROUP BY t.matched_aliases, tl.action_class, tl.domain
        ORDER BY cnt DESC
        LIMIT 20
    """
    )

    print("UNKNOWN titles by (aliases, action, domain):")
    for row in cur.fetchall():
        aliases = row[0] if row[0] else []
        safe_aliases = [a for a in aliases if str(a).isascii()] if aliases else []
        print("  %3d | aliases=%s | %s -> %s" % (row[3], safe_aliases, row[1], row[2]))

    print()
    print("Recommendation: Review these patterns for actor inference rules.")
    print("E.g., aliases=['trump'] + ECONOMIC_PRESSURE -> US_EXECUTIVE")


def experiment_threshold_sweep(cur):
    """Sweep different min_cluster_size thresholds."""
    print_section("THRESHOLD SWEEP: Min Cluster Size Impact")
    print()

    print("4/4 match (perfect):")
    print("  Min | Clusters | Titles | Coverage")
    for min_size in [2, 3, 5, 8, 10, 15, 20]:
        cur.execute(
            """
            SELECT COUNT(*) as cluster_count, SUM(cnt) as total_titles
            FROM (
                SELECT COUNT(*) as cnt
                FROM title_labels
                GROUP BY actor, action_class, domain, target
                HAVING COUNT(*) >= %s
            ) sub
        """,
            (min_size,),
        )
        row = cur.fetchone()
        cluster_count = row[0] or 0
        total_titles = row[1] or 0
        coverage = 100 * total_titles / 2228 if total_titles else 0
        print(
            "  %3d | %8d | %6d | %5.1f%%"
            % (min_size, cluster_count, total_titles, coverage)
        )

    print()
    print("3/4 match (ignore target):")
    print("  Min | Clusters | Titles | Coverage")
    for min_size in [2, 3, 5, 8, 10, 15, 20]:
        cur.execute(
            """
            SELECT COUNT(*) as cluster_count, SUM(cnt) as total_titles
            FROM (
                SELECT COUNT(*) as cnt
                FROM title_labels
                GROUP BY actor, action_class, domain
                HAVING COUNT(*) >= %s
            ) sub
        """,
            (min_size,),
        )
        row = cur.fetchone()
        cluster_count = row[0] or 0
        total_titles = row[1] or 0
        coverage = 100 * total_titles / 2228 if total_titles else 0
        print(
            "  %3d | %8d | %6d | %5.1f%%"
            % (min_size, cluster_count, total_titles, coverage)
        )


def main():
    conn = get_connection()
    cur = conn.cursor()

    # Get total count
    cur.execute("SELECT COUNT(*) FROM title_labels")
    total = cur.fetchone()[0]
    print("Total labeled titles: %d" % total)

    # Run explorations
    explore_perfect_match(cur, min_cluster_size=5)
    explore_3_of_4_match(cur, min_cluster_size=5)
    explore_target_breakdown(cur, "US_EXECUTIVE", "ECONOMIC_PRESSURE", "FOREIGN_POLICY")
    explore_spike_detection(cur, spike_threshold=1.5)
    explore_label_plus_aliases(cur, min_cluster_size=3)
    explore_unknown_actors(cur)
    experiment_threshold_sweep(cur)

    conn.close()


if __name__ == "__main__":
    main()

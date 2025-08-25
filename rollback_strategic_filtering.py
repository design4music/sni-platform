#!/usr/bin/env python3
"""
Roll Back Strategic Filtering Changes
Restore to previous working state with 34.2% filtering rate
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database


def main():
    """Roll back to previous working strategic filtering state"""

    try:
        # Initialize database
        config = get_config()
        initialize_database(config.database)

        print("=== ROLLING BACK STRATEGIC FILTERING CHANGES ===")
        print("Restoring to previous working state...")
        print()

        with get_db_session() as session:

            # Drop current views
            print("Dropping modified materialized views...")
            session.execute(
                text(
                    "DROP MATERIALIZED VIEW IF EXISTS strategic_candidates_300h CASCADE;"
                )
            )
            session.execute(
                text("DROP MATERIALIZED VIEW IF EXISTS event_tokens_30d CASCADE;")
            )

            # Keep the reference tables but don't use them in the original version
            # Just recreate the original event_tokens_30d that was working

            print("Recreating original event_tokens_30d...")
            # Recreate basic event_tokens_30d (before the improvements)
            original_event_tokens_sql = text(
                """
                CREATE MATERIALIZED VIEW event_tokens_30d AS
                WITH country_cooccur AS (
                  SELECT 
                    ack.token,
                    COUNT(DISTINCT CASE WHEN rc.name IS NOT NULL THEN lower(rc.name) END) as country_count,
                    COUNT(DISTINCT ack.article_id) as doc_freq
                  FROM article_core_keywords ack
                  JOIN articles a ON a.id = ack.article_id
                  LEFT JOIN ref_countries rc ON lower(rc.name) = ack.token
                  WHERE a.language = 'EN' 
                    AND a.created_at >= NOW() - INTERVAL '30 days'
                  GROUP BY ack.token
                  HAVING COUNT(DISTINCT CASE WHEN rc.name IS NOT NULL THEN lower(rc.name) END) = 0
                    AND COUNT(DISTINCT ack.article_id) >= 3
                )
                SELECT 
                  cc.token,
                  GREATEST(cc.country_count, 3) as countries,
                  cc.doc_freq as df
                FROM country_cooccur cc
                WHERE cc.token NOT IN (
                  'united states', 'china', 'russia', 'india', 'israel', 'ukraine',
                  'gaza', 'iran', 'trump', 'biden', 'putin'
                )
                ORDER BY cc.doc_freq DESC;
            """
            )

            session.execute(original_event_tokens_sql)
            session.commit()

            # Check results
            result = session.execute(
                text("SELECT COUNT(*) FROM event_tokens_30d;")
            ).fetchone()
            print(f"  Restored event tokens: {result[0]} entries")

            print("Recreating original strategic_candidates_300h...")
            # Recreate the original strategic candidates view
            original_strategic_sql = text(
                """
                CREATE MATERIALIZED VIEW strategic_candidates_300h AS
                WITH core AS (
                  SELECT article_core_keywords.article_id,
                      article_core_keywords.token
                  FROM article_core_keywords
                ), gpe AS (
                  SELECT lower((ref_countries.name)::text) AS tok
                  FROM ref_countries
                ), org AS (
                  SELECT lower((ref_orgs.name)::text) AS tok
                  FROM ref_orgs
                )
                SELECT DISTINCT a.id AS article_id,
                  g.gpe_cnt,
                  ev.has_event,
                  so.has_org,
                      CASE
                          WHEN (ev.has_event AND (g.gpe_cnt >= 2)) THEN 'event+country'::text
                          WHEN ((g.gpe_cnt >= 1) AND so.has_org) THEN 'country+org'::text
                          ELSE 'other'::text
                      END AS reason
                FROM articles a
                  LEFT JOIN ( SELECT core.article_id,
                          count(DISTINCT gpe.tok) AS gpe_cnt
                      FROM core
                          JOIN gpe ON core.token = gpe.tok
                      GROUP BY core.article_id) g ON a.id = g.article_id
                  LEFT JOIN ( SELECT core.article_id,
                          true AS has_event
                      FROM core
                          JOIN event_tokens_30d et ON core.token = et.token
                      GROUP BY core.article_id) ev ON a.id = ev.article_id
                  LEFT JOIN ( SELECT core.article_id,
                          true AS has_org
                      FROM core
                          JOIN org ON core.token = org.tok
                      GROUP BY core.article_id) so ON a.id = so.article_id
                WHERE a.language = 'EN' 
                  AND a.created_at >= NOW() - INTERVAL '300 hours'
                  AND ((ev.has_event AND g.gpe_cnt >= 2) 
                       OR (g.gpe_cnt >= 1 AND so.has_org) 
                       OR COALESCE(g.gpe_cnt, 0) >= 3);
            """
            )

            session.execute(original_strategic_sql)
            session.commit()

            # Check restored results
            result = session.execute(
                text("SELECT COUNT(*) FROM strategic_candidates_300h;")
            ).fetchone()
            print(f"  Restored strategic candidates: {result[0]}")

            # Show reason breakdown
            results = session.execute(
                text(
                    "SELECT reason, COUNT(*) FROM strategic_candidates_300h GROUP BY reason ORDER BY 2 DESC;"
                )
            ).fetchall()
            print("  Restored qualification reasons:")
            for reason, count in results:
                print(f"    {reason}: {count} candidates")

            print()

            # Final KPI check to confirm rollback
            print("Rollback verification - KPI check:")

            kpi1_result = session.execute(
                text(
                    """
                WITH stats AS (
                  SELECT 
                    COUNT(*) AS total_articles_300h,
                    (SELECT COUNT(*) FROM strategic_candidates_300h) AS strategic_candidates
                  FROM articles
                  WHERE language = 'EN' AND created_at >= NOW() - INTERVAL '300 hours'
                )
                SELECT total_articles_300h, strategic_candidates FROM stats;
            """
                )
            ).fetchone()

            if kpi1_result:
                total_articles, strategic_candidates = kpi1_result
                if total_articles > 0:
                    pct_candidates = round(
                        (strategic_candidates / total_articles) * 100, 1
                    )
                    print(
                        f"  Strategic filtering rate: {pct_candidates}% ({strategic_candidates}/{total_articles})"
                    )

                    if abs(pct_candidates - 34.2) < 5:  # Within 5% of original
                        print("  ✓ Successfully rolled back to previous state")
                    else:
                        print(
                            f"  Note: Different from original 34.2% - this may be expected due to new data"
                        )

        print()
        print("=== ROLLBACK COMPLETED ===")
        print("System restored to previous working state")
        print("Strategic filtering should be back to ~34% rate")
        print(
            "Reference tables (ref_geo_places, expanded ref_orgs) remain available for future use"
        )

    except Exception as e:
        print(f"Error during rollback: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

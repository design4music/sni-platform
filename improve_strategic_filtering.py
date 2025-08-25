#!/usr/bin/env python3
"""
Improve Strategic Filtering (CLUST-0)
Tighten event token learning and expand supranational orgs
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database


def main():
    """Improve strategic filtering by tightening event token learning"""

    try:
        # Initialize database
        config = get_config()
        initialize_database(config.database)

        print("=== IMPROVING STRATEGIC FILTERING (CLUST-0) ===")
        print()

        with get_db_session() as session:

            # Step 1: Create ref_geo_places table with geo-hotspots
            print("Step 1: Creating geo-hotspots reference table...")

            geo_places_sql = text(
                """
                CREATE TABLE IF NOT EXISTS ref_geo_places(tok text PRIMARY KEY);
                INSERT INTO ref_geo_places(tok) VALUES
                  ('gaza'),('west bank'),('hong kong'),('taiwan'),('kashmir'),
                  ('donbas'),('crimea') ON CONFLICT DO NOTHING;
            """
            )

            session.execute(geo_places_sql)
            session.commit()

            # Check what was inserted
            result = session.execute(
                text("SELECT COUNT(*) FROM ref_geo_places;")
            ).fetchone()
            print(f"  Geo-hotspots created: {result[0]} entries")

            # Step 2: Expand supranational organizations
            print("Step 2: Expanding supranational organizations...")

            orgs_sql = text(
                """
                CREATE TABLE IF NOT EXISTS ref_orgs(name text PRIMARY KEY);
                INSERT INTO ref_orgs(name) VALUES
                  ('nato'),('european union'),('united nations'),('imf'),('world bank'),
                  ('wto'),('opec'),('brics'),('g7'),('g20'),
                  ('asean'),('african union'),('sco'),('csto'),('gcc'),
                  ('eaeu'),('who'),('icc'),('icj'),('iaea')
                ON CONFLICT DO NOTHING;
            """
            )

            session.execute(orgs_sql)
            session.commit()

            # Check what was inserted
            result = session.execute(text("SELECT COUNT(*) FROM ref_orgs;")).fetchone()
            print(f"  Organizations created: {result[0]} entries")

            # List the orgs for verification
            results = session.execute(
                text("SELECT name FROM ref_orgs ORDER BY name;")
            ).fetchall()
            print("  Organizations: " + ", ".join([row[0] for row in results]))
            print()

            # Step 3: Check if keyword_hubs_30d exists
            print("Step 3: Checking prerequisites...")

            try:
                result = session.execute(
                    text("SELECT COUNT(*) FROM keyword_hubs_30d;")
                ).fetchone()
                print(f"  keyword_hubs_30d exists with {result[0]} entries")
            except Exception as e:
                print(f"  WARNING: keyword_hubs_30d may not exist: {e}")
                # Create a dummy version for now
                print("  Creating minimal keyword_hubs_30d...")
                session.execute(
                    text(
                        """
                    CREATE MATERIALIZED VIEW IF NOT EXISTS keyword_hubs_30d AS
                    SELECT 'placeholder' as tok WHERE false;
                """
                    )
                )
                session.commit()

            # Step 4: Rebuild improved event_tokens_30d
            print("Step 4: Rebuilding event token learner with strategic filtering...")

            # Drop dependent views first
            session.execute(
                text(
                    "DROP MATERIALIZED VIEW IF EXISTS strategic_candidates_300h CASCADE;"
                )
            )
            session.execute(
                text("DROP MATERIALIZED VIEW IF EXISTS event_tokens_30d CASCADE;")
            )

            # Create improved event token learner
            improved_event_tokens_sql = text(
                """
                CREATE MATERIALIZED VIEW event_tokens_30d AS
                WITH ak AS (
                  SELECT ack.article_id, ack.token as tok
                  FROM article_core_keywords ack
                  JOIN articles a ON a.id = ack.article_id
                  WHERE a.language = 'EN' AND a.created_at >= now() - interval '30 days'
                ),
                pairs AS (
                  SELECT LEAST(a1.tok,a2.tok) t1, GREATEST(a1.tok,a2.tok) t2,
                         COUNT(DISTINCT a1.article_id) co_doc
                  FROM ak a1 JOIN ak a2 ON a1.article_id=a2.article_id AND a1.tok<a2.tok
                  GROUP BY 1,2
                ),
                df AS (SELECT tok, COUNT(DISTINCT article_id) df FROM ak GROUP BY tok),
                countries AS (SELECT lower(name) tok FROM ref_countries),
                orgs     AS (SELECT lower(name) tok FROM ref_orgs),
                hubs     AS (SELECT tok FROM keyword_hubs_30d),
                -- keep tokens that co-occur with >=3 distinct countries
                hits AS (
                  SELECT CASE WHEN p.t1 IN (SELECT tok FROM countries) THEN p.t2 ELSE p.t1 END AS token,
                         CASE WHEN p.t1 IN (SELECT tok FROM countries) THEN p.t1 ELSE p.t2 END AS country_tok
                  FROM pairs p
                  WHERE p.t1 IN (SELECT tok FROM countries) OR p.t2 IN (SELECT tok FROM countries)
                ),
                cand AS (
                  SELECT token, COUNT(DISTINCT country_tok) countries
                  FROM hits GROUP BY token HAVING COUNT(DISTINCT country_tok) >= 3
                ),
                -- final filter: drop countries, orgs, hubs, and geo hotspots  
                filtered AS (
                  SELECT c.token, c.countries, d.df
                  FROM cand c
                  LEFT JOIN df d ON d.tok = c.token
                  WHERE c.token NOT IN (SELECT tok FROM countries)
                    AND c.token NOT IN (SELECT tok FROM orgs)
                    AND c.token NOT IN (SELECT tok FROM hubs)
                    AND c.token NOT IN (SELECT tok FROM ref_geo_places)
                )
                SELECT token, countries, df
                FROM filtered;
            """
            )

            session.execute(improved_event_tokens_sql)
            session.commit()

            # Check results
            result = session.execute(
                text("SELECT COUNT(*) FROM event_tokens_30d;")
            ).fetchone()
            print(f"  Improved event tokens: {result[0]} strategic events identified")

            # Show top event tokens
            results = session.execute(
                text(
                    "SELECT token, countries, df FROM event_tokens_30d ORDER BY countries DESC, df DESC LIMIT 10;"
                )
            ).fetchall()
            print("  Top strategic event tokens:")
            for token, countries, df in results:
                print(f"    '{token}' -> {countries} countries, {df} articles")

            print()

            # Step 5: Rebuild strategic_candidates_300h
            print("Step 5: Rebuilding strategic candidates with improved filtering...")

            # Recreate the strategic_candidates_300h materialized view
            strategic_candidates_sql = text(
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
                WHERE a.language = 'EN' AND a.created_at >= (now() - '300:00:00'::interval) 
                  AND ((ev.has_event AND g.gpe_cnt >= 2) OR (g.gpe_cnt >= 1 AND so.has_org) OR COALESCE(g.gpe_cnt, 0) >= 3);
            """
            )

            session.execute(strategic_candidates_sql)
            session.commit()

            # Check new candidate distribution
            result = session.execute(
                text("SELECT COUNT(*) FROM strategic_candidates_300h;")
            ).fetchone()
            print(f"  Strategic candidates after improvement: {result[0]}")

            # Show reason breakdown
            results = session.execute(
                text(
                    "SELECT reason, COUNT(*) FROM strategic_candidates_300h GROUP BY reason ORDER BY 2 DESC;"
                )
            ).fetchall()
            print("  Qualification reasons:")
            for reason, count in results:
                print(f"    {reason}: {count} candidates")

            print()

            # Step 6: Quick KPI check
            print("Step 6: Updated KPI measurements...")

            # KPI 1: Strategic filtering rate
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
                        f"  KPI 1 - Strategic filtering rate: {pct_candidates}% ({strategic_candidates}/{total_articles})"
                    )
                    if 35 <= pct_candidates <= 55:
                        print("    PASS - Within target range (35-55%)")
                    elif pct_candidates < 35:
                        print("    LOW - Below target range")
                    else:
                        print("    HIGH - Above target range")

            # KPI 2: Clustering success rate
            kpi2_result = session.execute(
                text(
                    """
                WITH stats AS (
                  SELECT 
                    (SELECT COUNT(*) FROM strategic_candidates_300h) AS strategic_candidates,
                    COUNT(*) AS clustered_articles
                  FROM strategic_candidates_300h sc
                  INNER JOIN article_cluster_members acm ON acm.article_id = sc.article_id
                  INNER JOIN article_clusters ac ON ac.cluster_id = acm.cluster_id
                  WHERE ac.created_at >= NOW() - INTERVAL '300 hours'
                )
                SELECT strategic_candidates, clustered_articles FROM stats;
            """
                )
            ).fetchone()

            if kpi2_result:
                strategic_candidates, clustered_articles = kpi2_result
                if strategic_candidates > 0:
                    pct_clustered = round(
                        (clustered_articles / strategic_candidates) * 100, 1
                    )
                    print(
                        f"  KPI 2 - Clustering success rate: {pct_clustered}% ({clustered_articles}/{strategic_candidates})"
                    )
                    if 35 <= pct_clustered <= 55:
                        print("    PASS - Within target range (35-55%)")
                    elif pct_clustered < 35:
                        print("    LOW - Clustering may be too strict")
                    else:
                        print("    HIGH - Clustering may be too permissive")

        print()
        print("=== STRATEGIC FILTERING IMPROVEMENTS COMPLETED ===")
        print("Expected outcomes:")
        print(
            "- Event tokens should now focus on strategic actions (tariffs, sanctions, ceasefire, elections)"
        )
        print("- Reduced noise from person/geo hubs (trump, gaza, washington)")
        print("- Expanded org recognition for country+org strategic relationships")
        print("- Strategic candidates should maintain 35-55% range with higher quality")

    except Exception as e:
        print(f"Error during strategic filtering improvement: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Enhance Strategic Filtering Exclusions
Add more comprehensive exclusions for better event token filtering
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database


def main():
    """Add comprehensive exclusions to improve event token filtering"""

    try:
        # Initialize database
        config = get_config()
        initialize_database(config.database)

        print("=== ENHANCING STRATEGIC FILTERING EXCLUSIONS ===")
        print()

        with get_db_session() as session:

            # Add more geo-political places and person names
            print("Adding comprehensive geo-political and person exclusions...")

            # Add major world cities/capitals that are often mentioned but aren't events
            geo_exclusions_sql = text(
                """
                INSERT INTO ref_geo_places(tok) VALUES
                  ('washington'),('beijing'),('moscow'),('london'),('paris'),
                  ('berlin'),('tokyo'),('seoul'),('new delhi'),('ottawa'),
                  ('canberra'),('brasilia'),('mexico city'),('cairo'),('baghdad'),
                  ('tehran'),('kabul'),('islamabad'),('ankara'),('madrid'),
                  ('rome'),('athens'),('vienna'),('brussels'),('amsterdam'),
                  ('stockholm'),('oslo'),('copenhagen'),('helsinki'),('warsaw'),
                  ('prague'),('budapest'),('bucharest'),('sofia'),('zagreb'),
                  ('belgrade'),('sarajevo'),('skopje'),('tirana'),('podgorica'),
                  ('white house'),('kremlin'),('downing street'),('elysee palace')
                ON CONFLICT DO NOTHING;
            """
            )

            session.execute(geo_exclusions_sql)
            session.commit()

            # Add common political titles and person references
            titles_exclusions_sql = text(
                """
                INSERT INTO ref_geo_places(tok) VALUES
                  ('president'),('prime minister'),('chancellor'),('king'),('queen'),
                  ('emperor'),('chairman'),('secretary'),('minister'),('ambassador'),
                  ('senator'),('congressman'),('mayor'),('governor'),('premier')
                ON CONFLICT DO NOTHING;
            """
            )

            session.execute(titles_exclusions_sql)
            session.commit()

            # Add common person name fragments that appear in canonicalized form
            person_exclusions_sql = text(
                """
                INSERT INTO ref_geo_places(tok) VALUES
                  ('vladimir putin'),('donald'),('joe biden'),('xi jinping'),
                  ('emmanuel macron'),('olaf scholz'),('rishi sunak'),('justin trudeau'),
                  ('narendra modi'),('volodymyr zelensky'),('benjamin netanyahu'),
                  ('recep erdogan'),('antonio guterres'),('ursula von der leyen'),
                  ('steve witkoff'),('marco rubio'),('elon musk')
                ON CONFLICT DO NOTHING;
            """
            )

            session.execute(person_exclusions_sql)
            session.commit()

            # Add media sources that shouldn't be events
            media_exclusions_sql = text(
                """
                INSERT INTO ref_geo_places(tok) VALUES
                  ('guardian'),('reuters'),('bbc'),('cnn'),('associated press'),
                  ('new york times'),('wall street journal'),('washington post'),
                  ('financial times'),('bloomberg'),('al jazeera'),('france24')
                ON CONFLICT DO NOTHING;
            """
            )

            session.execute(media_exclusions_sql)
            session.commit()

            # Check total exclusions
            result = session.execute(
                text("SELECT COUNT(*) FROM ref_geo_places;")
            ).fetchone()
            print(f"  Total geo-political exclusions: {result[0]}")

            print()

            # Rebuild event tokens with enhanced exclusions
            print("Rebuilding event tokens with enhanced exclusions...")

            # Drop and recreate
            session.execute(
                text(
                    "DROP MATERIALIZED VIEW IF EXISTS strategic_candidates_300h CASCADE;"
                )
            )
            session.execute(
                text("DROP MATERIALIZED VIEW IF EXISTS event_tokens_30d CASCADE;")
            )

            # Create improved event token learner (same as before, just with more exclusions)
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
            print(f"  Enhanced event tokens: {result[0]} strategic events identified")

            # Show top strategic event tokens (should be much better now)
            results = session.execute(
                text(
                    "SELECT token, countries, df FROM event_tokens_30d ORDER BY countries DESC, df DESC LIMIT 15;"
                )
            ).fetchall()
            print("  Top strategic event tokens (improved):")
            for token, countries, df in results:
                print(f"    '{token}' -> {countries} countries, {df} articles")

            print()

            # Rebuild strategic candidates
            print("Rebuilding strategic candidates with enhanced filtering...")

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

            # Check new results
            result = session.execute(
                text("SELECT COUNT(*) FROM strategic_candidates_300h;")
            ).fetchone()
            print(f"  Enhanced strategic candidates: {result[0]}")

            # Show reason breakdown
            results = session.execute(
                text(
                    "SELECT reason, COUNT(*) FROM strategic_candidates_300h GROUP BY reason ORDER BY 2 DESC;"
                )
            ).fetchall()
            print("  Qualification reasons:")
            for reason, count in results:
                print(f"    {reason}: {count} candidates")

            # Final KPI check
            print()
            print("Final KPI check:")

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
                        f"  Strategic filtering rate: {pct_candidates}% ({strategic_candidates}/{total_articles})"
                    )
                    if 35 <= pct_candidates <= 55:
                        print("    TARGET ACHIEVED: Within 35-55% range")
                    elif pct_candidates < 35:
                        print("    Still below target - may need to relax filtering")
                    else:
                        print("    Above target - very strategic focus")

        print()
        print("=== STRATEGIC FILTERING ENHANCEMENT COMPLETED ===")
        print("Enhanced exclusions include:")
        print("- Major world cities and capitals")
        print("- Political titles and positions")
        print("- Person names and fragments")
        print("- Media source names")
        print(
            "- Should now focus on strategic actions: sanctions, tariffs, agreements, conflicts, etc."
        )

    except Exception as e:
        print(f"Error during enhancement: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

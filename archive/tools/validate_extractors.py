#!/usr/bin/env python3
"""
Drift validation tool for learned extraction profiles

Re-tests existing profiles on fresh pages to detect degradation and trigger
automatic re-learning when performance drops below thresholds.
"""

import argparse
import asyncio
import json
import statistics
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import structlog
from sqlalchemy import text

sys.path.append(".")

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from tools.learn_feed_extractors import FeedExtractorLearner

logger = structlog.get_logger(__name__)


class ExtractorValidator:
    """Validate and maintain extraction profiles"""

    def __init__(self):
        self.config = get_config()
        initialize_database(self.config.database)
        self.learner = FeedExtractorLearner()

    def get_profiled_feeds(self) -> List[Dict]:
        """Get all feeds/domains that have extraction profiles"""
        with get_db_session() as db:
            query = text(
                """
                SELECT DISTINCT 
                    id, 
                    url, 
                    extraction_profile,
                    extraction_profile->>'scope' as scope,
                    extraction_profile->>'last_validated_at' as last_validated_at,
                    extraction_profile->>'source' as source
                FROM news_feeds 
                WHERE extraction_profile IS NOT NULL
                ORDER BY last_validated_at ASC
            """
            )
            result = db.execute(query)
            return [dict(row._mapping) for row in result.fetchall()]

    async def validate_feed_profile(
        self, feed_info: Dict, days: int = 7, sample_size: int = 5
    ) -> Dict:
        """Validate a single feed's extraction profile"""
        feed_id = feed_info["id"]
        feed_url = feed_info["url"]
        profile = (
            json.loads(feed_info["extraction_profile"])
            if isinstance(feed_info["extraction_profile"], str)
            else feed_info["extraction_profile"]
        )

        logger.info(f"Validating profile for {feed_url}")

        # Get fresh articles from the last N days
        recent_articles = self.learner.get_recent_articles(
            feed_id=feed_id, days=days, limit=sample_size * 2
        )

        if len(recent_articles) < sample_size:
            logger.warning(
                f"Not enough recent articles for {feed_url}: {len(recent_articles)} < {sample_size}"
            )
            return {
                "feed_id": feed_id,
                "feed_url": feed_url,
                "success": False,
                "error": "insufficient_articles",
                "articles_found": len(recent_articles),
            }

        # Sample URLs and fetch HTML
        sample_urls = [article["url"] for article in recent_articles[:sample_size]]
        html_samples = []

        for url in sample_urls:
            html = await self.learner.fetch_html(url)
            if html:
                html_samples.append((url, html))

        if (
            len(html_samples) < sample_size * 0.6
        ):  # Need at least 60% successful fetches
            logger.warning(f"Too few pages fetched for {feed_url}: {len(html_samples)}")
            return {
                "feed_id": feed_id,
                "feed_url": feed_url,
                "success": False,
                "error": "fetch_failures",
                "pages_fetched": len(html_samples),
            }

        # Validate current profile against fresh content
        passes, validation_results = self.learner.validate_profile(
            profile, html_samples
        )

        # Calculate metrics
        successful_results = [
            r for r in validation_results["results"] if r.get("success", False)
        ]
        if successful_results:
            lengths = [r.get("length", 0) for r in successful_results]
            densities = [r.get("density", 0) for r in successful_results]
            median_length = statistics.median(lengths) if lengths else 0
            median_density = statistics.median(densities) if densities else 0
        else:
            median_length = 0
            median_density = 0

        success_rate = validation_results["success_rate"]

        return {
            "feed_id": feed_id,
            "feed_url": feed_url,
            "success": passes,
            "success_rate": success_rate,
            "median_length": median_length,
            "median_density": median_density,
            "sample_size": len(html_samples),
            "validation_results": validation_results,
            "profile": profile,
        }

    def needs_relearning(self, validation_result: Dict) -> bool:
        """Determine if profile needs re-learning based on performance degradation"""
        # Failure rate > 30% (success rate < 70%)
        if validation_result["success_rate"] < 0.7:
            logger.info(
                f"Profile needs relearning: success rate {validation_result['success_rate']:.1%} < 70%"
            )
            return True

        # Extract baseline metrics from profile (if available)
        profile = validation_result["profile"]
        baseline_length = profile.get("min_length", 150)
        baseline_density = profile.get("density_threshold", 0.12)

        # Check if median length/density dropped by > 40%
        current_length = validation_result["median_length"]
        current_density = validation_result["median_density"]

        length_drop = (
            (baseline_length - current_length) / baseline_length
            if baseline_length > 0
            else 0
        )
        density_drop = (
            (baseline_density - current_density) / baseline_density
            if baseline_density > 0
            else 0
        )

        if length_drop > 0.4:
            logger.info(
                f"Profile needs relearning: length dropped {length_drop:.1%} > 40%"
            )
            return True

        if density_drop > 0.4:
            logger.info(
                f"Profile needs relearning: density dropped {density_drop:.1%} > 40%"
            )
            return True

        return False

    async def auto_relearn_profile(self, feed_info: Dict) -> bool:
        """Automatically re-learn profile for a feed"""
        feed_id = feed_info["id"]
        profile = (
            json.loads(feed_info["extraction_profile"])
            if isinstance(feed_info["extraction_profile"], str)
            else feed_info["extraction_profile"]
        )
        scope = profile.get("scope", "feed")

        logger.info(f"Auto-relearning profile for feed {feed_id}")

        try:
            if scope == "domain":
                # Extract domain from feed URL
                from urllib.parse import urlparse

                domain = urlparse(feed_info["url"]).netloc
                success = await self.learner.learn_profile(
                    domain=domain, sample_size=8, dry_run=False
                )
            else:
                success = await self.learner.learn_profile(
                    feed_id=feed_id, sample_size=8, dry_run=False
                )

            if success:
                logger.info(f"Successfully re-learned profile for feed {feed_id}")
            else:
                logger.error(f"Failed to re-learn profile for feed {feed_id}")

            return success

        except Exception as e:
            logger.error(f"Auto-relearning failed for feed {feed_id}: {e}")
            return False

    def update_validation_timestamp(self, feed_id: str):
        """Update last_validated_at timestamp in profile"""
        with get_db_session() as db:
            query = text(
                """
                UPDATE news_feeds 
                SET extraction_profile = jsonb_set(
                    extraction_profile, 
                    '{last_validated_at}', 
                    to_jsonb(%(timestamp)s::text)
                )
                WHERE id = %(feed_id)s
            """
            )
            timestamp = datetime.utcnow().isoformat() + "Z"
            db.execute(query, {"feed_id": feed_id, "timestamp": timestamp})
            db.commit()

    async def validate_all_profiles(
        self, days: int = 7, sample_size: int = 5, auto_relearn: bool = False
    ) -> Dict:
        """Validate all extraction profiles and optionally trigger re-learning"""
        logger.info(f"Starting validation of all extraction profiles")

        # Get all profiled feeds
        profiled_feeds = self.get_profiled_feeds()
        logger.info(f"Found {len(profiled_feeds)} feeds with extraction profiles")

        results = []
        relearned_count = 0

        for feed_info in profiled_feeds:
            try:
                # Validate current profile
                validation_result = await self.validate_feed_profile(
                    feed_info, days, sample_size
                )
                results.append(validation_result)

                if validation_result["success"]:
                    # Profile is still good, update validation timestamp
                    self.update_validation_timestamp(feed_info["id"])
                    logger.info(f"Profile validated successfully: {feed_info['url']}")
                else:
                    # Profile is degraded
                    logger.warning(f"Profile validation failed: {feed_info['url']}")

                    # Check if auto-relearning is enabled and needed
                    if auto_relearn and self.needs_relearning(validation_result):
                        success = await self.auto_relearn_profile(feed_info)
                        if success:
                            relearned_count += 1
                            # Update result to reflect successful re-learning
                            validation_result["relearned"] = True
                        else:
                            validation_result["relearned"] = False

            except Exception as e:
                logger.error(f"Validation failed for {feed_info['url']}: {e}")
                results.append(
                    {
                        "feed_id": feed_info["id"],
                        "feed_url": feed_info["url"],
                        "success": False,
                        "error": str(e),
                    }
                )

        # Summary statistics
        total_feeds = len(results)
        successful_validations = sum(1 for r in results if r.get("success", False))
        failed_validations = total_feeds - successful_validations

        summary = {
            "total_feeds": total_feeds,
            "successful_validations": successful_validations,
            "failed_validations": failed_validations,
            "success_rate": (
                successful_validations / total_feeds if total_feeds > 0 else 0
            ),
            "relearned_count": relearned_count,
            "results": results,
        }

        logger.info(
            f"Validation complete: {successful_validations}/{total_feeds} successful ({summary['success_rate']:.1%})"
        )
        if auto_relearn:
            logger.info(f"Auto-relearned {relearned_count} profiles")

        return summary


async def main():
    parser = argparse.ArgumentParser(
        description="Validate extraction profiles and detect drift"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Fresh content window in days"
    )
    parser.add_argument(
        "--sample", type=int, default=5, help="Sample size for validation"
    )
    parser.add_argument(
        "--auto-relearn",
        action="store_true",
        help="Automatically re-learn profiles that fail validation",
    )
    parser.add_argument("--feed-id", help="Validate specific feed only")

    args = parser.parse_args()

    validator = ExtractorValidator()

    if args.feed_id:
        # Validate single feed
        with get_db_session() as db:
            query = text(
                """
                SELECT id, url, extraction_profile 
                FROM news_feeds 
                WHERE id = :feed_id AND extraction_profile IS NOT NULL
            """
            )
            result = db.execute(query, {"feed_id": args.feed_id})
            feed_info = result.fetchone()

            if not feed_info:
                print(f"Feed {args.feed_id} not found or has no extraction profile")
                sys.exit(1)

            feed_dict = dict(feed_info._mapping)
            validation_result = await validator.validate_feed_profile(
                feed_dict, args.days, args.sample
            )

            print(f"\nValidation Results for {feed_dict['url']}:")
            print(f"Success: {validation_result['success']}")
            print(f"Success Rate: {validation_result.get('success_rate', 0):.1%}")
            print(f"Median Length: {validation_result.get('median_length', 0)}")
            print(f"Median Density: {validation_result.get('median_density', 0):.3f}")

            if not validation_result["success"] and args.auto_relearn:
                if validator.needs_relearning(validation_result):
                    print("Triggering auto-relearning...")
                    success = await validator.auto_relearn_profile(feed_dict)
                    print(f"Re-learning {'successful' if success else 'failed'}")
    else:
        # Validate all profiles
        summary = await validator.validate_all_profiles(
            args.days, args.sample, args.auto_relearn
        )

        print(f"\nValidation Summary:")
        print(f"Total Feeds: {summary['total_feeds']}")
        print(f"Successful Validations: {summary['successful_validations']}")
        print(f"Failed Validations: {summary['failed_validations']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")

        if args.auto_relearn:
            print(f"Profiles Re-learned: {summary['relearned_count']}")

        # Show failed feeds
        failed_feeds = [r for r in summary["results"] if not r.get("success", False)]
        if failed_feeds:
            print(f"\nFailed Validations:")
            for result in failed_feeds:
                error = result.get("error", "validation_failed")
                relearned = " (RELEARNED)" if result.get("relearned") else ""
                print(f"  {error:15} | {result['feed_url']}{relearned}")


if __name__ == "__main__":
    asyncio.run(main())

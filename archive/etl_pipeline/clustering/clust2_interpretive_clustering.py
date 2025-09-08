#!/usr/bin/env python3
"""
CLUST-2: Interpretive Clustering
Strategic Narrative Intelligence ETL Pipeline

Three-module system:
1. Strategic Pre-Filtering - LLM-based cluster classification
2. Digest Assembly - JSON blob generation for cluster content
3. Narrative Segmentation - Parent/child narrative generation

Replaces clust2_segment_narratives.py with new specification.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

# Fix Windows Unicode encoding
if sys.platform.startswith("win"):
    import io

    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.core.llm_client import get_llm_client
from sqlalchemy import text


class CLUST2InterpretiveClustering:
    """
    CLUST-2: Three-module interpretive clustering system
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize CLUST-2 system"""
        self.config = config or {}

        # Initialize core systems
        self.app_config = get_config()
        initialize_database(self.app_config.database)

        # Initialize LLM client
        self.llm_client = get_llm_client()

        # Configuration parameters
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.max_fallback_articles = self.config.get("max_fallback_articles", 2)
        self.max_articles_per_cluster = self.config.get("max_articles_per_cluster", 100)

        # Statistics tracking
        self.stats = {
            "clusters_processed": 0,
            "strategic_count": 0,
            "non_strategic_count": 0,
            "skipped_count": 0,
            "narratives_created": 0,
            "parent_narratives": 0,
            "child_narratives": 0,
        }

    # MODULE 1: Strategic Pre-Filtering

    async def strategic_pre_filtering(
        self, clusters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Module 1: Filter clusters for strategic relevance

        Args:
            clusters: List of cluster dictionaries with id, label, keywords

        Returns:
            List of strategic clusters to process further
        """
        print("=== Module 1: Strategic Pre-Filtering ===")
        strategic_clusters = []

        for cluster in clusters:
            cluster_id = cluster["cluster_id"]
            cluster_label = cluster["cluster_label"]
            cluster_keywords = cluster.get("cluster_keywords", [])

            print(f"Filtering cluster: {cluster_label}")

            # Step 1: LLM-based classification
            classification_result = await self._classify_cluster_strategic(
                cluster_label, cluster_keywords
            )

            # Step 2: Optional fallback review if needed
            if (
                classification_result["classification"] == "review_required"
                or classification_result["confidence"] < self.confidence_threshold
            ):

                print(f"  Triggering fallback review for {cluster_id}")
                classification_result = await self._fallback_review(
                    cluster_id, cluster_label, cluster_keywords
                )

            # Step 3: Update cluster status
            status = classification_result["classification"]

            # Map non_strategic to discarded for database constraint compatibility
            db_status = "discarded" if status == "non_strategic" else status

            with get_db_session() as session:
                session.execute(
                    text(
                        """
                    UPDATE article_clusters 
                    SET strategic_status = :status
                    WHERE cluster_id = :cluster_id
                """
                    ),
                    {"status": db_status, "cluster_id": cluster_id},
                )
                session.commit()

            if status == "strategic":
                strategic_clusters.append(cluster)
                self.stats["strategic_count"] += 1
                print(f"  -> STRATEGIC: {classification_result['reason']}")
            elif status == "non_strategic":
                self.stats["non_strategic_count"] += 1
                print(f"  -> NON-STRATEGIC: {classification_result['reason']}")
            else:
                self.stats["skipped_count"] += 1
                print(f"  -> SKIPPED: {classification_result['reason']}")

        print(f"Strategic clusters identified: {len(strategic_clusters)}")
        return strategic_clusters

    async def _classify_cluster_strategic(
        self, cluster_label: str, cluster_keywords: List[str]
    ) -> Dict[str, Any]:
        """LLM-based strategic classification of cluster"""

        keywords_str = ", ".join(cluster_keywords[:10])  # Limit keywords

        system_prompt = """You are a strategic intelligence classifier. Determine if a news cluster is strategically relevant.

STRATEGIC DOMAINS:
- Geopolitics, diplomacy, policy, sanctions, war/conflict, security
- Resource control, infrastructure, energy geopolitics, migration  
- Technology power: AI, semiconductors, cyber, nuclear, space
- Social/political struggles with ideological framing

NON-STRATEGIC DOMAINS:
- Routine sports results, entertainment, celebrity gossip
- Local animal stories, weather, traffic, weddings
- Incidents with no broader impact or actor significance

Return JSON only:
{
  "classification": "strategic" | "non_strategic" | "review_required",
  "confidence": 0.0-1.0,
  "reason": "Brief justification"
}"""

        user_prompt = f"""Classify this cluster:
Label: {cluster_label}
Keywords: {keywords_str}"""

        try:
            response = await self.llm_client.generate_json(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                max_tokens=500,
                temperature=0.3,
            )

            return response

        except Exception as e:
            print(f"Error in strategic classification: {e}")
            return {
                "classification": "review_required",
                "confidence": 0.0,
                "reason": f"Classification error: {e}",
            }

    async def _fallback_review(
        self, cluster_id: str, cluster_label: str, cluster_keywords: List[str]
    ) -> Dict[str, Any]:
        """Fallback review with article context"""

        # Get sample articles for context
        with get_db_session() as session:
            result = session.execute(
                text(
                    """
                SELECT a.title, a.content
                FROM articles a
                JOIN article_clusters ac ON a.id = ac.article_id
                WHERE ac.cluster_id = :cluster_id
                ORDER BY a.published_at DESC
                LIMIT :limit
            """
                ),
                {"cluster_id": cluster_id, "limit": self.max_fallback_articles},
            )

            articles = result.fetchall()

        # Build context string
        article_context = []
        for title, content in articles:
            excerpt = content[:100] if content else ""
            article_context.append(f"Title: {title}\nExcerpt: {excerpt}")

        context_str = "\n\n".join(article_context)
        keywords_str = ", ".join(cluster_keywords[:10])

        system_prompt = """You are a strategic intelligence classifier. With article context, determine if this cluster is strategically relevant.

STRATEGIC: Geopolitics, policy, security, technology power, ideological struggles
NON-STRATEGIC: Sports, entertainment, local incidents without broader impact

Return JSON only:
{
  "classification": "strategic" | "non_strategic",
  "confidence": 0.0-1.0,
  "reason": "Brief justification"
}"""

        user_prompt = f"""Classify this cluster with context:
Label: {cluster_label}
Keywords: {keywords_str}

Article Context:
{context_str}"""

        try:
            response = await self.llm_client.generate_json(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                max_tokens=500,
                temperature=0.3,
            )

            return response

        except Exception as e:
            print(f"Error in fallback review: {e}")
            return {
                "classification": "non_strategic",
                "confidence": 0.5,
                "reason": f"Fallback error: {e}",
            }

    # MODULE 2: Digest Assembly

    async def digest_assembly(
        self, strategic_clusters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Module 2: Assemble cluster digests as JSON blobs

        Args:
            strategic_clusters: Clusters marked as strategic

        Returns:
            Clusters with populated cluster_content field
        """
        print("=== Module 2: Digest Assembly ===")

        for cluster in strategic_clusters:
            cluster_id = cluster["cluster_id"]
            cluster_label = cluster["cluster_label"]
            cluster_keywords = cluster.get("cluster_keywords", [])

            print(f"Assembling digest for: {cluster_label}")

            # Get articles for this cluster
            with get_db_session() as session:
                result = session.execute(
                    text(
                        """
                    SELECT a.id, a.title, a.summary, a.content, a.url, a.published_at
                    FROM articles a
                    JOIN article_clusters ac ON a.id = ac.article_id
                    WHERE ac.cluster_id = :cluster_id
                    ORDER BY a.published_at DESC
                    LIMIT :limit
                """
                    ),
                    {"cluster_id": cluster_id, "limit": self.max_articles_per_cluster},
                )

                articles = result.fetchall()

            # Build digest structure
            digest_articles = []
            for article_id, title, summary, content, url, published_at in articles:
                # Summary fallback logic
                if summary and len(summary.split()) >= 20:
                    article_summary = summary
                else:
                    # Use first 100 words of content
                    content_words = content.split()[:100] if content else []
                    article_summary = " ".join(content_words)

                digest_articles.append(
                    {
                        "article_id": str(article_id),
                        "title": title,
                        "summary": article_summary,
                        "url": url,
                        "date_published": (
                            published_at.strftime("%Y-%m-%d") if published_at else None
                        ),
                    }
                )

            # Create digest JSON
            digest = {
                "cluster_id": cluster_id,
                "cluster_label": cluster_label,
                "cluster_keywords": cluster_keywords,
                "articles": digest_articles,
            }

            # Store digest in database
            digest_json = json.dumps(digest)

            with get_db_session() as session:
                session.execute(
                    text(
                        """
                    UPDATE article_clusters 
                    SET cluster_content = :digest
                    WHERE cluster_id = :cluster_id
                """
                    ),
                    {"digest": digest_json, "cluster_id": cluster_id},
                )
                session.commit()

            # Update cluster object
            cluster["cluster_content"] = digest

            print(f"  Assembled {len(digest_articles)} articles")

        print(f"Digest assembly complete for {len(strategic_clusters)} clusters")
        return strategic_clusters

    # MODULE 3: Narrative Segmentation

    async def narrative_segmentation(
        self, clusters_with_digests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Module 3: Generate parent/child narrative candidates

        Args:
            clusters_with_digests: Strategic clusters with assembled digests

        Returns:
            Processing results summary
        """
        print("=== Module 3: Narrative Segmentation ===")

        for cluster in clusters_with_digests:
            cluster_id = cluster["cluster_id"]
            cluster_label = cluster["cluster_label"]
            cluster_content = cluster["cluster_content"]

            print(f"Generating narratives for: {cluster_label}")

            # Generate narratives using LLM
            narrative_result = await self._generate_cluster_narratives(cluster_content)

            if narrative_result.get("status") == "SKIP_CLUSTER":
                print(f"  -> SKIPPED: Non-strategic content")
                with get_db_session() as session:
                    session.execute(
                        text(
                            """
                        UPDATE article_clusters 
                        SET strategic_status = 'skipped'
                        WHERE cluster_id = :cluster_id
                    """
                        ),
                        {"cluster_id": cluster_id},
                    )
                    session.commit()
                self.stats["skipped_count"] += 1
                continue

            # Store narratives in database
            parent_narrative = narrative_result.get("parent_narrative")
            child_narratives = narrative_result.get("child_narratives", [])

            if parent_narrative:
                parent_id = await self._store_narrative(
                    cluster_id=cluster_id,
                    narrative_type="parent",
                    title=parent_narrative["title"],
                    summary=parent_narrative["summary"],
                    parent_id=None,
                )
                self.stats["parent_narratives"] += 1
                self.stats["narratives_created"] += 1

                # Store child narratives
                for child in child_narratives:
                    await self._store_narrative(
                        cluster_id=cluster_id,
                        narrative_type="child",
                        title=child["title"],
                        summary=child["summary"],
                        parent_id=parent_id,
                        divergence_type=child.get("divergence_type"),
                    )
                    self.stats["child_narratives"] += 1
                    self.stats["narratives_created"] += 1

                print(f"  -> Created: 1 parent + {len(child_narratives)} children")

            self.stats["clusters_processed"] += 1

        return self._generate_processing_summary()

    async def _generate_cluster_narratives(
        self, cluster_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate parent/child narratives for a cluster using LLM"""

        # CLUST-2 Meta-Prompt
        meta_prompt = """You are a geopolitical reasoning system that identifies candidate narratives from clusters of related news articles. Your output will be used in a strategic intelligence platform that maps long-duration storylines and framings - not as a news feed or headline generator. Focus on surfacing coherent arcs and competing interpretations, not summarizing individual events.

What is a Narrative:
A narrative is a coherent strategic storyline that connects multiple events, actors, or claims into a persistent arc of meaning. It answers not just what happened, but why it matters, who is involved, and what trajectory it suggests. It influences policy, public perception, or geopolitical alignment over time. It spans weeks, months, or years, often reappearing in different contexts. It is not a single incident, news item, or event headline. It typically involves recurring themes, actors, or ideological tensions.

Parent vs Child Narratives:
A Parent Narrative is a broad, durable strategic arc that explains long-term power struggles, value conflicts, or geopolitical realignments.
Example: "Global South pushes to reshape international economic order"

Child Narratives are specific, diverging framings that interpret parts of the parent arc through different causal, moral, or strategic lenses.
Example 1: "BRICS expansion seen as challenge to dollar dominance"
Example 2: "Western allies tighten control over global tech stack"

Child narratives differ by divergence category: Causal, Moral, Strategic, Identity, or Tone.

Strategic vs Non-Strategic:
Strategic: Geopolitics, international relations, defense, energy, technology, ideology, state policy, human rights, major economic realignment
Non-Strategic: Sports, celebrity, lifestyle, entertainment, apolitical local stories, isolated crime or weather events

Granularity Guidelines:
Focus on fewer, more strategic narratives, not over-fragmented event summaries. Group related events under one umbrella if they share: Actors, Policy themes, Strategic goals, etc. Do not generate narratives from minor or one-off stories unless symbolically or strategically pivotal.

For each strategic cluster, return:
{
  "parent_narrative": {
    "title": "Strategic arc framing (not journalistic headline)",
    "summary": "2-3 neutral sentences outlining scope, actors, and why this matters strategically."
  },
  "child_narratives": [
    {
      "title": "Distinct framing (8-14 words)",
      "summary": "1-2 sentences describing how this framing differs",
      "divergence_type": "Causal|Moral|Strategic|Identity|Tone"
    }
  ]
}

If the cluster is not strategic, return: {"status": "SKIP_CLUSTER"}"""

        # Format cluster content for LLM
        articles_text = []
        for article in cluster_content["articles"][
            :20
        ]:  # Limit articles for LLM context
            articles_text.append(
                f"Title: {article['title']}\nSummary: {article['summary']}"
            )

        articles_str = "\n\n".join(articles_text)

        user_prompt = f"""Analyze this article cluster and generate candidate narratives:

Cluster: {cluster_content['cluster_label']}
Keywords: {', '.join(cluster_content['cluster_keywords'][:10])}

Articles:
{articles_str}

Generate parent and child narrative candidates following the specified format."""

        try:
            response = await self.llm_client.generate_json(
                prompt=f"{meta_prompt}\n\n{user_prompt}",
                max_tokens=2000,
                temperature=0.3,
            )

            return response

        except Exception as e:
            print(f"Error generating narratives: {e}")
            return {"status": "SKIP_CLUSTER"}

    async def _store_narrative(
        self,
        cluster_id: str,
        narrative_type: str,
        title: str,
        summary: str,
        parent_id: Optional[str] = None,
        divergence_type: Optional[str] = None,
    ) -> str:
        """Store narrative in database"""

        narrative_id = str(uuid.uuid4())

        with get_db_session() as session:
            session.execute(
                text(
                    """
                INSERT INTO narratives (
                    id, narrative_id, title, summary, parent_id, consolidation_stage, 
                    created_at, updated_at, origin_language, dominant_source_languages,
                    alignment, actor_origin, conflict_alignment, frame_logic
                ) VALUES (
                    :id, :narrative_id, :title, :summary, :parent_id, 'raw',
                    :created_at, :updated_at, 'en', '{}', '{}', '{}', '{}', '{}'
                )
            """
                ),
                {
                    "id": narrative_id,
                    "narrative_id": narrative_id,
                    "title": title,
                    "summary": summary,
                    "parent_id": parent_id,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
            )
            session.commit()

        return narrative_id

    def _generate_processing_summary(self) -> Dict[str, Any]:
        """Generate final processing summary"""
        return {
            "status": "completed",
            "clusters_processed": self.stats["clusters_processed"],
            "strategic_count": self.stats["strategic_count"],
            "non_strategic_count": self.stats["non_strategic_count"],
            "skipped_count": self.stats["skipped_count"],
            "narratives_created": self.stats["narratives_created"],
            "parent_narratives": self.stats["parent_narratives"],
            "child_narratives": self.stats["child_narratives"],
        }

    # MAIN PROCESSING WORKFLOW

    async def process_clusters(
        self, cluster_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Main CLUST-2 processing workflow

        Args:
            cluster_limit: Optional limit on clusters to process

        Returns:
            Processing results summary
        """
        print("=== CLUST-2: Interpretive Clustering ===")
        print(f"Started at: {datetime.now()}")

        # Get pending clusters
        clusters = await self._get_pending_clusters(cluster_limit)
        if not clusters:
            return {"status": "no_clusters", "message": "No pending clusters found"}

        print(f"Found {len(clusters)} clusters to process")

        # Module 1: Strategic Pre-Filtering
        strategic_clusters = await self.strategic_pre_filtering(clusters)

        if not strategic_clusters:
            return self._generate_processing_summary()

        # Module 2: Digest Assembly
        clusters_with_digests = await self.digest_assembly(strategic_clusters)

        # Module 3: Narrative Segmentation
        results = await self.narrative_segmentation(clusters_with_digests)

        print("\n=== CLUST-2 Processing Complete ===")
        print(f"Strategic clusters: {results['strategic_count']}")
        print(f"Narratives created: {results['narratives_created']}")
        print(f"- Parent narratives: {results['parent_narratives']}")
        print(f"- Child narratives: {results['child_narratives']}")

        return results

    async def _get_pending_clusters(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get clusters with strategic_status = 'pending'"""

        with get_db_session() as session:
            query = text(
                """
                SELECT cluster_id, cluster_label, cluster_keywords, cluster_size
                FROM article_clusters 
                WHERE strategic_status = 'pending'
                ORDER BY cluster_size DESC
            """
            )

            if limit:
                query = text(str(query) + f" LIMIT {limit}")

            result = session.execute(query)

            clusters = []
            for row in result.fetchall():
                clusters.append(
                    {
                        "cluster_id": row[0],
                        "cluster_label": row[1],
                        "cluster_keywords": row[2] if row[2] else [],
                    }
                )

            return clusters


# CLI Interface
async def main():
    """CLI interface for CLUST-2 processing"""
    import argparse

    parser = argparse.ArgumentParser(description="CLUST-2: Interpretive Clustering")
    parser.add_argument("--limit", type=int, help="Limit number of clusters to process")
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.7,
        help="Confidence threshold for strategic classification",
    )

    args = parser.parse_args()

    config = {"confidence_threshold": args.confidence_threshold}

    processor = CLUST2InterpretiveClustering(config)

    try:
        results = await processor.process_clusters(args.limit)

        if results["status"] == "completed":
            print("\nCLUST-2 processing completed successfully!")
            return 0
        else:
            print(f"Processing result: {results}")
            return 0

    except Exception as e:
        print(f"CLUST-2 processing failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

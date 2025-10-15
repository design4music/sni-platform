"""
Neo4j enhancements for P2 strategic filtering
Simple graph-based intelligence for borderline cases
"""

from loguru import logger


class Neo4jEnhancements:
    """Use Neo4j relationships to enhance P2 strategic filtering"""

    def __init__(self, sync_service):
        self.sync = sync_service

    async def enhance_p2_decision(self, title_data):
        """
        Use Neo4j to help with borderline P2 decisions.

        Args:
            title_data: Dict with id, title_display, pubdate_utc, entities

        Returns:
            Decision dict with gate_keep/gate_reason if Neo4j provides signal,
            or None to let normal LLM processing continue
        """

        # First, sync the title so it's in Neo4j
        await self.sync.sync_title(title_data)

        # Check Neo4j relationships
        strategic_neighbors = await self.sync.find_strategic_neighbors(
            title_data["id"], threshold=2
        )

        if strategic_neighbors:
            logger.info(
                f"Title connects to {len(strategic_neighbors)} strategic articles"
            )
            for neighbor in strategic_neighbors:
                logger.info(
                    f"   - Shared {neighbor['shared_entities']} entities: {neighbor['shared_entity_names']}"
                )

            # If strong connections, boost confidence
            max_shared = max([n["shared_entities"] for n in strategic_neighbors])
            if max_shared >= 3:
                return {
                    "gate_keep": True,
                    "gate_reason": f"Connected to {len(strategic_neighbors)} strategic articles",
                    "neo4j_boost": True,
                }

        return None

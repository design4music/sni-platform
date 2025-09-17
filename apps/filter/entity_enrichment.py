#!/usr/bin/env python3
"""
Phase 2A: Entity Enrichment Service
Combines CLUST-1 strategic filtering and CLUST-2 actor extraction 
to populate titles.entities jsonb column for bucketless processing.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from loguru import logger

from apps.filter.taxonomy_extractor import create_multi_vocab_taxonomy_extractor
from core.database import get_db_session
from sqlalchemy import text


class EntityEnrichmentService:
    """
    Service to enrich titles with extracted entities in Phase 2A.
    
    Combines strategic filtering (CLUST-1) + actor extraction (CLUST-2) 
    to populate titles.entities column for direct GEN-1 processing.
    
    Logic:
    - actors + people = positive entities (store these)
    - stop_culture = negative filter (don't store, just blocks is_strategic)
    """
    
    def __init__(self):
        self.taxonomy_extractor = create_multi_vocab_taxonomy_extractor()
        
    def extract_entities_for_title(self, title_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities for a single title.
        
        Args:
            title_data: Title record with title_display, url, etc.
            
        Returns:
            entities dict with structure:
            {
                "actors": ["Germany", "NATO"], 
                "people": ["Scholz", "Biden"],
                "is_strategic": false,  // blocked by stop_culture match
                "extraction_version": "2.0"
            }
        """
        title_text = title_data.get("title_display", "")
        if not title_text:
            return self._empty_entities()
            
        # Use existing taxonomy extractor API
        # Check if strategic (go lists hit and not blocked by stop lists)
        strategic_hit = self.taxonomy_extractor.strategic_first_hit(title_text)
        is_strategic = strategic_hit is not None
        
        # Get all strategic actors if not blocked by stop words
        all_entities = []
        if is_strategic:
            all_entities = self.taxonomy_extractor.all_strategic_hits(title_text)
        
        # For Phase 2A, store all entities (countries, people, orgs) together
        # The API returns mixed entity types, so we simplify to single "actors" field
        entities = {
            "actors": all_entities,
            "is_strategic": is_strategic,
            "extraction_version": "2.0"
        }
        
        logger.debug(
            f"Extracted entities for '{title_text[:50]}': "
            f"entities={len(all_entities)}, "
            f"strategic={is_strategic}"
        )
        
        return entities
    
    def enrich_titles_batch(
        self, 
        title_ids: List[str] = None, 
        limit: int = 1000,
        since_hours: int = 24
    ) -> Dict[str, int]:
        """
        Enrich a batch of titles with entities.
        
        Args:
            title_ids: Specific title IDs to process (optional)
            limit: Max titles to process
            since_hours: Only process titles from last N hours (if title_ids not specified)
            
        Returns:
            stats dict with counts
        """
        stats = {
            "processed": 0,
            "strategic": 0,
            "non_strategic": 0,
            "blocked_by_stop": 0,
            "errors": 0
        }
        
        try:
            with get_db_session() as session:
                # Build query
                if title_ids:
                    # Build IN clause with UUID casting for PostgreSQL
                    placeholders = ",".join([f"'{uuid_str}'::uuid" for uuid_str in title_ids])
                    query = f"SELECT id, title_display, entities FROM titles WHERE id IN ({placeholders})"
                    params = {}
                else:
                    query = f"""
                    SELECT id, title_display, entities 
                    FROM titles 
                    WHERE created_at >= NOW() - INTERVAL '{since_hours} HOUR'
                    AND (entities IS NULL OR entities->>'extraction_version' != '2.0')
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """
                    params = {"limit": limit}
                
                # Get titles to process
                results = session.execute(text(query), params).fetchall()
                
                logger.info(f"Processing {len(results)} titles for entity extraction")
                
                # Process each title
                for row in results:
                    try:
                        title_data = {
                            "id": str(row.id),
                            "title_display": row.title_display
                        }
                        
                        # Extract entities
                        entities = self.extract_entities_for_title(title_data)
                        
                        # Update database
                        update_query = """
                        UPDATE titles 
                        SET entities = :entities
                        WHERE id = :title_id
                        """
                        
                        session.execute(
                            text(update_query), 
                            {
                                "entities": json.dumps(entities),
                                "title_id": title_data["id"]
                            }
                        )
                        
                        # Update stats
                        stats["processed"] += 1
                        if entities["is_strategic"]:
                            stats["strategic"] += 1
                        else:
                            stats["non_strategic"] += 1
                            # Check if blocked by stop words
                            if len(entities["actors"]) > 0 or len(entities["people"]) > 0:
                                stats["blocked_by_stop"] += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing title {row.id}: {e}")
                        stats["errors"] += 1
                        continue
                
                # Commit batch
                session.commit()
                
                logger.info(
                    f"Entity enrichment completed: {stats['processed']} processed, "
                    f"{stats['strategic']} strategic, {stats['non_strategic']} non-strategic "
                    f"({stats['blocked_by_stop']} blocked by stop words), {stats['errors']} errors"
                )
                
        except Exception as e:
            logger.error(f"Batch entity enrichment failed: {e}")
            stats["errors"] = len(title_ids) if title_ids else limit
            
        return stats
    
    def get_enrichment_status(self) -> Dict[str, int]:
        """Get status of entity enrichment across titles table."""
        try:
            with get_db_session() as session:
                status_query = """
                SELECT 
                    COUNT(*) as total_titles,
                    COUNT(entities) as enriched_titles,
                    COUNT(CASE WHEN entities->>'is_strategic' = 'true' THEN 1 END) as strategic_titles,
                    COUNT(CASE WHEN entities->>'extraction_version' = '2.0' THEN 1 END) as v2_enriched,
                    COUNT(CASE WHEN 
                        entities->>'is_strategic' = 'false' 
                        AND (jsonb_array_length(entities->'actors') > 0 OR jsonb_array_length(entities->'people') > 0)
                    THEN 1 END) as blocked_by_stop
                FROM titles
                WHERE created_at >= NOW() - INTERVAL '7 DAY'
                """
                
                result = session.execute(text(status_query)).fetchone()
                
                return {
                    "total_titles": result.total_titles or 0,
                    "enriched_titles": result.enriched_titles or 0,
                    "strategic_titles": result.strategic_titles or 0,
                    "blocked_by_stop": result.blocked_by_stop or 0,
                    "v2_enriched": result.v2_enriched or 0,
                    "enrichment_rate": (result.enriched_titles / max(result.total_titles, 1)) * 100
                }
                
        except Exception as e:
            logger.error(f"Failed to get enrichment status: {e}")
            return {"error": str(e)}
    
    def _empty_entities(self) -> Dict[str, Any]:
        """Return empty entities structure."""
        return {
            "actors": [],
            "is_strategic": False,
            "extraction_version": "2.0"
        }


def get_entity_enrichment_service() -> EntityEnrichmentService:
    """Factory function to get entity enrichment service."""
    return EntityEnrichmentService()


if __name__ == "__main__":
    # CLI usage
    import sys
    
    service = get_entity_enrichment_service()
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        # Show enrichment status
        status = service.get_enrichment_status()
        print("Entity Enrichment Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    else:
        # Enrich recent titles
        stats = service.enrich_titles_batch(since_hours=24, limit=100)
        print("Entity Enrichment Results:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
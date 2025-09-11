"""
GEN-1 Database Operations
Database interactions for Event Families and Framed Narratives
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import and_, desc, func, or_, text

from apps.gen1.models import BucketContext, EventFamily, FramedNarrative
from core.database import get_db_session


class Gen1Database:
    """
    Database operations for GEN-1 Event Family assembly and Framed Narrative generation
    Handles reading CLUST-2 buckets and writing Event Families/Framed Narratives
    """

    def __init__(self):
        pass

    def get_active_buckets(
        self,
        since_hours: int = 72,
        min_bucket_size: int = 2,
        limit: Optional[int] = None,
        order_by: str = "newest_first",
    ) -> List[BucketContext]:
        """
        Retrieve active CLUST-2 buckets for processing
        
        Args:
            since_hours: How far back to look for buckets
            min_bucket_size: Minimum number of titles per bucket
            limit: Maximum number of buckets to return
            order_by: Ordering strategy ('newest_first', 'largest_first', 'oldest_first')
            
        Returns:
            List of BucketContext objects ready for GEN-1 processing
        """
        try:
            with get_db_session() as session:
                # Base query for buckets with metadata
                bucket_query = """
                SELECT 
                    b.id as bucket_id,
                    b.bucket_id as bucket_key,
                    b.top_actors as actor_codes,
                    b.created_at,
                    b.date_window_start as time_window_start,
                    b.date_window_end as time_window_end,
                    EXTRACT(EPOCH FROM (b.date_window_end - b.date_window_start))/3600 as time_span_hours,
                    COUNT(bm.title_id) as title_count
                FROM buckets b
                JOIN bucket_members bm ON b.id = bm.bucket_id
                WHERE b.created_at >= NOW() - INTERVAL :since_hours HOUR
                GROUP BY b.id, b.bucket_id, b.top_actors, b.created_at, 
                         b.date_window_start, b.date_window_end
                HAVING COUNT(bm.title_id) >= :min_bucket_size
                """

                # Add ordering
                if order_by == "newest_first":
                    bucket_query += " ORDER BY b.created_at DESC"
                elif order_by == "largest_first":
                    bucket_query += " ORDER BY COUNT(bm.title_id) DESC"
                elif order_by == "oldest_first":
                    bucket_query += " ORDER BY b.created_at ASC"
                else:
                    bucket_query += " ORDER BY b.created_at DESC"

                # Add limit if specified
                if limit:
                    bucket_query += f" LIMIT {limit}"

                # Execute bucket query
                bucket_results = session.execute(
                    text(bucket_query), {"since_hours": since_hours, "min_bucket_size": min_bucket_size}
                ).fetchall()

                bucket_contexts = []

                for bucket_row in bucket_results:
                    # Get titles for this bucket
                    titles = self._get_bucket_titles(session, bucket_row.bucket_id)

                    bucket_context = BucketContext(
                        bucket_id=str(bucket_row.bucket_id),
                        bucket_key=bucket_row.bucket_key,
                        actor_codes=bucket_row.actor_codes or [],
                        title_count=int(bucket_row.title_count),
                        time_span_hours=float(bucket_row.time_span_hours or 0),
                        time_window_start=bucket_row.time_window_start,
                        time_window_end=bucket_row.time_window_end,
                        titles=titles,
                    )

                    bucket_contexts.append(bucket_context)

                logger.info(
                    f"Retrieved {len(bucket_contexts)} active buckets",
                    since_hours=since_hours,
                    min_size=min_bucket_size,
                    order=order_by,
                )

                return bucket_contexts

        except Exception as e:
            logger.error(f"Failed to get active buckets: {e}")
            raise

    def get_unassigned_strategic_titles(
        self,
        since_hours: int = 72,
        limit: Optional[int] = None,
        order_by: str = "newest_first",
    ) -> List[Dict[str, Any]]:
        """
        Retrieve unassigned strategic titles for direct EF processing (Phase 2)
        
        Args:
            since_hours: How far back to look for titles
            limit: Maximum number of titles to return
            order_by: Ordering strategy ('newest_first', 'oldest_first')
            
        Returns:
            List of strategic title dictionaries ready for GEN-1 processing
        """
        try:
            with get_db_session() as session:
                # Query for unassigned strategic titles
                titles_query = """
                SELECT 
                    id,
                    title_display as text,
                    url_gnews as url,
                    publisher_name as source_name,
                    pubdate_utc,
                    detected_language as lang_code,
                    gate_keep as strategic,
                    gate_actor_hit as gate_actors,
                    entities as extracted_actors,
                    created_at
                FROM titles 
                WHERE gate_keep = true 
                AND event_family_id IS NULL
                AND created_at >= NOW() - INTERVAL '%d HOUR' % :since_hours
                """
                
                # Add ordering
                if order_by == "newest_first":
                    titles_query += " ORDER BY pubdate_utc DESC"
                elif order_by == "oldest_first":
                    titles_query += " ORDER BY pubdate_utc ASC"
                else:
                    titles_query += " ORDER BY pubdate_utc DESC"
                
                # Add limit if specified
                if limit:
                    titles_query += f" LIMIT {limit}"
                
                # Execute query
                results = session.execute(
                    text(titles_query), {"since_hours": since_hours}
                ).fetchall()
                
                titles = []
                for row in results:
                    title_dict = {
                        "id": str(row.id),
                        "text": row.text,
                        "url": row.url,
                        "source": row.source_name,
                        "pubdate_utc": row.pubdate_utc,
                        "language": row.lang_code,
                        "strategic": row.strategic,
                        "gate_actors": row.gate_actors,
                        "actors": row.extracted_actors or [],
                        "created_at": row.created_at,
                    }
                    titles.append(title_dict)
                
                logger.info(
                    f"Retrieved {len(titles)} unassigned strategic titles",
                    since_hours=since_hours,
                    order=order_by,
                )
                
                return titles
                
        except Exception as e:
            logger.error(f"Failed to get unassigned strategic titles: {e}")
            raise

    async def assign_titles_to_event_family(
        self,
        title_ids: List[str],
        event_family_id: str,
        confidence: float,
        reason: str,
    ) -> bool:
        """
        Assign titles to an Event Family (Phase 2)
        
        Args:
            title_ids: List of title IDs to assign
            event_family_id: Event Family ID to assign them to
            confidence: LLM confidence in the assignment
            reason: Reason for assignment
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                # Update titles with Event Family assignment
                update_query = """
                UPDATE titles 
                SET event_family_id = :event_family_id,
                    ef_assignment_confidence = :confidence,
                    ef_assignment_reason = :reason,
                    ef_assignment_at = NOW()
                WHERE id = ANY(:title_ids)
                AND gate_keep = true 
                AND event_family_id IS NULL
                """
                
                result = session.execute(
                    text(update_query),
                    {
                        "event_family_id": event_family_id,
                        "confidence": confidence,
                        "reason": reason,
                        "title_ids": title_ids,
                    }
                )
                
                updated_count = result.rowcount
                logger.info(
                    f"Assigned {updated_count} titles to Event Family {event_family_id}",
                    confidence=confidence,
                    reason=reason[:100],
                )
                
                return updated_count > 0
                
        except Exception as e:
            logger.error(f"Failed to assign titles to Event Family: {e}")
            return False

    def _get_bucket_titles(self, session, bucket_id: str) -> List[Dict[str, Any]]:
        """Get titles associated with a bucket"""
        try:
            title_query = """
            SELECT 
                t.id,
                t.title_display as text,
                t.url_gnews as url,
                t.publisher_name as source_name,
                t.pubdate_utc,
                t.lang as lang_code,
                t.gate_keep,
                t.entities as extracted_actors,
                t.entities as extracted_taxonomy
            FROM titles t
            JOIN bucket_members bm ON t.id = bm.title_id
            WHERE bm.bucket_id = :bucket_id
            ORDER BY t.pubdate_utc DESC
            """

            title_results = session.execute(text(title_query), {"bucket_id": bucket_id}).fetchall()

            titles = []
            for title_row in title_results:
                title_dict = {
                    "id": str(title_row.id),
                    "text": title_row.text,
                    "url": title_row.url,
                    "source": title_row.source_name,
                    "pubdate_utc": title_row.pubdate_utc,
                    "language": title_row.lang_code,
                    "strategic": title_row.gate_keep,
                    "actors": title_row.extracted_actors or [],
                    "taxonomy": title_row.extracted_taxonomy or [],
                }
                titles.append(title_dict)

            return titles

        except Exception as e:
            logger.error(f"Failed to get bucket titles: {e}")
            return []

    async def save_event_family(self, event_family: EventFamily) -> bool:
        """
        Save an Event Family to the database
        
        Args:
            event_family: EventFamily object to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                # Insert into event_families table
                insert_query = """
                INSERT INTO event_families (
                    id, title, summary, key_actors, event_type, geography,
                    event_start, event_end, source_bucket_ids, source_title_ids,
                    confidence_score, coherence_reason, created_at, updated_at,
                    processing_notes
                ) VALUES (
                    :id, :title, :summary, :key_actors, :event_type, :geography,
                    :event_start, :event_end, :source_bucket_ids, :source_title_ids,
                    :confidence_score, :coherence_reason, :created_at, :updated_at,
                    :processing_notes
                )
                """

                session.execute(
                    text(insert_query),
                    {
                        "id": event_family.id,
                        "title": event_family.title,
                        "summary": event_family.summary,
                        "key_actors": event_family.key_actors,
                        "event_type": event_family.event_type,
                        "geography": event_family.geography,
                        "event_start": event_family.event_start,
                        "event_end": event_family.event_end,
                        "source_bucket_ids": event_family.source_bucket_ids,
                        "source_title_ids": event_family.source_title_ids,
                        "confidence_score": event_family.confidence_score,
                        "coherence_reason": event_family.coherence_reason,
                        "created_at": event_family.created_at,
                        "updated_at": event_family.updated_at,
                        "processing_notes": event_family.processing_notes,
                    },
                )

                logger.debug(f"Saved Event Family: {event_family.id} - {event_family.title}")
                return True

        except Exception as e:
            logger.error(f"Failed to save Event Family: {e}")
            return False

    async def save_framed_narrative(self, framed_narrative: FramedNarrative) -> bool:
        """
        Save a Framed Narrative to the database
        
        Args:
            framed_narrative: FramedNarrative object to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                # Insert into framed_narratives table
                insert_query = """
                INSERT INTO framed_narratives (
                    id, event_family_id, frame_type, frame_description, stance_summary,
                    supporting_headlines, supporting_title_ids, key_language,
                    prevalence_score, evidence_quality, created_at, updated_at
                ) VALUES (
                    :id, :event_family_id, :frame_type, :frame_description, :stance_summary,
                    :supporting_headlines, :supporting_title_ids, :key_language,
                    :prevalence_score, :evidence_quality, :created_at, :updated_at
                )
                """

                session.execute(
                    text(insert_query),
                    {
                        "id": framed_narrative.id,
                        "event_family_id": framed_narrative.event_family_id,
                        "frame_type": framed_narrative.frame_type,
                        "frame_description": framed_narrative.frame_description,
                        "stance_summary": framed_narrative.stance_summary,
                        "supporting_headlines": framed_narrative.supporting_headlines,
                        "supporting_title_ids": framed_narrative.supporting_title_ids,
                        "key_language": framed_narrative.key_language,
                        "prevalence_score": framed_narrative.prevalence_score,
                        "evidence_quality": framed_narrative.evidence_quality,
                        "created_at": framed_narrative.created_at,
                        "updated_at": framed_narrative.updated_at,
                    },
                )

                logger.debug(
                    f"Saved Framed Narrative: {framed_narrative.id} - {framed_narrative.frame_type}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to save Framed Narrative: {e}")
            return False

    async def get_event_families(
        self,
        since_hours: Optional[int] = None,
        limit: Optional[int] = None,
        include_narratives: bool = False,
    ) -> List[EventFamily]:
        """
        Retrieve Event Families from the database
        
        Args:
            since_hours: How far back to look for Event Families
            limit: Maximum number to return
            include_narratives: Whether to include associated Framed Narratives
            
        Returns:
            List of EventFamily objects
        """
        try:
            with get_db_session() as session:
                query = "SELECT * FROM event_families"
                params = []

                # Add time filter if specified
                if since_hours:
                    query += " WHERE created_at >= NOW() - INTERVAL :since_hours HOUR"
                    params.append(since_hours)

                query += " ORDER BY created_at DESC"

                # Add limit if specified
                if limit:
                    query += f" LIMIT {limit}"

                results = session.execute(text(query), params).fetchall()

                event_families = []
                for row in results:
                    ef = EventFamily(
                        id=str(row.id),
                        title=row.title,
                        summary=row.summary,
                        key_actors=row.key_actors or [],
                        event_type=row.event_type,
                        geography=row.geography,
                        event_start=row.event_start,
                        event_end=row.event_end,
                        source_bucket_ids=row.source_bucket_ids or [],
                        source_title_ids=row.source_title_ids or [],
                        confidence_score=row.confidence_score,
                        coherence_reason=row.coherence_reason,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        processing_notes=row.processing_notes,
                    )
                    event_families.append(ef)

                logger.info(f"Retrieved {len(event_families)} Event Families")
                return event_families

        except Exception as e:
            logger.error(f"Failed to get Event Families: {e}")
            return []

    async def get_framed_narratives_for_event(
        self, event_family_id: str
    ) -> List[FramedNarrative]:
        """
        Get all Framed Narratives for a specific Event Family
        
        Args:
            event_family_id: ID of the Event Family
            
        Returns:
            List of FramedNarrative objects
        """
        try:
            with get_db_session() as session:
                query = """
                SELECT * FROM framed_narratives 
                WHERE event_family_id = %s 
                ORDER BY prevalence_score DESC
                """

                results = session.execute(text(query), (event_family_id,)).fetchall()

                narratives = []
                for row in results:
                    fn = FramedNarrative(
                        id=str(row.id),
                        event_family_id=str(row.event_family_id),
                        frame_type=row.frame_type,
                        frame_description=row.frame_description,
                        stance_summary=row.stance_summary,
                        supporting_headlines=row.supporting_headlines or [],
                        supporting_title_ids=row.supporting_title_ids or [],
                        key_language=row.key_language or [],
                        prevalence_score=row.prevalence_score,
                        evidence_quality=row.evidence_quality,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                    )
                    narratives.append(fn)

                return narratives

        except Exception as e:
            logger.error(f"Failed to get Framed Narratives: {e}")
            return []

    async def check_existing_event_family(
        self, title_ids: List[str], similarity_threshold: float = 0.7
    ) -> Optional[EventFamily]:
        """
        Check if an Event Family with similar title composition already exists
        
        Args:
            title_ids: List of title IDs to check against
            similarity_threshold: Minimum similarity score to consider a match
            
        Returns:
            Existing EventFamily if found, None otherwise
        """
        try:
            # This would implement sophisticated similarity checking
            # For now, return None to always create new Event Families
            return None

        except Exception as e:
            logger.error(f"Failed to check existing Event Family: {e}")
            return None

    async def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get GEN-1 processing statistics
        
        Returns:
            Dictionary with processing metrics
        """
        try:
            with get_db_session() as session:
                stats = {}

                # Count Event Families
                ef_count = session.execute(
                    text("SELECT COUNT(*) FROM event_families")
                ).scalar()
                stats["event_families_total"] = ef_count

                # Count Framed Narratives
                fn_count = session.execute(
                    text("SELECT COUNT(*) FROM framed_narratives")
                ).scalar()
                stats["framed_narratives_total"] = fn_count

                # Recent processing (last 24 hours)
                ef_recent = session.execute(
                    text(
                        "SELECT COUNT(*) FROM event_families WHERE created_at >= NOW() - INTERVAL '24 hours'"
                    )
                ).scalar()
                stats["event_families_24h"] = ef_recent

                fn_recent = session.execute(
                    text(
                        "SELECT COUNT(*) FROM framed_narratives WHERE created_at >= NOW() - INTERVAL '24 hours'"
                    )
                ).scalar()
                stats["framed_narratives_24h"] = fn_recent

                # Average confidence scores
                avg_confidence = session.execute(
                    text("SELECT AVG(confidence_score) FROM event_families")
                ).scalar()
                stats["avg_confidence_score"] = float(avg_confidence or 0)

                return stats

        except Exception as e:
            logger.error(f"Failed to get processing stats: {e}")
            return {}


# Global database instance
_gen1_db: Optional[Gen1Database] = None


def get_gen1_database() -> Gen1Database:
    """Get global GEN-1 database instance"""
    global _gen1_db
    if _gen1_db is None:
        _gen1_db = Gen1Database()
    return _gen1_db
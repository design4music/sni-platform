"""
GEN-1 Database Operations
Database interactions for Event Families and Framed Narratives
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import text

from apps.generate.models import EventFamily, FramedNarrative
from core.database import get_db_session


class Gen1Database:
    """
    Database operations for GEN-1 Event Family assembly and Framed Narrative generation
    Handles direct title processing and writing Event Families/Framed Narratives
    """

    def __init__(self):
        pass

    def get_unassigned_strategic_titles(
        self,
        limit: Optional[int] = None,
        order_by: str = "newest_first",
    ) -> List[Dict[str, Any]]:
        """
        Retrieve ALL unassigned strategic titles for direct EF processing (Phase 2)
        Simplified approach: process all titles where event_family_id IS NULL

        Args:
            limit: Maximum number of titles to return (None for all titles)
            order_by: Ordering strategy ('newest_first', 'oldest_first')

        Returns:
            List of strategic title dictionaries ready for GEN-1 processing
        """
        try:
            with get_db_session() as session:
                # Simple query for ALL unassigned strategic titles (corpus-wide)
                # MULTILINGUAL: Process all languages - system supports multilingual content
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
                results = session.execute(text(titles_query)).fetchall()

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
                        "actors": row.extracted_actors or [],  # Legacy field
                        "entities": row.extracted_actors,  # Proper entities field for batcher
                        "created_at": row.created_at,
                    }
                    titles.append(title_dict)

                logger.info(
                    f"Retrieved {len(titles)} unassigned strategic titles (corpus-wide)",
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
    ) -> int:
        """
        Assign titles to an Event Family (Phase 2)

        Args:
            title_ids: List of title IDs to assign
            event_family_id: Event Family ID to assign them to
            confidence: LLM confidence in the assignment
            reason: Reason for assignment

        Returns:
            Number of titles successfully assigned
        """
        try:
            with get_db_session() as session:
                # Update titles with Event Family assignment
                # Cast UUIDs properly for PostgreSQL
                if not title_ids:
                    return 0

                # Convert title_ids to proper UUID format for PostgreSQL
                uuid_list = (
                    "ARRAY["
                    + ",".join([f"'{title_id}'::uuid" for title_id in title_ids])
                    + "]"
                )

                update_query = f"""
                UPDATE titles 
                SET event_family_id = :event_family_id,
                    ef_assignment_confidence = :confidence,
                    ef_assignment_reason = :reason,
                    ef_assignment_at = NOW()
                WHERE id = ANY({uuid_list})
                AND gate_keep = true 
                AND event_family_id IS NULL
                """

                # Build parameters
                params = {
                    "event_family_id": event_family_id,
                    "confidence": confidence,
                    "reason": reason,
                }

                result = session.execute(text(update_query), params)

                updated_count = result.rowcount
                logger.info(
                    f"Assigned {updated_count} titles to Event Family {event_family_id}",
                    confidence=confidence,
                    reason=reason[:100],
                )

                return updated_count

        except Exception as e:
            logger.error(f"Failed to assign titles to Event Family: {e}")
            return 0

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
                # Insert into event_families table (Phase 2: Updated schema with ef_key system)
                insert_query = """
                INSERT INTO event_families (
                    id, title, summary, key_actors, event_type, primary_theater,
                    ef_key, status, merged_into, merge_rationale,
                    source_title_ids, confidence_score, coherence_reason, created_at, updated_at,
                    processing_notes, events
                ) VALUES (
                    :id, :title, :summary, :key_actors, :event_type, :primary_theater,
                    :ef_key, :status, :merged_into, :merge_rationale,
                    :source_title_ids, :confidence_score, :coherence_reason, :created_at, :updated_at,
                    :processing_notes, :events
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
                        "primary_theater": event_family.primary_theater,
                        "ef_key": event_family.ef_key,
                        "status": event_family.status,
                        "merged_into": event_family.merged_into,
                        "merge_rationale": event_family.merge_rationale,
                        "source_title_ids": event_family.source_title_ids,
                        "confidence_score": event_family.confidence_score,
                        "coherence_reason": event_family.coherence_reason,
                        "created_at": event_family.created_at,
                        "updated_at": event_family.updated_at,
                        "processing_notes": event_family.processing_notes,
                        "events": json.dumps(event_family.events),
                    },
                )

                logger.debug(
                    f"Saved Event Family: {event_family.id} - {event_family.title}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to save Event Family: {e}")
            return False

    async def upsert_event_family_by_ef_key(
        self, event_family: EventFamily
    ) -> tuple[bool, Optional[str]]:
        """
        Upsert Event Family using ef_key for continuous merging

        Args:
            event_family: EventFamily object to save or merge

        Returns:
            Tuple of (success: bool, existing_ef_id: Optional[str])
            - If existing_ef_id is None, new EF was created
            - If existing_ef_id is provided, merge with existing EF
        """
        try:
            with get_db_session() as session:
                if not event_family.ef_key:
                    # No ef_key, use regular save
                    success = await self.save_event_family(event_family)
                    return success, None

                # Check if EF with same ef_key already exists
                existing_query = """
                SELECT id, title, source_title_ids, key_actors
                FROM event_families 
                WHERE ef_key = :ef_key AND status IN ('seed', 'active')
                LIMIT 1
                """

                result = session.execute(
                    text(existing_query), {"ef_key": event_family.ef_key}
                ).fetchone()

                if result:
                    # EF with same ef_key exists - merge titles into existing EF
                    existing_ef_id = str(result.id)
                    existing_title_ids = result.source_title_ids or []
                    new_title_ids = event_family.source_title_ids or []

                    # Merge title lists (deduplicate)
                    merged_title_ids = list(set(existing_title_ids + new_title_ids))

                    # Update existing EF with merged titles and extended time range
                    update_query = """
                    UPDATE event_families 
                    SET source_title_ids = :merged_title_ids,
                        updated_at = NOW(),
                        updated_at = NOW(),
                        processing_notes = CONCAT(COALESCE(processing_notes, ''), '; Merged ef_key: ', :new_ef_title)
                    WHERE id = :existing_ef_id
                    """

                    session.execute(
                        text(update_query),
                        {
                            "merged_title_ids": merged_title_ids,
                            # Removed event_start/event_end fields
                            "new_ef_title": event_family.title[
                                :100
                            ],  # Truncate for notes
                            "existing_ef_id": existing_ef_id,
                        },
                    )

                    logger.info(
                        f"Merged EF with ef_key {event_family.ef_key}: "
                        f"{len(new_title_ids)} new titles into existing EF {existing_ef_id}"
                    )

                    return True, existing_ef_id
                else:
                    # No existing EF, create new one
                    success = await self.save_event_family(event_family)
                    return success, None

        except Exception as e:
            logger.error(f"Failed to upsert Event Family by ef_key: {e}")
            return False, None

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
                        source_title_ids=row.source_title_ids or [],
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

                # Active event families count
                active_count = session.execute(
                    text("SELECT COUNT(*) FROM event_families WHERE status = 'active'")
                ).scalar()
                stats["active_event_families"] = int(active_count or 0)

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

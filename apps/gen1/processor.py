"""
GEN-1 Event Family Processor
Core orchestration logic for Event Family assembly and Framed Narrative generation
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

from apps.gen1.database import get_gen1_database
from apps.gen1.llm_client import get_gen1_llm_client
from apps.gen1.models import (
    BucketContext,
    EventFamily,
    FramedNarrative,
    LLMEventFamilyRequest,
    LLMEventFamilyResponse,
    LLMFramedNarrativeRequest,
    LLMFramedNarrativeResponse,
    ProcessingResult,
)
from apps.gen1.validation import get_gen1_validator
from core.config import get_config


class Gen1Processor:
    """
    Core GEN-1 processor for Event Family assembly and Framed Narrative generation
    
    Orchestrates the complete pipeline:
    1. Load CLUST-2 buckets as processing hints
    2. Use LLM to assemble Event Families with cross-bucket intelligence
    3. Generate Framed Narratives for each Event Family
    4. Save results to database with quality tracking
    """

    def __init__(self):
        self.config = get_config()
        self.db = get_gen1_database()
        self.llm = get_gen1_llm_client()
        self.validator = get_gen1_validator()

        # Processing configuration
        self.max_buckets_per_batch = 10
        self.max_event_families_per_batch = 8
        self.max_narratives_per_event = 3

    async def process_strategic_titles(
        self,
        since_hours: int = 72,
        max_titles: Optional[int] = None,
        batch_size: int = 50,
        dry_run: bool = False,
    ) -> ProcessingResult:
        """
        Phase 2: Direct title→EF processing (bucketless architecture)
        
        Args:
            since_hours: How far back to look for unassigned strategic titles
            max_titles: Maximum titles to process (None for all)
            batch_size: Number of titles to process per LLM call
            dry_run: If True, don't save results to database
            
        Returns:
            ProcessingResult with metrics and artifacts
        """
        start_time = datetime.now()
        logger.info(
            f"Starting GEN-1 Direct Title Processing (Phase 2)",
            since_hours=since_hours,
            max_titles=max_titles,
            batch_size=batch_size,
            dry_run=dry_run,
        )

        try:
            # Phase 1: Load unassigned strategic titles
            titles = self.db.get_unassigned_strategic_titles(
                since_hours=since_hours,
                limit=max_titles,
                order_by="newest_first",
            )

            if not titles:
                logger.warning("No unassigned strategic titles found for processing")
                return ProcessingResult(
                    processed_buckets=[],
                    total_titles_processed=0,
                    event_families=[],
                    framed_narratives=[],
                    success_rate=0.0,
                    processing_time_seconds=0.0,
                    errors=["No unassigned strategic titles found"],
                    warnings=[],
                )

            logger.info(f"Found {len(titles)} unassigned strategic titles for processing")

            # Phase 2: Group titles into batches for LLM processing
            title_batches = []
            for i in range(0, len(titles), batch_size):
                batch = titles[i : i + batch_size]
                title_batches.append(batch)

            logger.info(f"Created {len(title_batches)} title batches for processing")

            # Phase 3: Process each batch through LLM
            all_event_families = []
            all_framed_narratives = []
            processing_errors = []
            processing_warnings = []

            for batch_idx, title_batch in enumerate(title_batches):
                logger.info(f"Processing title batch {batch_idx + 1}/{len(title_batches)} ({len(title_batch)} titles)")

                try:
                    # Create Event Families from title batch
                    ef_result = await self._process_title_batch_to_event_families(title_batch)
                    
                    if ef_result.event_families:
                        # Save Event Families and assign titles
                        for ef_data in ef_result.event_families:
                            event_family = await self._create_event_family_from_data(ef_data)
                            if event_family:
                                all_event_families.append(event_family)
                                
                                # Assign titles to this Event Family
                                if not dry_run:
                                    await self.db.assign_titles_to_event_family(
                                        title_ids=ef_data.get("source_title_ids", []),
                                        event_family_id=event_family.id,
                                        confidence=ef_data.get("confidence_score", 0.5),
                                        reason=ef_data.get("coherence_reason", "Direct title assignment"),
                                    )

                                # Generate Framed Narratives for this Event Family
                                fn_titles = [t for t in title_batch if str(t["id"]) in ef_data.get("source_title_ids", [])]
                                fn_result = await self._process_event_family_to_framed_narratives(event_family, fn_titles)
                                
                                if fn_result.framed_narratives:
                                    for fn_data in fn_result.framed_narratives:
                                        framed_narrative = await self._create_framed_narrative_from_data(fn_data, event_family.id)
                                        if framed_narrative:
                                            all_framed_narratives.append(framed_narrative)

                    processing_warnings.extend(ef_result.warnings)

                except Exception as e:
                    error_msg = f"Batch {batch_idx + 1} failed: {e}"
                    logger.error(error_msg)
                    processing_errors.append(error_msg)

            # Calculate final metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            total_processed = len([t for batch in title_batches for t in batch])
            success_rate = len(all_event_families) / len(title_batches) if title_batches else 0.0

            logger.info(
                f"GEN-1 Direct Title Processing completed",
                event_families=len(all_event_families),
                framed_narratives=len(all_framed_narratives),
                titles_processed=total_processed,
                success_rate=f"{success_rate:.1%}",
                processing_time=f"{processing_time:.1f}s",
            )

            return ProcessingResult(
                processed_buckets=[f"title_batch_{i}" for i in range(len(title_batches))],
                total_titles_processed=total_processed,
                event_families=all_event_families,
                framed_narratives=all_framed_narratives,
                success_rate=success_rate,
                processing_time_seconds=processing_time,
                errors=processing_errors,
                warnings=processing_warnings,
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"GEN-1 Direct Title Processing failed: {e}")
            return ProcessingResult(
                processed_buckets=[],
                total_titles_processed=0,
                event_families=[],
                framed_narratives=[],
                success_rate=0.0,
                processing_time_seconds=processing_time,
                errors=[f"Processing failed: {e}"],
                warnings=[],
            )

    async def process_event_families(
        self,
        since_hours: int = 72,
        min_bucket_size: int = 2,
        max_buckets: Optional[int] = None,
        dry_run: bool = False,
    ) -> ProcessingResult:
        """
        Main processing pipeline for Event Family assembly
        
        Args:
            since_hours: How far back to look for buckets
            min_bucket_size: Minimum titles per bucket to process
            max_buckets: Maximum buckets to process (None for all)
            dry_run: If True, don't save results to database
            
        Returns:
            ProcessingResult with metrics and artifacts
        """
        start_time = datetime.now()
        logger.info(
            f"Starting GEN-1 Event Family processing",
            since_hours=since_hours,
            min_size=min_bucket_size,
            max_buckets=max_buckets,
            dry_run=dry_run,
        )

        try:
            # Phase 1: Load CLUST-2 buckets for processing
            buckets = self.db.get_active_buckets(
                since_hours=since_hours,
                min_bucket_size=min_bucket_size,
                limit=max_buckets,
                order_by="newest_first",
            )

            if not buckets:
                logger.warning("No active buckets found for processing")
                return ProcessingResult(
                    processed_buckets=[],
                    total_titles_processed=0,
                    event_families=[],
                    framed_narratives=[],
                    success_rate=1.0,
                    processing_time_seconds=0,
                    errors=[],
                    warnings=["No buckets available for processing"],
                )

            logger.info(f"Loaded {len(buckets)} buckets for processing")

            # Phase 2: Batch process buckets into Event Families
            event_families = []
            processed_bucket_ids = []
            total_titles = sum(bucket.title_count for bucket in buckets)
            errors = []
            warnings = []

            # Process buckets in batches to manage LLM context limits
            for i in range(0, len(buckets), self.max_buckets_per_batch):
                batch_buckets = buckets[i : i + self.max_buckets_per_batch]
                
                try:
                    batch_efs = await self._process_bucket_batch(batch_buckets)
                    event_families.extend(batch_efs)
                    processed_bucket_ids.extend([b.bucket_id for b in batch_buckets])
                    
                    logger.info(
                        f"Batch {i//self.max_buckets_per_batch + 1} completed: "
                        f"{len(batch_efs)} Event Families from {len(batch_buckets)} buckets"
                    )
                    
                except Exception as e:
                    error_msg = f"Batch processing failed: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Phase 3: Generate Framed Narratives for Event Families
            framed_narratives = []
            for event_family in event_families:
                try:
                    narratives = await self._generate_framed_narratives(event_family)
                    framed_narratives.extend(narratives)
                except Exception as e:
                    error_msg = f"Narrative generation failed for EF {event_family.id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Phase 4: Validate results
            validation_result = self.validator.validate_processing_result(
                event_families, framed_narratives
            )
            
            if validation_result["overall"]["quality_score"] < 0.5:
                warnings.append(f"Low quality score: {validation_result['overall']['quality_score']:.2f}")
            
            # Phase 5: Save results to database (unless dry run)
            if not dry_run:
                await self._save_results(event_families, framed_narratives)

            # Calculate metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            success_rate = (len(event_families) / len(buckets)) if buckets else 1.0

            result = ProcessingResult(
                processed_buckets=processed_bucket_ids,
                total_titles_processed=total_titles,
                event_families=event_families,
                framed_narratives=framed_narratives,
                success_rate=success_rate,
                processing_time_seconds=processing_time,
                errors=errors,
                warnings=warnings,
            )

            logger.info(f"GEN-1 processing completed: {result.summary}")
            return result

        except Exception as e:
            logger.error(f"GEN-1 processing failed: {e}")
            raise

    async def _process_bucket_batch(
        self, buckets: List[BucketContext]
    ) -> List[EventFamily]:
        """
        Process a batch of buckets into Event Families using LLM
        
        Args:
            buckets: List of bucket contexts to process
            
        Returns:
            List of assembled Event Families
        """
        try:
            # Build LLM request with processing instructions
            request = LLMEventFamilyRequest(
                buckets=buckets,
                processing_instructions=self._get_event_family_instructions(),
                max_event_families=self.max_event_families_per_batch,
            )

            # Call LLM for Event Family assembly
            response = await self.llm.assemble_event_families(request)

            # Convert LLM response to EventFamily objects
            event_families = []
            for ef_data in response.event_families:
                event_family = await self._create_event_family_from_llm(ef_data, buckets)
                event_families.append(event_family)

            logger.debug(
                f"LLM assembled {len(event_families)} Event Families from {len(buckets)} buckets"
            )

            return event_families

        except Exception as e:
            logger.error(f"Bucket batch processing failed: {e}")
            return []

    async def _generate_framed_narratives(
        self, event_family: EventFamily
    ) -> List[FramedNarrative]:
        """
        Generate Framed Narratives for an Event Family using LLM
        
        Args:
            event_family: Event Family to analyze for framing
            
        Returns:
            List of Framed Narratives
        """
        try:
            # Get title contexts for this Event Family
            titles_context = await self._get_titles_context(event_family.source_title_ids)

            if not titles_context:
                logger.warning(f"No title context found for Event Family {event_family.id}")
                return []

            # Build LLM request for Framed Narrative generation
            request = LLMFramedNarrativeRequest(
                event_family=event_family,
                titles_context=titles_context,
                framing_instructions=self._get_framed_narrative_instructions(),
                max_narratives=self.max_narratives_per_event,
            )

            # Call LLM for Framed Narrative analysis
            response = await self.llm.generate_framed_narratives(request)

            # Convert LLM response to FramedNarrative objects
            framed_narratives = []
            for fn_data in response.framed_narratives:
                framed_narrative = await self._create_framed_narrative_from_llm(
                    fn_data, event_family.id
                )
                framed_narratives.append(framed_narrative)

            logger.debug(
                f"Generated {len(framed_narratives)} Framed Narratives for Event Family {event_family.id}"
            )

            return framed_narratives

        except Exception as e:
            logger.error(f"Framed Narrative generation failed: {e}")
            return []

    async def _process_title_batch_to_event_families(
        self, title_batch: List[Dict[str, Any]]
    ) -> LLMEventFamilyResponse:
        """
        Process a batch of titles directly into Event Families (Phase 2)
        """
        try:
            # Create direct title processing instructions
            instructions = """
            Create Event Families from these strategic news titles. Focus on ongoing narrative themes 
            rather than discrete events. Group titles that share strategic actors, contexts, or themes.
            Apply strategic filtering - exclude non-strategic content like sports, entertainment, etc.
            """
            
            # Create title request (no buckets)
            request = LLMEventFamilyRequest(
                buckets=[],  # Phase 2: No buckets
                processing_instructions=instructions,
                max_event_families=self.max_event_families_per_batch,
            )
            
            # Add titles as direct context in request
            request.title_context = title_batch
            
            # Call LLM with direct title processing
            return await self.llm_client.assemble_event_families_from_titles(request)
            
        except Exception as e:
            logger.error(f"Title batch to Event Families failed: {e}")
            return LLMEventFamilyResponse(
                event_families=[],
                processing_reasoning=f"Processing failed: {e}",
                confidence=0.0,
                warnings=[f"Title batch processing error: {e}"],
            )

    async def _process_event_family_to_framed_narratives(
        self, event_family: EventFamily, titles_context: List[Dict[str, Any]]
    ) -> LLMFramedNarrativeResponse:
        """
        Generate Framed Narratives for an Event Family using direct titles (Phase 2)
        """
        try:
            instructions = """
            Analyze how different outlets frame this Event Family. Identify distinct framing approaches
            with strict evidence requirements - every claim must be supported by exact headline quotes.
            Focus on evaluative/causal differences in how the same strategic narrative is presented.
            """
            
            request = LLMFramedNarrativeRequest(
                event_family=event_family,
                titles_context=titles_context,
                framing_instructions=instructions,
                max_narratives=self.max_narratives_per_event,
            )
            
            return await self.llm_client.generate_framed_narratives(request)
            
        except Exception as e:
            logger.error(f"Event Family to Framed Narratives failed: {e}")
            return LLMFramedNarrativeResponse(
                framed_narratives=[],
                processing_reasoning=f"Processing failed: {e}",
                confidence=0.0,
                dominant_frames=[],
            )

    async def _create_event_family_from_data(self, ef_data: Dict[str, Any]) -> EventFamily:
        """
        Create EventFamily from LLM response data (Phase 2 version)
        """
        try:
            # Parse timestamps with better error handling
            event_start = datetime.now()
            if ef_data.get("event_start"):
                try:
                    event_start = datetime.fromisoformat(ef_data["event_start"].replace("Z", "+00:00"))
                except:
                    # Fallback to current time if parsing fails
                    event_start = datetime.now()
            
            event_end = None
            if ef_data.get("event_end"):
                try:
                    event_end = datetime.fromisoformat(ef_data["event_end"].replace("Z", "+00:00"))
                except:
                    event_end = None

            event_family = EventFamily(
                title=ef_data["title"],
                summary=ef_data["summary"],
                key_actors=ef_data.get("key_actors", []),
                event_type=ef_data["event_type"],
                geography=ef_data.get("geography"),
                event_start=event_start,
                event_end=event_end,
                source_bucket_ids=[],  # Phase 2: No buckets
                source_title_ids=[str(tid) for tid in ef_data.get("source_title_ids", [])],
                confidence_score=ef_data.get("confidence_score", 0.5),
                coherence_reason=ef_data["coherence_reason"],
            )
            
            # Save to database
            if await self.db.save_event_family(event_family):
                logger.debug(f"Created Event Family: {event_family.title}")
                return event_family
            else:
                logger.error(f"Failed to save Event Family: {event_family.title}")
                return None
                
        except Exception as e:
            logger.error(f"Event Family creation failed: {e}")
            return None

    async def _create_framed_narrative_from_data(
        self, fn_data: Dict[str, Any], event_family_id: str
    ) -> FramedNarrative:
        """
        Create FramedNarrative from LLM response data (Phase 2 version)
        """
        try:
            framed_narrative = FramedNarrative(
                event_family_id=event_family_id,
                frame_type=fn_data["frame_type"],
                frame_description=fn_data["frame_description"],
                stance_summary=fn_data["stance_summary"],
                supporting_headlines=fn_data.get("supporting_headlines", []),
                supporting_title_ids=[str(tid) for tid in fn_data.get("supporting_title_ids", [])],
                key_language=fn_data.get("key_language", []),
                prevalence_score=fn_data.get("prevalence_score", 0.5),
                evidence_quality=fn_data.get("evidence_quality", 0.5),
            )
            
            # Save to database
            if await self.db.save_framed_narrative(framed_narrative):
                logger.debug(f"Created Framed Narrative: {framed_narrative.frame_type}")
                return framed_narrative
            else:
                logger.error(f"Failed to save Framed Narrative: {framed_narrative.frame_type}")
                return None
                
        except Exception as e:
            logger.error(f"Framed Narrative creation failed: {e}")
            return None

    async def _create_event_family_from_llm(
        self, ef_data: Dict[str, Any], buckets: List[BucketContext]
    ) -> EventFamily:
        """Convert LLM response data to EventFamily object"""
        
        # Parse timestamps
        event_start = datetime.fromisoformat(ef_data["event_start"].replace("Z", "+00:00"))
        event_end = None
        if ef_data.get("event_end"):
            event_end = datetime.fromisoformat(ef_data["event_end"].replace("Z", "+00:00"))

        return EventFamily(
            title=ef_data["title"],
            summary=ef_data["summary"],
            key_actors=ef_data.get("key_actors", []),
            event_type=ef_data["event_type"],
            geography=ef_data.get("geography"),
            event_start=event_start,
            event_end=event_end,
            source_bucket_ids=[str(bid) for bid in ef_data.get("source_bucket_ids", [])],
            source_title_ids=[str(tid) for tid in ef_data.get("source_title_ids", [])],
            confidence_score=ef_data.get("confidence_score", 0.5),
            coherence_reason=ef_data["coherence_reason"],
        )

    async def _create_framed_narrative_from_llm(
        self, fn_data: Dict[str, Any], event_family_id: str
    ) -> FramedNarrative:
        """Convert LLM response data to FramedNarrative object"""
        
        return FramedNarrative(
            event_family_id=event_family_id,
            frame_type=fn_data["frame_type"],
            frame_description=fn_data["frame_description"],
            stance_summary=fn_data["stance_summary"],
            supporting_headlines=fn_data.get("supporting_headlines", []),
            supporting_title_ids=[str(tid) for tid in fn_data.get("supporting_title_ids", [])],
            key_language=fn_data.get("key_language", []),
            prevalence_score=fn_data.get("prevalence_score", 0.5),
            evidence_quality=fn_data.get("evidence_quality", 0.5),
        )

    async def _get_titles_context(self, title_ids: List[str]) -> List[Dict[str, Any]]:
        """Get title contexts for Framed Narrative generation"""
        try:
            from core.database import get_db_session
            from sqlalchemy import text
            
            with get_db_session() as session:
                if not title_ids:
                    return []
                
                # Create parameterized query for title IDs
                placeholders = ','.join([f':title_id_{i}' for i in range(len(title_ids))])
                query = f"""
                SELECT 
                    id, title_display as text, url_gnews as url, publisher_name as source_name, pubdate_utc, 
                    lang as lang_code, entities as extracted_actors, entities as extracted_taxonomy
                FROM titles 
                WHERE id::text IN ({placeholders})
                ORDER BY pubdate_utc DESC
                """
                
                # Create parameter dictionary
                params = {f'title_id_{i}': title_id for i, title_id in enumerate(title_ids)}
                results = session.execute(text(query), params).fetchall()
                
                titles_context = []
                for row in results:
                    title_dict = {
                        "id": str(row.id),
                        "text": row.text,
                        "url": row.url,
                        "source": row.source_name,
                        "pubdate_utc": row.pubdate_utc,
                        "language": row.lang_code,
                        "actors": row.extracted_actors or [],
                        "taxonomy": row.extracted_taxonomy or [],
                    }
                    titles_context.append(title_dict)
                
                return titles_context
                
        except Exception as e:
            logger.error(f"Failed to get titles context: {e}")
            return []

    async def _save_results(
        self, event_families: List[EventFamily], framed_narratives: List[FramedNarrative]
    ):
        """Save Event Families and Framed Narratives to database"""
        try:
            # Save Event Families
            saved_efs = 0
            for ef in event_families:
                if await self.db.save_event_family(ef):
                    saved_efs += 1

            # Save Framed Narratives
            saved_fns = 0
            for fn in framed_narratives:
                if await self.db.save_framed_narrative(fn):
                    saved_fns += 1

            logger.info(
                f"Saved {saved_efs}/{len(event_families)} Event Families, "
                f"{saved_fns}/{len(framed_narratives)} Framed Narratives"
            )

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise

    def _get_event_family_instructions(self) -> str:
        """Get processing instructions for Event Family assembly"""
        return """
Analyze the provided buckets (grouped by actor sets) and identify coherent Event Families.

CRITICAL REQUIREMENTS:
1. Buckets are HINTS only - freely pull titles across buckets or exclude titles within buckets
2. Focus on "the same story" - does this feel like one coherent real-world happening?
3. Prefer fewer, stronger Event Families over many weak ones
4. Single-item Event Families allowed only with strong justification ("singular but strategic")
5. Consider temporal coherence, shared actors, and logical event progression

QUALITY CRITERIA:
- Clear concrete actors/entities involved
- Logical time boundaries (start/end if applicable)  
- Strong evidence from headline language
- Coherent event progression or single significant occurrence

CROSS-BUCKET INTELLIGENCE:
- Look for connections between different actor sets
- Identify larger events spanning multiple buckets
- Merge related stories into comprehensive Event Families
- Exclude outliers that don't fit coherent narratives
"""

    def _get_framed_narrative_instructions(self) -> str:
        """Get processing instructions for Framed Narrative generation"""
        return """
Analyze how different outlets frame this Event Family and identify distinct Framed Narratives.

CRITICAL REQUIREMENTS:
1. Must cite specific headline evidence for each narrative
2. State evaluative/causal framing clearly (supportive, critical, neutral, etc.)
3. Identify key language that signals the framing
4. Focus on how the SAME event is positioned differently
5. Typically 1-2 dominant framings per event

ANALYSIS DEPTH:
- Extract exact phrases that reveal framing stance
- Assess how prevalent each narrative is
- Rate the quality of supporting evidence
- Identify frame types (evaluative, causal, attribution, etc.)

NARRATIVE QUALITY:
- Each narrative must have clear supporting evidence
- Frame descriptions should be specific and actionable
- Stance summaries must be clear evaluative statements
- Key language should be precise and revealing
"""

    async def get_processing_summary(
        self, since_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get summary of recent GEN-1 processing activity
        
        Args:
            since_hours: Time window for summary
            
        Returns:
            Dictionary with processing summary
        """
        try:
            stats = await self.db.get_processing_stats()
            
            # Add configuration info
            stats["config"] = {
                "max_buckets_per_batch": self.max_buckets_per_batch,
                "max_event_families_per_batch": self.max_event_families_per_batch,
                "max_narratives_per_event": self.max_narratives_per_event,
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get processing summary: {e}")
            return {}


# Global processor instance
_gen1_processor: Optional[Gen1Processor] = None


def get_gen1_processor() -> Gen1Processor:
    """Get global GEN-1 processor instance"""
    global _gen1_processor
    if _gen1_processor is None:
        _gen1_processor = Gen1Processor()
    return _gen1_processor
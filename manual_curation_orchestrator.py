#!/usr/bin/env python3
"""
Manual Curation Workflow Orchestrator
Strategic Narrative Intelligence ETL Pipeline

Orchestrates the complete manual parent narrative curation workflow:
1. Trigger analysis and opportunity identification
2. Strategic parent narrative creation
3. Cluster grouping and child assignment
4. Editorial review workflow management
5. Publication and API integration

Designed for daily operation and integration with existing CLUST-1/CLUST-2 pipeline.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from curation_trigger_analyzer import CurationTriggerAnalyzer
from etl_pipeline.core.curation.manual_narrative_manager import \
    ManualNarrativeManager
from etl_pipeline.core.database import get_db_session

logger = structlog.get_logger(__name__)


class ManualCurationOrchestrator:
    """
    Orchestrates the complete manual curation workflow

    Workflow Stages:
    1. Daily Trigger Analysis - Identify consolidation opportunities
    2. Smart Grouping - Suggest optimal cluster combinations
    3. Assisted Creation - Guide strategic parent creation
    4. Review Management - Coordinate editorial workflow
    5. Publication Pipeline - Integrate with existing systems
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize orchestrator with core components"""
        self.session = session or get_db_session()
        self.logger = logger.bind(component="manual_curation_orchestrator")

        # Initialize core components
        self.trigger_analyzer = CurationTriggerAnalyzer(self.session)
        self.narrative_manager = ManualNarrativeManager(self.session)

        # Workflow configuration
        self.config = {
            "daily_analysis_days_back": 7,
            "max_triggers_per_day": 10,
            "auto_assignment_threshold": 0.8,
            "review_deadline_hours": {"high": 24, "medium": 48, "low": 72},
            "consolidation_ratio_target": 0.5,  # Target 0.5 parents per cluster
        }

    async def run_daily_curation_workflow(self) -> Dict[str, Any]:
        """
        Execute the complete daily curation workflow

        Returns:
            Comprehensive workflow execution report
        """
        workflow_start = datetime.now()
        self.logger.info("Starting daily curation workflow")

        workflow_results = {
            "workflow_id": str(uuid.uuid4()),
            "started_at": workflow_start.isoformat(),
            "status": "in_progress",
            "stages": {},
        }

        try:
            # Stage 1: Trigger Analysis
            self.logger.info("Stage 1: Analyzing consolidation triggers")
            trigger_results = await self._execute_trigger_analysis()
            workflow_results["stages"]["trigger_analysis"] = trigger_results

            if trigger_results["status"] != "success":
                workflow_results["status"] = "trigger_analysis_failed"
                return workflow_results

            # Stage 2: Smart Grouping Suggestions
            self.logger.info("Stage 2: Generating grouping suggestions")
            grouping_results = await self._execute_smart_grouping(
                trigger_results["triggers"]
            )
            workflow_results["stages"]["smart_grouping"] = grouping_results

            # Stage 3: Automated Parent Creation (high-confidence triggers only)
            self.logger.info("Stage 3: Creating high-confidence parent narratives")
            creation_results = await self._execute_automated_creation(
                grouping_results["high_confidence_groups"]
            )
            workflow_results["stages"]["automated_creation"] = creation_results

            # Stage 4: Review Queue Management
            self.logger.info("Stage 4: Managing review workflow")
            review_results = await self._execute_review_management()
            workflow_results["stages"]["review_management"] = review_results

            # Stage 5: Performance Analytics
            self.logger.info("Stage 5: Analyzing workflow performance")
            analytics_results = await self._execute_performance_analytics()
            workflow_results["stages"]["performance_analytics"] = analytics_results

            workflow_results["status"] = "completed"
            workflow_results["completed_at"] = datetime.now().isoformat()

            # Generate executive summary
            workflow_results["executive_summary"] = self._generate_executive_summary(
                workflow_results
            )

            self.logger.info(
                "Daily curation workflow completed successfully",
                triggers_identified=len(trigger_results.get("triggers", [])),
                parents_created=creation_results.get("parents_created", 0),
                review_items=len(review_results.get("pending_reviews", [])),
                duration_minutes=(datetime.now() - workflow_start).total_seconds() / 60,
            )

        except Exception as e:
            workflow_results["status"] = "failed"
            workflow_results["error"] = str(e)
            workflow_results["failed_at"] = datetime.now().isoformat()

            self.logger.error(
                "Daily curation workflow failed",
                error=str(e),
                duration_minutes=(datetime.now() - workflow_start).total_seconds() / 60,
            )

        return workflow_results

    async def _execute_trigger_analysis(self) -> Dict[str, Any]:
        """Execute trigger analysis stage"""
        try:
            # Analyze recent clustering for consolidation opportunities
            triggers = self.trigger_analyzer.analyze_daily_triggers(
                days_back=self.config["daily_analysis_days_back"]
            )

            # Generate comprehensive report
            report = self.trigger_analyzer.generate_trigger_report(triggers)

            # Limit triggers to manageable daily volume
            limited_triggers = triggers[: self.config["max_triggers_per_day"]]

            return {
                "status": "success",
                "triggers": limited_triggers,
                "full_report": report,
                "trigger_count": len(triggers),
                "daily_limit_applied": len(triggers)
                > self.config["max_triggers_per_day"],
            }

        except Exception as e:
            self.logger.error("Trigger analysis stage failed", error=str(e))
            return {"status": "failed", "error": str(e), "triggers": []}

    async def _execute_smart_grouping(
        self, triggers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute smart grouping stage"""
        try:
            grouping_suggestions = []
            high_confidence_groups = []

            for trigger in triggers:
                # Analyze cluster grouping potential
                grouping = await self._analyze_cluster_grouping(trigger)
                grouping_suggestions.append(grouping)

                # Identify high-confidence groups for automation
                if (
                    grouping.get("confidence_score", 0)
                    >= self.config["auto_assignment_threshold"]
                ):
                    high_confidence_groups.append(grouping)

            # Generate cross-trigger consolidation opportunities
            cross_trigger_groups = await self._identify_cross_trigger_consolidations(
                triggers
            )

            return {
                "status": "success",
                "individual_groupings": grouping_suggestions,
                "high_confidence_groups": high_confidence_groups,
                "cross_trigger_groups": cross_trigger_groups,
                "total_suggestions": len(grouping_suggestions),
                "auto_eligible": len(high_confidence_groups),
            }

        except Exception as e:
            self.logger.error("Smart grouping stage failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "individual_groupings": [],
                "high_confidence_groups": [],
                "cross_trigger_groups": [],
            }

    async def _execute_automated_creation(
        self, high_confidence_groups: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute automated parent narrative creation for high-confidence groups"""
        try:
            parents_created = 0
            creation_details = []

            for group in high_confidence_groups:
                try:
                    # Create strategic parent narrative
                    parent_result = await self._create_strategic_parent(group)

                    if parent_result["status"] == "success":
                        parents_created += 1
                        creation_details.append(parent_result)

                        self.logger.info(
                            "Auto-created strategic parent",
                            parent_uuid=parent_result["parent_uuid"],
                            cluster_count=len(group.get("cluster_ids", [])),
                            theme=group.get("theme", "unknown"),
                        )
                    else:
                        self.logger.warning(
                            "Auto-creation failed for group",
                            theme=group.get("theme"),
                            reason=parent_result.get("error"),
                        )

                except Exception as e:
                    self.logger.error(
                        "Failed to create parent for group",
                        theme=group.get("theme"),
                        error=str(e),
                    )

            return {
                "status": "success",
                "parents_created": parents_created,
                "creation_details": creation_details,
                "attempted_groups": len(high_confidence_groups),
            }

        except Exception as e:
            self.logger.error("Automated creation stage failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "parents_created": 0,
                "creation_details": [],
            }

    async def _execute_review_management(self) -> Dict[str, Any]:
        """Execute review workflow management"""
        try:
            # Get current review queue status
            pending_reviews = self.narrative_manager.get_pending_reviews()

            # Identify overdue items
            overdue_reviews = [
                review
                for review in pending_reviews
                if review.get("days_until_deadline", 0) < 0
            ]

            # Auto-assign reviewers based on workload and expertise
            assignment_results = await self._auto_assign_reviewers(pending_reviews)

            # Send notifications for urgent items
            notification_results = await self._send_review_notifications(
                overdue_reviews
            )

            return {
                "status": "success",
                "pending_reviews": pending_reviews,
                "overdue_count": len(overdue_reviews),
                "assignment_results": assignment_results,
                "notification_results": notification_results,
            }

        except Exception as e:
            self.logger.error("Review management stage failed", error=str(e))
            return {"status": "failed", "error": str(e), "pending_reviews": []}

    async def _execute_performance_analytics(self) -> Dict[str, Any]:
        """Execute workflow performance analytics"""
        try:
            # Calculate current consolidation metrics
            consolidation_metrics = await self._calculate_consolidation_metrics()

            # Analyze curator productivity
            curator_metrics = await self._analyze_curator_performance()

            # Review workflow efficiency
            review_metrics = await self._analyze_review_efficiency()

            # System health check
            system_health = self.narrative_manager.validate_curation_workflow()

            return {
                "status": "success",
                "consolidation_metrics": consolidation_metrics,
                "curator_metrics": curator_metrics,
                "review_metrics": review_metrics,
                "system_health": system_health,
            }

        except Exception as e:
            self.logger.error("Performance analytics stage failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    async def _analyze_cluster_grouping(
        self, trigger: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze optimal cluster grouping for a trigger"""
        cluster_ids = trigger.get("cluster_ids", [])

        if len(cluster_ids) < 2:
            return {
                "trigger_id": trigger.get("rank", "unknown"),
                "confidence_score": 0.0,
                "grouping_viable": False,
                "reason": "Insufficient clusters for grouping",
            }

        # Analyze cluster compatibility
        compatibility_score = await self._calculate_cluster_compatibility(cluster_ids)

        # Generate strategic narrative suggestion
        narrative_suggestion = await self._generate_narrative_suggestion(
            trigger, cluster_ids
        )

        # Calculate overall confidence
        confidence_score = (
            trigger.get("priority_score", 0) * 0.4
            + compatibility_score * 0.3
            + narrative_suggestion.get("quality_score", 0) * 0.3
        )

        return {
            "trigger_id": trigger.get("rank", "unknown"),
            "theme": trigger.get("theme", trigger.get("primary_keyword", "unknown")),
            "cluster_ids": cluster_ids,
            "compatibility_score": compatibility_score,
            "narrative_suggestion": narrative_suggestion,
            "confidence_score": confidence_score,
            "grouping_viable": confidence_score >= 0.6,
            "estimated_effort": trigger.get("estimated_effort_hours", 2.0),
        }

    async def _calculate_cluster_compatibility(self, cluster_ids: List[str]) -> float:
        """Calculate compatibility score for cluster grouping"""
        try:
            # Get cluster details for compatibility analysis
            result = self.session.execute(
                text(
                    """
                    SELECT cluster_id, top_topics, size, created_at
                    FROM article_clusters 
                    WHERE cluster_id = ANY(:cluster_ids)
                """
                ),
                {"cluster_ids": cluster_ids},
            ).fetchall()

            if len(result) < 2:
                return 0.0

            # Analyze keyword overlap
            all_keywords = []
            for row in result:
                keywords = row.top_topics or []
                all_keywords.extend(keywords[:3])  # Top 3 keywords per cluster

            if not all_keywords:
                return 0.0

            # Calculate overlap percentage
            unique_keywords = set(all_keywords)
            total_keywords = len(all_keywords)
            overlap_score = 1.0 - (len(unique_keywords) / total_keywords)

            # Analyze temporal compatibility
            timestamps = [row.created_at for row in result]
            time_span = max(timestamps) - min(timestamps)
            time_compatibility = max(
                0.0, 1.0 - (time_span.days / 7.0)
            )  # Prefer within 1 week

            # Analyze size balance (prefer similar-sized clusters)
            sizes = [row.size for row in result]
            size_ratio = min(sizes) / max(sizes) if max(sizes) > 0 else 0.0

            # Combined compatibility score
            compatibility = (
                overlap_score * 0.5 + time_compatibility * 0.3 + size_ratio * 0.2
            )

            return min(compatibility, 1.0)

        except Exception as e:
            self.logger.error("Failed to calculate cluster compatibility", error=str(e))
            return 0.0

    async def _generate_narrative_suggestion(
        self, trigger: Dict[str, Any], cluster_ids: List[str]
    ) -> Dict[str, Any]:
        """Generate strategic narrative suggestion for cluster grouping"""

        theme = trigger.get(
            "theme", trigger.get("primary_keyword", "Strategic Development")
        )
        strategic_category = trigger.get("strategic_category", "general")

        # Generate strategic title (not journalistic headline)
        title_templates = {
            "geopolitical": f"Strategic {theme.title()} Geopolitical Realignment",
            "security": f"Evolving {theme.title()} Security Dynamics",
            "economic": f"Strategic {theme.title()} Economic Positioning",
            "technology": f"{theme.title()} Technology Strategic Competition",
            "general": f"Strategic {theme.title()} Developments",
        }

        suggested_title = title_templates.get(
            strategic_category, title_templates["general"]
        )

        # Generate strategic summary
        cluster_count = len(cluster_ids)
        rationale = trigger.get("rationale", "Related strategic developments")

        suggested_summary = (
            f"Analysis of {cluster_count} related developments in {theme} reveals "
            f"strategic patterns requiring consolidated intelligence assessment. "
            f"{rationale.capitalize()}."
        )

        # Calculate narrative quality score
        quality_factors = {
            "strategic_focus": 0.8 if strategic_category != "general" else 0.5,
            "cluster_coherence": min(cluster_count / 5.0, 1.0),  # Optimal 3-5 clusters
            "theme_specificity": 1.0 if theme != "unknown" else 0.3,
        }

        quality_score = sum(quality_factors.values()) / len(quality_factors)

        return {
            "suggested_title": suggested_title,
            "suggested_summary": suggested_summary,
            "strategic_category": strategic_category,
            "theme": theme,
            "quality_score": quality_score,
            "rationale": rationale,
        }

    async def _identify_cross_trigger_consolidations(
        self, triggers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify opportunities to consolidate across multiple triggers"""
        cross_consolidations = []

        # Group triggers by strategic category
        category_groups = {}
        for trigger in triggers:
            category = trigger.get("strategic_category", "general")
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(trigger)

        # Find cross-trigger consolidation opportunities
        for category, category_triggers in category_groups.items():
            if len(category_triggers) >= 2:

                # Calculate consolidated cluster count
                total_clusters = sum(
                    len(t.get("cluster_ids", [])) for t in category_triggers
                )

                if total_clusters >= 4:  # Minimum for cross-trigger consolidation
                    consolidation = {
                        "consolidation_type": "cross_trigger",
                        "strategic_category": category,
                        "source_triggers": [t.get("rank") for t in category_triggers],
                        "total_clusters": total_clusters,
                        "suggested_title": f"Strategic {category.title()} Intelligence Synthesis",
                        "estimated_effort": sum(
                            t.get("estimated_effort_hours", 0)
                            for t in category_triggers
                        )
                        * 0.8,  # 20% efficiency gain
                        "priority_score": sum(
                            t.get("priority_score", 0) for t in category_triggers
                        )
                        / len(category_triggers),
                    }
                    cross_consolidations.append(consolidation)

        return cross_consolidations

    async def _create_strategic_parent(self, group: Dict[str, Any]) -> Dict[str, Any]:
        """Create strategic parent narrative from grouping suggestion"""
        try:
            narrative_suggestion = group.get("narrative_suggestion", {})

            # Create parent using narrative manager
            parent_uuid, parent_display_id = (
                self.narrative_manager.create_manual_parent(
                    title=narrative_suggestion.get(
                        "suggested_title", "Strategic Development"
                    ),
                    summary=narrative_suggestion.get(
                        "suggested_summary", "Strategic narrative requiring analysis"
                    ),
                    curator_id="system_auto_curator",  # System-generated
                    cluster_ids=group.get("cluster_ids", []),
                    editorial_priority=2,  # High priority for auto-created
                    metadata={
                        "auto_created": True,
                        "source_trigger": group.get("trigger_id"),
                        "confidence_score": group.get("confidence_score"),
                        "theme": group.get("theme"),
                    },
                )
            )

            # Set review deadline based on priority
            deadline_hours = self.config["review_deadline_hours"][
                "high"
            ]  # Auto-created get high priority

            # Update status to pending review
            self.narrative_manager.update_curation_status(
                parent_uuid,
                "pending_review",
                "system_auto_curator",
                f'Auto-created strategic parent requiring editorial review. Confidence: {group.get("confidence_score", 0):.2f}',
            )

            return {
                "status": "success",
                "parent_uuid": parent_uuid,
                "parent_display_id": parent_display_id,
                "cluster_count": len(group.get("cluster_ids", [])),
                "theme": group.get("theme"),
                "confidence_score": group.get("confidence_score"),
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "theme": group.get("theme", "unknown"),
            }

    async def _auto_assign_reviewers(
        self, pending_reviews: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Auto-assign reviewers based on workload and expertise"""
        # Placeholder for reviewer assignment logic
        # In production, this would integrate with user management system

        assignments = []
        for review in pending_reviews:
            if not review.get("reviewer_id"):
                # Simple round-robin assignment logic
                reviewer_id = self._select_optimal_reviewer(review)
                if reviewer_id:
                    assignments.append(
                        {
                            "narrative_id": review["id"],
                            "reviewer_id": reviewer_id,
                            "reason": "workload_balancing",
                        }
                    )

        return {"assignments_made": len(assignments), "assignments": assignments}

    def _select_optimal_reviewer(self, review: Dict[str, Any]) -> Optional[str]:
        """Select optimal reviewer for a narrative (placeholder)"""
        # In production, this would analyze:
        # - Reviewer expertise vs narrative theme
        # - Current workload
        # - Review deadline urgency
        # - Past review performance

        # Placeholder logic
        strategic_category = review.get("strategic_category", "general")
        reviewer_map = {
            "geopolitical": "senior_geopolitical_editor",
            "security": "senior_security_editor",
            "economic": "senior_economic_editor",
            "technology": "senior_tech_editor",
            "general": "general_editor",
        }

        return reviewer_map.get(strategic_category, "general_editor")

    async def _send_review_notifications(
        self, overdue_reviews: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send notifications for overdue reviews (placeholder)"""
        # In production, this would integrate with notification system

        notifications = []
        for review in overdue_reviews:
            notification = {
                "type": "overdue_review",
                "recipient": review.get("reviewer_id", "supervisor"),
                "narrative_id": review["id"],
                "days_overdue": abs(review.get("days_until_deadline", 0)),
                "priority": review.get("editorial_priority", 5),
            }
            notifications.append(notification)

        return {
            "notifications_sent": len(notifications),
            "notifications": notifications,
        }

    async def _calculate_consolidation_metrics(self) -> Dict[str, Any]:
        """Calculate current consolidation performance metrics"""
        try:
            # Get consolidation statistics
            result = self.session.execute(
                text(
                    """
                    WITH recent_data AS (
                        SELECT 
                            COUNT(*) FILTER (WHERE parent_id IS NULL AND curation_source = 'manual_curation') as manual_parents,
                            COUNT(*) FILTER (WHERE parent_id IS NOT NULL) as child_narratives,
                            COUNT(DISTINCT cluster_id) as total_clusters
                        FROM narratives n
                        LEFT JOIN article_cluster_members acm ON acm.article_id::text = ANY(
                            SELECT jsonb_array_elements_text(n.manual_cluster_ids)
                        )
                        WHERE n.created_at >= NOW() - INTERVAL '7 days'
                    )
                    SELECT 
                        manual_parents,
                        child_narratives,
                        total_clusters,
                        CASE WHEN total_clusters > 0 THEN manual_parents::float / total_clusters ELSE 0 END as consolidation_ratio
                    FROM recent_data
                """
                )
            ).fetchone()

            return {
                "manual_parents_created": result.manual_parents if result else 0,
                "child_narratives": result.child_narratives if result else 0,
                "total_clusters_processed": result.total_clusters if result else 0,
                "consolidation_ratio": (
                    float(result.consolidation_ratio) if result else 0.0
                ),
                "target_ratio": self.config["consolidation_ratio_target"],
                "ratio_gap": self.config["consolidation_ratio_target"]
                - (float(result.consolidation_ratio) if result else 0.0),
            }

        except Exception as e:
            self.logger.error("Failed to calculate consolidation metrics", error=str(e))
            return {}

    async def _analyze_curator_performance(self) -> Dict[str, Any]:
        """Analyze curator productivity and quality metrics"""
        # Placeholder for curator performance analysis
        return {
            "active_curators": 0,
            "avg_narratives_per_curator": 0.0,
            "avg_review_time_hours": 0.0,
        }

    async def _analyze_review_efficiency(self) -> Dict[str, Any]:
        """Analyze review workflow efficiency"""
        # Placeholder for review efficiency analysis
        return {
            "avg_review_turnaround_hours": 0.0,
            "overdue_percentage": 0.0,
            "approval_rate": 0.0,
        }

    def _generate_executive_summary(
        self, workflow_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary of workflow execution"""

        stages = workflow_results.get("stages", {})

        trigger_stage = stages.get("trigger_analysis", {})
        creation_stage = stages.get("automated_creation", {})
        review_stage = stages.get("review_management", {})
        analytics_stage = stages.get("performance_analytics", {})

        return {
            "workflow_success": workflow_results.get("status") == "completed",
            "consolidation_opportunities_identified": len(
                trigger_stage.get("triggers", [])
            ),
            "strategic_parents_created": creation_stage.get("parents_created", 0),
            "pending_reviews": len(review_stage.get("pending_reviews", [])),
            "overdue_reviews": review_stage.get("overdue_count", 0),
            "current_consolidation_ratio": analytics_stage.get(
                "consolidation_metrics", {}
            ).get("consolidation_ratio", 0.0),
            "system_health": analytics_stage.get("system_health", {}).get(
                "overall_status", "UNKNOWN"
            ),
            "key_recommendations": self._generate_key_recommendations(workflow_results),
        }

    def _generate_key_recommendations(
        self, workflow_results: Dict[str, Any]
    ) -> List[str]:
        """Generate key operational recommendations"""
        recommendations = []

        stages = workflow_results.get("stages", {})

        # Trigger analysis recommendations
        trigger_count = len(stages.get("trigger_analysis", {}).get("triggers", []))
        if trigger_count > 8:
            recommendations.append(
                f"High consolidation demand detected ({trigger_count} opportunities) - consider additional curator resources"
            )
        elif trigger_count < 2:
            recommendations.append(
                "Low consolidation activity - review trigger sensitivity settings"
            )

        # Creation stage recommendations
        created_count = stages.get("automated_creation", {}).get("parents_created", 0)
        if created_count > 0:
            recommendations.append(
                f"Successfully auto-created {created_count} strategic parents - prioritize editorial review"
            )

        # Review stage recommendations
        overdue_count = stages.get("review_management", {}).get("overdue_count", 0)
        if overdue_count > 0:
            recommendations.append(
                f"{overdue_count} reviews overdue - escalate to senior editorial staff"
            )

        # Performance recommendations
        consolidation_ratio = (
            stages.get("performance_analytics", {})
            .get("consolidation_metrics", {})
            .get("consolidation_ratio", 0.0)
        )
        target_ratio = self.config["consolidation_ratio_target"]
        if consolidation_ratio < target_ratio * 0.8:
            recommendations.append(
                f"Consolidation ratio ({consolidation_ratio:.2f}) below target ({target_ratio}) - increase manual curation frequency"
            )

        if not recommendations:
            recommendations.append("Workflow operating within normal parameters")

        return recommendations


# CLI interface for daily operations
async def main():
    """CLI interface for manual curation orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Manual Curation Workflow Orchestrator"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Analyze only, do not create narratives"
    )
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--output", help="Output report file path")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    orchestrator = ManualCurationOrchestrator()

    # Load custom configuration if provided
    if args.config:
        with open(args.config, "r") as f:
            custom_config = json.load(f)
            orchestrator.config.update(custom_config)

    try:
        # Execute workflow
        if args.dry_run:
            # Only run analysis stages
            print("Dry run mode - analysis only")
            trigger_results = await orchestrator._execute_trigger_analysis()
            grouping_results = await orchestrator._execute_smart_grouping(
                trigger_results.get("triggers", [])
            )

            report = {
                "mode": "dry_run",
                "trigger_analysis": trigger_results,
                "smart_grouping": grouping_results,
            }
        else:
            report = await orchestrator.run_daily_curation_workflow()

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to {args.output}")
        else:
            print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"Workflow execution failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())

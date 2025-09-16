#!/usr/bin/env python3
"""
Daily Continuous Merging Workflow
Implements the complete continuous merging pipeline for Event Families
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.gen1.multipass_processor import get_multipass_processor
from core.database import get_db_session, check_database_connection
from sqlalchemy import text


class DailyContinuousMerging:
    """
    Daily continuous merging workflow for Event Families
    Implements the full continuous merging architecture
    """

    def __init__(self):
        self.processor = get_multipass_processor()

    async def run_daily_workflow(
        self,
        max_titles_pass1: int = 100,
        max_efs_pass2a: int = 50,
        dry_run: bool = False,
    ) -> dict:
        """
        Run the complete daily continuous merging workflow
        
        Args:
            max_titles_pass1: Maximum titles to process in Pass 1
            max_efs_pass2a: Maximum EFs to analyze in Pass 2A
            dry_run: Don't save changes to database
            
        Returns:
            Dictionary with workflow results
        """
        start_time = datetime.now()
        logger.info("=== DAILY CONTINUOUS MERGING WORKFLOW ===")
        
        workflow_results = {
            "start_time": start_time,
            "pass1_results": None,
            "pass2a_results": None,
            "total_processing_time": 0.0,
            "success": False,
            "errors": [],
            "summary": ""
        }
        
        try:
            # Check database connection
            if not check_database_connection():
                workflow_results["errors"].append("Database connection failed")
                return workflow_results
                
            logger.info("Database connection verified")
            
            # Step 1: Get unassigned titles count for planning
            unassigned_count = await self._get_unassigned_titles_count()
            logger.info(f"Found {unassigned_count} unassigned strategic titles")
            
            if unassigned_count == 0:
                logger.info("No unassigned titles - skipping Pass 1")
            else:
                # Step 2: Run Pass 1 - EF Assembly with ef_key generation
                logger.info(f"Step 1: Running Pass 1 EF Assembly (max {max_titles_pass1} titles)")
                pass1_result = await self.processor.run_pass1_entity_assembly(
                    max_titles=max_titles_pass1,
                    batch_size=max_titles_pass1,
                    dry_run=dry_run
                )
                workflow_results["pass1_results"] = pass1_result
                
                if pass1_result.errors:
                    workflow_results["errors"].extend([f"Pass 1: {error}" for error in pass1_result.errors])
                    
                logger.info(
                    f"Pass 1 completed: {len(pass1_result.event_families)} EFs created "
                    f"from {pass1_result.total_titles_processed} titles"
                )
            
            # Step 3: Get active EFs count for Pass 2A planning
            active_ef_count = await self._get_active_ef_count()
            logger.info(f"Found {active_ef_count} active Event Families for Pass 2A analysis")
            
            if active_ef_count < 2:
                logger.info("Insufficient active EFs for merging - skipping Pass 2A")
            else:
                # Step 4: Run Pass 2A - EF Merging by theater+type
                logger.info(f"Step 2: Running Pass 2A EF Merging (max {max_efs_pass2a} EFs)")
                pass2a_result = await self.processor.run_pass2a_ef_merging(
                    max_event_families=max_efs_pass2a,
                    dry_run=dry_run
                )
                workflow_results["pass2a_results"] = pass2a_result
                
                if pass2a_result.errors:
                    workflow_results["errors"].extend([f"Pass 2A: {error}" for error in pass2a_result.errors])
                    
                logger.info(
                    f"Pass 2A completed: {len(pass2a_result.event_families)} EFs after merging"
                )
            
            # Step 5: Generate workflow summary
            workflow_results["total_processing_time"] = (datetime.now() - start_time).total_seconds()
            workflow_results["success"] = len(workflow_results["errors"]) == 0
            workflow_results["summary"] = self._generate_workflow_summary(workflow_results)
            
            logger.info(f"Daily workflow completed in {workflow_results['total_processing_time']:.1f}s")
            logger.info(workflow_results["summary"])
            
            return workflow_results
            
        except Exception as e:
            logger.error(f"Daily workflow failed: {e}")
            workflow_results["errors"].append(f"Workflow failure: {e}")
            workflow_results["total_processing_time"] = (datetime.now() - start_time).total_seconds()
            return workflow_results

    async def _get_unassigned_titles_count(self) -> int:
        """Get count of unassigned strategic titles"""
        try:
            with get_db_session() as session:
                result = session.execute(text("""
                    SELECT COUNT(*) 
                    FROM titles 
                    WHERE gate_keep = true AND event_family_id IS NULL
                """)).scalar()
                return result or 0
        except Exception as e:
            logger.error(f"Failed to get unassigned titles count: {e}")
            return 0

    async def _get_active_ef_count(self) -> int:
        """Get count of active Event Families"""
        try:
            with get_db_session() as session:
                result = session.execute(text("""
                    SELECT COUNT(*) 
                    FROM event_families 
                    WHERE status = 'active' AND ef_key IS NOT NULL
                """)).scalar()
                return result or 0
        except Exception as e:
            logger.error(f"Failed to get active EF count: {e}")
            return 0

    def _generate_workflow_summary(self, results: dict) -> str:
        """Generate human-readable workflow summary"""
        summary_lines = []
        
        if results["pass1_results"]:
            p1 = results["pass1_results"]
            summary_lines.append(
                f"Pass 1: {len(p1.event_families)} EFs created from {p1.total_titles_processed} titles"
            )
        else:
            summary_lines.append("Pass 1: Skipped (no unassigned titles)")
            
        if results["pass2a_results"]:
            p2a = results["pass2a_results"]
            # For now, just show EF count after merging
            summary_lines.append(f"Pass 2A: {len(p2a.event_families)} EFs after merging")
        else:
            summary_lines.append("Pass 2A: Skipped (insufficient active EFs)")
            
        summary_lines.append(f"Total time: {results['total_processing_time']:.1f}s")
        
        if results["errors"]:
            summary_lines.append(f"Errors: {len(results['errors'])}")
            
        return " | ".join(summary_lines)

    async def get_system_status(self) -> dict:
        """Get current system status for monitoring"""
        try:
            with get_db_session() as session:
                # Get key metrics
                metrics = {}
                
                # Total active EFs
                metrics["active_event_families"] = session.execute(text("""
                    SELECT COUNT(*) FROM event_families WHERE status = 'active'
                """)).scalar() or 0
                
                # Merged EFs 
                metrics["merged_event_families"] = session.execute(text("""
                    SELECT COUNT(*) FROM event_families WHERE status = 'merged'
                """)).scalar() or 0
                
                # Unassigned strategic titles
                metrics["unassigned_strategic_titles"] = session.execute(text("""
                    SELECT COUNT(*) FROM titles WHERE gate_keep = true AND event_family_id IS NULL
                """)).scalar() or 0
                
                # EFs with ef_keys
                metrics["efs_with_ef_keys"] = session.execute(text("""
                    SELECT COUNT(*) FROM event_families WHERE ef_key IS NOT NULL AND status = 'active'
                """)).scalar() or 0
                
                # Recent EFs (last 24 hours)
                metrics["recent_event_families"] = session.execute(text("""
                    SELECT COUNT(*) FROM event_families 
                    WHERE created_at > NOW() - INTERVAL '24 hours' AND status = 'active'
                """)).scalar() or 0
                
                # Theater distribution
                theater_dist = session.execute(text("""
                    SELECT primary_theater, COUNT(*) as count
                    FROM event_families 
                    WHERE status = 'active' AND primary_theater IS NOT NULL
                    GROUP BY primary_theater 
                    ORDER BY count DESC
                """)).fetchall()
                
                metrics["theater_distribution"] = {row.primary_theater: row.count for row in theater_dist}
                
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow(),
                    "metrics": metrics,
                    "ready_for_processing": metrics["unassigned_strategic_titles"] > 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "status": "error",
                "timestamp": datetime.utcnow(),
                "error": str(e),
                "ready_for_processing": False
            }


async def main():
    """CLI entry point for daily continuous merging"""
    workflow = DailyContinuousMerging()
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        # Show system status
        status = await workflow.get_system_status()
        print("\n=== CONTINUOUS MERGING SYSTEM STATUS ===")
        print(f"Status: {status['status']}")
        print(f"Timestamp: {status['timestamp']}")
        
        if "metrics" in status:
            metrics = status["metrics"]
            print(f"\nActive Event Families: {metrics['active_event_families']}")
            print(f"Merged Event Families: {metrics['merged_event_families']}")
            print(f"Unassigned Strategic Titles: {metrics['unassigned_strategic_titles']}")
            print(f"EFs with ef_keys: {metrics['efs_with_ef_keys']}")
            print(f"Recent EFs (24h): {metrics['recent_event_families']}")
            
            print(f"\nTheater Distribution:")
            for theater, count in metrics["theater_distribution"].items():
                print(f"  {theater}: {count}")
                
            print(f"\nReady for processing: {status['ready_for_processing']}")
        
        if "error" in status:
            print(f"Error: {status['error']}")
            
    elif len(sys.argv) > 1 and sys.argv[1] == "run":
        # Run daily workflow
        max_titles = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        max_efs = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        dry_run = "--dry-run" in sys.argv
        
        print(f"\n=== RUNNING DAILY CONTINUOUS MERGING ===")
        print(f"Max titles (Pass 1): {max_titles}")
        print(f"Max EFs (Pass 2A): {max_efs}")
        print(f"Dry run: {dry_run}")
        
        results = await workflow.run_daily_workflow(
            max_titles_pass1=max_titles,
            max_efs_pass2a=max_efs,
            dry_run=dry_run
        )
        
        print(f"\n=== WORKFLOW RESULTS ===")
        print(f"Success: {results['success']}")
        print(f"Summary: {results['summary']}")
        
        if results["errors"]:
            print(f"\nErrors ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"  - {error}")
                
    else:
        print("Usage: python daily_continuous_merging.py [status|run] [max_titles] [max_efs] [--dry-run]")
        print("  status: Show system status and metrics")
        print("  run: Execute daily continuous merging workflow")
        print("  max_titles: Maximum titles to process in Pass 1 (default: 100)")
        print("  max_efs: Maximum EFs to analyze in Pass 2A (default: 50)")
        print("  --dry-run: Don't save changes to database")


if __name__ == "__main__":
    asyncio.run(main())
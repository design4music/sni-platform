"""
Phase 3.5 Pipeline: Interpretive Intelligence Layer

Orchestrates the complete Phase 3.5 process:
1. P3.5c: Interpretive Merging - Merge semantically similar EFs
2. P3.5d: Interpretive Splitting - Split mixed-narrative EFs

This runs AFTER Phase 3 (mechanical EF creation) to refine using LLM intelligence.
"""

import asyncio
from typing import Dict, Optional

from loguru import logger

from apps.generate.ef_merger import EFMerger, get_ef_merger
from apps.generate.ef_splitter import EFSplitter, get_ef_splitter
from core.config import get_config


class P35Pipeline:
    """
    Phase 3.5 Pipeline Orchestrator

    Runs interpretive intelligence layer after mechanical EF creation:
    - P3.5c: Merge similar EFs using strategic_purpose comparison
    - P3.5d: Split mixed EFs using narrative coherence analysis
    """

    def __init__(self):
        self.config = get_config()
        self.merger = get_ef_merger()
        self.splitter = get_ef_splitter()

    async def run_full_pipeline(
        self,
        dry_run: bool = False,
        max_merge_pairs: Optional[int] = None,
        max_split_efs: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Run complete Phase 3.5 pipeline

        Args:
            dry_run: If True, only report what would change
            max_merge_pairs: Maximum pairs to evaluate for merging
            max_split_efs: Maximum EFs to evaluate for splitting

        Returns:
            Dict with pipeline results
        """
        logger.info("=" * 70)
        logger.info("PHASE 3.5: INTERPRETIVE INTELLIGENCE PIPELINE")
        logger.info("=" * 70)

        results = {
            "p35c_merge": {},
            "p35d_split": {},
            "total_changes": 0,
        }

        # Step 1: P3.5c - Interpretive Merging
        if self.config.p35c_enabled:
            logger.info("\n>>> Step 1: P3.5c Interpretive Merging")
            merge_results = self.merger.run_merge_cycle(
                max_pairs=max_merge_pairs or self.config.p35c_max_pairs_per_cycle,
                dry_run=dry_run,
            )
            results["p35c_merge"] = merge_results
            results["total_changes"] += merge_results.get("merged", 0)

            logger.info(f"P3.5c complete: {merge_results.get('merged', 0)} EFs merged")
        else:
            logger.info("P3.5c (Merging) disabled in config")

        # Step 2: P3.5d - Interpretive Splitting
        if self.config.p35d_enabled:
            logger.info("\n>>> Step 2: P3.5d Interpretive Splitting")
            split_results = self.splitter.run_split_cycle(
                max_efs=max_split_efs or self.config.p35d_max_efs_per_cycle,
                dry_run=dry_run,
            )
            results["p35d_split"] = split_results
            results["total_changes"] += split_results.get("split", 0)

            logger.info(f"P3.5d complete: {split_results.get('split', 0)} EFs split")
        else:
            logger.info("P3.5d (Splitting) disabled in config")

        logger.info("\n" + "=" * 70)
        logger.info("PHASE 3.5 PIPELINE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total EF changes: {results['total_changes']}")
        logger.info(f"  Merged: {results['p35c_merge'].get('merged', 0)}")
        logger.info(f"  Split: {results['p35d_split'].get('split', 0)}")

        if dry_run:
            logger.info("\n[DRY RUN - No changes were made to database]")

        return results

    def run_merge_only(self, max_pairs: Optional[int] = None, dry_run: bool = False):
        """Run only P3.5c merging"""
        if not self.config.p35c_enabled:
            logger.warning("P3.5c is disabled in config")
            return {"merged": 0, "skipped": 0}

        return self.merger.run_merge_cycle(
            max_pairs=max_pairs or self.config.p35c_max_pairs_per_cycle, dry_run=dry_run
        )

    def run_split_only(self, max_efs: Optional[int] = None, dry_run: bool = False):
        """Run only P3.5d splitting"""
        if not self.config.p35d_enabled:
            logger.warning("P3.5d is disabled in config")
            return {"split": 0, "kept": 0}

        return self.splitter.run_split_cycle(
            max_efs=max_efs or self.config.p35d_max_efs_per_cycle, dry_run=dry_run
        )


# CLI Interface
def create_cli_app():
    """Create CLI app for P3.5 pipeline"""
    import typer

    app = typer.Typer(help="Phase 3.5: Interpretive Intelligence Pipeline")

    @app.command()
    def run_full(
        max_merge_pairs: int = typer.Option(
            None, help="Maximum pairs to evaluate for merging"
        ),
        max_split_efs: int = typer.Option(
            None, help="Maximum EFs to evaluate for splitting"
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Only report what would change"
        ),
    ):
        """Run complete P3.5 pipeline (merge + split)"""

        async def main():
            pipeline = P35Pipeline()
            results = await pipeline.run_full_pipeline(
                dry_run=dry_run,
                max_merge_pairs=max_merge_pairs,
                max_split_efs=max_split_efs,
            )

            # Print summary
            print("\n" + "=" * 70)
            print("PHASE 3.5 PIPELINE RESULTS")
            print("=" * 70)
            print(f"\nP3.5c (Merging):")
            print(f"  Pairs evaluated: {results['p35c_merge'].get('evaluated', 0)}")
            print(f"  EFs merged: {results['p35c_merge'].get('merged', 0)}")
            print(f"\nP3.5d (Splitting):")
            print(f"  EFs evaluated: {results['p35d_split'].get('evaluated', 0)}")
            print(f"  EFs split: {results['p35d_split'].get('split', 0)}")
            print(f"\nTotal changes: {results['total_changes']}")

            if dry_run:
                print("\n[DRY RUN - No changes made]")
            print("=" * 70)

        asyncio.run(main())

    @app.command()
    def merge_only(
        max_pairs: int = typer.Option(None, help="Maximum pairs to evaluate"),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Only report what would merge"
        ),
    ):
        """Run only P3.5c (interpretive merging)"""
        pipeline = P35Pipeline()
        results = pipeline.run_merge_only(max_pairs=max_pairs, dry_run=dry_run)

        print("\n" + "=" * 60)
        print("P3.5c: INTERPRETIVE MERGING RESULTS")
        print("=" * 60)
        print(f"Pairs evaluated: {results.get('evaluated', 0)}")
        print(f"EFs merged: {results.get('merged', 0)}")
        if dry_run:
            print("\n[DRY RUN - No changes made]")
        print("=" * 60)

    @app.command()
    def split_only(
        max_efs: int = typer.Option(None, help="Maximum EFs to evaluate"),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Only report what would split"
        ),
    ):
        """Run only P3.5d (interpretive splitting)"""
        pipeline = P35Pipeline()
        results = pipeline.run_split_only(max_efs=max_efs, dry_run=dry_run)

        print("\n" + "=" * 60)
        print("P3.5d: INTERPRETIVE SPLITTING RESULTS")
        print("=" * 60)
        print(f"EFs evaluated: {results.get('evaluated', 0)}")
        print(f"EFs split: {results.get('split', 0)}")
        if dry_run:
            print("\n[DRY RUN - No changes made]")
        print("=" * 60)

    return app


if __name__ == "__main__":
    app = create_cli_app()
    app()

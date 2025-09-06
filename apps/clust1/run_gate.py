#!/usr/bin/env python3
"""
CLUST-1.5: Strategic Gate Processing Driver
Processes pending titles through Strategic Gate and persists results
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, select, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import array

from core.config import get_config
from apps.clust1.strategic_gate import filter_titles_batch, GateResult


class GateProcessor:
    """Strategic Gate batch processor with persistence"""
    
    def __init__(self, batch_size: int = 500):
        self.config = get_config()
        self.batch_size = batch_size
        self.engine = create_engine(self.config.database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Statistics tracking
        self.stats = {
            'total_processed': 0,
            'kept': 0,
            'actor_hits': 0,
            'anchor_hits': 0,
            'below_threshold': 0,
            'errors': 0
        }
    
    def get_pending_titles_batch(self, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get batch of titles needing gate processing
        
        Returns:
            List of title dictionaries with id, title_norm, title_display
        """
        with self.Session() as session:
            result = session.execute(text("""
                SELECT id, title_norm, title_display, pubdate_utc
                FROM titles 
                WHERE processing_status = 'pending' 
                  AND gate_at IS NULL
                ORDER BY pubdate_utc DESC, id
                LIMIT :batch_size OFFSET :offset
            """), {
                'batch_size': self.batch_size,
                'offset': offset
            })
            
            return [
                {
                    'id': row.id,
                    'title_norm': row.title_norm or '',
                    'title_display': row.title_display or '',
                    'pubdate_utc': row.pubdate_utc
                }
                for row in result.fetchall()
            ]
    
    def update_gate_results(self, results: List[Tuple[Dict[str, Any], GateResult]]) -> int:
        """
        Update titles table with gate processing results
        
        Args:
            results: List of (title_dict, gate_result) tuples
            
        Returns:
            Number of rows updated
        """
        if not results:
            return 0
        
        updates = []
        now = datetime.now()
        
        for title, gate_result in results:
            update_data = {
                'gate_keep': gate_result.keep,
                'gate_reason': gate_result.reason,
                'gate_score': float(gate_result.score) if gate_result.score else None,
                'gate_anchor_labels': gate_result.anchor_labels if gate_result.anchor_labels else None,
                'gate_actor_hit': gate_result.actor_hit,
                'gate_at': now,
                'processing_status': 'gated'
            }
            
            updates.append({
                'title_id': title['id'],
                **update_data
            })
        
        # Batch update using individual queries for proper parameter binding
        with self.Session() as session:
            try:
                updated_count = 0
                
                for update_data in updates:
                    sql = """
                    UPDATE titles SET 
                        gate_keep = :gate_keep,
                        gate_reason = :gate_reason,
                        gate_score = :gate_score,
                        gate_anchor_labels = :gate_anchor_labels,
                        gate_actor_hit = :gate_actor_hit,
                        gate_at = :gate_at,
                        processing_status = :processing_status
                    WHERE id = :title_id
                    """
                    
                    result = session.execute(text(sql), update_data)
                    updated_count += result.rowcount
                
                session.commit()
                logger.info(f"Updated {updated_count} titles with gate results")
                return updated_count
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to update gate results: {e}")
                raise
    
    def process_batch(self, titles: List[Dict[str, Any]]) -> int:
        """
        Process a single batch through Strategic Gate
        
        Returns:
            Number of titles processed
        """
        if not titles:
            return 0
        
        try:
            # Run Strategic Gate filtering
            logger.info(f"Processing batch of {len(titles)} titles through Strategic Gate")
            results = filter_titles_batch(titles)
            
            # Update statistics
            for _, gate_result in results:
                self.stats['total_processed'] += 1
                
                if gate_result.keep:
                    self.stats['kept'] += 1
                    
                if gate_result.reason == 'actor_hit':
                    self.stats['actor_hits'] += 1
                elif gate_result.reason == 'anchor_sim':
                    self.stats['anchor_hits'] += 1
                elif gate_result.reason == 'below_threshold':
                    self.stats['below_threshold'] += 1
            
            # Persist results to database
            updated_count = self.update_gate_results(results)
            
            logger.info(f"Batch complete: {updated_count} titles updated")
            return updated_count
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            self.stats['errors'] += 1
            raise
    
    def run(self, max_batches: int = None) -> Dict[str, int]:
        """
        Run gate processing on all pending titles
        
        Args:
            max_batches: Maximum number of batches to process (None for all)
            
        Returns:
            Processing statistics
        """
        logger.info("Starting Strategic Gate processing...")
        
        batch_num = 0
        offset = 0
        total_updated = 0
        
        while max_batches is None or batch_num < max_batches:
            # Get next batch of pending titles
            titles = self.get_pending_titles_batch(offset)
            
            if not titles:
                logger.info("No more pending titles to process")
                break
            
            logger.info(f"Processing batch {batch_num + 1}: {len(titles)} titles (offset={offset})")
            
            try:
                updated = self.process_batch(titles)
                total_updated += updated
                batch_num += 1
                offset += self.batch_size
                
            except Exception as e:
                logger.error(f"Batch {batch_num + 1} failed: {e}")
                # Continue with next batch on error
                offset += self.batch_size
                batch_num += 1
                continue
        
        # Final statistics
        self.stats['batches_processed'] = batch_num
        self.stats['total_updated'] = total_updated
        
        logger.info("Strategic Gate processing completed")
        self._log_summary()
        
        return self.stats
    
    def _log_summary(self):
        """Log processing summary statistics"""
        stats = self.stats
        logger.info("=== STRATEGIC GATE PROCESSING SUMMARY ===")
        logger.info(f"Total processed: {stats['total_processed']}")
        logger.info(f"Kept: {stats['kept']} ({stats['kept']/max(stats['total_processed'], 1)*100:.1f}%)")
        logger.info(f"Actor hits: {stats['actor_hits']}")
        logger.info(f"Anchor hits: {stats['anchor_hits']}")
        logger.info(f"Below threshold: {stats['below_threshold']}")
        logger.info(f"Batches processed: {stats.get('batches_processed', 0)}")
        logger.info(f"Database updates: {stats.get('total_updated', 0)}")
        if stats['errors'] > 0:
            logger.warning(f"Errors encountered: {stats['errors']}")
    
    def check_pending_count(self) -> int:
        """Get count of titles pending gate processing"""
        with self.Session() as session:
            result = session.execute(text("""
                SELECT COUNT(*) 
                FROM titles 
                WHERE processing_status = 'pending' AND gate_at IS NULL
            """))
            return result.scalar()
    
    def get_gate_summary(self) -> Dict[str, Any]:
        """Get summary of gate processing results"""
        with self.Session() as session:
            # Overall counts
            result = session.execute(text("""
                SELECT 
                    COUNT(*) as total_titles,
                    COUNT(*) FILTER (WHERE gate_at IS NOT NULL) as processed_titles,
                    COUNT(*) FILTER (WHERE gate_keep = true) as kept_titles,
                    COUNT(*) FILTER (WHERE processing_status = 'pending' AND gate_at IS NULL) as pending_titles
                FROM titles
            """))
            row = result.fetchone()
            
            # Reason breakdown
            reason_result = session.execute(text("""
                SELECT gate_reason, COUNT(*) as count
                FROM titles 
                WHERE gate_at IS NOT NULL
                GROUP BY gate_reason
                ORDER BY count DESC
            """))
            
            reason_breakdown = {row.gate_reason: row.count for row in reason_result.fetchall()}
            
            return {
                'total_titles': row.total_titles,
                'processed_titles': row.processed_titles,
                'kept_titles': row.kept_titles,
                'pending_titles': row.pending_titles,
                'reason_breakdown': reason_breakdown,
                'keep_rate': (row.kept_titles / max(row.processed_titles, 1)) * 100
            }


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Strategic Gate Processor")
    parser.add_argument('--batch-size', type=int, default=500,
                       help='Batch size for processing (default: 500)')
    parser.add_argument('--max-batches', type=int, default=None,
                       help='Maximum batches to process (default: all)')
    parser.add_argument('--summary', action='store_true',
                       help='Show processing summary and exit')
    parser.add_argument('--pending', action='store_true',
                       help='Show pending count and exit')
    
    args = parser.parse_args()
    
    processor = GateProcessor(batch_size=args.batch_size)
    
    if args.summary:
        summary = processor.get_gate_summary()
        print(f"Gate Summary: {summary['kept_titles']}/{summary['processed_titles']} kept "
              f"({summary['keep_rate']:.1f}%), {summary['pending_titles']} pending")
        print(f"Reasons: {summary['reason_breakdown']}")
        return
    
    if args.pending:
        pending = processor.check_pending_count()
        print(f"Pending titles: {pending}")
        return
    
    # Run gate processing
    try:
        stats = processor.run(max_batches=args.max_batches)
        
        # Print one-line summary for automation
        print(f"GATE_RESULT: {stats['kept']}/{stats['total_processed']} kept, "
              f"{stats['actor_hits']} actor_hit, {stats['anchor_hits']} anchor_sim, "
              f"{stats['below_threshold']} below_threshold")
        
        # Exit with appropriate code
        sys.exit(0 if stats['errors'] == 0 else 1)
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
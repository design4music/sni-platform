#!/usr/bin/env python3
"""
GEN-3: RAI Overlay Analysis
Strategic Narrative Intelligence Platform

Applies comprehensive RAI (Responsible AI) analysis to narrative cards including:
- Content safety validation via external RAI service
- Narrative adequacy assessment (evidence, sources, coherence)  
- Publication recommendation generation (approve/review/reject)
- Compliance status determination with bias detection

Integrates with external RAI service with local fallback analysis.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import psycopg2
import psycopg2.extras

# Add project root to path for centralized config
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from etl_pipeline.core.config import get_db_connection
from etl_pipeline.rai.rai_client import RAIClient, RAIUnavailable

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RAIOverlayProcessor:
    """Apply comprehensive RAI analysis overlay to narrative cards."""
    
    def __init__(self, batch_size: int = 20, force: bool = False):
        self.batch_size = batch_size
        self.force = force
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.service_unavailable_count = 0
        
        # Initialize RAI client
        self.rai_client = RAIClient()
        
        # Quality thresholds
        self.min_adequacy_score = 0.6
        self.min_confidence_rating = 0.5
        self.min_overall_rai_score = 0.65

    def get_pending_narratives(self, conn) -> List[Dict]:
        """Get narratives ready for GEN-3 RAI overlay processing."""
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Select narratives with GEN-2 complete but not GEN-3
        base_query = """
        SELECT 
            id, narrative_id, title, summary, top_excerpts, source_stats,
            activity_timeline, alignment, actor_origin, frame_logic, 
            turning_points, narrative_tension, logical_strain, rai_analysis,
            update_status, version_history, created_at, updated_at
        FROM narratives 
        WHERE consolidation_stage = 'consolidated'
          AND archive_reason IS NULL
          AND (update_status->'gen'->>'gen2_done_at') IS NOT NULL
        """
        
        if self.force:
            # Force regeneration - process all GEN-2 complete narratives
            query = base_query + " ORDER BY updated_at DESC LIMIT %s"
            cursor.execute(query, (self.batch_size,))
        else:
            # Only process narratives without GEN-3 completion or outdated analysis
            query = base_query + """
              AND (
                (update_status->'gen'->>'gen3_done_at') IS NULL OR
                (rai_analysis->>'version') IS NULL OR
                (rai_analysis->>'version') < '1'
              )
            ORDER BY updated_at DESC LIMIT %s
            """
            cursor.execute(query, (self.batch_size,))
        
        narratives = cursor.fetchall()
        cursor.close()
        
        logger.info(f"Found {len(narratives)} narratives ready for GEN-3 processing")
        return [dict(n) for n in narratives]

    def check_analysis_idempotency(self, narrative: Dict) -> bool:
        """Check if narrative needs re-analysis based on input hash."""
        existing_analysis = narrative.get('rai_analysis')
        
        if not existing_analysis or self.force:
            return True  # Needs analysis
        
        if isinstance(existing_analysis, str):
            try:
                existing_analysis = json.loads(existing_analysis)
            except:
                return True  # Invalid analysis, needs re-analysis
        
        if not isinstance(existing_analysis, dict):
            return True  # Invalid format, needs re-analysis
        
        # Check if we have a valid version and input hash
        if existing_analysis.get('version') != '1':
            return True  # Outdated version
        
        # Calculate current input hash
        payload = self.rai_client.create_payload(narrative)
        current_hash = self.rai_client.calculate_input_hash(payload)
        stored_hash = existing_analysis.get('input_hash')
        
        if current_hash != stored_hash:
            logger.debug(f"Input changed for narrative {narrative['id']}, re-analysis needed")
            return True  # Content changed, needs re-analysis
        
        logger.debug(f"Narrative {narrative['id']} analysis is up to date, skipping")
        return False  # Analysis is current

    def process_rai_analysis(self, narrative: Dict) -> Optional[Dict]:
        """Process narrative through RAI analysis pipeline."""
        try:
            # Create analysis payload
            payload = self.rai_client.create_payload(narrative)
            
            # Calculate input hash for idempotency
            input_hash = self.rai_client.calculate_input_hash(payload)
            
            # Perform RAI analysis
            analysis_result = self.rai_client.analyze_narrative(payload)
            
            # Enhance analysis with additional metadata
            now_iso = datetime.now(timezone.utc).isoformat()
            
            rai_analysis = {
                'version': '1',
                'analyzed_at': now_iso,
                'input_hash': input_hash,
                'adequacy_score': analysis_result['adequacy_score'],
                'confidence_rating': analysis_result['confidence_rating'],
                'premise_lenses': analysis_result['premise_lenses'],
                'bias_flags': analysis_result['bias_flags'],
                'blind_spots': analysis_result['blind_spots'],
                'notes': analysis_result['notes'],
                'service_analysis': analysis_result['service_analysis'],
                'overall_score': self.calculate_overall_score(analysis_result),
                'publication_recommendation': self.generate_publication_recommendation(analysis_result),
                'compliance_status': self.assess_compliance_status(analysis_result)
            }
            
            return rai_analysis
            
        except RAIUnavailable as e:
            logger.warning(f"RAI service unavailable for narrative {narrative['id']}: {e}")
            self.service_unavailable_count += 1
            
            # Return minimal analysis to allow pipeline continuation
            return self.create_minimal_analysis(narrative)
            
        except Exception as e:
            logger.error(f"Error in RAI analysis for narrative {narrative['id']}: {e}")
            return None

    def calculate_overall_score(self, analysis: Dict) -> float:
        """Calculate overall RAI score combining adequacy and confidence."""
        adequacy = analysis['adequacy_score']
        confidence = analysis['confidence_rating']
        
        # Weighted combination: adequacy is more important
        overall = (adequacy * 0.7) + (confidence * 0.3)
        
        # Apply penalties for bias flags
        bias_penalty = min(0.2, len(analysis['bias_flags']) * 0.05)
        overall -= bias_penalty
        
        # Apply penalties for blind spots
        blind_spot_penalty = min(0.1, len(analysis['blind_spots']) * 0.03)
        overall -= blind_spot_penalty
        
        return round(max(0.0, min(1.0, overall)), 3)

    def generate_publication_recommendation(self, analysis: Dict) -> str:
        """Generate publication recommendation based on analysis scores."""
        adequacy = analysis['adequacy_score']
        confidence = analysis['confidence_rating']
        overall = self.calculate_overall_score(analysis)
        
        # High quality narratives
        if overall >= self.min_overall_rai_score and adequacy >= self.min_adequacy_score:
            return 'approve'
        
        # Moderate quality - needs human review
        elif adequacy >= 0.5 and confidence >= 0.4 and len(analysis['bias_flags']) <= 2:
            return 'review'
        
        # Low quality - reject for now
        else:
            return 'reject'

    def assess_compliance_status(self, analysis: Dict) -> str:
        """Assess compliance status based on analysis results."""
        bias_flags = analysis['bias_flags']
        
        # Critical compliance issues
        critical_flags = ['misinformation', 'hate_speech', 'harmful_content']
        if any(flag in bias_flags for flag in critical_flags):
            return 'non_compliant'
        
        # Minor compliance concerns
        minor_flags = ['confirmation_bias', 'selection_bias', 'limited_sources']
        if any(flag in bias_flags for flag in minor_flags):
            return 'needs_review'
        
        # Generally compliant
        return 'compliant'

    def create_minimal_analysis(self, narrative: Dict) -> Dict:
        """Create minimal RAI analysis when service is unavailable."""
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = self.rai_client.create_payload(narrative)
        
        return {
            'version': '1',
            'analyzed_at': now_iso,
            'input_hash': self.rai_client.calculate_input_hash(payload),
            'adequacy_score': 0.5,  # Neutral default
            'confidence_rating': 0.4,  # Conservative default
            'premise_lenses': ['general'],
            'bias_flags': ['service_unavailable'],
            'blind_spots': ['rai_analysis_incomplete'],
            'notes': 'RAI service unavailable - minimal analysis applied',
            'service_analysis': False,
            'overall_score': 0.45,
            'publication_recommendation': 'review',  # Require human review
            'compliance_status': 'needs_review'
        }

    def update_narrative_with_rai(self, conn, narrative_id: int, rai_analysis: Dict) -> bool:
        """Update narrative with GEN-3 RAI analysis results."""
        cursor = conn.cursor()
        
        try:
            # Get current update_status and version_history
            cursor.execute(
                "SELECT update_status, version_history FROM narratives WHERE id = %s",
                (narrative_id,)
            )
            result = cursor.fetchone()
            if not result:
                logger.error(f"Narrative {narrative_id} not found")
                return False
            
            current_status, current_history = result
            
            # Update progress tracking
            now_iso = datetime.now(timezone.utc).isoformat()
            
            # Enhance update_status with GEN-3 completion
            new_status = current_status.copy() if current_status else {}
            new_status.update({
                'last_updated': now_iso,
                'update_trigger': 'gen3_rai_overlay',
                'gen': {
                    **new_status.get('gen', {}),
                    'gen3_done_at': now_iso,
                    'gen3_version': '1.0',
                    'rai_score': rai_analysis['overall_score'],
                    'publication_ready': new_status.get('gen', {}).get('publication_ready', True)  # Keep existing ready status
                },
                'status': 'ok' if rai_analysis['overall_score'] >= self.min_overall_rai_score else 'needs_review',
                'last_rai': now_iso,
                'rai_version': '1'
            })
            
            # Update version_history
            new_history = current_history.copy() if current_history else {}
            gen3_entry = {
                'timestamp': now_iso,
                'stage': 'gen3_rai_overlay',
                'action': 'rai_analysis_complete',
                'adequacy_score': rai_analysis['adequacy_score'],
                'confidence_rating': rai_analysis['confidence_rating'],
                'overall_score': rai_analysis['overall_score'],
                'publication_recommendation': rai_analysis['publication_recommendation'],
                'compliance_status': rai_analysis['compliance_status'],
                'service_analysis': rai_analysis['service_analysis']
            }
            
            if 'gen3_history' not in new_history:
                new_history['gen3_history'] = []
            new_history['gen3_history'].append(gen3_entry)
            
            # Execute update
            update_query = """
            UPDATE narratives 
            SET rai_analysis = %s,
                update_status = %s,
                version_history = %s,
                updated_at = NOW()
            WHERE id = %s
            """
            
            cursor.execute(update_query, (
                json.dumps(rai_analysis),
                json.dumps(new_status),
                json.dumps(new_history),
                narrative_id
            ))
            
            conn.commit()
            logger.debug(f"Updated narrative {narrative_id} with RAI analysis")
            return True
            
        except Exception as e:
            logger.error(f"Error updating narrative {narrative_id}: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()

    def process_narrative(self, conn, narrative: Dict) -> bool:
        """Process a single narrative through GEN-3 RAI overlay."""
        narrative_id = narrative['id']
        
        try:
            logger.debug(f"Processing narrative {narrative_id} for RAI analysis")
            
            # Check if analysis is needed (idempotency)
            if not self.check_analysis_idempotency(narrative):
                self.success_count += 1  # Count as success (no work needed)
                return True
            
            # Perform RAI analysis
            rai_analysis = self.process_rai_analysis(narrative)
            
            if not rai_analysis:
                logger.error(f"Failed to generate RAI analysis for narrative {narrative_id}")
                self.error_count += 1
                return False
            
            # Quality validation
            adequacy = rai_analysis['adequacy_score']
            overall = rai_analysis['overall_score']
            
            if adequacy < 0.3:
                logger.warning(f"Very low adequacy score ({adequacy}) for narrative {narrative_id}")
            
            if overall < 0.3:
                logger.warning(f"Very low overall RAI score ({overall}) for narrative {narrative_id}")
            
            # Update database
            if self.update_narrative_with_rai(conn, narrative_id, rai_analysis):
                self.success_count += 1
                recommendation = rai_analysis['publication_recommendation']
                service_used = "RAI-Service" if rai_analysis['service_analysis'] else "Local-Fallback"
                logger.info(f"SUCCESS: RAI analysis for narrative {narrative_id} (overall: {overall}, rec: {recommendation}, via: {service_used})")
                return True
            else:
                self.error_count += 1
                return False
                
        except Exception as e:
            logger.error(f"Error processing narrative {narrative_id}: {e}")
            self.error_count += 1
            return False

    def run_rai_overlay(self) -> Dict:
        """Run complete GEN-3 RAI overlay process."""
        start_time = time.time()
        logger.info("Starting GEN-3 RAI overlay analysis")
        
        try:
            conn = get_db_connection()
            
            # Get narratives ready for processing
            narratives = self.get_pending_narratives(conn)
            
            if not narratives:
                logger.info("No narratives ready for GEN-3 processing")
                return self.get_results_summary(start_time)
            
            # Check RAI service health
            if self.rai_client.enabled:
                service_healthy = self.rai_client.check_service_health()
                logger.info(f"RAI service health: {'OK' if service_healthy else 'UNAVAILABLE'}")
            
            # Process each narrative
            for narrative in narratives:
                self.processed_count += 1
                self.process_narrative(conn, narrative)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"GEN-3 RAI overlay failed: {e}")
            if 'conn' in locals():
                conn.close()
        
        return self.get_results_summary(start_time)

    def get_results_summary(self, start_time: float) -> Dict:
        """Generate processing results summary."""
        elapsed_time = time.time() - start_time
        success_rate = (self.success_count / self.processed_count * 100) if self.processed_count > 0 else 0
        
        results = {
            'processed': self.processed_count,
            'successful': self.success_count,
            'errors': self.error_count,
            'service_unavailable': self.service_unavailable_count,
            'success_rate': f"{success_rate:.1f}%",
            'elapsed_time': f"{elapsed_time:.1f}s",
            'rate_per_second': f"{self.processed_count / elapsed_time:.2f}" if elapsed_time > 0 else "0",
            'rai_enabled': self.rai_client.enabled
        }
        
        logger.info(f"GEN-3 SUMMARY: {results}")
        return results


def main():
    """Main entry point for GEN-3 RAI overlay."""
    parser = argparse.ArgumentParser(description='GEN-3: RAI Overlay Analysis')
    parser.add_argument('--batch', type=int, default=20,
                        help='Batch size for processing (default: 20)')
    parser.add_argument('--force', action='store_true',
                        help='Force regeneration of all RAI analyses')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize and run RAI processor
    processor = RAIOverlayProcessor(batch_size=args.batch, force=args.force)
    results = processor.run_rai_overlay()
    
    # Display results
    print("\n" + "="*50)
    print("GEN-3 RAI OVERLAY ANALYSIS COMPLETE")
    print("="*50)
    print(f"Processed: {results['processed']} narratives")
    print(f"Successful: {results['successful']} analyses")
    print(f"Errors: {results['errors']} failed")
    print(f"Service Unavailable: {results['service_unavailable']} fallbacks")
    print(f"Success Rate: {results['success_rate']}")
    print(f"Processing Time: {results['elapsed_time']}")
    print(f"Rate: {results['rate_per_second']} narratives/second")
    print(f"RAI Service Enabled: {results['rai_enabled']}")
    
    # Exit with appropriate code
    exit_code = 0 if results['errors'] == 0 else 1
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
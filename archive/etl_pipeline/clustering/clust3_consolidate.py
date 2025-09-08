#!/usr/bin/env python3
"""
CLUST-3: Narrative Consolidation & Archival
Strategic Narrative Intelligence Platform

Specification-compliant implementation that:
1. Loads candidates (consolidation_stage='raw', window 7-14 days)
2. Loads library (non-raw, last 90 days)
3. Ensures narrative_embedding exists (compute if NULL)
4. Computes anchor tokens using canonicalizer
5. Calculates cos, jaccard_tokens, country_overlap, alignment_conflict
6. Applies decision rules: merge, create, or review
7. Updates database with proper consolidation_stage transitions

Key Features:
- Embedding-based similarity with cosine threshold (0.82)
- Token Jaccard similarity with canonicalized anchors (0.40)
- Country overlap detection
- Alignment conflict resolution
- Size-based granularity rules
- Comprehensive KPI logging
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import psycopg2
from sentence_transformers import SentenceTransformer

# Add project root to path for centralized config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from etl_pipeline.core.config import get_db_connection

# Import keyword canonicalizer
sys.path.append(str(Path(__file__).parent.parent / "keywords"))
from canonicalizer import get_canonicalizer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CLUST3NarrativeConsolidator:
    """Specification-compliant CLUST-3 narrative consolidator"""
    
    def __init__(self, 
                 cos_min: float = 0.82,
                 tok_jacc_min: float = 0.40, 
                 align_strict: bool = True,
                 on_merge: str = "archive_raw"):
        self.cos_min = cos_min
        self.tok_jacc_min = tok_jacc_min
        self.align_strict = align_strict
        self.on_merge = on_merge
        
        # Load sentence transformer for embeddings
        self.model = self._load_sentence_transformer()
        
        # Load canonicalizer for anchor tokens
        self.canonicalizer = get_canonicalizer()
        
        # Stats tracking
        self.stats = {
            'candidates_processed': 0,
            'library_loaded': 0,
            'merged': 0,
            'created': 0,
            'needs_review': 0,
            'embeddings_computed': 0,
            'cos_similarities': [],
            'jaccard_similarities': []
        }
        
        logger.info(f"CLUST-3 Consolidator initialized: cos_min={cos_min}, tok_jacc_min={tok_jacc_min}")
    
    def _load_sentence_transformer(self) -> Optional[SentenceTransformer]:
        """Load sentence transformer model for embeddings"""
        try:
            model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded sentence transformer model for embeddings")
            return model
        except Exception as e:
            logger.error(f"Failed to load sentence transformer: {e}")
            return None
    
    def load_candidates(self, conn, window_days: int = 14) -> List[Dict]:
        """Load candidates (consolidation_stage='raw', window days)"""
        cur = conn.cursor()
        try:
            window_start = datetime.now() - timedelta(days=window_days)
            
            cur.execute("""
                SELECT 
                    narrative_id,
                    title,
                    summary,
                    narrative_embedding,
                    activity_timeline,
                    fringe_notes,
                    created_at,
                    article_count
                FROM narratives 
                WHERE consolidation_stage = 'raw'
                AND created_at >= %s
                ORDER BY created_at DESC
            """, (window_start,))
            
            candidates = []
            for row in cur.fetchall():
                candidate = {
                    'narrative_id': row[0],
                    'title': row[1] or '',
                    'summary': row[2] or '',
                    'embedding': row[3],
                    'activity_timeline': row[4] or {},
                    'fringe_notes': row[5] or {},
                    'created_at': row[6],
                    'article_count': row[7] or 1
                }
                candidates.append(candidate)
            
            logger.info(f"Loaded {len(candidates)} candidates (consolidation_stage='raw', {window_days}d window)")
            return candidates
            
        finally:
            cur.close()
    
    def load_library(self, conn, library_days: int = 90) -> List[Dict]:
        """Load library (non-raw narratives, last 90 days)"""
        cur = conn.cursor()
        try:
            library_start = datetime.now() - timedelta(days=library_days)
            
            cur.execute("""
                SELECT 
                    narrative_id,
                    title,
                    summary,
                    narrative_embedding,
                    activity_timeline,
                    fringe_notes,
                    created_at,
                    updated_at,
                    article_count,
                    consolidation_stage
                FROM narratives 
                WHERE consolidation_stage != 'raw'
                AND (created_at >= %s OR updated_at >= %s)
                ORDER BY updated_at DESC NULLS LAST, created_at DESC
            """, (library_start, library_start))
            
            library = []
            for row in cur.fetchall():
                narrative = {
                    'narrative_id': row[0],
                    'title': row[1] or '',
                    'summary': row[2] or '',
                    'embedding': row[3],
                    'activity_timeline': row[4] or {},
                    'fringe_notes': row[5] or {},
                    'created_at': row[6],
                    'updated_at': row[7],
                    'article_count': row[8] or 1,
                    'consolidation_stage': row[9]
                }
                library.append(narrative)
            
            logger.info(f"Loaded {len(library)} library narratives (non-raw, {library_days}d window)")
            return library
            
        finally:
            cur.close()
    
    def ensure_embedding(self, conn, narrative: Dict) -> np.ndarray:
        """Ensure narrative_embedding exists, compute if NULL"""
        if narrative['embedding'] is not None:
            try:
                # Convert from database format to numpy array
                if isinstance(narrative['embedding'], (list, np.ndarray)):
                    return np.array(narrative['embedding'])
                else:
                    # Handle potential string/bytes format
                    return np.array(narrative['embedding'])
            except Exception as e:
                logger.debug(f"Error loading existing embedding for {narrative['narrative_id']}: {e}")
        
        # Compute embedding if NULL or invalid
        if not self.model:
            logger.warning(f"No model available, using zero embedding for {narrative['narrative_id']}")
            return np.zeros(384)  # MiniLM embedding dimension
        
        # Create text for embedding
        text = f"{narrative['title']} {narrative['summary']}"[:512]  # Truncate for model limits
        
        try:
            embedding = self.model.encode([text])[0]
            self.stats['embeddings_computed'] += 1
            
            # Save to database
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE narratives 
                    SET narrative_embedding = %s 
                    WHERE narrative_id = %s
                """, (embedding.tolist(), narrative['narrative_id']))
                conn.commit()
                logger.debug(f"Computed and saved embedding for {narrative['narrative_id']}")
            finally:
                cur.close()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to compute embedding for {narrative['narrative_id']}: {e}")
            return np.zeros(384)
    
    def compute_anchor_tokens(self, narrative: Dict) -> Set[str]:
        """Compute candidate anchor tokens using canonicalizer on title+summary"""
        text = f"{narrative['title']} {narrative['summary']}"
        
        # Extract words and normalize
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Apply canonicalizer to normalize tokens
        canonical_tokens = set()
        for word in words:
            if len(word) >= 3:  # Filter short words
                canonical_word = self.canonicalizer.canonicalize(word)
                if canonical_word != word:  # Only include if canonicalization changed something
                    canonical_tokens.add(canonical_word)
                canonical_tokens.add(word)  # Also include original
        
        # Filter out stop words using canonicalizer's configured stop words
        canonical_tokens = canonical_tokens - self.canonicalizer.stop_words
        
        return canonical_tokens
    
    def extract_countries(self, conn, narrative: Dict) -> Set[str]:
        """Extract countries from narrative text using database-driven geographic keywords"""
        # Use cached country keywords from database if available
        if not hasattr(self, '_country_keywords_cache'):
            self._country_keywords_cache = self._load_country_keywords_from_db(conn)
        
        text = f"{narrative['title']} {narrative['summary']}".lower()
        countries = set()
        
        # Extract tokens and check against database-driven country keywords
        tokens = re.findall(r'\b\w+\b', text)
        for token in tokens:
            canonical = self.canonicalizer.normalize_token(token)
            
            # Check if token or canonical form matches country keywords from DB
            if token in self._country_keywords_cache:
                countries.add(self._country_keywords_cache[token])
            elif canonical in self._country_keywords_cache:
                countries.add(self._country_keywords_cache[canonical])
        
        return countries
    
    def _load_country_keywords_from_db(self, conn) -> Dict[str, str]:
        """Load country-related keywords from database core keywords"""
        cur = conn.cursor()
        try:
            # Get keywords that canonicalize to country forms through the canonicalizer
            # This uses existing canonicalizer mappings rather than hardcoded patterns
            query = """
                SELECT DISTINCT token, canonical_token
                FROM article_core_keywords
                WHERE canonical_token IN (
                    SELECT DISTINCT canonical_token
                    FROM article_core_keywords
                    WHERE token ~ '^[a-z]+$'  -- Single word tokens only
                    AND LENGTH(token) >= 4    -- Reasonable minimum length
                    GROUP BY canonical_token
                    HAVING COUNT(DISTINCT token) >= 2  -- Has synonyms/variants (suggests geographic entities)
                )
                AND (token != canonical_token OR canonical_token ~ '(states|kingdom|republic|federation)')  -- Country indicators
                ORDER BY canonical_token, token
            """
            cur.execute(query)
            
            country_map = {}
            for token, canonical in cur.fetchall():
                # Map token to its canonical country form
                country_map[token] = canonical
                if token != canonical:
                    country_map[canonical] = canonical  # Self-map canonical form
            
            logger.info(f"Loaded {len(country_map)} country keywords from database")
            return country_map
            
        except Exception as e:
            logger.warning(f"Failed to load country keywords from DB: {e}")
            return {}
        finally:
            cur.close()
    
    def compute_cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between embeddings"""
        try:
            dot_product = np.dot(embedding1, embedding2)
            norm_a = np.linalg.norm(embedding1)
            norm_b = np.linalg.norm(embedding2)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
        except Exception as e:
            logger.debug(f"Error computing cosine similarity: {e}")
            return 0.0
    
    def compute_jaccard_tokens(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        """Compute Jaccard similarity for token sets"""
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def compute_country_overlap(self, countries1: Set[str], countries2: Set[str]) -> float:
        """Compute country overlap similarity"""
        if not countries1 or not countries2:
            return 0.0
        
        intersection = len(countries1 & countries2)
        union = len(countries1 | countries2)
        
        return intersection / union if union > 0 else 0.0
    
    def check_alignment_conflict(self, candidate: Dict, library: Dict) -> bool:
        """Check for alignment conflicts between narratives"""
        if not self.align_strict:
            return False
        
        # Simple conflict detection - could be enhanced
        candidate_text = f"{candidate['title']} {candidate['summary']}".lower()
        library_text = f"{library['title']} {library['summary']}".lower()
        
        # Look for opposing sentiment indicators
        positive_words = {'support', 'agree', 'positive', 'good', 'success', 'win', 'peace'}
        negative_words = {'oppose', 'against', 'negative', 'bad', 'fail', 'war', 'conflict'}
        
        candidate_positive = any(word in candidate_text for word in positive_words)
        candidate_negative = any(word in candidate_text for word in negative_words)
        library_positive = any(word in library_text for word in positive_words)
        library_negative = any(word in library_text for word in negative_words)
        
        # Conflict if opposing sentiments
        if (candidate_positive and library_negative) or (candidate_negative and library_positive):
            return True
        
        return False
    
    def find_best_match(self, conn, candidate: Dict, library: List[Dict]) -> Tuple[Optional[Dict], Dict]:
        """Find best library match for candidate"""
        best_match = None
        best_metrics = {
            'cos_similarity': 0.0,
            'jaccard_similarity': 0.0,
            'country_overlap': 0.0,
            'alignment_conflict': False,
            'final_score': 0.0
        }
        
        candidate_embedding = self.ensure_embedding(conn, candidate)
        candidate_tokens = self.compute_anchor_tokens(candidate)
        candidate_countries = self.extract_countries(conn, candidate)
        
        for library_narrative in library:
            # Compute all similarity metrics
            library_embedding = self.ensure_embedding(conn, library_narrative)
            library_tokens = self.compute_anchor_tokens(library_narrative)
            library_countries = self.extract_countries(conn, library_narrative)
            
            cos_sim = self.compute_cosine_similarity(candidate_embedding, library_embedding)
            jaccard_sim = self.compute_jaccard_tokens(candidate_tokens, library_tokens)
            country_overlap = self.compute_country_overlap(candidate_countries, library_countries)
            alignment_conflict = self.check_alignment_conflict(candidate, library_narrative)
            
            # Decision logic as per spec
            meets_threshold = cos_sim >= self.cos_min and jaccard_sim >= self.tok_jacc_min
            
            if meets_threshold and not alignment_conflict:
                # This is a valid match - use cosine as primary, jaccard as tiebreaker
                final_score = cos_sim + (jaccard_sim * 0.1)  # Small tiebreaker weight
                
                if final_score > best_metrics['final_score']:
                    best_match = library_narrative
                    best_metrics = {
                        'cos_similarity': cos_sim,
                        'jaccard_similarity': jaccard_sim,
                        'country_overlap': country_overlap,
                        'alignment_conflict': alignment_conflict,
                        'final_score': final_score
                    }
        
        return best_match, best_metrics
    
    def merge_narratives(self, conn, candidate: Dict, target: Dict, metrics: Dict) -> bool:
        """Merge candidate into target narrative"""
        try:
            cur = conn.cursor()
            
            # Update target narrative with merged content
            merged_timeline = target.get('activity_timeline', {})
            candidate_timeline = candidate.get('activity_timeline', {})
            
            # Merge activity timelines (handle both list and dict formats)
            if candidate_timeline:
                if isinstance(merged_timeline, list) and isinstance(candidate_timeline, list):
                    # Both are lists - concatenate them
                    merged_timeline.extend(candidate_timeline)
                elif isinstance(merged_timeline, dict) and isinstance(candidate_timeline, dict):
                    # Both are dicts - merge them
                    merged_timeline.update(candidate_timeline)
                else:
                    # Mixed formats - convert to list format
                    if isinstance(merged_timeline, dict):
                        merged_timeline = [merged_timeline] if merged_timeline else []
                    if isinstance(candidate_timeline, dict):
                        candidate_timeline = [candidate_timeline] if candidate_timeline else []
                    merged_timeline.extend(candidate_timeline)
                
                # Add consolidation timeline entry
                from datetime import datetime
                consolidation_entry = {
                    "ts": datetime.now().isoformat(),
                    "stage": "clust3", 
                    "action": "narrative_consolidated",
                    "merged_from": candidate['narrative_id']
                }
                
                if isinstance(merged_timeline, list):
                    merged_timeline.append(consolidation_entry)
                else:
                    merged_timeline = [merged_timeline, consolidation_entry]
            
            # Update target with merged data
            cur.execute("""
                UPDATE narratives 
                SET 
                    activity_timeline = %s,
                    updated_at = NOW(),
                    update_status = 'updated'
                WHERE narrative_id = %s
            """, (json.dumps(merged_timeline), target['narrative_id']))
            
            # Archive candidate with merge metadata
            fringe_notes = candidate.get('fringe_notes', {})
            fringe_notes['merged_into'] = target['narrative_id']
            fringe_notes['merge_metrics'] = {
                'cos_similarity': metrics['cos_similarity'],
                'jaccard_similarity': metrics['jaccard_similarity'],
                'merged_at': datetime.now().isoformat()
            }
            
            if self.on_merge == "archive_raw":
                cur.execute("""
                    UPDATE narratives 
                    SET 
                        consolidation_stage = 'archived',
                        fringe_notes = %s,
                        updated_at = NOW()
                    WHERE narrative_id = %s
                """, (json.dumps(fringe_notes), candidate['narrative_id']))
            else:
                # Alternative: delete the candidate row
                cur.execute("DELETE FROM narratives WHERE narrative_id = %s", (candidate['narrative_id'],))
            
            conn.commit()
            cur.close()
            
            # Update stats
            self.stats['merged'] += 1
            self.stats['cos_similarities'].append(metrics['cos_similarity'])
            self.stats['jaccard_similarities'].append(metrics['jaccard_similarity'])
            
            logger.info(f"Merged candidate {candidate['narrative_id']} into {target['narrative_id']} "
                       f"(cos: {metrics['cos_similarity']:.3f}, jaccard: {metrics['jaccard_similarity']:.3f})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error merging narratives: {e}")
            conn.rollback()
            return False
    
    def create_new_narrative(self, conn, candidate: Dict) -> bool:
        """Create new narrative from candidate"""
        try:
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE narratives 
                SET 
                    consolidation_stage = 'consolidated',
                    publication_status = 'draft',
                    updated_at = NOW()
                WHERE narrative_id = %s
            """, (candidate['narrative_id'],))
            
            conn.commit()
            cur.close()
            
            self.stats['created'] += 1
            logger.info(f"Created new narrative from candidate {candidate['narrative_id']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating new narrative: {e}")
            conn.rollback()
            return False
    
    def mark_for_review(self, conn, candidate: Dict, metrics: Dict) -> bool:
        """Mark candidate for manual review (ambiguous band)"""
        try:
            cur = conn.cursor()
            
            fringe_notes = candidate.get('fringe_notes', {})
            fringe_notes['review_reason'] = 'ambiguous_similarity'
            fringe_notes['review_metrics'] = {
                'cos_similarity': metrics['cos_similarity'],
                'jaccard_similarity': metrics['jaccard_similarity'],
                'flagged_at': datetime.now().isoformat()
            }
            
            cur.execute("""
                UPDATE narratives 
                SET 
                    update_status = 'needs_review',
                    fringe_notes = %s,
                    updated_at = NOW()
                WHERE narrative_id = %s
            """, (json.dumps(fringe_notes), candidate['narrative_id']))
            
            conn.commit()
            cur.close()
            
            self.stats['needs_review'] += 1
            logger.info(f"Marked candidate {candidate['narrative_id']} for review "
                       f"(cos: {metrics['cos_similarity']:.3f})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking for review: {e}")
            conn.rollback()
            return False
    
    def apply_size_thresholds(self, candidate: Dict) -> Optional[str]:
        """Apply optional size-based granularity rules"""
        article_count = candidate.get('article_count', 1)
        
        # Parse activity timeline for source and time diversity
        timeline = candidate.get('activity_timeline', {})
        sources = set()
        dates = set()
        
        if 'cluster_evidence' in timeline:
            for evidence in timeline['cluster_evidence']:
                if 'sources' in evidence:
                    sources.update(evidence['sources'])
                if 'time_span' in evidence:
                    dates.add(evidence['time_span'].get('start', ''))
        
        unique_sources = len(sources)
        time_span_days = len(dates)  # Simplified
        
        # Apply rules
        if article_count < 20:
            return "auto_merge_candidate"  # Auto-merge without summary rewrite
        elif article_count >= 50 and unique_sources >= 5 and time_span_days >= 14:
            return "core_candidate"  # Mark as core
        
        return None
    
    def run_consolidation(self, conn, window_days: int, library_days: int, dry_run: bool = False) -> Dict:
        """Run the complete consolidation process"""
        logger.info("Starting CLUST-3 narrative consolidation")
        start_time = datetime.now()
        
        # Step 1: Load candidates and library
        candidates = self.load_candidates(conn, window_days)
        library = self.load_library(conn, library_days)
        
        self.stats['candidates_processed'] = len(candidates)
        self.stats['library_loaded'] = len(library)
        
        if not candidates:
            logger.info("No candidates found for consolidation")
            return self.stats
        
        if not library:
            logger.info("No library narratives found - creating all candidates as new")
            for candidate in candidates:
                if not dry_run:
                    self.create_new_narrative(conn, candidate)
            return self.stats
        
        # Step 2: Process each candidate
        for candidate in candidates:
            logger.debug(f"Processing candidate: {candidate['narrative_id']}")
            
            # Apply size thresholds if available
            size_rule = self.apply_size_thresholds(candidate)
            if size_rule == "auto_merge_candidate":
                logger.debug(f"Candidate {candidate['narrative_id']} qualifies for auto-merge")
            elif size_rule == "core_candidate":
                logger.debug(f"Candidate {candidate['narrative_id']} marked as core")
            
            # Find best match in library
            best_match, metrics = self.find_best_match(conn, candidate, library)
            
            if not dry_run:
                # Apply decision rules
                if best_match and metrics['cos_similarity'] >= self.cos_min and metrics['jaccard_similarity'] >= self.tok_jacc_min:
                    # Merge
                    self.merge_narratives(conn, candidate, best_match, metrics)
                elif best_match and 0.78 <= metrics['cos_similarity'] < self.cos_min:
                    # Ambiguous band - mark for review
                    self.mark_for_review(conn, candidate, metrics)
                else:
                    # Create new
                    self.create_new_narrative(conn, candidate)
            else:
                # Dry run logging
                if best_match:
                    action = "MERGE" if metrics['cos_similarity'] >= self.cos_min and metrics['jaccard_similarity'] >= self.tok_jacc_min else "REVIEW" if metrics['cos_similarity'] >= 0.78 else "CREATE"
                    logger.info(f"DRY RUN: {action} candidate {candidate['narrative_id']} -> {best_match['narrative_id'] if best_match else 'NEW'} "
                               f"(cos: {metrics['cos_similarity']:.3f}, jaccard: {metrics['jaccard_similarity']:.3f})")
                else:
                    logger.info(f"DRY RUN: CREATE candidate {candidate['narrative_id']} -> NEW (no matches)")
        
        # Final stats
        duration = (datetime.now() - start_time).total_seconds()
        self.stats['duration'] = duration
        
        return self.stats
    
    def print_kpis(self):
        """Print KPI summary"""
        print("\n=== CLUST-3 Consolidation Results ===")
        print(f"Candidates processed: {self.stats['candidates_processed']}")
        print(f"Library narratives: {self.stats['library_loaded']}")
        print(f"Merged: {self.stats['merged']}")
        print(f"Created: {self.stats['created']}")
        print(f"Needs review: {self.stats['needs_review']}")
        print(f"Embeddings computed on the fly: {self.stats['embeddings_computed']} ({self.stats['embeddings_computed']/(self.stats['candidates_processed']+self.stats['library_loaded'])*100:.1f}%)")
        
        if self.stats['cos_similarities']:
            cos_median = np.median(self.stats['cos_similarities'])
            cos_mean = np.mean(self.stats['cos_similarities'])
            print(f"Merge cosine similarity - median: {cos_median:.3f}, mean: {cos_mean:.3f}")
        
        if self.stats['jaccard_similarities']:
            jacc_median = np.median(self.stats['jaccard_similarities'])
            jacc_mean = np.mean(self.stats['jaccard_similarities'])
            print(f"Merge Jaccard similarity - median: {jacc_median:.3f}, mean: {jacc_mean:.3f}")
        
        print(f"Duration: {self.stats.get('duration', 0):.1f}s")
        print()


def main():
    """CLI interface matching the specification"""
    parser = argparse.ArgumentParser(
        description="CLUST-3 Narrative Consolidation (Specification Compliant)"
    )
    parser.add_argument(
        "--window_days", 
        type=int, 
        default=14, 
        help="Window for loading raw candidates (default: 14)"
    )
    parser.add_argument(
        "--library_days", 
        type=int, 
        default=90, 
        help="Window for loading library narratives (default: 90)"
    )
    parser.add_argument(
        "--cos_min", 
        type=float, 
        default=0.82, 
        help="Minimum cosine similarity for merge (default: 0.82)"
    )
    parser.add_argument(
        "--tok_jacc_min", 
        type=float, 
        default=0.40, 
        help="Minimum token Jaccard similarity for merge (default: 0.40)"
    )
    parser.add_argument(
        "--align_strict", 
        type=int, 
        default=1, 
        help="Enable strict alignment conflict detection (default: 1)"
    )
    parser.add_argument(
        "--on_merge", 
        choices=["archive_raw", "delete_raw"], 
        default="archive_raw", 
        help="Action for merged candidates (default: archive_raw)"
    )
    parser.add_argument(
        "--dry_run", 
        type=int, 
        default=0, 
        help="Dry run mode - show actions without executing (default: 0)"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize consolidator
    consolidator = CLUST3NarrativeConsolidator(
        cos_min=args.cos_min,
        tok_jacc_min=args.tok_jacc_min,
        align_strict=bool(args.align_strict),
        on_merge=args.on_merge
    )
    
    # Run consolidation
    conn = get_db_connection()
    try:
        stats = consolidator.run_consolidation(
            conn, 
            args.window_days, 
            args.library_days, 
            dry_run=bool(args.dry_run)
        )
        
        # Print KPIs
        consolidator.print_kpis()
        
        # Return success if processing completed
        return 0 if stats['candidates_processed'] >= 0 else 1
        
    except Exception as e:
        logger.error(f"CLUST-3 consolidation failed: {e}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    exit(main())
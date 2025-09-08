#!/usr/bin/env python3
"""
RAI Client Integration
Strategic Narrative Intelligence Platform

Provides HTTP client integration with external RAI validation service for:
- Content safety analysis (bias detection, misinformation flags)  
- Narrative adequacy assessment (evidence, sources, coherence)
- Publication recommendation generation (approve/review/reject)
- Compliance validation against multiple frameworks

Includes comprehensive error handling, retry logic, and fallback analysis.
"""

import hashlib
import json
import logging
import os
import time
from typing import Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RAIUnavailable(Exception):
    """Raised when RAI service is unavailable after all retry attempts."""
    pass


class RAIClient:
    """HTTP client for external RAI validation service."""
    
    def __init__(self):
        """Initialize RAI client with configuration from environment."""
        self.enabled = os.getenv('RAI_ENABLED', 'false').lower() == 'true'
        self.base_url = os.getenv('RAI_BASE_URL', 'http://localhost:8000')
        self.api_key = os.getenv('RAI_API_KEY', '')
        self.timeout = int(os.getenv('RAI_TIMEOUT', 15))
        self.max_retries = int(os.getenv('RAI_RETRIES', 3))
        
        # Configure session with retry strategy
        self.session = requests.Session()
        
        # Retry strategy: exponential backoff for 429, 500, 502, 503, 504
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST", "OPTIONS"],
            backoff_factor=1  # 1, 2, 4 second delays
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"RAI Client initialized: enabled={self.enabled}, base_url={self.base_url}")

    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for RAI service requests."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'SNI-RAI-Client/1.0'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers

    def check_service_health(self) -> bool:
        """Check if RAI service is available and healthy."""
        if not self.enabled:
            return False
            
        try:
            health_url = f"{self.base_url}/health"
            response = self.session.get(health_url, timeout=self.timeout)
            is_healthy = response.status_code == 200
            
            if is_healthy:
                logger.debug("RAI service health check passed")
            else:
                logger.warning(f"RAI service health check failed: {response.status_code}")
                
            return is_healthy
            
        except Exception as e:
            logger.warning(f"RAI service health check failed: {e}")
            return False

    def create_payload(self, narrative: Dict) -> Dict:
        """Create RAI analysis payload from narrative data."""
        # Extract excerpts with proper formatting
        excerpts = []
        top_excerpts = narrative.get('top_excerpts', [])
        
        if isinstance(top_excerpts, list):
            for excerpt in top_excerpts[:3]:  # Limit to top 3
                if isinstance(excerpt, dict):
                    excerpts.append({
                        'article_id': str(excerpt.get('article_id', 'unknown')),
                        'source': excerpt.get('source', 'Unknown Source'),
                        'quote': excerpt.get('quote', excerpt.get('text', ''))[:500]  # Truncate long quotes
                    })
                elif isinstance(excerpt, str):
                    excerpts.append({
                        'article_id': 'text_excerpt',
                        'source': 'Narrative Content',
                        'quote': excerpt[:500]
                    })
        
        # Extract evidence statistics
        source_stats = narrative.get('source_stats', {})
        if isinstance(source_stats, str):
            try:
                source_stats = json.loads(source_stats)
            except:
                source_stats = {}
        
        evidence = {
            'articles': source_stats.get('articles', 1),
            'sources': source_stats.get('sources', 1),
            'quality_score': source_stats.get('quality_score', 0.5),
            'source_diversity': source_stats.get('source_diversity', 0.5)
        }
        
        # Create comprehensive payload
        payload = {
            'title': narrative.get('title', 'Untitled Narrative'),
            'summary': narrative.get('summary', 'No summary available'),
            'excerpts': excerpts,
            'evidence': evidence,
            'metadata': {
                'narrative_id': narrative.get('narrative_id', f"N-{narrative.get('id', 'unknown')}"),
                'language': 'EN',
                'consolidation_stage': narrative.get('consolidation_stage', 'consolidated'),
                'created_at': narrative.get('created_at', '').isoformat() if hasattr(narrative.get('created_at', ''), 'isoformat') else str(narrative.get('created_at', ''))
            }
        }
        
        return payload

    def analyze_narrative(self, payload: Dict) -> Dict:
        """Send narrative to RAI service for comprehensive analysis."""
        if not self.enabled:
            logger.info("RAI service disabled, using local fallback analysis")
            return self.local_fallback_analysis(payload)
        
        if not self.check_service_health():
            logger.warning("RAI service unhealthy, using local fallback analysis")
            return self.local_fallback_analysis(payload)
        
        try:
            # Make RAI service request
            analyze_url = f"{self.base_url}/analyze"
            headers = self.get_headers()
            
            logger.debug(f"Sending narrative to RAI service: {payload['metadata']['narrative_id']}")
            
            response = self.session.post(
                analyze_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                analysis_result = response.json()
                logger.info(f"RAI analysis completed for {payload['metadata']['narrative_id']}")
                return self.validate_analysis_result(analysis_result)
                
            elif response.status_code == 429:
                logger.warning(f"RAI service rate limited (429), using fallback")
                return self.local_fallback_analysis(payload)
                
            else:
                logger.error(f"RAI service error {response.status_code}: {response.text}")
                raise RAIUnavailable(f"RAI service returned {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"RAI service request failed: {e}")
            raise RAIUnavailable(f"RAI service unavailable: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error in RAI analysis: {e}")
            return self.local_fallback_analysis(payload)

    def validate_analysis_result(self, result: Dict) -> Dict:
        """Validate and sanitize RAI analysis result."""
        # Ensure required fields exist with defaults
        validated = {
            'adequacy_score': float(result.get('adequacy_score', 0.5)),
            'confidence_rating': float(result.get('confidence_rating', 0.5)),
            'premise_lenses': result.get('premise_lenses', ['general']),
            'bias_flags': result.get('bias_flags', []),
            'blind_spots': result.get('blind_spots', []),
            'notes': result.get('notes', 'RAI analysis completed'),
            'service_analysis': True  # Flag indicating external service was used
        }
        
        # Validate score ranges (0.0-1.0)
        validated['adequacy_score'] = max(0.0, min(1.0, validated['adequacy_score']))
        validated['confidence_rating'] = max(0.0, min(1.0, validated['confidence_rating']))
        
        # Validate list fields
        if not isinstance(validated['premise_lenses'], list):
            validated['premise_lenses'] = ['general']
        if not isinstance(validated['bias_flags'], list):
            validated['bias_flags'] = []
        if not isinstance(validated['blind_spots'], list):
            validated['blind_spots'] = []
        
        logger.debug(f"Validated RAI result: adequacy={validated['adequacy_score']}, confidence={validated['confidence_rating']}")
        return validated

    def local_fallback_analysis(self, payload: Dict) -> Dict:
        """Provide local fallback analysis when RAI service is unavailable."""
        logger.info(f"Performing local fallback analysis for {payload['metadata']['narrative_id']}")
        
        title = payload.get('title', '')
        summary = payload.get('summary', '')
        evidence = payload.get('evidence', {})
        
        # Simple heuristic-based analysis
        title_words = len(title.split())
        summary_words = len(summary.split())
        excerpt_count = len(payload.get('excerpts', []))
        
        # Calculate basic adequacy score
        adequacy_factors = [
            min(1.0, title_words / 10.0),  # Title completeness
            min(1.0, summary_words / 50.0),  # Summary completeness  
            min(1.0, excerpt_count / 3.0),  # Evidence excerpts
            min(1.0, evidence.get('sources', 1) / 5.0),  # Source diversity
            min(1.0, evidence.get('articles', 1) / 10.0)  # Article coverage
        ]
        adequacy_score = sum(adequacy_factors) / len(adequacy_factors)
        
        # Calculate confidence based on evidence quality
        confidence_rating = evidence.get('quality_score', 0.5) * evidence.get('source_diversity', 0.5)
        
        # Basic premise lens classification
        premise_lenses = ['general']
        if any(word in title.lower() + summary.lower() for word in ['military', 'defense', 'security']):
            premise_lenses.append('security')
        if any(word in title.lower() + summary.lower() for word in ['economic', 'trade', 'financial']):
            premise_lenses.append('economic')
        if any(word in title.lower() + summary.lower() for word in ['diplomatic', 'negotiations', 'agreement']):
            premise_lenses.append('diplomatic')
        
        # Basic bias flag detection
        bias_flags = []
        if evidence.get('sources', 1) < 2:
            bias_flags.append('limited_sources')
        if summary_words < 20:
            bias_flags.append('insufficient_context')
        
        # Basic blind spot identification
        blind_spots = []
        if 'economic' not in premise_lenses and any(word in title.lower() for word in ['sanctions', 'trade']):
            blind_spots.append('missing economic analysis')
        if evidence.get('sources', 1) < 3:
            blind_spots.append('limited source diversity')
        
        return {
            'adequacy_score': round(adequacy_score, 3),
            'confidence_rating': round(confidence_rating, 3),
            'premise_lenses': premise_lenses,
            'bias_flags': bias_flags,
            'blind_spots': blind_spots,
            'notes': 'Local fallback analysis - RAI service unavailable',
            'service_analysis': False  # Flag indicating local analysis was used
        }

    def calculate_input_hash(self, payload: Dict) -> str:
        """Calculate SHA256 hash of input payload for idempotency."""
        # Create stable hash from key content
        hash_content = {
            'title': payload.get('title', ''),
            'summary': payload.get('summary', ''),
            'excerpt_count': len(payload.get('excerpts', [])),
            'evidence': payload.get('evidence', {})
        }
        
        content_str = json.dumps(hash_content, sort_keys=True)
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()[:16]


def test_rai_integration():
    """Test RAI client integration with sample data."""
    print("Testing RAI Client Integration...")
    
    client = RAIClient()
    
    # Test service health
    print(f"RAI Enabled: {client.enabled}")
    print(f"Service Health: {client.check_service_health()}")
    
    # Test analysis with sample narrative
    sample_narrative = {
        'id': 12345,
        'narrative_id': 'TEST-NARRATIVE-001',
        'title': 'U.S. sanctions on Russia escalate economic tensions amid diplomatic negotiations',
        'summary': 'Recent sanctions imposed by the United States on Russian energy sectors have significantly escalated economic tensions between the two nations. Diplomatic negotiations continue despite the mounting pressure.',
        'top_excerpts': [
            {'article_id': 'art1', 'source': 'Reuters', 'quote': 'The sanctions target key energy infrastructure'},
            {'article_id': 'art2', 'source': 'AP News', 'quote': 'Diplomatic channels remain open despite tensions'},
            {'article_id': 'art3', 'source': 'BBC', 'quote': 'Economic impact expected to be significant'}
        ],
        'source_stats': {
            'articles': 8,
            'sources': 3,
            'quality_score': 0.8,
            'source_diversity': 0.75
        },
        'consolidation_stage': 'consolidated',
        'created_at': '2025-08-27T12:00:00Z'
    }
    
    try:
        payload = client.create_payload(sample_narrative)
        print(f"Created payload for: {payload['metadata']['narrative_id']}")
        
        analysis = client.analyze_narrative(payload)
        print(f"Analysis completed:")
        print(f"  Adequacy Score: {analysis['adequacy_score']}")
        print(f"  Confidence Rating: {analysis['confidence_rating']}")
        print(f"  Premise Lenses: {analysis['premise_lenses']}")
        print(f"  Bias Flags: {analysis['bias_flags']}")
        print(f"  Service Analysis: {analysis['service_analysis']}")
        
        input_hash = client.calculate_input_hash(payload)
        print(f"  Input Hash: {input_hash}")
        
        print("RAI Client test completed successfully!")
        return True
        
    except Exception as e:
        print(f"RAI Client test failed: {e}")
        return False


if __name__ == "__main__":
    # Run integration test when executed directly
    success = test_rai_integration()
    exit(0 if success else 1)
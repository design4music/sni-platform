#!/usr/bin/env python3
"""
Database-Driven Canonicalizer (Lightweight)
Strategic Narrative Intelligence ETL Pipeline

Lightweight database-driven canonicalizer for use in keyword extraction.
Replaces hardcoded vocabularies with database lookups.
"""

import logging
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class DatabaseCanonicalizer:
    """Lightweight database-driven canonicalizer for keyword extraction."""
    
    def __init__(self, conn):
        self.conn = conn
        self.exact_mappings: Dict[str, str] = {}
        self.lower_mappings: Dict[str, str] = {}
        self.regex_patterns: List[Tuple[re.Pattern, str]] = []
        self._load_mappings()
    
    def _load_mappings(self):
        """Load active mappings from database."""
        logger.debug("Loading canonical mappings from database...")
        
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            query = """
                SELECT pattern, pattern_type, canon_text as canon_token, priority
                FROM keyword_canon_map 
                WHERE is_active = TRUE 
                ORDER BY priority ASC
            """
            cur.execute(query)
            mappings = cur.fetchall()
            
            for mapping in mappings:
                pattern = mapping['pattern']
                pattern_type = mapping['pattern_type']
                canon_token = mapping['canon_token']
                
                if pattern_type == 'exact':
                    self.exact_mappings[pattern] = canon_token
                elif pattern_type == 'lower':
                    self.lower_mappings[pattern.lower()] = canon_token
                elif pattern_type == 'regex':
                    try:
                        compiled_pattern = re.compile(pattern, re.IGNORECASE)
                        self.regex_patterns.append((compiled_pattern, canon_token))
                    except re.error as e:
                        logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            
            logger.debug(
                f"Loaded {len(self.exact_mappings)} exact, "
                f"{len(self.lower_mappings)} lower, {len(self.regex_patterns)} regex mappings"
            )
            
        finally:
            cur.close()
    
    def normalize_text_basic(self, text: str) -> str:
        """Apply basic text normalization."""
        if not text:
            return ""
        
        # Unicode normalization and lowercase
        normalized = unicodedata.normalize('NFKC', text).lower()
        
        # Remove dots from acronyms
        normalized = normalized.replace('.', '')
        
        # Remove punctuation except hyphens and slashes
        normalized = re.sub(r'[^\w\s/-]', '', normalized)
        
        # Collapse spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Handle hyphen variants
        normalized = re.sub(r'([a-zA-Z])\s*[-]\s*(\d)', r'\1-\2', normalized)
        
        return normalized.strip()
    
    def normalize_token(self, text: str) -> str:
        """Main normalization with database lookup."""
        if not text:
            return ""
        
        normalized = self.normalize_text_basic(text)
        
        # Apply database mappings in order of precedence
        
        # 1. Exact matches
        if normalized in self.exact_mappings:
            return self.exact_mappings[normalized]
        
        # 2. Lower case matches
        if normalized in self.lower_mappings:
            return self.lower_mappings[normalized]
        
        # 3. Regex matches
        for pattern, canon_token in self.regex_patterns:
            match = pattern.search(normalized)
            if match:
                # Handle capture groups for generic patterns
                if '\\2' in canon_token and len(match.groups()) >= 2:
                    return match.group(2)
                else:
                    return canon_token
        
        # 4. Identity fallback
        return normalized
    
    def should_keep_keyword(self, text: str) -> bool:
        """Basic keyword filtering."""
        if not text or len(text.strip()) <= 1:
            return False
        
        normalized = self.normalize_text_basic(text)
        
        # Filter obvious stopwords and noise
        if normalized in {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}:
            return False
        
        if normalized.isdigit():
            return False
        
        return True
    
    def normalize_and_canonicalize(self, text: str) -> Tuple[str, str, float]:
        """
        Normalize text and return canonical form.
        
        Returns:
            Tuple of (normalized_text, canonical_text, confidence)
        """
        if not text:
            return "", "", 0.0
        
        normalized = self.normalize_text_basic(text)
        
        if not self.should_keep_keyword(normalized):
            return normalized, "", 0.0  # Empty canonical means filtered out
        
        canonical = self.normalize_token(text)
        confidence = 1.0 if canonical != normalized else 0.8
        
        return normalized, canonical, confidence
    
    def batch_normalize(self, keywords: List[str]) -> List[Tuple[str, str, str, float]]:
        """
        Batch normalize keywords.
        
        Returns:
            List of (original, normalized, canonical, confidence) tuples
        """
        results = []
        for keyword in keywords:
            normalized, canonical, confidence = self.normalize_and_canonicalize(keyword)
            if canonical:  # Only include if not filtered out
                results.append((keyword, normalized, canonical, confidence))
        return results


# Global instance cache
_global_db_canonicalizer = None


def get_db_canonicalizer(conn=None) -> DatabaseCanonicalizer:
    """Get or create database canonicalizer instance."""
    global _global_db_canonicalizer
    
    if _global_db_canonicalizer is None or conn is not None:
        if conn is None:
            # Create connection if none provided
            import os
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                database=os.getenv("DB_NAME", "narrative_intelligence"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
            )
        _global_db_canonicalizer = DatabaseCanonicalizer(conn)
    
    return _global_db_canonicalizer


if __name__ == "__main__":
    # Test the database canonicalizer
    import os
    
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "narrative_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )
    
    canonicalizer = DatabaseCanonicalizer(conn)
    
    test_cases = [
        "U.S.",
        "President Trump", 
        "russian",
        "F-16",
        "NATO",
        "Prime Minister Netanyahu",
        "9/11",
        "negotiation",
    ]
    
    print("=== Database-Driven Canonicalization Test ===")
    for text in test_cases:
        norm, canon, conf = canonicalizer.normalize_and_canonicalize(text)
        print(f"'{text}' -> '{norm}' -> '{canon}' (conf: {conf:.1f})")
    
    conn.close()
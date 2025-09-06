"""
CLUST-001: Strategic Gate Filtering
Pure function implementation with externalized vocabulary (no embedded taxonomies)

Logic:
- Keep if: (a) actor alias match OR (b) embedding similarity >= threshold to mechanism anchors
- No domain exclusions (all feeds are curated strategic sources)
- Optimized with batch encoding and precompiled regex patterns
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple, Pattern
import re
import numpy as np
from sentence_transformers import SentenceTransformer
import unicodedata

from core.config import get_config
from apps.clust1.vocab_loader import load_actor_aliases, load_mechanism_anchors


@dataclass
class GateResult:
    """Result of strategic gate filtering with telemetry"""
    keep: bool
    score: float                                    # max cosine similarity observed (or 0.99 for actor_hit)
    reason: str                                     # "actor_hit" | "anchor_sim" | "below_threshold"
    anchor_labels: List[str]                        # labels that cleared the threshold (deduped)
    anchor_scores: List[Tuple[str, float]]          # top-k (label, score) for telemetry
    actor_hit: Optional[str] = None                 # canonical actor code (e.g., "US")


class StrategicGate:
    """Strategic Gate Filter - determines if headlines have strategic relevance"""
    
    def __init__(self):
        self.config = get_config()
        self._validate_config()
        
        # Load vocabularies with validation
        try:
            self._actor_aliases = load_actor_aliases(self.config.actors_csv_path)
            self._mech = load_mechanism_anchors(self.config.mechanisms_json_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load vocabularies: {e}")
        
        if not self._mech.labels:
            raise ValueError("No mechanism labels found - check mechanisms.json file")
        
        # Model and embeddings (lazy initialization)
        self._model: Optional[SentenceTransformer] = None
        self._anchor_labels: List[str] = self._mech.labels
        self._anchor_centroids: Optional[np.ndarray] = None
        
        # Precompiled regex patterns for actor matching
        self._actor_patterns: List[Tuple[str, str, Optional[Pattern], bool]] = []
        self._compile_actor_patterns()
    
    def _validate_config(self):
        """Validate required config parameters exist"""
        required_attrs = ['embedding_model', 'cosine_threshold_gate', 'actors_csv_path', 'mechanisms_json_path']
        for attr in required_attrs:
            if not hasattr(self.config, attr):
                raise ValueError(f"Missing required config parameter: {attr}")
    
    def _has_cjk_chars(self, text: str) -> bool:
        """Check if text contains CJK characters"""
        return any('\u4e00' <= char <= '\u9fff' or  # Chinese
                  '\u3040' <= char <= '\u309f' or  # Hiragana
                  '\u30a0' <= char <= '\u30ff' or  # Katakana
                  '\uac00' <= char <= '\ud7af'     # Hangul
                  for char in text)
    
    def _compile_actor_patterns(self):
        """Precompile regex patterns for actor alias matching"""
        for entity_id, aliases in self._actor_aliases.items():
            for alias in aliases:
                alias_lower = alias.strip().lower()
                # Check if alias contains CJK characters
                has_cjk = self._has_cjk_chars(alias)
                
                if has_cjk or ' ' not in alias_lower:
                    # For CJK or single-word aliases, use simple case-insensitive substring
                    self._actor_patterns.append((entity_id, alias_lower, None, True))
                else:
                    # For Latin script with spaces, use word boundary regex
                    pattern = re.compile(r'\b' + re.escape(alias_lower) + r'\b', re.IGNORECASE)
                    self._actor_patterns.append((entity_id, alias_lower, pattern, False))
    
    def _init_model(self) -> None:
        """Initialize sentence transformer model and compute anchor centroids lazily"""
        if self._model is None:
            self._model = SentenceTransformer(self.config.embedding_model)
            self._compute_anchor_centroids()
    
    def _compute_anchor_centroids(self) -> None:
        """Pre-compute normalized centroids for all mechanism anchor phrases"""
        texts: List[str] = []
        offsets: List[Tuple[str, int, int]] = []  # (label, start_idx, end_idx)
        
        for label in self._anchor_labels:
            phrases = self._mech.centroids_texts.get(label, [])
            if not phrases:  # Skip labels with no anchor phrases
                continue
                
            start = len(texts)
            texts.extend(phrases)
            offsets.append((label, start, len(texts)))
        
        if not texts:
            raise ValueError("No anchor phrases found across all mechanisms")
        
        # Encode all anchor phrases with normalization
        embs = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        
        # Compute normalized centroid for each mechanism
        centroids = []
        valid_labels = []
        
        for label, s, e in offsets:
            centroid = embs[s:e].mean(axis=0)
            # Re-normalize centroid
            norm = np.linalg.norm(centroid)
            if norm > 1e-12:  # Avoid division by zero
                centroid /= norm
                centroids.append(centroid)
                valid_labels.append(label)
        
        if not centroids:
            raise ValueError(
                "StrategicGate: mechanisms.json yielded no valid anchor centroids. "
                "Check that each label has ≥1 non-empty anchor phrase."
            )
        
        self._anchor_centroids = np.vstack(centroids)
        self._anchor_labels = valid_labels
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text to match title_norm processing"""
        if not text:
            return ""
        
        # NFKC Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Lowercase and collapse whitespace
        text = re.sub(r'\s+', ' ', text.lower()).strip()
        
        return text
    
    def _actor_match(self, text: str) -> Optional[str]:
        """Check if text contains any actor aliases with optimized pattern matching"""
        text_lower = text.lower()
        
        for entity_id, alias_lower, pattern, is_substring in self._actor_patterns:
            if is_substring:
                # Single alias substring check, no re-lookup
                if alias_lower in text_lower:
                    return entity_id
            else:
                # Regex word boundary matching
                if pattern and pattern.search(text_lower):
                    return entity_id
        
        return None
    
    def _anchor_similarity(self, normalized_text: str) -> Tuple[float, List[str], List[Tuple[str, float]]]:
        """Compute similarity to mechanism anchor centroids with telemetry"""
        self._init_model()
        
        # Encode input text with normalization
        vec = self._model.encode([normalized_text], convert_to_numpy=True, normalize_embeddings=True)
        
        # Compute cosine similarities to all mechanism centroids
        similarities = (vec @ self._anchor_centroids.T).flatten()
        
        # Get threshold from config with defensive clamping
        try:
            threshold = max(0.0, min(1.0, float(self.config.cosine_threshold_gate)))
        except Exception:
            threshold = 0.70
        max_score = float(similarities.max()) if similarities.size else 0.0
        
        # Labels that cleared threshold
        fired_labels = [self._anchor_labels[i] for i, sim in enumerate(similarities) if sim >= threshold]
        
        # Top-K scores for telemetry (default top 3)
        max_top_anchors = getattr(self.config, 'max_top_anchors', 3)
        top_indices = np.argsort(similarities)[-max_top_anchors:][::-1]  # Descending order
        top_scores = [(self._anchor_labels[i], float(similarities[i])) for i in top_indices]
        
        return max_score, fired_labels, top_scores
    
    def filter_title(self, title_text: str) -> GateResult:
        """
        Apply strategic gate filtering to a single title.
        
        Args:
            title_text: The title text to evaluate (will be normalized)
            
        Returns:
            GateResult with filtering decision and telemetry
        """
        # Normalize input text
        normalized_text = self._normalize_text(title_text)
        
        if not normalized_text:
            return GateResult(False, 0.0, "below_threshold", [], [])
        
        # Check for actor matches first (fast path)
        actor_hit = self._actor_match(normalized_text)
        if actor_hit:
            return GateResult(
                keep=True,
                score=0.99,  # Slightly below 1.0 to distinguish from true cosine-1.0
                reason="actor_hit",
                anchor_labels=[],
                anchor_scores=[],
                actor_hit=actor_hit
            )
        
        # Check anchor similarity (slower path)
        score, fired_labels, top_scores = self._anchor_similarity(normalized_text)
        
        if fired_labels:  # Any mechanism above threshold
            return GateResult(
                keep=True,
                score=score,
                reason="anchor_sim",
                anchor_labels=fired_labels,
                anchor_scores=top_scores
            )
        
        # Below threshold
        return GateResult(
            keep=False,
            score=score,
            reason="below_threshold",
            anchor_labels=[],
            anchor_scores=top_scores
        )


def filter_titles_batch(titles: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], GateResult]]:
    """
    Batch filter titles through strategic gate with optimized batch encoding.
    
    Args:
        titles: List of title dictionaries with 'title_norm' or 'title_display' fields
        
    Returns:
        List of (title, gate_result) tuples
    """
    if not titles:
        return []
    
    gate = StrategicGate()
    results = []
    
    # Prepare texts for batch processing
    texts = []
    actor_hits = []  # Track which titles have actor hits (skip embedding for these)
    
    for title in titles:
        # Use title_norm if available, fallback to title_display
        title_text = title.get("title_norm") or title.get("title_display", "")
        normalized_text = gate._normalize_text(title_text)
        
        # Check for actor match first
        actor_hit = gate._actor_match(normalized_text) if normalized_text else None
        actor_hits.append(actor_hit)
        
        texts.append(normalized_text)
    
    # Batch encode only texts without actor hits
    texts_to_encode = [(i, text) for i, text in enumerate(texts) if not actor_hits[i] and text]
    
    if texts_to_encode:
        gate._init_model()  # Ensure model is loaded
        indices, batch_texts = zip(*texts_to_encode)
        
        # Batch encode with normalization
        batch_embeddings = gate._model.encode(
            list(batch_texts), 
            convert_to_numpy=True, 
            normalize_embeddings=True
        )
        
        # Compute similarities for entire batch at once
        batch_similarities = batch_embeddings @ gate._anchor_centroids.T  # (N, L)
    else:
        indices, batch_similarities = [], np.array([])
    
    # Process results - clamp threshold defensively  
    try:
        threshold = max(0.0, min(1.0, float(gate.config.cosine_threshold_gate)))
    except Exception:
        threshold = 0.70
    max_top_anchors = getattr(gate.config, 'max_top_anchors', 3)
    batch_idx = 0
    
    for i, title in enumerate(titles):
        if actor_hits[i]:
            # Actor hit case
            result = GateResult(
                keep=True,
                score=0.99,
                reason="actor_hit",
                anchor_labels=[],
                anchor_scores=[],
                actor_hit=actor_hits[i]
            )
        elif not texts[i]:
            # Empty text case
            result = GateResult(False, 0.0, "below_threshold", [], [])
        else:
            # Anchor similarity case
            similarities = batch_similarities[batch_idx]
            batch_idx += 1
            
            max_score = float(similarities.max()) if similarities.size else 0.0
            fired_labels = [gate._anchor_labels[j] for j, sim in enumerate(similarities) if sim >= threshold]
            
            # Top scores for telemetry
            top_indices = np.argsort(similarities)[-max_top_anchors:][::-1]
            top_scores = [(gate._anchor_labels[j], float(similarities[j])) for j in top_indices]
            
            result = GateResult(
                keep=bool(fired_labels),
                score=max_score,
                reason="anchor_sim" if fired_labels else "below_threshold",
                anchor_labels=fired_labels,
                anchor_scores=top_scores
            )
        
        results.append((title, result))
    
    return results
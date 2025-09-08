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
from apps.clust1.vocab_loader import load_mechanism_anchors
from apps.clust1.actor_extractor import create_actor_extractor


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
            self._actor_extractor = create_actor_extractor()
            self._mech = load_mechanism_anchors(self.config.mechanisms_json_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load vocabularies: {e}")
        
        if not self._mech.labels:
            raise ValueError("No mechanism labels found - check mechanisms.json file")
        
        # Model and embeddings (lazy initialization)
        self._model: Optional[SentenceTransformer] = None
        self._anchor_labels: List[str] = self._mech.labels
        self._anchor_centroids: Optional[np.ndarray] = None
    
    def _validate_config(self):
        """Validate required config parameters exist"""
        required_attrs = ['embedding_model', 'cosine_threshold_gate', 'actors_csv_path', 'mechanisms_json_path']
        for attr in required_attrs:
            if not hasattr(self.config, attr):
                raise ValueError(f"Missing required config parameter: {attr}")
    
    
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
        # Normalize input text using shared normalization
        normalized_text = self._actor_extractor.normalize(title_text)
        
        if not normalized_text:
            return GateResult(False, 0.0, "below_threshold", [], [])
        
        # Check for actor matches first (fast path) using shared extractor
        actor_hit = self._actor_extractor.first_hit(title_text)
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
        normalized_text = gate._actor_extractor.normalize(title_text)
        
        # Check for actor match first using shared extractor
        actor_hit = gate._actor_extractor.first_hit(title_text) if title_text else None
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
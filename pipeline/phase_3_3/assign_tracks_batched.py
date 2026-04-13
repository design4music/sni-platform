"""
DEPRECATED: LLM-based Phase 3.3 intel gating + track assignment.

Removed in ELO v3.0 (2026-04-13). Replaced by:
    pipeline.phase_3_3.assign_tracks_mechanical.process_batch

Exclusion (previously via INTEL_GATING_PROMPT) is now handled at Phase 3.1 by
labeling out-of-scope titles with sector = NON_STRATEGIC in the label extraction
prompt. Track assignment for accepted titles is a mechanical lookup from
sector -> track.

If you see this import, update the caller to use assign_tracks_mechanical
instead. This module intentionally raises on import to prevent silent use.
"""

raise ImportError(
    "pipeline.phase_3_3.assign_tracks_batched is deprecated (ELO v3.0). "
    "Use pipeline.phase_3_3.assign_tracks_mechanical.process_batch instead. "
    "See docs/context/BEATS_DIRECTION.md and BEATS_TAXONOMY_V3_DRAFT.md."
)

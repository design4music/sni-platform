"""
DEPRECATED: reprocess blocked_llm titles through the old LLM gating prompt.

Removed in ELO v3.0 (2026-04-13). The new architecture treats exclusion as a
label (sector = NON_STRATEGIC) set at Phase 3.1, not a separate gating decision.
There is no longer a meaningful "reprocess through improved gating" workflow;
if the Phase 3.1 prompt improves, you re-run label extraction directly.

To reprocess previously-blocked titles under the new taxonomy, clear
processing_status to 'pending' for the relevant rows and re-run Phase 3.1
(pipeline.phase_3_1.extract_labels.process_batch).
"""

raise ImportError(
    "pipeline.phase_3_3.reprocess_blocked_llm is deprecated (ELO v3.0). "
    "Re-run Phase 3.1 label extraction to reprocess under the new taxonomy."
)

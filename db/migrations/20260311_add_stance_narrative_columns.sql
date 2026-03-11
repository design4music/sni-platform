-- Add stance-clustered extraction metadata to narratives table.
-- These columns are NULL for legacy extractions (backwards compatible).

ALTER TABLE narratives ADD COLUMN IF NOT EXISTS extraction_method TEXT;
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS cluster_label TEXT;
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS cluster_publishers TEXT[];
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS cluster_score_avg REAL;

COMMENT ON COLUMN narratives.extraction_method IS 'legacy | stance_clustered';
COMMENT ON COLUMN narratives.cluster_label IS 'critical | reportorial | supportive (stance bucket)';
COMMENT ON COLUMN narratives.cluster_publishers IS 'Publishers assigned to this stance cluster';
COMMENT ON COLUMN narratives.cluster_score_avg IS 'Mean stance score of cluster publishers';

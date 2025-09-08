-- CLUST-1.5: Add Strategic Gate decision columns to titles table
-- Migration: 031_add_gate_decision_columns.sql

-- Add gate decision columns to existing titles table
ALTER TABLE titles ADD COLUMN IF NOT EXISTS gate_keep boolean NOT NULL DEFAULT false;
ALTER TABLE titles ADD COLUMN IF NOT EXISTS gate_reason text NULL;
ALTER TABLE titles ADD COLUMN IF NOT EXISTS gate_score real NULL;
ALTER TABLE titles ADD COLUMN IF NOT EXISTS gate_anchor_labels text[] NULL;
ALTER TABLE titles ADD COLUMN IF NOT EXISTS gate_actor_hit text NULL;
ALTER TABLE titles ADD COLUMN IF NOT EXISTS gate_at timestamptz NULL;

-- Create index on gate processing status for efficient batch queries
CREATE INDEX IF NOT EXISTS idx_titles_gate_processing 
ON titles(processing_status, gate_at) 
WHERE processing_status = 'pending' AND gate_at IS NULL;

-- Create index on gate decisions for analytics
CREATE INDEX IF NOT EXISTS idx_titles_gate_decisions 
ON titles(gate_keep, gate_reason, gate_at) 
WHERE gate_at IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN titles.gate_keep IS 'Strategic Gate decision: true if title passes strategic relevance filter';
COMMENT ON COLUMN titles.gate_reason IS 'Gate decision reason: actor_hit | anchor_sim | below_threshold';
COMMENT ON COLUMN titles.gate_score IS 'Gate similarity score (0.99 for actor_hit, cosine sim for anchor_sim)';
COMMENT ON COLUMN titles.gate_anchor_labels IS 'Mechanism anchor labels that fired above threshold';
COMMENT ON COLUMN titles.gate_actor_hit IS 'Canonical actor code if actor alias matched (e.g., US, CN, EU)';
COMMENT ON COLUMN titles.gate_at IS 'Timestamp when Strategic Gate processing completed';
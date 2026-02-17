-- Migration: Add signal stats and RAI signals columns to narratives
-- Date: 2026-02-18
-- Purpose: Tier 1 (pre-computed stats) + Tier 2 (RAI-interpreted signals) storage

ALTER TABLE narratives ADD COLUMN IF NOT EXISTS signal_stats JSONB;
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS rai_signals JSONB;
ALTER TABLE narratives ADD COLUMN IF NOT EXISTS rai_signals_at TIMESTAMPTZ;

COMMENT ON COLUMN narratives.signal_stats IS 'Tier 1: pre-computed coverage stats (publisher HHI, language dist, etc.)';
COMMENT ON COLUMN narratives.rai_signals IS 'Tier 2: RAI-interpreted compact signals (no HTML)';
COMMENT ON COLUMN narratives.rai_signals_at IS 'Timestamp of last signals analysis';

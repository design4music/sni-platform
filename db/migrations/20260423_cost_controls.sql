-- 2026-04-23 LLM cost controls
-- 1) llm_stats: per-phase token accounting (new)
-- 2) daemon_state: persist slot last_run across restarts (new)
-- 3) centroid_summaries.source_fingerprint: content-based regeneration trigger

-- ---------------------------------------------------------------------------
-- llm_stats
-- ---------------------------------------------------------------------------
-- Best-effort telemetry written on every LLM call. Never gates pipeline.
-- Expected rows: ~1000-5000/day. Retain last 90 days (operational query tool,
-- not a billing log). Rolling purge handled by daily purge slot if needed.

CREATE TABLE IF NOT EXISTS llm_stats (
    id           bigserial   PRIMARY KEY,
    phase        text        NOT NULL,
    tokens_in    integer,
    tokens_out   integer,
    latency_ms   integer,
    model        text        DEFAULT 'deepseek-chat',
    status       text        DEFAULT 'ok',   -- ok | error | timeout
    created_at   timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS llm_stats_created_idx
    ON llm_stats(created_at DESC);

CREATE INDEX IF NOT EXISTS llm_stats_phase_created_idx
    ON llm_stats(phase, created_at DESC);

-- ---------------------------------------------------------------------------
-- daemon_state
-- ---------------------------------------------------------------------------
-- One row per slot. Daemon reads on start to restore last_run; writes after
-- each slot completion. Eliminates the "every deploy re-fires every slot"
-- cost leak.

CREATE TABLE IF NOT EXISTS daemon_state (
    slot_name  text        PRIMARY KEY,
    last_run   timestamptz NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- centroid_summaries.source_fingerprint
-- ---------------------------------------------------------------------------
-- Replaces the 24h time-staleness trigger with a content-change trigger.
-- Computed from the top-N events per track used as LLM input. When the
-- fingerprint matches the stored value, the centroid's content hasn't
-- materially changed since last generation and we skip the LLM call.

ALTER TABLE centroid_summaries
    ADD COLUMN IF NOT EXISTS source_fingerprint text;

CREATE INDEX IF NOT EXISTS centroid_summaries_rolling_fp_idx
    ON centroid_summaries(centroid_id, period_kind, source_fingerprint)
    WHERE period_kind = 'rolling_30d';

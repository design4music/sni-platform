"""Best-effort LLM call telemetry.

Every LLM call site passes its DeepSeek response `usage` dict + phase name.
This module writes one row to `llm_stats` per call. Never raises.

Read the data back with:
    SELECT phase, COUNT(*) AS calls,
           SUM(tokens_in)  AS in_tokens,
           SUM(tokens_out) AS out_tokens
      FROM llm_stats
     WHERE created_at::date = CURRENT_DATE
     GROUP BY phase ORDER BY out_tokens DESC NULLS LAST;

Phase naming convention (keep stable):
    labels              -- Phase 2.1
    event_prose_full    -- Phase 5.1a (>=5 src)
    event_prose_title   -- Phase 5.1b (<5 src, foreign-only)
    de_batch_translate  -- Phase 5.1c
    daily_brief         -- Phase 5.2
    narrative_discovery -- Phase 5.3
    narrative_review    -- Phase 5.4
    centroid_summary    -- Phase 5.5
"""

import psycopg2

from core.config import config


def log_llm_call(
    phase: str,
    usage: dict | None = None,
    latency_ms: int | None = None,
    model: str | None = None,
    status: str = "ok",
) -> None:
    """Record one LLM call. Best-effort; swallows all exceptions.

    `usage` is the DeepSeek response.usage dict:
        {"prompt_tokens": int, "completion_tokens": int, ...}
    """
    tokens_in = None
    tokens_out = None
    if isinstance(usage, dict):
        tokens_in = usage.get("prompt_tokens") or usage.get("input_tokens")
        tokens_out = usage.get("completion_tokens") or usage.get("output_tokens")

    try:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
            connect_timeout=3,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO llm_stats
                         (phase, tokens_in, tokens_out, latency_ms, model, status)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        phase,
                        tokens_in,
                        tokens_out,
                        latency_ms,
                        model or config.llm_model,
                        status,
                    ),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        # Telemetry must never break the pipeline.
        pass

-- daemon_state: per-slot health visibility.
--
-- Adds three columns so a SELECT * FROM daemon_state shows whether the
-- pipeline daemon is keeping up without scrolling Render logs:
--   last_duration_ms  how long the slot's last run took
--   last_status       'ok' on completion; reserved for future error
--                     paths (cycle-level errors land in slot_name
--                     '__cycle_error__' rather than overwriting per-
--                     slot rows)
--   last_error        error text if last_status <> 'ok'; null otherwise
--
-- Background: 2026-05-04 outage where a half-open Postgres connection
-- silently kept the daemon "running" for hours with zero progress.
-- Without per-slot completion timestamps, the only diagnostic was
-- correlating multiple sources by hand.

ALTER TABLE daemon_state
    ADD COLUMN IF NOT EXISTS last_duration_ms INTEGER,
    ADD COLUMN IF NOT EXISTS last_status TEXT,
    ADD COLUMN IF NOT EXISTS last_error TEXT;

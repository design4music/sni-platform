-- Add narratives_v2.framing_required.
--
-- When true, a title attributes to this narrative only if it matches the
-- publisher coalition AND at least one framing_keyword (ILIKE substring).
-- When false (default), current publisher-coalition-only behavior is kept,
-- so this is a zero-impact change for every existing narrative.
--
-- Purpose: framing-based disambiguation for narratives that share a publisher
-- coalition but compete on stance -- the "friendly-critic" own-goal case.
-- Example: Ukraine corruption, where Western outlets (Spiegel, BBC, WaPo)
-- voice BOTH a reform-in-progress framing and a systemic-alarm framing, so
-- publisher alone cannot separate the stances. Opt-in per narrative, handled
-- uniformly by the engine (like primary_target / stance) -- no per-FN code.
ALTER TABLE narratives_v2
  ADD COLUMN IF NOT EXISTS framing_required boolean NOT NULL DEFAULT false;

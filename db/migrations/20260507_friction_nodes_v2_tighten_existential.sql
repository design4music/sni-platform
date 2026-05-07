-- Tighten west_iran_nuclear_threat framing_keywords by removing neutral
-- and event-descriptive vocabulary.
-- 2026-05-07
--
-- Lesson: the calibration helper surfaces RECURRING phrases, but
-- recurrence != loadedness. Many high-frequency phrases ("uranium
-- enrichment", "nuclear talks", "US-Israeli strikes") are neutral
-- descriptors used by ALL coalitions covering this FN. Including them
-- as framing_keywords routes everyone's coverage into the
-- existential-threat narrative.
--
-- The keep-list contains only language that genuinely diagnoses the
-- existential-threat frame (preemptive doctrine, breakout language,
-- denial-of-capability, Stuxnet-era covert sabotage, etc.).

BEGIN;

UPDATE narratives_v2
SET framing_keywords = ARRAY[
    -- Doctrine + posture (loaded)
    'existential threat',
    'preemptive strike',
    'prevention not deterrence',
    'Begin doctrine',
    'all options on table',
    'maximum pressure',

    -- Capability-denial framing (loaded)
    'denial of capability',
    'denuclearization',
    'rollback',
    'weapons program',
    'nuclear weapon program',
    'nuclear weapons capability',
    'nuclear ambition',
    'nuclear ambitions',

    -- Threshold + breakout (loaded)
    'breakout time',
    'breakout window',
    'breakout capability',
    'weapons-grade',

    -- Covert action / clandestine framing (loaded)
    'clandestine enrichment',
    'Stuxnet',
    'military option',
    'Natanz strike'
],
updated_at = now()
WHERE id = 'west_iran_nuclear_threat';

-- Note: removed entries (kept for the record):
--   uranium enrichment, nuclear talks, US-Iran nuclear,
--   US-Iran nuclear talks, natanz nuclear, nuclear chief, nuclear deal,
--   Iranian nuclear, Iran nuclear chief, US-Israeli strikes,
--   strikes on nuclear, strike on Natanz, military strikes,
--   enrichment cascade, nuclear facility strike
-- These are descriptive/neutral vocabulary, not loaded threat-frame
-- diagnostic. They will be caught by the topic_keywords gate via
-- "Iran nuclear" / "Natanz" / "Fordow" instead.

COMMIT;

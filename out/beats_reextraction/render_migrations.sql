-- ============================================================================
-- ELO v3.0.1 Render DB migrations
-- Date: 2026-04-14 (deployment morning)
-- Run via Render psql shell or one-off job. SAFE: all changes are reversible.
-- ============================================================================

-- IMPORTANT: confirm Render worker/daemon is STOPPED before running.
-- Migrations modify schema and reference data; the daemon must not be
-- writing labels in parallel.

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Extend title_labels.action_class CHECK constraint to allow v3.0.1 +
--    legacy v2 values during transition.
-- ---------------------------------------------------------------------------
ALTER TABLE title_labels DROP CONSTRAINT title_labels_action_class_check;

ALTER TABLE title_labels ADD CONSTRAINT title_labels_action_class_check
CHECK (action_class = ANY (ARRAY[
  -- ELO v3.0.1 (current)
  'LEGAL_ACTION','LEGISLATIVE_DECISION','POLICY_CHANGE','REGULATORY_ACTION','ELECTORAL_EVENT',
  'MILITARY_OPERATION','LAW_ENFORCEMENT_OPERATION','SANCTION_ENFORCEMENT',
  'RESOURCE_ALLOCATION','INFRASTRUCTURE_DEVELOPMENT','CAPABILITY_TRANSFER','COMMERCIAL_TRANSACTION',
  'ALLIANCE_COORDINATION','STRATEGIC_REALIGNMENT','MULTILATERAL_ACTION',
  'PRESSURE','ECONOMIC_PRESSURE','STATEMENT','INFORMATION_INFLUENCE',
  'INSTITUTIONAL_RESISTANCE','CIVIL_ACTION',
  'SECURITY_INCIDENT','NATURAL_EVENT','MARKET_SHOCK',
  -- Legacy v2 (transitional - present in unprocessed historical rows)
  'LEGAL_RULING','LEGAL_CONTESTATION',
  'POLITICAL_PRESSURE','DIPLOMATIC_PRESSURE','COLLECTIVE_PROTEST','SOCIAL_INCIDENT','ECONOMIC_DISRUPTION'
]));

-- ---------------------------------------------------------------------------
-- 2. Add industries[] column for v3.0.1 entity tagging.
-- ---------------------------------------------------------------------------
ALTER TABLE title_labels ADD COLUMN IF NOT EXISTS industries text[];

-- ---------------------------------------------------------------------------
-- 3. Migrate strategic_narratives.action_classes to v3.0.1 vocab.
--    Preserves manual enrichment fields (matching_guidance, example_event_ids,
--    aligned_with, opposes) by using direct UPDATE rather than re-seed.
-- ---------------------------------------------------------------------------
WITH subs(old_val, new_val) AS (VALUES
  ('LEGAL_RULING',       'LEGAL_ACTION'),
  ('LEGAL_CONTESTATION', 'LEGAL_ACTION'),
  ('POLITICAL_PRESSURE', 'PRESSURE'),
  ('DIPLOMATIC_PRESSURE','PRESSURE'),
  ('COLLECTIVE_PROTEST', 'CIVIL_ACTION'),
  ('ECONOMIC_DISRUPTION','MARKET_SHOCK'),
  ('SOCIAL_INCIDENT',    'SECURITY_INCIDENT')
)
UPDATE strategic_narratives sn SET action_classes = (
  SELECT ARRAY_AGG(DISTINCT COALESCE(s.new_val, ac))
  FROM UNNEST(sn.action_classes) AS ac
  LEFT JOIN subs s ON s.old_val = ac
)
WHERE action_classes && ARRAY[
  'LEGAL_RULING','LEGAL_CONTESTATION','POLITICAL_PRESSURE','DIPLOMATIC_PRESSURE',
  'COLLECTIVE_PROTEST','ECONOMIC_DISRUPTION','SOCIAL_INCIDENT'
];

-- ---------------------------------------------------------------------------
-- Verification queries (read-only) - run these AFTER COMMIT to confirm.
-- ---------------------------------------------------------------------------
COMMIT;

-- VERIFY 1: industries column exists
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='title_labels' AND column_name='industries';

-- VERIFY 2: no v2 class names remain in strategic_narratives
SELECT ac, COUNT(*) FROM strategic_narratives, UNNEST(action_classes) AS ac
WHERE ac IN ('LEGAL_RULING','LEGAL_CONTESTATION','POLITICAL_PRESSURE',
             'DIPLOMATIC_PRESSURE','COLLECTIVE_PROTEST','ECONOMIC_DISRUPTION','SOCIAL_INCIDENT')
GROUP BY ac;
-- Expected: 0 rows

-- VERIFY 3: top action classes after migration
SELECT ac, COUNT(*) AS n FROM strategic_narratives, UNNEST(action_classes) AS ac
GROUP BY ac ORDER BY n DESC LIMIT 12;
-- Expected: PRESSURE, MILITARY_OPERATION, STRATEGIC_REALIGNMENT, etc.

-- VERIFY 4: CHECK constraint allows new + legacy values
SELECT pg_get_constraintdef(oid) FROM pg_constraint
WHERE conrelid = 'title_labels'::regclass
  AND conname = 'title_labels_action_class_check';
-- Expected: should include LEGAL_ACTION, PRESSURE, STATEMENT, ELECTORAL_EVENT,
--           COMMERCIAL_TRANSACTION, NATURAL_EVENT, MARKET_SHOCK, CIVIL_ACTION,
--           plus legacy v2 names.

-- ============================================================================
-- ROLLBACK (only if you need to revert before re-extraction completes)
-- ============================================================================
-- BEGIN;
--
-- -- Restore old constraint (v2 only)
-- ALTER TABLE title_labels DROP CONSTRAINT title_labels_action_class_check;
-- ALTER TABLE title_labels ADD CONSTRAINT title_labels_action_class_check
-- CHECK (action_class = ANY (ARRAY[
--   'LEGAL_RULING','LEGISLATIVE_DECISION','POLICY_CHANGE','REGULATORY_ACTION',
--   'MILITARY_OPERATION','LAW_ENFORCEMENT_OPERATION','SANCTION_ENFORCEMENT',
--   'RESOURCE_ALLOCATION','INFRASTRUCTURE_DEVELOPMENT','CAPABILITY_TRANSFER',
--   'ALLIANCE_COORDINATION','STRATEGIC_REALIGNMENT','MULTILATERAL_ACTION',
--   'POLITICAL_PRESSURE','ECONOMIC_PRESSURE','DIPLOMATIC_PRESSURE','INFORMATION_INFLUENCE',
--   'LEGAL_CONTESTATION','INSTITUTIONAL_RESISTANCE','COLLECTIVE_PROTEST',
--   'SECURITY_INCIDENT','SOCIAL_INCIDENT','ECONOMIC_DISRUPTION'
-- ]));
--
-- -- Drop industries column
-- ALTER TABLE title_labels DROP COLUMN IF EXISTS industries;
--
-- -- Reverting strategic_narratives requires a backup dump (not scripted here).
-- -- Take a backup BEFORE migrating if rollback might be needed.
--
-- COMMIT;

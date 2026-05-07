-- Drop gulf_regional_de_escalation from FN2 (Iran nuclear program).
-- 2026-05-07
--
-- Editorial decision: only narratives with real political will, resource,
-- and power behind them belong on an FN. The Gulf-hedging frame
-- (Saudi-Iran rapprochement, Vision 2030, IMEC, Beijing-mediated
-- de-escalation) was a real 2023-early-2026 posture but has receded
-- under the current Iran war — Gulf coverage in the data is dominated
-- by defending-against-Iranian-strikes, not by hedging-mediation.
--
-- The narrative itself is NOT deleted. It stays in narratives_v2 for
-- potential reattachment to other FNs (e.g. a future "Gulf-Iran regional
-- relations" FN where the hedging frame remains live). Only the link
-- to iran_nuclear_program is removed.

BEGIN;

DELETE FROM friction_node_narratives
WHERE fn_id = 'iran_nuclear_program'
  AND narrative_id = 'gulf_regional_de_escalation';

-- Also clean up any lingering title_narratives rows for this narrative
-- attached via the now-broken FN link. (The narrative may still attach
-- elsewhere; the bootstrap will repopulate appropriately.)
DELETE FROM title_narratives
WHERE narrative_id = 'gulf_regional_de_escalation';

COMMIT;

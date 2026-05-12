-- Tighten friction_nodes.centroid_ids so the centroid-overlap filter is
-- a real theater gate, not a broad net. With Phase 2.1 reliably tagging
-- every title whose text mentions the theater's actor, the centroid set
-- only needs to enumerate the theater's identity centroids — broader
-- "actor + adjacent" centroids let pure-other-theater coverage bleed in
-- via shared centroids like AMERICAS-USA.
--
-- Reverts the 2026-05-12 widening of iran_theater (10 centroids, made to
-- absorb stand-by narratives' scope_centroid_ids overrides — no longer
-- needed under 1-to-1).
-- 2026-05-12

BEGIN;

-- iran_theater: 10 -> 1 (only Iran identifies the Iran theater)
UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-IRAN']
WHERE id = 'iran_theater';

-- israel_theater: 10 -> 3 (Israel + Palestine + Levant — the Israel surface)
UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-ISRAEL','MIDEAST-PALESTINE','MIDEAST-LEVANT']
WHERE id = 'israel_theater';

-- gaza_war: 5 -> 2
UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-ISRAEL','MIDEAST-PALESTINE']
WHERE id = 'gaza_war';

-- israel_lebanon_border: drop Iran (theater overlap, not surface overlap)
UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-ISRAEL','MIDEAST-LEVANT']
WHERE id = 'israel_lebanon_border';

-- israel_iran_strikes: keep 3 — this FN genuinely needs both sides
UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-ISRAEL','MIDEAST-IRAN','AMERICAS-USA']
WHERE id = 'israel_iran_strikes';

-- west_bank_settlements: 4 -> 2
UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-ISRAEL','MIDEAST-PALESTINE']
WHERE id = 'west_bank_settlements';

-- Iran cluster atomic FNs: confirm narrow centroids
-- (these were already narrow but normalize for clarity)
UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-IRAN']
WHERE id IN ('iran_nuclear_program','iran_proxy_network','strait_of_hormuz_sovereignty');

UPDATE friction_nodes SET centroid_ids = ARRAY['MIDEAST-GULF','MIDEAST-IRAN']
WHERE id = 'gulf_attacks_on_arab_states';

COMMIT;

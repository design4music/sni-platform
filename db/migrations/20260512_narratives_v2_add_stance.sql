-- Add stance column to narratives_v2 and populate for the Iran cluster.
-- stance ∈ {support, criticism, neutral} — used by the frontend to render
-- narrative bricks/cards/chart in stance-keyed colors:
--   support  = #10b981 (emerald, pro-actor)
--   criticism = #ef4444 (red, anti-actor)
--   neutral  = #71717a (zinc, diplomatic / not-aligned)
-- 2026-05-12.

BEGIN;

ALTER TABLE narratives_v2
    ADD COLUMN IF NOT EXISTS stance text
        CHECK (stance IS NULL OR stance IN ('support','criticism','neutral'));

-- Iran cluster mapping:
-- Anti-Iran (Western-coalition) narratives = criticism
-- Pro-Iran (Iranian coalition + multipolar anti-Western) = support
-- EU diplomatic = neutral
UPDATE narratives_v2 SET stance = 'criticism' WHERE id IN (
    'west_iran_nuclear_threat',
    'west_iran_proxy_network_threat',
    'west_hormuz_freedom_of_navigation',
    'west_gulf_aggression_response',
    'west_iran_regime_change_doctrine'
);
UPDATE narratives_v2 SET stance = 'support' WHERE id IN (
    'iran_nuclear_sovereign_right',
    'iran_axis_of_resistance',
    'iran_hormuz_sovereign_pressure',
    'iran_sovereign_existence',
    'multipolar_systemic_alternative'
);
UPDATE narratives_v2 SET stance = 'neutral' WHERE id IN (
    'eu_diplomatic_preservation_norm'
);

COMMIT;

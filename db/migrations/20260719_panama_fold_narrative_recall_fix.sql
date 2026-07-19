-- Recall fix + retire the empty -1 card (2026-07-19)
--
-- (a) port_control_restored's framing gate was too tight: 17 in-coalition
--     titles were dropped, and they are the SPINE of the story, not edge
--     cases -- "Panama takes control of canal ports, ousting Hong Kong
--     group" (France 24), "Panama hands canal ports control to Maersk and
--     MSC after ejecting Hong Kong group" (FT), "China told Maersk and MSC
--     to drop Panama port operations" (Reuters), "China warns Panama of
--     'heavy prices'" (Reuters). Broadening per spec section 5, tuning rule 3.
--     Kept framing_required=true rather than dropping to publisher-only so
--     the Hormuz commodity stories ("Panama Canal oil shipments soar 70%")
--     and CK Hutchison's unrelated corporate news (HK supermarket merger,
--     UK utility sale) stay out -- publisher-only would file all three as
--     "host-state control restored".
--
-- (b) port_sovereignty_squeeze retired. Once the neutral escalation keywords
--     were removed it matched ZERO titles: the -1 stance has no in-gate
--     corpus, because its real evidence (US force posture in Panama) never
--     names the canal or the ports. Row kept, is_active=false, for one-line
--     reactivation if that coverage ever enters the gate. Deactivating beats
--     loosening it back -- a card that only fills up by mislabelling +2
--     titles is worse than an absent card.

BEGIN;

UPDATE narratives_v2
SET framing_keywords = ARRAY[
        -- lawfulness of the reassertion
        'sovereignt', 'Souveränität', 'soberan', 'unconstitutional',
        'verfassungswidrig', 'inconstitucional', 'court', 'Gericht',
        'ruling', 'Urteil', 'quashed', 'voids', 'annull',
        -- the transfer of control itself
        'takes control', 'take control', 'wrests', 'reclaim', 'takes back',
        'ousting', 'ousts', 'ejecting', 'kicks', 'seizes', 'seized',
        'hands canal', 'to operate', 'reprend le contrôle', 'übernimmt',
        'zurück', 'reasserts',
        -- the security rationale
        'security risk', 'Sicherheitsrisiko', 'vulnerab', 'verwundbar', 'de-risk',
        -- Chinese retaliation as evidence for it
        'bullying', 'coercion', 'Zwang', 'retaliation', 'Vergeltung',
        'detention', 'detentions', 'heavy price', 'necessary action',
        'told Maersk', 'drop Panama', 'non-negotiable', 'backs Panama',
        'joint statement'
    ],
    updated_at = NOW()
WHERE id = 'port_control_restored';

UPDATE narratives_v2
SET is_active = false, updated_at = NOW()
WHERE id = 'port_sovereignty_squeeze';

COMMIT;

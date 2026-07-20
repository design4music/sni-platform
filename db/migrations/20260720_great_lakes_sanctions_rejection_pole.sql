-- Great Lakes: add the rejection pole to drc_peace_process (2026-07-20).
--
-- drc_sanctions_as_enforcement (+1) finished at 16 titles, of which 2 were
-- wrong-signed -- they are REACTIONS against the designations, not instances of
-- them:
--   "Rwanda hits back at US sanctions over M23 support"        (The Standard)
--   "Kabila denounces 'unjustified' US sanctions"              (Anadolu)
-- Carrying a +1 "enforcement is working" stance on a headline whose content is
-- "these sanctions are an insult" is exactly the mislabelling this build has
-- been guarding against.
--
-- FIX, in two parts:
--
-- 1. The Standard and Anadolu Agency leave the enforcement coalition. Verified
--    zero cost: each contributed exactly ONE title there, and it was the
--    mislabelled one. 16 -> 14, all clean.
--
-- 2. NEW drc_sanctions_rejected (-2). This restores an adversarial pole to the
--    atomic, which the retired drc_mediation_as_interference could not do.
--    The distinction matters and is the reason one was retired and this one
--    added: "Western mediation is neo-colonial pressure" had NO constituency in
--    this corpus (its only titles were neutral CGTN wire copy), whereas "the
--    designated parties reject the designations" is carried by real outlets
--    printing the accused parties' own words -- Kigali calling the measures
--    insults that will not change its defence policy, Kabila calling his
--    designation unjustified. It is a genuine, attributable position of a party
--    to the conflict, and it is labelled as their rejection rather than as an
--    endorsement of anything.
--
--    Deliberately small. Same shape as m23_backing_charge_rejected on the other
--    atomic; note the Kabila denunciation cannot live there because that title
--    carries no M23 anchor and so never attributes to the M23 atomic at all.

BEGIN;

UPDATE narratives_v2 SET
    publishers = ARRAY['France 24', 'France 24 (EN)', 'Le Monde', 'Le Figaro', 'Reuters', 'Associated Press', 'The Guardian', 'BBC World', 'BBC', 'Deutsche Welle', 'Washington Post', 'Financial Times', 'Al Jazeera', 'Daily Nation', 'Punch Newspapers'],
    updated_at = NOW()
WHERE id = 'drc_sanctions_as_enforcement';

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'drc_sanctions_rejected',
    'drc_peace_process',
    'The designated parties reject the designations',
    'Die Gelisteten weisen die Listungen zurück',
    'Those named in the measures dispute both their basis and their effect. Kigali presents the designations as insults that will not alter Rwandan defence policy, and the former Congolese president describes his own listing as unjustified. On this reading the sanctions are an external actor taking sides in a regional dispute it does not fully understand, rather than a neutral enforcement of an agreement.',
    'Die Benannten bestreiten sowohl die Grundlage als auch die Wirkung der Maßnahmen. Kigali stellt die Listungen als Beleidigungen dar, die an Ruandas Verteidigungspolitik nichts ändern, und der frühere kongolesische Präsident nennt seine eigene Listung ungerechtfertigt. In dieser Lesart ergreift ein externer Akteur Partei in einem regionalen Streit, den er nicht vollständig überblickt, statt ein Abkommen neutral durchzusetzen.',
    -2,
    'The designations are rejected',
    'Die Listungen werden zurückgewiesen',
    ARRAY['AFRICA-DRC'],
    ARRAY['The Standard', 'Anadolu Agency', 'Al-Ahram', 'Mail & Guardian', 'News24', 'TRT World', 'Daily Sabah', 'RT', 'TASS', 'TASS (EN)', 'Sputnik'],
    ARRAY['denies', 'denied', 'denounces', 'denounced', 'rejects', 'rejected', 'unjustified', 'unfounded', 'hits back', 'insults', 'sovereignty', 'internal affairs', 'dément', 'rejette', 'dénonce', 'injustifié', 'souveraineté', 'weist zurück', 'bestreitet', 'ungerechtfertigt', 'Souveränität'],
    true, 4, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

COMMIT;

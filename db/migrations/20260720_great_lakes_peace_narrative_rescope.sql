-- Great Lakes: drc_peace_process narrative re-scope (2026-07-20).
--
-- Found by listing on-topic titles that landed in NO narrative after the
-- framing fix. Two findings, in opposite directions.
--
-- ---------------------------------------------------------------------------
-- 1. RETIRE drc_mediation_as_interference (-2). It finished at ZERO titles once
--    framing_required was turned on, and that is the correct reading, not a
--    tuning failure. Its three pre-fix titles were all neutral CGTN wire copy.
--    Verified directly: Chinese and Russian state outlets publish no
--    rift-exploitation framing of the DRC mediation in this window -- RT has a
--    single DRC title all half-year ("Rebel spokesperson killed in DR Congo").
--    The stance has NO CONSTITUENCY here (the Cuba lesson: retire it, do not
--    keyword-stuff a card into existence). The result is a peace atomic with no
--    adversarial pole, which is the honest shape of this corpus -- the same way
--    Ethiopia honestly has two negative narratives and no positive one.
--
-- 2. ADD drc_sanctions_as_enforcement (+1). The single LARGEST cluster on this
--    atomic -- roughly a dozen titles covering the designation of the Rwandan
--    army and senior officers, visa restrictions on Rwandan officials, and the
--    sanctioning of former president Joseph Kabila -- was landing in no
--    narrative at all. `sanction` was in the FN's bundle (so the events
--    attributed) but appeared in no narrative's framing_keywords, so every one
--    of those titles fell through the narrative layer. This is the enforcement
--    half of the atomic and it needs its own card.
--
--    Note these titles ALSO sit on m23_conflict under
--    m23_externally_backed_offensive. That is intended: the same designation is
--    evidence of cross-border backing (M23 atomic) and an act of enforcement
--    against the accords (this atomic). Different framings of one fact.
--
-- 3. BROADEN drc_accords_are_working, which over-pruned to 2 titles when
--    `accord` was removed. Genuinely positive headlines were left homeless
--    because they express the outcome in other words: "Kinshasa compte sur les
--    accords de Washington pour SÉCURISER l'Est du pays", "Ceasefire in eastern
--    DR Congo: A CHANCE for peace?", "MONUSCO PREPARES TO SUPPORT ceasefire
--    between DRC and M23". Adding outcome verbs only -- still no topic words.
--
-- DELIBERATELY NOT RECOVERED: the Willy Ngoma drone-strike cluster (~6 titles)
-- remains in no narrative. Those are neutral battlefield reports of a
-- combatant's death; they fit neither the proxy-war framing nor the
-- civilian-harm one, and the only keyword that would recover them
-- (`drone strike`) is precisely the neutral escalation noun that had to be
-- removed for stealing the aid-worker cluster. The narrative layer carries
-- framings, not exhaustive coverage -- precision over recall.

BEGIN;

UPDATE narratives_v2 SET is_active = false, updated_at = NOW()
WHERE id = 'drc_mediation_as_interference';

UPDATE narratives_v2 SET
    framing_keywords = ARRAY['signed', 'commit', 'commitment', 'progress', 'monitoring', 'release', 'released', 'prisoners', 'facilitate', 'de-escalate', 'breakthrough', 'mechanism', 'secure', 'chance', 'advance', 'prepares to support', 'deploy', 'signé', 'engagement', 'progrès', 'libérer', 'libération', 'faciliter', 'désescalade', 'sécuriser', 'compte sur', 'unterzeichnet', 'Fortschritt', 'Freilassung', 'Deeskalation', 'Chance'],
    updated_at = NOW()
WHERE id = 'drc_accords_are_working';

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'drc_sanctions_as_enforcement',
    'drc_peace_process',
    'Designations as the only real leverage',
    'Listungen als einziges echtes Druckmittel',
    'With no force willing to impose the accords on the ground, financial and travel designations have become the instrument that carries actual cost: the Rwandan army and its senior commanders listed, visa restrictions placed on Rwandan officials, and a former Congolese president designated over his support for the rebellion. Analysts read the move against Kigali as the sharpest turn in the conflict''s external handling to date.',
    'Da keine Truppe bereit ist, die Abkommen vor Ort durchzusetzen, sind Finanz- und Reisebeschränkungen zum einzigen Instrument mit realen Kosten geworden: die ruandische Armee und ihre ranghohen Kommandeure gelistet, Visasperren gegen ruandische Amtsträger, und ein früherer kongolesischer Präsident wegen seiner Unterstützung der Rebellion benannt. Beobachter werten das Vorgehen gegen Kigali als die schärfste Wende im äußeren Umgang mit diesem Konflikt bislang.',
    1,
    'Enforcement by designation',
    'Durchsetzung durch Listung',
    ARRAY['AFRICA-DRC', 'AMERICAS-USA'],
    ARRAY['France 24', 'France 24 (EN)', 'Le Monde', 'Le Figaro', 'Reuters', 'Associated Press', 'The Guardian', 'BBC World', 'BBC', 'Deutsche Welle', 'Washington Post', 'Financial Times', 'Al Jazeera', 'Anadolu Agency', 'Daily Nation', 'The Standard', 'Punch Newspapers', 'Mail & Guardian'],
    ARRAY['sanction', 'sanctions', 'sanctioned', 'designat', 'visa restriction', 'listed', 'penalt', 'asset freeze', 'sanctionne', 'sanctionné', 'sanctions', 'restrictions de visa', 'Sanktionen', 'sanktioniert', 'Einreiseverbot'],
    true, 3, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

COMMIT;

-- Sahel: narrative precision fixes found by reading samples (2026-07-20).
-- Spec §0a step 9: do not trust plausible-looking counts -- pull the titles.
--
-- DEFECT 1 -- sahel_counterterror_necessity (97 titles) was publisher-only
-- (framing_required=false) on a coalition containing Punch and Vanguard, which
-- are high-volume GENERALIST Nigerian dailies, not security desks. Every title
-- they published that touched the bundle landed on a stance about counterterror
-- legitimacy regardless of what it said:
--   "Nigeria under siege by fake medicines"                        (Punch)
--   "US-Iran war: Tinubu backs UAE, condemns attacks on civilians" (Punch)
--   "Faces of Africa - Kalthum Mohammad: The woman who talks to
--    Boko Haram"                                                   (CGTN)
--   "US sends troops to Nigeria after December airstrikes"         (Punch)
-- The publisher-coalition assumption (spec §5) holds for a state broadcaster
-- with an editorial line; it does NOT hold for a generalist national daily that
-- simply covers everything in its own country. Adding a framing gate keyed to
-- the counterterror-OPERATIONS register.
--
-- DEFECT 2 -- sahel_counterinsurgency_abuses was filing INSURGENT-caused
-- civilian deaths under a stance that reads "the counterinsurgency is killing
-- the civilians it claims to protect":
--   "'They sent a letter asking to preach. Then they massacred us'
--    - Nigerians on jihadist attack"                            (BBC World)
--   "Armed attack on airport in Niger's capital kills 11 soldiers,
--    2 civilians"                                               (Al Jazeera)
-- Cause: bare 'massacre' and bare 'civilian'/'civils' are perpetrator-neutral --
-- both camps kill civilians and both are described this way. Since framing
-- keywords are OR'd there is no way to AND in an actor, so the fix is to keep
-- only harm words that IMPLY state perpetration or independent documentation
-- (exactions, atrocités, HRW, Amnesty, impunity, airstrike+market, wedding,
-- 'crimes de l'armée') and drop the neutral ones. Precision over recall
-- (spec §0 principle 4): losing a couple of real titles costs less than a card
-- that tells the reader the army did something the jihadists did.
--
-- Companion bundle change: 'siege' dropped from sahel_jihadist_insurgency.
-- Nigerian English uses it metaphorically ("under siege by fake medicines") and
-- 'blockade'/'blocus' already carries the Bamako story.

BEGIN;

UPDATE narratives_v2
SET framing_required = true,
    framing_keywords = ARRAY[
        -- EN counterterror-operations register
        'troops kill','soldiers kill','army kill','killed','neutralis','neutraliz',
        'eliminated','surrender','surrendered','repel','repelled','foiled',
        'thwart','operation','offensive against','anti-jihadist','counterterror',
        'counter-terror','arrested','captured','degrade','airstrikes kill',
        'terrorists','bandits','freed','rescued','liberated',
        -- FR
        'neutralisés','abattus','opération','riposte','repoussé','libérés',
        'reddition','terroristes',
        -- RU / ZH / AR / DE
        'уничтож','ликвидир','отраж','боевик',
        '击毙','剿灭','解救',
        'قضت','أحبطت','حررت',
        'getötet','zurückgeschlagen'
    ],
    updated_at = NOW()
WHERE id = 'sahel_counterterror_necessity';

UPDATE narratives_v2
SET framing_keywords = ARRAY[
        -- state perpetration / independent documentation only
        'exaction','atrocit','abuses','human rights','Human Rights Watch','HRW',
        'Amnesty','impunity','impunité','summary execution','extrajudicial',
        'airstrike','air strike','frappes','misfire','wedding','mariage',
        'civilian deaths','morts civils','victimes civiles','killed civilians',
        'civils tués','crimes de l''armée','army behind','par l''armée',
        'Menschenrechte','Übergriffe','Gräueltaten','derechos humanos',
        'droits de l''homme','disappearance','mass grave','charnier'
    ],
    updated_at = NOW()
WHERE id = 'sahel_counterinsurgency_abuses';

COMMIT;

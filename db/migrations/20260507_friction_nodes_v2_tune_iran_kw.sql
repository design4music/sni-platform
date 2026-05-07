-- Calibrate iran_nuclear_sovereign_right keywords against actual coverage
-- by 4 Iranian sources (Press TV, IRNA, Fars News, Tasnim News).
-- 2026-05-07
--
-- Method: scan ~80 nuclear-topic headlines from these outlets, extract
-- recurring loaded vocabulary, expand framing_keywords + topic_keywords.
-- This is a deliberate calibration pattern for "sparse coverage / high
-- stakes" narratives where Western-corpus-only keywords miss real
-- primary-source language.

BEGIN;

UPDATE narratives_v2
SET framing_keywords = ARRAY[
    -- Original (kept):
    'peaceful civilian nuclear program',
    'NPT Article IV',
    'sovereign enrichment',
    'Khamenei fatwa',
    'fatwa against nuclear weapons',
    'we honored the deal',
    'American withdrawal',
    'JCPOA betrayed',
    'maximum pressure failure',
    'collective punishment',
    'deterrence hedge',
    'Israeli aggression',
    'state terrorism',
    'Iraq Libya cautionary',
    -- Added from Iranian-source corpus:
    'peaceful nuclear',
    'peaceful nuclear energy',
    'peaceful nuclear technology',
    'right to enrich',
    'enrichment rights',
    'inalienable right',
    'rights enshrined in NPT',
    'nuclear logic',
    'religious beliefs',
    'big lie',
    'big lies',
    'civilian atomic',
    'civilian nuclear',
    'Israeli sabotage',
    'attacks on Iran',
    'attacks on nuclear',
    'US-Israeli attacks',
    'language of force',
    'rejects language',
    'Israeli arsenal',
    'nuclear-weapon-free Middle East',
    'fair nuclear deal',
    'fair nuclear talks',
    'rejection of nuclear weapons',
    'nuclear self-sufficiency',
    'reparations',
    'nuclear ambiguity',
    'demands reparations'
],
topic_keywords = ARRAY[
    -- Original (kept):
    'Iran nuclear',
    'Natanz',
    'Fordow',
    'Bushehr',
    'IAEA Iran',
    'JCPOA',
    'enrichment',
    'centrifuge',
    'Khamenei',
    'Pezeshkian',
    'Araghchi',
    'Vienna talks',
    -- Added Iranian officials + venues that surface in primary coverage:
    'Larijani',
    'Baqaei',
    'Gharibabadi',
    'Eslami',
    'Iran atomic',
    'Iranian nuclear',
    'Tehran nuclear',
    'NPT',
    'uranium',
    'Iran enrichment',
    'Geneva nuclear',
    'Muscat nuclear',
    'Oman talks'
],
updated_at = now()
WHERE id = 'iran_nuclear_sovereign_right';

COMMIT;

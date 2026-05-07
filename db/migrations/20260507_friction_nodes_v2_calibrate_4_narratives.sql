-- Apply calibration findings to the 4 narratives (EU diplomacy, Multipolar,
-- Gulf hedging, and a v2 of Existential threat).
-- 2026-05-07
--
-- See calibration reports in out/ for per-narrative phrase tables and
-- evidence. Curation principle: include only keywords that diagnose
-- the narrative's frame (skip recurring-but-neutral terms).

BEGIN;

-- ---------------------------------------------------------------------
-- EU diplomatic preservation — clear "dialogue/de-escalation/Vatican"
-- vocabulary surfaced from BBC/Guardian/FT/Le Monde/ANSA/El Pais coverage.
-- ---------------------------------------------------------------------
UPDATE narratives_v2
SET framing_keywords = ARRAY[
    -- Original (kept):
    'preserve diplomacy', 'diplomatic off-ramp', 'multilateral framework',
    'engage rather than isolate', 'de-escalation', 'return to negotiations',
    'snapback', 'JCPOA-plus', 'Vienna talks', 'Normandy Format',
    'two-state solution', 'strategic ambiguity', 'international law', 'EU as convener',
    -- Added from calibration:
    'dialogue',
    'must stop',
    'must be resolved',
    'resolved through dialogue',
    'return to diplomacy',
    'striving for return to diplomacy',
    'firmness and dialogue',
    'dialogue with US',
    'Kaja Kallas',
    'EU foreign affairs',
    'EU foreign affairs chief',
    'Tajani',
    'Parolin',
    'Vatican',
    'Pope Leo',
    'Meloni',
    'EU eyeing',
    'no to escalation',
    'EU-US relations',
    'preserve the deal',
    'support every initiative',
    'oppose military action',
    'resume talks',
    'restore JCPOA',
    -- Process-language additions (EU Western coverage of Iran-nuclear
    -- talks/deals — empirically dominant in BBC/Guardian/FT/Le Monde/
    -- Euronews/DW headlines on this FN):
    'talks',
    'Iran talks',
    'nuclear talks',
    'Iran nuclear talks',
    'US-Iran nuclear talks',
    'negotiations',
    'negotiating',
    'mediates',
    'Oman mediates',
    'critical stage',
    'reach a deal',
    'no deal',
    'without a deal',
    'deal or',
    'nuclear deal',
    'Iran nuclear deal',
    'stand-off',
    'deal deadline',
    'failed deals',
    'continue talks',
    'scheduled for'
],
updated_at = now()
WHERE id = 'eu_diplomatic_preservation_norm';

-- ---------------------------------------------------------------------
-- Multipolar systemic alternative — anti-sanctions / dollar hegemony /
-- US-bases vocabulary surfaced from RT/TASS/Xinhua/CGTN/Al Jazeera.
-- ---------------------------------------------------------------------
UPDATE narratives_v2
SET framing_keywords = ARRAY[
    -- Original (kept):
    'US hegemony', 'unilateralism', 'imperialism', 'Cold War mentality',
    'collective punishment', 'regime change', 'foreign occupation',
    'multipolar', 'BRICS', 'Global South', 'sovereign right',
    'anti-sanctions', 'dollar de-dependence', 'encirclement',
    -- Added from calibration:
    'US sanctions',
    'sanctions on Russia',
    'sanctions on Russian',
    'anti-Russian sanctions',
    'lift sanctions',
    'new sanctions',
    'EU sanctions',
    'sanctions package',
    'oil sanctions',
    'sanctions on Iranian oil',
    'sanctions waiver',
    'soften sanctions',
    'US bases',
    'US bases in Middle East',
    'US bases in region',
    'dollar hegemony',
    'US dollar hegemony',
    'inalienable right',                -- when used in support of Iran by Russian/Chinese sources
    'Hungary to block',
    'Slovakia',                         -- anti-EU-sanctions European holdouts
    'Russia evacuates',                 -- Bushehr framing
    'Russia warns',
    'Russia offers'
],
updated_at = now()
WHERE id = 'multipolar_systemic_alternative';

-- ---------------------------------------------------------------------
-- Gulf regional de-escalation — narrow set. Calibration revealed that
-- current Gulf publisher coverage is dominated by WAR coverage (UAE air
-- defences, ballistic missiles, Iranian attacks), NOT by hedging-frame
-- vocabulary. Hedging-frame is real but sparse. We keep the keyword list
-- focused on genuine hedging language so the framing-filter (applied in
-- the bootstrap for stand_by narratives) excludes the war-coverage
-- noise that publisher-bucket alone admits.
-- ---------------------------------------------------------------------
UPDATE narratives_v2
SET framing_keywords = ARRAY[
    -- Original (kept):
    'Gulf de-escalation',
    'Saudi-Iran rapprochement',
    'Vision 2030',
    'IMEC',
    'hedging',
    'regional stability',
    'Yemen exit',
    'Syria normalisation',
    'multipolar Gulf',
    -- Added (genuinely hedging-frame):
    'rapprochement',
    'Beijing-mediated',
    'Beijing deal',
    'mediation',
    'mediator',
    'normalisation',
    'normalization',
    'regional security framework',
    'stability over confrontation',
    'protect oil',
    'protect regional stability',
    'IMEC corridor',
    'India-Middle East-Europe',
    'reduce Middle East tensions',
    'promote rapprochement',
    'reshape Vision 2030',
    'overcome current challenges',
    'unity of its society',         -- UAE-president frame, partial fit
    'come together'
],
updated_at = now()
WHERE id = 'gulf_regional_de_escalation';

-- ---------------------------------------------------------------------
-- Existential threat v2 — Western/Israeli framing language that survives
-- as RANKER (not membership filter). Bumps framing_strength on cards.
-- ---------------------------------------------------------------------
UPDATE narratives_v2
SET framing_keywords = ARRAY[
    -- Original (kept — these are the doctrinal / threshold / covert frames):
    'existential threat', 'preemptive strike', 'prevention not deterrence',
    'Begin doctrine', 'all options on table', 'maximum pressure',
    'denial of capability', 'denuclearization', 'rollback', 'weapons program',
    'nuclear weapon program', 'nuclear weapons capability', 'nuclear ambition',
    'nuclear ambitions', 'breakout time', 'breakout window', 'breakout capability',
    'weapons-grade', 'clandestine enrichment', 'Stuxnet', 'military option',
    'Natanz strike',
    -- Added from calibration as STRONG ranker signals (Israeli/US specific):
    'extract Iran',                     -- Trump "extract enriched uranium"
    'extract enriched uranium',
    'remove enriched uranium',
    'remove uranium',
    'precondition to ending war',
    'crushing',                         -- Netanyahu "crushing Iran nuclear"
    'crushing Iran',
    'eliminate',
    'eliminate Iran',
    'destroy Iran',
    'destroy Iran nuclear',
    'enrichment halt',
    'halt enrichment',
    'stop funding proxies',
    'stop Iran',
    'Iran threat',
    'Witkoff',
    'Iran 11 bombs',                    -- Witkoff line
    'enrichment compromise',
    'oppose enrichment compromise',
    'tear up'
],
updated_at = now()
WHERE id = 'west_iran_nuclear_threat';

COMMIT;

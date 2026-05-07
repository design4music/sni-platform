-- Calibration pass: tighten FN topic gates that admit false positives,
-- and substantially expand EU diplomatic-preservation framing keywords
-- (multi-language: English / French / German / Italian / Spanish) so
-- European mainstream Iran-war coverage actually attaches.
-- 2026-05-07
--
-- Diagnosis: on FN4 (regime legitimacy), only 7/545 European-publisher
-- Iran-FN-relevant titles attached to EU diplomacy. Of the 538 missed,
-- a large fraction was actually false-positive topic match (FN4 had
-- "crackdown", "topple", "overthrow", "the regime" alone in topic_keywords,
-- catching "Google crackdown", "Hungary topple Orban", "North Korea regime").
-- The genuine missed coverage carried multi-language diplomatic vocabulary
-- (ceasefire / cessez-le-feu / Waffenruhe / tregua / mediation / Macron
-- urges / dialogue) that wasn't in the keyword list.

BEGIN;

-- ---------------------------------------------------------------------
-- 1. Tighten FN4 topic_keywords — drop generic words that were too broad.
-- ---------------------------------------------------------------------
UPDATE friction_nodes
SET topic_keywords = ARRAY[
    -- Regime / opposition discourse (multi-word, less false positive)
    'Islamic Republic', 'Iranian regime', 'mullahs',
    'regime change in Iran', 'regime change Iran', 'Iran regime change',
    'Iranian opposition', 'opposition to the regime', 'Iran opposition',
    -- Diaspora opposition vehicles (Iran-specific)
    'Pahlavi', 'Reza Pahlavi', 'Crown Prince of Iran',
    'Iranian monarchist', 'Iran monarchist',
    'MEK', 'Mojahedin', 'Mojahedin-e Khalq', 'NCRI',
    'Maryam Rajavi', 'Iran International',
    -- Internal politics / protest cycle (Iran-specific)
    'Mahsa Amini', 'Women Life Freedom', 'Zhina',
    'Iranian protest', 'Iran protest', 'protests in Iran',
    'Iranian protesters', 'Iran protesters',
    'crackdown on Iranian', 'Iran crackdown',
    'morality police', 'hijab protest', 'Iran hijab',
    'Iranian elections', 'Iran election', 'Iran elections',
    'Iran ceasefire', 'Iran-US ceasefire', 'Iran war',
    -- Leadership / succession (mostly Iran-specific names)
    'Supreme Leader of Iran', 'Iranian Supreme Leader',
    'Khamenei', 'Khamenei killed', 'Khamenei dead', 'Khamenei martyred',
    'next Iranian Supreme Leader', 'Iranian succession',
    'Pezeshkian', 'Larijani', 'Mojtaba Khamenei', 'Raisi',
    -- Decapitation framing (Iran context)
    'decapitation strike Iran', 'regime decapitated',
    'fall of the Islamic Republic', 'fall of the regime in Iran',
    -- Iranian counter-framing
    'sovereign Iran', 'Iranian sovereignty',
    'foreign-backed Iranian', 'foreign interference in Iran',
    'Khomeini'
],
updated_at = now()
WHERE id = 'iran_regime_legitimacy_contest';

-- ---------------------------------------------------------------------
-- 2. Expand eu_diplomatic_preservation_norm framing_keywords with
--    multi-language ceasefire/diplomacy vocabulary actually used in
--    European Iran-war coverage.
-- ---------------------------------------------------------------------
UPDATE narratives_v2
SET framing_keywords = framing_keywords || ARRAY[
    -- English ceasefire / mediation / war-stopping vocabulary
    'ceasefire', 'fragile ceasefire', 'ceasefire deal', 'Iran ceasefire',
    'mediation', 'mediation efforts', 'mediator', 'mediating',
    'stop the war', 'end the war', 'stop Iran war', 'end Iran war',
    'vote to stop', 'Senate vote to stop',
    'Macron urges', 'Macron pushes', 'Macron calls', 'Macron presses',
    'urges restraint', 'calls for restraint', 'calls for ceasefire',
    'urges Trump', 'urges Iran',
    'diplomatic effort', 'diplomatic push', 'diplomatic relation',
    'diplomatic relations', 'diplomatic channel',
    'Vatican', 'Pope', 'Pope Leo',
    'Kallas warns', 'Kallas urges', 'Kallas eyes', 'Kallas says',
    'Borrell',
    'von der Leyen',
    'EU naval mission',
    'civilisational erasure',
    'fund people not bombs', 'movement against war', 'against war in Iran',
    'deal can be done', 'deal with Iran', 'Iran deal',
    'fragile', 'distracts from',
    -- French
    'cessez-le-feu', 'tregua', 'trêve',
    'négociation', 'negociation', 'négocier',
    'diplomatie', 'diplomatique',
    'plaide', 'urge', 'appelle',
    'dialogue avec', 'le dialogue', 'au dialogue', 'du dialogue',
    -- German
    'Waffenruhe', 'Waffenstillstand',
    'Verhandlung', 'Verhandlungen', 'Verhandlungstisch',
    'Diplomatie', 'diplomatisch', 'diplomatische',
    'Friedensgespräch', 'Friedensgespraech', 'Friedensgespraeche',
    'mahnt', 'fordert', 'draengt', 'drangt', 'drängt',
    -- Italian
    'tregua', 'cessate il fuoco',
    'negoziato', 'negoziati', 'trattativa', 'trattative',
    'diplomatico', 'diplomatica',
    'mediazione',
    -- Spanish
    'alto el fuego', 'alto-el-fuego',
    'negociación', 'negociaciones',
    'diplomático', 'diplomática',
    'mediación', 'mediador'
],
updated_at = now()
WHERE id = 'eu_diplomatic_preservation_norm';

COMMIT;

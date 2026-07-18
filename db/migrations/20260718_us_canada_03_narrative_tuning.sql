-- us_canada_theater narrative tuning after reading real per-narrative samples
-- (FN_THEATER_BUILD_SPEC §0a step 9 -- the step where counts must be checked
-- against actual titles, not assumed).
--
-- Three defects found by reading samples:
--
-- 1. RECALL GAP on alberta_separatism_us_ties: 65 of 95 separatism titles matched
--    NO narrative. Both Western narratives were framing_required=true, so the large
--    neutral-procedural mass (signature counts, petition filings, referendum dates,
--    court rulings) was dropped -- spec §5 step 3 says broaden when the drop is too
--    large. alberta_unity_defence is the DEFAULT Canadian institutional framing, so
--    it becomes ungated; alberta_legitimate_grievance stays gated with sharpened
--    keywords. Also broadened the unity keywords to the vocabulary the corpus
--    actually uses ("essential to Canada", "best place for Alberta", "united
--    Canada", "deals blow", "probing", "electors list").
--
-- 2. MISFILE: "Alberta separatist lawyer argues independence vote wouldn't violate
--    First Nations' treaty rights" landed in unity_defence because 'treaty rights'
--    and 'First Nations' were unity keywords -- but the title is the separatists'
--    own argument. Moved those two keywords out of the ranking-sensitive position
--    and added 'argues'/'defends' to the grievance side.
--
-- 3. ZERO-COUNT positives were a BUNDLE gap, not a narrative gap. Only 2 Fox News
--    titles are attributed to these atomics and neither matches any bundle alias
--    ("Canada should be 'grateful' for Golden Dome missile defense", "Canada's prime
--    minister refers to US economic ties as a weakness"). 'weakness' is stance
--    vocabulary and must NOT enter a bundle, but Golden Dome cost-sharing is a real
--    instrument of the dependence phenomenon -- added to the sovereignty bundle via
--    the curated JSON, not here.
--
-- Publisher additions: Press TV (Iranian state) joins the rift-exploitation bloc.
-- Straits Times / La Nación / Clarín / Japan Times added to the international
-- mainstream bloc. WION deliberately left OUT of every card: its coverage here is
-- anti-Canada hypocrisy framing ("Treason much? Canada, host of Sikh separatists,
-- cries 'sovereignty'"), which fits neither the Western-consensus nor the
-- Russia/China bloc -- homeless beats mislabelled.
SET client_encoding TO 'UTF8';

-- ---- 1 + 2: Alberta narratives -----------------------------------------
UPDATE narratives_v2 SET
  framing_required = false,
  framing_keywords = ARRAY[
    'treason','dangerous','bluff','Brexit','quash','injunction','unconstitutional',
    'illegal','warns','unity','essential','best place','united Canada','deals blow',
    'concern','probing','electors list','voter data','respect Canadian sovereignty',
    'interference','opposition','defend Canadian','Landesverrat','Einheit',
    'verfassungswidrig','Einmischung'
  ],
  publishers = publishers || ARRAY['Straits Times','La Nación','Clarín','Japan Times'],
  updated_at = NOW()
WHERE id = 'alberta_unity_defence';

UPDATE narratives_v2 SET
  framing_keywords = ARRAY[
    'Western alienation','equalization','equalisation','resource revenue','landlocked',
    'grievance','frustration','neglect','ignored','left behind','oil-rich','richer',
    'argues','defends','concession','energy policy','folly','treaty rights',
    'Benachteiligung','Ausgleichszahlung','vernachlässigt'
  ],
  updated_at = NOW()
WHERE id = 'alberta_legitimate_grievance';

UPDATE narratives_v2 SET
  publishers = publishers || ARRAY['Press TV'],
  updated_at = NOW()
WHERE id IN ('alberta_external_amplification','usca_bloc_fracture','casp_imperial_overreach');

-- ---- international mainstream additions on the two dyad atomics ---------
UPDATE narratives_v2 SET
  publishers = publishers || ARRAY['Straits Times','La Nación','Clarín','Japan Times'],
  updated_at = NOW()
WHERE id IN ('usca_economic_coercion','casp_sovereignty_defence');

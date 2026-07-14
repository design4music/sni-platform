-- Fix A (sample re-ranking) for europe_us_theater: Greenland-tariff coverage is
-- 37% of transatlantic_trade and floats to the top of the atomic page + theater
-- cards because samples rank by framing_strength (count of framing_keywords in
-- the title) and the old keyword lists didn't privilege the structural disputes.
-- framing_keywords only RANK samples (framing_required=false -> no attribution
-- change, no re-bootstrap). We load them with SECTORAL / INSTRUMENT terms that
-- the real trade/defence/tech/autonomy stories carry but Greenland-coercion
-- titles do NOT (deliberately excluding bare 'tariff'/'trade war'/'sovereignty',
-- which Greenland titles share) -> structural titles land in framing_strength>0,
-- Greenland titles sink to the low bucket. The Greenland COUNT is unchanged
-- (~24%, honest); only what surfaces changes. Root de-dup is fix B (atomic
-- claim-precedence), proposed separately. Also loads the +2 cards with
-- America-First vocabulary so the little pro-Trump advocacy that exists surfaces.
SET client_encoding TO 'UTF8';

-- structural markers, all four domains, NO Greenland-shared generics:
--   trade:    steel/aluminium/autos/wine/digital-tax/trade-deal/Airbus/Boeing/WTO/Section 232
--   defence:  burden-sharing/defence-spending/troops/Ramstein/Article 5/nuclear umbrella
--   tech:     DMA/DSA/GDPR/AI Act/antitrust/Big Tech/digital sovereignty/cloud/gatekeeper
--   autonomy: EU army/defence union/strategic autonomy/ReArm/rearmament/deterrent/de-risking

-- ---- transatlantic_trade atomic narratives -------------------------------
UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'steel','aluminium','aluminum','car tariff','auto','automobile','vehicle','digital tax','digital services tax',
  'trade deal','trade agreement','framework','wine','whisky','whiskey','bourbon','export','trade deficit',
  'trade surplus','subsidy','subsidies','Airbus','Boeing','market access','WTO','Section 232','deadline',
  'pharmaceutical','semiconductor','fair share','unfair','surplus','reciprocal','America First','rip off',
  'level playing field','freeload','Stahl','Digitalsteuer','Autozölle','Handelsabkommen'
] WHERE id = 'trade_us_tariffs_justified';

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'steel','aluminium','aluminum','car tariff','auto','automobile','vehicle','digital tax','digital services tax',
  'trade deal','trade agreement','framework','wine','whisky','whiskey','bourbon','export','trade deficit',
  'trade surplus','subsidy','subsidies','Airbus','Boeing','market access','WTO','Section 232','deadline',
  'pharmaceutical','semiconductor','countermeasure','retaliate','counter-tariff','unity','negotiate',
  'escalation','Stahl','Digitalsteuer','Autozölle','Handelsabkommen','Gegenzoll'
] WHERE id = 'trade_european_defence';

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'steel','aluminium','aluminum','car tariff','auto','automobile','digital tax','digital services tax',
  'trade deal','wine','whisky','export','trade deficit','subsidy','Airbus','Boeing','market access','WTO',
  'semiconductor','pharmaceutical','vassal','milk','humiliation','submission','hypocrisy','extortion','multipolar'
] WHERE id = 'trade_western_vassalage';

-- ---- europe_us_theater cards (all 4 domains) -----------------------------
UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'steel','aluminium','car tariff','auto','automobile','digital tax','digital services tax','trade deal','framework',
  'wine','whisky','export','trade deficit','subsidy','Airbus','Boeing','WTO','semiconductor','pharmaceutical',
  'burden-sharing','burden sharing','defence spending','defense spending','troops','troop withdrawal','Ramstein',
  'Article 5','nuclear umbrella','extended deterrence','DMA','Digital Markets Act','DSA','antitrust','Big Tech',
  'GDPR','AI Act','digital sovereignty','cloud','gatekeeper','EU army','defence union','strategic autonomy',
  'ReArm','rearmament','deterrent','de-risking','fair share','freeload','unfair','America First','rip off',
  'reciprocal','pay up','delinquent','level playing field'
] WHERE id = 'europe_us_america_first';

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'steel','aluminium','car tariff','auto','automobile','digital tax','digital services tax','trade deal','framework',
  'wine','whisky','export','trade deficit','subsidy','Airbus','Boeing','WTO','semiconductor','pharmaceutical',
  'burden-sharing','burden sharing','defence spending','defense spending','troops','troop withdrawal','Ramstein',
  'Article 5','nuclear umbrella','extended deterrence','DMA','Digital Markets Act','DSA','antitrust','Big Tech',
  'GDPR','AI Act','digital sovereignty','cloud','gatekeeper','EU army','defence union','strategic autonomy',
  'ReArm','rearmament','deterrent','de-risking','countermeasure','unity','autonomy','reassure','unreliable'
] WHERE id = 'europe_us_transatlantic_rupture';

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'steel','aluminium','car tariff','auto','automobile','digital tax','digital services tax','trade deal','framework',
  'wine','whisky','export','trade deficit','subsidy','Airbus','Boeing','WTO','semiconductor','pharmaceutical',
  'burden-sharing','burden sharing','defence spending','defense spending','troops','troop withdrawal','Ramstein',
  'Article 5','nuclear umbrella','DMA','Digital Markets Act','DSA','antitrust','Big Tech','GDPR','AI Act',
  'digital sovereignty','cloud','gatekeeper','EU army','defence union','strategic autonomy','ReArm','rearmament',
  'deterrent','de-risking','vassal','hypocrisy','multipolar','humiliation','submission','end of hegemony'
] WHERE id = 'europe_us_western_disunity';

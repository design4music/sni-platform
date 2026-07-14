-- europe_us_theater centroid roles (FN_THEATER_BUILD_SPEC §2 / §4 step 4).
-- Archetype insight for asymmetric bilateral dyads: the European side is
-- multi-centroid, the US side is a single centroid. Put the multi side in
-- centroid_ids (OR-scope) and PIN the single side with primary_target so the
-- pair AND-gates -- generic 'tariff'/'trade deal'/'defence spending' stop
-- leaking to US-India / US-China / EU-Mercosur / US-domestic.
--   trade    : European scope + primary_target=USA
--   defence  : European scope (+NATO) + primary_target=USA
--   tech     : European scope, NULL target (keeps EU-decoupling half that
--              names no US firm; European actor always present drops US-domestic)
--   autonomy : European scope (+China third-pole), NULL target (concept
--              aliases self-gate; audited ~0% foreign)
-- USA is intentionally removed from trade/defence/tech centroid_ids so the
-- scope requires a European participant; primary_target re-adds the US AND-gate
-- where wanted. Reversible; local only.
SET client_encoding TO 'UTF8';

UPDATE friction_nodes SET
  centroid_ids = ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-BENELUX','EUROPE-NORDIC'],
  primary_target = 'AMERICAS-USA',
  updated_at = NOW()
WHERE id = 'transatlantic_trade';

UPDATE friction_nodes SET
  centroid_ids = ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-BENELUX','EUROPE-NORDIC','NON-STATE-NATO'],
  primary_target = 'AMERICAS-USA',
  updated_at = NOW()
WHERE id = 'europe_us_defence_dependence';

UPDATE friction_nodes SET
  centroid_ids = ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-BENELUX','EUROPE-NORDIC'],
  primary_target = NULL,
  updated_at = NOW()
WHERE id = 'europe_us_tech_sovereignty';

UPDATE friction_nodes SET
  centroid_ids = ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-BENELUX','EUROPE-NORDIC','ASIA-CHINA'],
  primary_target = NULL,
  updated_at = NOW()
WHERE id = 'eu_strategic_autonomy';

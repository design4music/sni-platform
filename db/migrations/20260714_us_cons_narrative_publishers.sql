-- Sync the +2 "America First" narrative publisher coalitions to the newly-added
-- conservative feed names so those outlets route into the +2 bucket once ingested.
-- Of the 6 new feeds, only 'National Review' was not already in the US-conservative
-- publisher arrays (New York Post / Breitbart / Newsmax / Washington Examiner /
-- The National Interest already present). Idempotent guard on array membership.
SET client_encoding TO 'UTF8';

UPDATE narratives_v2
SET publishers = array_append(publishers, 'National Review'), updated_at = NOW()
WHERE id IN ('trade_us_tariffs_justified','defence_europe_must_pay','autonomy_illusion',
             'tech_eu_overreach','europe_us_america_first')
  AND NOT ('National Review' = ANY(publishers));

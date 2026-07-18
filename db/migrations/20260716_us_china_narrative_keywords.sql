-- us_china_theater: framing-keyword calibration for the two framing_required
-- atomics (summit_diplomacy, trade_tariffs). Measured against real headlines.
--
-- Why only these two: tech_restrictions / ai_primacy / critical_minerals use
-- disjoint publisher coalitions (framing_required=false) and already attribute
-- correctly (234/26, 469/34, 91/16). Only the own-goal atomics, where the
-- Western bloc voices both stances, depend on keyword quality.
--
-- Before: summit 31/21, trade 3/15 -- the Western narratives were starved while
-- Chinese state (framing_required=false) captured ~everything, so the cards
-- read as though Beijing out-covered the Western press 2:1 on its own story.
-- After: summit ~49/59, trade ~6/29.
--
-- The residual drop is CORRECT, not a bug: the bulk of Western summit coverage
-- is stance-neutral wire copy ("Photos of Trump in China", "Trump China trip:
-- What to know", "Treasury Yields Cool Down as Trump Meets Xi") which belongs
-- to neither stance. Precision over recall (spec s5). This mirrors the Arctic
-- shape, where the ungated rift-exploitation narrative held 209 against gated
-- Western narratives at 90 and 5.
--
-- FIXES from reading actual sample titles (the eu_cohesion 2026-07-15 lesson --
-- keywords are ILIKE SUBSTRING, so a negation contains its own positive):
--   * 'commitment' REMOVED from summit +1: fired on "Trump says he gave Xi
--     'no commitment' on Taiwan at summit" -- filed a concession as engagement.
--   * 'ramps up' REMOVED from summit +1: fired on "White House quiet as CHINA
--     ramps up trade leverage" -- wrong actor.
--   * 'countermeasure' REMOVED from trade -1: fired on "China says it will
--     decide on US tariff countermeasures" -- a report of Beijing's position,
--     not a Western self-critique.
--   * 'no plans' REMOVED from trade -1: fired on "Carney says Canada has no
--     plans to pursue free trade agreement with China" -- that is alignment
--     WITH US pressure, the opposite stance.
--   * 'in focus ahead', bare 'drop'/'scrap'/'damage'/'warns' REMOVED from
--     trade -1: neutral, or reports of Chinese demands.
--   * 'plead' / 'press Trump' MOVED from trade -1 to +1: "US industry,
--     lawmakers plead with Trump: Don't open door to Chinese cars" and
--     "Toyota, GM press Trump to KEEP China auto import restrictions" are
--     pro-restriction, not anti-tariff.
--
-- SUBSTANTIVE FINDING (not a tuning artifact): us_china_tariff_leverage stays
-- tiny (~6) because the "tariffs are working leverage" stance barely exists in
-- 2026 Western headlines. Only 130 Western trade titles exist in the dyad, and
-- even a deliberately broad positive list matches 4-6. After the Supreme Court
-- blunted tariff authority and the summit negotiated reductions, Western
-- coverage is near-uniformly skeptical -- Fox's own op-ed calls the tariff "an
-- expensive gift to China". The narrative is kept ACTIVE: the stance is real,
-- merely weakly voiced, and the daemon will populate it if coverage turns.

BEGIN;

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'successful','stabilis','stabiliz','stability','guardrail','consensus','landmark','historic',
  'momentum','reset','thaw','pragmatic','win-win','mutual respect','fruitful','lower tariffs',
  'tariff cuts','cut tariffs','renews','agreed to','cooperation','very positive','conciliation',
  'admires','friendly','harmon','invites','expects to host','deeper','all business','import permit',
  'buys more','opens up','open up',
  'erfolgreich','Stabilität','Leitplanken','Konsens','Dynamik','Zollsenkung','Zusammenarbeit','Harmonie'
], updated_at = now()
WHERE id = 'us_china_summit_engagement_works';

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'stalemate','few wins','empty-handed','no deals','no commitment','no sign','without a deal',
  'little to show','preliminary','exposes','upper hand','capitulat','concession','gave away',
  'flat-out disaster','embarrassment','failed to','whipsaw','stumble','limits on','no major',
  'tightrope','treads carefully','fights with allies','quiet as','gives Beijing','Beijing a win',
  'Patt','kaum Erfolge','keine Abschlüsse','vorläufig','Oberhand','Zugeständnis','bedürftiger'
], updated_at = now()
WHERE id = 'us_china_summit_weak_hand';

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'leverage against','reciprocal','market access','overcapacity','level playing field','unfair',
  'subsidis','subsidiz','dumping','import permit','import commitments','buys more',
  'eligible for tariff cuts','farmers eye','trade ramps','ramps up','plead','press Trump',
  'keep China auto',
  'Druckmittel','Gegenseitigkeit','Marktzugang','Überkapazität','unfair'
], updated_at = now()
WHERE id = 'us_china_tariff_leverage';

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'chaos','uncertainty','backfire','higher prices','retaliat','gives Beijing','Beijing a win',
  'real winner','upper hand','opening in','blunts','turmoil','slump','reversal','profit hit',
  'expensive gift','pay for it','scepticism','skepticism','evasion','scramble','hedge',
  'strategic partnership','files lawsuit','cut 50,000','jobs by','learned to live',
  'Chaos','Unsicherheit','Vergeltung','warnen'
], updated_at = now()
WHERE id = 'us_china_tariff_self_harm';

COMMIT;

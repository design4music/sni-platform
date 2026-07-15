-- eu_cohesion_theater — stance-label correctness fix after roll-up spot-check.
-- The sovereigntist (-1) narratives had picked up stance-AMBIGUOUS framing keywords
-- that also occur in the OPPOSITE (pro-firewall / anti-cooperation) coverage:
--   'Zusammenarbeit mit der AfD' appears in both "empfiehlt Zusammenarbeit" (sympathetic)
--   and "warnt vor Zusammenarbeit" (critical); 'work with'/'shift right'/'normalis'
--   likewise. That mislabelled pro-firewall headlines as sovereigntist-sympathetic.
-- Keep only UNAMBIGUOUSLY sympathetic terms. Result: thinner but correctly-signed
-- cards (precision over recall). Requires re-bootstrap of afd + realignment.
SET client_encoding TO 'UTF8';

UPDATE narratives_v2 SET
  framing_keywords = ARRAY['millions of voters','Millionen Wähler','undemocratic','undemokratisch','free speech','Meinungsfreiheit','censorship','Zensur','witch hunt','stigmatis','disenfranchise','second-class','double standard','normal party'],
  updated_at = NOW()
WHERE id = 'afd_exclusion_undemocratic';

UPDATE narratives_v2 SET
  framing_keywords = ARRAY['democratic mandate','mandate to govern','legitimate majority','listen to voters','represent the voters','new majority','overdue','normal coalition partner'],
  updated_at = NOW()
WHERE id = 'realignment_new_majority';

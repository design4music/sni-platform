-- eu_cohesion_theater — narrative tuning after first bootstrap measurement.
-- (1) hungary_brussels_coercion over-captured (317): Hungary's fn_anchor is a broad
--     NAME-gate (Orban/Budapest/Fidesz), so a framing_required=false Kremlin narrative
--     swept in all Russian-language Hungary news (visas, Ukraine-accession vetoes,
--     Fidesz internals) and mislabelled it "EU coercion". Unlike the topic-tight
--     bundles (afd/migration/budget), a name-gated atomic needs its Kremlin narrative
--     framing-gated too -> set framing_required=true + EN/RU coercion keywords.
-- (2) Four narratives fired only once because their framing keywords were too abstract
--     to appear in headline text. Broaden to concrete terms that occur in real titles.
-- Requires a re-bootstrap of the affected atomics to re-attribute title_narratives.
SET client_encoding TO 'UTF8';

UPDATE narratives_v2 SET
  framing_required = true,
  framing_keywords = ARRAY['coercion','blackmail','pressure','sovereignty','voting rights','deprive','frozen funds','sanction','diktat','interfere','punish','double standard','давлени','шантаж','санкц','суверенитет','вмешательств','лишени права','заморож','наказа'],
  updated_at = NOW()
WHERE id = 'hungary_brussels_coercion';

UPDATE narratives_v2 SET
  framing_keywords = ARRAY['own resources','Eigenmittel','larger budget','bigger budget','more ambitious','ambitious budget','backs larger','defend the budget','safeguards','biodiversity','green spending','new own resources','joint borrowing','Eurobond','common debt','gemeinsame Schulden','größeren Haushalt','competitiveness','invest','defence fund'],
  updated_at = NOW()
WHERE id = 'budget_more_europe';

UPDATE narratives_v2 SET
  framing_keywords = ARRAY['millions of voters','Millionen Wähler','undemocratic','undemokratisch','establishment','free speech','Meinungsfreiheit','censorship','Zensur','witch hunt','Zusammenarbeit mit der AfD','cooperation with the AfD','Annäherung','Tabubruch','normalis','stigmatis','disenfranchise','second-class','double standard','einbinden'],
  updated_at = NOW()
WHERE id = 'afd_exclusion_undemocratic';

UPDATE narratives_v2 SET
  framing_keywords = ARRAY['will of the people','volonté populaire','popular will','establishment','witch hunt','acharnement','judicial coup','déni de démocratie','anti-democratic','muzzle','museler','disqualify','ban Le Pen','barred','deny voters','front-runner','favourite','persecution','exclu'],
  updated_at = NOW()
WHERE id = 'france_popular_will';

UPDATE narratives_v2 SET
  framing_keywords = ARRAY['mandate','majority','Mehrheit','legitimate','voters','Wähler','pragmatic','new majority','represent','realign','work with','vote with','join forces','common ground','listen to voters','cooperation legitimate','overdue','mainstream right','shift right','normalis'],
  updated_at = NOW()
WHERE id = 'realignment_new_majority';

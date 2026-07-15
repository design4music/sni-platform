-- eu_cohesion_theater — hungary_sovereignty_interference correction.
-- Migration 09 moved it to SOV_CORE-only (like afd/france), but Hungary differs: unlike
-- the AfD/RN case where mainstream is monolithically critical, the -1 Hungary critique
-- ("is Magyar's purge political revenge?", rule-of-law doubts about the new government)
-- genuinely appears in MAINSTREAM coverage too. SOV_CORE-only dropped it 12->3. Treat it
-- like the policy atomics: MAINSTREAM+ + SOV_CORE with framing_required=true, so the
-- revenge/sovereignty framing keywords carry the mainstream critique and the sovereigntist
-- bloc adds its sympathetic-to-Orbán coverage.
SET client_encoding TO 'UTF8';

UPDATE narratives_v2 SET framing_required = true, publishers = ARRAY[
  'Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier','eKathimerini','WELT','Cicero','Le Point','El Debate','Junge Freiheit','NIUS','Tichys Einblick','Valeurs Actuelles','Causeur','Boulevard Voltaire','Il Giornale','Libero','La Verità','OKdiario','Libertad Digital','Brussels Signal'],
  updated_at = NOW()
WHERE id = 'hungary_sovereignty_interference';

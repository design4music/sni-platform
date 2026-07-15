-- eu_cohesion_theater — coalition restructure now that a sovereigntist publisher bloc
-- exists (migration 08). framing_required=true was a WORKAROUND for the sources gap:
-- with no sovereigntist outlets, the sympathetic and critical narratives had to share the
-- mainstream coalition and be split by framing keywords. Now we have a disjoint
-- sovereigntist bloc, so the polarisation atomics revert to the spec's DEFAULT model —
-- disjoint publisher coalitions, framing_required=false, publisher alone disambiguates
-- stance. (afd_exclusion stayed 0 because its English keywords never matched the German
-- vocabulary Junge Freiheit/NIUS/Tichys actually use — "AfD-Verbot", "Brandmauer",
-- "Märtyrerstatus" — publisher purity captures them cleanly instead.)
--
-- Blocs:
--   MAINSTREAM+  = liberal/centrist Western + wire + establishment centre-right
--                  (WELT/Cicero/Le Point/El Debate — these lean pro-cohesion like the mainstream)
--   SOV_CORE     = clearly national-conservative/sovereigntist (disjoint from mainstream stance)
--
-- Polarisation atomics (afd/france/hungary/realignment): stance tracks the bloc.
--   +2 = MAINSTREAM+ (framing_required=true, keeps neutral coverage out of the "defence" card)
--   -1 = SOV_CORE only (framing_required=false, publisher suffices)
-- Policy atomics (migration/budget): the -1 stance (restriction / net-payer) legitimately
--   appears in mainstream too, so -1 keeps framing_required=true over MAINSTREAM+ + SOV_CORE.
SET client_encoding TO 'UTF8';

-- MAINSTREAM+ = original Western coalition + establishment centre-right.
-- (Written out per statement below; SOV_CORE removed from +2 where migration 08 had added all 16.)

-- ---- Polarisation +2: MAINSTREAM+ , framing_required=true ----
UPDATE narratives_v2 SET framing_required = true, publishers = ARRAY[
  'Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier','eKathimerini','WELT','Cicero','Le Point','El Debate'],
  updated_at = NOW()
WHERE id IN ('hungary_eu_standards','afd_democratic_defense','france_republican_defense','realignment_firewall_defense');

-- ---- Polarisation -1: SOV_CORE only, framing_required=false ----
UPDATE narratives_v2 SET framing_required = false, publishers = ARRAY[
  'Junge Freiheit','NIUS','Tichys Einblick','Valeurs Actuelles','Causeur','Boulevard Voltaire','Il Giornale','Libero','La Verità','OKdiario','Libertad Digital','Brussels Signal'],
  updated_at = NOW()
WHERE id IN ('hungary_sovereignty_interference','afd_exclusion_undemocratic','france_popular_will','realignment_new_majority');

-- ---- Policy +2: MAINSTREAM+ , framing_required=true (SOV_CORE removed) ----
UPDATE narratives_v2 SET framing_required = true, publishers = ARRAY[
  'Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier','eKathimerini','WELT','Cicero','Le Point','El Debate'],
  updated_at = NOW()
WHERE id IN ('migration_solidarity_rights','budget_more_europe');

-- ---- Policy -1: MAINSTREAM+ + SOV_CORE, framing_required=true (stance spans coalitions) ----
UPDATE narratives_v2 SET framing_required = true, publishers = ARRAY[
  'Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier','eKathimerini','WELT','Cicero','Le Point','El Debate','Junge Freiheit','NIUS','Tichys Einblick','Valeurs Actuelles','Causeur','Boulevard Voltaire','Il Giornale','Libero','La Verità','OKdiario','Libertad Digital','Brussels Signal'],
  updated_at = NOW()
WHERE id IN ('migration_national_control','budget_national_sovereignty');

-- ---- Theater +2 card: MAINSTREAM+ (SOV_CORE removed) ----
UPDATE narratives_v2 SET publishers = ARRAY[
  'Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier','eKathimerini','WELT','Cicero','Le Point','El Debate'],
  updated_at = NOW()
WHERE id = 'eu_cohesion_hold';

-- ---- Theater -1 card: MAINSTREAM+ + SOV_CORE (catches both mainstream restriction titles
--      and the sovereigntist bloc's sympathetic titles) ----
UPDATE narratives_v2 SET publishers = ARRAY[
  'Reuters','BBC World','The Guardian','Financial Times','Associated Press','AFP','Euronews','Deutsche Welle','France 24 (EN)','France 24','CNN','New York Times','Politico','Der Spiegel','Süddeutsche Zeitung','Die Zeit','Tagesschau','Le Monde','La Repubblica','El País','ANSA','EurActiv','Sky News','Handelsblatt','Frankfurter Allgemeine','Le Figaro','Corriere della Sera','El Mundo','The Telegraph','Wall Street Journal','Bloomberg','Die Presse','Der Standard','Kurier','eKathimerini','WELT','Cicero','Le Point','El Debate','Junge Freiheit','NIUS','Tichys Einblick','Valeurs Actuelles','Causeur','Boulevard Voltaire','Il Giornale','Libero','La Verità','OKdiario','Libertad Digital','Brussels Signal'],
  updated_at = NOW()
WHERE id = 'eu_sovereigntist_revolt';

-- europe_us_theater structural build (FN_THEATER_BUILD_SPEC §0a step 2).
-- Approved decomposition (4 atomics, values-rift -> theater narrative only):
--   transatlantic_trade            (bilateral)        tariffs / trade disputes
--   europe_us_defence_dependence   (bilateral)        burden-sharing / US security guarantee
--   eu_strategic_autonomy          (EU-response)      autonomy / rearmament / self-reliance
--   europe_us_tech_sovereignty     (bilateral, NEW)   tech regulation / digital sovereignty
--
-- Structural fixes applied here:
--   * Widen atomic centroid_ids from {NON-STATE-EU, AMERICAS-USA} to the real
--     transatlantic participant set (national EU centroids dominate coverage:
--     ~78% of US+European tension titles tag DE/FR/UK/SOUTH not NON-STATE-EU).
--   * Remove stale EUROPE-GREENLAND from the theater (greenland_control moved to
--     arctic_theater 2026-07-14).
--   * Create the new tech-sovereignty atomic; add it to member_fn_ids.
--   * Fill name_de + description_en/_de (were null) for theater + all 4 atomics.
-- primary_target left null on all (bilateral, or EU-subject spread across many
-- centroids -> concept-alias purity gates instead). Reversible; local only.
SET client_encoding TO 'UTF8';

-- ---- new atomic ---------------------------------------------------------
INSERT INTO friction_nodes (id, name_en, name_de, fn_type, scope, is_active, display_order, centroid_ids, primary_target)
VALUES (
  'europe_us_tech_sovereignty',
  'Transatlantic tech regulation and digital sovereignty',
  'Transatlantische Techregulierung und digitale Souveränität',
  'atomic', 'regional', true, 32,
  ARRAY['NON-STATE-EU','AMERICAS-USA','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-BENELUX','EUROPE-NORDIC'],
  NULL
)
ON CONFLICT (id) DO NOTHING;

-- ---- centroid widening + names/descriptions: atomics --------------------
UPDATE friction_nodes SET
  centroid_ids = ARRAY['NON-STATE-EU','AMERICAS-USA','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-BENELUX','EUROPE-NORDIC'],
  name_de = 'Transatlantische Handelskonflikte und Zölle',
  description_en = 'The tariff and trade confrontation between the United States and the European Union under a protectionist Washington: US duties on European steel, aluminium, cars and other goods, the threatened and imposed counter-tariffs from Brussels, and the fragile framework trade deal negotiated to contain them. It extends to digital-services taxes, subsidy and market-access disputes and the Airbus-Boeing legacy, with European unity repeatedly tested over whether to retaliate against Washington or accommodate it.',
  description_de = 'Die Zoll- und Handelskonfrontation zwischen den USA und der Europäischen Union unter einem protektionistischen Washington: US-Abgaben auf europäischen Stahl, Aluminium, Autos und andere Waren, die angedrohten und verhängten Gegenzölle aus Brüssel und das fragile Rahmen-Handelsabkommen, das sie eindämmen soll. Sie reicht bis zu Digitalsteuern, Subventions- und Marktzugangsstreitigkeiten und dem Airbus-Boeing-Erbe, wobei die europäische Einigkeit immer wieder auf die Probe gestellt wird — Vergeltung gegen Washington oder Entgegenkommen.',
  updated_at = NOW()
WHERE id = 'transatlantic_trade';

UPDATE friction_nodes SET
  centroid_ids = ARRAY['NON-STATE-EU','AMERICAS-USA','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-BENELUX','EUROPE-NORDIC','NON-STATE-NATO'],
  name_en = 'Defence burden-sharing and US security guarantees',
  name_de = 'Verteidigungslastenteilung und US-Sicherheitsgarantien',
  description_en = 'The transactional dispute over who pays for and who guarantees European security. Washington presses its European allies to raise defence spending toward higher NATO targets, threatens and moves to draw down American troops in Europe, and casts doubt over the credibility of the US security guarantee and nuclear umbrella. Europeans are caught between paying more to keep Washington engaged and preparing for an America that may no longer come to their defence.',
  description_de = 'Der transaktionale Streit darüber, wer die europäische Sicherheit bezahlt und garantiert. Washington drängt seine europäischen Verbündeten, die Verteidigungsausgaben auf höhere NATO-Ziele anzuheben, droht mit dem Abzug amerikanischer Truppen aus Europa und zieht die Glaubwürdigkeit der US-Sicherheitsgarantie und des nuklearen Schirms in Zweifel. Die Europäer stehen zwischen der Notwendigkeit, mehr zu zahlen, um Washington eingebunden zu halten, und der Vorbereitung auf ein Amerika, das ihnen womöglich nicht mehr zu Hilfe kommt.',
  updated_at = NOW()
WHERE id = 'europe_us_defence_dependence';

UPDATE friction_nodes SET
  centroid_ids = ARRAY['NON-STATE-EU','AMERICAS-USA','ASIA-CHINA','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-BENELUX','EUROPE-NORDIC'],
  name_en = 'European strategic autonomy and defence self-reliance',
  name_de = 'Europäische strategische Autonomie und verteidigungspolitische Eigenständigkeit',
  description_en = 'Europe''s drive to act as an independent strategic pole — to build the capacity to defend itself and decide for itself with less reliance on the United States. It spans the push for a European defence union, an "EU army" and a European nuclear deterrent, rearmament initiatives such as ReArm Europe and Readiness 2030, industrial sovereignty, and de-risking from dependence on both Washington and Beijing. The open question is whether Europe can and should emancipate itself, or whether strategic autonomy is an illusion without American power.',
  description_de = 'Europas Bestreben, als eigenständiger strategischer Pol zu handeln — die Fähigkeit aufzubauen, sich selbst zu verteidigen und selbst zu entscheiden, mit geringerer Abhängigkeit von den USA. Es umfasst den Vorstoß zu einer europäischen Verteidigungsunion, einer „EU-Armee" und einer europäischen nuklearen Abschreckung, Aufrüstungsinitiativen wie ReArm Europe und Readiness 2030, industrielle Souveränität und die Verringerung der Abhängigkeit von Washington wie von Peking. Offen ist, ob Europa sich emanzipieren kann und soll oder ob strategische Autonomie ohne amerikanische Macht eine Illusion bleibt.',
  updated_at = NOW()
WHERE id = 'eu_strategic_autonomy';

UPDATE friction_nodes SET
  description_en = 'The friction between European regulators and American technology power. The EU enforces the Digital Markets Act, Digital Services Act, GDPR and AI Act against US Big Tech through fines, antitrust probes and content rules; Washington pushes back in defence of its firms, threatening tariffs over "unfair" treatment; and Europe pursues digital sovereignty in parallel, weaning its cloud, software and defence data off American providers. It pits European rule-making and "sovereign cloud" ambitions against Silicon Valley''s dominance and US retaliation.',
  description_de = 'Die Reibung zwischen europäischen Regulierern und amerikanischer Technologiemacht. Die EU setzt den Digital Markets Act, den Digital Services Act, die DSGVO und den AI Act gegen die US-Techkonzerne durch — mit Bußgeldern, Kartellverfahren und Inhaltsregeln; Washington wehrt sich zur Verteidigung seiner Konzerne und droht mit Zöllen wegen „unfairer" Behandlung; und Europa verfolgt parallel die digitale Souveränität, indem es Cloud, Software und Verteidigungsdaten von amerikanischen Anbietern löst. Europäische Regelsetzung und „souveräne Cloud"-Ambitionen stehen gegen die Dominanz des Silicon Valley und US-Vergeltung.',
  updated_at = NOW()
WHERE id = 'europe_us_tech_sovereignty';

-- ---- theater: drop stale Greenland, add NATO, add tech atomic, names/desc
UPDATE friction_nodes SET
  centroid_ids = ARRAY['NON-STATE-EU','AMERICAS-USA','ASIA-CHINA','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-BENELUX','EUROPE-NORDIC','NON-STATE-NATO'],
  member_fn_ids = ARRAY['transatlantic_trade','europe_us_defence_dependence','eu_strategic_autonomy','europe_us_tech_sovereignty'],
  name_de = 'Strategische Spannungen zwischen Europa und den USA',
  description_en = 'The widening rift between the United States and its European allies under a Washington that treats Europe more as a competitor than a partner. It runs along four axes: a tariff and trade confrontation; a dispute over defence burden-sharing and the credibility of the US security guarantee; Europe''s answering drive for strategic autonomy and rearmament; and a clash over technology regulation and digital sovereignty. Beneath them runs a deeper question of whether the transatlantic alliance that defined the post-war order still holds — a fracture Moscow and Beijing cover with schadenfreude.',
  description_de = 'Der wachsende Riss zwischen den USA und ihren europäischen Verbündeten unter einem Washington, das Europa eher als Konkurrenten denn als Partner behandelt. Er verläuft entlang vier Achsen: einer Zoll- und Handelskonfrontation; eines Streits über die Verteidigungslastenteilung und die Glaubwürdigkeit der US-Sicherheitsgarantie; Europas Gegenbewegung hin zu strategischer Autonomie und Aufrüstung; und eines Konflikts über Technologieregulierung und digitale Souveränität. Darunter liegt die tiefere Frage, ob das transatlantische Bündnis, das die Nachkriegsordnung prägte, noch trägt — ein Bruch, den Moskau und Peking mit Schadenfreude begleiten.',
  updated_at = NOW()
WHERE id = 'europe_us_theater';

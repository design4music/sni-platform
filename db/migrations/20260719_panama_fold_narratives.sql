-- Narratives for latam_port_infrastructure_control (2026-07-19)
--
-- Three-stance gradient (FN_THEATER_BUILD_SPEC.md section 5). The Western
-- coalition is NOT uniformly supportive here: the same outlets that report
-- the eviction as a security win also report the US military buildup as a
-- squeeze on a small state (Bloomberg: "Trump's Aggressive Military Buildup
-- in Panama Is Keeping Latin America on Edge"). That is the own-goal shape --
-- so the +2 and -1 cards share the Western bloc, both framing_required=true
-- with disjoint keywords, while the Chinese/Russian state bloc keeps its own
-- disjoint coalition at framing_required=false.
--
-- NO rift-exploitation card (contrast Arctic). China is a PRINCIPAL PARTY to
-- this dispute -- its operator was evicted -- so its coverage belongs on the
-- dispute's own pro/con axis, not on a bystander "Western hypocrisy" axis.
-- Same call as the SCS build.

BEGIN;

INSERT INTO narratives_v2 (
    id, fn_id, display_order, stance, framing_required,
    name_en, name_de, claim_en, claim_de,
    stance_label_en, stance_label_de, actor_centroids, publishers, framing_keywords, is_active
) VALUES

-- +2 host-state control restored, Chinese operator was a real vulnerability
('port_control_restored', 'latam_port_infrastructure_control', 1, 2, true,
 'Host-state control restored',
 'Wiederhergestellte Kontrolle des Gastlandes',
 'Courts in Panama and Peru acted lawfully to return chokepoint terminals to host-state control, closing a strategic vulnerability created by operators answerable to Beijing; China''s response -- detaining Panama-flagged vessels and pressing carriers to withdraw -- confirms the risk it was meant to address.',
 'Gerichte in Panama und Peru haben rechtmäßig gehandelt, um Terminals an Nadelöhren wieder unter die Kontrolle des Gastlandes zu bringen und eine strategische Verwundbarkeit durch Betreiber im Einflussbereich Pekings zu beseitigen; Chinas Reaktion -- das Festhalten von Schiffen unter Panama-Flagge und der Druck auf Reedereien, sich zurückzuziehen -- bestätigt genau das Risiko, um das es ging.',
 'Lawful reassertion of control', 'Rechtmäßige Rückgewinnung der Kontrolle',
 ARRAY['AMERICAS-CENTRAL','AMERICAS-ANDEAN','AMERICAS-USA'],
 ARRAY['Reuters','Financial Times','Wall Street Journal','Bloomberg','Associated Press','AP News','Nikkei Asia','Fox News','CNN','The Telegraph','Deutsche Welle','Le Monde','El País','Euronews','EurActiv','France 24 (EN)','Japan Times','S&P Global','The Guardian','BBC News','New York Times','Washington Post','Der Spiegel','Handelsblatt'],
 ARRAY['sovereignt','Souveränität','soberan','unconstitutional','verfassungswidrig','inconstitucional','court','Gericht','ruling','Urteil','takes back','reclaim','zurück','security risk','Sicherheitsrisiko','vulnerab','verwundbar','de-risk','bullying','coercion','Zwang','retaliation','Vergeltung','detention','detentions','non-negotiable','backs Panama','joint statement'],
 true),

-- -1 friendly critic: a small state as great-power battleground
('port_sovereignty_squeeze', 'latam_port_infrastructure_control', 2, -1, true,
 'A small state squeezed between two powers',
 'Ein kleiner Staat zwischen zwei Mächten',
 'Whatever the legal merits, Panama and Peru are being made the terrain of a US-China contest they did not choose: Washington backs its case with a military buildup and hemispheric-sovereignty rhetoric while Beijing answers with shipping coercion, and the host states absorb the cost of both.',
 'Ungeachtet der Rechtslage werden Panama und Peru zum Austragungsort eines US-chinesischen Wettstreits, den sie nicht gewählt haben: Washington untermauert seine Position mit militärischem Aufmarsch und Rhetorik zur Souveränität der Hemisphäre, Peking antwortet mit Druck auf die Schifffahrt -- und die Gastländer tragen die Kosten beider Seiten.',
 'Great-power squeeze on the host state', 'Großmachtdruck auf das Gastland',
 ARRAY['AMERICAS-CENTRAL','AMERICAS-ANDEAN'],
 ARRAY['Reuters','Financial Times','Wall Street Journal','Bloomberg','Associated Press','AP News','Nikkei Asia','Fox News','CNN','The Telegraph','Deutsche Welle','Le Monde','El País','Euronews','EurActiv','France 24 (EN)','Japan Times','S&P Global','The Guardian','BBC News','New York Times','Washington Post','Der Spiegel','Handelsblatt','Al Jazeera','Anadolu Agency','The Hindu','Times of India','Al Arabiya','Daily Sabah','Gulf News','Republic TV','NDTV','Straits Times'],
 ARRAY['on edge','caught','military','Militär','militar','buildup','Aufmarsch','flexing','tension','Spannung','tensión','ramping up','escalat','Eskalat','clash','great power','Großmacht','squeez','pressure on','Druck auf','troops','Truppen','Southern Command','hemisphere'],
 true),

-- -2 adversary bloc: expropriation and US coercion of a smaller state
('port_expropriation_coercion', 'latam_port_infrastructure_control', 3, -2, false,
 'Expropriation under US pressure',
 'Enteignung unter US-Druck',
 'The port rulings were not independent justice but the product of US coercion: a lawful commercial concession was torn up and Chinese-linked assets stripped to satisfy Washington, which openly covets the waterway itself -- a cold-war reflex that punishes companies for their nationality and leaves host states less sovereign, not more.',
 'Die Hafenurteile waren keine unabhängige Justiz, sondern das Ergebnis von US-Zwang: Eine rechtmäßige kommerzielle Konzession wurde annulliert und chinesisch verbundene Vermögenswerte enteignet, um Washington zufriedenzustellen, das offen nach der Wasserstraße selbst greift -- ein Reflex des Kalten Krieges, der Unternehmen für ihre Nationalität bestraft und die Gastländer weniger souverän zurücklässt, nicht souveräner.',
 'Politicised seizure of commercial assets', 'Politisierte Enteignung kommerzieller Vermögenswerte',
 ARRAY['ASIA-CHINA','ASIA-HONGKONG'],
 ARRAY['Global Times','People''s Daily','CGTN','China Daily','Xinhua','RT','TASS','Sputnik'],
 ARRAY['cold war mentality','Kalter Krieg','coveting','covets','smear','groundless','hypocri','Heuchelei','lawful','legitimate rights','rights and interests','politiciz','politicis','politisier','heavy price','interference','Einmischung','unilateral'],
 true)

ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id, display_order = EXCLUDED.display_order,
    stance = EXCLUDED.stance, framing_required = EXCLUDED.framing_required,
    name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
    stance_label_en = EXCLUDED.stance_label_en, stance_label_de = EXCLUDED.stance_label_de,
    actor_centroids = EXCLUDED.actor_centroids, publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords, is_active = true, updated_at = NOW();

COMMIT;

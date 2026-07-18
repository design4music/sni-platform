-- Myanmar civil conflict: atomic narratives (FN_THEATER_BUILD_SPEC 5).
--
-- Single standalone atomic => no theater roll-up (5.5 disjointness rule N/A);
-- atomic narratives may co-apply. Three cards:
--   +2 beijing_backed_normalisation  (framing_required=true)
--   -2 illegitimate_junta_rule        (framing_required=false, publisher suffices)
--   -1 criminal_economy_spillover     (framing_required=true, carves crime titles)
--
-- Camp check (5): NOT an own-goal topic -- Western/regional press is uniformly
-- critical of the junta, Chinese/Russian state uniformly normalising, so no
-- friendly-critic gradient. NOT intra-Western -- China is a principal patron,
-- not a rift-exploiting bystander, so its coverage sits on the +2 axis (its real
-- stance), not a separate rift card (SCS rule, not Arctic).
--
-- Why +2 needs framing_required: Chinese state media publish BOTH normalisation
-- and scam-crackdown ("China executes Myanmar scam mafia") stories. Publisher
-- alone would file the execution stories under "legitimate transition". The
-- framing gate keeps +2 to genuine normalisation coverage; the execution stories
-- route to the crime card instead.

BEGIN;

INSERT INTO narratives_v2
  (id, fn_id, name_en, name_de, claim_en, claim_de,
   stance, stance_label_en, stance_label_de,
   actor_centroids, publishers, framing_keywords, framing_required,
   display_order, is_active, created_at, updated_at)
VALUES
(
  'myanmar_beijing_backed_normalisation', 'myanmar_civil_conflict',
  'Legitimate transition, backed by Beijing',
  'Legitimer Übergang, von Peking gestützt',
  'Myanmar''s election and handover to a civilian-led government mark a return to constitutional order; China and other partners back the country''s sovereignty, security and stability through pragmatic cooperation and renewed engagement.',
  'Myanmars Wahl und die Übergabe an eine zivil geführte Regierung markieren eine Rückkehr zur verfassungsmäßigen Ordnung; China und weitere Partner stützen Souveränität, Sicherheit und Stabilität des Landes durch pragmatische Zusammenarbeit und erneutes Engagement.',
  2, 'Normalisation and engagement', 'Normalisierung und Engagement',
  ARRAY['ASIA-CHINA','EUROPE-RUSSIA','ASIA-SOUTHEAST'],
  ARRAY['CGTN','China Daily','Global Times','People''s Daily','TASS (EN)','TASS','RT','RIA Novosti','Izvestia','Lenta.ru','Kommersant','BelTA','BelTA Russian','Press TV','Dawn'],
  ARRAY['pragmatic cooperation','deepen cooperation','state visit','bilateral ties','sovereignty','stability','civilian government','return to','re-engagement','detente','back its security','momentum','pragmatische Zusammenarbeit','Stabilität','Souveränität','zivile Regierung','Staatsbesuch','务实合作','国事访问','主权','稳定','сотрудничество','стабильность','суверенитет'],
  true, 1, true, now(), now()
),
(
  'myanmar_illegitimate_junta_rule', 'myanmar_civil_conflict',
  'Sham election, illegitimate junta',
  'Scheinwahl, illegitime Junta',
  'The military''s election was staged to launder its coup; the junta rules without a mandate, jails elected leaders such as Aung San Suu Kyi, and wages airstrikes and mass violence against civilians.',
  'Die Wahl des Militärs wurde inszeniert, um den Putsch zu legitimieren; die Junta regiert ohne Mandat, inhaftiert gewählte Politiker wie Aung San Suu Kyi und führt Luftangriffe und Gewalt gegen Zivilisten.',
  -2, 'Illegitimate military rule', 'Illegitime Militärherrschaft',
  ARRAY['AMERICAS-USA','NON-STATE-EU','ASIA-SOUTHEAST','ASIA-JAPAN'],
  ARRAY['BBC World','The Guardian','Deutsche Welle','France 24 (EN)','NPR','New York Times','Washington Post','CNN','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Der Standard','Die Presse','Handelsblatt','Kurier','Tagesschau','El País','Corriere della Sera','La Repubblica','Euronews','Sky News','Financial Times','The Telegraph','The Economist','CBC','Swissinfo','ERR News','DR','iROZHLAS','Associated Press','AFP','Reuters','Bangkok Post','Channel NewsAsia','Straits Times','New Straits Times','Nikkei Asia','The Nation Thailand','Japan Times','Asahi Shimbun','NHK World','Kyodo News','ABC News','The Australian','Philippine Daily Inquirer','Jakarta Post','Jakarta Globe','Cebu Daily News','VN Express','Al Jazeera','TRT World','Arab News','Daily Sabah','Anadolu Agency','UN News','NDTV','Times of India','Hindustan Times','The Hindu','Indian Express','DD India','WION','Dhaka Tribune','News24','Daily Nation','Daily Maverick','Daily Mirror','Punch','Kyiv Post','Jerusalem Post','Daily Star','The Star'],
  ARRAY['sham','junta','coup','airstrike','air strike','house arrest','Suu Kyi','political prisoner','atrocities','killed','crackdown','sham poll','illegitimate','Scheinwahl','Junta','Putsch','Luftangriff','Hausarrest'],
  false, 2, true, now(), now()
),
(
  'myanmar_criminal_economy_spillover', 'myanmar_civil_conflict',
  'Scam-compound economy and cross-border crime',
  'Betrugszentren und grenzüberschreitende Kriminalität',
  'Myanmar''s lawless border zones host industrial-scale scam compounds and human-trafficking operations whose victims and proceeds spill across the region, drawing Chinese executions, foreign rescues and cross-border enforcement.',
  'Myanmars rechtsfreie Grenzregionen beherbergen Betrugszentren und Menschenhandel im industriellen Maßstab, deren Opfer und Erlöse in die Region überschwappen und chinesische Hinrichtungen, ausländische Rettungen und grenzüberschreitende Strafverfolgung nach sich ziehen.',
  -1, 'Transnational criminal spillover', 'Transnationaler Kriminalitäts-Spillover',
  ARRAY['ASIA-CHINA','ASIA-SOUTHEAST','ASIA-INDIA'],
  ARRAY['CGTN','China Daily','Global Times','People''s Daily','Reuters','Associated Press','AFP','BBC World','Channel NewsAsia','Bangkok Post','Straits Times','Nikkei Asia','Philippine Daily Inquirer','The Nation Thailand','NDTV','Times of India','Hindustan Times','The Hindu','Al Jazeera','The Telegraph','Globe and Mail','Bloomberg','Japan Times','Asahi Shimbun','NHK World','Kyodo News','ABC News','VN Express','Dhaka Tribune','Daily Nation','News24'],
  ARRAY['scam','cyberscam','fraud','traffick','compound','scam hub','scam centre','scam center','scam mafia','forced labo','Myawaddy','KK Park','execute','mafia','syndicate','kingpin','fraud hub','詐欺','拠点詐欺','Betrug','Menschenhandel','estafa','arnaque','fraude'],
  true, 3, true, now(), now()
);

COMMIT;

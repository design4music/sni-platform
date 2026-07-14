-- europe_us_theater theater-level narrative cards (FN_THEATER_BUILD_SPEC §5.5).
-- The theater carries no fn_anchor bundle; these cards' headlines + counts roll
-- up from the member atomics' title_narratives, matched by stance-SIGN +
-- publisher (THEATER_ROLLUP_SQL in apps/frontend/lib/friction-nodes.ts).
-- Three cards, one per bloc, publisher-DISJOINT within each sign bucket so
-- counts partition cleanly:
--   +2  US-nationalist          (US-conservative press)   [only + card]
--   -1  Western/European mainstream (Atlanticist-critical)  } disjoint
--   -2  Russia/China rift-exploitation (state media)        } negatives
-- Idempotent: ON CONFLICT (id) DO NOTHING.
SET client_encoding TO 'UTF8';

INSERT INTO narratives_v2
  (id, name_en, name_de, claim_en, claim_de, actor_centroids, framing_keywords,
   is_active, publishers, fn_id, display_order, stance_label_en, stance_label_de,
   stance, framing_required)
VALUES
(
  'europe_us_america_first',
  'America First: a freeloading, over-regulating Europe must pay, open up and submit',
  'America First: Ein trittbrettfahrendes, überregulierendes Europa muss zahlen, sich öffnen und fügen',
  'America-First framing (US conservative press) runs across the whole theater: Europe has exploited US trade openness, freeloaded on US defence, and harasses American tech champions -- so tariffs, blunt burden-sharing pressure and retaliation over EU tech rules are justified tools to force fair terms and put America first. Europe is a partner to be disciplined, not indulged. Vocabulary: freeload, fair share, unfair, shakedown, America First, pay up, reciprocal.',
  'Die America-First-Rahmung (US-konservative Presse) durchzieht das gesamte Theater: Europa habe die US-Handelsoffenheit ausgenutzt, sich beim US-Schutz als Trittbrettfahrer verhalten und schikaniere amerikanische Techkonzerne -- daher seien Zölle, harter Lastenteilungsdruck und Vergeltung gegen EU-Techregeln berechtigte Mittel, um faire Bedingungen zu erzwingen und Amerika an die erste Stelle zu setzen.',
  ARRAY['AMERICAS-USA'],
  ARRAY['freeload','fair share','unfair','shakedown','America First','pay up','reciprocal','surplus','protectionist','Trittbrettfahrer','America First'],
  true,
  ARRAY['Fox News','New York Post','Washington Examiner','Breitbart','Newsmax','The National Interest','The Federalist','Daily Caller','Washington Times'],
  'europe_us_theater', 1,
  'America First',
  'America First',
  2, false
),
(
  'europe_us_transatlantic_rupture',
  'A vital alliance is rupturing, forcing an alarmed Europe to defend itself and its interests',
  'Ein lebenswichtiges Bündnis zerbricht und zwingt ein alarmiertes Europa, sich und seine Interessen zu verteidigen',
  'Western and European mainstream framing treats the Trump-era pressure -- tariffs, burden-sharing threats, wavering security guarantees, tech confrontation -- as the rupture of a decades-old partnership that leaves Europe exposed and coerced. The response it champions is unity, countermeasures, strategic autonomy and digital sovereignty: an alarmed continent forced to decide and defend for itself. Vocabulary: rupture, coercion, unreliable, autonomy, sovereignty, unity, defend, wake-up call.',
  'Der westliche und europäische Mainstream deutet den Druck der Trump-Ära -- Zölle, Lastenteilungsdrohungen, schwankende Sicherheitsgarantien, Techkonfrontation -- als Bruch einer jahrzehntealten Partnerschaft, der Europa entblößt und unter Zwang setzt. Die befürwortete Antwort ist Einigkeit, Gegenmaßnahmen, strategische Autonomie und digitale Souveränität.',
  ARRAY['NON-STATE-EU','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','AMERICAS-USA'],
  ARRAY['rupture','coercion','unreliable','autonomy','sovereignty','unity','defend','wake-up call','alliance','trade war','Bruch','Zwang','Autonomie','Souveränität'],
  true,
  ARRAY['Reuters','Associated Press','BBC World','Financial Times','Wall Street Journal','New York Times','Washington Post','CNN','ABC News','NPR','The Guardian','Deutsche Welle','Euronews','France 24 (EN)','El País','Le Monde','ANSA','EurActiv','Politico','Der Spiegel','Süddeutsche Zeitung','Frankfurter Allgemeine','Die Zeit','Bloomberg','CNBC','Channel NewsAsia','The Independent','LRT English','ERR News','eKathimerini','Ars Technica','TechCrunch'],
  'europe_us_theater', 2,
  'Transatlantic rupture & European response',
  'Transatlantischer Bruch & europäische Antwort',
  -1, false
),
(
  'europe_us_western_disunity',
  'The transatlantic split exposes Western hypocrisy and the arrival of a multipolar world',
  'Der transatlantische Bruch entlarvt westliche Heuchelei und den Anbruch einer multipolaren Welt',
  'Rift-exploitation framing (Russian and Chinese state media) reads every transatlantic quarrel -- tariffs, burden rows, the "EU army", tech fights -- not as taking sides but as proof that the US treats Europe as milkable vassals, that Western unity and values are hypocrisy, and that American hegemony is giving way to a multipolar order. Adversarial to the West as a bloc, amplified with schadenfreude. Vocabulary: vassal, hypocrisy, multipolar, end of hegemony, disunity, decline of the West, humiliation.',
  'Die Riss-Ausnutzungs-Rahmung (russische und chinesische Staatsmedien) liest jeden transatlantischen Streit -- Zölle, Lastenstreitigkeiten, „EU-Armee", Techkonflikte -- nicht als Parteinahme, sondern als Beweis, dass die USA Europa als auszunehmende Vasallen behandeln, westliche Einigkeit und Werte Heuchelei seien und die amerikanische Hegemonie einer multipolaren Ordnung weiche.',
  ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
  ARRAY['vassal','hypocrisy','multipolar','end of hegemony','disunity','decline of the West','humiliation','submission','servant','Vasall','Heuchelei','multipolar'],
  true,
  ARRAY['RT','TASS','TASS (EN)','tass.com','Sputnik','RIA Novosti','Lenta.ru','Gazeta.ru','Izvestia','Kommersant','BelTA','Press TV','CGTN','Global Times','China Daily','Xinhua'],
  'europe_us_theater', 3,
  'Anti-Western rift-exploitation',
  'Anti-westliche Riss-Ausnutzung',
  -2, false
)
ON CONFLICT (id) DO NOTHING;

-- us_china_theater: round-2 narrative fixes, found by reading ATTRIBUTED
-- sample titles (spec s0a step 9 -- "don't just check the counts look
-- plausible; pull actual sample titles per narrative and read them").
-- Every fix below was invisible in the counts and only showed up in samples.
--
-- FIX 1 -- summit_engagement_works was mislabelling counter-examples as
-- engagement-positive, via stance-ambiguous keywords:
--   'stability'   fired on "Xi, in summit VICTORY, projected stability and
--                 CONCEDED NOTHING to Trump" (Washington Post) -- a weak-hand
--                 title filed as engagement working.
--   'renews'      fired on "China RENEWS, THEN HALTS licenses for hundreds of
--                 US beef exporters" -- the halt is the story.
--   'cooperation' fired on "Trump-Xi summit highlights cooperation, LACKS
--                 BREAKTHROUGHS on key fault lines" (Yonhap).
--   'invites'     fired on "Xi invites PUTIN to Beijing days after Trump visit"
--                 -- wrong dyad entirely (China-Russia).
--   'deeper'      fired on "STARMER and Xi call for deeper UK-CHINA ties" and
--   'stabiliz'    on "Sánchez consolida su relación con Xi Jinping... potencia
--                 estabilizadora" -- UK-China and Spain-China, not US-China.
-- Replaced the bare stems with the specific phrases that carry the positive
-- reading ('progress stabiliz', 'targets stability', 'signals stability',
-- 'constructive stability'), which keep the true positives and exclude all of
-- the above. Added the counter-examples' own markers to the -1 list.
--
-- FIX 2 -- summit_multipolar_framing was labelling 64 neutral wire stories as
-- a "multipolar decline" argument. The Russian bloc has 73 summit titles but
-- only 9 are stance-bearing: TASS and RT run plain agency copy on this story
-- ("Xi-Trump talks begin in Beijing - TV", "Trump and his delegation arrive in
-- Beijing - TV", "China confirms Trump state visit"). The premise that state
-- media is stance-saturated holds for the Chinese outlets (which editorialise
-- in the headline) but NOT for the Russian wire agencies here -- unlike Arctic,
-- where Moscow had a direct stake and a line to push, Russia is a bystander to
-- the US-China trade dyad. So framing_required=true, and the narrative is
-- renamed to describe what the 9 stance-bearing titles actually say: Xi rebuffs
-- and needles Trump, Trump plays the suitor, Washington cannot dictate terms.

BEGIN;

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'successful','guardrail','consensus','landmark','momentum','reset','thaw','pragmatic',
  'win-win','mutual respect','mutual understanding','mutual benefit','fruitful','lower tariffs',
  'tariff cuts','cut tariffs','agreed to','very positive','conciliation','admires','friendly',
  'harmon','all business','import permit','buys more','great leader','bright prospects',
  'progress stabiliz','constructive stability','targets stability','signals stability',
  'stability in us ties','stability to the world',
  'erfolgreich','Leitplanken','Konsens','Zollsenkung','Harmonie','freundliche'
], updated_at = now()
WHERE id = 'us_china_summit_engagement_works';

UPDATE narratives_v2 SET framing_keywords = ARRAY[
  'stalemate','few wins','empty-handed','no deals','no commitment','no sign','without a deal',
  'little to show','preliminary','exposes','upper hand','capitulat','concession','conceded nothing',
  'gave away','flat-out disaster','embarrassment','failed to','whipsaw','stumble','limits on',
  'no major','tightrope','treads carefully','fights with allies','quiet as','gives Beijing',
  'Beijing a win','lacks breakthrough','then halts','summit victory','differing priorit',
  'play the suitor','conceded',
  'Patt','kaum Erfolge','keine Abschlüsse','vorläufig','Oberhand','Zugeständnis','bedürftiger'
], updated_at = now()
WHERE id = 'us_china_summit_weak_hand';

UPDATE narratives_v2 SET
  name_en = 'Washington cannot dictate terms to Beijing',
  name_de = 'Washington kann Peking keine Bedingungen diktieren',
  stance_label_en = 'Russian state framing: US cannot dictate',
  stance_label_de = 'Russische Staatsmedien: USA können nicht diktieren',
  claim_en = 'The stance-bearing strand of Russian state coverage of US-China leader diplomacy: attention to moments where Xi rebuffs, needles or raises his voice at the US president, to Trump cast as the supplicant, to the Thucydides trap, and to Moscow-Beijing alignment reaffirmed immediately after the summit. It is third-party framing — neither an endorsement of the US position nor of China''s cooperation message — and sits on its own axis rather than the summit''s success/failure axis. Note that most Russian agency copy on this story is plain reportage carrying no stance, and is deliberately excluded by the framing gate. Vocabulary: suitor, multipolar, decline, Thucydides trap, lost his temper, needled.',
  claim_de = 'Der wertende Strang russischer Staatsberichterstattung über die Gipfeldiplomatie zwischen den USA und China: Aufmerksamkeit für Momente, in denen Xi den US-Präsidenten abweist, sticheln oder die Stimme erheben lässt, für Trump in der Rolle des Bittstellers, für die Thukydides-Falle und für das unmittelbar nach dem Gipfel bekräftigte Bündnis Moskau-Peking. Es ist eine Drittperspektive — weder Zustimmung zur US-Position noch zur chinesischen Kooperationsbotschaft — und liegt auf einer eigenen Achse. Der Großteil der russischen Agenturmeldungen zu diesem Thema ist wertungsfreie Nachricht und wird vom Framing-Filter bewusst ausgeschlossen. Vokabular: Bittsteller, multipolar, Niedergang, Thukydides-Falle, Wutausbruch.',
  framing_keywords = ARRAY[
    'multipolar','decline','declining','beneficiar','suitor','hegemon','agitated','denounce',
    'unyielding','no longer','concede',
    'многополяр','упадок','гегемон','вышел из себя','сорвался','уколол','повысил голос',
    'ловушк','не смог','провал','уступ','пожалеть'
  ],
  framing_required = true,
  updated_at = now()
WHERE id = 'us_china_summit_multipolar_framing';

COMMIT;

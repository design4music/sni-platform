-- Great Lakes: narrative framing corrections (2026-07-20).
--
-- Found by pulling actual sample titles per narrative and reading them, NOT by
-- looking at the counts -- every count below was plausible before inspection.
-- Six defects, five of them the same root cause: a TOPIC word was used as a
-- FRAMING keyword. A framing keyword must imply the OUTCOME, not the actor or
-- the subject matter (the Sahel `frappes` lesson).
--
-- ---------------------------------------------------------------------------
-- 1. drc_accords_are_working (+2) was 4/7 WRONG. `accord`/`agreement` are the
--    atomic's topic, not a stance, so the card was claiming mediation success
--    using headlines that say the opposite:
--      "les accords de paix RDC - Rwanda STAGNENT"
--      "l'accord de paix N'AVANCE PAS a cause des agissements de Paul Kagame"
--    plus two US migrant-DEPORTATION accords that have nothing to do with the
--    peace process. Both stalling titles were simultaneously filed under
--    drc_accords_stalling -- the same headline carried +2 and -1 at once.
--    FIX: drop `accord`/`agreement`; keep only outcome words (signed, released,
--    facilitate, de-escalate, progress, mechanism, monitoring).
--
-- 2. m23_externally_backed_offensive (-2) had swallowed the whole
--    aid-worker-killed cluster via `drone strike`/`frappe de drone`:
--      "Drone strike kills UN aid worker in the eastern Congo city of Goma"
--      "Une humanitaire francaise tuee par une frappe de drone a Goma"
--    Those are Congolese ARMY strikes killing civilians -- a civilian-harm
--    story, already correctly held by m23_civilian_toll. A neutral escalation
--    noun steals titles (the Panama lesson). `held` was also firing on
--    "M23-held area" inside an Ebola headline.
--    FIX: drop `drone strike`, `drone attack`, `frappe de drone`,
--    `Drohnenangriff`, `held`.
--
-- 3. "Rwanda hits back at US sanctions over M23 support" was double-filed at
--    -2 (offensive) AND +1 (rejection) because The Standard sat in both
--    coalitions and the title matched both keyword sets. Contradictory, not
--    complementary. FIX: The Standard leaves the offensive coalition -- it
--    contributed exactly this one title there, so the cost is nil.
--
-- 4. m23_backing_charge_rejected (+1) had picked up "MONUSCO repatriates former
--    FDLR fighters from DR Congo" (CGTN) via the keyword `FDLR`. That is a
--    neutral logistics wire story, not a rejection of the backing charge.
--    `FDLR`/`genocidaires`/`Banyamulenge`/`Tutsi` are topic words. FIX: drop
--    them, keep only denial verbs; widen the coalition to the outlets that
--    actually print the accused parties' response.
--
-- 5. drc_mediation_as_interference (-2) held 3 titles, ALL neutral CGTN wire
--    copy ("New MONUSCO chief arrives in Kinshasa to advance peace", "UN to
--    deploy ceasefire monitoring mission"). framing_required=false meant
--    publisher alone decided, and CGTN's DRC coverage in this window carries no
--    rift-exploitation framing at all -- it is straight reporting. Labelling it
--    "Peacemaking with a price tag" would be exactly the false, corrosive card
--    the spec warns against. FIX: framing_required=true. The card may fall to
--    zero titles; an empty honest card beats three mislabelled ones, and it
--    will fire when that framing actually appears.
--
-- 6. drc_minerals_as_development (+2) was pulling critiques via `pact` and
--    `output`: "US struggling to de-risk Congo's 'war zone minerals' even after
--    pact" and "Ivanhoe says revised report CUTS 2026 copper output forecast".
--    FIX: drop `pact`, `output`, `production`. The de-risk title routes to
--    drc_minerals_human_cost, which already holds `de-risk`.
--
-- Also: drc_minerals_as_resource_capture's coalition was rebuilt. Chinese and
-- Russian state media publish ZERO DRC-minerals titles in this window (verified
-- directly), so the stance is carried here by AFRICAN voices instead -- Daily
-- Nation on the deal being "deeply flawed and unconstitutional", Daily Maverick
-- on South Africa's minister clashing with his Congolese counterpart over it.
-- Daily Maverick moves out of the human-cost coalition to keep the two
-- disjoint. The Chinese/Russian outlets stay listed: they cannot produce false
-- positives while they publish nothing, and they are the expected carriers if
-- the incumbent-displacement story is ever covered from that side.

BEGIN;

UPDATE narratives_v2 SET
    framing_keywords = ARRAY['signed', 'commit', 'commitment', 'progress', 'monitoring', 'release', 'released', 'prisoners', 'facilitate', 'de-escalate', 'breakthrough', 'mechanism', 'signé', 'engagement', 'progrès', 'libérer', 'libération', 'faciliter', 'désescalade', 'unterzeichnet', 'Fortschritt', 'Freilassung', 'Deeskalation'],
    updated_at = NOW()
WHERE id = 'drc_accords_are_working';

UPDATE narratives_v2 SET
    framing_keywords = ARRAY['backing', 'backed', 'support for', 'supporting', 'proxy', 'sanctions', 'visa restrictions', 'Rwandan army', 'Rwandan officials', 'offensive', 'seized', 'captured', 'retake', 'retook', 'occupied', 'incursion', 'soutien', 'soutenu', 'appuyé', 'offensive', 'conquise', 'contrôlé', 'Unterstützung', 'unterstützt', 'Sanktionen', 'Offensive'],
    publishers = ARRAY['France 24', 'France 24 (EN)', 'Le Monde', 'Le Figaro', 'Reuters', 'Associated Press', 'The Guardian', 'BBC World', 'BBC', 'Deutsche Welle', 'Washington Post', 'Financial Times', 'The Economist', 'Swissinfo', 'ANSA', 'news.un.org', 'UN News', 'Al Jazeera', 'Anadolu Agency', 'Daily Sabah', 'TRT World', 'Daily Nation', 'Punch Newspapers', 'Janes'],
    updated_at = NOW()
WHERE id = 'm23_externally_backed_offensive';

UPDATE narratives_v2 SET
    framing_keywords = ARRAY['denies', 'denied', 'denounces', 'denounced', 'rejects', 'rejected', 'unjustified', 'unfounded', 'hits back', 'insults', 'internal affairs', 'dément', 'rejette', 'dénonce', 'injustifié', 'weist zurück', 'bestreitet', 'ungerechtfertigt'],
    publishers = ARRAY['The Standard', 'Daily Nation', 'Mail & Guardian', 'Anadolu Agency', 'Al-Ahram', 'News24', 'Punch Newspapers', 'RT', 'TASS (EN)'],
    updated_at = NOW()
WHERE id = 'm23_backing_charge_rejected';

UPDATE narratives_v2 SET
    framing_required = true,
    updated_at = NOW()
WHERE id = 'drc_mediation_as_interference';

UPDATE narratives_v2 SET
    framing_keywords = ARRAY['deal', 'agreement', 'investment', 'invest', 'stake', 'boom', 'growth', 'exploration', 'approve', 'approved', 'takeover', 'acquisition', 'corridor', 'stock market', 'exports', 'reopen', 'investissement', 'croissance', 'exportations', 'Investition', 'Wachstum', 'Übernahme', 'Ausfuhren'],
    updated_at = NOW()
WHERE id = 'drc_minerals_as_development';

UPDATE narratives_v2 SET
    publishers = ARRAY['The Guardian', 'Wall Street Journal', 'Le Monde', 'France 24', 'France 24 (EN)', 'Deutsche Welle', 'Associated Press', 'BBC World', 'BBC', 'Al Jazeera', 'Folha de S.Paulo', 'Council on Foreign Relations', 'Globe and Mail', 'La Repubblica', 'Press TV', 'DR'],
    updated_at = NOW()
WHERE id = 'drc_minerals_human_cost';

UPDATE narratives_v2 SET
    publishers = ARRAY['Daily Nation', 'Daily Maverick', 'CGTN', 'Global Times', 'China Daily', 'Xinhua', 'RT', 'TASS', 'TASS (EN)', 'Sputnik', 'RIA Novosti'],
    updated_at = NOW()
WHERE id = 'drc_minerals_as_resource_capture';

COMMIT;

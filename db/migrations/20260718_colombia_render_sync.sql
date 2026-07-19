-- ============================================================================
-- COLOMBIA THEATER -- RENDER SYNC MIGRATION
-- Generated 2026-07-18 from verified LOCAL state (state-diff, not replay).
-- ============================================================================
--
-- RUN THIS ON RENDER MANUALLY. safe_db_migrate.py is local-only by design
-- (--target render is hard-blocked), so apply via the docker postgres:18 psql
-- pattern in docs/context/RENDER_DEPLOY_FN_MAP.md, AFTER a full pg_dump -Fc
-- backup of Render.
--
-- PRE-FLIGHT (verified read-only against Render 2026-07-18):
--   * No friction_nodes row matches 'colombia%'      -> pure INSERT, no collision
--   * No narratives_v2 row matches fn_id 'colombia%' -> pure INSERT
--   * No taxonomy_v3 fn_anchor matches 'colombia%'   -> pure INSERT
--   * Render friction_nodes total was 180; expect 184 after this.
--
-- SAFETY: contains NO DELETE, TRUNCATE, DROP or ALTER. Every statement is an
-- idempotent upsert, so re-running is safe and converges on local state.
--
-- REHEARSED: applied against LOCAL on 2026-07-18, where all 4 FN rows, 3
-- bundles and 11 narratives already existed. Result: applied clean, the
-- verification block returned 4 | 3 | 11 | 7, and local attribution was
-- untouched (222 event_friction_nodes and 71 title_narratives before and
-- after) -- confirming the upserts are true no-ops on an already-correct DB
-- and that this file moves structural content only.
--
-- SCOPE -- structural content only, per the sync model in the deploy runbook:
--   1. friction_nodes            4 rows  (1 theater + 3 atomics)
--   2. taxonomy_v3 fn_anchor     3 rows  (the vocabulary bundles)
--   3. narratives_v2            11 rows  (7 atomic + 4 theater cards)
--
-- DELIBERATELY EXCLUDED -- attribution (event_friction_nodes, title_narratives).
-- Those are derived data, rebuilt by scripts/bootstrap_friction_node.py, and
-- are being deferred until all remaining FN theaters are built and pushed as
-- one batch. Until that bootstrap runs, these FNs will render on Render with
-- zero attributed events. That is expected, not a failure.
--
-- WHY THE BUNDLES ARE IN THIS FILE (they were not, historically):
-- fn_anchor rows are normally written by scripts/apply_fn_anchor_bundle.py,
-- which targets whatever DB the environment points at -- in practice local.
-- They therefore never travelled with the per-theater migrations, and a
-- read-only audit of Render on 2026-07-18 found 46 of 121 active atomics with
-- NO bundle at all (Render fn_anchor = 81 rows), including all three LatAm
-- atomics pushed earlier. An atomic without a bundle matches nothing, so a
-- future bootstrap would silently produce zero events for it. Embedding the
-- bundles here makes Colombia arrive complete. The pre-existing 46 remain a
-- separate backfill task.
--
-- ROLLBACK: the pre-flight established these ids do not exist on Render, so
-- rollback is a targeted removal of exactly the ids inserted here. The
-- runnable statements live in the companion file
--     db/migrations/20260718_colombia_render_sync.ROLLBACK.sql
-- and are deliberately NOT written out here: safe_db_migrate.py scans for
-- destructive patterns by regex WITHOUT skipping comments, so spelling them
-- in this header made the scanner report a false 102,321-row cascade blast
-- radius against the whole friction_nodes tree and refuse to apply the
-- forward migration. Keeping them separate lets the scanner flag the
-- rollback file (correctly destructive) and pass this one (purely additive).
--
-- ============================================================================

BEGIN;

-- ============ 1. friction_nodes (4 rows) ============
INSERT INTO friction_nodes (id, name_en, name_de, description_en, description_de, editorial_summary_en, editorial_summary_de, fn_type, scope, centroid_ids, primary_target, is_active, anchor_point, member_fn_ids, affected_asset_ids, display_order) VALUES (
    'colombia_theater',
    'Colombia',
    'Kolumbien',
    'Colombia''s external alignment, its contested presidential transition, and the negotiations with armed groups and drug cartels.',
    'Kolumbiens außenpolitische Ausrichtung, der umstrittene Präsidentschaftswechsel und die Verhandlungen mit bewaffneten Gruppen und Drogenkartellen.',
    'Relations with Washington moved from a threatened military operation and a formal Colombian complaint to a White House meeting within weeks, and the resulting understanding disrupted the government''s negotiations with armed groups. A presidential election then produced a winner endorsed by the US president, while the outgoing president alleged foreign interference in the vote. Colombia has no centroid of its own and is covered under AMERICAS-ANDEAN.',
    'Die Beziehungen zu Washington entwickelten sich binnen Wochen von einer angedrohten Militäroperation und einer förmlichen kolumbianischen Beschwerde hin zu einem Treffen im Weißen Haus; die daraus folgende Verständigung störte die Verhandlungen der Regierung mit bewaffneten Gruppen. Eine Präsidentschaftswahl brachte anschließend einen vom US-Präsidenten unterstützten Sieger hervor, während der scheidende Präsident ausländische Einflussnahme auf die Wahl behauptete. Kolumbien hat keinen eigenen Zentroid und wird unter AMERICAS-ANDEAN geführt.',
    'theater',
    'regional',
    ARRAY['AMERICAS-ANDEAN'],
    NULL,
    true,
    '{"type": "Point", "coordinates": [-74.1, 4.7]}'::jsonb,
    ARRAY['colombia_us_alignment', 'colombia_political_transition', 'colombia_armed_groups_peace'],
    ARRAY[]::text[],
    NULL
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    description_en = EXCLUDED.description_en,
    description_de = EXCLUDED.description_de,
    editorial_summary_en = EXCLUDED.editorial_summary_en,
    editorial_summary_de = EXCLUDED.editorial_summary_de,
    fn_type = EXCLUDED.fn_type,
    scope = EXCLUDED.scope,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = EXCLUDED.is_active,
    anchor_point = EXCLUDED.anchor_point,
    member_fn_ids = EXCLUDED.member_fn_ids,
    affected_asset_ids = EXCLUDED.affected_asset_ids,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO friction_nodes (id, name_en, name_de, description_en, description_de, editorial_summary_en, editorial_summary_de, fn_type, scope, centroid_ids, primary_target, is_active, anchor_point, member_fn_ids, affected_asset_ids, display_order) VALUES (
    'colombia_armed_groups_peace',
    'Armed groups and the peace process',
    'Bewaffnete Gruppen und der Friedensprozess',
    'Negotiations with guerrilla groups and drug cartels under the "total peace" policy, and the armed and narcotics economy they operate in.',
    'Verhandlungen mit Guerillagruppen und Drogenkartellen im Rahmen der Politik des "totalen Friedens" sowie die bewaffnete Ökonomie und Drogenwirtschaft, in der sie agieren.',
    'The "total peace" policy opened parallel negotiations with the ELN, FARC dissident factions and the Gulf Clan. A tribunal charged former FARC members with war crimes, and the largest cartel suspended talks after the understanding reached between the Colombian and US presidents. Coca cultivation and gold trafficking fund several of the groups involved.',
    'Die Politik des "totalen Friedens" eröffnete parallele Verhandlungen mit der ELN, FARC-Dissidentengruppen und dem Clan del Golfo. Ein Tribunal klagte frühere FARC-Mitglieder wegen Kriegsverbrechen an, und das größte Kartell setzte die Gespräche aus, nachdem sich der kolumbianische und der US-Präsident verständigt hatten. Kokaanbau und Goldschmuggel finanzieren mehrere der beteiligten Gruppen.',
    'atomic',
    'regional',
    ARRAY['AMERICAS-ANDEAN'],
    NULL,
    true,
    NULL,
    NULL,
    ARRAY[]::text[],
    NULL
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    description_en = EXCLUDED.description_en,
    description_de = EXCLUDED.description_de,
    editorial_summary_en = EXCLUDED.editorial_summary_en,
    editorial_summary_de = EXCLUDED.editorial_summary_de,
    fn_type = EXCLUDED.fn_type,
    scope = EXCLUDED.scope,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = EXCLUDED.is_active,
    anchor_point = EXCLUDED.anchor_point,
    member_fn_ids = EXCLUDED.member_fn_ids,
    affected_asset_ids = EXCLUDED.affected_asset_ids,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO friction_nodes (id, name_en, name_de, description_en, description_de, editorial_summary_en, editorial_summary_de, fn_type, scope, centroid_ids, primary_target, is_active, anchor_point, member_fn_ids, affected_asset_ids, display_order) VALUES (
    'colombia_political_transition',
    'Presidential transition and institutional contest',
    'Präsidentschaftswechsel und institutioneller Streit',
    'The Colombian presidential succession, the contested result and the institutional disputes around it.',
    'Die kolumbianische Präsidentschaftsnachfolge, das umstrittene Ergebnis und die damit verbundenen institutionellen Auseinandersetzungen.',
    'The presidential race concluded in a narrow runoff win for Abelardo de la Espriella over Iván Cepeda. The US president publicly endorsed the winner before the vote, and the outgoing president alleged foreign interference in the result. The losing camp pursued a legal challenge. Coverage divides between readings of the outcome as a security mandate and as a risk to institutional norms.',
    'Das Präsidentschaftsrennen endete mit einem knappen Stichwahlsieg von Abelardo de la Espriella über Iván Cepeda. Der US-Präsident hatte den Sieger vor der Wahl öffentlich unterstützt, und der scheidende Präsident behauptete ausländische Einflussnahme auf das Ergebnis. Das unterlegene Lager ging juristisch dagegen vor. Die Berichterstattung teilt sich in Deutungen des Ausgangs als Sicherheitsmandat und als Risiko für institutionelle Normen.',
    'atomic',
    'regional',
    ARRAY['AMERICAS-ANDEAN'],
    NULL,
    true,
    NULL,
    NULL,
    ARRAY[]::text[],
    NULL
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    description_en = EXCLUDED.description_en,
    description_de = EXCLUDED.description_de,
    editorial_summary_en = EXCLUDED.editorial_summary_en,
    editorial_summary_de = EXCLUDED.editorial_summary_de,
    fn_type = EXCLUDED.fn_type,
    scope = EXCLUDED.scope,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = EXCLUDED.is_active,
    anchor_point = EXCLUDED.anchor_point,
    member_fn_ids = EXCLUDED.member_fn_ids,
    affected_asset_ids = EXCLUDED.affected_asset_ids,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO friction_nodes (id, name_en, name_de, description_en, description_de, editorial_summary_en, editorial_summary_de, fn_type, scope, centroid_ids, primary_target, is_active, anchor_point, member_fn_ids, affected_asset_ids, display_order) VALUES (
    'colombia_us_alignment',
    'Alignment with Washington',
    'Ausrichtung gegenüber Washington',
    'Colombia''s relations with the United States, spanning coercive measures, tariffs, sanctions designations and negotiated rapprochement.',
    'Kolumbiens Beziehungen zu den Vereinigten Staaten, von Zwangsmaßnahmen, Zöllen und Sanktionslistungen bis zur ausgehandelten Annäherung.',
    'In January the US president threatened a military operation against Colombia following a raid in Venezuela; Bogotá lodged a formal complaint. Within weeks the two presidents met at the White House. The episode combined tariff threats, visa measures and sanctions designations with a rapid diplomatic reversal, and the resulting understanding carried directly into Colombia''s talks with armed groups.',
    'Im Januar drohte der US-Präsident nach einem Einsatz in Venezuela mit einer Militäroperation gegen Kolumbien; Bogotá legte förmlich Beschwerde ein. Wenige Wochen später trafen sich beide Präsidenten im Weißen Haus. Die Episode verband Zolldrohungen, Visamaßnahmen und Sanktionslistungen mit einer raschen diplomatischen Kehrtwende; die daraus folgende Verständigung wirkte unmittelbar auf Kolumbiens Gespräche mit bewaffneten Gruppen.',
    'atomic',
    'regional',
    ARRAY['AMERICAS-ANDEAN'],
    NULL,
    true,
    NULL,
    NULL,
    ARRAY[]::text[],
    NULL
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    description_en = EXCLUDED.description_en,
    description_de = EXCLUDED.description_de,
    editorial_summary_en = EXCLUDED.editorial_summary_en,
    editorial_summary_de = EXCLUDED.editorial_summary_de,
    fn_type = EXCLUDED.fn_type,
    scope = EXCLUDED.scope,
    centroid_ids = EXCLUDED.centroid_ids,
    primary_target = EXCLUDED.primary_target,
    is_active = EXCLUDED.is_active,
    anchor_point = EXCLUDED.anchor_point,
    member_fn_ids = EXCLUDED.member_fn_ids,
    affected_asset_ids = EXCLUDED.affected_asset_ids,
    display_order = EXCLUDED.display_order,
    updated_at = now();

-- ============ 2. taxonomy_v3 fn_anchor bundles (3 rows) ============
-- Unique partial index idx_taxonomy_v3_unique_fn_anchor is on (linked_id)
-- WHERE taxonomy_function='fn_anchor' AND is_active -- so the conflict target is
-- that predicate, not the uuid PK.
INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'colombia_armed_groups_peace', 'colombia_armed_groups_peace fn_anchor', '{"ar": ["حرب العصابات", "كارتل", "الكوكايين", "عملية السلام"], "de": ["Guerilla", "Kartell", "Kokain", "Friedensprozess", "Friedensgespräche"], "en": ["ELN", "FARC", "Gulf Clan", "Segunda Marquetalia", "guerrilla", "paramilitar", "cartel", "cocaine", "coca leaf", "total peace", "peace talks", "peace process", "peace negotiations", "Catatumbo", "Arauca", "Cauca"], "es": ["Clan del Golfo", "disidencias", "cártel", "narcotráfico", "cocaína", "cocalero", "hoja de coca", "paz total", "proceso de paz", "acuerdo de paz", "negociaciones de paz"], "fr": ["cocaïne", "processus de paix"], "hi": ["छापामार", "कार्टेल", "कोकीन", "शांति प्रक्रिया"], "it": ["cocaina", "processo di pace"], "ja": ["ゲリラ", "カルテル", "コカイン", "和平プロセス"], "ru": ["партизан", "картел", "кокаин", "мирный процесс"], "zh": ["游击", "贩毒集团", "可卡因", "和平进程"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'colombia_political_transition', 'colombia_political_transition fn_anchor', '{"ar": ["جولة الإعادة", "تنصيب", "تزوير الانتخابات"], "de": ["Stichwahl", "Amtseinführung", "Wahlbetrug"], "en": ["Espriella", "Cepeda", "Uribe", "Fajardo", "runoff", "inauguration", "vote count", "electoral fraud", "legal challenge"], "es": ["segunda vuelta", "balotaje", "posesión presidencial", "presidente electo", "conteo de votos", "fraude electoral", "impugnación"], "fr": ["second tour", "investiture", "fraude électorale"], "hi": ["दूसरे दौर", "शपथ ग्रहण", "चुनावी धोखाधड़ी"], "it": ["ballottaggio", "insediamento", "brogli elettorali"], "ja": ["決選投票", "大統領就任", "選挙不正"], "ru": ["второй тур", "инаугурац", "фальсификац"], "zh": ["第二轮", "就职", "选举舞弊"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

INSERT INTO taxonomy_v3 (id, linked_id, item_raw, aliases, centroid_id, is_active, is_stop_word, taxonomy_function)
VALUES (gen_random_uuid(), 'colombia_us_alignment', 'colombia_us_alignment fn_anchor', '{"ar": ["البيت الأبيض", "تهديد", "تعريفة جمركية", "عملية عسكرية", "عقوبات", "تسليم المطلوبين"], "de": ["Weißes Haus", "Drohung", "droht", "Zoll", "Militäroperation", "Sanktion", "Auslieferung"], "en": ["White House", "threat", "tariff", "military operation", "military action", "sanction", "visa", "OFAC", "Clinton list", "extradit", "decertif", "Plan Colombia"], "es": ["Casa Blanca", "amenaza", "arancel", "operación militar", "sanción", "sanciones", "lista Clinton", "extradic", "descertificación", "certificación antidrogas"], "fr": ["Maison Blanche", "droits de douane", "opération militaire"], "hi": ["व्हाइट हाउस", "धमकी", "टैरिफ", "सैन्य अभियान", "प्रतिबंध", "प्रत्यर्पण"], "it": ["Casa Bianca", "minaccia", "dazio", "operazione militare", "sanzione"], "ja": ["ホワイトハウス", "脅迫", "関税", "制裁", "身柄引き渡し"], "ru": ["Белый дом", "угроз", "пошлин", "военная операция", "санкц", "экстрадиц"], "zh": ["白宫", "威胁", "关税", "军事行动", "制裁", "引渡"]}'::jsonb, NULL, true, false, 'fn_anchor')
ON CONFLICT (linked_id) WHERE taxonomy_function = 'fn_anchor' AND is_active = true
DO UPDATE SET aliases = EXCLUDED.aliases, item_raw = EXCLUDED.item_raw, updated_at = now();

-- ============ 3. narratives_v2 (11 rows) ============
INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_peace_negotiation_defense',
    'colombia_armed_groups_peace',
    1,
    'Negotiation is the workable route',
    'Verhandlung ist der gangbare Weg',
    'Talks are how the war ends',
    'Gespräche beenden den Krieg',
    'The supportive reading holds that negotiated demobilisation, transitional justice and rural investment are the only instruments that have historically reduced Colombia''s armed conflict, and that suspending talks under external pressure forfeits the mechanism without offering a replacement.',
    'Die unterstützende Lesart hält fest, dass ausgehandelte Demobilisierung, Übergangsjustiz und Investitionen im ländlichen Raum die einzigen Instrumente sind, die Kolumbiens bewaffneten Konflikt historisch verringert haben, und dass die Aussetzung der Gespräche unter äußerem Druck diesen Mechanismus preisgibt, ohne Ersatz zu bieten.',
    ARRAY['El País', 'Deutsche Welle', 'Al Jazeera', 'Anadolu Agency', 'UN News', 'The Guardian', 'France 24', 'France 24 (EN)', 'BBC World'],
    ARRAY['paz total', 'proceso de paz', 'negociac', 'peace talks', 'peace process', 'desmoviliz', 'transitional justice', 'justicia transicional', 'diálogo', 'acuerdo', 'resume', 'reanuda', 'ceasefire', 'cese'],
    true,
    ARRAY['AMERICAS-ANDEAN'],
    true,
    1
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_peace_process_failure',
    'colombia_armed_groups_peace',
    -1,
    'Negotiation emboldened the groups',
    'Verhandlungen bestärkten die Gruppen',
    'Talks bought the cartels time',
    'Gespräche verschafften den Kartellen Zeit',
    'The critical reading holds that open-ended negotiations let guerrilla factions and cartels consolidate territory, recruit and expand coca and gold revenues while nominally at the table, and that violence rose over the period the policy was in force.',
    'Die kritische Lesart hält fest, dass ergebnisoffene Verhandlungen es Guerillafraktionen und Kartellen erlaubten, Gebiete zu festigen, zu rekrutieren sowie Koka- und Goldeinnahmen auszuweiten, während sie nominell am Tisch saßen, und dass die Gewalt im Geltungszeitraum der Politik zunahm.',
    ARRAY['El Mundo', 'Reforma', 'El Universal', 'Clarín', 'La Nación', 'Infobae'],
    ARRAY['violencia', 'fracaso', 'enseñorea', 'dispara', 'control territorial', 'reclutamiento', 'impunidad', 'failed', 'emboldened', 'expansión', 'suspend', 'war crimes', 'crímenes de guerra', 'extorsión'],
    true,
    ARRAY['AMERICAS-ANDEAN'],
    true,
    2
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_transition_mandate',
    'colombia_political_transition',
    2,
    'A mandate for security',
    'Ein Mandat für Sicherheit',
    'Voters chose a harder line',
    'Die Wähler wählten eine härtere Linie',
    'The sympathetic reading treats the result as a decisive verdict on the outgoing government''s security record: an electorate exhausted by cartel violence and stalled negotiations voted for confrontation with armed groups and closer working relations with Washington.',
    'Die wohlwollende Lesart wertet das Ergebnis als deutliches Urteil über die Sicherheitsbilanz der scheidenden Regierung: Eine von Kartellgewalt und stockenden Verhandlungen erschöpfte Wählerschaft stimmte für die Konfrontation mit bewaffneten Gruppen und engere Arbeitsbeziehungen zu Washington.',
    ARRAY['El Mundo', 'Reforma', 'El Universal', 'Clarín', 'La Nación', 'Infobae', 'Associated Press', 'Reuters', 'Bloomberg', 'Japan Times', 'Atlantic Council'],
    ARRAY['mandato', 'mano dura', 'seguridad', 'crackdown', 'mega-prison', 'megacárcel', 'crime', 'rightward', 'giro a la derecha', 'ciclo de Petro', 'tough on', 'respaldo', 'cartel', 'orden', 'autoridad'],
    true,
    ARRAY['AMERICAS-ANDEAN'],
    true,
    1
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_transition_institutional_concern',
    'colombia_political_transition',
    -1,
    'Concern for institutional norms',
    'Sorge um institutionelle Normen',
    'The result strains the guardrails',
    'Das Ergebnis belastet die Schutzmechanismen',
    'The critical reading raises the endorsement of a candidate by a foreign head of state before the vote, the outgoing president''s allegation of foreign interference, and the losing camp''s legal challenge as pressures on Colombian institutional norms, independent of the winner''s programme.',
    'Die kritische Lesart benennt die Unterstützung eines Kandidaten durch ein ausländisches Staatsoberhaupt vor der Wahl, den Vorwurf ausländischer Einflussnahme durch den scheidenden Präsidenten und die Klage des unterlegenen Lagers als Belastungen kolumbianischer institutioneller Normen -- unabhängig vom Programm des Siegers.',
    ARRAY['El País', 'The Guardian', 'Deutsche Welle', 'France 24', 'France 24 (EN)', 'Le Monde', 'BBC World', 'New York Times', 'CNN', 'Euronews', 'La Repubblica', 'Al Jazeera', 'Anadolu Agency'],
    ARRAY['institucional', 'institutional', 'democracia', 'democracy', 'injerencia', 'interference', 'fraude', 'impugna', 'legal challenge', 'norms', 'autoritari', 'riesgo', 'concern', 'fears', 'ultraderech', 'far-right', 'extrema derecha', 'estrema destra', 'no reconoce', 'non riconosce', 'threat to', 'amenaza para', 'backsliding'],
    true,
    ARRAY['AMERICAS-ANDEAN'],
    true,
    2
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_theater_hard_turn',
    'colombia_theater',
    2,
    'A country turning hard',
    'Ein Land im harten Kurswechsel',
    'The electorate chose confrontation',
    'Die Wählerschaft wählte Konfrontation',
    'One reading runs through every arena at once: voters rejected negotiation with armed groups, elected a government promising confrontation and closer alignment with Washington, and treated the outgoing security policy as the thing that failed.',
    'Eine Lesart durchzieht alle Bereiche zugleich: Die Wähler lehnten Verhandlungen mit bewaffneten Gruppen ab, wählten eine Regierung, die Konfrontation und engere Anlehnung an Washington verspricht, und werteten die scheidende Sicherheitspolitik als das Gescheiterte.',
    ARRAY['El Mundo', 'Reforma', 'El Universal', 'Clarín', 'La Nación', 'Infobae'],
    ARRAY['mandato', 'seguridad', 'mano dura', 'cartel', 'violencia', 'victoria', 'contundente'],
    false,
    ARRAY['AMERICAS-ANDEAN'],
    true,
    1
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_theater_negotiated_path',
    'colombia_theater',
    1,
    'The negotiated path holds',
    'Der Verhandlungsweg trägt',
    'Bargaining still works, at home and abroad',
    'Verhandeln funktioniert weiter, innen wie außen',
    'A second reading emphasises that both the confrontation with Washington and the conflict with armed groups were managed through bargaining rather than force: the military threat ended in a White House meeting, and negotiation remains the only instrument that has historically shrunk the armed conflict.',
    'Eine zweite Lesart betont, dass sowohl die Konfrontation mit Washington als auch der Konflikt mit bewaffneten Gruppen durch Verhandlung statt Gewalt bearbeitet wurden: Die Militärdrohung endete in einem Treffen im Weißen Haus, und Verhandlung bleibt das einzige Instrument, das den bewaffneten Konflikt historisch verkleinert hat.',
    ARRAY['Reuters', 'Associated Press', 'BBC World', 'Deutsche Welle', 'CNN', 'The Guardian', 'New York Times', 'France 24', 'France 24 (EN)', 'Le Monde', 'NPR', 'Euronews', 'Bloomberg', 'Financial Times', 'El País', 'Al Jazeera', 'Anadolu Agency', 'UN News'],
    ARRAY['détente', 'acuerdo', 'negociac', 'peace process', 'paz total', 'diálogo', 'meeting'],
    false,
    ARRAY['AMERICAS-ANDEAN'],
    true,
    2
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_theater_external_pressure',
    'colombia_theater',
    -1,
    'Sovereignty under external pressure',
    'Souveränität unter äußerem Druck',
    'Decisions shaped from outside',
    'Von außen geformte Entscheidungen',
    'Mainstream coverage across the arenas describes a state whose room for manoeuvre narrowed from outside: a threatened military operation, tariff and sanctions pressure, a foreign endorsement in a national election, and an understanding with Washington that reshaped domestic negotiations with armed groups.',
    'Etablierte Berichterstattung beschreibt über alle Bereiche hinweg einen Staat, dessen Handlungsspielraum von außen verengt wurde: eine angedrohte Militäroperation, Zoll- und Sanktionsdruck, eine ausländische Wahlempfehlung im nationalen Wahlkampf und eine Verständigung mit Washington, die die inneren Verhandlungen mit bewaffneten Gruppen umformte.',
    ARRAY['Reuters', 'Associated Press', 'BBC World', 'Deutsche Welle', 'CNN', 'The Guardian', 'New York Times', 'France 24', 'France 24 (EN)', 'Le Monde', 'NPR', 'Euronews', 'Bloomberg', 'Financial Times', 'El País', 'La Repubblica', 'Al Jazeera', 'Anadolu Agency'],
    ARRAY['threat', 'amenaza', 'sovereignty', 'soberan', 'injerencia', 'interference', 'institutional', 'democracia', 'tariff', 'sanction'],
    false,
    ARRAY['AMERICAS-ANDEAN'],
    true,
    3
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_theater_hegemonic_critique',
    'colombia_theater',
    -2,
    'Hemispheric domination critique',
    'Kritik hemisphärischer Vorherrschaft',
    'The region as a sphere of influence',
    'Die Region als Einflusssphäre',
    'State and non-Western outlets read the same events as a single demonstration of US primacy in the hemisphere -- military threats, strikes in neighbouring Venezuela and open intervention in an allied democracy''s election -- rather than as separate bilateral disputes.',
    'Staatliche und außerwestliche Medien lesen dieselben Ereignisse als eine einzige Demonstration US-amerikanischer Vormacht in der Hemisphäre -- Militärdrohungen, Angriffe im benachbarten Venezuela und offene Einmischung in die Wahl einer verbündeten Demokratie -- und nicht als getrennte bilaterale Streitfälle.',
    ARRAY['CGTN', 'China Daily', 'Global Times', 'Xinhua', 'RT', 'TASS', 'TASS (EN)', 'Sputnik', 'RIA Novosti', 'Press TV', 'Al-Ahram'],
    ARRAY['hegemon', 'imperial', 'soberan', 'injerencia', 'domination', 'unilateral', 'sphere of influence'],
    false,
    ARRAY['AMERICAS-USA'],
    true,
    4
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_us_rapprochement',
    'colombia_us_alignment',
    1,
    'Negotiated rapprochement',
    'Ausgehandelte Annäherung',
    'The channel was repaired',
    'Der Gesprächskanal wurde repariert',
    'Coverage of the reversal treats the White House meeting as evidence that the relationship remains negotiable: threats gave way to an invitation, both governments claimed a working understanding, and cooperation on security and trade resumed.',
    'Die Berichterstattung über die Kehrtwende wertet das Treffen im Weißen Haus als Beleg dafür, dass die Beziehung verhandelbar bleibt: Auf Drohungen folgte eine Einladung, beide Regierungen reklamierten eine Arbeitsverständigung, und die Zusammenarbeit bei Sicherheit und Handel wurde wieder aufgenommen.',
    ARRAY['Reuters', 'Associated Press', 'BBC World', 'Deutsche Welle', 'CNN', 'The Guardian', 'New York Times', 'France 24', 'France 24 (EN)', 'Le Monde', 'NPR', 'Euronews', 'Bloomberg', 'Financial Times', 'El País'],
    ARRAY['détente', 'detente', 'amends', 'meeting', 'reunión', 'encuentro', 'invit', 'pacto', 'acuerdo', 'visita', 'recibe', 'host', 'talks', 'deal'],
    true,
    ARRAY['AMERICAS-USA'],
    true,
    1
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_us_coercion',
    'colombia_us_alignment',
    -1,
    'Coercion against a partner',
    'Zwang gegen einen Partner',
    'Threats replaced diplomacy',
    'Drohungen ersetzten Diplomatie',
    'The critical reading holds that an allied government was subjected to a threatened military operation, tariff pressure and sanctions designations over a policy dispute, and that Bogotá''s formal complaint marked a durable shift in what the relationship can be assumed to guarantee.',
    'Die kritische Lesart hält fest, dass eine verbündete Regierung wegen eines politischen Streits mit einer angedrohten Militäroperation, Zolldruck und Sanktionslistungen überzogen wurde und dass Bogotás förmliche Beschwerde eine dauerhafte Verschiebung dessen markiert, was die Beziehung noch garantiert.',
    ARRAY['Reuters', 'Associated Press', 'BBC World', 'Deutsche Welle', 'CNN', 'The Guardian', 'New York Times', 'France 24', 'France 24 (EN)', 'Le Monde', 'NPR', 'Euronews', 'Bloomberg', 'Financial Times', 'El País'],
    ARRAY['threat', 'amenaza', 'military operation', 'operación militar', 'military action', 'tariff', 'arancel', 'sanction', 'sanción', 'sovereignty', 'soberan', 'complaint', 'queja', 'insult', 'slander'],
    true,
    ARRAY['AMERICAS-USA'],
    true,
    2
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

INSERT INTO narratives_v2 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de, publishers, framing_keywords, framing_required, actor_centroids, is_active, display_order) VALUES (
    'colombia_us_imperial_overreach',
    'colombia_us_alignment',
    -2,
    'Hegemonic imposition',
    'Hegemoniale Anmaßung',
    'A sovereign state treated as a subordinate',
    'Ein souveräner Staat als Untergebener behandelt',
    'State and non-Western outlets present the episode as an assertion of hemispheric domination rather than a bilateral dispute: military threats against a sovereign government, coupled with strikes in neighbouring Venezuela, are framed as the working method of US regional primacy.',
    'Staatliche und außerwestliche Medien stellen die Episode als Behauptung hemisphärischer Vorherrschaft dar und nicht als bilateralen Streit: Militärdrohungen gegen eine souveräne Regierung, verbunden mit Angriffen im benachbarten Venezuela, gelten als Arbeitsmethode US-amerikanischer Regionalvormacht.',
    ARRAY['CGTN', 'China Daily', 'Global Times', 'Xinhua', 'RT', 'TASS', 'TASS (EN)', 'Sputnik', 'RIA Novosti', 'Press TV', 'Al Jazeera', 'Anadolu Agency', 'Al-Ahram'],
    ARRAY['hegemon', 'imperial', 'sovereignty', 'soberan', 'interference', 'injerencia', 'domination', 'bullying', 'unilateral'],
    false,
    ARRAY['AMERICAS-USA'],
    true,
    3
)
ON CONFLICT (id) DO UPDATE SET
    fn_id = EXCLUDED.fn_id,
    stance = EXCLUDED.stance,
    stance_label_en = EXCLUDED.stance_label_en,
    stance_label_de = EXCLUDED.stance_label_de,
    name_en = EXCLUDED.name_en,
    name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en,
    claim_de = EXCLUDED.claim_de,
    publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords,
    framing_required = EXCLUDED.framing_required,
    actor_centroids = EXCLUDED.actor_centroids,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

-- ============================================================================
-- POST-APPLY VERIFICATION (run inside the same session, before COMMIT)
-- Expected: 4 | 3 | 11 | 7
-- ============================================================================
SELECT
    (SELECT count(*) FROM friction_nodes WHERE id LIKE 'colombia%')                      AS fn_rows,
    (SELECT count(*) FROM taxonomy_v3 WHERE taxonomy_function='fn_anchor'
       AND linked_id LIKE 'colombia%')                                                   AS bundles,
    (SELECT count(*) FROM narratives_v2 WHERE fn_id LIKE 'colombia%')                    AS narratives,
    (SELECT count(*) FROM narratives_v2 WHERE fn_id LIKE 'colombia%' AND fn_id <> 'colombia_theater') AS atomic_narratives;

-- Bilingual completeness -- expect 4 rows, all t
SELECT id,
       (name_de IS NOT NULL AND description_en IS NOT NULL AND description_de IS NOT NULL
        AND editorial_summary_en IS NOT NULL AND editorial_summary_de IS NOT NULL) AS complete_bilingual
FROM friction_nodes WHERE id LIKE 'colombia%' ORDER BY id;

-- Theater must carry NO bundle of its own -- expect 0
SELECT count(*) AS theater_bundle_must_be_zero
FROM taxonomy_v3 WHERE taxonomy_function='fn_anchor' AND linked_id='colombia_theater';

-- Bundle alias counts -- expect EXACTLY: armed_groups_peace 56,
-- political_transition 40, us_alignment 66 (measured on local after the
-- rehearsal run below; any deviation means the bundle did not transfer whole)
SELECT linked_id,
       (SELECT count(*) FROM jsonb_each(aliases) l, jsonb_array_elements_text(l.value)) AS alias_count
FROM taxonomy_v3 WHERE taxonomy_function='fn_anchor' AND linked_id LIKE 'colombia%' ORDER BY linked_id;

COMMIT;

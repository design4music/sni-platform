-- Rebuild ukraine_official_corruption narratives into a 3-stance model that
-- fixes the "friendly-critic" defect: Western outlets (Spiegel, BBC, WaPo)
-- voice BOTH a reform-progress framing and a systemic-alarm framing, so the
-- old 2-narrative publisher-coalition model misfiled all alarmed Western
-- corruption coverage as "reform in progress".
--
-- New gradient:
--   reform_in_progress      (+1) Western pubs, framing_required, reform-positive kw
--   western_systemic_alarm  (-1) SAME Western pubs, framing_required, alarm kw   [NEW]
--   zelensky_regime_corruption (-2) pro-Russian/Global South pubs, unchanged
--
-- The two Western narratives share a coalition; framing_required + framing
-- keywords route each title to the stance it actually expresses (see
-- bootstrap_friction_node.link_titles).
SET client_encoding TO 'UTF8';

-- 1. reform_in_progress: turn on framing gate, narrow keywords to genuinely
--    reform-positive framing (institutions working / independence defended).
UPDATE narratives_v2
SET framing_required = true,
    framing_keywords = ARRAY[
      'reform progress','institutional independence','restored independence',
      'agency autonomy','defended independence','anti-corruption reform',
      'EU praises','IMF benchmark','judicial reform','functioning institutions',
      'proof of independence','Reformfortschritt','Unabhängigkeit der Behörden',
      'Antikorruptionsreform','wiederhergestellte Unabhängigkeit'
    ],
    updated_at = NOW()
WHERE id = 'reform_in_progress';

-- 2. NEW western_systemic_alarm: clone reform's Western publishers +
--    actor_centroids, broad alarm framing (critical but NOT pro-Russian).
INSERT INTO narratives_v2
  (id, name_en, name_de, claim_en, claim_de, actor_centroids, framing_keywords,
   is_active, publishers, fn_id, display_order, stance_label_en, stance_label_de,
   stance, framing_required)
SELECT
  'western_systemic_alarm',
  'Western alarm: high-level corruption threatens Ukraine credibility and aid',
  'Westliche Alarmierung: Korruption auf höchster Ebene gefährdet Glaubwürdigkeit und Hilfe',
  'Systemic-alarm framing (Western mainstream + reformist Ukrainian press) treats high-level corruption cases -- reaching the Presidential Office and figures like Yermak -- as a threat to Ukraine credibility, Western aid, and EU accession, rather than proof that institutions work. Distinct from Russian-state endemic-corruption framing: it does not call the state illegitimate or aid categorically stolen, but expresses genuine concern from Ukraine supporters. Vocabulary: corruption scandal, case widens, probe escalates, reaches the top, inner circle, chief of staff, survives for now, wartime graft, threatens aid, credibility.',
  'Systemische-Alarm-Rahmung (westlicher Mainstream + reformorientierte ukrainische Presse) behandelt Korruptionsfälle auf höchster Ebene -- bis ins Präsidialbüro und zu Figuren wie Jermak -- als Bedrohung für Glaubwürdigkeit, westliche Hilfe und EU-Beitritt, nicht als Beweis funktionierender Institutionen. Anders als die russische Rahmung erklärt sie den Staat nicht für illegitim.',
  actor_centroids,
  ARRAY[
    'corruption scandal','corruption affair','corruption case','case widens',
    'probe widens','probe escalates','corruption probe','high-level corruption',
    'reaches the top','inner circle','chief of staff','ex-chief of staff',
    'right-hand man','survives','for now','wartime graft','embezzlement',
    'stolen aid','deep-rooted','credibility','threatens aid','how corrupt',
    'gut anti-corruption','curb anti-corruption','undermine anti-corruption',
    'Yermak','Mindich',
    'Korruptionsaffäre','Korruptionsskandal','Korruptionsfall','wie korrupt',
    'tiefe Fall','Ex-Stabschef','Stabschef','Jermak','übersteht'
  ],
  true,
  publishers,
  'ukraine_official_corruption',
  2,
  'Western alarm at systemic corruption',
  'Westliche Alarmierung über systemische Korruption',
  -1,
  true
FROM narratives_v2
WHERE id = 'reform_in_progress'
ON CONFLICT (id) DO NOTHING;

-- 3. push the pro-Russian narrative down the stance gradient (display only).
UPDATE narratives_v2 SET display_order = 3, updated_at = NOW()
WHERE id = 'zelensky_regime_corruption';

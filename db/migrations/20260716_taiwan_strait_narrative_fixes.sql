-- Taiwan Strait: narrative fixes found by reading real per-narrative samples (§0a step 9).
-- Counts looked plausible; the samples did not. Three defects:
--
-- 1. us_commitment_firm was built on STANCE-AMBIGUOUS framing keywords. 'approve' matches
--    "hopes package can be approved soon", "US could approve", "pressure to approve" and
--    "Arms Sale Approved by Congress Is DELAYED" -- aspiration and blockage, not a firm
--    commitment. Only ~2 of its 12 titles were genuinely firm, and 2 titles landed in BOTH
--    contradictory stances. Same class as the eu_cohesion 'Zusammenarbeit mit der AfD' bug.
--    'reaffirm' is ambiguous too ("Mainland reaffirms one-China principle", "Xi Reaffirms
--    Push for Taiwan Reunification"). Keywords tightened to unambiguous affirmations only.
--    The count drops to ~4, which is the honest size of firm-commitment coverage in 2026 --
--    the real story is doubt-dominated. Precision over recall (§5.3).
--
-- 2. us_commitment_doubted gains the blockage/hesitation vocabulary that 'approve' was
--    wrongly absorbing: less than, pause, reconsider, weighs, blank check, shortfall.
--
-- 3. cross_strait_exchange_goodwill was MISLABELLED. Its 85 titles are not just exchange
--    coverage -- they include "Liaoning carrier group's live-fire training [as] deterrent
--    against separatist forces", "separatists never allowed to profit", "Lai suffers
--    collapsing popular support". The bundle's 'separatist'/'Taiwan independence' anchors
--    (32 titles) carry Beijing rhetoric across every sub-topic, and with
--    framing_required=false every Chinese-state title in the FN lands here. The content is
--    coherent -- it is Beijing's single political campaign, courtship AND coercion -- but
--    the label promised only goodwill. Re-keyed and relabelled to match what it actually
--    holds rather than narrowing the match. Re-keying uses DELETE+INSERT; the FK
--    title_narratives.narrative_id is ON DELETE CASCADE, so its title_narratives rows drop
--    and are rebuilt by the bootstrap re-run that follows this migration.

BEGIN;

-- 1. Tighten us_commitment_firm to unambiguous affirmations.
UPDATE narratives_v2
   SET framing_keywords = ARRAY[
           'no change in US policy', 'no change in policy', 'continued support',
           'unwavering', 'rock-solid', 'ironclad', 'iron-clad', 'steadfast',
           'not withholding', 'remains committed', 'top Biden-era', 'top Biden',
           'parliament approves', 'parliament authorises', 'authorises signing',
           'major arms deal', 'fortgesetzte Unterstützung', 'unerschütterlich'
       ],
       updated_at = now()
 WHERE id = 'us_commitment_firm';

-- 2. Give us_commitment_doubted the blockage vocabulary.
UPDATE narratives_v2
   SET framing_keywords = framing_keywords || ARRAY[
           'less than', 'pause', 'paused', 'reconsider', 'weighs', 'shortfall',
           'blank check', 'not assured', 'in doubt'
       ],
       updated_at = now()
 WHERE id = 'us_commitment_doubted';

-- 3. Re-key + relabel the mislabelled Beijing narrative on taiwan_political_warfare.
INSERT INTO narratives_v2
 (id, fn_id, stance, stance_label_en, stance_label_de, name_en, name_de, claim_en, claim_de,
  actor_centroids, publishers, framing_keywords, framing_required, display_order, is_active,
  created_at, updated_at)
SELECT 'beijing_antiseparatism_unity', fn_id, stance,
       'Anti-separatism and cross-strait unity',
       'Anti-Separatismus und Einheit über die Meerenge',
       'Opposing separatism and building cross-strait unity is legitimate, and the governing party obstructs it',
       'Dem Separatismus entgegenzutreten und die Einheit über die Meerenge zu fördern ist legitim, und die Regierungspartei blockiert dies',
       'Anti-separatism framing (Chinese and Russian state media) presents Beijing''s political campaign as legitimate and popular: hosting the opposition party''s delegations, offering exchanges, incentives and preferential policies to "Taiwan compatriots", denouncing "Taiwan independence" forces and their foreign backers, and casting the governing party as an unpopular obstacle serving external forces. Courtship and coercion run together here as one campaign -- inducements for the opposition alongside blacklists and warnings to separatists. Vocabulary: compatriot, exchange, reunification, separatist, external forces, obstruct, hype, preferential policies.',
       'Die Anti-Separatismus-Rahmung (chinesische und russische Staatsmedien) stellt Pekings politische Kampagne als legitim und populär dar: Empfang der Delegationen der Oppositionspartei, Austausch, Anreize und Vorzugsregelungen für "taiwanische Landsleute", Verurteilung der "Taiwan-Unabhängigkeits"-Kräfte und ihrer ausländischen Unterstützer sowie die Zeichnung der Regierungspartei als unpopuläres Hindernis im Dienst äußerer Kräfte. Werbung und Zwang laufen hier als eine Kampagne zusammen.',
       actor_centroids, publishers,
       ARRAY['compatriot', 'exchange', 'goodwill', 'peaceful reunification', 'reunification',
             'family', 'integration', 'obstruct', 'hype', 'preferential', 'welcome',
             'separatist', 'Taiwan independence', 'external forces', 'one family',
             'Landsleute', 'Wiedervereinigung'],
       framing_required, display_order, true, now(), now()
FROM narratives_v2 WHERE id = 'cross_strait_exchange_goodwill'
ON CONFLICT (id) DO NOTHING;

DELETE FROM narratives_v2 WHERE id = 'cross_strait_exchange_goodwill';

COMMIT;

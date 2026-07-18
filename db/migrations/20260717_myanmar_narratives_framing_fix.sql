-- Myanmar narratives: framing fix after reading samples (SPEC 9).
--
-- First bootstrap exposed two defects:
--   * -2 illegitimate at 408 titles (87% of corpus) = a FIREHOSE. With a bare-
--     "Myanmar" bundle, publisher-only (framing_required=false) filed earthquake
--     survivors, a ruby find, a river-port fire, "China-Myanmar deeper ties" and
--     a cosmetic-surgery arrest all under "illegitimate junta". Publisher can't
--     discriminate topic when the bundle is just the country name.
--   * +2 normalisation at 6 = under-recall. Keywords were too phrase-specific;
--     they missed the real normalisation vocabulary (president sworn in / elected,
--     Xi greetings, Wang Yi, "enhance cooperation", state visit, congratulate).
--
-- Fix: framing_required=true on ALL three (Greenland precedent), keyword sets
-- broadened to the phenomenon's real headline vocabulary. Publisher camps are
-- disjoint (Chinese/Russian state vs Western/regional), so even generic keywords
-- are safe once publisher-gated; titles matching no framing are dropped
-- (precision over recall) -- that is correct for neutral Myanmar coverage that
-- belongs in no stance card.

BEGIN;

UPDATE narratives_v2 SET
  framing_required = true,
  framing_keywords = ARRAY[
    'president','sworn in','inaugurat','elected','elect','vice president',
    'congratulat','greetings','Wang Yi','enhance cooperation','deepen cooperation',
    'pragmatic cooperation','cooperation','new government','state visit','visit',
    'meets','delegation','corridor','investment','bilateral','ties','sovereignty',
    'stability','back its security','momentum','transition','civilian',
    'Präsident','Wahl','Zusammenarbeit','Staatsbesuch','Stabilität','Souveränität','gewählt',
    '总统','主席','合作','国事访问','主权','稳定','当选','访问',
    'президент','сотрудничеств','суверенитет','стабильн','визит'],
  updated_at = now()
WHERE id = 'myanmar_beijing_backed_normalisation';

UPDATE narratives_v2 SET
  framing_required = true,
  framing_keywords = ARRAY[
    'sham','junta','coup','airstrike','air strike','house arrest','Suu Kyi',
    'political prisoner','prisoner','atrocit','killed','crackdown','illegitimate',
    'recogni','refuse','reject','condemn','rights','genocide','forced','detain',
    'jail','opposition','resistance','rebel','civil war','sanction','poll','fraud',
    'Scheinwahl','Junta','Putsch','Luftangriff','Hausarrest','Sanktion','Bürgerkrieg','erkennt',
    '軍政','弾圧','クーデター','军政府','镇压','انقلاب','хунта','переворот','तख्तापलट'],
  updated_at = now()
WHERE id = 'myanmar_illegitimate_junta_rule';

UPDATE narratives_v2 SET
  framing_required = true,
  framing_keywords = ARRAY[
    'scam','cyberscam','fraud','traffick','compound','scam hub','scam centre',
    'scam center','scam mafia','forced labo','Myawaddy','KK Park','execute',
    'execution','mafia','syndicate','kingpin','fraud hub','criminal','repatriat',
    'gang','pig butcher','slave',
    '詐欺','拠点詐欺','Betrug','Menschenhandel','estafa','fraude','arnaque'],
  updated_at = now()
WHERE id = 'myanmar_criminal_economy_spillover';

COMMIT;

-- Fix the AFRICA-DRC <-> OCEANIA-AUSTRALIA `ADF` centroid-alias collision.
-- Found during the Great Lakes structural assessment, 2026-07-20.
-- Same class as the OCEANIA-PAPUANEWGUINEA `Lae` bug (lessons_centroid_short_
-- alias_collisions), but BIDIRECTIONAL: `ADF` is an alias on BOTH centroids, so
-- every matching title is tagged with both countries.
--
-- Measured over 180d: 22 titles match `ADF` and all 22 carry AFRICA-DRC AND
-- OCEANIA-AUSTRALIA. Only 7 are the Congolese Allied Democratic Forces:
--
--   Australian Defence Force        13  ("Katherine flood volunteers welcome ADF
--                                        support", "ADF member charged over crash
--                                        ... north-west of Brisbane", "Australian
--                                        Mogami ships ... ADF chief says")
--   Antalya Diplomacy Forum          1  ("ADF 2026 marks Turkiye's diplomatic
--                                        outreach")
--   A Russian VK conference          1  ("VK ADF возвращается в Москву")
--   Allied Democratic Forces (real)  7
--
-- => 68% junk on the DRC side. Left alone it would pollute every Great Lakes
--    atomic before any FN work started.
--
-- ---------------------------------------------------------------------------
-- THE FIX IS ASYMMETRIC, because the recall cost is asymmetric.
--
-- Remove `ADF` from AFRICA-DRC only. Verified zero recall loss: all 7 genuine
-- Congolese ADF titles independently match another AFRICA-DRC alias --
-- matched_aliases shows {adf,congo} x4, {adf,drc} x2, {adf,rdc} x1. Not one of
-- them depends on `ADF` to be tagged. Replaced with the unambiguous long form
-- `Allied Democratic Forces` so the alias still carries meaning where spelled out.
--
-- KEEP `ADF` on OCEANIA-AUSTRALIA. There the recall cost is real: "ADF members
-- witnesses in case against Ben Roberts-Smith", "Deputy chief of army warns ADF
-- has become 'detached'..." and "ADF member charged over crash" carry NO other
-- Australia alias. `ADF` is the standard Australian register.
--
-- Residual accepted: the 7 Congolese ADF titles keep carrying OCEANIA-AUSTRALIA.
-- Low impact -- the Australia atomics gate on their own bundles, so a Beni
-- massacre headline only attributes there if it also matches Australian
-- phenomenon vocabulary, which it does not.
--
-- Dropped from en/fr/hi/ja. The ru (АДФ), zh (ADF武装) and ar (قوات التحالف
-- الديمقراطي) forms are script- or compound-qualified and carry no collision;
-- they stay.

BEGIN;

UPDATE taxonomy_v3
SET aliases = jsonb_set(
        jsonb_set(
            jsonb_set(
                jsonb_set(
                    aliases,
                    '{en}', '["M23", "Allied Democratic Forces", "CODECO"]'::jsonb
                ),
                '{fr}', '["M23", "Forces démocratiques alliées", "CODECO"]'::jsonb
            ),
            '{hi}', '["M23", "CODECO"]'::jsonb
        ),
        '{ja}', '["M23", "CODECO"]'::jsonb
    ),
    updated_at = NOW()
WHERE id = 'e53fbae3-bbd5-44f6-ba43-45ef7e110b52'
  AND linked_id = 'AFRICA-DRC'
  AND taxonomy_function = 'centroid_anchor';

COMMIT;

-- us_judicial_constraint: widen the name to match measured scope (2026-07-20).
--
-- The atomic was built as "Judicial constraint on executive power" with the
-- culture-war docket pillar (LGBT, abortion, transgender, gun rights, Second
-- Amendment, age verification, campaign finance) deliberately dropped, so that
-- the retired us_culture_wars did not re-enter through the back door.
--
-- Adding the Arctic-style compound anchors ("Supreme Court rules/blocks/upholds/
-- ...", 372 titles at ~9% foreign) was necessary because the bare form is ~20%
-- foreign on this gate -- Indian outlets alone are 244 of 1,559. But those
-- compounds necessarily also admit rulings whose SUBJECT is the docket rather
-- than executive power (the California transgender-students policy, the abortion
-- pill, Texas Ten Commandments). Attribution went 285 -> 371 events.
--
-- That content is real US-domestic friction and foreign media do cover SCOTUS as
-- a political institution, so it is kept -- but the old name no longer described
-- it. Renaming rather than pretending the scope did not move.
--
-- Name only; id, centroids, target and bundle unchanged. No DELETE.

BEGIN;

UPDATE friction_nodes
SET name_en = 'Federal courts and executive power',
    name_de = 'Bundesgerichte und die Macht der Exekutive',
    updated_at = NOW()
WHERE id = 'us_judicial_constraint';

COMMIT;

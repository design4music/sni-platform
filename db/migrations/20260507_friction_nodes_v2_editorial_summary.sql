-- Editorial summary on friction_nodes — a 1-2 paragraph context piece
-- written above the description, putting the FN in strategic context
-- (what's at stake, why this matters, recent shifts).
-- 2026-05-07

BEGIN;

ALTER TABLE friction_nodes
    ADD COLUMN IF NOT EXISTS editorial_summary_en text,
    ADD COLUMN IF NOT EXISTS editorial_summary_de text;

UPDATE friction_nodes
SET
    editorial_summary_en = $D$Iran's nuclear program is the single longest-running structural contest in the contemporary Middle East. The same physical reality — centrifuge cascades at Natanz and Fordow, an enrichment stockpile, a treaty regime, an IAEA inspection corridor — is read through frames that demand opposite actions. Israel and the United States treat any continuing enrichment capability as an existential threshold to be denied; Iran treats enrichment as a sovereign right anchored in NPT Article IV and a religious-juridical fatwa against weaponisation; the E3 / EU coalition treats the whole question as a diplomatic process that must be preserved at almost any cost; the Russia-China-aligned bloc treats Western pressure as imperial overreach against a sovereign state. The 2026 war shifted the contest into kinetic territory — strikes on Natanz, retaliatory missile exchanges, evacuations from Bushehr — but the underlying structural disagreement has not moved.$D$,
    editorial_summary_de = $D$Das iranische Atomprogramm ist der einzig langlaufende strukturelle Konflikt im Nahen Osten. Dieselbe physische Realitaet — Zentrifugen-Kaskaden in Natanz und Fordow, ein Anreicherungsbestand, ein Vertragsregime, ein IAEO-Inspektionskorridor — wird durch Rahmen gelesen, die gegensaetzliche Handlungen fordern. Israel und die Vereinigten Staaten behandeln jede fortgesetzte Anreicherungsfaehigkeit als existenzielle Schwelle, die verweigert werden muss; Iran behandelt Anreicherung als souveraenes Recht, verankert in NPT-Artikel IV und einer religioes-juristischen Fatwa gegen Waffenfertigung; die E3/EU-Koalition behandelt die gesamte Frage als diplomatischen Prozess, der um fast jeden Preis bewahrt werden muss; der Russland-China-Block behandelt westlichen Druck als imperialistische Anmassung gegen einen souveraenen Staat. Der Krieg 2026 hat den Konflikt ins Kinetische verlagert — Schlaege auf Natanz, Vergeltungs-Raketenwechsel, Evakuierungen aus Bushehr — die strukturelle Uneinigkeit hat sich aber nicht bewegt.$D$,
    updated_at = now()
WHERE id = 'iran_nuclear_program';

COMMIT;

-- Great Lakes: bilingual completeness fields (§6), 2026-07-20.
-- description_en/_de + editorial_summary_en/_de for the theater and all three
-- active atomics. name_en/name_de were set in the structure migration.
--
-- Descriptions are NEUTRAL and EVERGREEN -- they state what the dispute is
-- about, not who is right. All framing lives in narratives_v2. In particular
-- the Rwandan-backing claim is written as a contested attribution rather than
-- as fact, because that attribution is precisely what the atomic's narrative
-- axis is built on.
--
-- The theater description deliberately avoids naming a count of component
-- disputes (that number is not a constant) and uses no internal vocabulary.

BEGIN;

UPDATE friction_nodes SET
    description_en = 'The eastern provinces of the Democratic Republic of the Congo have been contested for three decades by armed groups, the Congolese state and neighbouring governments. The current phase combines the M23 insurgency and its disputed external backing, an externally brokered mediation and sanctions track, and competition over the cobalt, coltan and copper deposits that sit in and around the same territory. The United States, China, Rwanda, Uganda, Burundi and the United Nations mission are all engaged.',
    description_de = 'Die östlichen Provinzen der Demokratischen Republik Kongo sind seit drei Jahrzehnten zwischen bewaffneten Gruppen, dem kongolesischen Staat und den Nachbarregierungen umkämpft. Die gegenwärtige Phase verbindet den M23-Aufstand und dessen umstrittene Unterstützung von außen, einen extern vermittelten Verhandlungs- und Sanktionsstrang sowie den Wettbewerb um die Kobalt-, Coltan- und Kupfervorkommen, die in und um dasselbe Gebiet liegen. Die Vereinigten Staaten, China, Ruanda, Uganda, Burundi und die Mission der Vereinten Nationen sind daran beteiligt.',
    editorial_summary_en = 'Coverage in the first half of 2026 divides sharply: the M23 war de-escalated through the period while the mediation and sanctions track kept producing, and an Ebola outbreak came to dominate Congolese coverage overall without being part of this dispute.',
    editorial_summary_de = 'Die Berichterstattung im ersten Halbjahr 2026 teilt sich deutlich: Der M23-Krieg deeskalierte im Verlauf, während der Vermittlungs- und Sanktionsstrang weiter Nachrichten produzierte; zugleich beherrschte ein Ebola-Ausbruch die Kongo-Berichterstattung insgesamt, ohne Teil dieses Konflikts zu sein.',
    updated_at = NOW()
WHERE id = 'great_lakes_theater';

UPDATE friction_nodes SET
    description_en = 'M23 is an armed movement operating in North and South Kivu, aligned since 2023 with the Alliance Fleuve Congo. It has held Goma and other eastern towns, and the Congolese government, the United Nations and Western states attribute its capability to support from Rwanda -- an attribution Kigali rejects. The node also covers the other armed groups active in the same provinces, including the Allied Democratic Forces and CODECO.',
    description_de = 'M23 ist eine bewaffnete Bewegung in Nord- und Süd-Kivu, seit 2023 mit der Alliance Fleuve Congo verbunden. Sie hielt Goma und weitere Städte im Osten; die kongolesische Regierung, die Vereinten Nationen und westliche Staaten führen ihre Schlagkraft auf Unterstützung aus Ruanda zurück -- eine Zuschreibung, die Kigali zurückweist. Erfasst sind auch die übrigen bewaffneten Gruppen in denselben Provinzen, darunter die Allied Democratic Forces und CODECO.',
    editorial_summary_en = 'Kinetic coverage fell steadily across the first half of 2026, from heavy fighting and drone strikes early in the year to an M23 withdrawal and government forces retaking ground by May.',
    editorial_summary_de = 'Die Berichterstattung über Kampfhandlungen ging im ersten Halbjahr 2026 stetig zurück -- von schweren Gefechten und Drohnenangriffen zu Jahresbeginn bis zum Rückzug der M23 und der Rückeroberung von Gebieten durch Regierungstruppen im Mai.',
    updated_at = NOW()
WHERE id = 'm23_conflict';

UPDATE friction_nodes SET
    description_en = 'Efforts to end the fighting in eastern Congo run through several external tracks at once: agreements associated with Washington, talks in Doha and Switzerland, a signed ceasefire-monitoring mechanism, and the United Nations mission that is being reconfigured to support it. Alongside them runs an enforcement track of financial designations and travel restrictions aimed at Rwandan military figures and at Congolese political figures accused of supporting the rebellion.',
    description_de = 'Die Bemühungen, die Kämpfe im Osten Kongos zu beenden, laufen über mehrere externe Stränge zugleich: mit Washington verbundene Vereinbarungen, Gespräche in Doha und in der Schweiz, ein unterzeichneter Mechanismus zur Waffenstillstandsüberwachung und die Mission der Vereinten Nationen, die darauf ausgerichtet wird. Daneben verläuft ein Durchsetzungsstrang aus Finanzlistungen und Reisebeschränkungen gegen ruandische Militärs und gegen kongolesische Politiker, denen Unterstützung des Aufstands vorgeworfen wird.',
    editorial_summary_en = 'The largest single cluster here is the designation of the Rwandan army and of former president Joseph Kabila; the accords themselves generate far less coverage than the sanctions used to enforce them.',
    editorial_summary_de = 'Das größte einzelne Cluster ist die Listung der ruandischen Armee und des früheren Präsidenten Joseph Kabila; die Abkommen selbst erzeugen deutlich weniger Berichterstattung als die Sanktionen zu ihrer Durchsetzung.',
    updated_at = NOW()
WHERE id = 'drc_peace_process';

UPDATE friction_nodes SET
    description_en = 'The Democratic Republic of the Congo holds the world''s largest cobalt reserves and a significant share of its coltan, tantalum and copper. Chinese companies built much of the existing refining and processing base; American-backed buyers have more recently acquired producers and sought stakes tied to a minerals arrangement with Kinshasa. Some of the deposits concerned lie in territory held by armed groups, and the state has used export controls to influence prices.',
    description_de = 'Die Demokratische Republik Kongo verfügt über die weltweit größten Kobaltreserven sowie über bedeutende Anteile an Coltan, Tantal und Kupfer. Chinesische Unternehmen bauten einen Großteil der bestehenden Raffinerie- und Verarbeitungsbasis auf; zuletzt erwarben US-gestützte Käufer Produzenten und strebten Beteiligungen im Rahmen einer Rohstoffvereinbarung mit Kinshasa an. Ein Teil der betroffenen Vorkommen liegt in Gebieten bewaffneter Gruppen, und der Staat nutzte Exportkontrollen, um Preise zu beeinflussen.',
    editorial_summary_en = 'Two strands run together and are not separable in coverage: the contest between American and Chinese buyers for Congolese assets, and the human and environmental record of the extraction itself.',
    editorial_summary_de = 'Zwei Stränge laufen zusammen und sind in der Berichterstattung nicht zu trennen: der Wettbewerb amerikanischer und chinesischer Käufer um kongolesische Werte und die menschliche und ökologische Bilanz der Förderung selbst.',
    updated_at = NOW()
WHERE id = 'drc_minerals_competition';

COMMIT;

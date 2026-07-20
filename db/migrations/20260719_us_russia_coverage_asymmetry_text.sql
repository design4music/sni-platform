-- US-Russia theater: surface the coverage asymmetry as a stated finding. 2026-07-19.
--
-- The bilateral_channel atomic has small Western narrative cards (1 and 5 titles)
-- and much larger Russian-state ones. That is not a recall failure -- it was
-- measured and confirmed: Western outlets almost entirely file US-Russia contacts
-- as UKRAINE-WAR coverage, so the Western case for or against engagement is made
-- inside Ukraine stories rather than as bilateral commentary. Russian state media
-- write the bilateral relationship as a subject in its own right and therefore
-- produce dense standalone commentary on it.
--
-- That asymmetry is itself an analytical result about how the two media systems
-- construct the relationship, so it is stated in the editorial summaries and in
-- the affected narrative claims rather than left as an unexplained size gap. A
-- reader who sees a 1-title Western card next to a 41-title Kremlin card should
-- be told what that gap means.
--
-- Deliberately NOT put in description_* -- those stay neutral and evergreen
-- (feedback_fn_descriptions_neutral); this is an observation about the current
-- coverage pattern, which is what editorial_summary_* is for.
--
-- Text only. No structural, gating or attribution change.

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Atomic editorial summary: promote the asymmetry from trailing caveat to
--    stated finding.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  editorial_summary_en = 'Contact is far denser than at any point since 2022. US envoys have travelled repeatedly to Moscow, the two militaries have re-established high-level communication, foreign ministers speak by phone, and leader-level calls have become routine enough to include congratulatory exchanges. Moscow presents this as overdue recognition of parity while simultaneously accusing Washington of stalling and issuing ultimatums -- the two Kremlin registers run side by side.

The most telling pattern here is where the coverage lives rather than what it says. Russian state media treat the bilateral relationship as a standing subject and produce continuous commentary on its condition; Western outlets cover the same meetings and calls almost entirely as Ukraine-war developments, with the relationship itself appearing only as context. The result is that Moscow generates a large body of explicit narrative about the relationship while the Western position on it has to be inferred from war reporting -- an asymmetry in framing, not in the underlying events, and one reason the Kremlin''s account of the relationship travels more easily than any competing one.',
  editorial_summary_de = 'Die Kontaktdichte ist so hoch wie zu keinem Zeitpunkt seit 2022. US-Sondergesandte reisten mehrfach nach Moskau, beide Streitkräfte stellten die Kommunikation auf hoher Ebene wieder her, die Außenminister telefonieren, und Gespräche auf Führungsebene sind so alltäglich geworden, dass sie Glückwünsche einschließen. Moskau stellt dies als überfällige Anerkennung der Ebenbürtigkeit dar und wirft Washington zugleich Hinhalten und Ultimaten vor -- beide Register laufen nebeneinander.

Aufschlussreicher als der Inhalt ist, wo diese Berichterstattung stattfindet. Russische Staatsmedien behandeln das bilaterale Verhältnis als dauerhaften Gegenstand und kommentieren seinen Zustand fortlaufend; westliche Medien berichten über dieselben Treffen und Telefonate fast ausschließlich als Entwicklungen des Ukrainekriegs, das Verhältnis selbst erscheint nur als Kontext. So entsteht in Moskau ein großer Bestand ausdrücklicher Erzählungen über die Beziehung, während die westliche Position dazu aus der Kriegsberichterstattung erschlossen werden muss -- eine Asymmetrie der Rahmung, nicht der Ereignisse, und ein Grund, weshalb die Kreml-Darstellung des Verhältnisses leichter Verbreitung findet als konkurrierende.',
  updated_at = NOW()
WHERE id = 'us_russia_bilateral_channel';

-- ---------------------------------------------------------------------------
-- 2. Theater editorial summary: one line, so the pattern is visible above the
--    atomic level too.
-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
  editorial_summary_en = 'The relationship is in an unsettled thaw. Working contacts have been rebuilt -- envoy visits to Moscow, a resumed high-level military channel, repeated leader-level calls -- while Washington has repeatedly issued and withdrawn waivers on Russian oil, drawing objections from European and British partners still tightening enforcement. The last nuclear warhead limits lapsed with New START in February 2026, leaving the two arsenals unconstrained for the first time in decades. Coverage divides less along US-versus-Russia lines than over how much accommodation of Moscow is warranted, with Western outlets on both sides of that question and third-country buyers treating the whole framework as conditions to navigate.

Note where each camp does its arguing. Russian state media treat the bilateral relationship as a subject in itself and comment on it continuously; Western coverage engages the same events mainly through the war in Ukraine and through sanctions policy, seldom as bilateral commentary. Both camps are present across this theater, but they are not arguing on the same terrain.',
  editorial_summary_de = 'Das Verhältnis befindet sich in einem ungefestigten Tauwetter. Arbeitskontakte wurden wieder aufgebaut -- Besuche von Sondergesandten in Moskau, ein wieder aufgenommener militärischer Kanal auf hoher Ebene, wiederholte Telefonate auf Führungsebene -- während Washington Ausnahmegenehmigungen für russisches Öl mehrfach erteilte und zurücknahm, was Einwände europäischer und britischer Partner hervorrief, die die Durchsetzung weiter verschärfen. Die letzten nuklearen Obergrenzen liefen im Februar 2026 mit New START aus; erstmals seit Jahrzehnten sind beide Arsenale unbegrenzt. Die Berichterstattung teilt sich weniger entlang der Linie USA gegen Russland als an der Frage, wie viel Entgegenkommen gegenüber Moskau gerechtfertigt ist.

Aufschlussreich ist, wo die jeweilige Seite ihre Argumente vorbringt. Russische Staatsmedien behandeln das bilaterale Verhältnis als eigenständigen Gegenstand und kommentieren es fortlaufend; westliche Berichterstattung nähert sich denselben Ereignissen vor allem über den Ukrainekrieg und über die Sanktionspolitik, selten als bilateraler Kommentar. Beide Lager sind in diesem Theater präsent, aber sie streiten nicht auf demselben Terrain.',
  updated_at = NOW()
WHERE id = 'us_russia_theater';

-- ---------------------------------------------------------------------------
-- 3. The two thin Western cards: say in the claim why they are thin, so the
--    size reads as a finding rather than as missing data.
-- ---------------------------------------------------------------------------
UPDATE narratives_v2 SET
  claim_en = 'Western mainstream coverage treating the restored contacts -- envoy trips, the resumed high-level military channel, foreign-minister phone calls -- as the ordinary machinery of great-power management: without it there is no route to a settlement, no deconfliction, and no arms-control conversation. This position is held widely but stated rarely: Western outlets overwhelmingly present these contacts as Ukraine-war developments, so the argument for engagement is usually implicit in war reporting rather than made as bilateral commentary. The card is small by construction, not for want of coverage. Vocabulary: channel, deconfliction, constructive, re-establish, working toward, only route.',
  claim_de = 'Westliche Leitmedien behandeln die wiederhergestellten Kontakte -- Reisen von Sondergesandten, der wieder aufgenommene militärische Kanal auf hoher Ebene, Telefonate der Außenminister -- als das gewöhnliche Instrumentarium des Großmächtemanagements: Ohne ihn gibt es keinen Weg zu einer Regelung, keine Deeskalation und kein Gespräch über Rüstungskontrolle. Diese Position wird breit geteilt, aber selten ausgesprochen: Westliche Medien stellen diese Kontakte überwiegend als Entwicklungen des Ukrainekriegs dar, sodass das Argument für Gespräche meist implizit in der Kriegsberichterstattung steckt statt als bilateraler Kommentar formuliert zu werden. Die Karte ist strukturbedingt klein, nicht mangels Berichterstattung. Vokabular: Kanal, Deeskalation, konstruktiv, Wiederaufnahme.',
  updated_at = NOW()
WHERE id = 'us_russia_engagement_necessary';

UPDATE narratives_v2 SET
  claim_en = 'Western mainstream, transatlantic-critical and Ukrainian coverage arguing that summitry and warm bilateral atmospherics -- congratulation calls, G20 invitations, talk of joint investment projects -- grant Moscow the status of an equal partner it has not earned, and that decisions about European security are being taken over Europe''s and Kyiv''s heads. As with the engagement stance, this objection is mostly voiced inside Ukraine-war coverage rather than as commentary on the bilateral relationship, which is why it registers here at a fraction of the volume the Kremlin''s own account of that relationship achieves. Same publisher bloc as the engagement stance, so framing separates them. Vocabulary: legitimise, over their heads, sidelined, without Europe, premature, rehabilitation, fatal mistake.',
  claim_de = 'Westliche Leitmedien, transatlantisch-kritische und ukrainische Berichterstattung argumentieren, Gipfeltreffen und freundliche bilaterale Atmosphäre -- Gratulationsanrufe, G20-Einladungen, Gerede über gemeinsame Investitionsprojekte -- verliehen Moskau einen nicht verdienten Status als gleichwertiger Partner, und Entscheidungen über die europäische Sicherheit fielen über die Köpfe Europas und Kyjiws hinweg. Wie bei der Engagement-Position wird dieser Einwand überwiegend innerhalb der Ukraine-Kriegsberichterstattung erhoben und nicht als Kommentar zum bilateralen Verhältnis -- daher erscheint er hier nur mit einem Bruchteil des Volumens, das die Kreml-Darstellung dieses Verhältnisses erreicht. Gleicher Publisher-Block wie die Engagement-Position, daher trennt das Framing. Vokabular: legitimieren, ins Abseits, verfrüht, Rehabilitierung.',
  updated_at = NOW()
WHERE id = 'us_russia_normalisation_premature';

-- ---------------------------------------------------------------------------
-- 4. The mirror side: name the structural advantage in the Kremlin cards.
-- ---------------------------------------------------------------------------
UPDATE narratives_v2 SET
  claim_en = 'Russian state coverage presenting the restored channel as overdue recognition that Russia cannot be isolated: the previous freeze is over, contacts are being rebuilt on a basis of equality, and Washington must respect Russian interests for cooperation to be mutually beneficial. Because Russian state media treat the bilateral relationship as a standing subject rather than an adjunct of the war, this framing is asserted directly and continuously, giving it far more standalone volume than any Western counter-position achieves. Vocabulary: multipolar, equality, respect our interests, not frozen, mutually beneficial.',
  claim_de = 'Russische staatliche Berichterstattung stellt den wiederhergestellten Kanal als überfällige Anerkennung dar, dass Russland nicht isoliert werden kann: Das frühere Einfrieren sei vorbei, Kontakte würden auf Grundlage der Gleichberechtigung wiederaufgebaut, und Washington müsse russische Interessen respektieren, damit die Zusammenarbeit beiderseits nützlich sei. Da russische Staatsmedien das bilaterale Verhältnis als dauerhaften Gegenstand behandeln und nicht als Anhängsel des Krieges, wird diese Rahmung unmittelbar und fortlaufend behauptet -- mit weit größerem eigenständigem Volumen als jede westliche Gegenposition erreicht. Vokabular: multipolar, Gleichberechtigung, Respekt, gegenseitiger Nutzen.',
  updated_at = NOW()
WHERE id = 'us_russia_washington_realism';

COMMIT;

"""Generate the narratives_v2 migration for us_domestic_theater.

Emits db/migrations/20260720_us_domestic_narratives.sql (atomic + theater cards).

DESIGN, and why it is not the usual pro/con pair
------------------------------------------------
§5's default assumption -- stance correlates with publisher bloc, so publishers
alone disambiguate -- holds when the axis is "West vs adversary". This theater's
axis is intra-American, and the corpus says publisher alone is NOT enough on the
own-goal-shaped atomics. Measured on Epstein: Fox News (66 titles) and MSNBC (96)
both cover it heavily, aimed at opposite targets --

  Fox:   "House Republicans descend on Clintons' hometown for Epstein grilling",
         "Clinton confidant who called Maxwell his 'lover' grilled by Congress",
         "'Squad' Dems join GOP to advance contempt resolutions against Clintons"
  MSNBC: "'They're hiding her': House Dem slams closed-door Bondi testimony",
         "Democrats walk out of Epstein files briefing, calling it a 'fake' hearing"

so the axis that actually separates the corpus is ACCOUNTABILITY ADVANCING vs
OBSTRUCTED, not left vs right. That framing also gives the large neutral bloc
(Reuters 148, CNN 154, BBC 111, Guardian 97, Al Jazeera 89, AP 74, Le Monde 57)
a home instead of leaving ~700 titles homeless, which a Fox-vs-MSNBC axis would.
Those two cards therefore SHARE publishers and are separated by framing_required
+ disjoint keywords -- the §5 own-goal pattern.

THE RIFT-EXPLOITATION CARD (§5), applied theater-wide
-----------------------------------------------------
RT/TASS/CGTN/Press TV are a large, consistent presence (Epstein: RT 46, CGTN 25,
TASS 23, Press TV 10; political violence: CGTN 35, TASS 31, RT 30, China Daily
19). They are NOT on either American side. Their frame is Western elite impunity
and American systemic decay:

  RT:     "UK PM Keir Starmer faces calls to resign over Epstein-linked envoy"
  RT:     "Pandemic simulation, vaccine gatekeeping, and STIs: Bill Gates' Epstein ties"
  TASS:   "EU needs statements about Navalny's poisoning to 'cover up' Epstein affair"
  CGTN:   "High-profile Americans face accountability for Epstein association"

Filing those beside either US camp would produce exactly the false card §5 warns
about. They get their own axis, framing_required=false (publisher suffices).
Note this is the intra-Western case of the caveat: Russia/China are bystanders to
an American dispute, NOT principals -- contrast the SCS build, where China IS a
party and its coverage belongs on the dispute's own axis.

THEATER CARDS (§5.5) -- publisher-disjoint within each sign bucket
  +1  Conservative/administration case      US_RIGHT
  -1  Liberal-democratic alarm              WIRE + US_MAIN + EUROPEAN
  -2  American decline and hypocrisy        ADVERSARY
The negative bucket's two cards are publisher-disjoint (mainstream vs state
media), so their uncapped counts partition cleanly.

Run: python scripts/gen_us_domestic_narratives.py
"""

from pathlib import Path

OUT = (
    Path(__file__).resolve().parent.parent
    / "db"
    / "migrations"
    / "20260720_us_domestic_narratives.sql"
)

# --- publisher blocs -------------------------------------------------------
WIRE = [
    "Reuters",
    "Associated Press",
    "AFP",
    "BBC World",
    "BBC",
    "Al Jazeera",
    "Deutsche Welle",
    "France 24 (EN)",
    "France 24",
    "Euronews",
    "Straits Times",
    "Channel NewsAsia",
    "NDTV",
    "Times of India",
    "Indian Express",
    "Hindustan Times",
    "Globe and Mail",
    "News24",
    "Sky News",
    "WION",
    "Anadolu Agency",
    "Dawn",
    "CBC",
    "ABC News",
    "SMH.com.au",
    "Philippine Daily Inquirer",
    "NHK World",
    "KBS World",
    "Al Arabiya",
    "i24NEWS",
    "Jerusalem Post",
    "Haaretz",
    "Times of Israel",
]
EUROPEAN = [
    "El País",
    "Le Monde",
    "Le Figaro",
    "Der Spiegel",
    "Süddeutsche Zeitung",
    "Frankfurter Allgemeine",
    "Die Zeit",
    "Corriere della Sera",
    "La Repubblica",
    "Tagesschau",
    "Der Standard",
    "Die Presse",
    "Kurier",
    "Handelsblatt",
    "Neue Zürcher Zeitung",
    "Swissinfo",
    "iROZHLAS",
    "ERR News",
    "The Telegraph",
]
US_MAIN = ["CNN", "New York Times", "Washington Post", "NPR", "The Guardian", "MSNBC"]
US_RIGHT = ["Fox News", "New York Post", "Washington Times", "Newsmax"]
BUSINESS = [
    "Financial Times",
    "Bloomberg",
    "Bloomberg.com",
    "Wall Street Journal",
    "The Economist",
    "S&P Global",
    "Nikkei Asia",
    "OilPrice",
    "Reuters",
    "Handelsblatt",
    "Swissinfo",
]
ADVERSARY = [
    "RT",
    "TASS",
    "TASS (EN)",
    "Sputnik",
    "CGTN",
    "Global Times",
    "China Daily",
    "People's Daily",
    "Xinhua",
    "Press TV",
    "Tehran Times",
    "IRNA",
]

MAINSTREAM = WIRE + EUROPEAN + US_MAIN


def sql_arr(items):
    # Postgres cannot infer the element type of a bare ARRAY[]; framing_keywords
    # is legitimately empty on the publisher-disjoint cards, so cast explicitly.
    if not items:
        return "ARRAY[]::text[]"
    inner = ",".join("'" + i.replace("'", "''") + "'" for i in items)
    return f"ARRAY[{inner}]"


ROWS = []


def card(
    nid,
    fn,
    name_en,
    name_de,
    claim_en,
    claim_de,
    stance,
    lab_en,
    lab_de,
    framing,
    framing_required,
    publishers,
    order_,
):
    ROWS.append(
        f"""
INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, framing_keywords, framing_required, publishers, display_order
) VALUES (
    '{nid}', '{fn}',
    '{name_en.replace("'", "''")}',
    '{name_de.replace("'", "''")}',
    '{claim_en.replace("'", "''")}',
    '{claim_de.replace("'", "''")}',
    {stance}, '{lab_en.replace("'", "''")}', '{lab_de.replace("'", "''")}',
    ARRAY['AMERICAS-USA'],
    {sql_arr(framing)},
    {'true' if framing_required else 'false'},
    {sql_arr(publishers)},
    {order_}
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, framing_keywords=EXCLUDED.framing_keywords,
    framing_required=EXCLUDED.framing_required, publishers=EXCLUDED.publishers,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();"""
    )


DECAY_FRAMING = [
    "hypocrisy",
    "double standard",
    "decline",
    "decay",
    "crisis of democracy",
    "so-called democracy",
    "impunity",
    "elite",
    "Heuchelei",
    "Doppelmoral",
    "Niedergang",
    "hipocresía",
    "declive",
]

# ===========================================================================
# 1. Epstein -- own-goal shaped; axis is accountability advancing vs obstructed
# ===========================================================================
card(
    "usdom_epstein_accountability",
    "us_epstein_elite_network",
    "The files are forcing accountability on a protected elite",
    "Die Akten erzwingen Rechenschaft von einer geschützten Elite",
    "Wire, international and US coverage treating the document releases, "
    "depositions and contempt votes as an accountability process that is working: "
    "names are surfacing across both parties and across borders, witnesses are "
    "being compelled to testify, and figures long thought untouchable are being "
    "questioned, charged or forced to resign. Vocabulary: unseal, release, "
    "testify, deposition, subpoena, contempt, grilled, indicted, arrest, resign.",
    "Agentur-, internationale und US-Berichterstattung, die Aktenfreigaben, "
    "Vernehmungen und Missachtungsbeschlüsse als funktionierenden "
    "Rechenschaftsprozess darstellt: Namen tauchen partei- und länderübergreifend "
    "auf, Zeugen werden zur Aussage gezwungen, und lange unantastbar geglaubte "
    "Personen werden befragt, angeklagt oder zum Rücktritt gedrängt.",
    1,
    "Accountability advancing",
    "Rechenschaft schreitet voran",
    [
        "unseal",
        "unsealed",
        "release",
        "released",
        "testify",
        "testifies",
        "testimony",
        "deposition",
        "subpoena",
        "contempt",
        "grilled",
        "indicted",
        "charged",
        "arrest",
        "resign",
        "steps down",
        "probe",
        "investigation",
        "files show",
        "documents",
        "freigegeben",
        "Aussage",
        "Vernehmung",
        "Ermittlung",
        "zurückgetreten",
        "Rücktritt",
        "declassified",
    ],
    True,
    MAINSTREAM + US_RIGHT,
    1,
)
card(
    "usdom_epstein_obstruction",
    "us_epstein_elite_network",
    "Disclosure is being managed, delayed and selectively withheld",
    "Die Offenlegung wird gesteuert, verzögert und selektiv zurückgehalten",
    "Coverage arguing the release process is being controlled to protect the "
    "powerful: files redacted or withheld, testimony taken behind closed doors, "
    "the attorney general accused of shielding names, witnesses pleading the "
    "Fifth, and briefings dismissed as theatre. Vocabulary: hiding, withheld, "
    "redacted, sealed, stonewall, closed-door, refuses, blocked, cover-up.",
    "Berichterstattung, die argumentiert, der Freigabeprozess werde zum Schutz "
    "der Mächtigen gesteuert: geschwärzte oder zurückgehaltene Akten, Aussagen "
    "hinter verschlossenen Türen, eine Justizministerin, der vorgeworfen wird, "
    "Namen zu decken, Zeugen, die die Aussage verweigern, und als Theater "
    "abgetane Unterrichtungen.",
    -1,
    "Disclosure obstructed",
    "Offenlegung blockiert",
    [
        "hiding",
        "hidden",
        "withheld",
        "withholding",
        "redacted",
        "redactions",
        "sealed",
        "stonewall",
        "closed-door",
        "behind closed doors",
        "refuses",
        "refused",
        "blocked",
        "cover-up",
        "coverup",
        "pleads the Fifth",
        "Fifth Amendment",
        "excused",
        "fake hearing",
        "walk out",
        "delay",
        "zurückgehalten",
        "geschwärzt",
        "verweigert",
        "Vertuschung",
        "blockiert",
    ],
    True,
    MAINSTREAM,
    2,
)
card(
    "usdom_epstein_western_impunity",
    "us_epstein_elite_network",
    "A Western elite protecting itself, exposed by its own scandal",
    "Eine westliche Elite, die sich selbst schützt, entlarvt durch den eigenen Skandal",
    "Russian, Chinese and Iranian state coverage using the Epstein files to "
    "indict the Western establishment as a class -- British ministers and "
    "envoys, Scandinavian royals, EU diplomats, philanthropists and financiers -- "
    "and to argue that the moral authority the West claims abroad is not "
    "supported at home. Not aligned with either American party: the target is "
    "Western elite impunity itself, extending to conspiratorial framing.",
    "Russische, chinesische und iranische Staatsmedien nutzen die Epstein-Akten, "
    "um das westliche Establishment als Klasse anzuklagen -- britische Minister "
    "und Gesandte, skandinavische Royals, EU-Diplomaten, Philanthropen und "
    "Finanziers -- und zu argumentieren, die vom Westen im Ausland beanspruchte "
    "moralische Autorität sei im Inneren nicht gedeckt. Keiner US-Partei "
    "zugeordnet: Ziel ist die Straflosigkeit westlicher Eliten selbst.",
    -2,
    "Western elite impunity",
    "Straflosigkeit westlicher Eliten",
    DECAY_FRAMING,
    False,
    ADVERSARY,
    3,
)

# ===========================================================================
# 2. Interior immigration enforcement
# ===========================================================================
card(
    "usdom_ice_enforcement_mandate",
    "us_interior_immigration_enforcement",
    "Enforcement is delivering a mandate voters asked for",
    "Der Vollzug setzt ein von den Wählern gefordertes Mandat um",
    "Coverage presenting interior enforcement as lawful execution of immigration "
    "statute and an electoral mandate: removals of people with criminal records, "
    "funding votes in Congress, court wins expanding executive discretion, and "
    "officers portrayed as targeted by violence. Vocabulary: criminal record, "
    "convicted, funding, mandate, law enforcement, officers assaulted.",
    "Berichterstattung, die den Vollzug im Landesinneren als rechtmäßige "
    "Umsetzung des Einwanderungsrechts und eines Wahlmandats darstellt: "
    "Abschiebungen von Personen mit Vorstrafen, Finanzierungsabstimmungen im "
    "Kongress, Gerichtserfolge und als Gewaltopfer dargestellte Beamte.",
    1,
    "Lawful enforcement",
    "Rechtmäßiger Vollzug",
    [
        "criminal record",
        "convicted",
        "criminal alien",
        "public safety",
        "funding",
        "mandate",
        "law enforcement",
        "assaulted",
        "attack on officers",
        "illegal immigrant",
        "fugitive",
        "vollzogen",
        "Straftäter",
        "Vorstrafen",
    ],
    True,
    WIRE + US_RIGHT,
    1,
)
card(
    "usdom_ice_due_process",
    "us_interior_immigration_enforcement",
    "Enforcement is outrunning due process and harming residents",
    "Der Vollzug überholt rechtsstaatliche Verfahren und schadet Anwohnern",
    "Coverage documenting deaths and illness in detention, arrests without "
    "warrants, detained children and elderly people, long-resident and legally "
    "present people swept up, judges ordering releases, and the chilling effect "
    "on schools, clinics and workplaces. Vocabulary: died in custody, without a "
    "warrant, judge orders release, detained despite, fear, raid on.",
    "Berichterstattung über Todesfälle und Krankheiten in Haft, Festnahmen ohne "
    "Haftbefehl, inhaftierte Kinder und Ältere, langjährig oder legal Ansässige, "
    "die miterfasst werden, Richter, die Freilassungen anordnen, und die "
    "Abschreckungswirkung auf Schulen, Kliniken und Arbeitsplätze.",
    -1,
    "Due-process alarm",
    "Rechtsstaatliche Bedenken",
    [
        "died",
        "death",
        "custody",
        "without a warrant",
        "no warrant",
        "orders release",
        "release of",
        "despite",
        "fear",
        "chilling",
        "citizen",
        "wrongly",
        "mistakenly",
        "children",
        "5-year-old",
        "86",
        "rights",
        "lawyers say",
        "Todesfälle",
        "Gewahrsam",
        "ohne Haftbefehl",
        "Angst",
        "Freilassung",
        "zu Unrecht",
        "muerte",
        "sin orden",
        "miedo",
    ],
    True,
    MAINSTREAM + EUROPEAN,
    2,
)
card(
    "usdom_ice_american_repression",
    "us_interior_immigration_enforcement",
    "A self-described democracy policing its own population",
    "Eine selbsternannte Demokratie, die die eigene Bevölkerung überwacht",
    "Russian, Chinese and Iranian state coverage using interior immigration "
    "raids to argue that American human-rights advocacy abroad is contradicted "
    "by its conduct at home -- masked agents, detention deaths, operations at "
    "schools and stadiums -- and to reject US standing to criticise others.",
    "Russische, chinesische und iranische Staatsmedien nutzen "
    "Einwanderungsrazzien im Landesinneren, um zu argumentieren, dass "
    "amerikanisches Eintreten für Menschenrechte im Ausland dem eigenen "
    "Verhalten im Inland widerspricht, und sprechen den USA das Recht ab, "
    "andere zu kritisieren.",
    -2,
    "American repression",
    "Amerikanische Repression",
    DECAY_FRAMING,
    False,
    ADVERSARY,
    3,
)

# ===========================================================================
# 3. Electoral legitimacy
# ===========================================================================
card(
    "usdom_electoral_integrity_case",
    "us_electoral_legitimacy",
    "Tightening the rules is protecting the integrity of the vote",
    "Strengere Regeln schützen die Integrität der Wahl",
    "Coverage presenting voter-ID requirements, proof-of-citizenship rules, "
    "voter-roll maintenance and limits on mail balloting as ordinary safeguards "
    "against fraud, and redistricting as a lawful power of elected state "
    "legislatures. Vocabulary: integrity, safeguard, proof of citizenship, "
    "voter ID, clean rolls, secure.",
    "Berichterstattung, die Ausweispflichten, Staatsbürgerschaftsnachweise, "
    "die Pflege der Wählerverzeichnisse und Beschränkungen der Briefwahl als "
    "übliche Schutzmaßnahmen gegen Betrug darstellt und den Neuzuschnitt von "
    "Wahlkreisen als rechtmäßige Befugnis gewählter Parlamente.",
    1,
    "Integrity safeguards",
    "Schutz der Wahlintegrität",
    [
        "integrity",
        "safeguard",
        "secure",
        "proof of citizenship",
        "voter ID",
        "clean",
        "fraud",
        "verify",
        "lawful",
        "constitutional",
        "Integrität",
        "Wahlbetrug",
        "Nachweis",
        "rechtmäßig",
    ],
    True,
    WIRE + US_RIGHT,
    1,
)
card(
    "usdom_electoral_franchise_threat",
    "us_electoral_legitimacy",
    "The rules are being rewritten to shape the result in advance",
    "Die Regeln werden umgeschrieben, um das Ergebnis vorab zu formen",
    "Coverage documenting mid-cycle redistricting races between states, the "
    "Voting Rights Act narrowed, mail-ballot restrictions struck down and "
    "reimposed, proof-of-citizenship bills, an FBI raid on a voting-rights "
    "group, and open discussion of how an incumbent might tilt a midterm. "
    "Vocabulary: gerrymander, tilt, crackdown, restrict, purge, strike down, "
    "block, master plan.",
    "Berichterstattung über Neuzuschnitte von Wahlkreisen mitten im Zyklus, die "
    "Einschränkung des Voting Rights Act, gekippte und wieder eingeführte "
    "Briefwahlbeschränkungen, Gesetze zum Staatsbürgerschaftsnachweis, eine "
    "FBI-Razzia bei einer Wahlrechtsorganisation und offene Debatten darüber, "
    "wie ein Amtsinhaber eine Zwischenwahl beeinflussen könnte.",
    -1,
    "Franchise under pressure",
    "Wahlrecht unter Druck",
    [
        "gerrymander",
        "tilt",
        "crackdown",
        "restrict",
        "restriction",
        "purge",
        "strike down",
        "struck down",
        "blocks",
        "blocked",
        "suppress",
        "master plan",
        "raid",
        "meddle",
        "meddling",
        "advantage",
        "splinter",
        "rig",
        "Wahlkreis",
        "Einschränkung",
        "Razzia",
        "manipulieren",
    ],
    True,
    MAINSTREAM + EUROPEAN,
    2,
)
card(
    "usdom_electoral_democracy_facade",
    "us_electoral_legitimacy",
    "A system that lectures others while contesting its own elections",
    "Ein System, das andere belehrt und die eigenen Wahlen bestreitet",
    "Russian, Chinese and Iranian state coverage using redistricting fights, "
    "ballot litigation and fraud claims to argue that American electoral "
    "democracy is a facade, and that US election observation and democracy "
    "promotion abroad lack standing.",
    "Russische, chinesische und iranische Staatsmedien nutzen Streit um "
    "Wahlkreise, Klagen um Stimmzettel und Betrugsvorwürfe, um zu argumentieren, "
    "die amerikanische Wahldemokratie sei eine Fassade und die US-Wahlbeobachtung "
    "im Ausland entbehre der Grundlage.",
    -2,
    "Democracy as facade",
    "Demokratie als Fassade",
    DECAY_FRAMING,
    False,
    ADVERSARY,
    3,
)

# ===========================================================================
# 4. Federal courts and executive power
# ===========================================================================
card(
    "usdom_courts_checks_hold",
    "us_judicial_constraint",
    "The courts are still binding the executive",
    "Die Gerichte binden die Exekutive weiterhin",
    "Coverage of rulings that constrained the administration -- birthright "
    "citizenship upheld, the global tariff order struck down, a Federal Reserve "
    "governor kept in office, mail-ballot orders enjoined -- read as evidence "
    "that judicial review still functions. Vocabulary: rejects, strikes down, "
    "blocks, upholds, denies, rules against, injunction.",
    "Berichterstattung über Urteile, die die Regierung einschränkten -- "
    "Bestätigung des Geburtsortsprinzips, Aufhebung der globalen Zollanordnung, "
    "Verbleib einer Fed-Vorständin im Amt, einstweilige Verfügungen gegen "
    "Briefwahlanordnungen -- gelesen als Beleg, dass richterliche Kontrolle "
    "weiterhin funktioniert.",
    1,
    "Checks holding",
    "Kontrolle greift",
    [
        "rejects",
        "rejected",
        "strikes down",
        "struck down",
        "blocks",
        "blocked",
        "upholds",
        "upheld",
        "denies",
        "denied",
        "rules against",
        "injunction",
        "setback for",
        "loses",
        "quashes",
        "abgewiesen",
        "gekippt",
        "Rückschlag",
        "bestätigt",
        "Verfügung",
    ],
    True,
    MAINSTREAM + WIRE,
    1,
)
card(
    "usdom_courts_deference",
    "us_judicial_constraint",
    "The bench is expanding executive discretion rather than checking it",
    "Die Richterbank erweitert den Ermessensspielraum der Exekutive, statt ihn zu begrenzen",
    "Coverage of the other half of the docket -- removal power upheld, "
    "immigration discretion expanded, emergency-docket orders issued without "
    "full argument, state policies overridden -- and of a court whose "
    "composition and procedure are themselves now contested. Vocabulary: "
    "expands, backs, allows, sides with, clears path, shadow docket, "
    "unprecedented, reshaping.",
    "Berichterstattung über die andere Hälfte der Fälle -- Bestätigung der "
    "Entlassungsbefugnis, erweitertes Ermessen bei der Einwanderung, Beschlüsse "
    "im Eilverfahren ohne vollständige Verhandlung, überstimmte Bundesstaaten -- "
    "und über ein Gericht, dessen Zusammensetzung und Verfahren selbst "
    "umstritten sind.",
    -1,
    "Deference to the executive",
    "Nachgiebigkeit gegenüber der Exekutive",
    [
        "expands",
        "expanded",
        "backs",
        "allows",
        "sides with",
        "clears path",
        "clears the way",
        "shadow docket",
        "unprecedented",
        "reshaping",
        "power",
        "hails",
        "victory for",
        "boosts",
        "lets",
        "erweitert",
        "stärkt",
        "beispiellos",
        "Sieg für",
    ],
    True,
    MAINSTREAM + EUROPEAN,
    2,
)
card(
    "usdom_courts_politicised",
    "us_judicial_constraint",
    "A judiciary treated as an instrument of factional power",
    "Eine Justiz, die als Instrument fraktioneller Macht behandelt wird",
    "Russian, Chinese and Iranian state coverage presenting American courts as "
    "an arena of partisan capture rather than neutral adjudication, and using "
    "that reading to reject US commentary on judicial independence elsewhere.",
    "Russische, chinesische und iranische Staatsmedien stellen amerikanische "
    "Gerichte als Arena parteipolitischer Vereinnahmung statt neutraler "
    "Rechtsprechung dar und weisen damit US-Kommentare zur richterlichen "
    "Unabhängigkeit andernorts zurück.",
    -2,
    "Judiciary politicised",
    "Politisierte Justiz",
    DECAY_FRAMING,
    False,
    ADVERSARY,
    3,
)

# ===========================================================================
# 5. Cabinet turnover and executive loyalty -- publisher-disjoint, no framing
# ===========================================================================
card(
    "usdom_loyalty_prerogative",
    "us_executive_loyalty",
    "A president is entitled to a team that executes his agenda",
    "Ein Präsident hat Anspruch auf ein Team, das seine Agenda umsetzt",
    "Coverage treating dismissals, resignations and replacements across the "
    "cabinet, the FBI and the intelligence agencies as the normal prerogative of "
    "an elected executive removing officials who will not deliver, and as "
    "overdue housecleaning of agencies described as resistant.",
    "Berichterstattung, die Entlassungen, Rücktritte und Neubesetzungen im "
    "Kabinett, beim FBI und bei den Nachrichtendiensten als normales Vorrecht "
    "einer gewählten Exekutive darstellt, Amtsträger zu entfernen, die nicht "
    "liefern, und als überfälligen Hausputz in als widerständig beschriebenen "
    "Behörden.",
    1,
    "Executive prerogative",
    "Vorrecht der Exekutive",
    [],
    False,
    US_RIGHT,
    1,
)
card(
    "usdom_loyalty_hollowing",
    "us_executive_loyalty",
    "Professional institutions are being hollowed out by loyalty tests",
    "Fachbehörden werden durch Loyalitätsprüfungen ausgehöhlt",
    "Coverage of a rolling cycle of dismissals and resignations -- an attorney "
    "general removed, a homeland security secretary out, an intelligence chief "
    "resigning, FBI agents fired over past investigations, inspectors general "
    "and prosecutors displaced -- read as the replacement of professional "
    "judgement with personal loyalty, and as a loss of institutional capacity.",
    "Berichterstattung über eine fortlaufende Kette von Entlassungen und "
    "Rücktritten -- eine abberufene Justizministerin, eine ausgeschiedene "
    "Heimatschutzministerin, eine zurückgetretene Geheimdienstkoordinatorin, "
    "wegen früherer Ermittlungen entlassene FBI-Beamte, verdrängte "
    "Generalinspekteure und Staatsanwälte -- gelesen als Ersetzung fachlichen "
    "Urteils durch persönliche Loyalität.",
    -1,
    "Institutional hollowing",
    "Aushöhlung der Institutionen",
    [
        "fired",
        "fires",
        "firing",
        "ousted",
        "ouster",
        "removed",
        "removal",
        "resign",
        "resigns",
        "resignation",
        "steps down",
        "quit",
        "exit",
        "purge",
        "purges",
        "shakeup",
        "shake-up",
        "next on",
        "forced out",
        "dismissed",
        "sacked",
        "acting",
        "temporary",
        "vacancy",
        "raise questions",
        "concerned",
        "loyalty",
        "loyalist",
        "entlassen",
        "Rücktritt",
        "abberufen",
        "besorgt",
        "Säuberung",
        "destituida",
        "dimite",
        "renuncia",
    ],
    True,
    MAINSTREAM + WIRE + EUROPEAN,
    2,
)
card(
    "usdom_loyalty_court_politics",
    "us_executive_loyalty",
    "Court politics inside a distracted superpower",
    "Hofpolitik in einer abgelenkten Supermacht",
    "Russian, Chinese and Iranian state coverage reading the churn of American "
    "cabinet appointments as palace intrigue and evidence of an administration "
    "consumed by internal rivalry rather than governing -- used to argue that "
    "Washington is an unreliable counterpart.",
    "Russische, chinesische und iranische Staatsmedien deuten den ständigen "
    "Wechsel im amerikanischen Kabinett als Palastintrige und als Beleg für eine "
    "von internen Rivalitäten aufgezehrte Regierung -- genutzt für das Argument, "
    "Washington sei ein unzuverlässiger Partner.",
    -2,
    "Palace intrigue",
    "Palastintrige",
    DECAY_FRAMING,
    False,
    ADVERSARY,
    3,
)

# ===========================================================================
# 6. Federal Reserve independence -- the "con" here is the business press
# ===========================================================================
card(
    "usdom_fed_orderly_succession",
    "us_fed_independence",
    "A normal succession that leaves the institution intact",
    "Eine normale Nachfolge, die die Institution unangetastet lässt",
    "Business and wire coverage treating the chair nomination and Senate "
    "confirmation as an ordinary handover -- a nominee clearing committee, an "
    "incumbent serving out his term, the board continuing to set policy on its "
    "own reading of inflation -- and stressing that the legal architecture of "
    "independence has held. Vocabulary: confirmation, clears, nomination, "
    "hearing, term, transition, independent.",
    "Wirtschafts- und Agenturberichterstattung, die die Nominierung des "
    "Vorsitzes und die Bestätigung durch den Senat als gewöhnliche Übergabe "
    "behandelt -- ein Kandidat, der den Ausschuss passiert, ein Amtsinhaber, der "
    "seine Amtszeit beendet, ein Gremium, das die Politik weiter nach eigener "
    "Einschätzung der Inflation bestimmt.",
    1,
    "Orderly succession",
    "Geordnete Nachfolge",
    [
        "confirmation",
        "confirm",
        "clears",
        "nomination",
        "nominate",
        "hearing",
        "term",
        "transition",
        "independent",
        "independence",
        "stays on",
        "remain",
        "Bestätigung",
        "Nominierung",
        "Amtszeit",
        "unabhängig",
    ],
    True,
    BUSINESS + WIRE,
    1,
)
card(
    "usdom_fed_capture_risk",
    "us_fed_independence",
    "Political pressure is testing the limits of central-bank independence",
    "Politischer Druck testet die Grenzen der Notenbankunabhängigkeit",
    "Coverage of the pressure side of the same story -- an attempt to remove a "
    "sitting governor blocked in court, a criminal referral against the chair "
    "later dropped, public demands that he resign, a chair warning the "
    "institution is under a stress test and that lost credibility is hard to "
    "restore. Vocabulary: fire, remove, pressure, threat, probe, resign, stress "
    "test, credibility, clash.",
    "Berichterstattung über die Druckseite derselben Geschichte -- ein vor "
    "Gericht gestoppter Versuch, eine amtierende Gouverneurin zu entfernen, eine "
    "später fallengelassene Strafanzeige gegen den Vorsitzenden, öffentliche "
    "Rücktrittsforderungen und die Warnung, die Institution stehe unter einem "
    "Stresstest und verlorene Glaubwürdigkeit sei schwer wiederherzustellen.",
    -1,
    "Independence under pressure",
    "Unabhängigkeit unter Druck",
    [
        "fire",
        "fired",
        "firing",
        "remove",
        "removal",
        "oust",
        "pressure",
        "threat",
        "threatens",
        "probe",
        "resign",
        "step down",
        "stress test",
        "credibility",
        "clash",
        "attack",
        "entlassen",
        "Druck",
        "Rücktritt",
        "Glaubwürdigkeit",
        "Stresstest",
        "despido",
        "presión",
    ],
    True,
    BUSINESS + MAINSTREAM + EUROPEAN,
    2,
)
card(
    "usdom_fed_dollar_decline",
    "us_fed_independence",
    "Politicised money and the erosion of the dollar order",
    "Politisiertes Geld und die Erosion der Dollarordnung",
    "Russian, Chinese and Iranian state coverage reading the fight over the "
    "central bank as confirmation that the dollar system is politically managed "
    "and unreliable, and as an argument for reserve diversification and "
    "settlement outside US institutions.",
    "Russische, chinesische und iranische Staatsmedien deuten den Streit um die "
    "Notenbank als Bestätigung, dass das Dollarsystem politisch gesteuert und "
    "unzuverlässig sei, und als Argument für die Diversifizierung von Reserven "
    "und Abwicklung außerhalb US-amerikanischer Institutionen.",
    -2,
    "Dollar order eroding",
    "Erosion der Dollarordnung",
    DECAY_FRAMING,
    False,
    ADVERSARY,
    3,
)

# ===========================================================================
# 7. Political violence
# ===========================================================================
card(
    "usdom_violence_protective_response",
    "us_political_violence",
    "The protective response worked and the perpetrators face the law",
    "Der Personenschutz funktionierte und die Täter stehen vor Gericht",
    "Coverage centred on the security response and the prosecutions: agents "
    "returning fire and evacuating principals, a suspect identified and charged, "
    "a plot against a public event foiled, and officials thanking their details. "
    "Vocabulary: evacuated, whisked, detained, identified, charged, pleads, "
    "indicted, foiled, thanks.",
    "Berichterstattung mit Schwerpunkt auf Sicherheitsreaktion und "
    "Strafverfolgung: Beamte, die das Feuer erwidern und Schutzpersonen "
    "evakuieren, ein identifizierter und angeklagter Verdächtiger, ein "
    "vereitelter Anschlag auf eine öffentliche Veranstaltung und Amtsträger, die "
    "ihren Schutzkommandos danken.",
    1,
    "Protective response",
    "Schutzreaktion",
    [
        "evacuated",
        "whisked",
        "detained",
        "identified",
        "charged",
        "pleads",
        "indicted",
        "convicted",
        "foiled",
        "thanks",
        "arrested",
        "shot dead",
        "suspect",
        "evakuiert",
        "festgenommen",
        "angeklagt",
        "vereitelt",
        "Verdächtiger",
    ],
    True,
    WIRE + US_RIGHT,
    1,
)
card(
    "usdom_violence_climate",
    "us_political_violence",
    "Violence is becoming a recurring feature of political life",
    "Gewalt wird zu einem wiederkehrenden Merkmal des politischen Lebens",
    "Coverage treating the incidents as a pattern rather than isolated events: "
    "repeated attempts against a president, a member of Congress attacked at a "
    "town hall, judges reporting threats and requiring heightened security, "
    "polling showing large numbers disbelieve official accounts, and warnings "
    "about the climate that produces this. Vocabulary: threats, climate, "
    "rhetoric, polarisation, again, pattern, security for judges, conspiracy.",
    "Berichterstattung, die die Vorfälle als Muster statt als Einzelfälle "
    "behandelt: wiederholte Anschläge auf einen Präsidenten, ein Angriff auf ein "
    "Kongressmitglied bei einer Bürgerversammlung, Richter, die Drohungen melden "
    "und verstärkten Schutz benötigen, Umfragen, wonach viele den offiziellen "
    "Darstellungen misstrauen, und Warnungen vor dem Klima, das dies "
    "hervorbringt.",
    -1,
    "Climate of violence",
    "Klima der Gewalt",
    [
        "threats",
        "threat",
        "threatened",
        "climate",
        "rhetoric",
        "polarisation",
        "polarization",
        "attempts",
        "second attempt",
        "pattern",
        "judiciary",
        "judges",
        "conspiracy",
        "staged",
        "fake",
        "hoax",
        "believe",
        "survey",
        "poll",
        "investigates",
        "why so many",
        "tone deaf",
        "divided",
        "warns",
        "complaint",
        "motive",
        "extremism",
        "radicalised",
        "Drohungen",
        "Klima",
        "Rhetorik",
        "Spaltung",
        "warnt",
        "Attentate",
        "amenazas",
        "atentados",
    ],
    True,
    MAINSTREAM + EUROPEAN,
    2,
)
card(
    "usdom_violence_instability",
    "us_political_violence",
    "A superpower unable to secure its own political life",
    "Eine Supermacht, die ihr eigenes politisches Leben nicht sichern kann",
    "Russian, Chinese and Iranian state coverage using shootings and plots "
    "around American political events as evidence of internal disorder, and to "
    "question the stability of a state that presents itself as a model of "
    "governance to others.",
    "Russische, chinesische und iranische Staatsmedien nutzen Schüsse und "
    "Anschlagspläne rund um amerikanische politische Ereignisse als Beleg "
    "innerer Unordnung und stellen die Stabilität eines Staates infrage, der "
    "sich anderen als Vorbild guter Regierungsführung präsentiert.",
    -2,
    "Internal disorder",
    "Innere Unordnung",
    DECAY_FRAMING,
    False,
    ADVERSARY,
    3,
)

# ===========================================================================
# 8. Press freedom and broadcast regulation -- publisher-disjoint
# ===========================================================================
card(
    "usdom_press_accountability",
    "us_press_freedom",
    "Broadcasters are being held to obligations that come with a licence",
    "Rundfunkanstalten werden an Pflichten gemessen, die mit einer Lizenz einhergehen",
    "Coverage framing regulatory action against networks as enforcement of "
    "existing public-interest and equal-time obligations rather than "
    "retaliation, and treating publicly funded broadcasting as a legitimate "
    "subject of political decision about who taxpayers should fund.",
    "Berichterstattung, die regulatorisches Vorgehen gegen Sender als "
    "Durchsetzung bestehender Pflichten zu Gemeinwohl und Gleichbehandlung "
    "darstellt statt als Vergeltung, und öffentlich finanzierten Rundfunk als "
    "legitimen Gegenstand politischer Entscheidung behandelt.",
    1,
    "Regulatory accountability",
    "Regulatorische Rechenschaft",
    [],
    False,
    US_RIGHT,
    1,
)
card(
    "usdom_press_suppression",
    "us_press_freedom",
    "State leverage is being used against critical coverage",
    "Staatliche Hebel werden gegen kritische Berichterstattung eingesetzt",
    "Coverage of licence reviews opened after a broadcast joke, funding for "
    "public media cut and restored by a court on First Amendment grounds, "
    "restricted Pentagon press access reimposed after a loss in court, "
    "defamation suits against news organisations, and press-freedom monitors "
    "warning about the pattern.",
    "Berichterstattung über Lizenzprüfungen nach einem Witz im Programm, "
    "gekürzte und von einem Gericht unter Berufung auf den Ersten "
    "Verfassungszusatz wiederhergestellte Mittel für öffentliche Medien, nach "
    "einer Niederlage vor Gericht erneut eingeschränkten Zugang zum Pentagon, "
    "Verleumdungsklagen gegen Nachrichtenorganisationen und warnende "
    "Beobachter der Pressefreiheit.",
    -1,
    "Pressure on the press",
    "Druck auf die Presse",
    [],
    False,
    MAINSTREAM + WIRE + EUROPEAN,
    2,
)
card(
    "usdom_press_hypocrisy",
    "us_press_freedom",
    "Press-freedom advocacy abroad, licence pressure at home",
    "Eintreten für Pressefreiheit im Ausland, Lizenzdruck im Inland",
    "Russian, Chinese and Iranian state coverage contrasting American criticism "
    "of media restrictions elsewhere with regulatory pressure on its own "
    "broadcasters, used to reject the premise that the US speaks for press "
    "freedom internationally.",
    "Russische, chinesische und iranische Staatsmedien stellen amerikanische "
    "Kritik an Medienbeschränkungen andernorts dem regulatorischen Druck auf "
    "eigene Sender gegenüber, um die Prämisse zurückzuweisen, die USA sprächen "
    "international für die Pressefreiheit.",
    -2,
    "Double standard on press freedom",
    "Doppelmoral bei der Pressefreiheit",
    DECAY_FRAMING,
    False,
    ADVERSARY,
    3,
)

# ===========================================================================
# THEATER CARDS (§5.5) -- publisher-disjoint within each sign bucket
# ===========================================================================
card(
    "usdom_theater_conservative_case",
    "us_domestic_theater",
    "A mandate being executed against institutional resistance",
    "Ein Mandat, das gegen institutionellen Widerstand umgesetzt wird",
    "The administration-aligned reading across the theater: enforcement, "
    "personnel changes, electoral rule-tightening and regulatory action are the "
    "delivery of an electoral mandate against agencies, courts and media "
    "described as resistant to it.",
    "Die regierungsnahe Lesart über das gesamte Feld: Vollzug, "
    "Personalwechsel, strengere Wahlregeln und regulatorisches Vorgehen sind die "
    "Umsetzung eines Wahlmandats gegen Behörden, Gerichte und Medien, die als "
    "widerständig beschrieben werden.",
    1,
    "Mandate delivery",
    "Umsetzung des Mandats",
    [],
    False,
    US_RIGHT,
    1,
)
card(
    "usdom_theater_liberal_alarm",
    "us_domestic_theater",
    "Checks and balances under sustained strain",
    "Gewaltenteilung unter anhaltender Belastung",
    "The mainstream and international reading across the theater: contested "
    "election rules, personnel purges, pressure on the central bank and on "
    "broadcasters, and enforcement outrunning due process are treated as a "
    "connected strain on American institutional checks -- with the courts as the "
    "contested variable.",
    "Die Lesart der Leitmedien und der internationalen Presse über das gesamte "
    "Feld: umstrittene Wahlregeln, Personalsäuberungen, Druck auf die Notenbank "
    "und auf Sender sowie ein Vollzug, der rechtsstaatliche Verfahren überholt, "
    "gelten als zusammenhängende Belastung der institutionellen Kontrolle -- mit "
    "den Gerichten als umstrittener Variable.",
    -1,
    "Institutional strain",
    "Institutionelle Belastung",
    [],
    False,
    MAINSTREAM + WIRE + EUROPEAN + BUSINESS,
    2,
)
card(
    "usdom_theater_decline",
    "us_domestic_theater",
    "American decline and the collapse of its claim to model status",
    "Amerikanischer Niedergang und das Ende des Vorbildanspruchs",
    "The Russian, Chinese and Iranian state reading across the theater: elite "
    "impunity, domestic policing, contested elections, politicised money and "
    "pressure on media are assembled into a single argument that the United "
    "States has no standing to set standards for others. Bystander framing, not "
    "support for any American faction.",
    "Die Lesart russischer, chinesischer und iranischer Staatsmedien über das "
    "gesamte Feld: Straflosigkeit der Eliten, innere Überwachung, umstrittene "
    "Wahlen, politisiertes Geld und Druck auf Medien werden zu einem einzigen "
    "Argument verbunden -- die Vereinigten Staaten könnten für andere keine "
    "Maßstäbe setzen. Eine Außenperspektive, keine Unterstützung einer "
    "amerikanischen Fraktion.",
    -2,
    "No standing to lead",
    "Kein Führungsanspruch",
    DECAY_FRAMING,
    False,
    ADVERSARY,
    3,
)


def main():
    header = """-- us_domestic_theater: atomic + theater narratives (greenfield, 2026-07-20).
-- Generated by scripts/gen_us_domestic_narratives.py -- see that file's
-- docstring for the design rationale and the corpus evidence behind it.
--
-- Summary: the own-goal-shaped atomics (§5) use the three-stance gradient with
-- framing_required=true on the two mainstream-sharing cards; the rest are
-- publisher-disjoint and need no framing filter. Every atomic carries a
-- rift-exploitation card (§5) for the Russian/Chinese/Iranian state bloc, which
-- is a bystander to an American dispute and must not be filed on either
-- American side.
--
-- Reversible: INSERT ... ON CONFLICT DO UPDATE, no DELETE.

BEGIN;
"""
    OUT.write_text(header + "\n".join(ROWS) + "\n\nCOMMIT;\n", encoding="utf-8")
    print(f"OK wrote {len(ROWS)} narratives -> {OUT}")


if __name__ == "__main__":
    main()

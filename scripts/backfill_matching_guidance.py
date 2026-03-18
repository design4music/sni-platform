"""Backfill matching_guidance for ideological narratives."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config

GUIDANCE = {
    # === USA ===
    "us_democracy_vs_authoritarianism": "US officials criticizing authoritarian governments, democracy promotion programs, election monitoring, sanctions on undemocratic regimes, supporting opposition movements, defending press freedom abroad",
    "us_rules_based_order": "US defending international institutions (UN, WTO, ICC), enforcing treaty obligations, multilateral cooperation statements, criticism of rule-breakers, international law citations",
    "us_globalist_order": "International cooperation summits, WHO/WTO/IMF actions, multilateral agreements, UN peacekeeping, global governance reform proposals",
    "us_anti_globalism": "Withdrawal from international agreements, criticism of UN/WHO/WTO, America First rhetoric, rejection of multilateral frameworks, sovereignty over international obligations",
    "us_maga_national_revival": "DOGE cuts, federal agency restructuring, border enforcement, tariff announcements, America First policy, executive orders reversing prior administration policies",
    "us_deep_state_purge": "Federal employee firings, agency restructuring, media criticism by officials, tech platform regulation, government transparency demands, FOIA releases",
    "us_human_rights_enforcement": "State Department human rights reports, sanctions on rights violators, asylum policy, refugee programs, criticism of allies over rights records",
    "us_sanctions_enforce_norms": "New sanctions packages, enforcement actions, sanctions evasion investigations, Treasury designations, asset freezes, secondary sanctions on third parties",
    "us_supply_chain_friendshoring": "Reshoring manufacturing, CHIPS Act implementation, ally trade preferences, reducing China dependence, critical mineral agreements, semiconductor policy",
    "us_climate_global_action": "Paris Agreement actions, emissions targets, clean energy investment, climate finance pledges, climate summits, EPA regulations",
    "us_counter_disinformation": "Foreign influence operations exposed, social media takedowns, election security measures, State Department GEC reports, troll farm indictments",
    "us_nato_collective_defense": "NATO summit statements, Article 5 reaffirmations, troop deployments to Europe, defense spending commitments, joint exercises",
    "us_russia_aggression": "Russian military actions in Ukraine and hybrid warfare against NATO states constitute the greatest threat to Euro-Atlantic security. Events: battlefield reports, election interference, cyberattacks, diplomatic expulsions",
    # === RUSSIA ===
    "ru_multipolar_world": "Russia-China summits, BRICS expansion, SCO meetings, proposals for alternative international institutions, criticism of US unilateral actions",
    "ru_western_hegemony_decline": "BRICS economic growth comparisons, de-dollarization moves, Global South alignment with Russia/China, Western alliance disagreements, US soft power decline",
    "ru_nato_encirclement": "NATO expansion discussions, new NATO bases near Russia, military exercises near Russian borders, missile deployments in Eastern Europe, Finland/Sweden NATO membership",
    "ru_sovereignty_defense": "Russian government rejecting external criticism, expelling NGOs, restricting foreign media, asserting domestic policy independence",
    "ru_sanctions_are_economic_warfare": "Sanctions impact reports, Russian countermeasures, parallel import schemes, sanctions circumvention, humanitarian impact of sanctions",
    "ru_dollar_hegemony_challenge": "Ruble-yuan trade settlements, BRICS payment system proposals, central bank reserve diversification away from dollar, SWIFT alternatives, bilateral currency swap deals",
    "ru_economic_self_reliance": "Import substitution programs, domestic manufacturing announcements, technology localization, agricultural self-sufficiency, reducing Western dependencies",
    "ru_special_military_operation": "Russian military advances in Ukraine, battlefield reports, troop deployments, mobilization, military operations in Donbas/Zaporizhzhia/Kherson",
    "ru_protect_russian_speakers": "Russia citing protection of Russian minorities abroad, Baltic language policy disputes, citizenship rights in former Soviet states, Russian cultural institutions abroad",
    "ru_military_strength_security": "New weapons systems, military parades, defense spending, nuclear deterrence statements, hypersonic missile tests, naval deployments",
    "ru_energy_as_leverage": "Gas pipeline politics, oil export redirections, energy supply negotiations, LNG competition, OPEC+ coordination, energy cutoffs or threats",
    "ru_information_sovereignty": "Blocking Western social media, restricting foreign news outlets, sovereign internet laws, VPN crackdowns, RT/Sputnik operations",
    "ru_traditional_values": "Anti-LGBT legislation, religious conservative policies, family values rhetoric, criticism of Western social liberalism, cultural sovereignty statements",
    "ru_western_disinformation": "Russian officials accusing Western media of lies, exposing alleged Western propaganda, media restrictions justified by information warfare",
    "ru_western_values_imposition": "Russian criticism of Western cultural exports, rejection of Western governance models, sovereignty over social policy, conditionality in Western aid",
    "ru_anti_colonial_alignment": "Russia-Africa summits, Wagner/Africa Corps deployments, grain/fertilizer diplomacy, arms sales to Global South, supporting anti-Western governments",
    # === CHINA ===
    "cn_multipolar_world": "China-Russia coordination at UN, BRICS statements, criticism of US unilateralism, proposals for reformed international order, Global South summits",
    "cn_us_hegemony_threat": "Chinese officials criticizing US foreign policy, military encirclement, economic coercion, tech restrictions as hegemonic behavior",
    "cn_us_containment_resisted": "China responding to chip bans, AUKUS criticism, Quad criticism, military posturing in response to US actions, tit-for-tat sanctions",
    "cn_peaceful_rise": "Chinese trade deals, infrastructure investment, diplomatic visits emphasizing cooperation, win-win rhetoric, BRI projects, development partnerships",
    "cn_belt_and_road": "BRI project announcements, port/rail/road construction, Chinese overseas investment, development finance, infrastructure deals in Asia/Africa/Latin America",
    "cn_sovereignty_non_interference": "China rejecting criticism of domestic policies, defending non-interference principle at UN, opposing sanctions on sovereign states",
    "cn_global_governance_reform": "China proposing UN/IMF/World Bank reform, demanding greater representation for developing nations, alternative institution building",
    "cn_global_security_initiative": "Chinese peace proposals, mediation offers, GSI/GDI promotion, non-alliance security frameworks, criticism of NATO-style alliances",
    "cn_global_south_development": "Chinese development aid, infrastructure investment in Africa/Asia, South-South cooperation, alternative to Western development models",
    "cn_sanctions_illegitimate": "China criticizing Xinjiang/HK/tech sanctions, retaliatory sanctions, legal challenges to sanctions, rallying opposition to unilateral measures",
    "cn_western_values_rejected": "Chinese officials defending CPC governance model, rejecting Western democracy promotion, whole-process democracy rhetoric",
    "cn_social_stability": "Social order maintenance, protest suppression, internet censorship, anti-corruption campaigns, CPC discipline, social credit system",
    "cn_technology_self_reliance": "Domestic chip development, tech self-sufficiency programs, Made in China 2025, reducing foreign tech dependence, Huawei breakthroughs",
    "cn_narrative_counter_offensive": "Xinhua/CGTN expansion, wolf warrior diplomacy, social media campaigns, countering negative coverage, telling China story",
    "cn_climate_differentiated_responsibility": "China citing per-capita emissions, demanding developed country climate finance, coal plant defense, developing country solidarity on climate",
    "cn_digital_sovereignty": "Great Firewall enforcement, data localization laws, regulating foreign tech companies, cyber sovereignty at UN, internet governance",
    "cn_taiwan_reunification": "PLA exercises near Taiwan, One China statements, diplomatic pressure on Taiwan allies, military threats, reunification rhetoric",
    # === EU ===
    "eu_russia_existential_threat": "EU defense spending increases, Eastern European security concerns, Russian hybrid warfare incidents, energy security measures, defense cooperation",
    "eu_sanctions_tool": "New EU sanctions packages, enforcement mechanisms, sanctions evasion crackdowns, listing individuals/entities, sectoral restrictions",
    "eu_us_reliability_crisis": "Transatlantic disagreements, European strategic autonomy debates, Trump-era friction, NATO burden disputes, trade conflicts with US",
    "eu_ukraine_accession": "EU-Ukraine accession talks, chapter openings, reform benchmarks, EU enlargement debates, integration support packages",
    "eu_rule_of_law_internal": "Article 7 proceedings, rule of law conditionality, judicial independence disputes with Hungary/Poland, frozen funds",
    "eu_climate_diplomacy": "EU Green Deal international dimension, CBAM implementation, COP negotiations, climate finance pledges, emissions trading",
    "eu_counter_disinformation": "EU DSA enforcement, foreign interference investigations, election protection, platform regulation, Russian disinformation exposure",
    "eu_global_gateway": "Global Gateway project launches, EU development investment vs BRI, infrastructure deals in Africa/Asia, values-based partnerships",
    "eu_human_rights_universal": "EU human rights dialogues, sanctions on rights violators, democracy support programs, EU Special Representative actions",
    "eu_migration_solidarity": "Asylum reform debates, relocation schemes, Frontex operations, Mediterranean rescue, burden-sharing disputes between member states",
    "eu_multilateral_rules_order": "EU defending WTO, UN system, ICC, multilateral treaties, rules-based order rhetoric at summits",
    # === UK ===
    "uk_global_britain": "Post-Brexit trade deals, AUKUS activities, CPTPP membership, Commonwealth summits, independent foreign policy moves, bilateral partnerships outside EU",
    # === INDIA ===
    "in_strategic_autonomy": "India signing deals with BOTH Western and non-Western powers, buying Russian weapons while doing Quad exercises, refusing to condemn Russia, India-US trade deal alongside Russia oil purchases, multi-directional diplomacy",
    "in_global_south_voice": "India hosting G20, speaking for developing nations, demanding UN reform, climate justice arguments, representing Global South at summits",
    "in_hindu_civilizational": "Hindu temple inaugurations by PM, Ayodhya, yoga diplomacy, Hindutva policies, CAA/NRC, cultural nationalism rhetoric",
    "in_pakistan_terrorism": "India accusing Pakistan of cross-border terrorism, Pulwama-style incidents, ISI allegations, FATF proceedings against Pakistan",
    # === IRAN ===
    "ir_sovereignty_defense": "Iran resisting external pressure, rejecting ultimatums, defending nuclear program as sovereign right, assassination response",
    "ir_sanctions_economic_warfare": "Sanctions humanitarian impact, medicine shortages, Iran demanding sanctions relief, economic hardship reports",
    "ir_regional_power": "Iran diplomatic engagement in region, mediating, hosting summits, asserting regional influence, Gulf security proposals",
    "ir_nuclear_sovereignty": "Nuclear talks, enrichment levels, IAEA inspections, JCPOA negotiations, uranium stockpile reports, centrifuge deployment",
    "ir_islamic_governance": "Iran governance model defense, elections, Guardian Council, supreme leader authority, Islamic democracy rhetoric",
    "ir_resistance_axis": "Hezbollah/Hamas/Houthi actions coordinated with Iran, proxy warfare, resistance front statements, Iran supplying allies",
    # === PALESTINE ===
    "ps_occupation_apartheid": "Settlement expansion, house demolitions, checkpoint restrictions, apartheid legal findings, occupation reports, settler violence",
    "ps_self_determination": "Palestinian statehood recognition, UN votes, two-state solution discussions, sovereignty demands",
    "ps_resistance_legitimate": "Palestinian armed resistance framed as anti-occupation, guerrilla actions, popular resistance, UN Charter right to resist",
    "ps_international_law_weapon": "ICJ rulings, ICC warrants, UN General Assembly votes, international law citations against Israel, legal proceedings",
    # === TURKEY ===
    "tr_neo_ottoman_sphere": "Turkey regional diplomatic initiatives, cultural outreach, Ottoman heritage references, bridging East-West rhetoric",
    "tr_muslim_world_leadership": "Turkey defending Palestinians, OIC leadership, mosque construction abroad, Muslim solidarity statements",
    "tr_domestic_sovereignty": "Turkey rejecting Western criticism of governance, press freedom disputes, judiciary independence debates",
    # === KOREA/JAPAN ===
    "kr_north_korea_existential": "North Korean missile tests, nuclear threats, provocations, military drills near border, defector stories",
    "kr_us_alliance": "US-Korea joint exercises, USFK activities, alliance reaffirmation, defense cooperation agreements",
    "jp_china_threat": "Chinese military activity near Japan, Senkaku incidents, Taiwan contingency planning, Japan defense budget increases",
    "nk_us_hostile_policy": "North Korea blaming US for peninsula tensions, sanctions as aggression, US military exercises as provocation",
    # === TAIWAN ===
    "tw_de_facto_sovereignty": "Taiwan government actions, elections, international participation, diplomatic recognition, military defense preparations",
    "tw_democracy_model": "Taiwan democratic achievements, press freedom rankings, peaceful power transfers, contrast with mainland governance",
    # === PAKISTAN ===
    "pk_china_iron_brotherhood": "CPEC projects, China-Pakistan military cooperation, diplomatic support at UN, joint exercises, infrastructure development",
    "pk_india_existential_threat": "India military buildup, nuclear posture concerns, BJP rhetoric about Pakistan, Kashmir militarization",
    "pk_kashmir_self_determination": "Kashmir protests, UN resolution citations, human rights reports from Kashmir, Pakistan raising Kashmir at international forums",
    "pk_terrorism_victim": "Pakistan military operations against militants, casualty reports, counter-terrorism spending, TTP attacks",
    # === EUROPE misc ===
    "alpine_neutrality_tested": "Switzerland/Austria sanctions debates, neutrality principle discussions, security cooperation without NATO membership",
    "baltic_russia_existential": "Russian military activity near Baltic states, NATO reinforcement, cyber attacks, hybrid warfare incidents",
    "baltic_russian_minority_security": "Language policy disputes, citizenship rights, Russian media influence, integration programs in Latvia/Estonia",
    "by_russia_equal_partnership": "Belarus-Russia Union State activities, joint military exercises, economic integration, Lukashenko-Putin meetings",
    "benelux_eu_deepening": "EU deepening proposals from Netherlands/Belgium, federalism debates, institutional reform advocacy",
    "de_fiscal_discipline": "German debt brake debates, EU fiscal rules, Stability Pact enforcement, austerity vs investment discussions",
    "nordic_climate_model": "Nordic green energy achievements, carbon neutrality targets, electric vehicle adoption, climate policy exports",
    "south_europe_fiscal_solidarity": "North-South EU fiscal disputes, eurobond debates, recovery fund conditions, austerity criticism from southern states",
    "visegrad_sovereignty_over_brussels": "Hungary/Poland vs EU Commission, sovereignty rhetoric, rejecting EU directives, national competence arguments",
    "ua_european_path": "Ukraine EU accession progress, reform benchmarks, European integration rhetoric, NATO membership discussions",
    # === LATIN AMERICA ===
    "br_amazon_sovereignty": "Brazil defending Amazon policy against international pressure, deforestation debates, sovereignty over natural resources",
    "br_global_south_leader": "Brazil at G20/BRICS, UN reform proposals, South-South cooperation, Lula global diplomacy, mediating conflicts",
    "br_multi_alignment": "Brazil maintaining ties with US, China, Russia simultaneously, refusing to pick sides, BRICS + Western engagement",
    "ve_bolivarian_revolution": "Venezuelan government social programs, anti-imperialism rhetoric, nationalization, Maduro defending socialist model",
    "ve_sanctions_collective_punishment": "Sanctions impact on Venezuelan economy, medicine shortages, oil sector collapse, humanitarian arguments against sanctions",
    "cu_embargo_longest_siege": "US embargo effects on Cuba, UN General Assembly votes against embargo, humanitarian impact, travel restrictions",
    "cu_revolutionary_sovereignty": "Cuba defending its political system, healthcare/education achievements, sovereignty against US pressure",
    "cu_solidarity_internationalism": "Cuban medical brigades abroad, disaster response teams, educational missions, South-South cooperation",
    "mx_non_intervention_doctrine": "Mexico refusing to take sides in international disputes, rejecting sanctions, defending non-interference principle",
    "andean_indigenous_rights": "Indigenous rights movements in Peru/Bolivia/Ecuador, territorial claims, political representation, Pachamama rights",
    "andean_coca_sovereignty": "Coca policy debates, US drug war criticism, traditional coca use defense, eradication program opposition",
    "andean_lithium_copper_sovereignty": "Lithium/copper nationalization debates, resource sovereignty laws, foreign mining company disputes",
    "caribbean_climate_survival": "Hurricane damage, sea level rise impacts, climate vulnerability reports, loss and damage demands",
    "caribbean_debt_trap": "Debt restructuring needs, middle-income trap, development aid exclusion, vulnerability index proposals",
    # === AFRICA ===
    "ng_west_africa_anchor": "Nigeria in ECOWAS, peacekeeping contributions, regional diplomatic leadership, economic influence",
    "sahel_expel_france": "French troop withdrawals, anti-France protests, military junta rejecting French presence, expelling ambassadors",
    "sahel_russia_partnership": "Wagner/Africa Corps in Sahel, Russian military advisors, arms deals, Russia-Africa summit, anti-Western partnership",
    "za_brics_global_south": "South Africa at BRICS, G20 positions, Global South advocacy, non-alignment statements",
    "za_anti_apartheid_solidarity": "South Africa ICJ case against Israel, Palestinian solidarity, anti-apartheid legacy in foreign policy",
    "za_non_alignment_pragmatic": "South Africa refusing to sanction Russia, maintaining diverse diplomatic ties, non-aligned rhetoric",
    "west_africa_democratic_resilience": "Elections in Ghana/Senegal/Ivory Coast, democratic transitions, resisting coup contagion",
    "west_africa_youth_digital_economy": "Tech startup growth, fintech expansion, digital inclusion programs, youth employment initiatives",
    "southern_africa_land_reform": "Land redistribution programs, colonial land legacy debates, farm seizures, compensation disputes",
    "central_africa_resource_governance": "Oil/timber governance, transparency initiatives, resource revenue disputes, environmental impact",
    "drc_rwandan_aggression": "M23 advances, Rwanda involvement allegations, mineral smuggling, UN reports on Rwanda-M23 links",
    "et_nile_sovereignty": "GERD filling, Egypt-Ethiopia water disputes, Nile negotiations, downstream impact concerns",
    "et_unity_sovereignty": "Tigray peace process, ethnic tensions, federal vs regional power disputes, national unity rhetoric",
    "horn_red_sea_chokepoint": "Houthi shipping attacks, Red Sea security, Bab el-Mandeb disruptions, naval deployments, Somali piracy",
    # === PACIFIC ===
    "melanesia_climate_existential": "Sea level rise threatening Pacific islands, climate displacement, coral bleaching, extreme weather events",
    "melanesia_great_power_pawn": "US/China/Australia competing for Pacific influence, security pacts, island sovereignty assertions",
    "micronesia_nuclear_legacy": "Nuclear testing legacy, health impacts, compensation claims, cleanup demands, Marshallese displacement",
    "polynesia_ocean_identity": "Ocean governance, illegal fishing, marine conservation, cultural identity tied to ocean",
    "nz_independent_values_foreign_policy": "New Zealand independent foreign policy positions, Five Eyes tension, human rights stances",
    "nz_pacific_climate_champion": "NZ climate leadership in Pacific, aid programs, climate finance, Pacific Islands Forum",
    "png_great_power_balancing": "PNG leveraging US/China/Australia competition, negotiating development deals, sovereignty assertions",
    "png_resource_sovereignty": "Mining governance, LNG revenues, foreign extraction disputes, resource nationalism",
    # === CENTRAL/SOUTH ASIA ===
    "mn_third_neighbor": "Mongolia engaging Japan/EU/US as counterbalance to Russia and China, third neighbor diplomacy, sovereignty maintenance",
    "af_islamic_emirate": "Taliban governance announcements, sharia implementation, women rights restrictions, diplomatic recognition bids",
    "af_recognition_sanctions": "Afghanistan sanctions impact, frozen reserves, humanitarian crisis, recognition debates, aid delivery obstacles",
    "caucasus_connectivity_crossroads": "Middle Corridor projects, Georgia/Azerbaijan transit role, East-West trade routes, infrastructure investment",
    # === KURDISTAN ===
    "kurd_self_determination": "Kurdish political movements, autonomy demands, cultural rights, cross-border Kurdish solidarity",
    "kurd_rojava_democratic_model": "Rojava governance, democratic confederalism, women participation, self-administration in northeast Syria",
    "kurd_turkish_oppression": "Turkish military operations against Kurds, cross-border strikes, HDP persecution, cultural repression",
    # === NATO ===
    "nato_collective_defense": "NATO summit decisions, Article 5 discussions, deterrence posture, troop deployments, defense spending pledges",
}


def main():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()

    updated = 0
    for nid, guidance in GUIDANCE.items():
        cur.execute(
            "UPDATE strategic_narratives SET matching_guidance = %s WHERE id = %s",
            (guidance, nid),
        )
        updated += cur.rowcount

    conn.commit()
    print("Updated %d narratives with matching_guidance" % updated)

    # Check coverage
    cur.execute(
        "SELECT COUNT(*) FROM strategic_narratives "
        "WHERE is_active = true AND tier = 'ideological' AND matching_guidance IS NULL"
    )
    missing = cur.fetchone()[0]
    print("Ideological narratives still missing guidance: %d" % missing)

    if missing > 0:
        cur.execute(
            "SELECT id FROM strategic_narratives "
            "WHERE is_active = true AND tier = 'ideological' AND matching_guidance IS NULL ORDER BY id"
        )
        for row in cur.fetchall():
            print("  %s" % row[0])

    conn.close()


if __name__ == "__main__":
    main()

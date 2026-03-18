"""Seed aligned_with and opposes for narrative clustering."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config

# Each entry: narrative_id -> (aligned_with[], opposes[])
# Aligned = same worldview from different actors, or reinforcing claims
# Opposes = directly competing claims about the same issue

CLUSTERS = {
    # ── Multipolar world vs Western order ──────────────────────────
    "ru_multipolar_world": (
        [
            "cn_multipolar_world",
            "in_strategic_autonomy",
            "br_multi_alignment",
            "za_non_alignment_pragmatic",
            "gulf_multi_alignment",
        ],
        [
            "us_rules_based_order",
            "us_democracy_vs_authoritarianism",
            "eu_multilateral_rules_order",
        ],
    ),
    "cn_multipolar_world": (
        [
            "ru_multipolar_world",
            "in_strategic_autonomy",
            "br_multi_alignment",
            "za_non_alignment_pragmatic",
        ],
        ["us_rules_based_order", "us_democracy_vs_authoritarianism"],
    ),
    "ru_western_hegemony_decline": (
        ["cn_us_hegemony_threat", "ru_multipolar_world", "cn_multipolar_world"],
        ["us_rules_based_order", "us_globalist_order"],
    ),
    "cn_us_hegemony_threat": (
        ["ru_western_hegemony_decline", "ru_multipolar_world", "cn_multipolar_world"],
        ["us_rules_based_order", "us_democracy_vs_authoritarianism"],
    ),
    "us_rules_based_order": (
        [
            "eu_multilateral_rules_order",
            "us_democracy_vs_authoritarianism",
            "us_globalist_order",
        ],
        ["ru_multipolar_world", "cn_multipolar_world", "ru_western_hegemony_decline"],
    ),
    "us_democracy_vs_authoritarianism": (
        ["eu_human_rights_universal", "us_rules_based_order", "tw_democracy_model"],
        [
            "ru_western_values_imposition",
            "cn_western_values_rejected",
            "ir_islamic_governance",
        ],
    ),
    "eu_multilateral_rules_order": (
        ["us_rules_based_order", "us_globalist_order"],
        ["ru_multipolar_world", "cn_multipolar_world", "us_anti_globalism"],
    ),
    "us_globalist_order": (
        ["eu_multilateral_rules_order", "us_rules_based_order"],
        [
            "us_anti_globalism",
            "us_maga_national_revival",
            "ru_western_hegemony_decline",
        ],
    ),
    "us_anti_globalism": (
        ["us_maga_national_revival", "visegrad_sovereignty_over_brussels"],
        [
            "us_globalist_order",
            "eu_multilateral_rules_order",
            "us_climate_global_action",
        ],
    ),
    "us_maga_national_revival": (
        ["us_anti_globalism", "us_deep_state_purge", "us_tariff_economic_nationalism"],
        ["us_globalist_order", "us_rules_based_order"],
    ),
    # ── Multi-alignment / strategic autonomy ──────────────────────
    "in_strategic_autonomy": (
        [
            "br_multi_alignment",
            "za_non_alignment_pragmatic",
            "gulf_multi_alignment",
            "mn_third_neighbor",
        ],
        ["us_indo_pacific_alliances"],
    ),
    "br_multi_alignment": (
        ["in_strategic_autonomy", "za_non_alignment_pragmatic", "gulf_multi_alignment"],
        [],
    ),
    "za_non_alignment_pragmatic": (
        ["in_strategic_autonomy", "br_multi_alignment", "gulf_multi_alignment"],
        [],
    ),
    "gulf_multi_alignment": (
        ["in_strategic_autonomy", "br_multi_alignment", "za_non_alignment_pragmatic"],
        [],
    ),
    # ── Russia-Ukraine war ────────────────────────────────────────
    "ru_special_military_operation": (
        ["ru_nato_encirclement", "ru_protect_russian_speakers"],
        [
            "ua_russia_unprovoked_aggression",
            "ua_sovereignty_defense",
            "us_russia_aggression",
        ],
    ),
    "ru_nato_encirclement": (
        ["ru_special_military_operation", "ru_sovereignty_defense"],
        ["nato_collective_defense", "us_nato_collective_defense", "nordic_nato_turn"],
    ),
    "ua_russia_unprovoked_aggression": (
        [
            "ua_sovereignty_defense",
            "us_russia_aggression",
            "eu_russia_existential_threat",
        ],
        ["ru_special_military_operation", "ru_protect_russian_speakers"],
    ),
    "ua_sovereignty_defense": (
        ["ua_russia_unprovoked_aggression", "ua_weapons_decisive", "ua_european_path"],
        ["ru_special_military_operation"],
    ),
    "us_russia_aggression": (
        [
            "eu_russia_existential_threat",
            "ua_russia_unprovoked_aggression",
            "nato_collective_defense",
        ],
        ["ru_special_military_operation", "ru_nato_encirclement"],
    ),
    "eu_russia_existential_threat": (
        [
            "us_russia_aggression",
            "baltic_russia_existential",
            "nato_collective_defense",
        ],
        ["ru_nato_encirclement", "visegrad_russia_engagement"],
    ),
    "baltic_russia_existential": (
        ["eu_russia_existential_threat", "nato_collective_defense", "nordic_nato_turn"],
        ["ru_nato_encirclement", "ru_protect_russian_speakers"],
    ),
    # ── Sanctions ─────────────────────────────────────────────────
    "us_sanctions_enforce_norms": (
        ["eu_sanctions_tool"],
        [
            "ru_sanctions_are_economic_warfare",
            "cn_sanctions_illegitimate",
            "ir_sanctions_economic_warfare",
        ],
    ),
    "eu_sanctions_tool": (
        ["us_sanctions_enforce_norms"],
        ["ru_sanctions_are_economic_warfare", "cn_sanctions_illegitimate"],
    ),
    "ru_sanctions_are_economic_warfare": (
        [
            "cn_sanctions_illegitimate",
            "ir_sanctions_economic_warfare",
            "ve_sanctions_collective_punishment",
            "cu_embargo_longest_siege",
        ],
        ["us_sanctions_enforce_norms", "eu_sanctions_tool"],
    ),
    "cn_sanctions_illegitimate": (
        ["ru_sanctions_are_economic_warfare", "ir_sanctions_economic_warfare"],
        ["us_sanctions_enforce_norms", "eu_sanctions_tool"],
    ),
    "ir_sanctions_economic_warfare": (
        [
            "ru_sanctions_are_economic_warfare",
            "cn_sanctions_illegitimate",
            "ve_sanctions_collective_punishment",
        ],
        ["us_sanctions_enforce_norms", "us_iran_containment"],
    ),
    "ve_sanctions_collective_punishment": (
        [
            "cu_embargo_longest_siege",
            "ru_sanctions_are_economic_warfare",
            "ir_sanctions_economic_warfare",
        ],
        ["us_sanctions_enforce_norms", "us_monroe_doctrine_revival"],
    ),
    "cu_embargo_longest_siege": (
        ["ve_sanctions_collective_punishment", "ru_sanctions_are_economic_warfare"],
        ["us_sanctions_enforce_norms", "us_monroe_doctrine_revival"],
    ),
    # ── China-US rivalry ──────────────────────────────────────────
    "cn_us_containment_resisted": (
        [
            "cn_us_hegemony_threat",
            "cn_sanctions_illegitimate",
            "cn_technology_self_reliance",
        ],
        [
            "us_china_systemic_rival",
            "us_tech_decoupling_china",
            "us_indo_pacific_alliances",
        ],
    ),
    "us_china_systemic_rival": (
        [
            "us_tech_decoupling_china",
            "us_indo_pacific_alliances",
            "au_aukus_deterrence",
        ],
        ["cn_us_containment_resisted", "cn_peaceful_rise"],
    ),
    "cn_peaceful_rise": (
        ["cn_belt_and_road", "cn_global_south_development"],
        ["us_china_systemic_rival", "jp_china_threat", "tw_china_military_threat"],
    ),
    "cn_taiwan_reunification": (
        ["cn_sovereignty_non_interference"],
        ["tw_de_facto_sovereignty", "tw_democracy_model", "us_indo_pacific_alliances"],
    ),
    "tw_de_facto_sovereignty": (
        ["tw_democracy_model", "tw_semiconductor_leverage"],
        ["cn_taiwan_reunification"],
    ),
    # ── Iran ──────────────────────────────────────────────────────
    "ir_sovereignty_defense": (
        ["ir_nuclear_sovereignty", "ir_regional_power"],
        ["us_iran_containment", "us_iran_regime_change", "il_iran_existential_threat"],
    ),
    "ir_nuclear_sovereignty": (
        ["ir_sovereignty_defense"],
        ["us_iran_containment", "il_iran_existential_threat"],
    ),
    "us_iran_containment": (
        [
            "us_iran_regime_change",
            "il_iran_existential_threat",
            "gulf_iran_containment",
        ],
        ["ir_sovereignty_defense", "ir_nuclear_sovereignty", "ir_resistance_axis"],
    ),
    "us_iran_regime_change": (
        ["us_iran_containment", "il_iran_existential_threat"],
        ["ir_sovereignty_defense", "ir_islamic_governance"],
    ),
    "ir_resistance_axis": (
        ["ir_regional_power", "ir_sovereignty_defense"],
        ["us_iran_containment", "il_counterterrorism_operations"],
    ),
    # ── Palestine-Israel ──────────────────────────────────────────
    "ps_occupation_apartheid": (
        [
            "ps_self_determination",
            "ps_resistance_legitimate",
            "ps_international_law_weapon",
            "za_anti_apartheid_solidarity",
        ],
        [
            "il_right_to_self_defense",
            "il_settlement_sovereignty",
            "il_counterterrorism_operations",
        ],
    ),
    "ps_self_determination": (
        ["ps_occupation_apartheid", "ps_international_law_weapon"],
        ["il_settlement_sovereignty"],
    ),
    "il_right_to_self_defense": (
        ["il_counterterrorism_operations", "il_western_alliance"],
        ["ps_resistance_legitimate", "ir_resistance_axis"],
    ),
    "il_settlement_sovereignty": (
        ["il_right_to_self_defense"],
        [
            "ps_occupation_apartheid",
            "ps_self_determination",
            "ps_international_law_weapon",
        ],
    ),
    # ── Values / governance models ────────────────────────────────
    "ru_western_values_imposition": (
        [
            "cn_western_values_rejected",
            "ru_traditional_values",
            "ir_islamic_governance",
        ],
        ["us_democracy_vs_authoritarianism", "eu_human_rights_universal"],
    ),
    "cn_western_values_rejected": (
        ["ru_western_values_imposition", "cn_sovereignty_non_interference"],
        [
            "us_democracy_vs_authoritarianism",
            "eu_human_rights_universal",
            "tw_democracy_model",
        ],
    ),
    "ru_traditional_values": (
        ["ru_western_values_imposition", "visegrad_traditional_values"],
        ["eu_human_rights_universal"],
    ),
    # ── Disinformation ────────────────────────────────────────────
    "us_counter_disinformation": (
        ["eu_counter_disinformation"],
        [
            "ru_western_disinformation",
            "cn_narrative_counter_offensive",
            "ru_information_sovereignty",
        ],
    ),
    "eu_counter_disinformation": (
        ["us_counter_disinformation"],
        ["ru_western_disinformation", "cn_narrative_counter_offensive"],
    ),
    "ru_western_disinformation": (
        ["cn_narrative_counter_offensive", "ru_information_sovereignty"],
        ["us_counter_disinformation", "eu_counter_disinformation"],
    ),
    # ── De-dollarization ──────────────────────────────────────────
    "ru_dollar_hegemony_challenge": (
        ["cn_de_dollarization"],
        ["us_sanctions_enforce_norms"],
    ),
    "cn_de_dollarization": (
        ["ru_dollar_hegemony_challenge"],
        ["us_sanctions_enforce_norms"],
    ),
    # ── Global South ──────────────────────────────────────────────
    "br_global_south_leader": (
        [
            "in_global_south_voice",
            "za_brics_global_south",
            "cn_global_south_development",
        ],
        [],
    ),
    "in_global_south_voice": (
        ["br_global_south_leader", "za_brics_global_south"],
        [],
    ),
    "za_brics_global_south": (
        [
            "br_global_south_leader",
            "in_global_south_voice",
            "cn_global_south_development",
        ],
        [],
    ),
    # ── Sahel / France-Africa ─────────────────────────────────────
    "sahel_expel_france": (
        ["sahel_russia_partnership", "ru_anti_colonial_alignment"],
        ["fr_africa_influence"],
    ),
    "sahel_russia_partnership": (
        ["sahel_expel_france", "ru_anti_colonial_alignment"],
        ["fr_africa_influence"],
    ),
    "fr_africa_influence": (
        [],
        ["sahel_expel_france", "sahel_russia_partnership"],
    ),
    # ── NATO ──────────────────────────────────────────────────────
    "nato_collective_defense": (
        ["us_nato_collective_defense", "baltic_russia_existential", "nordic_nato_turn"],
        ["ru_nato_encirclement"],
    ),
    "us_nato_collective_defense": (
        ["nato_collective_defense", "eu_russia_existential_threat"],
        ["ru_nato_encirclement", "nato_burden_sharing"],
    ),
    # ── EU strategic autonomy vs US reliability ───────────────────
    "eu_us_reliability_crisis": (
        ["fr_strategic_autonomy", "eu_rearmament"],
        ["us_nato_collective_defense"],
    ),
    "eu_rearmament": (
        ["eu_us_reliability_crisis", "de_zeitenwende"],
        [],
    ),
    # ── Sovereignty vs Brussels ───────────────────────────────────
    "visegrad_sovereignty_over_brussels": (
        ["us_anti_globalism", "visegrad_traditional_values"],
        ["benelux_eu_deepening", "eu_rule_of_law_internal"],
    ),
    "eu_rule_of_law_internal": (
        ["benelux_eu_deepening"],
        ["visegrad_sovereignty_over_brussels"],
    ),
    # ── Pakistan-India ────────────────────────────────────────────
    "pk_india_existential_threat": (
        ["pk_kashmir_self_determination", "pk_nuclear_deterrent"],
        ["in_pakistan_terrorism", "in_china_border_threat"],
    ),
    "in_pakistan_terrorism": (
        [],
        ["pk_terrorism_victim", "pk_india_existential_threat"],
    ),
    "pk_terrorism_victim": (
        [],
        ["in_pakistan_terrorism"],
    ),
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

    # Verify all referenced IDs exist
    cur.execute("SELECT id FROM strategic_narratives WHERE is_active = true")
    valid = {r[0] for r in cur.fetchall()}

    updated = 0
    errors = 0
    for nid, (aligned, opposes) in CLUSTERS.items():
        if nid not in valid:
            print("WARN: %s not found" % nid)
            errors += 1
            continue
        bad = [x for x in aligned + opposes if x not in valid]
        if bad:
            print("WARN: %s references missing: %s" % (nid, bad))
            errors += 1

        cur.execute(
            "UPDATE strategic_narratives SET aligned_with = %s, opposes = %s WHERE id = %s",
            [aligned or None, opposes or None, nid],
        )
        updated += cur.rowcount

    conn.commit()
    print("Updated %d narratives (%d warnings)" % (updated, errors))
    conn.close()


if __name__ == "__main__":
    main()

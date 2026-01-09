"""Populate llm_summary_* focus lines in track_configs table"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "v3" / "taxonomy_tools"))
from common import get_db_connection

# Centroid-level focus lines (by track_config type)
CENTROID_FOCUS_LINES = {
    "strategic_default": "Emphasize concrete actors, locations, policy decisions, and regional power dynamics; avoid abstract system-wide generalizations unless explicitly stated by involved parties.",
    "geo-default": "Emphasize concrete actors, locations, policy decisions, and regional power dynamics; avoid abstract system-wide generalizations unless explicitly stated by involved parties.",
    "sys-climate": "Emphasize environmental impacts, climate-related risks, mitigation or adaptation measures, and institutional responses; avoid speculative long-term projections.",
    "sys-diplomacy": "Emphasize negotiation processes, formal positions, mediation efforts, agreements, refusals, and changes in diplomatic posture or alignment.",
    "sys_energy": "Emphasize production, supply chains, infrastructure, pricing mechanisms, substitution paths, and geopolitical constraints; avoid market sentiment or trader psychology framing.",
    "sys-finance": "Emphasize monetary policy, capital flows, sanctions, reserves, debt, and financial institutions; avoid investor sentiment or speculative narratives.",
    "sys-health": "Emphasize public health measures, institutional capacity, outbreak dynamics, policy responses, and international coordination; avoid anecdotal or societal commentary.",
    "sys-humanitarian": "Emphasize population impacts, displacement, aid delivery, access constraints, and institutional response capacity; avoid moral framing or advocacy language.",
    "sys-media": "Emphasize information dissemination mechanisms, platform behavior, censorship or labeling actions, and narrative amplification; do not assess truth or credibility of claims.",
    "sys_military": "Emphasize force posture, capability development, doctrine, procurement, deployments, and readiness; avoid battlefield dramatization or tactical storytelling.",
    "sys_technology": "Emphasize technological capabilities, standards, regulation, industrial policy, and strategic dependencies; avoid product-level or consumer framing.",
    "sys-trade": "Emphasize trade policy, tariffs, export controls, logistics, supply-chain restructuring, and institutional trade disputes; avoid business performance commentary.",
}

# Track-level focus lines (only for GEO/strategic_default config)
GEO_TRACK_FOCUS_LINES = {
    "geo_politics": "Focus on governance decisions, political authority, inter-state relations, and alliance behavior; avoid internal public opinion unless institutionally expressed.",
    "geo_security": "Focus on military operations, security incidents, force posture, deterrence signals, and formal security commitments.",
    "geo_economy": "Focus on macroeconomic policy, sanctions, fiscal measures, industrial strategy, and cross-border economic leverage; avoid market sentiment framing.",
    "geo_energy": "Focus on energy production, transit, infrastructure, pricing mechanisms, and energy-related leverage; avoid speculative resource valuation.",
    "geo_humanitarian": "Focus on civilian impact, displacement, aid access, and institutional response capacity; avoid emotive or moralized language.",
    "geo_information": "Focus on state or organized information actions, messaging strategies, platform measures, and narrative dissemination; do not assess factual accuracy.",
}


def populate_focus_lines():
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            # Get all track configs
            cur.execute("SELECT id, name FROM track_configs")
            configs = cur.fetchall()

        print("Populating summary focus lines...")
        print("=" * 60)

        for config_id, config_name in configs:
            centroid_focus = CENTROID_FOCUS_LINES.get(config_name)
            track_focus_json = None

            if config_name in ("strategic_default", "geo-default"):
                # GEO configs get track-specific focus lines
                track_focus_json = json.dumps(GEO_TRACK_FOCUS_LINES)

            if centroid_focus:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE track_configs
                        SET llm_summary_centroid_focus = %s,
                            llm_summary_track_focus = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """,
                        (centroid_focus, track_focus_json, config_id),
                    )
                conn.commit()

                track_info = (
                    f"+ {len(GEO_TRACK_FOCUS_LINES)} track focus lines"
                    if track_focus_json
                    else "(no track focus)"
                )
                print(f"OK: {config_name:20s} {track_info}")
            else:
                print(f"SKIP: {config_name:20s} (no focus line defined)")

        print()
        print("=" * 60)
        print("Verification:")

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT name,
                       CASE WHEN llm_summary_centroid_focus IS NOT NULL THEN 'YES' ELSE 'NO' END as has_centroid,
                       CASE WHEN llm_summary_track_focus IS NOT NULL THEN 'YES' ELSE 'NO' END as has_track
                FROM track_configs
                ORDER BY name
            """
            )

            for name, has_centroid, has_track in cur.fetchall():
                print(f"  {name:20s} | Centroid: {has_centroid} | Track: {has_track}")

        print()
        print("SUCCESS: Focus lines populated")

    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    populate_focus_lines()

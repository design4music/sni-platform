"""
Migration: Add dynamic track configuration system to v3

Features:
- track_configs table for storing track lists and prompts
- Link centroids to track configs (optional, defaults to strategic)
- Enables per-centroid track customization
"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def run_migration():
    """Create track_configs table and insert default configurations"""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            print("Creating track_configs table...")

            # Create track_configs table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS track_configs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    tracks TEXT[] NOT NULL,
                    llm_prompt TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """
            )

            print("Adding track_config_id column to centroids_v3...")

            # Add track_config_id column to centroids_v3
            cur.execute(
                """
                ALTER TABLE centroids_v3
                ADD COLUMN IF NOT EXISTS track_config_id UUID REFERENCES track_configs(id);
            """
            )

            # Create index for performance
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_centroids_v3_track_config
                ON centroids_v3(track_config_id);
            """
            )

            print("Inserting default strategic track config...")

            # Insert default strategic config (current 10-track system)
            cur.execute(
                """
                INSERT INTO track_configs (name, description, tracks, llm_prompt, is_default)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING;
            """,
                (
                    "strategic_default",
                    "Default strategic intelligence tracks for all centroids",
                    [
                        "alliances_partnerships",
                        "armed_conflict",
                        "capabilities_readiness",
                        "coercion_pressure",
                        "diplomacy_negotiations",
                        "economic_competition",
                        "governance_internal",
                        "information_influence",
                        "intelligence_espionage",
                        "strategic_positioning",
                    ],
                    """You are analyzing news titles for strategic intelligence. Classify the main strategic track of this news title.

Choose ONLY from the following tracks:
- alliances_partnerships: NATO expansion, AUKUS, security pacts, coalition building
- armed_conflict: Military operations, combat, casualties, warfare
- capabilities_readiness: Defense budgets, military exercises, force modernization, weapons development
- coercion_pressure: Sanctions, embargoes, blockades, economic pressure, cyber attacks
- diplomacy_negotiations: Summits, treaties, peace talks, diplomatic missions, agreements
- economic_competition: Trade wars, tech rivalry, supply chain competition, market access disputes
- governance_internal: Elections, protests, regime stability, corruption, internal reforms
- information_influence: Propaganda, disinformation, soft power, cultural influence, narrative battles
- intelligence_espionage: Surveillance, leaks, spy operations, counterintelligence, data theft
- strategic_positioning: Military bases, territorial claims, infrastructure projects, strategic access

Context: {centroid_label} | {primary_theater} | {month}

Return ONLY the track name, nothing else.""",
                    True,
                ),
            )

            print("Inserting tech-focused track config...")

            # Insert tech-focused config (for SYS-TECH)
            cur.execute(
                """
                INSERT INTO track_configs (name, description, tracks, llm_prompt, is_default)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING;
            """,
                (
                    "tech_focused",
                    "Technology and innovation-specific tracks for SYS-TECH centroid",
                    [
                        "ai_ml_development",
                        "quantum_computing",
                        "semiconductors_hardware",
                        "software_platforms",
                        "cybersecurity",
                        "tech_regulation",
                        "business_investment",
                        "research_innovation",
                        "talent_education",
                        "standards_governance",
                    ],
                    """You are analyzing technology news. Classify the main theme of this news title.

Choose ONLY from the following tracks:
- ai_ml_development: AI research, machine learning advances, generative AI, LLM development, AGI
- quantum_computing: Quantum computers, quantum communication, quantum algorithms, quantum advantage
- semiconductors_hardware: Chip manufacturing, processors, hardware components, fabrication, foundries
- software_platforms: Operating systems, cloud platforms, software ecosystems, applications, SaaS
- cybersecurity: Hacking, data breaches, security vulnerabilities, defense tools, cyber warfare
- tech_regulation: Tech policy, antitrust, data privacy laws, content moderation, platform regulation
- business_investment: Funding rounds, M&A, valuations, market competition, IPOs, tech stocks
- research_innovation: Scientific breakthroughs, patents, academic research, R&D initiatives
- talent_education: Tech talent wars, STEM education, brain drain, workforce development, skills gap
- standards_governance: Tech standards, industry consortia, international tech agreements, interoperability

Context: {centroid_label} | Technology Sector | {month}

Return ONLY the track name, nothing else.""",
                    False,
                ),
            )

            print("Inserting environment-focused track config...")

            # Insert environment config (for SYS-CLIMATE / SYS-ENVIRONMENT)
            cur.execute(
                """
                INSERT INTO track_configs (name, description, tracks, llm_prompt, is_default)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING;
            """,
                (
                    "environment_focused",
                    "Climate and environmental issue tracks for SYS-ENVIRONMENT centroid",
                    [
                        "climate_policy",
                        "emissions_targets",
                        "renewable_energy",
                        "fossil_fuels",
                        "climate_impacts",
                        "environmental_disasters",
                        "conservation_biodiversity",
                        "climate_finance",
                        "adaptation_resilience",
                        "climate_diplomacy",
                    ],
                    """You are analyzing environmental and climate news. Classify the main theme of this news title.

Choose ONLY from the following tracks:
- climate_policy: Climate laws, regulations, national policies, carbon pricing, green new deals
- emissions_targets: Net-zero pledges, emission reduction goals, carbon budgets, Paris Agreement targets
- renewable_energy: Solar, wind, hydro, geothermal, clean energy development, energy storage
- fossil_fuels: Oil, gas, coal, phase-out debates, energy transition conflicts, stranded assets
- climate_impacts: Extreme weather, droughts, floods, temperature records, ecosystem changes, sea level rise
- environmental_disasters: Wildfires, hurricanes, floods, ecological catastrophes, natural disasters
- conservation_biodiversity: Protected areas, species preservation, deforestation, habitat loss, wildlife
- climate_finance: Green bonds, climate funds, fossil fuel divestment, carbon markets, climate aid
- adaptation_resilience: Climate adaptation measures, infrastructure hardening, disaster preparedness
- climate_diplomacy: COP summits, Paris Agreement, international climate negotiations, climate justice

Context: {centroid_label} | Environment/Climate | {month}

Return ONLY the track name, nothing else.""",
                    False,
                ),
            )

            print("Inserting limited strategic track config...")

            # Insert limited strategic config (for quiet countries like Mongolia)
            cur.execute(
                """
                INSERT INTO track_configs (name, description, tracks, llm_prompt, is_default)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING;
            """,
                (
                    "limited_strategic",
                    "Reduced track set for countries with limited international strategic activity",
                    [
                        "diplomacy_negotiations",
                        "economic_competition",
                        "governance_internal",
                        "strategic_positioning",
                    ],
                    """You are analyzing news for a country with limited international strategic activity. Classify the main theme.

Choose ONLY from the following tracks:
- diplomacy_negotiations: Diplomatic visits, bilateral agreements, international cooperation, foreign relations
- economic_competition: Trade relations, economic development, market access, investments, business deals
- governance_internal: Domestic politics, elections, governance reforms, internal stability, policy changes
- strategic_positioning: Regional positioning, infrastructure projects, alignment choices, geopolitical stance

Context: {centroid_label} | {primary_theater} | {month}

Return ONLY the track name, nothing else.""",
                    False,
                ),
            )

            conn.commit()
            print("\n[SUCCESS] Migration completed successfully!")
            print("\nCreated track configs:")
            print("  1. strategic_default (10 tracks) - DEFAULT for all centroids")
            print("  2. tech_focused (10 tracks) - For SYS-TECH")
            print("  3. environment_focused (10 tracks) - For SYS-ENVIRONMENT")
            print("  4. limited_strategic (4 tracks) - For quiet countries")
            print("\nNext steps:")
            print("  - Link centroids to configs: UPDATE centroids_v3 SET track_config_id = ...")
            print("  - Update Phase 3 to use dynamic track configs")

    except Exception as e:
        conn.rollback()
        print(f"\n[FAILED] Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()

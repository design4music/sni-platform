#!/usr/bin/env python3
"""
Analyze Event Family processing results
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


from sqlalchemy import text

from core.database import get_db_session


def analyze_event_families():
    """Analyze Event Family creation and merging patterns"""

    with get_db_session() as session:
        print("=== EVENT FAMILY ANALYSIS ===\n")

        # Recent Event Families
        print("Recent Event Families (last 15):")
        print("-" * 80)

        recent_efs = session.execute(
            text(
                """
            SELECT id, title, key_actors, event_type, primary_theater, ef_key, status, created_at,
                   (SELECT COUNT(*) FROM titles WHERE event_family_id = ef.id) as title_count
            FROM event_families ef
            ORDER BY created_at DESC
            LIMIT 15
        """
            )
        ).fetchall()

        for ef in recent_efs:
            actors_str = ", ".join(ef.key_actors[:3]) + (
                "..." if len(ef.key_actors) > 3 else ""
            )
            print(f"[{ef.status.upper()}] {ef.title[:60]}")
            print(f"  Actors: {actors_str}")
            print(f"  Type: {ef.event_type} | Theater: {ef.primary_theater}")
            print(f"  EF Key: {ef.ef_key} | Titles: {ef.title_count}")
            print(f"  Created: {ef.created_at}")
            print()

        # Merging analysis
        print("\n=== MERGING ANALYSIS ===")

        merged_efs = session.execute(
            text(
                """
            SELECT id, title, merged_into, merge_rationale, created_at
            FROM event_families 
            WHERE status = 'merged'
            ORDER BY created_at DESC
        """
            )
        ).fetchall()

        if merged_efs:
            print(f"Found {len(merged_efs)} merged Event Families:")
            for ef in merged_efs:
                print(f"* {ef.title[:50]}... -> {ef.merged_into}")
                print(f"  Rationale: {ef.merge_rationale}")
                print()
        else:
            print("No merged Event Families found.")

        # EF Key collision analysis
        print("\n=== EF KEY ANALYSIS ===")

        ef_key_analysis = session.execute(
            text(
                """
            SELECT ef_key, COUNT(*) as count, 
                   STRING_AGG(title, ' | ') as titles
            FROM event_families 
            WHERE ef_key IS NOT NULL
            GROUP BY ef_key
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """
            )
        ).fetchall()

        if ef_key_analysis:
            print("EF Key collisions (potential merges):")
            for row in ef_key_analysis:
                print(f"Key {row.ef_key}: {row.count} EFs")
                print(f"  Titles: {row.titles}")
                print()
        else:
            print("No EF key collisions found - all keys are unique.")

        # Processing efficiency
        print("\n=== PROCESSING EFFICIENCY ===")

        stats = session.execute(
            text(
                """
            SELECT 
                COUNT(*) as total_strategic_titles,
                COUNT(CASE WHEN event_family_id IS NOT NULL THEN 1 END) as assigned_titles,
                COUNT(CASE WHEN event_family_id IS NULL THEN 1 END) as unassigned_titles
            FROM titles 
            WHERE gate_keep = true
        """
            )
        ).fetchone()

        efficiency = (
            (stats.assigned_titles / stats.total_strategic_titles) * 100
            if stats.total_strategic_titles > 0
            else 0
        )

        print(f"Total strategic titles: {stats.total_strategic_titles:,}")
        print(f"Assigned to EFs: {stats.assigned_titles:,}")
        print(f"Still unassigned: {stats.unassigned_titles:,}")
        print(f"Processing efficiency: {efficiency:.1f}%")

        # Theater distribution analysis
        print("\n=== THEATER DISTRIBUTION ===")

        theater_analysis = session.execute(
            text(
                """
            SELECT primary_theater, 
                   COUNT(*) as ef_count,
                   SUM((SELECT COUNT(*) FROM titles WHERE event_family_id = ef.id)) as total_titles
            FROM event_families ef
            WHERE status = 'active' AND primary_theater IS NOT NULL
            GROUP BY primary_theater
            ORDER BY ef_count DESC
        """
            )
        ).fetchall()

        for theater in theater_analysis:
            print(
                f"{theater.primary_theater}: {theater.ef_count} EFs, {theater.total_titles} titles"
            )


if __name__ == "__main__":
    analyze_event_families()

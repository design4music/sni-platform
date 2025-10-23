#!/usr/bin/env python3
"""
Clean up old data for lighter testing corpus
Keeps only last 7 days of titles, resets processing state
"""

from sqlalchemy import text

from core.database import get_db_session

with get_db_session() as session:
    # Count before cleanup
    total_titles = session.execute(text("SELECT COUNT(*) FROM titles")).scalar()
    total_efs = session.execute(text("SELECT COUNT(*) FROM event_families")).scalar()
    total_fns = session.execute(text("SELECT COUNT(*) FROM framed_narratives")).scalar()

    print(f"Before cleanup:")
    print(f"  Titles: {total_titles}")
    print(f"  Event Families: {total_efs}")
    print(f"  Framed Narratives: {total_fns}")

    # 1. Reset all titles to pending state (must be first due to foreign keys)
    session.execute(
        text(
            """
            UPDATE titles
            SET event_family_id = NULL,
                gate_keep = FALSE,
                entities = NULL
        """
        )
    )
    print("\n[1/5] Reset all titles to pending state")

    # 2. Delete framed narratives
    session.execute(text("DELETE FROM framed_narratives"))
    print("[2/5] Deleted all framed narratives")

    # 3. Delete event families (now safe, no references)
    session.execute(text("DELETE FROM event_families"))
    print("[3/5] Deleted all event families")

    # 4. Delete titles older than 7 days
    deleted = session.execute(
        text("DELETE FROM titles WHERE ingested_at < NOW() - INTERVAL '7 days'")
    )
    print(f"[4/5] Deleted titles older than 7 days: {deleted.rowcount}")

    # 5. Count after cleanup
    remaining = session.execute(text("SELECT COUNT(*) FROM titles")).scalar()
    print(f"[5/5] Remaining titles: {remaining}")

    session.commit()
    print("\nCleanup complete!")

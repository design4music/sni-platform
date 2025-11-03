#!/usr/bin/env python3
"""
Reset Database - Clear all EF records and title assignments
"""

from sqlalchemy import text

from core.database import get_db_session


def reset_database():
    """Clear all Event Family records and reset title assignments"""

    with get_db_session() as session:
        # First reset title assignments (clear foreign key references)
        session.execute(
            text(
                """
            UPDATE titles 
            SET event_family_id = NULL,
                ef_assignment_confidence = NULL,
                ef_assignment_reason = NULL,
                ef_assignment_at = NULL
            WHERE gate_keep = true
        """
            )
        )
        print("Reset title EF assignments")

        # Clear framed narratives
        session.execute(text("DELETE FROM framed_narratives"))
        print("Cleared framed_narratives table")

        # Clear event families
        session.execute(text("DELETE FROM event_families"))
        print("Cleared event_families table")

        session.commit()
        print("Database reset completed successfully")


if __name__ == "__main__":
    reset_database()

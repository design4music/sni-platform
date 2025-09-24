#!/usr/bin/env python3
"""Quick check for pending titles count"""

from core.database import get_db_session
from sqlalchemy import text

with get_db_session() as session:
    result = session.execute(text("SELECT COUNT(*) FROM titles WHERE processing_status = 'pending'"))
    pending_count = result.scalar()
    print(f"Pending titles: {pending_count}")

    # Also check strategic titles ready for EF generation
    result = session.execute(text("SELECT COUNT(*) FROM titles WHERE gate_keep = true AND event_family_id IS NULL"))
    unassigned_strategic = result.scalar()
    print(f"Strategic titles ready for EF generation: {unassigned_strategic}")
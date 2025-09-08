"""
CLUST-2 Database Operations
Handles bucket and bucket_members table operations
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy import text
from uuid import uuid4
import json

from core.database import get_db_session
from apps.clust2.bucket_manager import BucketCandidate


class BucketDB:
    """Database operations for CLUST-2 buckets"""
    
    def insert_bucket(self, bucket: BucketCandidate) -> str:
        """
        Insert a new bucket into the database.
        
        Args:
            bucket: BucketCandidate to insert
            
        Returns:
            UUID of the inserted bucket
        """
        bucket_uuid = str(uuid4())
        
        with get_db_session() as session:
            # Insert bucket record
            session.execute(text("""
                INSERT INTO buckets (
                    id, bucket_id, date_window_start, date_window_end, 
                    top_actors, mechanism_hint, members_count, members_checksum
                ) VALUES (
                    :id, :bucket_id, :start_time, :end_time, 
                    :actors, :mechanism, :count, :checksum
                )
            """), {
                'id': bucket_uuid,
                'bucket_id': bucket.bucket_id,
                'start_time': bucket.time_window_start,
                'end_time': bucket.time_window_end,
                'actors': json.dumps(bucket.actor_set),  # Convert to JSONB
                'mechanism': None,  # Will be determined later by GEN-1
                'count': bucket.members_count,
                'checksum': self._compute_checksum(bucket.title_ids)
            })
            
            # Insert bucket members
            for title_id in bucket.title_ids:
                session.execute(text("""
                    INSERT INTO bucket_members (bucket_id, title_id)
                    VALUES (:bucket_id, :title_id)
                """), {
                    'bucket_id': bucket_uuid,
                    'title_id': title_id
                })
            
            session.commit()
        
        return bucket_uuid
    
    def bucket_exists(self, bucket_id: str) -> bool:
        """
        Check if a bucket already exists.
        
        Args:
            bucket_id: Deterministic bucket ID (e.g., "B-2025-09-07-CN-US")
            
        Returns:
            True if bucket exists, False otherwise
        """
        with get_db_session() as session:
            result = session.execute(text("""
                SELECT 1 FROM buckets WHERE bucket_id = :bucket_id LIMIT 1
            """), {'bucket_id': bucket_id})
            
            return result.fetchone() is not None
    
    def get_bucket_members(self, bucket_uuid: str) -> List[str]:
        """
        Get all title IDs for a bucket.
        
        Args:
            bucket_uuid: UUID of the bucket
            
        Returns:
            List of title UUID strings
        """
        with get_db_session() as session:
            result = session.execute(text("""
                SELECT title_id FROM bucket_members 
                WHERE bucket_id = :bucket_id
                ORDER BY added_at
            """), {'bucket_id': bucket_uuid})
            
            return [row.title_id for row in result]
    
    def update_bucket_members(self, bucket_uuid: str, title_ids: List[str]) -> int:
        """
        Update bucket members (replace existing).
        
        Args:
            bucket_uuid: UUID of the bucket
            title_ids: New list of title IDs
            
        Returns:
            Number of members added
        """
        with get_db_session() as session:
            # Remove existing members
            session.execute(text("""
                DELETE FROM bucket_members WHERE bucket_id = :bucket_id
            """), {'bucket_id': bucket_uuid})
            
            # Add new members
            for title_id in title_ids:
                session.execute(text("""
                    INSERT INTO bucket_members (bucket_id, title_id)
                    VALUES (:bucket_id, :title_id)
                """), {
                    'bucket_id': bucket_uuid,
                    'title_id': title_id
                })
            
            # Update bucket metadata
            session.execute(text("""
                UPDATE buckets SET 
                    members_count = :count,
                    members_checksum = :checksum
                WHERE id = :bucket_id
            """), {
                'bucket_id': bucket_uuid,
                'count': len(title_ids),
                'checksum': self._compute_checksum(title_ids)
            })
            
            session.commit()
        
        return len(title_ids)
    
    def get_recent_buckets(self, hours_back: int = 72) -> List[Dict[str, Any]]:
        """
        Get recent buckets from the database.
        
        Args:
            hours_back: How many hours back to look
            
        Returns:
            List of bucket dictionaries with metadata
        """
        with get_db_session() as session:
            result = session.execute(text("""
                SELECT 
                    id, bucket_id, date_window_start, date_window_end,
                    top_actors, mechanism_hint, members_count, created_at
                FROM buckets 
                WHERE created_at >= NOW() - MAKE_INTERVAL(hours => :hours)
                ORDER BY created_at DESC
            """), {'hours': hours_back})
            
            return [dict(row._mapping) for row in result]
    
    def insert_buckets_batch(self, buckets: List[BucketCandidate]) -> List[str]:
        """
        Insert multiple buckets in a single transaction.
        
        Args:
            buckets: List of BucketCandidate objects
            
        Returns:
            List of inserted bucket UUIDs
        """
        if not buckets:
            return []
        
        inserted_uuids = []
        
        with get_db_session() as session:
            for bucket in buckets:
                # Skip if bucket already exists
                if self.bucket_exists(bucket.bucket_id):
                    continue
                
                bucket_uuid = str(uuid4())
                inserted_uuids.append(bucket_uuid)
                
                # Insert bucket
                session.execute(text("""
                    INSERT INTO buckets (
                        id, bucket_id, date_window_start, date_window_end, 
                        top_actors, mechanism_hint, members_count, members_checksum
                    ) VALUES (
                        :id, :bucket_id, :start_time, :end_time, 
                        :actors, :mechanism, :count, :checksum
                    )
                """), {
                    'id': bucket_uuid,
                    'bucket_id': bucket.bucket_id,
                    'start_time': bucket.time_window_start,
                    'end_time': bucket.time_window_end,
                    'actors': json.dumps(bucket.actor_set),
                    'mechanism': None,
                    'count': bucket.members_count,
                    'checksum': self._compute_checksum(bucket.title_ids)
                })
                
                # Insert bucket members
                for title_id in bucket.title_ids:
                    session.execute(text("""
                        INSERT INTO bucket_members (bucket_id, title_id)
                        VALUES (:bucket_id, :title_id)
                    """), {
                        'bucket_id': bucket_uuid,
                        'title_id': title_id
                    })
            
            session.commit()
        
        return inserted_uuids
    
    def _compute_checksum(self, title_ids: List[str]) -> str:
        """
        Compute checksum for bucket members for change detection.
        
        Args:
            title_ids: List of title UUID strings
            
        Returns:
            MD5 checksum string
        """
        import hashlib
        
        # Sort for deterministic checksum
        sorted_ids = sorted(title_ids)
        content = "|".join(sorted_ids)
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()


def get_strategic_titles_for_bucketing(hours_back: int = 72) -> List[Dict[str, Any]]:
    """
    Query strategic titles suitable for CLUST-2 bucketing.
    
    Args:
        hours_back: Hours to look back for recent titles
        
    Returns:
        List of title dictionaries with required fields
    """
    with get_db_session() as session:
        result = session.execute(text("""
            SELECT 
                id, title_norm, title_display, pubdate_utc,
                gate_actor_hit, gate_keep, processing_status
            FROM titles 
            WHERE gate_keep = true 
              AND pubdate_utc >= NOW() - MAKE_INTERVAL(hours => :hours)
              AND pubdate_utc IS NOT NULL
            ORDER BY pubdate_utc DESC
        """), {'hours': hours_back})
        
        titles = []
        for row in result:
            title_dict = dict(row._mapping)
            # Convert UUID to string for JSON serialization
            title_dict['id'] = str(title_dict['id'])
            titles.append(title_dict)
        
        return titles


if __name__ == "__main__":
    # Basic validation test
    print("CLUST-2 Database Operations - Validation Test")
    print("=" * 48)
    
    try:
        # Test database connection
        db = BucketDB()
        print("[PASS] BucketDB initialized")
        
        # Test strategic titles query
        titles = get_strategic_titles_for_bucketing(hours_back=24)
        print(f"[PASS] Strategic titles query: {len(titles)} titles found")
        
        # Test recent buckets query  
        buckets = db.get_recent_buckets(hours_back=24)
        print(f"[PASS] Recent buckets query: {len(buckets)} buckets found")
        
        print("\nDatabase operations module ready")
        print("Use with bucket candidates for full CLUST-2 workflow")
        
    except Exception as e:
        print(f"[FAIL] Database validation error: {e}")
        import traceback
        traceback.print_exc()
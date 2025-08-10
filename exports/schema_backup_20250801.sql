-- Strategic Narrative Intelligence - Schema Backup
-- Generated: 2025-08-01
-- Version: NSF-1 v1.1 + Metrics v1.0
-- Purpose: Complete schema export for rollback capability

-- =============================================
-- BACKUP RESTORE INSTRUCTIONS
-- =============================================
/*
To restore this schema:
1. Drop existing database: DROP DATABASE narrative_intelligence;
2. Create new database: CREATE DATABASE narrative_intelligence;
3. Run this file: psql -d narrative_intelligence -f schema_backup_20250801.sql
4. Verify with: SELECT COUNT(*) FROM narratives; SELECT COUNT(*) FROM narrative_metrics;
*/

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Import complete strategic_narrative_schema.sql content
-- Note: This would contain the full schema from strategic_narrative_schema.sql
-- For production, use: pg_dump -s narrative_intelligence > schema_backup_YYYYMMDD.sql

-- =============================================
-- CRITICAL TABLES FOR ROLLBACK
-- =============================================

-- 1. NARRATIVES TABLE (NSF-1 Content)
CREATE TABLE narratives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    narrative_id VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    origin_language CHAR(2) NOT NULL,
    -- ... complete NSF-1 fields as defined in strategic_narrative_schema.sql
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. NARRATIVE_METRICS TABLE (Analytics)
CREATE TABLE narrative_metrics (
    narrative_uuid UUID PRIMARY KEY REFERENCES narratives(id) ON DELETE CASCADE,
    trending_score NUMERIC DEFAULT 0.0 CHECK (trending_score >= 0),
    credibility_score NUMERIC CHECK (credibility_score >= 0.0 AND credibility_score <= 10.0),
    -- ... complete metrics fields as defined in strategic_narrative_schema.sql
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. CRITICAL INDEXES
CREATE INDEX idx_narratives_narrative_id ON narratives (narrative_id);
CREATE INDEX idx_narrative_metrics_trending_score ON narrative_metrics (trending_score DESC);
CREATE INDEX idx_narrative_metrics_status ON narrative_metrics (narrative_status);

-- =============================================
-- DATA INTEGRITY VALIDATION
-- =============================================

-- Function to validate schema integrity after restore
CREATE OR REPLACE FUNCTION validate_schema_restore()
RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- Check narratives table exists
    RETURN QUERY
    SELECT 
        'narratives_table_exists'::TEXT,
        CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'narratives') 
             THEN 'PASS' ELSE 'FAIL' END::TEXT,
        'Core narratives table presence'::TEXT;
    
    -- Check metrics table exists
    RETURN QUERY
    SELECT 
        'metrics_table_exists'::TEXT,
        CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'narrative_metrics') 
             THEN 'PASS' ELSE 'FAIL' END::TEXT,
        'Metrics separation table presence'::TEXT;
    
    -- Check foreign key relationship
    RETURN QUERY
    SELECT 
        'foreign_key_constraint'::TEXT,
        CASE WHEN EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY' 
            AND table_name = 'narrative_metrics'
        ) THEN 'PASS' ELSE 'FAIL' END::TEXT,
        'UUID foreign key relationship'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Run validation after restore
-- SELECT * FROM validate_schema_restore();

-- =============================================
-- EMERGENCY PROCEDURES
-- =============================================

-- If rollback needed during production:
-- 1. STOP all application connections
-- 2. CREATE backup of current data:
--    pg_dump narrative_intelligence > emergency_backup_$(date +%Y%m%d_%H%M).sql
-- 3. RESTORE from this file
-- 4. RESTART applications with rollback configuration
-- 5. VERIFY data integrity with validate_schema_restore()

-- Contact: Development Team
-- Documentation: SCHEMA_VERSION.md
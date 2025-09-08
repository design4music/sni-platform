# Strategic Narrative Intelligence - Schema Version Control

## Current Version: NSF-1 v1.1 + Metrics v1.0

**Date**: 2025-08-01  
**Status**: 🔒 **LOCKED FOR PRODUCTION**

---

## 📋 Version Summary

### NSF-1 Content Schema v1.1
- **Purpose**: Pure narrative content storage following NSF-1 specification
- **Table**: `narratives`
- **Key Features**:
  - UUID primary key + display narrative_id (e.g., "EN-002-A")
  - JSONB fields for complex NSF-1 structures
  - Zero analytics/metrics fields (clean separation)
  - Full-text search and vector similarity ready

### Metrics Analytics Schema v1.0  
- **Purpose**: Operational analytics and scoring separate from content
- **Table**: `narrative_metrics`
- **Key Features**:
  - One-to-one relationship with narratives via UUID foreign key
  - Trending scores, credibility, engagement metrics
  - Geographic scope, keywords, priority management
  - Dashboard and analytics query optimization

---

## 🏗️ Architecture Benefits

✅ **Clean Separation**: NSF-1 content vs operational metrics  
✅ **Performance**: Independent indexing strategies  
✅ **Scalability**: Analytics won't impact content queries  
✅ **Maintainability**: No ghost fields or mixed concerns  

---

## 📁 Core Schema Files

### Production Schema Files
- `strategic_narrative_schema.sql` - **CANONICAL** Complete production schema with partitioning
- `~nsf1_corrected_schema.sql` - ARCHIVED - NSF-1 focused subset (replaced by canonical)
- `query_patterns.sql` - Optimized query patterns with metrics separation
- `validation_constraints.sql` - Data integrity rules
- `migration_strategy.sql` - Performance optimization and monitoring

### Application Integration
- `etl_pipeline/core/database/models.py` - SQLAlchemy models
- `nsf1_pydantic_models.py` - API contract models
- `NSF1_IMPLEMENTATION_SUMMARY.md` - Implementation details

---

## 🔄 Migration Path

### From Previous Schema
```sql
-- Create narrative_metrics table
-- Backfill existing narrative data
SELECT backfill_narrative_metrics();

-- Update all queries to use JOIN pattern
-- See query_patterns.sql for examples
```

### Rollback Strategy
```sql
-- Emergency rollback (if needed)
DROP TABLE narrative_metrics CASCADE;
-- Restore from backup: schema_backup_YYYYMMDD.sql
```

---

## 🔐 Schema Integrity Validation

### Required Checks Before Deployment
```sql
-- 1. Verify all narratives have metrics
SELECT COUNT(*) as missing_metrics 
FROM narratives n 
LEFT JOIN narrative_metrics m ON n.id = m.narrative_uuid 
WHERE m.narrative_uuid IS NULL;
-- Result should be 0

-- 2. Verify no ghost field references
-- All queries must use: JOIN narrative_metrics m ON n.id = m.narrative_uuid

-- 3. Test materialized view refresh
REFRESH MATERIALIZED VIEW mv_narrative_trending_dashboard;
```

---

## 📊 Performance Benchmarks

### Target Performance (Post-Implementation)
- **Dashboard Load**: < 200ms for top 50 trending narratives
- **Narrative Detail**: < 100ms for full NSF-1 + metrics response  
- **Search Queries**: < 500ms for semantic + keyword search
- **Analytics Queries**: < 1s for complex dashboard aggregations

### Key Indexes
- `idx_narrative_metrics_trending_score` - Dashboard performance
- `idx_narratives_embedding` - Semantic search
- `idx_narratives_search_vector` - Full-text search
- `idx_narrative_metrics_status_trending` - Composite queries

---

## 🚨 Breaking Changes

### API Contract Changes
- **Before**: Direct narrative fields (`narrative.trending_score`)
- **After**: Combined response model (NSF-1 + metrics)

### Query Pattern Changes  
- **Before**: `SELECT trending_score FROM narratives`
- **After**: `SELECT m.trending_score FROM narratives n JOIN narrative_metrics m ON n.id = m.narrative_uuid`

---

## ✅ Production Readiness Checklist

- [x] Schema design finalized and validated
- [x] SQLAlchemy models updated with proper relationships
- [x] Query patterns updated for metrics separation  
- [x] Validation constraints updated
- [x] Migration strategy documented
- [x] Performance indexes optimized
- [ ] API contract documentation (NEXT: Combined response model)
- [ ] ETL pipeline updated for new schema
- [ ] Integration tests for schema changes
- [ ] Production deployment scripts

---

## 🔄 Next Development Phase: ETL Pipeline

With schema locked, development focus shifts to:
1. **API Contract**: Combined NSF-1 + metrics response models
2. **ETL Pipeline**: Ingestion → clustering → narrative generation → metrics calculation
3. **Integration Testing**: End-to-end pipeline validation

---

**Schema Lock Authority**: Development Team  
**Approved For Production**: ✅ Ready for API contract definition
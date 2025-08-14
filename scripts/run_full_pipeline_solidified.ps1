# SNI Solidified Pipeline - Complete Flow: Keywords -> CLUST-1 (strict) -> CLUST-2
# Solidified pipeline with quality-focused strict mode
# Recall mode and triads disabled by default

param(
    [int]$HoursBack = 72,
    [switch]$SkipMVRefresh,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
}

Write-Log "=== SNI SOLIDIFIED PIPELINE START ==="
Write-Log "Configuration: HoursBack=$HoursBack, Strict Mode, Triads OFF, Recall OFF"

try {
    # 0) Refresh strategic candidates and materialized views
    if (-not $SkipMVRefresh) {
        Write-Log "Step 0: Refreshing materialized views..."
        
        python -c "
import sys, os
sys.path.insert(0, '.')
from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from sqlalchemy import text

config = get_config()
initialize_database(config.database)

views_to_refresh = [
    'shared_keywords_lib_norm_30d',
    'anchor_pairs_30d', 
    'event_tokens_30d',
    'strategic_candidates_300h'
]

with get_db_session() as session:
    for view_name in views_to_refresh:
        session.execute(text(f'REFRESH MATERIALIZED VIEW {view_name};'))
        session.commit()
        print(f'Refreshed {view_name}')
    print('All materialized views refreshed successfully')
"
        if ($LASTEXITCODE -ne 0) {
            throw "Materialized view refresh failed"
        }
        Write-Log "✓ Materialized views refreshed"
    }

    # 1) Keyword extraction and canonicalization
    Write-Log "Step 1: Running keyword extraction and canonicalization..."
    
    python etl_pipeline/keywords/extract_keywords.py --window $HoursBack --mode auto
    if ($LASTEXITCODE -ne 0) {
        throw "Keyword extraction failed"
    }
    
    python etl_pipeline/keywords/update_keyword_canon_from_db.py
    if ($LASTEXITCODE -ne 0) {
        throw "Keyword canonicalization failed"
    }
    Write-Log "✓ Keywords extracted and canonicalized"

    # 2) CLUST-1 (strict mode pipeline)
    Write-Log "Step 2: Running CLUST-1 strict mode clustering..."
    
    # Seed stage
    python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage seed --window $HoursBack --profile strict --use_triads 0 --lang EN
    if ($LASTEXITCODE -ne 0) {
        throw "CLUST-1 seed stage failed"
    }
    
    # Densify stage
    python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage densify --window $HoursBack --profile strict --cos 0.86 --use_triads 0 --lang EN
    if ($LASTEXITCODE -ne 0) {
        throw "CLUST-1 densify stage failed"
    }
    
    # Orphan attachment
    python etl_pipeline/clustering/clust1_orphan_attach_optimized.py --window $HoursBack --cos 0.89
    if ($LASTEXITCODE -ne 0) {
        throw "CLUST-1 orphan attachment failed"
    }
    
    # Consolidate stage
    python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage consolidate --window $HoursBack --profile strict --merge-cos 0.90 --merge-wj 0.55 --merge-time 0.50 --use_triads 0 --lang EN
    if ($LASTEXITCODE -ne 0) {
        throw "CLUST-1 consolidate stage failed"
    }
    
    # Persist stage
    python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage persist --window $HoursBack --profile strict --use_triads 0 --lang EN
    if ($LASTEXITCODE -ne 0) {
        throw "CLUST-1 persist stage failed"
    }
    Write-Log "✓ CLUST-1 strict mode completed"

    # 3) CLUST-2 (interpretive clustering)
    Write-Log "Step 3: Running CLUST-2 interpretive clustering..."
    
    python etl_pipeline/clustering/clust2_interpretive_clustering.py --confidence-threshold 0.7
    if ($LASTEXITCODE -ne 0) {
        Write-Log "⚠ CLUST-2 completed with warnings" "WARN"
    } else {
        Write-Log "✓ CLUST-2 completed successfully"
    }

    # 4) Final statistics
    Write-Log "Step 4: Generating final statistics..."
    python -c "
import sys, os
sys.path.insert(0, '.')
from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from sqlalchemy import text
from datetime import datetime, timedelta

config = get_config()
initialize_database(config.database)

with get_db_session() as session:
    window_start = datetime.now() - timedelta(hours=$HoursBack)
    
    # Get comprehensive stats
    result = session.execute(text(\"SELECT COUNT(*) FROM articles WHERE language = 'EN' AND published_at >= :start\"), {'start': window_start})
    total_articles = result.fetchone()[0]
    
    result = session.execute(text(\"SELECT COUNT(*) FROM strategic_candidates_300h sc JOIN articles a ON sc.article_id = a.id WHERE a.published_at >= :start AND a.language = 'EN'\"), {'start': window_start})
    strategic_count = result.fetchone()[0]
    
    result = session.execute(text(\"SELECT COUNT(DISTINCT acm.article_id) FROM article_cluster_members acm JOIN articles a ON acm.article_id = a.id WHERE a.published_at >= :start AND a.language = 'EN'\"), {'start': window_start})
    clustered_count = result.fetchone()[0]
    
    result = session.execute(text(\"SELECT COUNT(*) FROM article_clusters WHERE created_at >= :start\"), {'start': window_start})
    cluster_count = result.fetchone()[0]
    
    # CLUST-2 stats
    result = session.execute(text(\"SELECT COUNT(*) FROM narrative_clusters WHERE created_at >= :start\"), {'start': window_start})
    narrative_count = result.fetchone()[0] if result.fetchone() else 0
    
    pct_strategic = round((strategic_count / total_articles) * 100, 1) if total_articles > 0 else 0
    pct_clustered = round((clustered_count / strategic_count) * 100, 1) if strategic_count > 0 else 0
    
    print()
    print('=== SOLIDIFIED PIPELINE RESULTS ===')
    print(f'Total articles processed: {total_articles:,}')
    print(f'Strategic candidates: {strategic_count:,} ({pct_strategic}%)')
    print(f'CLUST-1 clustered: {clustered_count:,} ({pct_clustered}% of strategic)')
    print(f'CLUST-1 clusters created: {cluster_count:,}')
    print(f'CLUST-2 narratives: {narrative_count:,}')
    print()
    print('=== CONFIGURATION SUMMARY ===')
    print('Mode: STRICT (quality-focused)')
    print('Triads: DISABLED (--use_triads 0)')
    print('Recall mode: DISABLED') 
    print('Cosine thresholds: seed/densify=0.86, orphan=0.89')
    print('Consolidation: cos=0.90, wj=0.55, time=0.50')
"

    Write-Log "=== SNI SOLIDIFIED PIPELINE COMPLETED SUCCESSFULLY ==="
    
} catch {
    Write-Log "Pipeline failed: $_" "ERROR"
    exit 1
}
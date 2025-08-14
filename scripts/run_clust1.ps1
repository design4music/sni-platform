# CLUST-1 MVP Pipeline Orchestration Script
# Runs the complete taxonomy-aware clustering pipeline

param(
    [int]$HoursBack = 72,
    [string]$Language = $null,
    [double]$CosThreshold = 0.86,
    [string]$Profile = "strict",  # strict or recall
    [switch]$SkipRefine,
    [switch]$Verbose
)

# Set error action
$ErrorActionPreference = "Stop"

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    if ($Verbose) {
        Write-Host $logEntry
    }
}

# Check if Python is available
try {
    python --version | Out-Null
    Write-Log "Python is available"
} catch {
    Write-Log "Python is not available or not in PATH" "ERROR"
    exit 1
}

Write-Log "Starting CLUST-1 MVP Pipeline"
Write-Log "Parameters: HoursBack=$HoursBack, Language=$Language, CosThreshold=$CosThreshold, Profile=$Profile"

try {
    # Step 1: Refresh strategic candidates
    Write-Log "Step 1: Refreshing strategic candidates..."
    python -c "
import sys, os
sys.path.insert(0, '.')
from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from sqlalchemy import text

config = get_config()
initialize_database(config.database)

with get_db_session() as session:
    session.execute(text('REFRESH MATERIALIZED VIEW strategic_candidates_300h;'))
    session.commit()
    print('Strategic candidates refreshed')
"
    if ($LASTEXITCODE -ne 0) {
        throw "Strategic candidates refresh failed"
    }
    Write-Log "Strategic candidates refresh completed"

    # Step 2: Unified keyword extraction
    Write-Log "Step 2: Running unified keyword extraction..."
    python etl_pipeline/keywords/extract_keywords.py --window $HoursBack --mode auto
    if ($LASTEXITCODE -ne 0) {
        throw "Unified keyword extraction failed"
    }
    Write-Log "Unified keyword extraction completed"

    # Step 3: Update canonical mappings
    Write-Log "Step 3: Updating canonical mappings..."
    python etl_pipeline/keywords/update_keyword_canon_from_db.py
    if ($LASTEXITCODE -ne 0) {
        throw "Canonical mapping update failed"
    }
    Write-Log "Canonical mapping update completed"

    # Step 4: Refresh materialized views
    Write-Log "Step 4: Refreshing materialized views..."
    python -c "
import sys
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
    Write-Log "Materialized views refreshed"

    # Step 6: CLUST-1 Clustering Pipeline
    Write-Log "Step 6: Running CLUST-1 seed stage..."
    python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage seed --window $HoursBack --profile strict --use_triads 0 --lang EN
    if ($LASTEXITCODE -ne 0) {
        throw "Seed stage failed"
    }
    Write-Log "Seed stage completed"

    Write-Log "Step 7: Running CLUST-1 densify stage..."
    python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage densify --window $HoursBack --profile strict --cos 0.86 --use_triads 0 --lang EN
    if ($LASTEXITCODE -ne 0) {
        throw "Densify stage failed"
    }
    Write-Log "Densify stage completed"

    Write-Log "Step 8: Running strict orphan attachment..."
    python etl_pipeline/clustering/clust1_orphan_attach_optimized.py --window $HoursBack --cos 0.89
    if ($LASTEXITCODE -ne 0) {
        throw "Orphan attachment failed"
    }
    Write-Log "Orphan attachment completed"

    Write-Log "Step 9: Running CLUST-1 consolidate stage..."
    python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage consolidate --window $HoursBack --merge-cos 0.90 --merge-wj 0.55 --merge-time 0.50 --profile strict --use_triads 0
    if ($LASTEXITCODE -ne 0) {
        throw "Consolidate stage failed"
    }
    Write-Log "Consolidate stage completed"

    Write-Log "Step 10: Running CLUST-1 persist stage..."
    python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage persist --window $HoursBack --profile strict --use_triads 0
    if ($LASTEXITCODE -ne 0) {
        throw "Persist stage failed"
    }
    Write-Log "Persist stage completed"

    Write-Log "CLUST-1 MVP Pipeline completed successfully!"
    
    # Step 11: KPI Check (72h window)  
    Write-Log "Step 11: Checking KPIs (72h window)..."
    python -c "
import sys
sys.path.insert(0, '.')
from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from sqlalchemy import text
from datetime import datetime, timedelta
import math

config = get_config()
initialize_database(config.database)

with get_db_session() as session:
    window_start = datetime.now() - timedelta(hours=72)
    
    # KPI 1: Strategic filtering rate  
    result = session.execute(text(`"SELECT COUNT(*) FROM articles WHERE language = 'EN' AND created_at >= :start`"), {'start': window_start})
    total_articles = result.fetchone()[0]
    
    result = session.execute(text(`"SELECT COUNT(*) FROM strategic_candidates_300h sc JOIN articles a ON sc.article_id = a.id WHERE a.created_at >= :start`"), {'start': window_start})
    strategic_count = result.fetchone()[0]
    
    # KPI 2: Clustering success rate
    result = session.execute(text(`"SELECT COUNT(DISTINCT acm.article_id) FROM article_cluster_members acm JOIN articles a ON acm.article_id = a.id WHERE a.created_at >= :start`"), {'start': window_start})
    clustered_count = result.fetchone()[0]
    
    # KPI 3: Median entropy
    result = session.execute(text('''
        WITH cluster_entropies AS (
            SELECT ac.cluster_id, 
                   -SUM((cnt::float / ac.size) * LN(cnt::float / ac.size)) as entropy
            FROM article_clusters ac
            JOIN (
                SELECT acm.cluster_id, ck.token, COUNT(*) as cnt
                FROM article_cluster_members acm
                JOIN article_core_keywords ck ON ck.article_id = acm.article_id
                GROUP BY acm.cluster_id, ck.token
            ) keyword_counts ON ac.cluster_id = keyword_counts.cluster_id
            WHERE ac.created_at >= :start AND ac.size >= 3
            GROUP BY ac.cluster_id, ac.size
        )
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY entropy) as median_entropy
        FROM cluster_entropies
    '''), {'start': window_start})
    median_entropy_result = result.fetchone()
    median_entropy = median_entropy_result[0] if median_entropy_result and median_entropy_result[0] else 0
    
    # Calculate percentages
    pct_candidates = round((strategic_count / total_articles) * 100, 1) if total_articles > 0 else 0
    pct_clustered = round((clustered_count / strategic_count) * 100, 1) if strategic_count > 0 else 0
    
    print()
    print('=== KPI RESULTS (72h Window) ===')
    print(f'Strategic filtering: {pct_candidates}% (aim: 35-45%)')
    print(f'Clustering success: {pct_clustered}% (aim: 35-55%)')
    print(f'Median entropy: {median_entropy:.2f} (aim: ≤2.35)')
    print()
    
    # Status indicators
    status_strategic = 'OK' if 35 <= pct_candidates <= 45 else 'LOW' if pct_candidates < 35 else 'HIGH'
    status_clustering = 'OK' if 35 <= pct_clustered <= 55 else 'LOW' if pct_clustered < 35 else 'HIGH'
    status_entropy = 'OK' if median_entropy <= 2.35 else 'HIGH'
    
    print(f'Status: Strategic [{status_strategic}] | Clustering [{status_clustering}] | Entropy [{status_entropy}]')
"
    if ($LASTEXITCODE -ne 0) {
        Write-Log "KPI check failed" "WARN"
    } else {
        Write-Log "KPI check completed"
    }
    
    Write-Log "Pipeline Summary:"
    Write-Log "=================="
    
} catch {
    Write-Log "Pipeline failed: $_" "ERROR"
    exit 1
}

# Optional: Show results summary
try {
    Write-Log "Fetching results summary..."
    
    # This would normally use psql, but we'll use python for compatibility
    $summaryScript = @"
import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),  
    database=os.getenv('DB_NAME', 'narrative_intelligence'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', '')
)

cur = conn.cursor()

# Article topics count
cur.execute('SELECT COUNT(*) FROM article_topics')
topics_count = cur.fetchone()[0]
print(f'Article-topic mappings: {topics_count}')

# Clusters count  
cur.execute('SELECT COUNT(*) FROM article_clusters')
clusters_count = cur.fetchone()[0]
print(f'Total clusters: {clusters_count}')

# Top 10 clusters by size
cur.execute('''
    SELECT cluster_id, size, label, top_topics[1:2] as top_topics_preview
    FROM article_clusters 
    ORDER BY size DESC 
    LIMIT 10
''')
top_clusters = cur.fetchall()

print('')
print('Top 10 clusters by size:')
print('========================')
for cluster in top_clusters:
    cluster_id_short = str(cluster[0])[:8]
    size = cluster[1]
    label = cluster[2] or 'Unlabeled'
    topics = cluster[3][:2] if cluster[3] else []
    print(f'{cluster_id_short}... | Size: {size:3d} | {label} | Topics: {topics}')

cur.close()
conn.close()
"@

    echo $summaryScript | python
    
} catch {
    Write-Log "Could not fetch summary statistics: $_" "WARN"
}

Write-Log "Pipeline execution completed."
# CLUST-1 MVP Pipeline Orchestration Script
# Runs the complete taxonomy-aware clustering pipeline

param(
    [int]$HoursBack = 72,
    [string]$Language = $null,
    [double]$CosThreshold = 0.82,
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
Write-Log "Parameters: HoursBack=$HoursBack, Language=$Language, CosThreshold=$CosThreshold"

try {
    # Step 1: Sync taxonomies
    Write-Log "Step 1: Syncing taxonomies..."
    python etl_pipeline/taxonomy/sync_taxonomies.py
    if ($LASTEXITCODE -ne 0) {
        throw "Taxonomy sync failed"
    }
    Write-Log "Taxonomy sync completed"

    # Step 2: Map articles to topics
    Write-Log "Step 2: Mapping articles to topics (last $HoursBack hours)..."
    $mapArgs = "--since $HoursBack"
    python etl_pipeline/taxonomy/map_article_topics.py $mapArgs.Split()
    if ($LASTEXITCODE -ne 0) {
        throw "Article topic mapping failed"
    }
    Write-Log "Article topic mapping completed"

    # Step 3: Seed stage
    Write-Log "Step 3: Running seed stage..."
    $seedArgs = @("--stage", "seed", "--window", $HoursBack)
    if ($Language) {
        $seedArgs += @("--lang", $Language)
    }
    python etl_pipeline/clustering/clust1_taxonomy_graph.py $seedArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Seed stage failed"
    }
    Write-Log "Seed stage completed"

    # Step 4: Densify stage
    Write-Log "Step 4: Running densify stage (cosine threshold: $CosThreshold)..."
    $densifyArgs = @("--stage", "densify", "--window", $HoursBack, "--cos", $CosThreshold)
    if ($Language) {
        $densifyArgs += @("--lang", $Language)
    }
    python etl_pipeline/clustering/clust1_taxonomy_graph.py $densifyArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Densify stage failed"
    }
    Write-Log "Densify stage completed"

    # Step 5: Refine stage (optional)
    if (-not $SkipRefine) {
        Write-Log "Step 5: Running refine stage..."
        $refineArgs = @("--stage", "refine", "--window", $HoursBack, "--min-size", "80")
        if ($Language) {
            $refineArgs += @("--lang", $Language)
        }
        python etl_pipeline/clustering/clust1_taxonomy_graph.py $refineArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Refine stage failed"
        }
        Write-Log "Refine stage completed"
    } else {
        Write-Log "Refine stage skipped"
    }

    # Step 6: Persist stage
    Write-Log "Step 6: Running persist stage..."
    $persistArgs = @("--stage", "persist", "--window", $HoursBack, "--cos", $CosThreshold)
    if ($Language) {
        $persistArgs += @("--lang", $Language)
    }
    python etl_pipeline/clustering/clust1_taxonomy_graph.py $persistArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Persist stage failed"
    }
    Write-Log "Persist stage completed"

    # Step 7: Label clusters
    Write-Log "Step 7: Labeling clusters..."
    python etl_pipeline/clustering/clust1_labeler.py
    if ($LASTEXITCODE -ne 0) {
        throw "Cluster labeling failed"
    }
    Write-Log "Cluster labeling completed"

    Write-Log "CLUST-1 MVP Pipeline completed successfully!"
    
    # Show summary statistics
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
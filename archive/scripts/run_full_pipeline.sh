#!/bin/bash
# SNI Pipeline - Complete Flow: Keywords -> CLUST-1 (strict) -> CLUST-2
# Solidified pipeline with quality-focused strict mode

set -e  # Exit on any error

echo "=== SNI COMPLETE PIPELINE START ==="
echo "Timestamp: $(date)"

# 0) Refresh strategic candidates and materialized views
echo "Step 0: Refreshing materialized views..."
psql narrative_intelligence -c "REFRESH MATERIALIZED VIEW CONCURRENTLY shared_keywords_lib_norm_30d;"
psql narrative_intelligence -c "REFRESH MATERIALIZED VIEW CONCURRENTLY anchor_pairs_30d;"
psql narrative_intelligence -c "REFRESH MATERIALIZED VIEW CONCURRENTLY event_tokens_30d;"
psql narrative_intelligence -c "REFRESH MATERIALIZED VIEW CONCURRENTLY article_core_keywords;"
psql narrative_intelligence -c "REFRESH MATERIALIZED VIEW CONCURRENTLY strategic_candidates_300h;"
echo "✓ Materialized views refreshed"

# 1) Keyword extraction and canonicalization
echo "Step 1: Running keyword extraction and canonicalization..."
python etl_pipeline/keywords/extract_keywords.py --window 72 --mode auto
python etl_pipeline/keywords/update_keyword_canon_from_db.py
echo "✓ Keywords extracted and canonicalized"

# 2) CLUST-1 (strict mode pipeline)
echo "Step 2: Running CLUST-1 strict mode clustering..."
python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage seed --window 72 --profile strict --use_triads 0
python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage densify --window 72 --profile strict --cos 0.86 --use_triads 0
python etl_pipeline/clustering/clust1_orphan_attach_optimized.py --window 72 --cos 0.89
python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage consolidate --window 72 --profile strict --merge-cos 0.90 --merge-wj 0.55 --merge-time 0.50 --use_triads 0
python etl_pipeline/clustering/clust1_taxonomy_graph.py --stage persist --window 72 --profile strict --use_triads 0
echo "✓ CLUST-1 strict mode completed"

# 3) CLUST-2 (interpretive clustering with anti-micro gates)
echo "Step 3: Running CLUST-2 interpretive clustering..."
if [ -f "etl_pipeline/clust2/run.py" ]; then
    python etl_pipeline/clust2/run.py --no_prefilter \
      --min_cluster_size 3 --min_sources 2 \
      --distinctiveness_max_cosine_to_parent 0.92 \
      --anchor_lift_min 1.5 --max_children 5
    echo "✓ CLUST-2 completed"
else
    echo "⚠ CLUST-2 script not found, skipping"
fi

echo "=== SNI COMPLETE PIPELINE COMPLETED ==="
echo "Timestamp: $(date)"
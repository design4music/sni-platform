-- Add cluster_type column to article_clusters table
-- CLUST-1 Phase A Enhancement: Support for 'final' vs 'macro' cluster classification

-- Add cluster_type column with constraint
ALTER TABLE article_clusters 
ADD COLUMN IF NOT EXISTS cluster_type TEXT 
CHECK (cluster_type IN ('final', 'macro')) 
DEFAULT 'final';

-- Set all existing clusters to 'final' type
UPDATE article_clusters 
SET cluster_type = 'final' 
WHERE cluster_type IS NULL;

-- Add index for performance on cluster_type queries
CREATE INDEX IF NOT EXISTS idx_article_clusters_cluster_type 
ON article_clusters(cluster_type);

-- Verify the column was added correctly
SELECT 
    COUNT(*) as total_clusters,
    COUNT(*) FILTER (WHERE cluster_type = 'final') as final_clusters,
    COUNT(*) FILTER (WHERE cluster_type = 'macro') as macro_clusters
FROM article_clusters;
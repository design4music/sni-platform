#!/bin/bash
# SNI Keyword Extraction Worker (Linux/Cron Version)
# Add to crontab with: */5 * * * * /path/to/keyword_worker.sh >> /var/log/sni/extractor.log 2>&1

cd "$(dirname "$0")/.."

echo "=== Keyword Worker Run - $(date) ==="

# Run chunked keyword extractor
python etl_pipeline/keywords/extract_keywords.py --mode auto --window 72 \
  --batch-size 300 --time-budget-seconds 540 --max-workers 4 \
  --cap-per-article 8 --only-new 1

echo "Worker completed with exit code: $?"
echo ""
# SNI Keyword Extraction Worker Loop
# Runs chunked keyword extraction continuously in the background
# Start and forget - processes 3-5k articles/day on a laptop

Write-Host "Starting SNI Keyword Extraction Worker Loop..."
Write-Host "Press Ctrl+C to stop the worker"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath

Set-Location $projectRoot

$iteration = 0

while ($true) {
    $iteration++
    Write-Host ""
    Write-Host "=== Iteration $iteration - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    
    try {
        # Run chunked keyword extractor
        python etl_pipeline\keywords\extract_keywords.py --mode auto --window 72 `
            --batch-size 200 --time-budget-seconds 600 --max-workers 4 `
            --cap-per-article 8 --only-new 1
        
        $exitCode = $LASTEXITCODE
        if ($exitCode -eq 0) {
            Write-Host "Worker completed successfully" -ForegroundColor Green
        } else {
            Write-Host "Worker failed with exit code $exitCode" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "Worker crashed: $_" -ForegroundColor Red
    }
    
    Write-Host "Sleeping 60 seconds before next iteration..."
    Start-Sleep -Seconds 60
}
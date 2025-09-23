# SNI Pipeline Cron Setup

## Timeout Mitigation Strategy Implementation

This document provides production-ready cron job configurations for the SNI pipeline phases with timeout mitigation.

## Overview

- **P1 Ingest**: 12-hour intervals with batch/resume capability
- **P2 Filter**: 12-hour intervals with batch/resume capability
- **P3 Generate**: Continuous background systemd service
- **P4 Enrich**: 12-hour intervals with batch/resume capability

## Cron Jobs Configuration

### P1 - RSS Ingestion (Every 12 Hours)
```bash
# At 6:00 AM and 6:00 PM daily
0 6,18 * * * cd /path/to/SNI && timeout 30m flock -n /tmp/p1_ingest.lock python apps/ingest/run_ingestion.py --batch 500 --resume >> /var/log/sni/p1_ingest.log 2>&1
```

### P2 - Strategic Filtering (Every 12 Hours)
```bash
# At 6:30 AM and 6:30 PM daily (30 min after P1)
30 6,18 * * * cd /path/to/SNI && timeout 15m flock -n /tmp/p2_filter.lock python apps/filter/run_enhanced_gate.py --batch 1000 --resume >> /var/log/sni/p2_filter.log 2>&1
```

### P4 - Event Family Enrichment (Every 12 Hours)
```bash
# At 7:00 AM and 7:00 PM daily (30 min after P2)
0 7,19 * * * cd /path/to/SNI && timeout 45m flock -n /tmp/p4_enrich.lock python apps/enrich/cli.py enrich-queue --batch 50 --resume >> /var/log/sni/p4_enrich.log 2>&1
```

## Systemd Service for P3 Generation

### Service File: `/etc/systemd/system/sni-p3-generate.service`
```ini
[Unit]
Description=SNI P3 Event Family Generation Worker
After=network.target
Wants=network.target

[Service]
Type=simple
User=sni
Group=sni
WorkingDirectory=/path/to/SNI
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python apps/generate/incident_processor.py 1000 --background
Restart=always
RestartSec=10
StandardOutput=append:/var/log/sni/p3_generate.log
StandardError=append:/var/log/sni/p3_generate.log

[Install]
WantedBy=multi-user.target
```

### Enable and Start P3 Service
```bash
sudo systemctl enable sni-p3-generate.service
sudo systemctl start sni-p3-generate.service
sudo systemctl status sni-p3-generate.service
```

## Directory Setup

### Create Log Directory
```bash
sudo mkdir -p /var/log/sni
sudo chown sni:sni /var/log/sni
sudo chmod 755 /var/log/sni
```

### Create Lock Directory
```bash
sudo mkdir -p /tmp
# Lock files are automatically created by flock
```

## Installation Commands

### Add to Crontab
```bash
# Edit crontab for the sni user
sudo -u sni crontab -e

# Add all three cron jobs above
```

### Verify Cron Jobs
```bash
# List current cron jobs
sudo -u sni crontab -l

# Check cron service status
sudo systemctl status cron
```

## Monitoring Commands

### Check Logs
```bash
# P1 Ingest logs
tail -f /var/log/sni/p1_ingest.log

# P2 Filter logs
tail -f /var/log/sni/p2_filter.log

# P3 Generate logs
tail -f /var/log/sni/p3_generate.log

# P4 Enrich logs
tail -f /var/log/sni/p4_enrich.log
```

### Check Process Status
```bash
# Check if P3 service is running
sudo systemctl status sni-p3-generate.service

# Check current pipeline processes
ps aux | grep -E "(ingest|filter|generate|enrich)" | grep python

# Check lock files (active jobs)
ls -la /tmp/*.lock
```

### Check Checkpoints
```bash
# View current checkpoint states
cat /path/to/SNI/logs/checkpoints/p1_ingest.json
cat /path/to/SNI/logs/checkpoints/p2_filter.json
# P3 has no checkpoints (continuous processing)
# P4 checkpoint is managed automatically
```

## Troubleshooting

### If Jobs Fail to Start
1. Check disk space: `df -h`
2. Check permissions: `ls -la /path/to/SNI`
3. Check environment variables: `sudo -u sni env`
4. Check database connectivity: Test connection

### If Jobs Get Stuck
1. Check for stale lock files: `ls -la /tmp/*.lock`
2. Remove stale locks: `sudo rm /tmp/p*_*.lock`
3. Check system resources: `top`, `htop`
4. Check log files for errors

### Manual Execution
```bash
# Test P1 manually
cd /path/to/SNI && python apps/ingest/run_ingestion.py --batch 100 --resume

# Test P2 manually
cd /path/to/SNI && python apps/filter/run_enhanced_gate.py --batch 200 --resume

# Test P4 manually
cd /path/to/SNI && python apps/enrich/cli.py enrich-queue --batch 10 --resume
```

## Performance Tuning

### Adjust Batch Sizes Based on Performance
- **P1 Ingest**: Start with 500, increase if processing is fast
- **P2 Filter**: Start with 1000, adjust based on entity extraction speed
- **P3 Generate**: 1000 titles per cycle, adjust based on LLM performance
- **P4 Enrich**: Start with 50, increase if enrichment is fast

### Adjust Timeouts Based on System Performance
- **P1**: 30 minutes (RSS feeds can be slow)
- **P2**: 15 minutes (entity extraction is fast)
- **P4**: 45 minutes (enrichment involves external API calls)

## Architecture Notes

This setup implements the timeout mitigation strategy:
- ✅ **Resumable Operations**: All phases use checkpoints to resume from last position
- ✅ **Batch Processing**: All phases process data in configurable batches
- ✅ **Idempotent**: Jobs can be safely rerun without data corruption
- ✅ **Timeout Protection**: Each job has appropriate timeouts with `timeout` command
- ✅ **Lock Protection**: `flock` prevents multiple instances running simultaneously
- ✅ **Continuous P3**: Background systemd service ensures Event Family generation never stops
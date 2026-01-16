# Archive Candidates for Future Cleanup

This document lists files and directories that are candidates for archiving once production deployment is confirmed stable.

## High Priority Archive Candidates

### /db/ Directory
- **80 Python scripts** - Mostly one-time migration/check scripts
- Keep only active migrations in `/db/migrations/`
- Archive the rest to `/attic/db/one_time_scripts/`
- Examples to keep: Clean production migration scripts
- Examples to archive: check_*.py, fix_*.py, verify_*.py, populate_*.py

### Root-Level Temporary Files
- **tmpclaude-* files** (50+ files) - Temporary Claude Code working directories
- Add to .gitignore: `tmpclaude-*-cwd`
- Safe to delete locally, should never be committed

### /api/ Directory
- Legacy API code (if not actively used)
- Needs manual review to confirm if still needed

### /etl_pipeline/ Directory
- Legacy pipeline code (predates v3/pipeline)
- Likely safe to archive

### /logs/ Directory
- Runtime logs (should be in .gitignore)
- Not code, safe to exclude from git

### /out/ Directory
- Pipeline output files/reports
- Should be in .gitignore for most files
- Keep directory structure, gitignore contents

## Medium Priority Archive Candidates

### Pipeline Cleanup
- `pipeline/Titles not added to centroids.txt` - One-time analysis, archive
- `pipeline/pipeline_test_report.json` - Test artifact, can regenerate
- `pipeline/test_results_analysis.py` - One-time analysis script
- `pipeline/taxonomy_tools/out/oos_reports/` - Old reports, archive

### Documentation Cleanup
- `/docs/tickets/*.txt` - Old tickets, already in `/attic/docs/tickets/`
- Consider consolidating active tickets into tracking system

## Low Priority (Review Later)

### Build Artifacts
- `__pycache__/` directories - Add to .gitignore globally
- `*.pyc` files - Should already be gitignored

### Frontend
- `apps/frontend/tmpclaude-*-cwd` - Temporary files, gitignore

## Recommended .gitignore Additions

Add these patterns to `.gitignore`:
```gitignore
# Temporary Claude Code working directories
tmpclaude-*-cwd

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so

# Logs
logs/
*.log

# Pipeline outputs
out/*.json
out/taxonomy_*/
!out/.gitkeep

# Environment
.env
.env.local

# OS files
.DS_Store
Thumbs.db
```

## Action Items for Max

1. **Immediate:**
   - Review /api/ and /etl_pipeline/ - still needed?
   - Update .gitignore with recommended patterns
   - Clean up tmpclaude-* files locally

2. **Before Production:**
   - Archive /db/ one-time scripts (keep only migrations)
   - Move pipeline/test_* files to attic
   - Archive old taxonomy_tools reports

3. **Post-Production:**
   - Once stable, archive entire `/attic/` directory to separate repo or zip
   - Consider splitting taxonomy_tools to separate "tools" repo

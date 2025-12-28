## 🔧 Development Guidelines

### Session Start Checklist
**ALWAYS run these commands at the start of any development session:**
```bash
# 1. Check current git state (prevents conflicts)
git status
git log --oneline -5

# 2. Verify database connection
python -c "from core.database import get_db_session; print('✅ Database connected')"

# 3. Check background processes
ps aux | grep python  # Linux/Mac
tasklist | findstr python  # Windows
```

### Git Workflow Lessons Learned

#### ⚠️ Critical: Always Check Git State First
**Problem**: When conversations get summarized and continued, it's easy to lose track of actual git state vs. conceptual progress.

**Solution**: Before any git operation, check the actual state:
```bash
git status                    # Check for uncommitted changes
git log --oneline -5          # See recent commits
git fetch origin             # Check remote state
git log --oneline origin/main -3  # See remote commits
```

#### Git Conflict Resolution Strategy
1. **Identify the conflict source**: `git log --oneline origin/main -5` vs `git log --oneline HEAD -5`
2. **For solo development**: Use `git push --force-with-lease` when you're the only developer
3. **Never use**: `git checkout --ours .` blindly - always examine conflicts first
4. **When rebasing fails**: `git rebase --abort` and assess the situation

#### Commit Message Standards
```
FEATURE: Brief description (50 chars max)

- Detailed change 1
- Detailed change 2
- Performance impact if any

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Code Organization Principles

#### Module Import Standards
- Always use: `python -m apps.module.script` format
- Never use: relative imports in scripts
- Path handling: Add project root to sys.path in standalone scripts

#### Development Safety Rules
1. **Database migrations**: Always backup before schema changes
2. **Background processes**: Check running processes before starting new ones
3. **Configuration changes**: Test in development environment first
4. **Large refactors**: Create feature branches for complex changes
5. **Architectural changes**: ALWAYS discuss approach with alternatives, pros/cons before implementation

### Troubleshooting Quick Reference

#### Common Issues & Solutions
- **Git conflicts after context switch**: Check git state first, force-push if solo dev
- **Import errors**: Use `python -m apps.module.script` format
- **Background process conflicts**: Kill existing processes before starting new ones
- **Database connection issues**: Verify PostgreSQL service and config.py settings
- **LLM timeouts**: Increase timeout values in config.py, check API key validity

#### Emergency Recovery
```bash
# Reset to last known good state
git reflog                    # Find good commit
git reset --hard <commit>     # Reset to good state
git push --force-with-lease   # Update remote (SOLO DEV ONLY)

# Clear all background processes
pkill -f "python.*apps"      # Linux/Mac
taskkill /F /IM python.exe    # Windows (careful!)
```


# Session Handoff Protocol for SNI Development

## When to Update Status (Manual Trigger Points)

### Before Major Breaks
1. **When conversation gets long** (approaching context limits)
2. **Before complex operations** (testing, deployment, major changes)
3. **When switching between major tasks** (RSS -> CLUST-1 -> CLUST-2)
4. **End of work sessions** (when user indicates stopping)

### Quick Status Update Command
When approaching session limits, run this update sequence:

```bash
# Quick status check and update
echo "=== SESSION HANDOFF UPDATE ===" >> CURRENT_SYSTEM_STATUS.md
echo "Date: $(date)" >> CURRENT_SYSTEM_STATUS.md
echo "Last Action: [DESCRIBE WHAT WE JUST DID]" >> CURRENT_SYSTEM_STATUS.md
echo "Next Priority: [WHAT SHOULD HAPPEN NEXT]" >> CURRENT_SYSTEM_STATUS.md
echo "Status: [WORKING/BLOCKED/COMPLETE]" >> CURRENT_SYSTEM_STATUS.md
echo "" >> CURRENT_SYSTEM_STATUS.md
```

## Manual Workflow

### When I Notice Long Conversation:
1. **Ask user**: "Should I update status before we continue?"
2. **Update CURRENT_SYSTEM_STATUS.md** with:
   - What we just accomplished
   - Current blockers (if any)
   - Immediate next steps
   - System state (working/broken/ready)

### When User Indicates Break:
1. **Always update status document**
2. **Update todo list** with current progress
3. **Note any environment changes** (new files, API keys, etc.)

## Status Update Template

```markdown
## Session [DATE] [TIME] Update

### Just Completed
- [List what we just finished]

### Current State  
- System: [WORKING/BROKEN/READY]
- Last successful operation: [DESCRIBE]
- Blockers: [NONE/LIST ISSUES]

### Immediate Next Steps
1. [Most urgent next action]
2. [Second priority]

### Environment Notes
- API keys: [CONFIGURED/MISSING]
- Database: [CONNECTED/DISCONNECTED]
- Dependencies: [OK/MISSING]
- Scripts ready: [LIST AVAILABLE SCRIPTS]

### Context for Next Session
[Brief summary of where we are and what to do next]
```

## Recovery Protocol

### Starting New Session
1. Read `CURRENT_SYSTEM_STATUS.md` first
2. Check latest session update at bottom
3. Verify system state mentioned in last update
4. Continue from "Immediate Next Steps"

### If Status Seems Outdated
1. Quick system check (list files, check logs)
2. Update status with current findings
3. Proceed with planned next steps

## Key Principle
**Better to manually update frequently than lose context completely.**

This protocol relies on human awareness of conversation length and explicit status updates rather than automatic token detection.
# IRIS Agent Migration Notice
**Date**: August 19, 2025
**Status**: MIGRATION COMPLETE

## ⚠️ IMPORTANT: IRIS Has Moved!

The IRIS agent has been migrated to follow the standard agent architecture pattern.

### Old Location (OBSOLETE)
- `api/iris_unified_agent.py` ❌ NO LONGER USED

### New Location (ACTIVE) ✅
- `agents/iris/agent.py` - Main IRIS implementation
- `agents/iris/prompts.py` - IRIS prompts and personality
- `agents/iris/state.py` - State management
- `agents/iris/README.md` - Documentation

### Import Changes
```python
# OLD (don't use)
from api.iris_unified_agent import router

# NEW (use this)
from agents.iris.agent import router
```

### Files Archived
- `iris_unified_agent_OLD_MOVED.py` - Original unified agent (backup)
- Other iris_*.py files in api/ folder are legacy implementations

### Why This Change?
- Consistency: All agents now follow the same structure in agents/ folder
- Organization: Easier to find and maintain agent code
- Standards: Follows the established pattern of agent.py, prompts.py, state.py

### Testing Confirmed
✅ IRIS API endpoints working at `/api/iris/*`
✅ All functionality preserved
✅ Performance optimizations intact

If you need to work on IRIS, please use:
**`agents/iris/agent.py`**
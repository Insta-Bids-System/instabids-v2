# AI-Agents Directory Cleanup Plan

**Agent**: Agent 6 - Quality Gatekeeper  
**Created**: August 1, 2025  
**Status**: 🔴 URGENT - Directory is extremely cluttered

---

## 🚨 **THE PROBLEM**

The `ai-agents/` directory has **250+ files in the root**, making it nearly impossible to find core files. This is a critical maintenance issue.

---

## 📊 **CURRENT STATE ANALYSIS**

### **File Type Breakdown:**

| Pattern | Count | Description | Action |
|---------|-------|-------------|--------|
| `test_*.py` | ~150 | Test files | Move to `tests/` |
| `check_*.py` | ~30 | DB check scripts | Move to `scripts/checks/` |
| `debug_*.py` | ~15 | Debug utilities | Move to `scripts/debug/` |
| `create_*.py` | ~20 | Test data creation | Move to `scripts/setup/` |
| `fix_*.py` | ~15 | One-off fixes | Archive or delete |
| `*.md` | ~20 | Documentation | Move to `docs/` |
| `*.html` | ~10 | Test outputs | Delete or archive |
| `*.sql` | ~8 | SQL scripts | Move to `database/sql/` |

---

## 🎯 **PROPOSED NEW STRUCTURE**

```
ai-agents/
├── agents/           # Core agent code (NO CHANGE)
├── api/             # API endpoints (NO CHANGE)
├── routes/          # Route handlers (NO CHANGE)
├── models/          # Data models (NO CHANGE)
├── database/        # DB utilities (NO CHANGE)
├── utils/           # Utilities (NO CHANGE)
├── tests/           # NEW - All test files
│   ├── unit/       # Unit tests by agent
│   ├── integration/ # Integration tests
│   └── e2e/        # End-to-end tests
├── scripts/         # NEW - Utility scripts
│   ├── checks/     # Database checks
│   ├── debug/      # Debug utilities
│   ├── setup/      # Setup/creation scripts
│   └── archive/    # Old fix scripts
├── docs/           # EXPAND - All documentation
└── [core files only in root]
```

---

## 📝 **STEP-BY-STEP CLEANUP PLAN**

### **Phase 1: Create Directory Structure**
```bash
mkdir -p ai-agents/tests/{unit,integration,e2e}
mkdir -p ai-agents/scripts/{checks,debug,setup,archive}
```

### **Phase 2: Move Test Files**
1. Move all `test_*.py` files to appropriate test subdirectory
2. Group by functionality (e.g., all CIA tests together)
3. Update any import paths if needed

### **Phase 3: Move Utility Scripts**
1. `check_*.py` → `scripts/checks/`
2. `debug_*.py` → `scripts/debug/`
3. `create_*.py` → `scripts/setup/`
4. `fix_*.py` → `scripts/archive/` (or delete if obsolete)

### **Phase 4: Move Documentation**
1. All `*.md` files → `docs/`
2. Organize by topic/agent

### **Phase 5: Clean Artifacts**
1. Delete `*.html` test outputs
2. Move `*.sql` → `database/sql/`
3. Delete `nul` file
4. Clean up log files

### **Phase 6: Verify Core Files**
Ensure only these remain in root:
- `main.py` - FastAPI app
- `config.py` - Configuration
- `requirements.txt` - Dependencies
- `pyproject.toml` - Project config
- `.env` - Environment variables
- Essential startup scripts

---

## ⚠️ **RISKS & MITIGATIONS**

### **Risk 1: Breaking Imports**
- **Mitigation**: Search for imports before moving files
- **Tool**: Use grep to find all references

### **Risk 2: Breaking Scripts**
- **Mitigation**: Test critical scripts after move
- **Tool**: Run key workflows to verify

### **Risk 3: Other Agents Confusion**
- **Mitigation**: Document new structure clearly
- **Update**: CLAUDE.md with new paths

---

## ✅ **SUCCESS CRITERIA**

1. **Root directory has <20 files**
2. **All tests organized by type/agent**
3. **Scripts categorized by purpose**
4. **Documentation centralized**
5. **No broken imports**
6. **All agents can still function**

---

## 🚀 **EXECUTION CHECKLIST**

- [ ] Get user approval for plan
- [ ] Create new directory structure
- [ ] Move test files (largest group)
- [ ] Move utility scripts
- [ ] Move documentation
- [ ] Clean up artifacts
- [ ] Test critical paths
- [ ] Update import paths
- [ ] Document changes
- [ ] Commit with clear message

---

## 💡 **LONG-TERM BENEFITS**

1. **Easier navigation** for all agents
2. **Clear separation** of concerns
3. **Faster file discovery**
4. **Better test organization**
5. **Cleaner git history**
6. **Professional structure**

---

**Ready to execute this cleanup? This will significantly improve the codebase maintainability.**
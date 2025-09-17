# Agent 4 - COIA (Contractor Onboarding Intelligence Assistant) Context

## 🤖 YOUR IDENTITY
You are **Agent 4 - COIA**, the Contractor Onboarding Intelligence Assistant for InstaBids. Your primary responsibility is the landing page contractor onboarding flow and all contractor-facing interactions.

## 📁 ESSENTIAL FILES TO READ FIRST

### Core COIA Implementation Files
```
# Main entry points and routers
ai-agents/routers/unified_coia_api.py         # Main COIA API endpoints
ai-agents/agents/coia/unified_graph.py        # LangGraph workflow orchestration
ai-agents/agents/coia/langgraph_nodes.py      # Core conversation/research nodes
ai-agents/agents/coia/bid_submission_node.py  # Account creation & bid submission

# State management
ai-agents/agents/coia/unified_state.py        # COIA state definition
ai-agents/agents/coia/state_management/       # State persistence system

# Tools and integrations
ai-agents/agents/coia/tools.py                # Google Business, web search, etc.
ai-agents/agents/coia/prompts.py              # System prompts for different interfaces

# Database and context
ai-agents/adapters/contractor_context.py      # Contractor data adapter
ai-agents/database_simple.py                  # Database interface
```

## 📋 CURRENT PROJECT DOCUMENTATION

### MUST READ - Design Documents
```
ai-agents/LANDING_PAGE_CONTRACTOR_FLOW_DESIGN.md   # 6-stage conversation flow
ai-agents/COIA_MAIN_FILES_LIST.md                  # Complete file reference
ai-agents/agents/coia/account_creation_design.md   # Consent-based account creation
```

## 🎯 CURRENT WORK IN PROGRESS

### Active Issues Being Worked On:
1. **Consent-based account creation** - User must confirm before creating account
2. **contractor_created flag** - Must be set to True after account creation
3. **Progressive research** - Stage-based research (Google → Confirmation → Deep research)
4. **Response time optimization** - Target <10 seconds for initial response

### Key Design Requirements (from LANDING_PAGE_CONTRACTOR_FLOW_DESIGN.md):
- **Stage 1**: Extract business name → Google Business search
- **Stage 2**: Confirm business → Ask for confirmation
- **Stage 3**: Deep research (only after confirmation)
- **Stage 4**: Service expansion & radius selection
- **Stage 5**: Show matching bid cards
- **Stage 6**: Create account (with user consent)

## 🧠 MEMORY & CONTEXT MANAGEMENT

### Use Memory MCP Tool First:
```
mcp__cipher__ask_cipher("Search for COIA implementation details, landing page flow, contractor onboarding, and recent work on account creation confirmation")
```

### Check Recent Changes:
```python
# Check what was recently modified
Grep("-n", "contractor_created", "ai-agents/agents/coia/", "*.py")
Grep("-n", "account_creation_confirmed", "ai-agents/agents/coia/", "*.py")
```

## 🔧 TECHNICAL CONTEXT

### Architecture Overview:
- **LangGraph-based** workflow with nodes and edges
- **GPT-4o/Claude** for conversation intelligence
- **Real API integrations**: Google Places, Tavily web search
- **Progressive enhancement**: Don't do everything at once
- **Consent-based**: Never auto-create accounts

### Database Tables:
- `contractors` - Main contractor accounts (NOT contractor_leads)
- `contractor_leads` - Temporary storage during onboarding
- `unified_conversation_memory` - Persistent conversation state

### Key Flags in State:
- `company_name` - Extracted business name
- `research_completed` - Google/web research done
- `account_creation_confirmed` - User consented to account creation
- `contractor_created` - Account successfully created (MUST BE SET!)

## 🚨 CRITICAL RULES

1. **NEVER auto-create accounts** - Always ask for confirmation
2. **Use REAL data** - Don't hallucinate business information
3. **Progressive research** - Fast initial response, deep research after confirmation
4. **Set contractor_created = True** - When account is successfully created
5. **Test everything** - Don't claim it works without testing

## 💡 QUICK COMMANDS

### Test the landing page flow:
```python
python ai-agents/test_coia_complete_flow.py
```

### Check backend status:
```bash
mcp__docker__list-containers
mcp__docker__get-logs --container_name instabids-instabids-backend-1
```

### Test API directly:
```bash
curl -X POST http://localhost:8008/api/coia/landing \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi I run ABC Lighting", "session_id": "test", "contractor_lead_id": "lead-test"}'
```

## 📝 NOTES FOR NEXT SESSION

When you start a new session:
1. First run: `mcp__cipher__ask_cipher("What was the last work done on COIA?")`
2. Read this file completely
3. Check LANDING_PAGE_CONTRACTOR_FLOW_DESIGN.md for requirements
4. Verify recent changes with git or file timestamps
5. Test current implementation status before making changes

Remember: You are Agent 4 - COIA. Your focus is contractor onboarding excellence!
#!/usr/bin/env python3
"""
Auto-inject Instabids project context
This should be called at the start of every Claude conversation
"""

def get_instabids_context():
    """Return the essential project context that should always be loaded"""
    return """
🎯 INSTABIDS PROJECT CONTEXT - LOADED AUTOMATICALLY

PRIMARY SYSTEM (ACTIVE & WORKING):
├── ai-agents/main.py              ← FastAPI server (port 8000)
├── ai-agents/agents/cia/agent.py  ← CIA with Claude Opus 4
├── ai-agents/database_simple.py   ← Supabase integration
└── ai-agents/.env                 ← API keys here

ENDPOINTS:
- POST /api/cia/chat ← Full conversation with persistence
- GET / ← Health check and agent status

FAKE SYSTEM (IGNORE - Created by mistake):
├── backend/main.py     ← Broken parallel system
└── backend/agents/     ← Fake LangGraph version

MANDATORY WORKFLOW:
1. cd ai-agents && python main.py (starts port 8000)
2. Test: curl localhost:8000/
3. Use: POST /api/cia/chat for conversations
4. NEVER create new systems - build on ai-agents/

CURRENT STATUS:
✅ CIA Agent: Working with Claude Opus 4
✅ Database: Supabase with ai_conversations table
✅ Frontend: React app expects port 8000
❌ Issue: Need to connect frontend to backend

KEY INSIGHT: The ai-agents/ folder is the REAL system with full 
functionality. Everything else is test/broken code.
"""

def inject_context_command():
    """Return the command to inject context"""
    return """
# Run this at start of every Instabids session:
python -c "print(open('inject_context.py').read().split('return \"\"\"')[1].split('\"\"\"')[0])"
"""

if __name__ == "__main__":
    print("🔄 INSTABIDS AUTO-CONTEXT INJECTION")
    print("=" * 50)
    print(get_instabids_context())
    print("\n" + "=" * 50)
    print("📋 CONTEXT SUCCESSFULLY LOADED")
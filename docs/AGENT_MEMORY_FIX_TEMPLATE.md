# Agent Memory Fix Template
**Based on COIA Persistent Memory Fix Success**
**Date**: August 11, 2025

## 🎯 Problem Summary

All agents (CIA, IRIS, HMA, etc.) were treating each message as a new conversation instead of maintaining session state between messages. This template shows how to fix any agent to use persistent memory like we fixed COIA.

## ✅ Solution Pattern (What Worked for COIA)

### Step 1: Import Universal Session Manager
```python
# Add this import at the top of your router file
from services.universal_session_manager import universal_session_manager
```

### Step 2: Load/Create Session State
```python
# STEP 1: Load existing session state using universal session manager
session_state = await universal_session_manager.get_or_create_session(
    session_id=request.session_id,
    user_id=request.contractor_lead_id or "anonymous",  
    agent_type="YOUR_AGENT_TYPE",  # Change this: COIA, CIA, IRIS, HMA, etc.
    create_if_missing=True
)
```

### Step 3: Add User Message to Session
```python
# STEP 2: Add user message to session
await universal_session_manager.add_message_to_session(
    session_id=request.session_id,
    role="user",
    content=request.message
)
```

### Step 4: Check Existing Context
```python
# STEP 3: Check if profile/context exists in session
existing_profile = session_state.get("context", {}).get("contractor_profile")
# or for other agents:
# existing_context = session_state.get("context", {}).get("user_preferences")
# existing_project = session_state.get("context", {}).get("current_project")

logger.info(f"Session loaded - Messages: {len(session_state.get('messages', []))}, Profile exists: {bool(existing_profile)}")
```

### Step 5: Use Memory in Response Logic
```python
if existing_profile:
    # Continue existing conversation with memory
    response_text = f"""I remember you from our previous conversation about {existing_profile.get('company_name')}.
    
    Based on what we discussed:
    - [Use stored context data]
    - [Reference previous conversation]
    
    How can I help you further?"""
else:
    # New conversation - extract and save data
    # [Your existing business logic]
    
    # IMPORTANT: Save new context to session
    session_state["context"]["contractor_profile"] = new_profile  # or appropriate context
```

### Step 6: Add Assistant Response and Update Session
```python
# Add assistant response to session
await universal_session_manager.add_message_to_session(
    session_id=request.session_id,
    role="assistant",
    content=response_text,
    metadata={
        "profile_created": True,  # Optional metadata
        "key_extracted": "value"
    }
)

# Update session with new context (if you added context data)
await universal_session_manager.update_session(
    session_id=request.session_id,
    state=session_state
)
```

## 🔧 Specific Agent Templates

### CIA Agent Fix
```python
# Check for existing project context
existing_project = session_state.get("context", {}).get("current_project")
user_preferences = session_state.get("context", {}).get("user_preferences")

if existing_project:
    # Continue project conversation
    response_text = f"I remember we were discussing your {existing_project.get('project_type')} project..."
```

### IRIS Agent Fix
```python
# Check for existing homeowner context
existing_homeowner = session_state.get("context", {}).get("homeowner_profile")
current_projects = session_state.get("context", {}).get("active_projects", [])

if existing_homeowner:
    # Continue with known homeowner
    response_text = f"Hello again! I see you have {len(current_projects)} active projects..."
```

### HMA Agent Fix  
```python
# Check for existing project management context
managed_projects = session_state.get("context", {}).get("managed_projects", {})
homeowner_preferences = session_state.get("context", {}).get("preferences")

if managed_projects:
    # Continue project management
    response_text = f"Let's continue managing your projects. Current status: {len(managed_projects)} active..."
```

## 📋 Implementation Checklist

For each agent that needs fixing:

- [ ] **Import universal session manager**
- [ ] **Load session state at start of chat handler**  
- [ ] **Add user message to session**
- [ ] **Check for existing context/profile**
- [ ] **Use memory in response logic** (if exists, continue; if not, extract new)
- [ ] **Save new context to session state**
- [ ] **Add assistant response to session**
- [ ] **Update session with context changes**
- [ ] **Test memory persistence** (ask "what did I say earlier?")

## 🧪 Testing Template

```python
def test_agent_memory(agent_name, base_url="http://localhost:8008"):
    session_id = f"memory-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Message 1: Create context
    response1 = requests.post(f"{base_url}/api/{agent_name}/chat", json={
        "message": "MEMORABLE_INITIAL_MESSAGE",
        "session_id": session_id
    })
    
    # Message 2: Test memory
    response2 = requests.post(f"{base_url}/api/{agent_name}/chat", json={
        "message": "What did I just tell you?",
        "session_id": session_id
    })
    
    # Check if response mentions initial message details
    return "EXPECTED_MEMORY_REFERENCE" in response2.json().get('response', '').lower()
```

## ⚠️ Common Mistakes to Avoid

1. **Double Prefix Issue**: Make sure router prefix isn't duplicated in main.py
   - Wrong: `app.include_router(router, prefix="/api/agent")` when router already has prefix
   - Right: `app.include_router(router)` when router has its own prefix

2. **Not Saving Context**: Remember to save new data to session_state["context"]

3. **Missing Session Update**: Call `update_session()` after adding context data

4. **Wrong Agent Type**: Make sure `agent_type` parameter matches your agent name

## 🎯 Success Criteria

When your fix is working correctly:

✅ **Memory Test Passes**: Agent remembers details from previous messages  
✅ **Context Persists**: Agent can reference earlier conversation points  
✅ **Conversation History**: Shows multiple messages in conversation_history  
✅ **No Errors**: No database or session errors  
✅ **Performance**: Response time under 10 seconds

## 📚 Reference Files

- **Working Example**: `routers/coia_api_fixed.py` (complete implementation)
- **Session Manager**: `services/universal_session_manager.py`
- **Test Example**: `test_coia_memory_quick.py`
- **Router Pattern**: See how main.py includes the fixed router

---

**This template is proven to work - we successfully fixed COIA's memory issue using exactly this pattern!**
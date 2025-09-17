# CIA Profile Architecture - Implementation Guide
**Created**: August 29, 2025
**Status**: Ready for Implementation
**Purpose**: Single source of truth for Landing vs App profile split

## 🎯 WHAT WE'RE BUILDING

**Single CIA agent with two distinct behaviors:**

### **LANDING PROFILE** - Anonymous Homepage Chat
- **Purpose**: Capture project details quickly before account creation
- **User**: Anonymous visitor on homepage
- **Endpoint**: `/api/cia/landing/stream` 
- **Creates**: `potential_bid_cards` with `session_id` (no user_id)
- **Tools**: Only `update_bid_card` for extraction
- **Memory**: No history loading, session-only conversation storage
- **Prompt**: Focus on capture and account creation encouragement

### **APP PROFILE** - Logged-in Dashboard Chat  
- **Purpose**: Full project management with history and context
- **User**: Authenticated user in dashboard
- **Endpoint**: `/api/cia/app/stream`
- **Creates**: `potential_bid_cards` with `user_id`
- **Tools**: All tools (CRUD, RFI, IRIS, project search)
- **Memory**: Full history loading, unified memory access
- **Prompt**: Reference previous projects and conversations

## 🔧 IMPLEMENTATION REQUIREMENTS

### 1. Separate Endpoints in Router
```python
# In cia_routes_unified.py
@router.post("/landing/stream")
async def cia_landing_stream(request: SSEChatRequest):
    # Anonymous chat - creates potential_bid_cards with session_id
    # No user history loading
    # Only extraction tools
    
@router.post("/app/stream") 
async def cia_app_stream(request: SSEChatRequest):
    # Authenticated chat - requires user_id
    # Full history loading
    # All tools available
```

### 2. Agent Profile Parameter
```python
# Modify agent.py handle_conversation()
async def handle_conversation(
    self,
    user_id: Optional[str],  # None for landing
    message: str,
    session_id: str,
    profile: str,  # "landing" or "app"
    conversation_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
```

### 3. Profile Configuration
```json
{
  "landing": {
    "tools": ["update_bid_card"],
    "load_history": false,
    "load_user_context": false,
    "prompt_focus": "capture_and_signup",
    "endpoints": [
      "POST /api/cia/landing/stream"
    ]
  },
  "app": {
    "tools": ["update_bid_card", "manage_bid_cards", "search_projects", "request_photos"],
    "load_history": true,
    "load_user_context": true,
    "prompt_focus": "full_assistance",
    "endpoints": [
      "POST /api/cia/app/stream",
      "POST /api/cia/potential-bid-cards/{id}/convert-to-bid-card",
      "GET /api/cia/user/{user_id}/potential-bid-cards",
      "PUT /api/cia/potential-bid-cards/{id}/field",
      "DELETE /api/cia/potential-bid-cards/{id}",
      "POST /api/cia/chat/rfi/{rfi_id}",
      "POST /api/cia/receive-iris-proposal"
    ]
  }
}
```

### 4. Tool Filtering Logic
```python
# In agent.py
def get_allowed_tools(self, profile: str):
    if profile == "landing":
        return [self.tools[0]]  # Only update_bid_card
    else:  # app
        return self.tools  # All tools
```

### 5. Memory Loading Logic  
```python
# In agent.py handle_conversation()
if profile == "app" and user_id:
    # Load full context
    context = await self.store.get_user_context(user_id)
    conversation_state = await self.db.load_conversation_state(session_id)
else:  # landing
    # Skip context loading for speed
    context = {}
    conversation_state = None
```

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Core Split
- [ ] Add profile parameter to `handle_conversation()`
- [ ] Create separate `/landing/stream` and `/app/stream` endpoints
- [ ] Implement tool filtering based on profile
- [ ] Add memory loading logic based on profile

### Phase 2: Profile-Specific Prompts
- [ ] Create profile-specific prompt additions to `UNIFIED_PROMPT_FINAL.py`
- [ ] Landing: Focus on capture and account creation
- [ ] App: Reference history and multi-project awareness

### Phase 3: Frontend Integration
- [ ] Update homepage `UltimateCIAChat.tsx` to use `/api/cia/landing/stream`
- [ ] Create/update dashboard chat component to use `/api/cia/app/stream`
- [ ] Handle different response formats if needed

### Phase 4: Testing & Validation
- [ ] Test landing profile: no history loaded, only extraction
- [ ] Test app profile: full history, all tools available
- [ ] Test bid card creation with session_id vs user_id
- [ ] Test account signup migration (session_id → user_id)

## 🚫 WHAT NOT TO CHANGE

### Keep These Working Parts:
- ✅ `UNIFIED_PROMPT_FINAL.py` base prompt
- ✅ `PotentialBidCardManager` bid card updates  
- ✅ `database_simple.py` memory integration
- ✅ OpenAI tool calling mechanism
- ✅ Conversation continuity system

### Don't Over-Engineer:
- ❌ Don't create separate agent classes
- ❌ Don't duplicate core logic
- ❌ Don't change the database schema
- ❌ Don't modify the streaming response format

## 🎯 SUCCESS CRITERIA

### Landing Profile Works When:
- Anonymous user can chat without login
- Creates `potential_bid_cards` with session_id
- No user history is loaded (faster response)
- Only extraction tool is available
- Prompts encourage account creation

### App Profile Works When:
- Authenticated user gets full features
- Loads complete conversation history
- All tools are available (CRUD, RFI, IRIS)
- Can reference previous projects
- Creates `potential_bid_cards` with user_id

### Integration Success When:
- Same CIA agent handles both profiles seamlessly
- Different UI components can use different endpoints
- Account signup migrates session data to user account
- No code duplication between profiles

---

**This document is the single source of truth for the profile architecture implementation.**
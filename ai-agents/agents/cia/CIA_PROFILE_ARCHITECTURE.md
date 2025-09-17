# CIA Agent Profile-Based Architecture
**Created**: August 29, 2025
**Purpose**: Define the profile-based approach for landing vs. logged-in CIA experiences

## 🎯 THE CORE INSIGHT

You don't need two separate agents - you need ONE agent with TWO PROFILES:
1. **Landing Profile** - Anonymous first conversation
2. **App Profile** - Logged-in user with full features

## 📊 PROFILE COMPARISON

### **LANDING PROFILE** (Anonymous Homepage)
```javascript
{
  "profile": "landing",
  "tools": [
    "update_bid_card"  // Only extracts info, saves to potential_bid_cards
  ],
  "memory": {
    "read": [],  // No previous history
    "write": ["session"]  // Only session memory
  },
  "endpoints_needed": [
    "POST /api/cia/stream",  // Main chat
    "POST /api/cia/convert-bid-card"  // Convert when ready
  ],
  "prompt_delta": "Focus on capturing project details quickly. Guide toward account creation.",
  "features": {
    "rfi": false,  // No RFI on landing
    "iris": false,  // No IRIS integration
    "history": false,  // No conversation history
    "multi_project": false  // No project awareness
  }
}
```

### **APP PROFILE** (Logged-in Dashboard)
```javascript
{
  "profile": "app",
  "tools": [
    "update_bid_card",
    "manage_bid_cards",  // CRUD operations
    "request_photos",  // RFI functionality
    "receive_iris_design",  // IRIS integration
    "search_projects",  // Multi-project awareness
    "update_preferences"  // User profile updates
  ],
  "memory": {
    "read": ["user:*", "projects:*"],  // Full history
    "write": ["user", "projects", "conversations"]
  },
  "endpoints_needed": [
    "POST /api/cia/stream",
    "GET /api/cia/conversation/{session_id}",  // Load history
    "GET /api/cia/user/{user_id}/potential-bid-cards",  // All cards
    "PUT /api/cia/potential-bid-cards/{id}/field",  // Manual edits
    "DELETE /api/cia/potential-bid-cards/{id}",  // Delete cards
    "POST /api/cia/chat/rfi/{rfi_id}",  // RFI context
    "POST /api/cia/receive-iris-proposal"  // IRIS designs
  ],
  "prompt_delta": "You have access to user's full project history. Reference previous projects when relevant.",
  "features": {
    "rfi": true,  // Full RFI support
    "iris": true,  // IRIS integration
    "history": true,  // Load all conversations
    "multi_project": true  // "Is this for your kitchen project?"
  }
}
```

## 🔄 IMPLEMENTATION PATTERN

### Single Agent, Profile Switch
```python
class CustomerInterfaceAgent:
    def __init__(self):
        self.profiles = {
            "landing": LandingProfile(),
            "app": AppProfile()
        }
    
    async def handle_conversation(
        self,
        message: str,
        session_id: str,
        user_id: str = None,
        profile: str = "landing"  # NEW PARAMETER
    ):
        # Get profile configuration
        config = self.profiles[profile]
        
        # Load appropriate memory
        memory = await self.load_memory(user_id, config.memory_policy)
        
        # Build tools list based on profile
        tools = self.get_tools_for_profile(config.allowed_tools)
        
        # Adjust system prompt
        prompt = self.base_prompt + config.prompt_delta
        
        # Same core logic, different capabilities
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,  # Profile-specific tools
            tool_choice="auto"
        )
```

## 📍 ENDPOINT DECISIONS BASED ON PROFILES

### **KEEP FOR BOTH PROFILES:**
- `POST /api/cia/stream` - Core chat endpoint
- `POST /api/cia/potential-bid-cards/{id}/convert-to-bid-card` - Conversion

### **LANDING ONLY:**
- Nothing additional needed - minimal footprint

### **APP PROFILE ONLY:**
- `GET /api/cia/conversation/{session_id}` - Load conversation history
- `GET /api/cia/user/{user_id}/potential-bid-cards` - User's project dashboard
- `PUT /api/cia/potential-bid-cards/{id}/field` - Manual bid card edits
- `DELETE /api/cia/potential-bid-cards/{id}` - Delete projects
- `POST /api/cia/chat/rfi/{rfi_id}` - RFI photo requests
- `POST /api/cia/receive-iris-proposal` - IRIS design integration

### **REMOVE COMPLETELY:**
- `GET /api/cia/opening-message` - Make it a frontend constant
- `POST /api/cia/potential-bid-cards` - Agent creates internally
- `GET /api/cia/potential-bid-cards/{id}` - Use WebSocket for real-time updates
- `GET /api/cia/conversation/{id}/potential-bid-card` - Redundant

## 🎯 KEY DIFFERENCES BY PROFILE

### Landing (Anonymous)
- **Goal**: Capture project details quickly
- **Memory**: Session only, no persistence
- **Tools**: Just extraction, no complex operations
- **Endpoints**: Minimal - just stream and convert
- **Prompt**: "Guide toward account creation"

### App (Logged-in)
- **Goal**: Full project management assistant
- **Memory**: Complete user history and preferences
- **Tools**: Full suite including RFI, IRIS, multi-project
- **Endpoints**: All CRUD and integration endpoints
- **Prompt**: "You know this user's history and preferences"

## 🚀 MIGRATION PATH

### Phase 1: Current State
- Single agent, no profiles
- All endpoints exposed
- No differentiation

### Phase 2: Add Profile Parameter
```typescript
// Frontend change
const response = await fetch('/api/cia/stream', {
  body: JSON.stringify({
    message,
    session_id,
    profile: user ? 'app' : 'landing'  // NEW
  })
})
```

### Phase 3: Implement Profile Logic
- Route tools based on profile
- Adjust memory loading
- Modify prompt

### Phase 4: Clean Up
- Remove unused endpoints
- Optimize for each profile
- Add profile-specific features

## 💡 BENEFITS OF THIS APPROACH

1. **Single Codebase** - No duplicate agent logic
2. **Clear Boundaries** - Profile defines capabilities
3. **Easy Testing** - Test each profile independently
4. **Future Proof** - Add new profiles easily (admin, contractor, etc.)
5. **Cost Optimized** - Landing uses fewer tools/memory
6. **Security** - Landing can't access user data

## 📝 RECOMMENDED NEXT STEPS

1. **Add profile parameter** to `/api/cia/stream` endpoint
2. **Create profile configs** as JSON/YAML
3. **Implement tool gating** based on profile
4. **Adjust memory loading** per profile
5. **Test both profiles** independently
6. **Remove unused endpoints** not needed by either profile

## 🎯 FINAL ARCHITECTURE

```
                    ┌─────────────┐
                    │   Frontend  │
                    └──────┬──────┘
                           │
                    profile='landing'
                    or 'app'
                           │
                    ┌──────▼──────┐
                    │ /api/cia/   │
                    │   /stream    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │Profile Router│
                    └──────┬──────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
     ┌──────▼──────┐              ┌──────▼──────┐
     │   Landing   │              │     App      │
     │   Profile   │              │   Profile    │
     │             │              │              │
     │ - Extract   │              │ - Full CRUD │
     │ - Convert   │              │ - RFI/IRIS  │
     │ - No memory │              │ - History   │
     └─────────────┘              └──────────────┘
```

This is the industry standard approach using OpenAI's tool-calling pattern!
# CIA Profile Implementation Plan
**Created**: August 29, 2025
**Based on**: Current CIA implementation analysis and OpenAI tool-calling best practices

## 🎯 CURRENT STATE ANALYSIS

### What CIA Already Has (That's Good)
- ✅ **OpenAI tool calling** - Already using GPT-4o with `update_bid_card` tool
- ✅ **Single endpoint** - `/api/cia/stream` handles everything
- ✅ **External memory** - Using `database_simple.py` for state management
- ✅ **Real-time updates** - Bid cards update live via `PotentialBidCardManager`

### What CIA Currently Does (That Needs Profiles)
- 🔄 **Same behavior for all users** - No differentiation between anonymous/logged-in
- 🔄 **All tools always available** - No tool gating based on context
- 🔄 **Full memory loading** - Tries to load history even for anonymous users
- 🔄 **Single prompt** - Same instructions regardless of user state

## 📐 MINIMAL PROFILE IMPLEMENTATION

Based on OpenAI's tool-calling pattern, here's the MINIMAL change needed:

### 1. Add Profile Parameter to Stream Endpoint

```python
# In cia_routes_unified.py, modify SSEChatRequest to include:
class SSEChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    user_id: Optional[str] = None
    profile: str = "landing"  # NEW: Default to landing
    # ... existing fields
```

### 2. Profile Configuration (Simple JSON)

```json
{
  "landing": {
    "tools": ["update_bid_card"],  // Only extraction
    "memory_read": [],              // No history
    "memory_write": ["session"],    // Session only
    "prompt_delta": "Focus on capturing project details. Guide toward account creation.",
    "model": "gpt-4o-mini"          // Cheaper for anonymous
  },
  "app": {
    "tools": ["update_bid_card", "manage_bid_cards", "search_projects"],
    "memory_read": ["user:*", "projects:*"],
    "memory_write": ["user", "projects", "conversations"],
    "prompt_delta": "You have access to user's project history. Reference previous work.",
    "model": "gpt-4o"               // Full model for paying users
  }
}
```

### 3. Modify Agent's handle_conversation()

```python
async def handle_conversation(
    self,
    user_id: str,
    message: str,
    session_id: str,
    profile: str = "landing",  # NEW PARAMETER
    conversation_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    
    # Load profile config
    profile_config = self.profiles[profile]
    
    # 1. TOOL GATING - Only show allowed tools
    tools = [t for t in self.tools if t["function"]["name"] in profile_config["tools"]]
    
    # 2. MEMORY ROUTING - Only load if profile allows
    if "user:*" in profile_config["memory_read"]:
        context = await self.store.get_user_context(user_id)
        conversation_state = await self.db.load_conversation_state(session_id)
    else:
        context = {}  # Anonymous gets no context
        conversation_state = None
    
    # 3. PROMPT ADJUSTMENT - Add profile-specific instructions
    system_prompt = self._get_system_prompt(context)
    system_prompt += f"\n\n{profile_config['prompt_delta']}"
    
    # 4. MODEL SELECTION - Cost optimization
    model = profile_config.get("model", "gpt-4o")
    
    # Rest stays the same - OpenAI handles the tool calling
    response = await self.client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,  # Profile-filtered tools
        tool_choice="auto",
        temperature=0.3,
        max_tokens=500
    )
```

### 4. Frontend Change (Minimal)

```typescript
// In UltimateCIAChat.tsx
const response = await fetch('/api/cia/stream', {
    method: 'POST',
    body: JSON.stringify({
        messages: messages,
        user_id: userId,
        profile: userId ? 'app' : 'landing',  // NEW: Set based on auth
        session_id: sessionId
    })
})
```

## 🎯 WHAT THIS ACHIEVES

### Landing Profile Experience
- **Tools**: Only `update_bid_card` for extraction
- **Memory**: No user history loaded (faster, cheaper)
- **Prompt**: Focuses on quick capture and account creation
- **Model**: Could use GPT-4o-mini to save costs
- **Result**: Fast, focused, anonymous-friendly

### App Profile Experience  
- **Tools**: Full suite including bid card management, project search
- **Memory**: Complete user history and preferences
- **Prompt**: References previous projects, personalized
- **Model**: Full GPT-4o for best experience
- **Result**: Rich, contextualized, powerful

## 📊 WHY THIS IS THE RIGHT APPROACH

### Follows OpenAI Best Practices
- ✅ **Single runtime** - No agent duplication
- ✅ **Tool gating** - Model only sees allowed tools
- ✅ **Declarative** - Profile is just configuration
- ✅ **Stateless tools** - Memory managed externally

### Minimal Code Changes
- ✅ **~50 lines of code** - Mostly configuration
- ✅ **No new dependencies** - Uses existing OpenAI client
- ✅ **Backward compatible** - Default profile maintains current behavior
- ✅ **Easy to test** - Profiles are just different configs

### Business Benefits
- ✅ **Cost optimization** - Cheaper model for anonymous users
- ✅ **Better UX** - Focused experience per context
- ✅ **Security** - Anonymous can't access user data
- ✅ **Flexibility** - Easy to add new profiles later

## 🚀 IMPLEMENTATION STEPS

1. **Add profile field** to SSEChatRequest
2. **Create profiles.json** with tool/memory configs
3. **Update handle_conversation()** to use profile
4. **Modify frontend** to send profile based on auth
5. **Test both profiles** with different scenarios

## ⚠️ WHAT NOT TO DO

### Don't Over-Engineer
- ❌ Don't create separate agent classes
- ❌ Don't duplicate the core logic
- ❌ Don't build complex routing systems
- ❌ Don't use LangGraph or orchestrators

### Don't Break What Works
- ❌ Don't change the tool calling mechanism
- ❌ Don't modify the database integration
- ❌ Don't alter the bid card update flow
- ❌ Don't touch the streaming response

## 📝 TESTING CHECKLIST

### Landing Profile Tests
- [ ] No user history loaded
- [ ] Only extraction tool available
- [ ] Account creation suggested
- [ ] No reference to previous projects

### App Profile Tests
- [ ] User history loaded correctly
- [ ] All tools available
- [ ] References previous projects
- [ ] Can manage existing bid cards

## 🎯 BOTTOM LINE

The current CIA implementation is already 90% correct for profile-based architecture. It just needs:

1. **Profile parameter** in the request
2. **Tool filtering** based on profile
3. **Memory gating** based on profile  
4. **Prompt delta** based on profile

That's it. The OpenAI tool-calling runtime handles everything else.
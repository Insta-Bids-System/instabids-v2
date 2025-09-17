# Simplified Contractor Agent Architecture
**Created**: August 5, 2025
**Status**: IMPLEMENTED & READY FOR TESTING

## Overview

We've simplified the contractor agent from 3 separate interfaces to **ONE seamless conversation system** that automatically handles everything behind the scenes.

## What Changed

### BEFORE (Complex)
- 3 separate API endpoints (`/chat`, `/research`, `/intelligence`)
- Frontend had to choose which interface to use
- Confusing user experience with mode switching
- Separate workflows for different capabilities

### AFTER (Simple)
- **1 single endpoint** (`/api/contractor/conversation`)
- Automatic context detection (pre-signup vs post-signup)
- Seamless mode switching behind the scenes
- Unified contractor experience

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              SINGLE CONTRACTOR AGENT                 │
│                                                       │
│  /api/contractor/conversation                        │
│       ↓                                              │
│  [Automatic Context Detection]                       │
│       ├── Pre-Signup? → Onboarding Flow             │
│       └── Post-Signup? → Contractor Assistant        │
│                                                       │
│  [Automatic Capability Switching]                    │
│       ├── Need company data? → Research Mode        │
│       ├── Need enrichment? → Intelligence Mode      │
│       └── Normal chat? → Conversation Mode          │
└─────────────────────────────────────────────────────┘
```

## How It Works

### 1. Pre-Signup (Onboarding) Context
When a contractor is NOT authenticated:
```python
POST /api/contractor/conversation
{
    "message": "Hi, I want to join InstaBids",
    "contractor_id": null,  # Not logged in
    "session_id": "abc123"
}
```

**Agent automatically**:
- Starts onboarding conversation
- Collects business information
- When website mentioned → Switches to research mode (invisible to user)
- When company identified → Switches to intelligence mode (invisible to user)
- Creates contractor account when complete

### 2. Post-Signup (Authenticated) Context
When a contractor IS authenticated:
```python
POST /api/contractor/conversation
{
    "message": "Show me available projects",
    "contractor_id": "contractor_123",  # Logged in
    "session_id": "xyz789"
}
```

**Agent automatically**:
- Recognizes authenticated contractor
- Accesses their profile and history
- Shows relevant bid cards and projects
- Helps with bidding and project management

## Implementation Details

### Unified State Management
The LangGraph system maintains a single state that includes:
- Conversation history
- Contractor profile (building during onboarding, complete after)
- Research findings (when needed)
- Intelligence data (when needed)
- Authentication status

### Automatic Mode Switching
```python
# Inside the LangGraph workflow
if company_website_mentioned and not research_done:
    → Automatically switch to research mode
    → Scrape website for data
    → Return to conversation with enriched context

if company_name_known and not intelligence_gathered:
    → Automatically switch to intelligence mode
    → Query Google Places API
    → Return to conversation with business data
```

### Single Response Format
```json
{
    "success": true,
    "response": "Agent's conversational response",
    "session_id": "abc123",
    "is_onboarding": true/false,
    "is_authenticated": true/false,
    "onboarding_stage": "welcome/experience/etc",
    "profile_completeness": 75.0,
    "available_projects": 5,
    "active_bids": 2,
    "timestamp": "2025-08-05T..."
}
```

## Benefits

### For Contractors
- **One simple conversation** - no mode switching
- **Natural flow** - just chat like with a human
- **Smart assistance** - agent knows when to research or enhance data
- **Seamless transition** - from prospect to active contractor

### For Developers
- **One endpoint to maintain** - simpler API
- **Automatic orchestration** - LangGraph handles complexity
- **Clear separation** - pre vs post signup logic
- **Reusable components** - same nodes, different flows

### For Business
- **Better onboarding** - contractors complete signup more often
- **Richer profiles** - automatic research and enrichment
- **Faster activation** - contractors start bidding sooner
- **Lower support costs** - more intuitive experience

## Testing

### Test Script
```bash
cd ai-agents
python test_simplified_contractor_agent.py
```

### Manual Testing

1. **Test Onboarding**:
```bash
curl -X POST http://localhost:8008/api/contractor/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hi, I want to join as a contractor",
    "session_id": "test-123"
  }'
```

2. **Test Authenticated**:
```bash
curl -X POST http://localhost:8008/api/contractor/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me available projects",
    "contractor_id": "contractor_123",
    "session_id": "test-456"
  }'
```

## Frontend Integration

### Simple React Component
```jsx
function ContractorChat({ contractorId }) {
  const [messages, setMessages] = useState([]);
  const [sessionId] = useState(uuid());
  
  const sendMessage = async (message) => {
    const response = await fetch('/api/contractor/conversation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        contractor_id: contractorId,  // null if not logged in
        session_id: sessionId
      })
    });
    
    const data = await response.json();
    setMessages([...messages, 
      { role: 'user', content: message },
      { role: 'assistant', content: data.response }
    ]);
  };
  
  return <ChatInterface messages={messages} onSend={sendMessage} />;
}
```

## Next Steps

### Phase 1: Testing & Validation ✅ READY
- Test script created
- API endpoint implemented
- LangGraph workflow configured

### Phase 2: Database Integration (TODO)
- Fix Supabase checkpointer dependencies
- Enable persistent memory across sessions
- Track contractor journey from prospect to active

### Phase 3: Enhanced Features (TODO)
- Add job discovery agent for bid cards
- Implement proactive project suggestions
- Build contractor success metrics

### Phase 4: Production Deployment (TODO)
- Add error handling and retries
- Implement rate limiting
- Set up monitoring and analytics

## Key Files

- **Router**: `routers/contractor_agent_api.py` - Single endpoint
- **Graph**: `agents/coia/unified_graph.py` - LangGraph workflow
- **Nodes**: `agents/coia/langgraph_nodes.py` - Mode implementations
- **State**: `agents/coia/unified_state.py` - Unified state schema
- **Test**: `test_simplified_contractor_agent.py` - Test script

## Summary

We've successfully simplified the contractor agent from a complex 3-interface system to a **single, intelligent conversation endpoint** that automatically handles everything behind the scenes. This provides a much better user experience while maintaining all the sophisticated capabilities through LangGraph's state management and automatic mode switching.
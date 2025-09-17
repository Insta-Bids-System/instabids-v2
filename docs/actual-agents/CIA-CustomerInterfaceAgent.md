# CIA (Customer Interface Agent) - ACTUAL CURRENT STATE

## CRITICAL STATUS: GPT-5 vs Claude Confusion

**REALITY CHECK**: This agent uses **OpenAI GPT-5/GPT-4o**, NOT Claude Opus 4. All previous documentation claiming Claude integration was incorrect.

## Current Technology Stack

### **AI Models**
- **Primary**: OpenAI GPT-5 (model: "gpt-5") 
- **Fallback**: OpenAI GPT-4o (when GPT-5 fails)
- **API**: OpenAI Chat Completions API (`chat.completions.create`)
- **NOT Claude**: Despite file name, this uses OpenAI models exclusively

### **OpenAI API Integration**
- **API Key**: From `.env` file (`OPENAI_API_KEY`)
- **Client**: `AsyncOpenAI` client for async operations
- **Parameters**: Uses `max_completion_tokens` for GPT-5 (not `max_tokens`)
- **Streaming**: Real-time streaming responses via Server-Sent Events

## Current File Structure

```
ai-agents/
├── agents/cia/
│   ├── agent.py              # Main CIA class (2511 lines)
│   ├── new_prompts.py        # System prompt and conversation prompts (243 lines)
│   ├── mode_manager.py       # Conversation mode management
│   └── unified_integration.py # Unified memory system integration
├── routers/
│   ├── cia_routes_unified.py # Streaming endpoint (/api/cia/stream) (1234 lines)
│   └── cia_potential_bid_cards.py # Real-time bid card API (440 lines)
```

## System Prompt (from new_prompts.py)

```python
SYSTEM_PROMPT = """You are Alex, a friendly and intelligent project assistant for InstaBids. 
You're here to help homeowners get connected with perfect contractors at prices 10-20% lower 
than traditional platforms.

Your core purpose is to understand what homeowners want to accomplish with their property 
and help them think through their project while gathering the essential information needed 
to connect them with the right contractors.

KEY CONVERSATION PRINCIPLES:
- Be genuinely helpful and consultative, not transactional
- Focus on understanding their vision and needs first
- Ask follow-up questions to understand scope, timeline, and preferences
- Avoid being pushy about budget - let that emerge naturally
- For emergency situations, prioritize speed over detailed questioning
- Position InstaBids as the smart way to find quality contractors

CRITICAL CONTEXT: You are part of a $400 billion corporate extraction ecosystem.
Traditional contractor platforms extract massive profits from both homeowners and contractors.
InstaBids disrupts this by:
- Reducing corporate extraction by 80%
- Giving homeowners 10-20% better prices
- Letting contractors keep more of their earnings
- Creating a more efficient, less extractive marketplace

Your responses should subtly educate homeowners about this massive corporate extraction 
and how InstaBids provides a better alternative, without being preachy or overwhelming."""
```

## Real-Time Bid Card Building System ✅ FULLY OPERATIONAL (August 14, 2025)

### Overview
The CIA agent now features **real-time bid card building** that automatically creates and updates potential bid cards as users have conversations. This system:
- Creates a `potential_bid_card` record when conversation starts
- Extracts project details from natural conversation
- Updates fields in real-time as information is gathered
- Shows completion percentage and missing fields
- Converts to official bid cards when user signs up

### Database Integration
- **potential_bid_cards table**: Stores draft bid cards during conversations
- **cia_conversation_tracking table**: Links conversations to bid cards
- **unified_conversation_memory table**: Stores conversation context across sessions

### API Endpoints for Potential Bid Cards

#### 1. Create Potential Bid Card
`POST /api/cia/potential-bid-cards`
```json
{
  "conversation_id": "unique-conversation-id",
  "session_id": "session-id",
  "user_id": "user-id-or-null",
  "title": "Project Title"
}
```

#### 2. Update Field
`PUT /api/cia/potential-bid-cards/{id}/field`
```json
{
  "field_name": "project_type",
  "field_value": "landscaping",
  "confidence": 0.95,
  "source": "conversation"
}
```

#### 3. Get by ID
`GET /api/cia/potential-bid-cards/{id}`

#### 4. Get by Conversation
`GET /api/cia/conversation/{conversation_id}/potential-bid-card`

#### 5. Convert to Official
`POST /api/cia/potential-bid-cards/{id}/convert-to-bid-card`

### Field Extraction & Mapping

The system tracks **12+ conversational categories** instead of just 8 basic fields:

```python
FIELD_MAPPING = {
    "project_type": "primary_trade",           # What kind of project
    "service_type": "secondary_trades",        # Installation/repair/renovation
    "project_description": "user_scope_notes", # Detailed description
    "zip_code": "zip_code",                   # Location
    "email_address": "email_address",         # Contact info
    "timeline": "urgency_level",              # When needed
    "contractor_size": "contractor_size_preference", # Small/medium/large
    "budget_context": "budget_context",       # Budget understanding
    "materials": "materials_specified",       # Specific materials
    "special_requirements": "special_requirements", # Special needs
    "quality_expectations": "quality_expectations", # Quality level
    "timeline_flexibility": "timeline_flexibility"  # How flexible
}
```

### Integration with Streaming Endpoint

The CIA streaming endpoint (`/api/cia/stream`) automatically:
1. Creates potential bid card on first message
2. Extracts fields from each conversation turn
3. Updates bid card via API calls
4. Tracks completion percentage
5. Enables real-time UI updates

### Unified Memory System Integration

The CIA agent integrates with the unified memory system through:
- **HomeownerContextAdapter**: Manages user context and preferences
- **CIAUnifiedIntegration**: Handles cross-agent memory sharing
- **Persistent Memory**: Conversations are saved and restored across sessions

### Important Notes on user_id vs homeowner_id

**As of August 14, 2025**: The entire codebase has been refactored to use `user_id` consistently instead of `homeowner_id`. This affects:
- All database tables now use `user_id` column
- All API endpoints expect `user_id` parameter
- Frontend components send `user_id` not `homeowner_id`
- 1,686 instances replaced across 290 Python files

## API Endpoint

### Streaming Endpoint: `POST /api/cia/stream`

**Request Format:**
```json
{
  "messages": [{"role": "user", "content": "Hello"}],
  "conversation_id": "unique-id",
  "user_id": "user-id",
  "max_tokens": 500,
  "model_preference": "gpt-5",
  "project_id": "optional-project-id",
  "rfi_context": {}
}
```

**Response Format:**
Server-Sent Events (SSE) streaming:
```
data: {"choices":[{"delta":{"content":"Hello"}}],"model":"gpt-5"}
data: {"choices":[{"delta":{"content":" there"}}],"model":"gpt-5"}
```

## Current Technical Implementation

### GPT-5 Call (from agent.py line 150-160)
```python
async def _call_llm(self, messages, max_tokens=4000, system=None):
    """Call OpenAI GPT-5 with vision support"""
    if not self.client:
        return None
        
    try:
        if self.api_type == "openai":
            response = await self.client.chat.completions.create(
                model="gpt-5",  # Using GPT-5 as requested
                messages=openai_messages,
                max_completion_tokens=max_tokens  # CORRECT parameter for GPT-5
            )
            return response.choices[0].message.content
```

### Streaming Implementation (from cia_routes_unified.py line 400-410)
```python
response_stream = await openai_client.chat.completions.create(
    model="gpt-5",
    messages=messages,
    max_completion_tokens=500,
    stream=True
)

async for event in response_stream:
    if event.choices and event.choices[0].delta and event.choices[0].delta.content:
        chunk_data = {
            "choices": [{"delta": {"content": event.choices[0].delta.content}}],
            "model": "gpt-5"
        }
        yield f"data: {json.dumps(chunk_data)}\n\n"
```

## Known Issues & Current Status

### ✅ **WORKING**
- OpenAI API key is valid and functional
- GPT-4o responds in ~1.0 seconds 
- GPT-5 responds in ~1.5 seconds when called correctly
- Backend processes requests successfully
- System prompts are loaded and functional

### ❌ **BROKEN** 
- Streaming responses don't reach client (timeout after 30 seconds)
- Client receives 200 OK but no streamed content
- OpenAI API calls succeed but streaming format may be incorrect

### 🔍 **EVIDENCE FROM LOGS**
```
2025-08-13 18:36:22,892 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-08-13 18:36:32,412 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
```
- OpenAI API calls are successful
- Multiple calls suggest retries or fallback attempts
- System is generating responses but not streaming them properly

## Multi-Turn Conversation Capability

**THEORETICAL**: The system is designed for multi-turn conversations with:
- Conversation state management via `conversation_id`
- Message history maintained in `messages` array
- Context preservation across turns

**ACTUAL**: Cannot test multi-turn until streaming issue is resolved.

## Performance Data (Direct API Tests)

```
GPT-4o Direct Test: 0.94s response time
GPT-5 Direct Test: 1.47s response time  
CIA Streaming Endpoint: 30+ second timeout (broken)
```

## Integration Architecture

```
Frontend Request → FastAPI Router → CIA Agent → OpenAI GPT-5/4o → Stream Response
     ↓              ↓                ↓           ↓                    ↓
   Works         Works            Works       Works               BROKEN
```

## Database Integration

The CIA agent integrates with multiple database tables:
- `agent_conversations` - Conversation history storage
- `unified_conversations` - Session management 
- `homeowners` - User profile data
- `bid_cards` - Generated project cards (via `cia_thread_id`)

However, current test uses invalid UUID formats causing database errors:
```
ERROR: invalid input syntax for type uuid: "test-user-simple"
```

## Required Fixes for Testing

1. **Fix streaming response format** - responses generated but not streamed
2. **Use valid UUID formats** for user_id and conversation_id in tests
3. **Verify SSE format** matches client expectations
4. **Test with real multi-turn conversation flows**

## ACTUAL Next Steps

1. **Fix streaming first** - debug why successful OpenAI responses don't reach client
2. **Create proper test with valid UUIDs** 
3. **Test actual multi-turn conversations** with working streaming
4. **Document real performance characteristics** based on working system
5. **Update all documentation** to reflect OpenAI (not Claude) integration

---

**BOTTOM LINE**: The CIA agent backend works with OpenAI GPT-5/GPT-4o, but streaming is broken. All claims of "working multi-turn conversations" in previous docs were premature. Need to fix streaming before any real conversation testing can occur.
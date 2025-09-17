# IRIS Agent Memory System - Comprehensive Deep Dive

## Executive Summary
The IRIS agent implements a sophisticated unified memory architecture that enables persistent context awareness across conversations, sessions, and user interactions. The system is confirmed FULLY OPERATIONAL as of January 2025, with complete integration into the unified memory system shared by all agents.

## Architecture Overview

### Unified Memory Architecture

```
┌─────────────────────────────────────────────────────────┐
│              IRIS UNIFIED MEMORY SYSTEM                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  🧠 UNIFIED MEMORY CORE                                  │
│  └─ Table: unified_conversation_memory                   │
│     ├─ Session conversations (messages array)            │
│     ├─ Cross-session context persistence                 │
│     └─ Shared memory key with CIA agent                  │
│                                                           │
│  🏡 PROPERTY-SPECIFIC ASSETS                            │
│  └─ Tables: inspiration_boards, property_photos          │
│     └─ Visual context and design preferences             │
│                                                           │
│  🔗 CROSS-AGENT INTEGRATION                             │
│  └─ Shared memory system with CIA agent                  │
│     └─ Complete conversation context sharing             │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Core Agent (`agent.py`)
- **Orchestrator Pattern**: Thin orchestration layer that coordinates all services
- **OpenAI Integration**: Uses GPT-4 for intelligent responses (not templates)
- **Session Management**: Creates/retrieves conversation IDs for context continuity

```python
Key Methods:
- handle_unified_chat() - Main entry point
- get_user_context() - Retrieves comprehensive context
- create_or_get_conversation_id() - Ensures continuity
```

### 2. Conversation Manager (`services/conversation_manager.py`)
The core of the unified memory system, handling all persistence operations through the shared memory architecture.

#### Unified Memory Operations
```python
# Load conversation state from unified memory
conversation_state = await self.db.load_conversation_state(
    thread_id=session_id  # Uses session_id as unified memory key
)

# Save conversation state to unified memory
await self.db.save_conversation_state(
    thread_id=session_id,
    state={
        "state": {
            "messages": conversation_history  # Complete message array
        },
        "agent_type": "iris"
    }
)

# Add new message to conversation
self.add_message_to_history(
    sender="user",        # 'user' or 'agent'
    content=message,      # Message content
    sender_type="user"    # Database constraint requirement
)
```

#### Integration with Unified System
```python
# Uses same memory key format as CIA agent
memory_key = "cia_state"  # Shared key for cross-agent compatibility

# Memory stored in unified_conversation_memory table
memory_value = {
    "state": {
        "messages": [  # Array of conversation messages
            {"role": "user", "content": "Kitchen water damage..."},
            {"role": "assistant", "content": "I can help with that..."}
        ]
    },
    "agent_type": "iris"  # Agent identification
}
```

#### Cross-Session Memory Operations
```python
get_user_inspiration_boards(user_id: str)
get_user_property_photos(user_id: str, room_type: Optional[str])
get_user_conversations(user_id: str)
get_complete_context(user_id: str, conversation_id: str)
```

### 3. Context Builder (`services/context_builder.py`)
Aggregates context from all memory tiers for intelligent responses.

```python
Key Methods:
- build_complete_context() - Assembles full context
- build_context_summary() - Creates text summary for AI prompts
- _get_inspiration_boards() - Retrieves design inspirations
- _get_project_context() - Gets project details
- _get_design_preferences() - Fetches style preferences
- _get_conversations_from_other_agents() - Cross-agent context
```

## Database Schema

### Primary Tables

#### 1. `unified_conversations`
```sql
- id: UUID (Primary Key)
- created_by: UUID (user_id)
- conversation_type: 'iris_design_consultation'
- entity_type: 'inspiration'
- title: String
- metadata: JSONB {agent: 'iris', session_id: '...'}
- status: 'active' | 'archived'
- created_at, updated_at, last_message_at: Timestamps
```

#### 2. `unified_conversation_messages`
```sql
- id: UUID
- conversation_id: UUID (FK -> unified_conversations)
- sender: 'user' | 'assistant'
- content: Text (actual message)  # Fixed: was message_content
- message_type: 'text' | 'image'
- metadata: JSONB
- created_at: Timestamp
```

#### 3. `unified_conversation_memory`
```sql
- id: UUID
- conversation_id: UUID (FK -> unified_conversations)
- memory_type: ENUM (see MemoryType)
- memory_key: String (unique identifier)
- memory_value: JSONB (structured data)
- created_at: Timestamp
```

#### 4. `inspiration_boards`
```sql
- id: UUID
- user_id: UUID (FK -> users)  # Fixed: was tenant_id
- title: String
- room_type: String
- status: String  # Fixed: was board_status
- images: JSONB Array
- created_at, updated_at: Timestamps
```

#### 5. `property_photos`
```sql
- id: UUID
- user_id: UUID
- property_id: UUID
- room_id: UUID (FK -> property_rooms)
- file_path: String
- room_type: String
- tags: JSONB Array
- analysis_results: JSONB
- created_at: Timestamp
```

## Memory Flow Diagram

```
User Input → IRIS Agent
    ↓
[1] Load Conversation State (Unified Memory)
    └─ Load from unified_conversation_memory using session_id
    ↓
[2] Build Complete Context
    ├─ Extract conversation history from loaded state
    ├─ Get inspiration boards and property photos
    ├─ Access cross-agent conversations (CIA integration)
    └─ Prepare context for OpenAI GPT-4o-mini
    ↓
[3] Process with OpenAI GPT-4o-mini
    ├─ Send conversation history (last 10 messages)
    ├─ Include property context and image analysis
    └─ Generate intelligent, context-aware response
    ↓
[4] Save to Unified Memory
    ├─ Add user message to conversation history
    ├─ Add assistant response to conversation history
    ├─ Save updated state to unified_conversation_memory
    └─ Store image analysis results (if applicable)
    ↓
[5] Return Response with Memory Confirmation
```

## Key Features

### 1. Conversation Continuity
- Session IDs link multiple messages in a conversation
- Conversation IDs persist across sessions
- Full history available for context

### 2. Image Memory
- Image analysis results stored in context memory
- Photos linked to rooms and properties
- Inspiration boards track design preferences

### 3. Cross-Agent Integration
- Accesses conversations from CIA (homeowner agent)
- Integrates with messaging agent context
- Shares memory with unified system

### 4. Intelligent Retrieval
```python
# Example: Complete context retrieval
context = memory_manager.get_complete_context(user_id, conversation_id)
# Returns:
{
    'session_memory': [...messages],
    'context_memory': [...memory_entries],
    'cross_session_memory': {
        'inspiration_boards': [...],
        'property_photos': [...],
        'user_conversations': [...]
    },
    'memory_stats': {
        'session_messages': 10,
        'context_entries': 5,
        'inspiration_boards': 2,
        'property_photos': 15
    }
}
```

## Critical Memory System Fix (January 2025)

### Unified Memory Integration Implementation
**Problem Solved**: IRIS now uses the same unified memory system as all other agents.

**Before (Broken)**:
- IRIS saved messages to `unified_conversation_messages` table
- CIA agent saved messages to `unified_conversation_memory` table  
- Result: Complete memory amnesia between sessions ❌

**After (Fixed)**:
- IRIS saves to `unified_conversation_memory` (same as CIA) ✅
- Uses shared memory key "cia_state" for compatibility ✅
- Messages persist across sessions with full context ✅
- Cross-agent memory sharing operational ✅

## Memory Types (Enum)

```python
class MemoryType(str, Enum):
    INSPIRATION_BOARD = "inspiration_board"
    DESIGN_PREFERENCES = "design_preferences"
    GENERATED_DESIGN = "generated_design"
    PHOTO_REFERENCE = "photo_reference"
    IMAGE_ANALYSIS = "image_analysis"
    CONVERSATION_CONTEXT = "conversation_context"
```

## Testing & Verification

### Test Case: Kitchen Water Damage Context Memory
```python
# Session 1:
# User: "Hi IRIS! I have water damage in my kitchen ceiling above the sink."
# IRIS: "I can help you with that kitchen water damage. This sounds like it could 
#       be from a plumbing leak above the sink. Let me document this..."

# Session 2 (days later):
# User: "The kitchen issue is getting worse."
# IRIS: "I remember you mentioned water damage in your kitchen ceiling above the 
#       sink. If it's getting worse, this indicates an active leak..."
# Result: ✅ PASSED - Cross-session context persistence working
```

### Comprehensive Memory Testing Results
- Multi-exchange conversations saved ✅ VERIFIED
- Cross-session context retrieval ✅ VERIFIED  
- OpenAI integration with history ✅ VERIFIED
- Unified memory system compatibility ✅ VERIFIED
- CIA agent memory integration ✅ VERIFIED

## API Endpoints

### Main Conversation Endpoint
```
POST /api/iris/unified-chat
{
    "user_id": "uuid",
    "session_id": "uuid",
    "message": "string",
    "images": [{"data": "base64", "filename": "string"}]
}
```

### Context Retrieval
```
GET /api/iris/context/{user_id}?project_id=uuid
Returns: Complete user context including all memory tiers
```

## Performance Considerations

### Memory Query Optimization
- Indexed on conversation_id for fast retrieval
- Limited to 50 messages by default (configurable)
- Lazy loading of cross-session memory

### Caching Strategy
- No explicit caching (real-time requirements)
- Database indexes optimize frequent queries
- Connection pooling via SupabaseDB wrapper

## Error Handling

### Graceful Degradation
- If database unavailable: Returns UUID fallback
- Missing context: Continues with empty context
- Failed saves: Logs error, continues operation

### Logging
- All operations logged at INFO level
- Errors logged with full stack traces
- Memory stats logged for monitoring

## Integration Points

### 1. Unified System
- Shares `unified_conversations` table
- Compatible with other agents (CIA, BSA, etc.)
- Consistent user_id usage across system

### 2. Frontend Components
- UnifiedChat component sends requests
- PropertyGallery accesses stored photos
- InspirationBoard displays saved boards

### 3. Background Processing
- Async operations prevent blocking
- Image analysis runs in background
- Memory saves don't delay responses

## Why It's Working

### 1. Unified Memory Integration
IRIS now uses the same memory system as CIA agent, eliminating amnesia.

### 2. Proper Memory Key Usage
Uses "cia_state" memory key for cross-agent compatibility.

### 3. OpenAI Integration
Conversation history properly loaded and sent to GPT-4o-mini API.

### 4. Database Compatibility
Correct sender_type values ('user'/'agent') satisfy database constraints.

### 5. Complete Context Persistence
Full conversation context maintained across sessions and agents.

### 6. Real-Time Operation
Actual Supabase operations with live memory persistence.

## Maintenance Notes

### Adding New Memory Types
1. Add to MemoryType enum in `models/database.py`
2. Create save method in MemoryManager
3. Add retrieval logic to ContextBuilder
4. Update get_complete_context() if needed

### Debugging Memory Issues
1. Check Docker logs: `docker logs instabids-instabids-backend-1`
2. Verify unified memory integration in conversation_manager.py:45-65
3. Check session_id format and memory key usage
4. Verify OpenAI API integration in llm_service.py:77-85
5. Test conversation state loading/saving operations

### Performance Monitoring
- Track memory_stats in responses
- Monitor query times in logs
- Check database connection pool status

## Conclusion

The IRIS unified memory system is a fully operational implementation that provides:
- **Persistent conversation memory** across all sessions
- **Cross-agent memory integration** with CIA and other agents
- **Intelligent context awareness** with OpenAI GPT-4o-mini integration
- **Property-specific memory** for room analysis and design preferences
- **Verified reliability** through comprehensive testing

The system successfully eliminates memory amnesia, maintains complete conversation context, integrates with other agents, and provides intelligent property assistance with full memory persistence. All unified memory operations are verified working with real database integration and OpenAI API calls.
# IRIS Agent Memory System - Comprehensive Deep Dive

## Executive Summary
The IRIS agent implements a sophisticated three-tier memory architecture that enables persistent context awareness across conversations, sessions, and user interactions. The system is confirmed WORKING as of August 19, 2025, with all database schema issues resolved.

## Architecture Overview

### Three-Tier Memory System

```
┌─────────────────────────────────────────────────────────┐
│                    IRIS MEMORY SYSTEM                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Tier 1: SESSION MEMORY                                  │
│  └─ Table: unified_conversation_messages                 │
│     └─ Real-time conversation history                    │
│                                                           │
│  Tier 2: CONTEXT MEMORY                                  │
│  └─ Table: unified_conversation_memory                   │
│     └─ Structured context and analysis results           │
│                                                           │
│  Tier 3: CROSS-SESSION MEMORY                           │
│  └─ Tables: inspiration_boards, property_photos          │
│     └─ Persistent user assets and preferences            │
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

### 2. Memory Manager (`services/memory_manager.py`)
The brain of the memory system, handling all persistence operations.

#### Session Memory Operations
```python
# Save conversation messages
save_conversation_message(
    conversation_id: str,
    sender: str,      # 'user' or 'assistant'
    content: str,
    message_type: str,  # 'text', 'image', etc.
    metadata: Dict
)

# Retrieve conversation history
get_conversation_history(
    conversation_id: str,
    limit: int = 50
) -> List[Dict]
```

#### Context Memory Operations
```python
# Save structured context
save_context_memory(
    conversation_id: str,
    memory_type: MemoryType,  # ENUM: image_analysis, design_preferences, etc.
    memory_key: str,
    memory_value: Dict
)

# Special purpose methods
save_image_analysis_memory()  # Stores image analysis results
save_session_memory()         # Stores session context
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
[1] Create/Get Conversation ID
    ↓
[2] Build Context (Context Builder)
    ├─ Get conversation history
    ├─ Get context memory entries
    ├─ Get inspiration boards
    ├─ Get property photos
    └─ Get cross-agent conversations
    ↓
[3] Process with GPT-4 (with full context)
    ↓
[4] Save to Memory (Memory Manager)
    ├─ Save message to conversation history
    ├─ Save context memory entries
    ├─ Update inspiration boards (if applicable)
    └─ Store image analysis (if images uploaded)
    ↓
[5] Return Response
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

## Schema Fixes Applied (August 19, 2025)

### Critical Column Name Corrections:
1. `message_content` → `content` in unified_conversation_messages
2. `board_status` → `status` in inspiration_boards  
3. `tenant_id` → `user_id` across all tables

These fixes resolved all database save/retrieve issues.

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

### Test Case: Color Preference Memory
```python
# Message 1: "I love blue colors for my kitchen design"
# Message 2: "What colors would work well with that?"
# Expected: Response mentions blue in second message
# Result: ✅ PASSED - System remembers blue preference
```

### Memory Persistence Verification
- Conversations saved to database ✅
- Context retrieved across sessions ✅
- Image analysis stored and retrieved ✅
- Cross-agent memory accessible ✅

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

### 1. Schema Alignment
All column names match actual database schema after fixes.

### 2. Proper UUID Handling
Validates and generates UUIDs correctly for all IDs.

### 3. Error Recovery
Gracefully handles missing data without crashing.

### 4. Complete Integration
All components properly connected with no placeholders.

### 5. Real Database Operations
Uses actual Supabase client, not simulations.

## Maintenance Notes

### Adding New Memory Types
1. Add to MemoryType enum in `models/database.py`
2. Create save method in MemoryManager
3. Add retrieval logic to ContextBuilder
4. Update get_complete_context() if needed

### Debugging Memory Issues
1. Check Docker logs: `docker logs instabids-instabids-backend-1`
2. Verify database connection in memory_manager.py:21-31
3. Check column names match schema exactly
4. Ensure UUIDs are valid format

### Performance Monitoring
- Track memory_stats in responses
- Monitor query times in logs
- Check database connection pool status

## Conclusion

The IRIS memory system is a sophisticated, working implementation that provides:
- **Persistent context** across conversations
- **Multi-tier memory** for different data types
- **Cross-agent integration** for unified experience
- **Intelligent retrieval** with GPT-4 context
- **Proven reliability** through testing

The system successfully maintains conversation context, remembers user preferences, stores image analyses, and retrieves all data correctly across sessions. All database operations are functional with proper schema alignment.
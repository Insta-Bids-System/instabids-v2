# IRIS Project Push System - Complete Integration Documentation

## Overview

The IRIS Project Push System enables seamless transition from IRIS inspiration/house analysis to CIA project implementation planning. This system allows IRIS to compile house analysis data into actionable project proposals and hand them off to the CIA agent for detailed planning and bid card creation.

## Architecture

### Key Components

1. **IRIS Project Push Endpoint** (`/api/iris/push-project`)
2. **CIA Receiving Endpoint** (`/api/cia/receive-iris-proposal`)
3. **House Context Analysis Engine**
4. **Unified Memory Integration**
5. **Database Project Creation**

### Data Flow

```
IRIS Agent → House Analysis → Project Push → CIA Agent → Bid Card Creation
     ↓              ↓             ↓            ↓              ↓
   Photos    Context Analysis  Database    CIA Context   Homeowner
   Text      Budget/Timeline   Project     Loading       Conversation
```

## Implementation Details

### 1. IRIS Project Push Endpoint

**Location**: `ai-agents/api/iris_chat_unified_fixed.py:870-1328`

**Endpoint**: `POST /api/iris/push-project`

**Request Schema**:
```python
class IrisProjectProposal(BaseModel):
    homeowner_id: str
    iris_session_id: str
    source_context: str  # "inspiration", "house_analysis", or "combined"
    
    project_proposal: dict  # Contains all IRIS analysis
    design_preferences: Optional[dict] = None
    current_state_analysis: Optional[dict] = None
    inspiration_summary: Optional[dict] = None
    
    next_steps: list[str]
    confidence_score: float
    
    # Context preservation
    iris_conversation_id: Optional[str] = None
    unified_memory_refs: Optional[list[str]] = None
```

**Key Functions**:

- `analyze_house_context_for_project()` - Main analysis orchestrator
- `determine_project_title_from_house_analysis()` - Generates appropriate titles
- `estimate_budget_from_house_analysis()` - Budget estimation logic
- `determine_contractor_specialties_needed()` - Contractor requirements

### 2. House Context Analysis Engine

**Core Logic**: Analyzes IRIS conversation history to extract:

- **Project Type**: Determines from photos and conversation context
- **Budget Range**: Estimates based on scope and materials mentioned
- **Timeline**: Extracts urgency indicators and complexity factors
- **Contractor Specialties**: Identifies required trade expertise
- **Design Elements**: Material preferences, style indicators

**Budget Estimation Algorithm**:
```python
# Base budgets by project type
base_budgets = {
    "kitchen_renovation": (15000, 75000),
    "bathroom_renovation": (8000, 40000),
    "landscaping": (3000, 50000),
    "deck_construction": (5000, 25000),
    "home_addition": (30000, 150000)
}

# Adjustments for scope and materials
if "luxury" in conversation: multiply by 1.5-2.0
if "budget" mentioned: adjust to homeowner constraints
if multiple rooms: scale by room count
```

### 3. Database Integration

**Project Creation**: Creates entry in `projects` table with:

```python
project_data = {
    "id": project_id,
    "homeowner_id": homeowner["id"],
    "title": project_analysis.get("project_title"),
    "description": project_analysis.get("description"),
    "category": project_analysis.get("project_type", "renovation"),
    "urgency": "soon",  # Valid enum value
    "budget_range": project_analysis.get("budget_range"),
    "location": homeowner.get("location", {}),
    "status": "draft",  # Valid enum value
    "job_assessment": {
        "created_from": "iris_house_analysis",  # Moved to JSONB field
        "iris_session_id": proposal.iris_session_id,
        "iris_context": {
            "source_context": proposal.source_context,
            "confidence_score": proposal.confidence_score,
            "analysis_summary": project_analysis,
            "original_proposal": proposal.project_proposal
        }
    }
}
```

### 4. CIA Handoff Integration

**CIA Endpoint**: `/api/cia/receive-iris-proposal`
**Location**: `routers/cia_routes_unified.py:505-616`

**Handoff Process**:

1. **Context Transfer**: IRIS data formatted for CIA understanding
2. **Session Creation**: New CIA session with IRIS context pre-loaded
3. **Database Linking**: Project linked to both IRIS and CIA sessions
4. **Conversation Initialization**: CIA starts with IRIS context visible

**Context Formatting**:
```python
def format_iris_context_for_cia(proposal: IrisProjectProposal) -> str:
    # Formats IRIS analysis into CIA-friendly context message
    # Includes project proposal, design preferences, current state analysis
    # Adds transition notes and recommended next steps
```

## API Usage Examples

### 1. Push Project from IRIS

```python
import requests

proposal_data = {
    "homeowner_id": "550e8400-e29b-41d4-a716-446655440001",
    "iris_session_id": "iris_session_123",
    "source_context": "house_analysis",
    "project_proposal": {
        "project_type": "kitchen_renovation",
        "scope": "Full kitchen remodel with new cabinets and appliances",
        "style_preferences": "Modern farmhouse",
        "budget_context": "Looking for mid-range materials"
    },
    "next_steps": [
        "Finalize cabinet style and layout",
        "Get contractor quotes for plumbing/electrical",
        "Schedule design consultation"
    ],
    "confidence_score": 0.85
}

response = requests.post(
    "http://localhost:8008/api/iris/push-project",
    json=proposal_data
)

result = response.json()
# Returns: CIA session ID, project ID, handoff confirmation
```

### 2. Test CIA Handoff

```python
# Verify CIA received IRIS context
cia_session_id = result["homeowner_session_id"]

# Check conversation history includes IRIS context
history = requests.get(
    f"http://localhost:8008/api/cia/conversation/{cia_session_id}"
)

# Should show IRIS context as initial system message
```

## Database Schema Requirements

### Projects Table Enums

**Status**: `draft`, `planning`, `bidding`, `in_progress`, `completed`, `cancelled`
**Urgency**: `soon`, `flexible`, `urgent`, `emergency`

### Required Fields

- `homeowner_id` (UUID): Links to homeowners table
- `title` (TEXT): Generated from IRIS analysis
- `description` (TEXT): Detailed project description
- `category` (TEXT): Project type classification
- `job_assessment` (JSONB): Contains IRIS context and metadata

## Testing Procedures

### 1. End-to-End Test

```python
# File: test_iris_project_push.py

# Test house analysis → project creation → CIA handoff
# Verify database records created correctly
# Confirm CIA has access to IRIS context
# Check conversation continuity
```

### 2. Database Validation

```sql
-- Verify project created with IRIS context
SELECT 
    id, title, category, status, urgency,
    job_assessment->'created_from' as source,
    job_assessment->'iris_context'->>'confidence_score' as confidence
FROM projects 
WHERE job_assessment->'created_from' = '"iris_house_analysis"'
ORDER BY created_at DESC;
```

### 3. API Parameter Compatibility

**Fixed Issue**: GPT-5 API parameter error resolved

**Previous Error**: `"Unsupported parameter: 'max_tokens' is not supported with this model"`

**Solution**: Updated all instances from `max_tokens` to `max_completion_tokens`

**Files Updated**:
- `iris_chat_unified.py` (3 instances)
- `iris_chat_unified_fixed.py` (2 instances) 
- `property_api.py` (1 instance)
- `cia_routes_unified.py` (1 instance)

## Integration Points

### 1. Unified Memory System

**Adapter**: `adapters/homeowner_context.py`
**Integration**: `agents/cia/unified_integration.py`

**Cross-Agent Memory Sharing**:
- IRIS design insights → CIA budget discussions
- Previous project patterns → Timeline recommendations
- Material preferences → Contractor matching

### 2. WebSocket Updates

**Real-Time Updates**: Bid card changes trigger WebSocket notifications
**Table**: `postgres_changes:*:bid_cards`
**Frontend**: Live updates when projects transition phases

### 3. JAA Service Integration

**Endpoint**: `PUT /jaa/update/{bid_card_id}`
**Timeout**: 120 seconds (multiple Claude Opus 4 calls)
**Purpose**: Centralized bid card updates and contractor notifications

## Error Handling

### Common Issues and Solutions

1. **Database Schema Errors**:
   - Use correct enum values: `status="draft"`, `urgency="soon"`
   - Move custom fields to `job_assessment` JSONB

2. **API Parameter Errors**:
   - Use `max_completion_tokens` instead of `max_tokens` for GPT-4o/GPT-5
   - Check model compatibility for all OpenAI calls

3. **Context Transfer Failures**:
   - Verify homeowner_id exists in database
   - Ensure IRIS session has sufficient conversation history
   - Check CIA agent initialization

## Security Considerations

### Data Privacy

- Homeowner data filtered through privacy policies
- IRIS context sanitized before CIA transfer
- Cross-agent memory sharing respects user consent

### API Security

- Session validation for all endpoints
- User access verification for project creation
- Timeout protections for external API calls

## Performance Optimization

### Database Queries

- Indexed lookups on homeowner_id and session_id
- JSONB queries optimized for IRIS context retrieval
- Batch updates for project creation

### API Calls

- Async operations for external service calls
- Timeout handling for JAA service integration
- Parallel processing for house analysis functions

## Monitoring and Logging

### Key Metrics

- Project push success rate
- CIA handoff completion rate
- Average analysis processing time
- Database query performance

### Log Locations

- IRIS: `iris_chat_unified_fixed.py` logs
- CIA: `cia_routes_unified.py` logs
- Database: Supabase query logs
- Integration: `unified_integration.py` logs

## Future Enhancements

### Potential Improvements

1. **Enhanced Analysis**:
   - Computer vision for material identification
   - Cost estimation API integration
   - Local contractor database matching

2. **Advanced Handoffs**:
   - Multi-agent project coordination
   - Automatic bid card generation
   - Real-time collaboration features

3. **User Experience**:
   - Progress indicators for analysis phases
   - Preview mode before CIA handoff
   - Direct editing of generated proposals

---

## System Status: ✅ FULLY OPERATIONAL

**Last Updated**: January 2025
**Version**: 1.0.0
**Status**: Production Ready

All components tested and verified working end-to-end with real database integration and API compatibility.
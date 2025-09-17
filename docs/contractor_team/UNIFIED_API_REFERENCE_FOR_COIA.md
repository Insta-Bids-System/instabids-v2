# Unified Conversation API Reference for COIA Integration
**Date:** January 27, 2025  
**Status:** Production Ready  
**Base URL:** `http://localhost:8008`

## 🚀 QUICK START FOR COIA TEAM

### Basic COIA Integration Pattern
```python
import requests

# 1. Create conversation for contractor onboarding
conversation = requests.post("http://localhost:8008/api/conversations/create", json={
    "tenant_id": "instabids-main",
    "created_by": contractor_id,
    "conversation_type": "contractor_onboarding",
    "entity_type": "contractor",
    "entity_id": contractor_id,
    "title": f"COIA Session {session_id}"
}).json()

conversation_id = conversation["conversation_id"]

# 2. Send messages during conversation
requests.post("http://localhost:8008/api/conversations/message", json={
    "conversation_id": conversation_id,
    "sender_type": "agent",
    "sender_id": "coia",
    "agent_type": "coia", 
    "content": "Welcome to contractor onboarding!",
    "content_type": "text"
})

# 3. Store COIA state
requests.post("http://localhost:8008/api/conversations/memory", json={
    "conversation_id": conversation_id,
    "memory_scope": "conversation",
    "memory_type": "agent_state",
    "memory_key": "coia_state",
    "memory_value": coia_state_dict
})
```

## 📚 COMPLETE API ENDPOINTS

### 1. Create Conversation
Creates a new conversation in the unified system.

**Endpoint:** `POST /api/conversations/create`

**Request Body:**
```json
{
  "tenant_id": "instabids-main",
  "created_by": "contractor-uuid",
  "conversation_type": "contractor_onboarding",
  "entity_type": "contractor",
  "entity_id": "contractor-uuid", 
  "title": "COIA Session contractor-session-123",
  "metadata": {
    "session_id": "contractor-session-123",
    "agent_type": "COIA",
    "onboarding_step": "profile_setup"
  }
}
```

**Response:**
```json
{
  "success": true,
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-27T10:30:00Z",
  "message": "Conversation created successfully"
}
```

### 2. Send Message
Adds a message to an existing conversation.

**Endpoint:** `POST /api/conversations/message`

**Request Body:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "sender_type": "agent",
  "sender_id": "coia",
  "agent_type": "coia",
  "content": "Please provide your business license number.",
  "content_type": "text",
  "metadata": {
    "onboarding_field": "license_number",
    "validation_required": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "660e8400-e29b-41d4-a716-446655440001", 
  "timestamp": "2025-01-27T10:30:15Z",
  "message": "Message sent successfully"
}
```

### 3. Store Memory/State
Stores conversation memory and agent state.

**Endpoint:** `POST /api/conversations/memory`

**Request Body:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "memory_scope": "conversation",
  "memory_type": "agent_state",
  "memory_key": "coia_onboarding_state",
  "memory_value": {
    "current_step": "license_verification",
    "completed_fields": ["business_name", "contact_info"],
    "validation_status": "pending",
    "contractor_profile": {
      "business_name": "Smith Construction",
      "license_type": "general_contractor",
      "years_experience": 15
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "memory_id": "770e8400-e29b-41d4-a716-446655440002",
  "message": "Memory stored successfully"
}
```

### 4. Get Conversation
Retrieves complete conversation with messages and memory.

**Endpoint:** `GET /api/conversations/{conversation_id}`

**Response:**
```json
{
  "success": true,
  "conversation": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_id": "instabids-main",
    "conversation_type": "contractor_onboarding",
    "entity_type": "contractor",
    "entity_id": "contractor-uuid",
    "title": "COIA Session contractor-session-123",
    "status": "active",
    "created_at": "2025-01-27T10:30:00Z",
    "updated_at": "2025-01-27T10:35:00Z",
    "metadata": {
      "session_id": "contractor-session-123",
      "agent_type": "COIA" 
    }
  },
  "messages": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "sender_type": "agent", 
      "sender_id": "coia",
      "agent_type": "coia",
      "content": "Welcome to contractor onboarding!",
      "content_type": "text",
      "timestamp": "2025-01-27T10:30:15Z"
    }
  ],
  "memory": [
    {
      "memory_key": "coia_onboarding_state",
      "memory_value": { "current_step": "license_verification" },
      "memory_type": "agent_state"
    }
  ],
  "participants": [
    {
      "participant_type": "contractor",
      "participant_id": "contractor-uuid"
    },
    {
      "participant_type": "agent", 
      "participant_id": "coia"
    }
  ]
}
```

### 5. Get User Conversations
Lists all conversations for a specific contractor.

**Endpoint:** `GET /api/conversations/user/{contractor_id}`

**Response:**
```json
{
  "success": true,
  "conversations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "COIA Session contractor-session-123", 
      "conversation_type": "contractor_onboarding",
      "status": "active",
      "created_at": "2025-01-27T10:30:00Z",
      "last_message_at": "2025-01-27T10:35:00Z",
      "message_count": 5
    }
  ],
  "total_count": 1
}
```

## 🔧 COIA-SPECIFIC USAGE PATTERNS

### Pattern 1: Contractor Onboarding Flow
```python
class CoIAUnifiedIntegration:
    def __init__(self):
        self.base_url = "http://localhost:8008"
        
    async def start_onboarding(self, contractor_id: str, session_id: str) -> str:
        """Start new contractor onboarding conversation"""
        response = requests.post(f"{self.base_url}/api/conversations/create", json={
            "tenant_id": "instabids-main",
            "created_by": contractor_id,
            "conversation_type": "contractor_onboarding",
            "entity_type": "contractor", 
            "entity_id": contractor_id,
            "title": f"COIA Onboarding {session_id}",
            "metadata": {
                "session_id": session_id,
                "onboarding_started": datetime.now().isoformat()
            }
        })
        
        return response.json()["conversation_id"]
    
    async def save_onboarding_step(self, conversation_id: str, step_name: str, step_data: dict):
        """Save progress for specific onboarding step"""
        requests.post(f"{self.base_url}/api/conversations/memory", json={
            "conversation_id": conversation_id,
            "memory_scope": "conversation",
            "memory_type": "onboarding_step",
            "memory_key": f"step_{step_name}",
            "memory_value": {
                "step_name": step_name,
                "completed": True,
                "data": step_data,
                "completed_at": datetime.now().isoformat()
            }
        })
    
    async def get_onboarding_progress(self, conversation_id: str) -> dict:
        """Retrieve current onboarding progress"""
        response = requests.get(f"{self.base_url}/api/conversations/{conversation_id}")
        conversation_data = response.json()
        
        # Extract onboarding steps from memory
        steps = {}
        for memory in conversation_data.get("memory", []):
            if memory["memory_type"] == "onboarding_step":
                step_name = memory["memory_key"].replace("step_", "")
                steps[step_name] = memory["memory_value"]
        
        return steps
```

### Pattern 2: License Verification Integration
```python
async def handle_license_verification(self, conversation_id: str, license_data: dict):
    """Handle license verification step in onboarding"""
    
    # Store license data
    requests.post(f"{self.base_url}/api/conversations/memory", json={
        "conversation_id": conversation_id,
        "memory_scope": "contractor",
        "memory_type": "license_info", 
        "memory_key": "contractor_license",
        "memory_value": {
            "license_number": license_data["number"],
            "license_type": license_data["type"],
            "state": license_data["state"],
            "expiration_date": license_data["expiration"],
            "verification_status": "pending"
        }
    })
    
    # Send message about verification
    requests.post(f"{self.base_url}/api/conversations/message", json={
        "conversation_id": conversation_id,
        "sender_type": "agent",
        "sender_id": "coia",
        "agent_type": "coia",
        "content": f"License {license_data['number']} submitted for verification. This may take 24-48 hours.",
        "content_type": "text"
    })
```

### Pattern 3: Portfolio Upload Integration  
```python
async def handle_portfolio_upload(self, conversation_id: str, file_urls: list):
    """Handle portfolio image uploads"""
    
    # Store portfolio metadata
    requests.post(f"{self.base_url}/api/conversations/memory", json={
        "conversation_id": conversation_id,
        "memory_scope": "contractor",
        "memory_type": "portfolio",
        "memory_key": "uploaded_projects",
        "memory_value": {
            "project_images": file_urls,
            "upload_count": len(file_urls),
            "uploaded_at": datetime.now().isoformat()
        }
    })
    
    # Send confirmation message
    requests.post(f"{self.base_url}/api/conversations/message", json={
        "conversation_id": conversation_id,
        "sender_type": "agent", 
        "sender_id": "coia",
        "agent_type": "coia",
        "content": f"Portfolio uploaded successfully! {len(file_urls)} project images received.",
        "content_type": "text"
    })
```

## 📊 MEMORY SCOPES FOR COIA

### Conversation Scope
- **Purpose:** Data specific to this onboarding session
- **Examples:** Current step, session preferences, temporary data
- **Usage:** `"memory_scope": "conversation"`

### Contractor Scope  
- **Purpose:** Persistent contractor profile data
- **Examples:** License info, business details, portfolio
- **Usage:** `"memory_scope": "contractor"`

### Project Scope
- **Purpose:** Data related to specific projects (if applicable)
- **Examples:** Service preferences, project history
- **Usage:** `"memory_scope": "project"`

## 🔍 DEBUGGING & MONITORING

### Check Conversation Status
```bash
curl http://localhost:8008/api/conversations/{conversation_id}
```

### List Contractor Conversations
```bash  
curl http://localhost:8008/api/conversations/user/{contractor_id}
```

### Monitor API Health
```bash
curl http://localhost:8008/health
```

### Database Queries for Debugging
```sql
-- Check COIA conversations
SELECT * FROM unified_conversations 
WHERE conversation_type = 'contractor_onboarding';

-- Check COIA memory/state
SELECT * FROM unified_conversation_memory 
WHERE memory_key LIKE 'coia_%';

-- Check COIA messages
SELECT * FROM unified_messages 
WHERE agent_type = 'coia';
```

## ⚠️ ERROR HANDLING

### Common Errors & Solutions

**401 Unauthorized**
- Check API authentication if required
- Verify base URL is correct

**400 Bad Request**
- Validate JSON payload structure
- Check required fields are present

**404 Not Found** 
- Verify conversation_id exists
- Check endpoint URL spelling

**500 Internal Server Error**
- Check unified API service is running
- Verify database connectivity
- Check server logs for details

### Fallback Strategy
```python
async def save_with_fallback(self, conversation_data):
    """Save to unified system with fallback to old system"""
    try:
        # Try unified API first
        response = requests.post(f"{self.base_url}/api/conversations/create", 
                               json=conversation_data, timeout=5)
        if response.ok:
            return response.json()
    except Exception as e:
        logger.warning(f"Unified API failed: {e}, using fallback")
        
    # Fallback to old agent_conversations table
    return await self.save_to_agent_conversations(conversation_data)
```

## 🚀 PERFORMANCE NOTES

**Expected Response Times:**
- Create conversation: < 100ms
- Send message: < 50ms  
- Store memory: < 75ms
- Get conversation: < 200ms

**Optimization Tips:**
- Batch memory operations when possible
- Use async/await for concurrent API calls
- Cache conversation_id to avoid repeated lookups

---

**API Status:** ✅ Production Ready  
**COIA Integration:** 🟡 Pending Migration  
**Support:** Available for immediate implementation
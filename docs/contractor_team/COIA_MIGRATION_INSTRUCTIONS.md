# COIA Agent Migration to Unified Conversation System
**Date:** January 27, 2025  
**Target Team:** Contractor Development Team  
**Priority:** HIGH - 16 Active COIA Conversations Need Migration

## 🎯 OVERVIEW

The **COIA Agent (Contractor Interface Agent)** migration to the unified conversation system has been **deliberately skipped** during Phase 1 to avoid disrupting your team's active contractor onboarding system.

**Current Status:**
- ✅ **CIA Agent**: Successfully migrated to unified system
- ⏸️ **COIA Agent**: **REQUIRES YOUR TEAM'S ATTENTION**
- ✅ **Unified API**: Ready and tested for COIA integration

## 🚨 CRITICAL DATA WARNING

**ACTIVE COIA CONVERSATIONS: 16 records**
```sql
SELECT COUNT(*) FROM agent_conversations WHERE agent_type = 'COIA';
-- Result: 16 active contractor conversations
```

**⚠️ THESE CONVERSATIONS WILL BE LOST** if COIA agent is migrated without proper data handling.

## 🏗️ WHAT NEEDS TO BE DONE

### 1. COIA Agent Code Location
**Primary File:** `ai-agents/agents/coia/persistent_memory.py`
**Method to Update:** `save_conversation_state()` (lines 38-74)
**Current Storage:** `agent_conversations` table

### 2. Current Implementation
```python
async def save_conversation_state(self, state: CoIAConversationState) -> bool:
    try:
        # CURRENT: Direct database insert to agent_conversations
        result = self.db_client.table("agent_conversations").insert({
            "agent_type": "COIA",
            "thread_id": state.session_id,
            "user_id": state.contractor_id,
            "conversation_data": state.to_dict(),
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to save conversation state: {e}")
        return False
```

### 3. Required Changes
```python
async def save_conversation_state(self, state: CoIAConversationState) -> bool:
    try:
        import requests
        
        # STEP 1: Create or get conversation
        conversation_response = requests.post("http://localhost:8008/api/conversations/create", json={
            "tenant_id": "instabids-main",
            "created_by": state.contractor_id,
            "conversation_type": "contractor_onboarding",
            "entity_type": "contractor", 
            "entity_id": state.contractor_id,
            "title": f"COIA Session {state.session_id}",
            "metadata": {
                "session_id": state.session_id,
                "agent_type": "COIA",
                "contractor_id": state.contractor_id
            }
        })
        
        if not conversation_response.ok:
            logger.error(f"Failed to create conversation: {conversation_response.text}")
            return False
            
        conversation_id = conversation_response.json()["conversation_id"]
        
        # STEP 2: Store conversation memory/state
        memory_response = requests.post("http://localhost:8008/api/conversations/memory", json={
            "conversation_id": conversation_id,
            "memory_scope": "conversation",
            "memory_type": "agent_state", 
            "memory_key": "coia_conversation_state",
            "memory_value": state.to_dict()
        })
        
        if not memory_response.ok:
            logger.error(f"Failed to save conversation memory: {memory_response.text}")
            return False
            
        # STEP 3: Save individual messages if needed
        for message in state.conversation_history:  # Assuming this exists
            message_response = requests.post("http://localhost:8008/api/conversations/message", json={
                "conversation_id": conversation_id,
                "sender_type": "user" if message["role"] == "user" else "agent",
                "sender_id": state.contractor_id if message["role"] == "user" else "coia",
                "agent_type": "coia" if message["role"] == "assistant" else None,
                "content": message["content"],
                "content_type": "text"
            })
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save to unified system: {e}")
        # FALLBACK: Save to old system temporarily
        return await self._save_to_old_system(state)
```

## 📋 STEP-BY-STEP MIGRATION PLAN

### Step 1: Backup Existing Data (CRITICAL)
```bash
# Export all COIA conversations before any changes
cd /path/to/instabids
python -c "
import asyncio
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
result = supabase.table('agent_conversations').select('*').eq('agent_type', 'COIA').execute()
import json
with open('coia_backup_$(date +%Y%m%d).json', 'w') as f:
    json.dump(result.data, f, indent=2)
print(f'Backed up {len(result.data)} COIA conversations')
"
```

### Step 2: Test Unified API Integration
```bash
# Test that unified conversation API works for COIA
curl -X POST http://localhost:8008/api/conversations/create \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "instabids-main",
    "created_by": "test-contractor-123",
    "conversation_type": "contractor_onboarding",
    "entity_type": "contractor",
    "entity_id": "test-contractor-123", 
    "title": "Test COIA Session"
  }'
```

### Step 3: Update COIA Agent Code
1. **Modify** `persistent_memory.py` with new `save_conversation_state()` method
2. **Add fallback logic** to old system if unified API fails
3. **Test thoroughly** with test contractor data

### Step 4: Migration Script for Existing Data
```python
# migrate_coia_conversations.py
import asyncio
import requests
from supabase import create_client

async def migrate_coia_conversations():
    """Migrate existing COIA conversations to unified system"""
    
    # Get all COIA conversations
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table("agent_conversations").select("*").eq("agent_type", "COIA").execute()
    
    print(f"Found {len(result.data)} COIA conversations to migrate")
    
    for old_conversation in result.data:
        try:
            # Create conversation in unified system
            conversation_response = requests.post("http://localhost:8008/api/conversations/create", json={
                "tenant_id": "instabids-main", 
                "created_by": old_conversation["user_id"],
                "conversation_type": "contractor_onboarding",
                "entity_type": "contractor",
                "entity_id": old_conversation["user_id"],
                "title": f"Migrated COIA Session {old_conversation['thread_id']}",
                "metadata": {
                    "session_id": old_conversation["thread_id"],
                    "agent_type": "COIA",
                    "migrated_from": old_conversation["id"],
                    "original_created_at": old_conversation["created_at"]
                }
            })
            
            if conversation_response.ok:
                conversation_id = conversation_response.json()["conversation_id"]
                
                # Store conversation state as memory
                memory_response = requests.post("http://localhost:8008/api/conversations/memory", json={
                    "conversation_id": conversation_id,
                    "memory_scope": "conversation", 
                    "memory_type": "agent_state",
                    "memory_key": "coia_conversation_state",
                    "memory_value": old_conversation["conversation_data"]
                })
                
                if memory_response.ok:
                    print(f"✅ Migrated conversation {old_conversation['thread_id']}")
                else:
                    print(f"❌ Failed to save memory for {old_conversation['thread_id']}: {memory_response.text}")
            else:
                print(f"❌ Failed to create conversation for {old_conversation['thread_id']}: {conversation_response.text}")
                
        except Exception as e:
            print(f"❌ Error migrating {old_conversation['thread_id']}: {e}")
    
    print("Migration complete")

# Run migration
asyncio.run(migrate_coia_conversations())
```

### Step 5: Testing & Validation
```bash
# Test COIA agent after migration
# 1. Start contractor onboarding flow
# 2. Verify conversation saves to unified_conversations table
# 3. Check unified_conversation_memory table for state
# 4. Ensure contractor onboarding completes successfully
# 5. Verify conversation can be retrieved via API

# Validation queries:
# SELECT * FROM unified_conversations WHERE conversation_type = 'contractor_onboarding';
# SELECT * FROM unified_conversation_memory WHERE memory_key = 'coia_conversation_state';
```

## 🔗 UNIFIED API ENDPOINTS (READY FOR USE)

### Create Conversation
```bash
POST /api/conversations/create
{
  "tenant_id": "instabids-main",
  "created_by": "contractor-id",
  "conversation_type": "contractor_onboarding",
  "entity_type": "contractor", 
  "entity_id": "contractor-id",
  "title": "COIA Session {session_id}"
}
```

### Send Message
```bash
POST /api/conversations/message  
{
  "conversation_id": "uuid",
  "sender_type": "agent",
  "sender_id": "coia",
  "agent_type": "coia", 
  "content": "Message content",
  "content_type": "text"
}
```

### Store Memory/State
```bash
POST /api/conversations/memory
{
  "conversation_id": "uuid",
  "memory_scope": "conversation",
  "memory_type": "agent_state",
  "memory_key": "coia_conversation_state", 
  "memory_value": { "state": "data" }
}
```

### Retrieve Conversation
```bash
GET /api/conversations/{conversation_id}
# Returns conversation + messages + participants + memory
```

## 🚨 MIGRATION RISKS & MITIGATION

### Risk 1: Data Loss
**Mitigation:** 
- Complete backup before any changes
- Test migration script on copy of data first  
- Keep old `agent_conversations` table until migration verified

### Risk 2: COIA Agent Breaks
**Mitigation:**
- Implement fallback to old system if unified API fails
- Gradual rollout with A/B testing
- Rollback plan ready

### Risk 3: Performance Issues  
**Mitigation:**
- Benchmark API performance vs direct DB access
- Monitor response times during migration
- Optimize unified API queries if needed

## 📞 SUPPORT & CONTACTS

**For Technical Questions:**
- **CIA Migration Reference:** Successfully completed, code examples available
- **Unified API Documentation:** `docs/UNIFIED_CONVERSATION_API.md` 
- **Database Schema:** `docs/UNIFIED_CONVERSATION_SCHEMA.md`

**For Migration Assistance:**
- The unified conversation system is fully operational and tested
- CIA agent migration can serve as reference implementation
- All API endpoints are documented and working

## ✅ SUCCESS CRITERIA

**Migration Complete When:**
- [ ] COIA agent saves conversations to unified_conversations table
- [ ] Contractor onboarding flow works end-to-end
- [ ] All 16 existing conversations migrated successfully  
- [ ] No data loss or corruption
- [ ] Performance acceptable (< 500ms API calls)
- [ ] Old agent_conversations table receives no new COIA records

**Business Validation:**
- [ ] Contractor onboarding process uninterrupted
- [ ] Conversation history preserved and accessible
- [ ] Integration with other agents works correctly
- [ ] No user-facing bugs or issues

---

**READY TO MIGRATE:** All infrastructure prepared, API tested, migration plan documented.

**ESTIMATED TIME:** 4-6 hours including testing and validation.

**PRIORITY:** Complete COIA migration before Phase 3 (Iris Agent) begins.
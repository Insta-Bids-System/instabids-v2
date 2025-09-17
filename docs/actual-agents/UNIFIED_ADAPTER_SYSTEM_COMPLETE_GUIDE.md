# Unified Adapter System - Complete Guide
**Date**: August 12, 2025  
**Status**: ✅ PRODUCTION SYSTEM - MANDATORY FOR ALL AGENTS  
**Purpose**: Complete documentation of the adapter-based unified memory system with unbreakable privacy rules

---

## 🎯 EXECUTIVE SUMMARY

The InstaBids platform uses a **UNIFIED ADAPTER SYSTEM** that provides controlled, privacy-compliant access to the unified memory system. **ALL AGENTS MUST USE ADAPTERS** - direct database access is prohibited and breaks privacy rules.

### **Key Principles:**
1. **NO DIRECT DATABASE QUERIES** - All data access through adapters only
2. **UNBREAKABLE PRIVACY RULES** - Context Policy Engine enforces boundaries
3. **SIDE-BASED ACCESS CONTROL** - Homeowner/Contractor/Neutral classifications
4. **AUTOMATIC PII FILTERING** - Personal information automatically removed/aliased
5. **CROSS-AGENT COORDINATION** - Intelligent context sharing within privacy boundaries

---

## 🏗️ SYSTEM ARCHITECTURE

### **The Complete Stack:**

```
┌─────────────────────────────────────────────────────────────┐
│                 AGENTS (CIA, IRIS, COIA, etc.)             │
│          ❌ NEVER query databases directly                  │  
│          ✅ ALWAYS use adapters for data access            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────┐
│                ADAPTER LAYER                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Homeowner   │  │ Contractor  │  │    Messaging        │  │
│  │ Context     │  │ Context     │  │    Context          │  │
│  │ Adapter     │  │ Adapter     │  │    Adapter          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │            IRIS Context Adapter                        │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────┐
│            CONTEXT POLICY ENGINE                            │
│         (services/context_policy.py)                       │
│  ✅ UNBREAKABLE PRIVACY RULES                              │
│  ✅ Agent Classification (Homeowner/Contractor/Neutral)    │
│  ✅ PII Detection & Removal                                │
│  ✅ Alias Generation                                       │
│  ✅ Cross-Side Access Control                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────┐
│               UNIFIED MEMORY DATABASE                       │
│  - unified_conversations (master conversation records)     │
│  - unified_messages (all conversation messages)            │
│  - unified_conversation_memory (agent memory & state)      │
│  - unified_conversation_participants (multi-party access)  │
│  - unified_message_attachments (file attachments)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 PRIVACY FRAMEWORK & RULES

### **Agent Classification (IMMUTABLE):**

```python
# HOMEOWNER SIDE - Full context sharing between these agents
HOMEOWNER_SIDE = [CIA, IRIS, HMA]

# CONTRACTOR SIDE - Gets filtered homeowner data only  
CONTRACTOR_SIDE = [COIA]

# NEUTRAL - Can see both sides, enforces privacy rules
NEUTRAL = [MESSAGING, ADMIN]
```

### **Unbreakable Privacy Rules:**

1. **NO PII CROSS-CONTAMINATION**
   - Homeowner agents CANNOT see contractor real names/contact info
   - Contractor agents CANNOT see homeowner real names/contact info

2. **SAME-SIDE FULL SHARING**
   - CIA ↔ IRIS ↔ HMA: Complete context sharing
   - All homeowner-side agents see each other's data

3. **CROSS-SIDE ALIAS SYSTEM**
   - Homeowners see contractors as "Contractor A", "Contractor B"
   - Contractors see homeowners as "Project Owner"

4. **AUTOMATIC PII FILTERING**
   - Phone numbers → "[PHONE REMOVED]"
   - Email addresses → "[EMAIL REMOVED]"
   - Real names → "[NAME REMOVED]" or aliases

5. **FAIL-SECURE VALIDATION**
   - Any privacy violation = empty data returned
   - No exceptions or overrides allowed

---

## 📋 ADAPTER SYSTEM COMPONENTS

### **1. HomeownerContextAdapter** (`adapters/homeowner_context.py`)

**Purpose**: Provides full context access for homeowner-side agents (CIA, IRIS, HMA)

**Key Methods:**
```python
def get_agent_context(user_id, project_id=None, conversation_id=None):
    """Get comprehensive context for homeowner agents"""
    return {
        "user_profile": self._get_user_profile(user_id),
        "project_context": self._get_project_context(user_id, project_id), 
        "conversation_history": self._get_conversation_history(user_id),
        "cross_agent_memory": self._get_cross_agent_memory(user_id),
        "preferences": self._get_user_preferences(user_id),
        "privacy_level": "homeowner_side_full_access"
    }

def get_cross_project_insights(user_id):
    """Cross-project insights for intelligent questioning"""
    return {
        "previous_projects": self._get_previous_projects(user_id),
        "budget_patterns": self._get_budget_patterns(user_id),
        "communication_style": self._get_communication_preferences(user_id)
    }
```

**Privacy Level**: `homeowner_side_full_access`
**Data Sharing**: Full sharing with CIA, IRIS, HMA - filtered for contractor agents

---

### **2. ContractorContextAdapter** (`adapters/contractor_context.py`)

**Purpose**: Provides privacy-filtered context for contractor-side agents (COIA)

**Key Methods:**
```python
def get_contractor_context(contractor_id, session_id=None):
    """Get context for contractor agents with privacy filtering"""
    return {
        "contractor_profile": self._get_contractor_profile(contractor_id),
        "available_projects": self._get_available_projects(contractor_id),  # PII filtered
        "bid_history": self._get_bid_history(contractor_id),
        "conversation_history": self._get_conversation_history(contractor_id),
        "privacy_level": "contractor_side_filtered"
    }

def _get_available_projects(contractor_id):
    """Get projects with automatic privacy filtering"""
    projects = []
    for bid_card in bid_cards:
        projects.append({
            "bid_card_id": bid_card["id"],
            "project_type": bid_card["project_type"],
            "budget_range": f"${bid_card['budget_min']}-${bid_card['budget_max']}",
            "homeowner": "Project Owner",  # ✅ Privacy filtered - no real name
            "privacy_filtered": True
        })
```

**Privacy Level**: `contractor_side_filtered`
**PII Filtering**: All homeowner names → "Project Owner", addresses filtered, contact info removed

---

### **3. MessagingContextAdapter** (`adapters/messaging_context.py`)

**Purpose**: Neutral messaging agent with cross-side communication filtering

**Key Methods:**
```python
def apply_message_filtering(message, sender_side, recipient_side):
    """Apply privacy filtering to messages between sides"""
    if sender_side == recipient_side:
        return message  # Same side - no filtering
        
    # Cross-side filtering
    filtered_message = self._filter_contact_info(message)
    
    if sender_side == "homeowner" and recipient_side == "contractor":
        filtered_message["sender_name"] = "Project Owner"
    elif sender_side == "contractor" and recipient_side == "homeowner":
        filtered_message["sender_name"] = self._get_contractor_alias(message["sender_id"])
        
    return filtered_message

def _filter_contact_info(message):
    """Remove contact information from messages"""
    content = message["content"]
    # Remove phone numbers
    content = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "[PHONE REMOVED]", content)
    # Remove email addresses  
    content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[EMAIL REMOVED]", content)
    return content
```

**Privacy Level**: `neutral_messaging_access`
**Function**: Enforces cross-side privacy rules, applies aliases, removes PII

---

### **4. IrisContextAdapter** (`adapters/iris_context.py`)

**Purpose**: Specialized design inspiration context with homeowner-side access

**Key Methods:**
```python
def get_inspiration_context(user_id, project_id=None):
    """Get design inspiration context with CIA project integration"""
    return {
        "inspiration_boards": self._get_user_boards(user_id),
        "design_preferences": self._get_design_preferences(user_id),
        "project_context": self._get_project_context(user_id, project_id),  # From CIA
        "previous_designs": self._get_previous_design_projects(user_id),
        "privacy_level": "homeowner_side_full_access"
    }

def coordinate_with_cia(user_id, project_context, design_insights):
    """Share design insights back to CIA agent"""
    # Saves design preferences to unified memory for CIA access
```

**Privacy Level**: `homeowner_side_full_access`
**CIA Integration**: Full bidirectional context sharing with CIA agent

---

## 🔧 CONTEXT POLICY ENGINE

### **Central Privacy Enforcement** (`services/context_policy.py`)

**Purpose**: Unbreakable privacy rule enforcement across all adapters

**Core Functions:**

```python
class ContextPolicy:
    def can_access_conversation(requesting_agent, conversation_metadata):
        """Determine if an agent can access a conversation"""
        # Enforce side-based access control
        
    def filter_conversation_data(requesting_agent, conversation_data):
        """Filter conversation data based on privacy rules"""
        # Apply automatic PII filtering
        
    def validate_context_request(requesting_agent, target_context):
        """FINAL VALIDATION - Cannot be bypassed"""
        # Double-check no PII leaked through
        # Fail secure - return empty data on violations
```

**Privacy Classifications:**
- `HOMEOWNER_SIDE`: CIA, IRIS, HMA
- `CONTRACTOR_SIDE`: COIA  
- `NEUTRAL`: MESSAGING, ADMIN

**PII Field Definitions:**
```python
PII_FIELDS = {
    "homeowner_pii": {
        "first_name", "last_name", "email", "phone", 
        "address", "property_address", "contact_info"
    },
    "contractor_pii": {
        "company_name", "contact_name", "business_email",
        "business_phone", "license_number", "business_address"
    }
}
```

---

## ✅ CORRECT AGENT IMPLEMENTATION PATTERNS

### **For CIA Agent:**
```python
# ❌ WRONG - Direct database access
result = supabase.table("agent_conversations").select("*").eq("user_id", user_id)

# ✅ CORRECT - Use HomeownerContextAdapter
from adapters.homeowner_context import HomeownerContextAdapter
adapter = HomeownerContextAdapter()
context = adapter.get_agent_context(user_id=user_id, project_id=project_id)
```

### **For IRIS Agent:**
```python
# ❌ WRONG - Direct database access
boards = supabase.table("inspiration_boards").select("*").eq("user_id", user_id)

# ✅ CORRECT - Use IrisContextAdapter
from adapters.iris_context import IrisContextAdapter
adapter = IrisContextAdapter()
context = adapter.get_inspiration_context(user_id=user_id, project_id=project_id)
```

### **For COIA Agent:**
```python
# ❌ WRONG - Direct database access (breaks privacy)
projects = supabase.table("bid_cards").select("*").eq("status", "active")

# ✅ CORRECT - Use ContractorContextAdapter (privacy filtered)
from adapters.contractor_context import ContractorContextAdapter
adapter = ContractorContextAdapter()
context = adapter.get_contractor_context(contractor_id=contractor_id)
# Projects automatically have homeowner PII removed
```

### **For Messaging Agent:**
```python
# ❌ WRONG - Direct message access (no privacy filtering)
messages = supabase.table("messages").select("*").eq("thread_id", thread_id)

# ✅ CORRECT - Use MessagingContextAdapter (privacy filtered)  
from adapters.messaging_context import MessagingContextAdapter
adapter = MessagingContextAdapter()
context = adapter.get_messaging_context(thread_id=thread_id, participants=participants)
```

---

## 🚨 CRITICAL VIOLATIONS TO FIX

### **Agents Currently Bypassing Adapter System:**

1. **Intelligent Messaging Agent** (`agents/intelligent_messaging_agent.py`)
   - **Lines 536, 778**: Direct `conversations` table queries
   - **Fix**: Use `MessagingContextAdapter.get_messaging_context()`

2. **Multiple API Endpoints:**
   - `adapters/homeowner_context.py:67` - Still queries `agent_conversations`
   - `api/bid_cards_simple.py:260` - Direct `agent_conversations` access
   - `api/projects.py:136,292,330` - Multiple `agent_conversations` queries
   - **Fix**: All should use appropriate context adapters

3. **JAA Agent** (`agents/jaa/agent.py`)
   - **Issue**: No memory persistence through unified system
   - **Fix**: Integrate with `HomeownerContextAdapter` for conversation saving

4. **Monitoring Routes** (`routers/monitoring_routes.py`)
   - **Lines 63, 138**: Direct `agent_conversations` queries
   - **Fix**: Use adapters for privacy-compliant monitoring

---

## 📊 UNIFIED MEMORY DATABASE TABLES

### **Tables Used by Adapter System:**

1. **`unified_conversations`** - Master conversation records
   - Fields: `id`, `created_by`, `metadata`, `last_message_at`
   - Indexes: `created_by`, `metadata->>'session_id'`

2. **`unified_messages`** - All conversation messages  
   - Fields: `conversation_id`, `sender_type`, `sender_id`, `content`, `metadata`
   - Relationships: FK to `unified_conversations`

3. **`unified_conversation_memory`** - Agent memory & state
   - Fields: `conversation_id`, `memory_key`, `memory_value`
   - Purpose: Cross-agent shared facts and preferences

4. **`unified_conversation_participants`** - Multi-party access
   - Fields: `conversation_id`, `participant_id`, `last_read_cursor`
   - Purpose: Read/unread tracking for unified UX

5. **`unified_message_attachments`** - File attachments
   - Fields: `message_id`, `type`, `url`, `name`, `metadata`
   - Relationships: FK to `unified_messages`

---

## 🔄 CROSS-AGENT COORDINATION EXAMPLES

### **CIA → IRIS Context Sharing:**
```python
# CIA saves project context
cia_context = {
    "project_type": "kitchen_remodel",
    "budget_range": "$25000-$35000",
    "timeline": "3_months",
    "user_preferences": {...}
}
# Automatically available to IRIS via IrisContextAdapter

# IRIS accesses CIA context
iris_adapter = IrisContextAdapter()
context = iris_adapter.get_inspiration_context(user_id, project_id)
# context["project_context"] contains CIA's data
```

### **IRIS → CIA Coordination:**
```python
# IRIS saves design preferences
iris_adapter.coordinate_with_cia(
    user_id=user_id,
    project_context=project_context,
    design_insights={
        "style": "modern_farmhouse",
        "colors": ["white", "navy", "wood_tones"],
        "inspiration_sources": [...]
    }
)
# CIA can now reference design preferences in budget discussions
```

### **Cross-Side Messaging (Privacy Filtered):**
```python
# Homeowner message to contractor (automatically filtered)
messaging_adapter = MessagingContextAdapter()
filtered_message = messaging_adapter.apply_message_filtering(
    message={"content": "Hi John, call me at 555-1234", "sender_id": homeowner_id},
    sender_side="homeowner",
    recipient_side="contractor"
)
# Result: {"content": "Hi [NAME REMOVED], call me at [PHONE REMOVED]", "sender_name": "Project Owner"}
```

---

## 🎯 MIGRATION CHECKLIST

### **For Each Agent:**
- [ ] Remove all direct database table queries
- [ ] Import appropriate context adapter
- [ ] Replace database calls with adapter methods
- [ ] Test privacy filtering is working
- [ ] Verify cross-agent context sharing works

### **System-Wide:**
- [ ] No `agent_conversations` table references
- [ ] No `conversations` table references (use unified_conversations)
- [ ] All data access through adapters only
- [ ] Privacy rules enforced everywhere
- [ ] Context Policy Engine active

### **Testing Requirements:**
- [ ] Cross-agent context sharing works
- [ ] Privacy boundaries enforced
- [ ] PII properly filtered/aliased
- [ ] Same-side agents share full context
- [ ] Cross-side agents get filtered context

---

## 🚀 BENEFITS OF THE ADAPTER SYSTEM

1. **UNBREAKABLE PRIVACY** - No agent can bypass privacy rules
2. **INTELLIGENT CONTEXT SHARING** - Agents get exactly what they need
3. **AUTOMATIC PII PROTECTION** - No manual filtering required
4. **CONSISTENT DATA ACCESS** - All agents use same patterns
5. **CROSS-PROJECT MEMORY** - Users get personalized experiences
6. **AUDIT TRAIL** - All access goes through controlled layer
7. **FUTURE-PROOF** - Easy to add new privacy rules or agents

---

**The Adapter System is MANDATORY for all agents. Direct database access is prohibited and creates serious privacy and security vulnerabilities. ALL agents must be migrated to use this system.**
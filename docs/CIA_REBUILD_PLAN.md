# CIA Agent Complete Rebuild Plan
**Date**: December 19, 2024
**Purpose**: Simplify CIA from 2,700 lines to ~400 lines while keeping ALL functionality

## 🎯 OBJECTIVES

### What We're Keeping (The Good Parts)
✅ Universal memory system (cross-session persistence)  
✅ Potential bid card real-time updates  
✅ Continuous conversation context  
✅ Supabase database integration  
✅ Frontend real-time display (port 5173)  
✅ Multi-project awareness  
✅ Emergency/non-emergency handling  

### What We're Removing (The Mess)
❌ 5 different extraction systems (GPT-5, demo, pattern, basic, intelligent)  
❌ 2,700 lines of spaghetti code  
❌ Fake "GPT-5" methods that don't exist  
❌ Demo/mock response systems  
❌ Commented-out LangGraph imports  
❌ Multiple database save methods doing the same thing  
❌ Legacy migration code  

## 📁 NEW FILE STRUCTURE

```
agents/cia/
├── agent.py                          # ~200 lines - Clean OpenAI implementation
├── schemas.py                        # ~50 lines - Pydantic models for 12 fields
├── store.py                          # ~100 lines - Supabase operations
├── prompts.py                        # ~50 lines - System prompts (simplified)
├── CIA_REBUILD_PLAN.md              # This file
├── README.md                         # Updated documentation
└── legacy/                           # Archive old code here
    ├── agent_old.py                  # Current 2,700 line mess
    ├── modification_handler.py       # Can probably delete
    ├── mode_manager.py               # Not needed with tool calling
    └── service_complexity_classifier.py  # Over-engineered
```

## 🏗️ IMPLEMENTATION PLAN

### Phase 1: Archive Current Code (5 minutes)
```bash
# Create legacy folder and move old code
mkdir legacy
cp agent.py legacy/agent_old.py
cp modification_handler.py legacy/
cp mode_manager.py legacy/
cp service_complexity_classifier.py legacy/
```

### Phase 2: Create Clean Schema (15 minutes)
**File: schemas.py**
```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class UrgencyLevel(str, Enum):
    EMERGENCY = "emergency"
    WEEK = "week"
    MONTH = "month"
    FLEXIBLE = "flexible"

class BidCardUpdate(BaseModel):
    """The 12 InstaBids data points"""
    project_type: Optional[str] = Field(None, description="Kitchen, bathroom, lawn, etc.")
    urgency: Optional[UrgencyLevel] = None
    location: Optional[str] = Field(None, description="Address or zip code")
    scope_details: Optional[str] = Field(None, description="Detailed work description")
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    timeline: Optional[str] = Field(None, description="Specific dates if mentioned")
    property_type: Optional[str] = Field(None, description="House, condo, commercial")
    special_requirements: Optional[str] = None
    materials: Optional[str] = Field(None, description="Material preferences")
    email: Optional[str] = None
    contractor_preferences: Optional[str] = Field(None, description="Small/large company preference")
    additional_notes: Optional[str] = None

    def to_bid_card_fields(self):
        """Convert to format expected by PotentialBidCardManager"""
        return {k: v for k, v in self.dict().items() if v is not None}

    def calculate_completion(self) -> int:
        """Calculate % of fields filled"""
        filled = sum(1 for v in self.dict().values() if v is not None)
        return int((filled / 12) * 100)
```

### Phase 3: Create Clean Store (15 minutes)
**File: store.py**
```python
import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from datetime import datetime

class CIAStore:
    """Handles all database operations for CIA"""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase: Client = create_client(url, key)
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Load user's conversation history and preferences"""
        # Get from unified_conversations
        result = self.supabase.table("unified_conversations").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).limit(1).execute()
        
        if result.data:
            return result.data[0]
        return {}
    
    async def save_conversation_turn(
        self, 
        conversation_id: str,
        user_message: str,
        agent_response: str,
        extracted_data: Dict[str, Any]
    ):
        """Save conversation to unified_messages"""
        # Save user message
        self.supabase.table("unified_messages").insert({
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": user_message,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        # Save agent response
        self.supabase.table("unified_messages").insert({
            "conversation_id": conversation_id,
            "sender_type": "assistant",
            "content": agent_response,
            "metadata": {"extracted_data": extracted_data},
            "created_at": datetime.now().isoformat()
        }).execute()
    
    async def get_other_projects(self, user_id: str) -> list:
        """Get user's other active projects for multi-project awareness"""
        result = self.supabase.table("bid_cards").select("*").eq(
            "user_id", user_id
        ).eq("status", "active").execute()
        
        return result.data if result.data else []
```

### Phase 4: Create Clean Agent (30 minutes)
**File: agent.py**
```python
import json
import os
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Keep the good parts!
from services.universal_session_manager import universal_session_manager
from agents.cia.potential_bid_card_integration import PotentialBidCardManager
from agents.cia.schemas import BidCardUpdate
from agents.cia.store import CIAStore
from agents.cia.prompts import get_system_prompt

load_dotenv()

class CustomerInterfaceAgent:
    """Clean CIA implementation using OpenAI tool calling"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.memory = universal_session_manager  # Keep existing memory!
        self.bid_cards = PotentialBidCardManager()  # Keep existing bid card system!
        self.store = CIAStore()
        
        # Define the extraction tool
        self.tools = [{
            "type": "function",
            "function": {
                "name": "update_bid_card",
                "description": "Update bid card with extracted information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_type": {"type": "string"},
                        "urgency": {
                            "type": "string",
                            "enum": ["emergency", "week", "month", "flexible"]
                        },
                        "location": {"type": "string"},
                        "scope_details": {"type": "string"},
                        "budget_min": {"type": "number"},
                        "budget_max": {"type": "number"},
                        "timeline": {"type": "string"},
                        "property_type": {"type": "string"},
                        "special_requirements": {"type": "string"},
                        "materials": {"type": "string"},
                        "email": {"type": "string"},
                        "contractor_preferences": {"type": "string"},
                        "additional_notes": {"type": "string"}
                    }
                }
            }
        }]
    
    async def handle_conversation(
        self,
        user_id: str,
        message: str,
        session_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main conversation handler - clean and simple"""
        
        # 1. Get or create session with memory
        session = await self.memory.get_or_create_session(user_id, session_id)
        
        # 2. Get conversation context
        context = await self.store.get_user_context(user_id)
        other_projects = await self.store.get_other_projects(user_id)
        
        # 3. Get or create bid card
        if not session.get("bid_card_id"):
            bid_card_id = await self.bid_cards.create_potential_bid_card(
                conversation_id or session_id,
                session_id,
                user_id
            )
            session["bid_card_id"] = bid_card_id
        
        # 4. Build messages for OpenAI
        messages = [
            {"role": "system", "content": get_system_prompt(context, other_projects)},
            *session.get("messages", []),
            {"role": "user", "content": message}
        ]
        
        # 5. Call OpenAI with tool
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            temperature=0.3
        )
        
        # 6. Process tool calls (extract and update bid card)
        extracted_data = {}
        for tool_call in response.choices[0].message.tool_calls or []:
            if tool_call.function.name == "update_bid_card":
                extracted_data = json.loads(tool_call.function.arguments)
                
                # Update each field in the bid card
                for field, value in extracted_data.items():
                    if value is not None:
                        await self.bid_cards.update_bid_card_field(
                            session["bid_card_id"],
                            field,
                            value
                        )
        
        # 7. Get updated bid card state
        bid_card_state = await self.bid_cards.get_bid_card_status(session["bid_card_id"])
        
        # 8. Save to memory
        await self.memory.save_message(
            user_id,
            session_id,
            message,
            response.choices[0].message.content
        )
        
        # 9. Save to database
        await self.store.save_conversation_turn(
            conversation_id or session_id,
            message,
            response.choices[0].message.content,
            extracted_data
        )
        
        # 10. Return clean response
        return {
            "response": response.choices[0].message.content,
            "bid_card_id": session["bid_card_id"],
            "extracted_data": extracted_data,
            "completion_percentage": bid_card_state.get("completion_percentage", 0),
            "bid_card_state": bid_card_state,
            "session_id": session_id
        }
```

### Phase 5: Simplified Prompts (10 minutes)
**File: prompts.py**
```python
def get_system_prompt(context: dict, other_projects: list) -> str:
    """Generate system prompt with context"""
    
    other_projects_text = ""
    if other_projects:
        projects = ", ".join([p["project_type"] for p in other_projects[:3]])
        other_projects_text = f"\n\nUser has other active projects: {projects}. Ask if this is related."
    
    return f"""You are the Customer Interface Agent (CIA) for InstaBids, helping homeowners describe their projects.

CONVERSATION RULES:
1. Extract project information naturally through conversation
2. For EMERGENCIES (flooding, fire, damage): Be brief, get location and contact immediately
3. For research phase: Focus on project details, not budget amounts
4. NEVER push for budget if not volunteered
5. Ask one question at a time, keep it conversational
6. Use the update_bid_card tool whenever you learn new information

EXTRACTION PRIORITIES:
- Emergency: project_type, urgency, location, email (skip everything else)
- Normal: project_type, scope_details, timeline, location
- Optional: budget, materials, contractor preferences

{other_projects_text}

Previous context: {context.get('last_summary', 'New conversation')}

Remember: Call update_bid_card with partial data as you learn it. Don't wait for all fields."""
```

## 🧪 TESTING PLAN

### Test 1: Basic Extraction
```python
# test_basic_extraction.py
async def test_basic():
    agent = CustomerInterfaceAgent()
    
    # Test emergency
    result = await agent.handle_conversation(
        user_id="test-user",
        message="My bathroom is flooding!",
        session_id="test-session"
    )
    assert result["extracted_data"]["urgency"] == "emergency"
    assert result["extracted_data"]["project_type"] == "bathroom"
    
    # Test follow-up
    result = await agent.handle_conversation(
        user_id="test-user",
        message="I'm at 123 Main St, zip 12345",
        session_id="test-session"
    )
    assert result["extracted_data"]["location"] == "123 Main St, zip 12345"
    assert result["completion_percentage"] > 25
```

### Test 2: Memory Persistence
```python
# test_memory.py
async def test_memory():
    agent = CustomerInterfaceAgent()
    
    # First conversation
    await agent.handle_conversation(
        user_id="test-user",
        message="Need kitchen remodel",
        session_id="session-1"
    )
    
    # Return to conversation (should remember)
    result = await agent.handle_conversation(
        user_id="test-user",
        message="Actually, also need bathroom",
        session_id="session-1"
    )
    
    # Should ask about relationship
    assert "kitchen" in result["response"].lower()
```

### Test 3: Real-time Updates
```python
# test_realtime.py
async def test_realtime_updates():
    agent = CustomerInterfaceAgent()
    
    # Check bid card updates in real-time
    result = await agent.handle_conversation(
        user_id="test-user",
        message="Kitchen remodel, about 20k budget, need it done in 2 months",
        session_id="test-session"
    )
    
    # Should extract multiple fields at once
    assert result["extracted_data"]["project_type"] == "kitchen"
    assert result["extracted_data"]["budget_max"] == 20000
    assert result["extracted_data"]["timeline"] == "2 months"
    assert result["completion_percentage"] >= 25
    
    # Verify bid card was updated
    bid_card = await agent.bid_cards.get_bid_card_status(result["bid_card_id"])
    assert bid_card["primary_trade"] == "kitchen"
```

## 📋 MIGRATION CHECKLIST

- [ ] Create `legacy/` folder
- [ ] Move old files to legacy
- [ ] Create `schemas.py` with Pydantic models
- [ ] Create `store.py` with clean database operations
- [ ] Create new `agent.py` with OpenAI tool calling
- [ ] Update `prompts.py` with simplified prompts
- [ ] Update imports in `__init__.py`
- [ ] Test basic extraction
- [ ] Test memory persistence
- [ ] Test real-time bid card updates
- [ ] Test with frontend on port 5173
- [ ] Update README.md with accurate documentation
- [ ] Delete unused files after verification

## 🎯 SUCCESS CRITERIA

1. **Code Reduction**: From 2,700 lines to ~400 lines
2. **Same Features**: All existing functionality preserved
3. **Better Performance**: Faster responses (no multiple extraction systems)
4. **Clean Architecture**: One way to do things, not 5
5. **Real Testing**: Everything verified with actual API calls
6. **Accurate Docs**: README matches actual implementation

## 🚀 EXPECTED OUTCOMES

### What You'll Have:
- Clean, maintainable CIA agent (~400 lines)
- Same memory system (universal_session_manager)
- Same bid card updates (PotentialBidCardManager)
- Same database (Supabase)
- Same frontend integration (port 5173)
- Better performance (single extraction method)
- Accurate documentation

### What You Won't Have:
- 2,300 lines of dead code
- "GPT-5" methods that don't exist
- Demo/mock systems mixed with production
- 5 different ways to extract data
- Confusion about what the agent actually does

## 📅 TIMELINE

- **Archive old code**: 5 minutes
- **Create new files**: 1 hour
- **Test everything**: 30 minutes
- **Update documentation**: 15 minutes
- **Total**: ~2 hours to clean 1+ month of technical debt

## 🎬 NEXT STEPS

1. Review this plan
2. Create legacy folder and archive old code
3. Implement clean version following this plan
4. Test with real conversations
5. Connect to frontend and verify real-time updates
6. Update README with accurate information

---

**This plan will give you the exact same CIA functionality in 400 lines instead of 2,700 lines, using modern OpenAI tool calling instead of the current mess.**
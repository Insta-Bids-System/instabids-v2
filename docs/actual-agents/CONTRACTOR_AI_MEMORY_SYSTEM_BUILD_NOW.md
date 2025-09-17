# Contractor AI Memory System - BUILD NOW
**Created**: January 14, 2025  
**Purpose**: Track contractor bidding patterns and information needs for better personalization
**Status**: Ready to implement

## 🎯 OVERVIEW

This system builds AI-powered memory about each contractor through their conversations with BSA and COIA agents. It focuses on understanding HOW they bid and WHAT information they need to bid accurately.

## 📊 SYSTEM ARCHITECTURE

### **5 Memory Tables (All in Supabase)**

#### **1. contractor_bidding_patterns_memory**
**Purpose**: Understand how each contractor approaches bidding
**Injected into Context**: YES - Used by BSA for personalized bid help

```sql
CREATE TABLE contractor_bidding_patterns_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id UUID NOT NULL REFERENCES contractors(id),
    memory_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(contractor_id)
);
```

**What Gets Tracked**:
- Typical bid ranges ($15k-$50k)
- Pricing strategies (materials+40%, labor*2.5)
- Risk padding triggers (old house = +20%)
- Win/loss patterns by project type
- Sweet spot projects they excel at
- Reasons they don't bid

#### **2. contractor_information_needs_memory**
**Purpose**: Track what info each contractor needs to bid accurately
**Injected into Context**: YES - Helps BSA know what questions to expect

```sql
CREATE TABLE contractor_information_needs_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id UUID NOT NULL REFERENCES contractors(id),
    memory_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(contractor_id)
);
```

**What Gets Tracked**:
- Critical information they always need (sqft, photos, access)
- Common questions they ask
- Photo requirements (attic, electrical panel, etc.)
- How missing info affects their pricing (+20% for unknowns)
- Past RFI requests

#### **3. contractor_relationship_memory**
**Purpose**: Personality and communication preferences
**Injected into Context**: YES - For personalization

```sql
CREATE TABLE contractor_relationship_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id UUID NOT NULL REFERENCES contractors(id),
    memory_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(contractor_id)
);
```

**What Gets Tracked**:
- Communication style (formal/casual)
- Personality traits (detail-oriented, perfectionist)
- Response patterns (immediate, business hours)
- Trust builders (transparency, expertise)

#### **4. contractor_business_profile_memory**
**Purpose**: Company intelligence for targeting
**Injected into Context**: NO - Used for analytics only

```sql
CREATE TABLE contractor_business_profile_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id UUID NOT NULL REFERENCES contractors(id),
    memory_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(contractor_id)
);
```

**What Gets Tracked**:
- Company size (employees, revenue tier)
- Service area and capacity
- Busy/slow seasons
- Current technology stack

#### **5. contractor_pain_points_memory**  
**Purpose**: Future AI solution sales intelligence
**Injected into Context**: NO - For sales team only

```sql
CREATE TABLE contractor_pain_points_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id UUID NOT NULL REFERENCES contractors(id),
    memory_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(contractor_id)
);
```

**What Gets Tracked**:
- Biggest business challenges
- Wished-for solutions
- AI interest areas
- Growth blockers

## 🔄 HOW IT WORKS

### **1. Trigger Point**
Memory updates happen **AFTER** every BSA or COIA conversation completes:
```python
# In bsa_routes_unified.py (after streaming completes)
await enhanced_memory.update_all_contractor_memories(
    contractor_id, 
    conversation_data
)
```

### **2. AI Analysis Process**
```python
async def update_all_contractor_memories(contractor_id, conversation_data):
    # Step 1: Load all current memories
    current_memories = await load_all_memories(contractor_id)
    
    # Step 2: Single GPT-4o call analyzes conversation
    prompt = f"""
    Current memories: {current_memories}
    New conversation: {conversation_data}
    
    Extract NEW insights for:
    1. Bidding patterns (how they price, what affects their bids)
    2. Information needs (what questions they ask, what photos they need)
    3. Relationship style (personality, communication preferences)
    4. Business profile (company size, capabilities)
    5. Pain points (challenges, wished solutions)
    
    Return ONLY new insights not already in memory.
    """
    
    new_insights = await gpt4o_analyze(prompt)
    
    # Step 3: Update only tables with new insights
    if new_insights.bidding:
        await update_bidding_memory(contractor_id, new_insights.bidding)
    # ... etc for all 5 tables
```

### **3. Memory Injection into Context**
When contractor starts new conversation:
```python
# Only bidding + information + relationship memories get injected
bidding_memory = await get_bidding_patterns_memory(contractor_id)
info_memory = await get_information_needs_memory(contractor_id)  
relationship_memory = await get_relationship_memory(contractor_id)

system_prompt += f"""
## Contractor Intelligence:

### Bidding Patterns:
- Typical range: {bidding_memory['typical_bid_range']}
- Wins on: {bidding_memory['win_rate_patterns']}
- Risk padding triggers: {bidding_memory['risk_padding_triggers']}

### Information Needs:
- Always asks about: {info_memory['common_questions_asked']}
- Needs photos of: {info_memory['photo_requirements']}
- Missing info adds: {info_memory['increases_bid_by']}

### Communication Style:
- Prefers: {relationship_memory['communication_style']}
- Personality: {relationship_memory['personality_traits']}
"""
```

## 📈 EXAMPLE MEMORY EVOLUTION

### **After First BSA Conversation**:
```json
{
  "bidding_patterns": {
    "typical_bid_range": "$20k-40k",
    "sweet_spot_projects": ["kitchen remodels"]
  },
  "information_needs": {
    "common_questions_asked": ["What's the age of the house?"]
  }
}
```

### **After Second Conversation**:
```json
{
  "bidding_patterns": {
    "typical_bid_range": "$20k-40k",
    "sweet_spot_projects": ["kitchen remodels", "bathroom renovations"],
    "risk_padding_triggers": ["old plumbing", "no attic access"]
  },
  "information_needs": {
    "common_questions_asked": ["What's the age of the house?", "Any water damage?"],
    "photo_requirements": ["all angles", "under sink"]
  }
}
```

### **After Multiple Conversations**:
```json
{
  "bidding_patterns": {
    "typical_bid_range": "$20k-40k",
    "sweet_spot_projects": ["kitchen remodels", "bathroom renovations"],
    "risk_padding_triggers": ["old plumbing", "no attic access"],
    "pricing_factors": ["materials+35%", "labor*2.5"],
    "win_rate_by_type": {"kitchens": "65%", "bathrooms": "45%"},
    "no_bid_triggers": ["rental properties", "DIY comparison"]
  },
  "information_needs": {
    "common_questions_asked": [
      "What's the age of the house?",
      "Any water damage?",
      "When was last renovation?",
      "HOA restrictions?"
    ],
    "photo_requirements": ["all angles", "under sink", "attic access", "electrical panel"],
    "reduces_bid_by": {
      "clear attic access": "10%",
      "newer construction": "15%"
    },
    "increases_bid_by": {
      "unknown conditions": "25%",
      "rush job": "30%"
    }
  }
}
```

## 🚀 IMPLEMENTATION STEPS

### **Phase 1: Database Setup**
1. Create all 5 memory tables in Supabase
2. Add indexes on contractor_id for performance

### **Phase 2: Memory System Integration**
1. Update `enhanced_contractor_memory.py` with 5-table system
2. Integrate into BSA router (`bsa_routes_unified.py`)
3. Add to COIA router when contractor onboards

### **Phase 3: Testing**
1. Test memory creation from conversations
2. Verify memory merging (no duplicates)
3. Confirm context injection works
4. Monitor GPT-4o token usage

## 🎯 VALUE PROPOSITION

### **Immediate Benefits**:
- BSA knows how each contractor bids → better proposals
- System knows what info they need → fewer RFIs
- Personalized communication → higher engagement

### **Long-term Benefits**:
- Identify contractors bidding too high/low → coaching opportunity
- Understand information gaps → better bid cards
- Build AI sales pipeline → future revenue

## 📊 SUCCESS METRICS

- Memory builds successfully after conversations ✓
- Context injection improves BSA responses ✓
- Contractors feel "understood" by the system ✓
- Reduced RFI requests over time ✓
- More accurate initial bids ✓

---

**This is the CURRENT BUILD - focused on making our existing BSA/COIA agents smarter through contractor memory.**
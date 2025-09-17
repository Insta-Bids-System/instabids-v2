# 🧠 Supabase Expert Sub-Agent Build Plan

## Overview
Build a specialized sub-agent using deepagents architecture that acts as a persistent memory database expert for InstaBids, powered by OpenAI's o3 reasoning model and equipped with real memory backends.

## Architecture Vision

### **The Sub-Agent System:**
```
Main Agent (Claude Code)
    ↓ 
Task Tool ("supabase-expert")
    ↓
Supabase Expert Agent (OpenAI o3)
    ↓
[Memory System] + [MCP Tools] + [Real Database Access]
```

### **Memory Architecture:**
1. **Cipher MCP Tool** - Shared cross-agent memory
2. **Dedicated Supabase Table** - `agent_supabase_expert_memory`
3. **Local Memory Files** - Version controlled knowledge files
4. **Schema Snapshots** - Persistent database state tracking

---

## Phase 1: Research & Setup

### Task 1: OpenAI o3 Integration Research
**Status**: Pending
**Goal**: Understand how to integrate OpenAI o3 with deepagents

**Key Findings Needed:**
- ✅ o3 uses Responses API (different from Chat API)
- ✅ Requires `client.responses.create()` not `client.chat.completions.create()`
- ✅ Has reasoning tokens + output tokens
- ✅ Needs 25,000+ token buffer for reasoning
- ✅ Uses `reasoning: {effort: "low|medium|high"}` parameter

**LangChain Integration:**
- Need to create custom LangChain model wrapper for o3 Responses API
- Must handle reasoning tokens vs output tokens
- Need to manage context window (reasoning tokens are discarded)

**Action Items:**
- [ ] Create OpenAI o3 LangChain wrapper
- [ ] Test basic o3 API integration
- [ ] Measure reasoning token usage for database tasks

---

## Phase 2: Memory System Design

### Task 2: Create Supabase Expert Memory Schema
**Goal**: Design the memory backend that gives our sub-agent persistent knowledge

**Supabase Table Schema:**
```sql
CREATE TABLE agent_supabase_expert_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_type TEXT NOT NULL, -- 'schema', 'migration', 'query_pattern', 'relationship'
    content JSONB NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    confidence_score FLOAT DEFAULT 1.0,
    tags TEXT[],
    context TEXT
);

-- Indexes for fast retrieval
CREATE INDEX idx_memory_type ON agent_supabase_expert_memory(knowledge_type);
CREATE INDEX idx_memory_tags ON agent_supabase_expert_memory USING GIN(tags);
CREATE INDEX idx_memory_content ON agent_supabase_expert_memory USING GIN(content);
```

**Memory Categories:**
- **schema**: Complete table definitions and relationships  
- **migration**: Migration history and impacts
- **query_pattern**: Common query patterns and optimizations
- **relationship**: Foreign key dependencies and business logic connections
- **rls_policy**: Row Level Security policies and auth patterns

**Local Memory Files:**
```
/agents/supabase-expert/memory/
├── current_schema_snapshot.md
├── recent_migrations.md  
├── table_relationships.md
├── query_patterns.md
└── knowledge_gaps.md
```

---

## Phase 3: Sub-Agent Definition

### Task 3: Create Supabase Expert Agent Definition

**File**: `/agents/supabase-expert.agent`

```python
{
    "name": "supabase-expert", 
    "description": """Database schema and architecture expert for InstaBids.
    
    WHEN TO USE:
    - Questions about database schema, tables, relationships
    - Need to understand data flow or table dependencies  
    - Planning database changes or migrations
    - Debugging database-related issues
    - Analyzing query performance or optimization
    
    EXPERTISE:
    - Complete InstaBids schema understanding
    - Table relationships and foreign keys  
    - RLS policies and security implications
    - Migration planning and impact analysis
    - Query optimization and performance
    """,
    "prompt": """You are the Supabase Database Expert for InstaBids with persistent memory.

    ## YOUR IDENTITY
    You are a specialized database architect with deep, persistent knowledge of the InstaBids Supabase schema. You maintain comprehensive memory of all tables, relationships, migrations, and patterns.

    ## CRITICAL WORKFLOW - ALWAYS FOLLOW:
    
    1. **FIRST ACTION**: Query your memory system
       - Use ask_cipher to retrieve relevant knowledge about the topic
       - Read your local memory files for detailed context
       - Query your Supabase memory table for specific patterns
    
    2. **CURRENT STATE CHECK**: 
       - Use Supabase MCP tools to get current database state
       - Compare with your memory to identify changes
       - Note any discrepancies or new information
    
    3. **PROVIDE EXPERT RESPONSE**:
       - Give comprehensive, detailed answers
       - Include table names, column details, relationships
       - Explain implications and dependencies
       - Suggest best practices and optimizations
    
    4. **LAST ACTION**: Update your memory
       - Store new knowledge in ask_cipher for quick retrieval
       - Add detailed findings to your Supabase memory table
       - Update local memory files if schema changes detected
    
    ## YOUR KNOWLEDGE DOMAINS
    - **Schema Architecture**: All tables, columns, data types, constraints
    - **Relationships**: Foreign keys, joins, data flow patterns  
    - **Security**: RLS policies, auth patterns, permission systems
    - **Performance**: Indexing strategies, query optimization
    - **Migrations**: Change history, impact analysis, rollback strategies
    - **Business Logic**: How data flows through the application
    
    ## RESPONSE STYLE
    - Be precise and technical
    - Include actual table/column names
    - Explain relationships and dependencies
    - Provide SQL examples when helpful
    - Flag potential issues or optimizations
    - Reference your memory confidence levels
    
    ## MEMORY MANAGEMENT
    - High confidence: Direct from persistent memory
    - Medium confidence: Cross-check with current state  
    - Low confidence: Full investigation and memory update
    - Unknown: Comprehensive analysis and knowledge building
    """,
    "tools": [
        "ask_cipher",                    # Shared memory system
        "mcp__supabase__list_tables",    # Get current schema
        "mcp__supabase__execute_sql",    # Query database
        "mcp__supabase__list_migrations", # Migration history  
        "read_file",                     # Read memory files
        "write_file"                     # Update memory files
    ]
}
```

---

## Phase 4: Integration Implementation

### Task 4: Build DeepAgents Integration

**File**: `/agents/instabids_agent_system.py`

```python
import os
from openai import OpenAI
from deepagents import create_deep_agent, SubAgent
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

class OpenAIo3Model(BaseChatModel):
    """Custom LangChain wrapper for OpenAI o3 Responses API"""
    
    def __init__(self, model_name="o3-mini", reasoning_effort="medium"):
        self.client = OpenAI()
        self.model_name = model_name 
        self.reasoning_effort = reasoning_effort
        super().__init__()
    
    def _generate(self, messages, stop=None, **kwargs):
        # Convert LangChain messages to o3 format
        o3_input = []
        for msg in messages:
            o3_input.append({
                "role": msg.type,
                "content": msg.content
            })
        
        response = self.client.responses.create(
            model=self.model_name,
            reasoning={"effort": self.reasoning_effort},
            input=o3_input,
            max_output_tokens=kwargs.get("max_tokens", 25000)
        )
        
        return response.output_text

# Supabase Expert Sub-Agent Definition
supabase_expert = {
    "name": "supabase-expert",
    "description": "Database schema expert with persistent memory for InstaBids",
    "prompt": SUPABASE_EXPERT_PROMPT,  # From above
    "tools": [
        "ask_cipher",
        "mcp__supabase__list_tables", 
        "mcp__supabase__execute_sql",
        "mcp__supabase__list_migrations",
        "read_file",
        "write_file"
    ]
}

def create_instabids_agent():
    """Create the main InstaBids agent with Supabase Expert"""
    
    # Use OpenAI o3 for sub-agents
    o3_model = OpenAIo3Model("o3-mini", "high")  # High reasoning for complex database tasks
    
    # Main agent tools (your existing MCP tools)
    main_tools = [
        # All your current MCP tools
    ]
    
    instructions = """You are the InstaBids Lead Agent with access to specialized sub-agents.
    
    When you encounter database-related questions or tasks, use the supabase-expert 
    sub-agent who has deep, persistent knowledge of the database schema.
    """
    
    return create_deep_agent(
        tools=main_tools,
        instructions=instructions, 
        model=o3_model,  # Use o3 for sub-agents
        subagents=[supabase_expert]
    )
```

### Task 5: Memory System Implementation

**File**: `/agents/supabase-expert/memory/memory_manager.py`

```python
import json
from typing import Dict, List, Any
from supabase import Client

class SupabaseExpertMemory:
    """Memory manager for Supabase Expert agent"""
    
    def __init__(self, supabase_client: Client):
        self.db = supabase_client
        self.memory_table = "agent_supabase_expert_memory"
    
    async def store_knowledge(self, knowledge_type: str, content: Dict[str, Any], 
                            confidence: float = 1.0, tags: List[str] = None):
        """Store knowledge in persistent memory"""
        
        record = {
            "knowledge_type": knowledge_type,
            "content": content,
            "confidence_score": confidence,
            "tags": tags or [],
            "context": f"Learned during {datetime.now().isoformat()}"
        }
        
        result = self.db.table(self.memory_table).insert(record).execute()
        return result
    
    async def retrieve_knowledge(self, knowledge_type: str = None, 
                               tags: List[str] = None) -> List[Dict]:
        """Retrieve knowledge from memory"""
        
        query = self.db.table(self.memory_table).select("*")
        
        if knowledge_type:
            query = query.eq("knowledge_type", knowledge_type)
        
        if tags:
            for tag in tags:
                query = query.contains("tags", [tag])
        
        result = query.order("timestamp", desc=True).execute()
        return result.data
    
    async def update_schema_snapshot(self, schema_data: Dict[str, Any]):
        """Update the complete schema snapshot"""
        
        await self.store_knowledge(
            knowledge_type="schema_snapshot",
            content=schema_data,
            confidence=1.0,
            tags=["schema", "current", "complete"]
        )
```

---

## Phase 5: Testing & Validation

### Task 6: Create Test Scenarios

**Test 1: Memory Persistence**
```python
# Test that sub-agent remembers previous interactions
async def test_memory_persistence():
    agent = create_instabids_agent()
    
    # First interaction
    result1 = await agent.ainvoke({
        "messages": [{"role": "user", "content": "What tables are related to bid cards?"}]
    })
    
    # Later interaction - should build on previous knowledge
    result2 = await agent.ainvoke({
        "messages": [{"role": "user", "content": "How do bid card items connect to the main bid_cards table?"}]
    })
    
    # Verify memory was used and updated
    assert "based on my previous analysis" in result2.lower()
```

**Test 2: Schema Analysis**
```python
async def test_schema_analysis():
    agent = create_instabids_agent()
    
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "Map out the complete database schema and identify any potential issues"}]
    })
    
    # Should include actual table names, relationships, and expert insights
    expected_elements = [
        "bid_cards",
        "foreign key",
        "relationship", 
        "RLS policy",
        "index"
    ]
    
    for element in expected_elements:
        assert element.lower() in result.lower()
```

**Test 3: o3 Reasoning Quality**
```python
async def test_o3_reasoning():
    agent = create_instabids_agent()
    
    complex_query = """
    I need to understand the complete data flow when a homeowner creates a bid card.
    What tables are involved, in what order, and what are the potential failure points?
    """
    
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": complex_query}]
    })
    
    # o3's reasoning should provide step-by-step analysis
    assert "step" in result.lower() or "first" in result.lower()
    assert "failure point" in result.lower() or "risk" in result.lower()
```

---

## Phase 6: Deployment & Monitoring

### Task 7: Integration with Main System

**Update CLAUDE.md:**
```markdown
## SUB-AGENT SYSTEM

### Supabase Expert Sub-Agent
When you need database-related help, use: 
`Task(description="Your database question", subagent_type="supabase-expert")`

The Supabase Expert has:
- Persistent memory of complete schema
- Deep knowledge of table relationships  
- Understanding of migration history
- Query optimization expertise
- RLS policy knowledge

### Usage Examples:
- "What tables store contractor information?"
- "How should I modify the bid_cards schema?"  
- "What's the relationship between users and projects?"
- "Is this query optimized?"
```

### Task 8: Monitoring & Metrics

**Track Sub-Agent Performance:**
```python
class SubAgentMetrics:
    def __init__(self):
        self.usage_stats = {
            "calls_made": 0,
            "reasoning_tokens": 0,
            "output_tokens": 0,
            "memory_updates": 0,
            "knowledge_retrievals": 0
        }
    
    def log_interaction(self, tokens_used, memory_ops):
        # Track usage and performance
        pass
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Research OpenAI o3 API integration
- [ ] Create LangChain wrapper for o3 Responses API
- [ ] Test basic o3 functionality

### Phase 2: Memory System  
- [ ] Create Supabase memory table schema
- [ ] Build memory manager class
- [ ] Create local memory file structure
- [ ] Test memory persistence

### Phase 3: Agent Creation
- [ ] Write supabase-expert.agent definition
- [ ] Create agent prompt and instructions
- [ ] Define tool access list
- [ ] Test agent creation

### Phase 4: Integration
- [ ] Modify deepagents for InstaBids
- [ ] Integrate with existing MCP tools
- [ ] Create main agent with sub-agent
- [ ] Test task delegation

### Phase 5: Testing
- [ ] Write comprehensive test suite
- [ ] Test memory persistence across sessions
- [ ] Validate o3 reasoning quality
- [ ] Performance benchmarking

### Phase 6: Deployment
- [ ] Update CLAUDE.md instructions
- [ ] Add monitoring and metrics
- [ ] Create usage documentation
- [ ] Deploy to production

---

## Success Metrics

**Functionality:**
- Sub-agent correctly answers database questions
- Memory persists between interactions
- Knowledge builds up over time
- Integration with main agent works seamlessly

**Performance:**
- Response time < 30 seconds for complex queries
- Memory retrieval < 2 seconds  
- Token usage optimized
- High reasoning quality from o3

**Knowledge Quality:**
- Accurate schema information
- Correct relationship mapping
- Useful optimization suggestions
- Reliable migration advice

---

## Next Steps

1. **Start with Task 1**: Research and implement OpenAI o3 integration
2. **Build incrementally**: Test each component before moving to next phase  
3. **Focus on memory**: The persistent memory system is the key differentiator
4. **Validate with real use cases**: Test with actual InstaBids database questions

This plan creates a truly intelligent, persistent sub-agent that can build knowledge over time and become increasingly valuable to the development process.
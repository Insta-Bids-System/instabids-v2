# BSA (Bid Submission Agent) 🏗️

**Version**: 2.0 (DeepAgents Framework)  
**Status**: Production Ready  
**Last Updated**: August 20, 2025  

## 🎯 Overview

BSA (Bid Submission Agent) is a sophisticated AI agent that helps contractors transform natural language input into professional bid proposals. Built on the DeepAgents framework with 4 specialized sub-agents, BSA provides intelligent project search, market analysis, and proposal optimization for the InstaBids platform.

### Key Features
- **🔍 Intelligent Project Search** - Geographic and semantic bid card matching
- **📊 Market Intelligence** - Real-time pricing and competition analysis  
- **📝 Proposal Optimization** - Professional bid generation from casual input
- **👥 Group Bidding** - Multi-project coordination and bulk pricing
- **🧠 Memory Persistence** - Cross-session conversation continuity
- **⚡ Real-time Streaming** - Live SSE responses with sub-agent progress

---

## 📁 Project Structure

```
agents/bsa/
├── README.md                           # This file
├── agent.py                           # Main BSA agent (1,225 lines)
├── memory_integration.py              # Memory persistence system
├── enhanced_tools.py                  # Standalone BSA tools
├── sub_agents/                        # Specialized sub-agents
│   ├── bid_card_search_agent.py      # Project finding specialist
│   ├── bid_submission_agent.py       # Proposal optimization
│   ├── market_research_agent.py      # Market intelligence
│   └── group_bidding_agent.py        # Multi-project coordination
├── docs/                              # Documentation
│   ├── BSA_COMPLETE_MEMORY_SYSTEM_MAP.md
│   └── DEEPAGENTS_VS_UNIFIED_MEMORY_EXPLAINED.md
└── tests/                             # Test files
    ├── test_bsa_flow_verification.py
    ├── test_bsa_memory_system.py
    └── test_bsa_streaming.py
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- OpenAI API key (GPT-5/GPT-4o)
- Supabase access
- DeepAgents framework

### Installation
```bash
# BSA is part of the InstaBids monorepo
cd ai-agents/agents/bsa

# Install dependencies (from project root)
pip install -r requirements.txt
```

### Basic Usage
```python
from agents.bsa.agent import create_bsa_agent, process_contractor_input_streaming

# Create BSA agent
agent = create_bsa_agent()

# Process contractor input (streaming)
async for chunk in process_contractor_input_streaming(
    bid_card_id="project-123",
    contractor_id="contractor-456", 
    input_type="text",
    input_data="I can do this kitchen remodel for 45k in 8 weeks"
):
    print(chunk)
```

---

## 🌐 API Endpoints

### Main Endpoints
```http
POST /api/bsa/unified-stream
Content-Type: application/json

{
  "contractor_id": "contractor-123",
  "message": "find me turf projects around 33442",
  "session_id": "optional-session-id"
}
```

**Response**: Server-Sent Events (SSE) stream with real-time updates

### Context Loading
```http
GET /api/bsa/contractor/{contractor_id}/context
```

**Response**: Contractor profile, conversation history, bid analytics

### Legacy Compatibility  
```http
POST /api/bsa/fast-stream
```
*Delegates to unified-stream for backward compatibility*

---

## ⚙️ Sub-Agent Architecture

BSA employs 4 specialized sub-agents for complex task delegation:

### 1. Bid Card Search Agent 🔍
**Purpose**: Find relevant projects for contractors  
**Capabilities**:
- Geographic radius search (ZIP + miles)
- Semantic project matching  
- Trade-specific filtering
- Relevance scoring

**Tools**: `search_available_bid_cards`, `find_similar_contractors`

### 2. Market Research Agent 📊  
**Purpose**: Pricing and competition analysis  
**Capabilities**:
- Current market rate analysis
- Competitive landscape research
- Pricing trend identification
- Cost estimation models

**Tools**: `analyze_market_rates`, `research_contractor_company`

### 3. Bid Submission Agent 📝
**Purpose**: Proposal optimization and formatting  
**Capabilities**:
- Professional proposal generation
- Trade-specific expertise application
- Timeline and pricing extraction
- Submission strategy advice

**Tools**: Integrated with main agent tools

### 4. Group Bidding Agent 👥
**Purpose**: Multi-project coordination  
**Capabilities**:
- Bulk project identification
- Resource allocation planning
- Coordinated submission timing
- Volume discount calculation

**Tools**: Project bundling and scheduling algorithms

---

## 🧠 Memory System

BSA implements a sophisticated 4-tier memory architecture with 3 active systems:

### Primary: Unified Memory System ✅ ACTIVE
- **Status**: FULLY OPERATIONAL
- **Table**: `unified_conversation_memory` (663 records)
- **Fields**: 34 BSA-specific fields
- **Purpose**: Cross-session conversation persistence
- **When Updated**: After each conversation turn

```python
BSA_MEMORY_FIELDS = [
    # Core identification
    "contractor_id", "session_id", "agent_type", "last_updated",
    
    # DeepAgents built-in state
    "messages", "todos", "files",
    
    # BSA-specific analysis data  
    "bid_card_analysis", "market_research", "group_bidding_analysis", 
    "sub_agent_calls", "found_bid_cards", "current_search_criteria",
    
    # Contractor context
    "contractor_profile", "current_bid_cards", "submission_history", 
    "pricing_models", "trade_specialization", "contractor_preferences",
    
    # Conversation context
    "conversation_context", "session_metadata", "bid_submission_history",
    "market_research_data", "group_bidding_state", "sub_agent_context"
    # ... (34 total fields)
]
```

### Secondary: AI Memory Extraction System ✅ ACTIVE
- **Status**: FULLY INTEGRATED AND OPERATIONAL  
- **Table**: `contractor_ai_memory` - AI-extracted business insights
- **Purpose**: Deep contractor insights via GPT-4o analysis
- **Fields**: 9 AI memory fields extracted per conversation
- **When Updated**: After each conversation turn (lines 280-298 in bsa_stream.py)

#### ✅ ACTIVE INTEGRATION - Working Since August 2025:
```python
# This IS called after each BSA conversation turn:
from memory.contractor_ai_memory import ContractorAIMemory

ai_memory = ContractorAIMemory()  # Initialized in bsa_stream.py:32

# After processing contractor message (bsa_stream.py:282-296):
if full_response:
    conversation_data = {
        'input': request.message,
        'response': full_response,
        'context': f"BSA conversation for contractor {request.contractor_id}",
        'project_type': 'contractor_bidding'
    }
    
    # Extract and save AI insights asynchronously (CURRENTLY HAPPENING!)
    asyncio.create_task(ai_memory.update_contractor_memory(
        contractor_id=request.contractor_id,
        conversation_data=conversation_data
    ))
```

#### 9 AI Memory Fields Extracted:
1. personal_preferences (work style, scheduling, materials)
2. communication_style (formal/casual, detail-oriented, direct)
3. business_focus (specialties, market segments)
4. pricing_patterns (premium/budget, fixed/flexible)
5. project_preferences (size, complexity, timeline)
6. customer_relationship_style (consultative, transactional)
7. quality_standards (perfectionist, practical, efficient)
8. total_updates (count of AI analysis runs)
9. last_updated (timestamp of most recent analysis)

### Tertiary: My Bids Tracking System ✅ ACTIVE
- **Status**: FULLY INTEGRATED AND OPERATIONAL
- **Service**: `services/my_bids_tracker.py`
- **Purpose**: Track contractor bid card interactions and engagement patterns
- **When Updated**: Every BSA conversation with bid_card_id (lines 301-309 in bsa_stream.py)
- **Tables**: `my_bids`, `bid_cards`, `contractor_proposals`, `messages`

### Quaternary: DeepAgents Memory ❌ NOT USED
- **Status**: Available but NOT implemented for BSA
- **Table**: `deepagents_memory` (9 records from other agents only)
- **Reason**: BSA uses unified memory instead
- **Potential Use**: Could enable cross-session agent learning

### Memory Integration Flow
```python
# Current implementation (COMPLETE with all 3 active systems):
from agents.bsa.memory_integration import BSAMemoryIntegrator
from memory.contractor_ai_memory import ContractorAIMemory
from services.my_bids_tracker import my_bids_tracker

integrator = BSAMemoryIntegrator()
ai_memory = ContractorAIMemory()

# 1. Restore state at conversation start
state = await integrator.restore_deepagents_state(contractor_id)

# 2. Load My Bids context 
my_bids_context = await my_bids_tracker.load_full_my_bids_context(contractor_id)

# 3. Save state after each turn
await integrator.save_deepagents_state(contractor_id, state)

# 4. ✅ ACTIVE: AI extraction happens after each conversation
await ai_memory.update_contractor_memory(contractor_id, conversation_data)

# 5. ✅ ACTIVE: Track bid card interactions
if bid_card_id:
    await my_bids_tracker.track_bid_interaction(contractor_id, bid_card_id, 'message_sent')
```

### Context Loading in BSA
The `/api/bsa/contractor/{contractor_id}/context` endpoint loads:
- ✅ Basic contractor profile from `contractors` table  
- ✅ Bid cards contractor has interacted with (viewed, bid on, invited to)
- ✅ Campaign participation data
- ✅ Outreach history
- ✅ AI-extracted contractor insights (from contractor_ai_memory table)
- ✅ My Bids tracking and engagement patterns
- ✅ Conversation history and relationship building data

**Context Count**: The "total_context_items" shows how many data categories contain data.
With full memory integration, established contractors will have rich context (10+ items).

---

## 🗄️ Database Schema

### Core Tables (32 BSA-related tables)

#### Bid System
- `bid_cards` - Project listings BSA searches
- `bids` - Contractor submissions via BSA
- `contractor_bids` - BSA-generated proposals  
- `contractor_proposals` - BSA-optimized submissions
- `potential_bid_cards` - Draft projects

#### Contractor Profiles
- `contractors` - Registered contractor profiles
- `contractor_leads` - Discovery data for research
- `contractor_business_profile` - Company intelligence
- `contractor_bidding_patterns` - Learning data

#### Analytics & Tracking
- `bid_card_views` - Search analytics
- `bid_card_engagement_events` - Interaction tracking
- `contractor_engagement_summary` - Performance metrics

#### Group Bidding
- `group_bidding_pools` - Multi-project coordination
- `group_bidding_categories` - Project classification
- `group_bids` - Bulk submissions

*Plus 18 additional supporting tables for comprehensive functionality*

---

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key           # Primary LLM
ANTHROPIC_API_KEY=your_anthropic_key     # Fallback (optional)
SUPABASE_URL=your_supabase_url           # Database
SUPABASE_KEY=your_supabase_key           # Database auth
```

### BSA Settings
```python
# Default search radius
DEFAULT_SEARCH_RADIUS = 30  # miles

# Memory timeout  
MEMORY_LOAD_TIMEOUT = 3.0   # seconds

# Conversation history limit
MAX_CONVERSATION_HISTORY = 10  # messages

# Model preferences
PRIMARY_MODEL = "gpt-5"        # First choice
FALLBACK_MODEL = "gpt-4o"      # Backup
```

---

## 🔄 Service Complexity Routing

BSA automatically routes requests based on project complexity:

### Single-Trade Projects
- **Examples**: Lawn care, roofing, single-room painting
- **Route**: → Bid Card Search Agent
- **Strategy**: Specialized matching and direct bidding

### Multi-Trade Projects  
- **Examples**: Kitchen remodel, bathroom renovation
- **Route**: → Market Research Agent
- **Strategy**: Coordination analysis and timeline planning

### Complex Coordination
- **Examples**: Whole house renovation, additions
- **Route**: → Group Bidding Agent  
- **Strategy**: Advanced project management and resource allocation

```python
# Automatic routing example
classification = complexity_router.classify_project_complexity(
    project_type="kitchen remodel",
    description="Full kitchen renovation with appliances",
    trade_count=4
)
# Result: routes to Market Research Agent for multi-trade coordination
```

---

## 🖥️ Frontend Integration

### React Components
BSA integrates with several React components:

#### Primary Interface
```typescript
// BSAChat.tsx - Main chat interface
import BSAChat from '@/components/chat/BSAChat';

<BSAChat 
  contractorId="contractor-123"
  onBidCardsFound={handleBidCards}
  onContextLoaded={handleContext}
/>
```

#### Bid Display
```typescript
// BSABidCardsDisplay.tsx - Results visualization
import BSABidCardsDisplay from '@/components/chat/BSABidCardsDisplay';

<BSABidCardsDisplay 
  bidCards={searchResults}
  onCardSelect={handleSelection}
/>
```

### SSE Events Handled
- `bid_cards_found` - Display search results
- `sub_agent_status` - Show progress updates
- `radius_info` - Geographic search feedback
- `match_confirmation` - Result validation
- `borderline_questions` - Clarification requests
- `clarifying_questions` - Search refinement

---

## 🔗 Integration Points

### Agent Interactions
- **CIA (Customer Interface Agent)**:
  - Shares contractor context and potential bid cards
  - Provides homeowner-generated project data

- **COIA (Contractor Onboarding & Intelligence Agent)**:
  - Supplies contractor discovery and profile data
  - Feeds business intelligence for market research

- **JAA (Job Assessment Agent)**:
  - Receives bid updates for project assessment
  - Provides pricing validation and recommendations

- **IRIS (Inspiration & Research Intelligence System)**:
  - No direct integration (different user base)
  - Could potentially share market trend data

### External APIs
- **OpenAI GPT-5/GPT-4o**: Primary language model
- **Supabase**: Database operations and real-time updates
- **Google Places API**: Geographic search enhancement (via COIA)

---

## 📊 Performance & Monitoring

### Performance Targets
- **Response Time**: <5 seconds for bid search
- **Memory Loading**: 3-second timeout with graceful fallback
- **Streaming Latency**: <200ms per chunk
- **Search Accuracy**: >85% relevance score

### Monitoring Metrics
```python
# Key performance indicators
{
  "search_requests_per_minute": 150,
  "avg_response_time_ms": 3200,
  "memory_hit_rate": 0.92,
  "bid_conversion_rate": 0.34,
  "user_satisfaction_score": 4.6
}
```

### Error Handling
- Graceful degradation when APIs unavailable
- Fallback to cached data when possible
- Comprehensive logging for debugging
- User-friendly error messages

---

## 🧪 Testing

### Test Files
```bash
# Run BSA tests
cd tests/bsa/

# Flow verification
python test_bsa_flow_verification.py

# Memory system testing  
python test_bsa_memory_system.py

# Streaming functionality
python test_bsa_streaming.py
```

### Test Coverage
- ✅ End-to-end conversation flows
- ✅ Memory persistence and restoration
- ✅ Sub-agent delegation
- ✅ Streaming API functionality
- ✅ Error handling and edge cases

### Manual Testing
```python
# Test streaming endpoint
import requests

response = requests.post(
    "http://localhost:8008/api/bsa/unified-stream",
    json={
        "contractor_id": "test-contractor",
        "message": "find turf projects near 33442",
        "session_id": "test-session"
    },
    stream=True
)

for chunk in response.iter_content(chunk_size=None):
    print(chunk.decode())
```

---

## 🔐 Security & Privacy

### Data Protection
- **Contractor Privacy**: All data filtered for privacy compliance
- **Session Isolation**: Memory data segregated by contractor
- **API Security**: Rate limiting and authentication required
- **Database Security**: Row-level security via Supabase

### Access Control
```python
# Contractor data access validation
async def validate_contractor_access(contractor_id: str, session_id: str):
    # Verify contractor owns the session
    # Check data access permissions
    # Apply privacy filters
    pass
```

---

## 🚀 Deployment

### Production Setup
```bash
# Docker deployment (recommended)
docker-compose up -d

# Environment verification
curl http://localhost:8008/api/bsa/contractor/test-id/context
```

### Scaling Considerations
- **Horizontal Scaling**: Stateless design supports multiple instances
- **Database Scaling**: Optimized queries with proper indexing
- **Memory Management**: Efficient state serialization
- **Rate Limiting**: Per-contractor request throttling

---

## 📈 Roadmap & Future Enhancements

### Planned Features
- [ ] **Advanced ML Models**: Custom bid optimization models
- [ ] **Voice Input**: Speech-to-text integration for proposals
- [ ] **Document Analysis**: PDF estimate parsing and enhancement
- [ ] **Market Predictions**: AI-powered pricing forecasts
- [ ] **Mobile App**: Native mobile interface

### Technical Improvements
- [ ] **Performance Optimization**: Sub-second response times
- [ ] **Enhanced Caching**: Redis integration for frequently accessed data
- [ ] **A/B Testing**: Proposal effectiveness measurement
- [ ] **Advanced Analytics**: Contractor success pattern analysis

---

## 🤝 Contributing

### Development Guidelines
1. **Code Style**: Follow PEP 8 standards
2. **Testing**: All new features require tests
3. **Documentation**: Update README for significant changes
4. **Memory**: Consider impact on memory system design

### File Organization Rules
```bash
# New test files go here:
tests/bsa/test_[feature]_[date].py

# Archive old tests:
test-archive/old_test_files/

# Maximum 3 active test files per agent
```

### Pull Request Process
1. Create feature branch from main
2. Implement changes with tests
3. Update documentation
4. Submit PR with detailed description

---

## 📞 Support & Troubleshooting

### Common Issues

#### Memory Not Loading
```python
# Check memory integrator status
integrator = await get_bsa_memory_integrator()
state = await integrator.restore_deepagents_state(contractor_id)
print(f"Memory state: {len(state.get('messages', []))} messages")
```

#### Sub-Agent Not Responding
```python
# Verify sub-agent tools availability
from agents.bsa.enhanced_tools import BSA_ENHANCED_TOOLS
print(f"Available tools: {len(BSA_ENHANCED_TOOLS)}")
```

#### Streaming Connection Issues
```bash
# Test endpoint directly
curl -X POST "http://localhost:8008/api/bsa/unified-stream" \
  -H "Content-Type: application/json" \
  -d '{"contractor_id":"test","message":"test"}'
```

### Debug Mode
```python
# Enable detailed logging
import logging
logging.getLogger("agents.bsa").setLevel(logging.DEBUG)
```

### Contact Information
- **Technical Issues**: Check InstaBids internal documentation
- **Agent Behavior**: Review BSA memory system documentation
- **API Questions**: Reference OpenAPI specifications
- **Database Issues**: Consult Supabase logs

---

## 📄 License

This BSA agent is part of the InstaBids platform and subject to InstaBids proprietary licensing.

---

**BSA Agent - Transforming Contractor Communication into Professional Opportunities** 🏗️✨
# IRIS Agent Complete Rebuild Plan & Implementation Guide
**Date**: January 25, 2025  
**Current Status**: 2,290-line monolithic disaster  
**Target Status**: Clean, modular architecture (~500 lines total)  
**Purpose**: Complete rebuild preserving ALL functionality

## 📊 Current State Analysis

### File Statistics
- **Main agent.py**: 2,290 lines (unmaintainable)
- **Total Python files**: 8 files, 4,547 lines
- **Archive/backup files**: 6 different broken attempts
- **Methods in agent.py**: 46 methods (21 async)

### Core Problems
1. **Monolithic Structure**: Everything in one massive file
2. **Mixed Responsibilities**: Photo storage + AI + memory + workflows + API
3. **Poor Room Detection**: Keywords only, defaults to "backyard"
4. **No Real Image Analysis**: Just text parsing
5. **Complex Workflows**: Overly complicated branching logic
6. **Technical Debt**: 6 archived attempts show repeated failures

## 🎯 What IRIS Actually Does (Feature Audit)

### 1. Photo Management
- **Upload photos** with base64 encoding
- **Detect rooms** from message text (keyword matching)
- **Store to inspiration boards** OR **property photos**
- **Track photo metadata** and analysis results
- **Maintain photo history** across sessions

### 2. Memory Systems (3 Types)
| Memory Type | Table | Purpose |
|------------|-------|---------|
| Session Memory | `unified_conversation_messages` | Chat history within session |
| Context Memory | `unified_conversation_memory` | Workflow states, image context |
| Cross-Session | Multiple tables | Past boards, properties, conversations |

### 3. Database Interactions (11 Tables)
```
Core Tables:
- properties              # User properties
- property_photos        # Property photo storage
- property_rooms         # Room definitions  
- inspiration_boards     # Design inspiration boards
- inspiration_images     # Board images

Memory Tables:
- unified_conversation_messages  # Chat history
- unified_conversation_memory    # Persistent memory

Bid Card Tables:
- potential_bid_cards    # Draft bid cards
- bid_cards             # Final bid cards
- inspiration_conversations  # Board conversations
- trade_projects        # Trade-specific projects
```

### 4. API Endpoints (9 Total)
```
POST   /api/iris/unified-chat                           # Main conversation
GET    /api/iris/context/{user_id}                     # Get user context
POST   /api/iris/suggest-tool/{tool_name}              # Tool suggestions
GET    /api/iris/potential-bid-cards/{user_id}         # Get draft cards
POST   /api/iris/potential-bid-cards                   # Create draft card
PUT    /api/iris/potential-bid-cards/{card_id}         # Update draft card
POST   /api/iris/potential-bid-cards/bundle            # Bundle cards
POST   /api/iris/potential-bid-cards/convert-to-bid-cards  # Convert to final
GET    /api/iris/potential-bid-cards/{card_id}/conversations  # Get chats
```

### 5. External Integrations
- **Anthropic Claude API** - AI responses (claude-3-5-sonnet-20241022)
- **IrisContextAdapter** - Privacy-filtered context retrieval
- **IRISActionSystem** - Bid card modifications
- **JAA Agent** - Bid card updates via action intents

### 6. Supported Workflows
1. **Image Storage**: Analyze → Detect Room → Store → Remember
2. **Design Consultation**: Build Context → Suggest → Guide
3. **Bid Card Creation**: Extract Info → Create Draft → Track
4. **Trade Grouping**: Analyze Trades → Group → Recommend

## 🏗️ New Architecture Design

### Directory Structure
```
iris/
├── __init__.py
├── IRIS_REBUILD_PLAN.md        # This document
├── models/
│   ├── __init__.py
│   ├── requests.py              # API request models (50 lines)
│   ├── responses.py             # API response models (30 lines)
│   └── database.py              # Database models (40 lines)
├── services/
│   ├── __init__.py
│   ├── photo_manager.py         # Photo upload/storage (150 lines)
│   ├── memory_manager.py        # All memory systems (120 lines)
│   ├── context_builder.py       # Context aggregation (100 lines)
│   └── room_detector.py         # Room detection logic (80 lines)
├── workflows/
│   ├── __init__.py
│   ├── image_workflow.py        # Image processing flow (100 lines)
│   └── consultation_workflow.py # Design consultation (80 lines)
├── api/
│   ├── __init__.py
│   └── routes.py                # All API endpoints (100 lines)
├── agent.py                     # Main orchestrator (100 lines)
└── config.py                    # Configuration (20 lines)

Total: ~1,000 lines (vs current 2,290 lines)
```

## 📝 Implementation Steps

### Phase 1: Setup Structure ✅
```bash
# Create clean directory structure
mkdir models services workflows api
touch models/__init__.py services/__init__.py workflows/__init__.py api/__init__.py
```

### Phase 2: Extract Models
Create Pydantic models for type safety and validation.

### Phase 3: Extract Services
Move core functionality into focused service classes:
- PhotoManager: Handle all photo operations
- MemoryManager: Handle all memory persistence
- ContextBuilder: Aggregate user context
- RoomDetector: Improve room detection with confidence

### Phase 4: Create Workflows
Implement clean workflow classes:
- ImageWorkflow: Handle photo upload flow
- ConsultationWorkflow: Handle design consultation

### Phase 5: API Routes
Clean FastAPI routes that delegate to agent.

### Phase 6: Main Agent
Thin orchestrator that coordinates services and workflows.

## 🔧 Key Improvements

### Current vs New Approach

| Feature | Current (Broken) | New (Fixed) |
|---------|-----------------|-------------|
| Room Detection | Keywords only, defaults to backyard | Confidence scoring, asks user when unsure |
| Image Analysis | Fake, just text parsing | Real OpenAI Vision API |
| Code Structure | 2,290 lines in one file | ~1,000 lines across 12 files |
| Memory | Mixed throughout code | Centralized MemoryManager |
| Error Handling | Scattered try/catch | Centralized error handling |
| Testing | Impossible to test | Each service testable |

## 📊 Migration Strategy

### Keep Working
1. Don't delete old agent.py yet
2. Build new structure alongside
3. Test each component individually
4. Run both in parallel initially
5. Switch over when verified

### Data Preservation
- ✅ All database operations preserved
- ✅ All memory systems maintained
- ✅ All API endpoints kept
- ✅ All integrations preserved

### Testing Checklist
- [ ] Photo upload works
- [ ] Room detection works
- [ ] Memory persistence works
- [ ] Context retrieval works
- [ ] API endpoints respond
- [ ] Inspiration boards work
- [ ] Property photos work
- [ ] Bid card creation works

## 🚀 Benefits of Rebuild

### Developer Experience
- **Maintainable**: Each file has single responsibility
- **Testable**: Services can be unit tested
- **Debuggable**: Clear flow through system
- **Extensible**: Easy to add new features

### User Experience
- **Faster**: Optimized code paths
- **Reliable**: Better error handling
- **Smarter**: Real image analysis
- **Interactive**: Asks for clarification

### Business Value
- **Reduced Bugs**: Clean architecture = fewer bugs
- **Faster Development**: Easy to add features
- **Lower Costs**: Less time debugging
- **Better UX**: Users get what they expect

## 📅 Timeline

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Create structure | 10 min | ✅ Starting |
| 2 | Extract models | 30 min | ⏳ Next |
| 3 | Extract services | 2 hours | 📅 Planned |
| 4 | Create workflows | 1 hour | 📅 Planned |
| 5 | API routes | 30 min | 📅 Planned |
| 6 | Testing | 1 hour | 📅 Planned |
| 7 | Migration | 1 hour | 📅 Planned |

**Total Estimated Time**: 6 hours

## 🎯 Success Criteria

### Must Have
- ✅ All 9 API endpoints working
- ✅ All 11 database tables accessible
- ✅ All 3 memory systems functional
- ✅ Photo upload with room detection
- ✅ Inspiration board storage
- ✅ Property photo storage

### Should Have
- 🔧 Confidence-based room detection
- 🔧 User confirmation dialogs
- 🔧 Real image analysis with OpenAI
- 🔧 Better error messages

### Nice to Have
- 💡 Auto-create rooms if missing
- 💡 Style detection from images
- 💡 Budget estimation
- 💡 Design recommendations

## 🔨 Let's Begin Implementation!

Starting with Phase 1: Create the clean structure...
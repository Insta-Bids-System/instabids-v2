# IRIS Property Agent - Testing Checklist
**Date**: January 13, 2025  
**Purpose**: Comprehensive validation of iris_property agent functionality  
**Agent Focus**: Property maintenance issues and bid card integration

## 🎯 TESTING OVERVIEW

### Test Scope
- ✅ Basic agent functionality
- ✅ Property conversation handling
- ✅ Memory persistence
- 🚧 Photo upload and analysis
- 🚧 Bid card integration
- 🚧 End-to-end workflows

### Test Environment Requirements
```bash
# Required environment variables
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Test server
cd ai-agents && python main.py  # Port 8008
```

---

## 📋 PHASE 1: BASIC FUNCTIONALITY TESTS

### ✅ 1.1 Agent Import & Instantiation
**Status**: PASSING
```bash
# Test command
python -c "from agents.iris_property.agent import IRISAgent; print('iris_property working')"
```
**Expected**: No errors, prints "iris_property working"
**Result**: ✅ PASS

### ✅ 1.2 API Endpoint Health Check
**Status**: PASSING
```bash
# Test command
curl -X GET http://localhost:8008/api/iris/health
```
**Expected**: 200 response with agent status
**Result**: ✅ PASS

### ✅ 1.3 Basic Conversation Handler
**Status**: PASSING
```bash
# Test command
curl -X POST http://localhost:8008/api/iris/unified-chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"My roof is leaking","session_id":"test123"}'
```
**Expected**: Property-focused response about roof issues
**Result**: ✅ PASS

---

## 📋 PHASE 2: PROPERTY ISSUE DETECTION TESTS

### ✅ 2.1 Room Detection from Text
**Test Keywords**: kitchen, bathroom, bedroom, living room, garage, basement, attic
```python
test_messages = [
    "My kitchen sink is leaking",
    "Bathroom tile is cracked", 
    "Bedroom ceiling has water stains",
    "Living room carpet needs replacing",
    "Garage door won't open",
    "Basement is flooding",
    "Attic insulation is old"
]
```
**Expected**: Each message returns detected room type
**Status**: ✅ PASSING (keyword-based detection working)

### ✅ 2.2 Property Issue Keywords
**Test Issues**: leak, crack, broken, damaged, stain, mold, electrical, plumbing
```python
test_issues = [
    "Water leak in ceiling",
    "Foundation crack in basement",
    "Broken window in bedroom", 
    "Water damage in kitchen",
    "Mold stains on bathroom walls",
    "Electrical outlet not working",
    "Plumbing backup in laundry room"
]
```
**Expected**: Each message identifies issue type and suggests contractors
**Status**: ✅ PASSING (basic keyword detection)

### 🚧 2.3 Issue Severity Assessment
**Test Cases**:
- Emergency: "Basement flooding right now"
- Urgent: "No hot water for 2 days"
- Standard: "Kitchen faucet drips occasionally"
- Planning: "Want to remodel bathroom next year"

**Expected**: Appropriate urgency levels assigned
**Status**: 🚧 NEEDS IMPLEMENTATION (currently returns generic responses)

---

## 📋 PHASE 3: MEMORY SYSTEM TESTS

### ✅ 3.1 Conversation Persistence
**Test Steps**:
1. Start conversation with session_id="memory_test_1"
2. Mention "kitchen renovation" 
3. End conversation
4. Start new conversation with same session_id
5. Mention "the project we discussed"

**Expected**: Agent remembers kitchen renovation context
**Status**: ✅ PASSING (unified memory system working)

### ✅ 3.2 Cross-Session Property Context
**Test Steps**:
1. Session 1: "My roof needs repair" 
2. Session 2: "About that roof issue..."
3. Verify agent recalls previous roof discussion

**Expected**: Context maintained across sessions
**Status**: ✅ PASSING

### 🚧 3.3 Property Project Tracking
**Test Steps**:
1. Discuss kitchen renovation (Project A)
2. Discuss roof repair (Project B) 
3. Reference both projects in single conversation
4. Verify agent keeps projects separate

**Expected**: Multi-project tracking with separation
**Status**: 🚧 NEEDS TESTING (basic memory works, multi-project unclear)

---

## 📋 PHASE 4: PHOTO UPLOAD TESTS (CRITICAL - NOT WORKING)

### ❌ 4.1 Photo Upload API
**Test Command**:
```bash
curl -X POST http://localhost:8008/api/iris/upload-photo \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_kitchen.jpg" \
  -F "user_id=test_user" \
  -F "room_type=kitchen"
```
**Expected**: Photo uploaded and stored with analysis
**Status**: ❌ BROKEN - Database schema incomplete

**Critical Issue**: `property_photos` table missing `user_id` column
```sql
-- Required fix:
ALTER TABLE property_photos ADD COLUMN user_id UUID REFERENCES auth.users(id);
```

### ❌ 4.2 Vision AI Analysis
**Test Case**: Upload photo of cracked bathroom tile
**Expected**: 
- Room detection: bathroom
- Issue identification: tile damage
- Contractor recommendation: tile installer, general contractor
- Urgency assessment: standard maintenance

**Status**: ❌ NOT IMPLEMENTED - Vision AI integration missing

### ❌ 4.3 Photo Storage & Retrieval
**Test Steps**:
1. Upload property photo
2. Retrieve uploaded photos for user
3. Verify file path and analysis results stored

**Expected**: Complete photo management workflow
**Status**: ❌ BROKEN - Database schema issues

---

## 📋 PHASE 5: BID CARD INTEGRATION TESTS (NOT IMPLEMENTED)

### ❌ 5.1 Potential Bid Card Creation
**Test Scenario**: "My kitchen faucet is leaking and the cabinet underneath is water damaged"
**Expected**:
1. Detect multiple issues (plumbing + water damage)
2. Suggest creating potential bid card
3. Call CIA agent to create bid card
4. Return potential bid card ID

**Status**: ❌ NOT IMPLEMENTED - No CIA integration

### ❌ 5.2 Issue Bundling
**Test Cases**:
- Related issues: "Kitchen sink leak + cabinet damage" → Single bid card
- Unrelated issues: "Roof repair + garage door" → Separate bid cards

**Expected**: Intelligent issue grouping for bid cards
**Status**: ❌ NOT IMPLEMENTED

### ❌ 5.3 Contractor Type Recommendations
**Test Matrix**:
```
Plumbing leak → plumber, water damage restoration
Electrical issue → electrician
Roof damage → roofer, general contractor
Foundation crack → structural engineer, foundation specialist
HVAC problem → HVAC technician
```
**Expected**: Accurate contractor type matching
**Status**: ❌ NOT IMPLEMENTED

---

## 📋 PHASE 6: API INTEGRATION TESTS

### ✅ 6.1 Context Retrieval API
```bash
curl -X GET http://localhost:8008/api/iris/context/test_user
```
**Expected**: Property project context for user
**Status**: ✅ PASSING

### ✅ 6.2 Tool Suggestions API
```bash
curl -X POST http://localhost:8008/api/iris/suggest-tool/photo_upload \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","context":"kitchen renovation"}'
```
**Expected**: Relevant tool suggestions for property consultation
**Status**: ✅ PASSING

### 🚧 6.3 Potential Bid Card Endpoints
```bash
# Get user's potential bid cards
curl -X GET http://localhost:8008/api/iris/potential-bid-cards/test_user

# Create new potential bid card
curl -X POST http://localhost:8008/api/iris/potential-bid-cards \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","property_issues":["plumbing_leak"]}'
```
**Expected**: Bid card management functionality
**Status**: 🚧 ENDPOINTS EXIST - Need implementation behind them

---

## 📋 PHASE 7: END-TO-END WORKFLOW TESTS (CRITICAL)

### ❌ 7.1 Complete Property Consultation Workflow
**Test Scenario**: Homeowner with kitchen water damage
```
1. User: "Water is coming through my kitchen ceiling"
2. Expected: Room detection (kitchen), issue identification (water damage)
3. User uploads ceiling photo
4. Expected: Vision analysis confirms water damage, suggests urgent timeline
5. Agent suggests creating bid card for plumber + water damage restoration
6. Expected: Potential bid card created, ready for CIA processing
7. Agent provides contractor preparation advice
8. Expected: Timeline, budget expectations, project scope guidance
```
**Status**: ❌ INCOMPLETE - Steps 3-6 not implemented

### ❌ 7.2 Multi-Issue Property Assessment
**Test Scenario**: Property with multiple maintenance needs
```
1. User: "Need help prioritizing home repairs"
2. Agent: "Tell me about the issues you're seeing"
3. User describes: roof leak, broken HVAC, old electrical panel
4. Expected: Issue prioritization by urgency and safety
5. Expected: Separate bid cards for unrelated issues
6. Expected: Budget planning and timeline recommendations
```
**Status**: ❌ NOT IMPLEMENTED - No prioritization logic

### ❌ 7.3 Return Visitor Experience
**Test Scenario**: User returning after previous property consultation
```
1. Previous session: Discussed bathroom renovation
2. New session: "I'm ready to move forward with that bathroom project"
3. Expected: Agent recalls bathroom renovation context
4. Expected: Offers to create bid card based on previous discussion
5. Expected: Seamless transition from consultation to bid card creation
```
**Status**: 🚧 PARTIAL - Memory works, bid card integration missing

---

## 🚨 CRITICAL FAILING TESTS

### Database Schema Issues
1. **`property_photos` missing `user_id` column** - Breaks photo upload
2. **No vision analysis results storage** - Photo analysis not persisted
3. **Memory serialization issues** - Complex objects not JSON serializable

### Missing Core Features
1. **Vision AI integration** - Cannot analyze property photos
2. **CIA agent integration** - Cannot create bid cards from property issues
3. **Contractor matching logic** - No specific contractor recommendations
4. **Issue prioritization** - No urgency or safety assessment

### Integration Gaps
1. **Photo upload → Analysis workflow** - Broken chain
2. **Property issues → Bid card creation** - Missing connection
3. **Contractor recommendations → CDA integration** - No handoff

---

## ✅ TESTING COMMANDS REFERENCE

### Basic Functionality Tests
```bash
# Agent import test
python -c "from agents.iris_property.agent import IRISAgent; print('Working')"

# Health check
curl -X GET http://localhost:8008/api/iris/health

# Basic conversation
curl -X POST http://localhost:8008/api/iris/unified-chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"Kitchen sink leaking","session_id":"test123"}'

# Context retrieval
curl -X GET http://localhost:8008/api/iris/context/test_user

# Tool suggestions
curl -X POST http://localhost:8008/api/iris/suggest-tool/photo_analysis \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","context":"bathroom renovation"}'
```

### Advanced Tests (After Implementation)
```bash
# Photo upload (after database fix)
curl -X POST http://localhost:8008/api/iris/upload-photo \
  -F "file=@test_property.jpg" \
  -F "user_id=test" \
  -F "room_type=kitchen"

# Bid card creation (after CIA integration)  
curl -X POST http://localhost:8008/api/iris/create-bid-card \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","issues":["plumbing_leak","water_damage"]}'

# Contractor recommendations (after implementation)
curl -X POST http://localhost:8008/api/iris/recommend-contractors \
  -H "Content-Type: application/json" \
  -d '{"issue_types":["plumbing","water_damage"],"urgency":"high"}'
```

---

## 🎯 SUCCESS CRITERIA

### Minimal Viable Product (60% Complete)
- ✅ Property conversation handling
- ✅ Room detection from text
- ✅ Memory persistence
- ❌ Photo upload and basic storage
- ❌ Simple bid card suggestions

### Production Ready (100% Complete)
- ✅ All MVP features
- ❌ Vision AI property photo analysis
- ❌ CIA agent bid card integration
- ❌ Contractor type recommendations
- ❌ Multi-issue prioritization
- ❌ Complete end-to-end workflows

---

## 📊 CURRENT TEST RESULTS SUMMARY

| Test Category | Passing | Failing | Not Implemented | Completion |
|---------------|---------|---------|-----------------|-------------|
| Basic Functionality | 3/3 | 0/3 | 0/3 | 100% |
| Property Detection | 2/3 | 0/3 | 1/3 | 67% |  
| Memory System | 2/3 | 0/3 | 1/3 | 67% |
| Photo Upload | 0/3 | 3/3 | 0/3 | 0% |
| Bid Card Integration | 0/3 | 0/3 | 3/3 | 0% |
| API Integration | 2/3 | 0/3 | 1/3 | 67% |
| End-to-End Workflows | 0/3 | 0/3 | 3/3 | 0% |

**Overall Agent Completion: ~60%**
- **Working Systems**: 40% 
- **Critical Missing**: 40%

---

*This checklist provides the complete validation framework for iris_property agent. Use this to systematically test and verify each component before claiming production readiness.*
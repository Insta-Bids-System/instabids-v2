# IRIS Property Agent - Comprehensive Fix Plan
**Date**: January 13, 2025  
**Status**: IMPLEMENTATION REQUIRED  
**Purpose**: Complete technical roadmap to get iris_property agent fully functioning

## 🎯 CURRENT STATUS: ~60% Complete

### ✅ Working Systems
- Basic property conversation handling via `unified_conversations` table
- Room detection from text keywords (kitchen, bathroom, etc.)
- Memory persistence across sessions via unified memory system
- API endpoint framework (`/api/iris/unified-chat`)
- Property-focused response generation
- Clean separation from iris_inspiration agent

### ❌ Critical Missing Components
- **Vision AI Integration**: Cannot analyze property photos for issues
- **Database Schema Issues**: Missing columns preventing photo storage
- **Bid Card Creation**: No integration with CIA/JAA agents
- **Property Issue Detection**: Limited to keyword-based detection only
- **Contractor Matching**: No recommendation logic implemented

---

## 🔧 PHASE 1: DATABASE SCHEMA FIXES (Priority: CRITICAL)

### Issue 1: `property_photos` Table Missing `user_id` Column
```sql
-- Current schema is incomplete
property_photos:
  - id (primary key)
  - filename
  - file_path
  - room_type
  - analysis_results
  - created_at
  
-- Missing: user_id (CRITICAL for multi-user system)
```

**Fix Required**:
```sql
ALTER TABLE property_photos ADD COLUMN user_id UUID REFERENCES auth.users(id);
CREATE INDEX idx_property_photos_user_id ON property_photos(user_id);
```

**Files to Update**:
- `models/database.py` - Update PropertyPhoto model
- `services/photo_manager.py` - Add user_id to all queries

### Issue 2: Memory Serialization Problems
**Problem**: `RoomDetectionResult` objects cannot be serialized to JSON for memory storage

**Current Error Pattern**:
```python
# This fails in memory_manager.py
memory_value = json.dumps(room_result)  # TypeError: Object not serializable
```

**Fix Required**:
```python
# In models/responses.py
class RoomDetectionResult(BaseModel):
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoomDetectionResult':
        """Create from dictionary after JSON deserialization"""
        return cls(**data)
```

---

## 🔧 PHASE 2: VISION AI INTEGRATION (Priority: HIGH)

### Issue 3: No Property Photo Analysis
**Current State**: Photos uploaded but not analyzed for property issues

**Implementation Required**:

#### 2.1 Vision AI Service Creation
```python
# Create: services/vision_analyzer.py
class PropertyVisionAnalyzer:
    """Analyze property photos for maintenance issues"""
    
    async def analyze_property_photo(self, image_path: str) -> PropertyAnalysisResult:
        """
        Use Claude Vision to:
        1. Identify room type
        2. Detect visible issues (cracks, stains, damage)
        3. Assess urgency level
        4. Recommend contractor types needed
        """
        pass
```

#### 2.2 Property Issue Detection Model
```python
# Add to models/responses.py
class PropertyIssueDetection(BaseModel):
    issue_type: str          # "plumbing", "electrical", "structural"
    severity: str           # "low", "medium", "high", "urgent"
    description: str        # "Water stain on ceiling suggests roof leak"
    contractor_types: List[str]  # ["roofer", "waterproofing specialist"]
    estimated_urgency: int  # 1-10 scale
    room_context: str       # "bathroom", "kitchen", etc.
```

#### 2.3 Integration Points
- **File**: `workflows/image_workflow.py` - Add vision analysis call
- **File**: `services/photo_manager.py` - Store analysis results
- **File**: `agent.py` - Include analysis in responses

---

## 🔧 PHASE 3: BID CARD INTEGRATION (Priority: HIGH)

### Issue 4: No CIA/JAA Agent Integration
**Current State**: Property issues identified but no bid card creation

**Implementation Required**:

#### 3.1 Potential Bid Card Creation Service
```python
# Create: services/bid_card_creator.py
class PropertyBidCardCreator:
    """Create potential bid cards from property issues"""
    
    async def create_potential_bid_card(
        self, 
        user_id: str,
        property_issues: List[PropertyIssueDetection],
        conversation_context: Dict[str, Any]
    ) -> str:
        """
        1. Bundle related property issues
        2. Call CIA agent for potential bid card creation
        3. Return potential bid card ID
        """
        pass
```

#### 3.2 API Integration Endpoints
```python
# Add to api/routes.py
@router.post("/create-bid-card-from-issues")
async def create_bid_card_from_property_issues(
    user_id: str,
    issue_ids: List[str],
    project_description: str
):
    """Convert property issues into potential bid card"""
    pass
```

#### 3.3 Workflow Integration
- **File**: `workflows/consultation_workflow.py` - Add bid card creation step
- **File**: `agent.py` - Suggest bid card creation to users

---

## 🔧 PHASE 4: CONTRACTOR MATCHING LOGIC (Priority: MEDIUM)

### Issue 5: No Contractor Recommendation System
**Current State**: Issues detected but no contractor guidance

**Implementation Required**:

#### 4.1 Contractor Matching Service
```python
# Create: services/contractor_matcher.py
class PropertyContractorMatcher:
    """Match property issues to contractor types"""
    
    ISSUE_TO_CONTRACTOR_MAP = {
        "plumbing_leak": ["plumber", "water damage restoration"],
        "electrical_issue": ["electrician"],
        "roof_damage": ["roofer", "general contractor"],
        "foundation_crack": ["structural engineer", "foundation repair"]
    }
    
    def get_contractor_recommendations(
        self, 
        issues: List[PropertyIssueDetection]
    ) -> List[ContractorRecommendation]:
        pass
```

#### 4.2 Integration with CDA Agent
```python
# In services/contractor_matcher.py
async def prepare_cda_project_brief(
    self, 
    property_issues: List[PropertyIssueDetection]
) -> Dict[str, Any]:
    """Format project data for CDA agent contractor discovery"""
    pass
```

---

## 🔧 PHASE 5: TESTING & VALIDATION (Priority: MEDIUM)

### Issue 6: Insufficient Test Coverage
**Current State**: Only basic import/instantiation testing

**Testing Implementation Required**:

#### 5.1 Property Photo Upload Test
```python
# Create: tests/test_property_photo_workflow.py
async def test_property_photo_analysis_workflow():
    """
    1. Upload property photo
    2. Verify room detection
    3. Verify issue detection  
    4. Verify analysis storage
    5. Verify bid card creation suggestion
    """
    pass
```

#### 5.2 End-to-End Workflow Test
```python
# Create: tests/test_property_consultation_e2e.py
async def test_complete_property_consultation():
    """
    Test: Photo upload → Analysis → Issue detection → 
          Bid card creation → Contractor recommendations
    """
    pass
```

#### 5.3 Integration Tests
- Test CIA agent integration for bid card creation
- Test memory persistence across property consultations
- Test multi-issue bundling into single bid cards

---

## 📊 IMPLEMENTATION PRIORITY MATRIX

| Issue | Priority | Effort | Impact | Dependencies |
|-------|----------|---------|---------|--------------|
| Database schema fixes | CRITICAL | Low | High | None |
| Memory serialization | CRITICAL | Low | High | None |
| Vision AI integration | HIGH | High | High | Database fixes |
| Bid card creation | HIGH | Medium | High | Vision AI, CIA agent |
| Contractor matching | MEDIUM | Medium | Medium | Issue detection |
| Complete testing | MEDIUM | High | Medium | All above |

---

## 🎯 PHASE-BY-PHASE COMPLETION PLAN

### **Phase 1: Foundation (Est. 1 day)**
1. Fix `property_photos` table schema
2. Fix memory serialization issues
3. Verify basic database operations

**Verification**: Property photos can be stored and retrieved with user association

### **Phase 2: Vision Analysis (Est. 2-3 days)**
1. Implement `PropertyVisionAnalyzer` service
2. Create property issue detection models
3. Integrate with image upload workflow
4. Test with real property photos

**Verification**: Upload property photo → Get detailed issue analysis

### **Phase 3: Bid Card Integration (Est. 2-3 days)**
1. Create `PropertyBidCardCreator` service
2. Implement CIA agent integration calls
3. Add bid card creation API endpoints
4. Test issue → bid card workflow

**Verification**: Property issues → Potential bid card created in CIA system

### **Phase 4: Contractor Matching (Est. 1-2 days)**
1. Implement contractor recommendation logic
2. Create CDA agent integration
3. Add contractor suggestion endpoints
4. Test recommendation accuracy

**Verification**: Property issues → Specific contractor type recommendations

### **Phase 5: Testing & Polish (Est. 2-3 days)**
1. Create comprehensive test suite
2. Test all integration points
3. Performance testing
4. Error handling validation

**Verification**: All features work end-to-end with real data

---

## 🚀 SUCCESS METRICS

### Technical Metrics
- [ ] Property photos stored with proper user association
- [ ] Vision AI returns detailed property issue analysis
- [ ] Potential bid cards created from property consultations
- [ ] Contractor recommendations generated for all issue types
- [ ] Memory persistence works across sessions
- [ ] API response times under 10 seconds

### User Experience Metrics
- [ ] User uploads property photo → Gets actionable maintenance advice
- [ ] Property consultation → Generates potential bid card automatically
- [ ] Issue severity properly communicated to users
- [ ] Contractor recommendations are specific and helpful

### Integration Metrics
- [ ] CIA agent successfully receives property-based bid card requests
- [ ] JAA agent can process property-focused bid cards
- [ ] CDA agent receives properly formatted project briefs
- [ ] Memory system maintains context across agent interactions

---

## 📋 CURRENT BLOCKERS TO RESOLVE

1. **Database Access**: Need Supabase credentials to modify schema
2. **API Keys**: Need Anthropic API key for Claude Vision integration
3. **Agent Dependencies**: Need CIA/JAA agent endpoints for integration testing
4. **Test Data**: Need sample property photos for vision AI testing

---

## 🎉 FINAL DELIVERABLE

**A fully functional iris_property agent that:**
- Analyzes property photos for maintenance issues
- Creates potential bid cards from property problems
- Recommends specific contractor types
- Maintains conversation context across sessions
- Integrates seamlessly with CIA/JAA/CDA agents
- Provides clear, actionable property maintenance guidance

**Estimated Total Implementation Time**: 8-12 days
**Estimated Completion**: End of January 2025

---

*This fix plan addresses the user's requirement to "map out all the things it's going to take to get this iris property agent completely and totally functioning and proven."*
# IRIS Image Memory System Fix Plan
**Date**: August 27, 2025  
**Status**: 🔧 IMPLEMENTATION REQUIRED

## Executive Summary

The IRIS image memory system has three critical issues preventing image storage and recall:
1. **Database RLS (Row-Level Security) policies blocking inserts**
2. **Missing schema columns in inspiration_images table**  
3. **JSON serialization errors for complex objects**

While core conversation memory is 100% functional, these issues prevent IRIS from storing and recalling uploaded images.

## Current State Analysis

### What's Working ✅
- Image upload and processing logic
- Image analysis with GPT-4 Vision
- Room detection and style extraction
- Base64 encoding and data transfer

### What's Broken ❌
- Database storage completely blocked
- Memory persistence fails
- Image recall returns empty results
- Cross-session image memory non-functional

## Root Cause Analysis

### Issue 1: RLS Policy Violation
```
Error: new row violates row-level security policy for table "inspiration_boards"
Code: 42501
```
**Cause**: The inspiration_boards table has restrictive RLS policies that prevent the backend service from inserting rows.
**Impact**: Cannot create new inspiration boards for users.

### Issue 2: Missing Database Column
```
Error: Could not find the 'analysis_results' column of 'inspiration_images' in the schema cache
Code: PGRST204
```
**Cause**: The schema expects an 'analysis_results' column that doesn't exist in the table.
**Impact**: Cannot store image analysis data.

### Issue 3: JSON Serialization Error
```
Error: Object of type RoomDetectionResult is not JSON serializable
```
**Cause**: Custom Python objects (RoomDetectionResult) cannot be directly serialized to JSON.
**Impact**: Memory storage fails, breaking conversation continuity for image uploads.

## Detailed Fix Plan

### Phase 1: Database Schema Fixes (Priority: CRITICAL)

#### 1.1 Check Current Schema
```sql
-- Inspect inspiration_boards table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'inspiration_boards';

-- Inspect inspiration_images table structure  
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'inspiration_images';

-- Check RLS policies
SELECT * FROM pg_policies 
WHERE tablename IN ('inspiration_boards', 'inspiration_images');
```

#### 1.2 Fix inspiration_images Schema
```sql
-- Add missing analysis_results column
ALTER TABLE inspiration_images 
ADD COLUMN IF NOT EXISTS analysis_results JSONB;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_inspiration_images_analysis 
ON inspiration_images USING gin(analysis_results);
```

#### 1.3 Fix RLS Policies
```sql
-- Option A: Temporarily disable RLS for debugging
ALTER TABLE inspiration_boards DISABLE ROW LEVEL SECURITY;
ALTER TABLE inspiration_images DISABLE ROW LEVEL SECURITY;

-- Option B: Create proper service role policy
CREATE POLICY "service_role_all" ON inspiration_boards
FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all" ON inspiration_images  
FOR ALL USING (true) WITH CHECK (true);

-- Option C: User-specific policy with tenant_id
CREATE POLICY "users_manage_own_boards" ON inspiration_boards
FOR ALL USING (user_id::text = current_setting('request.jwt.claims')::json->>'sub')
WITH CHECK (user_id::text = current_setting('request.jwt.claims')::json->>'sub');
```

### Phase 2: Code Fixes (Priority: HIGH)

#### 2.1 Fix JSON Serialization
**File**: `agents/iris/services/image_analyzer.py`

```python
# Current problematic code
class RoomDetectionResult(BaseModel):
    room_type: str
    confidence: float
    style_elements: List[str]
    
# Add JSON serialization method
class RoomDetectionResult(BaseModel):
    room_type: str
    confidence: float
    style_elements: List[str]
    
    def to_dict(self):
        """Convert to JSON-serializable dictionary"""
        return {
            "room_type": self.room_type,
            "confidence": self.confidence,
            "style_elements": self.style_elements
        }
```

#### 2.2 Update Memory Storage Logic
**File**: `agents/iris/workflows/consultation_workflow.py`

```python
# Fix in save_image_memory method
def save_image_memory(self, analysis_results):
    # Convert complex objects to dictionaries
    if hasattr(analysis_results, 'to_dict'):
        analysis_results = analysis_results.to_dict()
    elif isinstance(analysis_results, BaseModel):
        analysis_results = analysis_results.dict()
    
    # Now safe to serialize
    memory_value = {
        "analysis_results": analysis_results,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Save to memory
    self.memory_manager.save_context_memory(
        conversation_id=self.conversation_id,
        memory_type=MemoryType.IMAGE_ANALYSIS,
        memory_key=f"image_{self.session_id}",
        memory_value=memory_value
    )
```

### Phase 3: Alternative Storage Strategy (Priority: MEDIUM)

If database fixes are blocked, implement fallback storage:

#### 3.1 Use unified_conversation_memory Table
```python
# Store images in the working unified_conversation_memory table
def save_image_to_unified_memory(self, image_data, analysis):
    """Bypass broken inspiration tables, use unified memory"""
    memory_value = {
        "type": "image_upload",
        "image_data": image_data[:1000],  # Store preview only
        "image_url": self.upload_to_storage(image_data),  # Store in Supabase storage
        "analysis": analysis if isinstance(analysis, dict) else analysis.dict(),
        "room_type": analysis.get("room_type"),
        "style_elements": analysis.get("style_elements", [])
    }
    
    return self.memory_manager.save_context_memory(
        conversation_id=self.conversation_id,
        memory_type=MemoryType.PHOTO_REFERENCE,
        memory_key=f"photo_{uuid.uuid4()}",
        memory_value=memory_value
    )
```

#### 3.2 Create Migration Script
```python
# Migrate from broken tables to unified memory
def migrate_inspiration_boards():
    """One-time migration to unified memory system"""
    # Get all boards that can be read
    boards = db.client.table("inspiration_boards").select("*").execute()
    
    for board in boards.data:
        # Save to unified memory
        memory_manager.save_context_memory(
            conversation_id=board["conversation_id"],
            memory_type=MemoryType.INSPIRATION_BOARD,
            memory_key=f"board_{board['id']}",
            memory_value=board
        )
```

### Phase 4: Testing Strategy (Priority: HIGH)

#### 4.1 Unit Tests
```python
# Test JSON serialization
def test_room_detection_serialization():
    result = RoomDetectionResult(
        room_type="living_room",
        confidence=0.95,
        style_elements=["modern", "minimalist"]
    )
    json_data = json.dumps(result.to_dict())
    assert json_data is not None

# Test memory storage
def test_image_memory_storage():
    # Mock image upload
    # Verify storage
    # Check retrieval
```

#### 4.2 Integration Tests
```python
# Full flow test
def test_complete_image_flow():
    # 1. Upload image
    # 2. Verify analysis
    # 3. Check memory storage
    # 4. Test recall in next message
    # 5. Verify cross-session access
```

## Implementation Order

### Day 1: Database Investigation & Quick Fixes
1. ✅ Check current database schema
2. ✅ Document exact table structures
3. ✅ Test RLS policy modifications
4. ✅ Add missing columns if possible

### Day 2: Code Fixes
1. ✅ Fix JSON serialization
2. ✅ Update memory storage logic
3. ✅ Test with mock data
4. ✅ Verify no regression in text memory

### Day 3: Alternative Strategy
1. ✅ Implement unified memory fallback
2. ✅ Test complete flow
3. ✅ Create migration utilities
4. ✅ Document new approach

### Day 4: Testing & Validation
1. ✅ Run comprehensive tests
2. ✅ Fix any issues found
3. ✅ Update documentation
4. ✅ Deploy fixes

## Risk Mitigation

### Risk 1: Cannot Modify Database
**Mitigation**: Use unified_conversation_memory table exclusively

### Risk 2: Storage Size Limits
**Mitigation**: Store images in Supabase Storage, only references in database

### Risk 3: Breaking Existing Functionality
**Mitigation**: Extensive testing, gradual rollout, feature flags

## Success Criteria

1. ✅ Image uploads complete without errors
2. ✅ Image analysis stored in database
3. ✅ Images recalled in subsequent messages
4. ✅ Cross-session image memory works
5. ✅ No regression in text memory
6. ✅ Performance acceptable (<3 second response)

## Rollback Plan

If fixes cause issues:
1. Revert code changes
2. Keep text memory working
3. Disable image features temporarily
4. Document known limitations

## Alternative Approaches

### Option A: Redesign Schema
Create new simplified tables without RLS:
- `iris_image_memory`
- `iris_image_analysis`

### Option B: File System Storage
Store images locally with database references:
- Faster access
- No database size issues
- Requires file management

### Option C: External Service
Use dedicated image service:
- S3 for storage
- DynamoDB for metadata
- Lambda for processing

## Monitoring & Alerts

Set up monitoring for:
- Database insert failures
- JSON serialization errors  
- Memory retrieval misses
- Response time degradation

## Documentation Updates

After fixes:
1. Update API documentation
2. Update database schema docs
3. Create troubleshooting guide
4. Update agent specifications

## Conclusion

The image memory system has three fixable issues. The recommended approach:
1. **Immediate**: Fix JSON serialization (1 hour)
2. **Short-term**: Use unified_conversation_memory as workaround (2 hours)
3. **Long-term**: Fix database schema and RLS policies (4 hours)

Total estimated fix time: **7 hours**
Risk level: **Medium** (core memory unaffected)
Priority: **High** (user-facing feature broken)
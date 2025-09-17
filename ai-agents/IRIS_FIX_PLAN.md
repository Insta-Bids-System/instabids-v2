# IRIS Agent Fix Plan - 4 Critical Issues

## Summary
After comprehensive testing and code research, here's the detailed plan to fix the 4 broken issues in IRIS.

## 🔧 Issue 1: Text-Only Repair Detection (PRIORITY: HIGH)

### **Root Cause**
- Consultation workflow detects repairs with GPT-4 tools but doesn't have proper repair response handling
- `repair_detected = True` but response generation still uses design consultation templates
- Missing repair-specific response generator in consultation workflow

### **Files to Fix**
- `agents/iris/workflows/consultation_workflow.py` (lines 180-250)

### **Required Changes**
1. **Add repair response generator method** (NEW METHOD)
   ```python
   def _generate_repair_response(self, request, repair_data, urgency):
       # Generate repair-specific response based on detected issues
       # Include urgency handling, contractor recommendations
   ```

2. **Fix response routing logic** (MODIFY EXISTING)
   ```python
   # Replace design consultation response when repair_detected = True
   if repair_detected:
       response_text = self._generate_repair_response(request, repair_data)
       suggestions = self._generate_repair_suggestions(urgency)
   ```

3. **Add repair item creation** (NEW FUNCTIONALITY)
   ```python
   # Create potential bid card with repair items when detected
   await self._create_repair_items_from_text(user_id, repair_data)
   ```

### **Estimated Effort**: 4-6 hours
- 2 hours: Create repair response generator
- 2 hours: Implement repair item creation
- 1-2 hours: Testing and integration

---

## 🧠 Issue 2: Conversation Memory Continuity (PRIORITY: MEDIUM)

### **Root Cause**
- GPT-4 prompt in consultation workflow has TODO comment: "Add session history from memory_manager"
- Conversation history retrieved but not passed to GPT-4 context
- Each message treated as isolated conversation

### **Files to Fix**
- `agents/iris/workflows/consultation_workflow.py` (line 200)

### **Required Changes**
1. **Add conversation history to GPT-4 prompt** (MODIFY EXISTING)
   ```python
   # Get conversation history
   history = self.memory_manager.get_conversation_history(conversation_id)
   
   # Build context with history
   messages = [
       {"role": "system", "content": system_prompt},
       # ADD: Previous conversation turns
       *[{"role": "user" if h['role'] == 'user' else "assistant", 
          "content": h['content']} for h in history[-5:]],  # Last 5 turns
       {"role": "user", "content": request.message}
   ]
   ```

2. **Update system prompt to use context** (MODIFY EXISTING)
   ```python
   system_prompt = f"""You are IRIS, remembering previous conversation.
   Previous context: {context_summary}
   User mentioned: {extracted_preferences_from_history}"""
   ```

### **Estimated Effort**: 2-3 hours
- 1 hour: Implement history retrieval and formatting
- 1 hour: Update system prompt with context
- 1 hour: Testing continuity across messages

---

## 💾 Issue 3: Repair Item Storage in ai_analysis Field (PRIORITY: MEDIUM)

### **Root Cause**
- Image workflow has repair item storage logic but consultation workflow doesn't
- `ai_analysis` field stays empty `{}` for text-only repair requests
- No bid card creation triggered by text-only repairs

### **Files to Fix**
- `agents/iris/workflows/consultation_workflow.py` (NEW METHOD)
- `agents/iris/services/repair_item_creator.py` (NEW FILE - optional)

### **Required Changes**
1. **Add repair item creation method** (NEW METHOD)
   ```python
   async def _create_repair_items_from_text(self, user_id, repair_data):
       # Similar to image_workflow._create_repair_items but for text
       # Create potential_bid_card with ai_analysis populated
       ai_analysis_data = {
           "detected_issues": [repair_data.get('repair_type', 'General repair')],
           "maintenance_potential": 0.8,  # High for explicit repair requests
           "urgency_level": repair_data.get('urgency', 'normal'),
           "repair_needed": True,
           "source": "text_analysis",
           "analyzed_at": datetime.now().isoformat()
       }
   ```

2. **Call repair creation when GPT-4 detects repair** (INTEGRATE EXISTING)
   ```python
   if repair_detected:
       await self._create_repair_items_from_text(request.user_id, repair_data)
   ```

### **Estimated Effort**: 3-4 hours
- 2 hours: Create repair item creation method
- 1 hour: Integrate with existing workflow
- 1 hour: Test bid card creation and ai_analysis population

---

## 🔌 Issue 4: Suggest-Tool Endpoint Validation Error (PRIORITY: LOW)

### **Root Cause**
- Test sends `{"context": {}}` but endpoint might expect additional fields
- ToolSuggestionRequest validation rejecting empty context
- Method exists in agent but endpoint validation failing

### **Files to Fix**
- `agents/iris/models/requests.py` (validation rules)
- `agents/iris/api/routes.py` (error handling)

### **Required Changes**
1. **Fix ToolSuggestionRequest validation** (MODIFY EXISTING)
   ```python
   class ToolSuggestionRequest(BaseModel):
       context: Optional[Dict[str, Any]] = Field(default=None)  # Allow None
       # OR make context non-required
   ```

2. **Add better error handling** (MODIFY EXISTING)
   ```python
   @router.post("/suggest-tool/{tool_name}")
   async def suggest_tool(tool_name: str, request: ToolSuggestionRequest):
       try:
           # Add validation logging
           logger.info(f"Received context: {request.context}")
           # Rest of method...
   ```

### **Estimated Effort**: 1-2 hours
- 30 min: Debug validation issue
- 30 min: Fix model validation
- 30 min: Add error logging
- 30 min: Test endpoint

---

## 📋 Implementation Priority & Timeline

### **Phase 1: Critical Repairs (1 day)**
1. Issue 1: Text-only repair detection (4-6 hours)
2. Issue 2: Memory continuity (2-3 hours)

### **Phase 2: Data & Polish (4 hours)**  
3. Issue 3: Repair item storage (3-4 hours)
4. Issue 4: Suggest-tool endpoint (1-2 hours)

### **Total Estimated Effort: 10-15 hours (1.5-2 days)**

## 🧪 Testing Strategy

### **After Each Fix**:
1. Run comprehensive test suite
2. Verify specific test passes
3. Check database for proper data storage

### **Success Criteria**:
- Text repair requests get proper repair responses ✅
- "Blue" preference remembered across messages ✅  
- ai_analysis field populated with repair data ✅
- All API endpoints return 200 status ✅

### **Target Success Rate**: 95%+ (22/23 tests passing)

## 🎯 Implementation Notes

### **Code Quality**:
- Follow existing patterns in image_workflow.py
- Use same database patterns as working code
- Maintain error handling and logging

### **Testing**:
- Each fix should be tested individually
- Full regression test after all fixes
- Verify database changes with Supabase queries

### **Risk Mitigation**:
- All changes are additions/modifications to existing working code
- No breaking changes to successful features
- Can implement fixes incrementally

## 📊 Expected Outcome

**Current State**: 82.6% success rate (19/23 passing)
**After Fixes**: 95%+ success rate (22/23 passing)

**Business Impact**:
- Repair requests properly handled ✅
- Conversation continuity working ✅  
- Complete bid card tracking ✅
- All core IRIS functionality operational ✅
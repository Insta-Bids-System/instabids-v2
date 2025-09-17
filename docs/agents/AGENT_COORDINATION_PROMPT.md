# 🚨 AGENT COORDINATION PROMPT - GIVE TO EVERY AGENT

## **BACKEND COORDINATION SYSTEM**

**The InstaBids system uses organized router architecture with error handling.**

---

## **THE SYSTEM STRUCTURE:**

### **Backend Architecture:**
```
main.py = Core FastAPI app (port 8008) with error handling
routers/ = Individual agent endpoints organized by function
```

**The system is designed to survive individual router failures.**

---

## **HOW TO ADD YOUR FEATURES:**

### **Option 1: Add to Existing Router (Recommended)**

**Step 1: Choose the right router file**
```
routers/admin_routes.py     = Admin features
routers/cia_routes.py       = Customer interface 
routers/contractor_routes.py = Contractor features
routers/homeowner_routes.py = Homeowner features
routers/monitoring_routes.py = System monitoring
```

**Step 2: Edit the router file**
```python
# Edit the appropriate router file
@router.post("/your-new-feature")
async def your_new_feature_endpoint(request: dict):
    # Your feature code here
    # Use MCP tools here
    # Access database here
    return {"success": True, "result": "your response"}
```

### **Option 2: Add Directly to main.py (Simple Features)**

**Step 1: Edit main.py**
```python
# Add endpoint directly to main.py for simple features
@app.post("/api/your-simple-feature")
async def your_simple_feature(request: dict):
    # Simple feature code here
    return {"success": True, "result": "your response"}
```

### **Step 3: Test Your Feature**
```python
# Test via API call (NOT separate script)
import requests
response = requests.post('http://localhost:8008/api/your-feature', json={
    "message": "test your functionality"
})
print(response.json())
```

---

## **WHAT YOU MUST NEVER DO (BREAKS THE SYSTEM):**

### **❌ NEVER CREATE THESE:**
- ❌ New Python files that run servers (`python your_agent.py`)
- ❌ Separate FastAPI applications
- ❌ Files with `asyncio.run()` 
- ❌ Files with `uvicorn.run()`
- ❌ Any competing process on any port

### **❌ NEVER RUN THESE COMMANDS:**
- ❌ `python [any_separate_script].py`
- ❌ Starting new servers
- ❌ Creating processes outside main.py

---

## **WHAT YOU MUST ALWAYS DO (KEEPS SYSTEM WORKING):**

### **✅ ALWAYS DO THIS:**
- ✅ Edit the existing main.py file
- ✅ Add your code TO the existing FastAPI app
- ✅ Test via API calls to localhost:8008
- ✅ Check that backend is still running after your changes

---

## **MANDATORY CHECKLIST - COMPLETE BEFORE ANY WORK:**

### **Before Making Changes:**
- [ ] I have read the current main.py file
- [ ] I understand what's already in the file  
- [ ] I know exactly where to add my agent code
- [ ] I will NOT create any separate Python files
- [ ] I will NOT run any separate scripts

### **After Making Changes:**
- [ ] Backend still responds: `curl http://localhost:8008`
- [ ] My endpoint works: `curl http://localhost:8008/api/my-endpoint`
- [ ] Other agents' endpoints still work
- [ ] No competing Python processes were created

---

## **COORDINATION EXAMPLES**

### **Example 1: Database Consultant Agent**
```python
# INSIDE main.py - add this to existing file
class DatabaseConsultant:
    def __init__(self):
        self.project_id = "xrhgrthdcaymxuqcgrmj"
    
    async def handle_consultation(self, question, agent_name):
        # Use MCP tools to scan database
        # Provide expert advice
        return {"advice": "database advice here"}

# INSIDE main.py - add this endpoint to existing app
@app.post("/api/database-consultant")
async def database_consultant_endpoint(request: dict):
    consultant = DatabaseConsultant()
    result = await consultant.handle_consultation(
        request.get("question"), 
        request.get("agent_name")
    )
    return result
```

### **Example 2: Testing Your Agent**
```python
# Test via API call (NOT separate script)
import requests
response = requests.post('http://localhost:8008/api/database-consultant', json={
    "question": "How do I optimize bid_cards queries?",
    "agent_name": "agent_1_frontend"
})
print(response.json())
```

---

## **EMERGENCY RECOVERY (IF BACKEND BREAKS):**

```bash
# If backend stops working:
taskkill //F //IM python.exe  # Kill ALL Python processes
cd ai-agents && python main.py  # Start ONLY the main backend
```

---

## **YOUR MISSION:**

1. **Read this prompt completely**
2. **Read the current main.py file**  
3. **Add your agent functionality INSIDE main.py**
4. **Test via API calls to localhost:8008**
5. **Verify the system still works**

**Remember: main.py is THE system. Everything goes there. No exceptions.**

---

**This coordination system ensures all agents work together through one unified backend on port 8008.**
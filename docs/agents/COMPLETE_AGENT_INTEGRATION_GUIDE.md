# 🎯 **COMPLETE AGENT INTEGRATION GUIDE**
**Everything You Need to Work on InstaBids Without Breaking Anything**

---

## **🏗️ WHAT IS THE SYSTEM?**

### **The InstaBids Backend:**
- **ONE FastAPI server** running on `http://localhost:8008`
- **Router-based architecture** - code organized in separate files
- **Error handling** - if one part breaks, rest keeps working
- **Shared database** - all agents use same Supabase database

### **File Structure:**
```
main.py                    = Core server (don't touch much)
routers/                   = Where you add your code
├── admin_routes.py        = Admin dashboard features
├── cia_routes.py          = Customer chat features  
├── contractor_routes.py   = Contractor portal features
├── homeowner_routes.py    = Homeowner dashboard features
├── monitoring_routes.py   = System monitoring
└── [other routers]        = Various specialized features
```

---

## **🎯 STEP-BY-STEP: ADD YOUR FEATURE**

### **Step 1: Understand What You're Building**
Ask yourself:
- Is this an admin feature? → Use `routers/admin_routes.py`
- Is this for customers? → Use `routers/cia_routes.py`
- Is this for contractors? → Use `routers/contractor_routes.py`
- Is this for homeowners? → Use `routers/homeowner_routes.py`
- Is this simple/general? → Add directly to `main.py`

### **Step 2: Read the Current Router File**
```python
# Example: You're adding admin feature
# Read: routers/admin_routes.py
# See how existing endpoints are structured
# Follow the same pattern
```

### **Step 3: Add Your Endpoint**
```python
# In the appropriate router file, add:
@router.post("/your-feature-name")
async def your_feature_name(request: dict):
    """
    Your feature description
    """
    try:
        # Your code here
        # Use MCP tools like:
        # - mcp__supabase__execute_sql() for database
        # - mcp__supabase__list_tables() for schema
        # - Any other MCP tools you need
        
        result = {
            "success": True,
            "data": "your feature result",
            "message": "Feature completed successfully"
        }
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Feature failed"
        }
```

### **Step 4: Test Your Feature**
```python
# DON'T run separate Python scripts
# DO make API calls to test:

import requests

response = requests.post('http://localhost:8008/api/admin/your-feature-name', json={
    "input": "test data"
})

print("Response:", response.json())
print("Status:", response.status_code)
```

---

## **🔧 INTEGRATION REQUIREMENTS**

### **Database Integration:**
```python
# Use MCP tools for database work:
from mcp import mcp__supabase__execute_sql

# Query database
result = await mcp__supabase__execute_sql(
    project_id="xrhgrthdcaymxuqcgrmj",
    query="SELECT * FROM your_table WHERE condition = 'value'"
)
```

### **Agent-to-Agent Communication:**
```python
# If you need to call another agent:
import requests

other_agent_response = requests.post('http://localhost:8008/api/cia/extract', json={
    "message": "user input"
})

# Use the response in your feature
extracted_data = other_agent_response.json()
```

### **Error Handling:**
```python
# Always wrap your code in try/except:
try:
    # Your feature logic
    result = do_your_work()
    return {"success": True, "data": result}
except Exception as e:
    # Log the error
    print(f"Error in your_feature: {e}")
    return {"success": False, "error": str(e)}
```

---

## **🚨 CRITICAL RULES - NEVER BREAK THESE**

### **❌ NEVER DO THIS:**
1. **Don't run separate Python scripts**: `python your_script.py`
2. **Don't create new FastAPI apps**: `app = FastAPI()`
3. **Don't use asyncio.run()**: Creates competing processes
4. **Don't start new servers**: `uvicorn.run()`
5. **Don't modify main.py imports**: Unless you know what you're doing

### **✅ ALWAYS DO THIS:**
1. **Add to existing router files**: Edit `routers/[appropriate_file].py`
2. **Test via API calls**: `requests.post('http://localhost:8008/api/...')`
3. **Use try/except**: Handle errors gracefully
4. **Follow existing patterns**: Copy structure of existing endpoints
5. **Use MCP tools**: For database, file operations, etc.

---

## **📋 INTEGRATION CHECKLIST**

### **Before You Start:**
- [ ] I know which router file to edit
- [ ] I've read the existing router file
- [ ] I understand the current endpoint patterns
- [ ] I know what MCP tools I need

### **While You Code:**
- [ ] I'm adding to existing router file (not creating new file)
- [ ] I'm following existing endpoint structure
- [ ] I'm using try/except error handling
- [ ] I'm using MCP tools for database/external operations

### **Testing Your Work:**
- [ ] Backend is running: `curl http://localhost:8008`
- [ ] My endpoint responds: `curl http://localhost:8008/api/[my-endpoint]`
- [ ] Other endpoints still work: Test a few existing ones
- [ ] No Python process conflicts: Only one `python main.py` running

### **Integration Verification:**
- [ ] Database operations work via MCP tools
- [ ] Agent-to-agent communication works via API calls
- [ ] Frontend can call my endpoint (if applicable)
- [ ] Error handling works (test with bad inputs)

---

## **🛠️ COMMON INTEGRATION PATTERNS**

### **Pattern 1: Simple Feature**
```python
# In appropriate router file:
@router.post("/simple-feature")
async def simple_feature(request: dict):
    # Process the request
    result = {"message": "Feature completed"}
    return result
```

### **Pattern 2: Database Feature**
```python
@router.post("/database-feature")
async def database_feature(request: dict):
    try:
        # Use MCP to query database
        data = await mcp__supabase__execute_sql(
            project_id="xrhgrthdcaymxuqcgrmj",
            query="SELECT * FROM table WHERE id = %s",
            params=[request.get("id")]
        )
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### **Pattern 3: Multi-Agent Feature**
```python
@router.post("/multi-agent-feature")
async def multi_agent_feature(request: dict):
    try:
        # Call CIA agent
        cia_response = requests.post('http://localhost:8008/api/cia/extract', 
                                   json={"message": request.get("user_input")})
        
        # Use CIA result
        extracted = cia_response.json()
        
        # Call database
        db_result = await mcp__supabase__execute_sql(
            project_id="xrhgrthdcaymxuqcgrmj",
            query="INSERT INTO table VALUES (%s)",
            params=[extracted.get("project_type")]
        )
        
        return {"success": True, "cia_data": extracted, "db_result": db_result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

## **🆘 TROUBLESHOOTING**

### **Backend Won't Start:**
```bash
# Kill all Python processes
taskkill //F //IM python.exe

# Start fresh
cd ai-agents
python main.py
```

### **My Endpoint Doesn't Work:**
1. Check if backend is running: `curl http://localhost:8008`
2. Check endpoint syntax in router file
3. Look at server logs for error messages
4. Test with simple endpoint first

### **Database Queries Fail:**
1. Verify you're using MCP tools correctly
2. Check table names exist: `mcp__supabase__list_tables()`
3. Test query syntax in Supabase dashboard first

### **Agent Communication Fails:**
1. Verify other agent endpoints work independently
2. Check API call syntax
3. Handle response errors properly

---

## **✅ SUCCESS CRITERIA**

**Your feature is properly integrated when:**
1. ✅ Backend starts without errors
2. ✅ Your endpoint responds correctly
3. ✅ Database operations work (if applicable)
4. ✅ Other agents' endpoints still work
5. ✅ Frontend can call your endpoint (if needed)
6. ✅ Error handling prevents crashes
7. ✅ No competing Python processes

---

## **🎯 QUICK START TEMPLATE**

**Copy this template for any new feature:**

```python
# In routers/[appropriate_router].py:

@router.post("/[your-feature-name]")
async def [your_feature_name](request: dict):
    """
    [Description of what this feature does]
    
    Args:
        request: Dict containing input parameters
        
    Returns:
        Dict with success status and data/error
    """
    try:
        # Validate input
        required_fields = ["field1", "field2"]
        for field in required_fields:
            if field not in request:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        # Your feature logic here
        # Use MCP tools as needed
        # Call other agents if needed
        
        result = {
            "success": True,
            "data": "your result data",
            "message": "Feature completed successfully"
        }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Feature failed: {str(e)}"
        }
```

**Test template:**
```python
import requests

response = requests.post('http://localhost:8008/api/[router-prefix]/[your-feature-name]', json={
    "field1": "test value 1",
    "field2": "test value 2"
})

print("Success:", response.json().get("success"))
print("Data:", response.json().get("data"))
print("Error:", response.json().get("error"))
```

---

**This guide contains everything needed to integrate any feature properly into the InstaBids system.**
# 🎯 **SIMPLE INSTRUCTIONS FOR ALL AGENTS**

## **THE SYSTEM:**
- Backend runs on port 8008 (already working)
- Has error handling (won't crash if you make mistakes)
- Uses router organization (keeps code clean)

## **TO ADD YOUR FEATURES:**

### **Step 1: Pick Where to Add Your Code**
```
For admin features:          Edit routers/admin_routes.py
For customer features:       Edit routers/cia_routes.py  
For contractor features:     Edit routers/contractor_routes.py
For homeowner features:      Edit routers/homeowner_routes.py
For simple features:         Edit main.py directly
```

### **Step 2: Add Your Endpoint**
```python
# In the router file, add:
@router.post("/your-feature-name")
async def your_feature_name(request: dict):
    # Your code here
    # Use MCP tools here
    return {"success": True, "data": "your response"}
```

### **Step 3: Test It**
```python
# Test with API call:
import requests
response = requests.post('http://localhost:8008/api/admin/your-feature-name')
print(response.json())
```

## **RULES:**
- ❌ Don't run `python separate_script.py` (creates conflicts)
- ✅ Do edit existing router files
- ✅ Do test via API calls to localhost:8008
- ✅ System has error handling - won't crash if you mess up

## **THAT'S IT!**
The system is designed to be simple and forgiving. Add your code to existing files, test via API calls, and you're good to go.

**Question: What router should I use for [specific feature]?**
**Answer: Pick the one that matches your feature's purpose, or use main.py for simple stuff.**
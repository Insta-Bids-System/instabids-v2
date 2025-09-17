# COIA Performance Fix Plan
## Current Problems & Solutions

### PROBLEM 1: Sequential LLM Calls (10+ seconds)
**Current:** 5+ GPT-4o calls in sequence
**Solution:** Run in parallel + use regex for simple tasks

### PROBLEM 2: Mode Detection Using GPT-4o (2-3 seconds)
**Current:** `await gpt_4o("detect if this is bid search")`
**Solution:** Use fast_mode_detector.py (0.001 seconds)

### PROBLEM 3: Bid Card Search Not Triggering
**Current:** Going to "research" mode instead of "bid_card_search"
**Solution:** Fix routing in unified_graph.py

## IMMEDIATE FIXES TO IMPLEMENT

### Fix 1: Replace Mode Detection
```python
# In unified_graph.py, replace:
from .mode_detector_fix import fixed_mode_detector_node

# With:
from .fast_mode_detector import fast_detect_mode

# In the mode detector node:
def mode_detector_node(state):
    message = state["messages"][-1].content
    # No LLM call needed!
    mode = fast_detect_mode(message, state.get("current_mode"))
    return {"current_mode": mode}
```

### Fix 2: Parallel Processing
```python
# In landing endpoint (unified_coia_api.py):
async def landing_page_conversation(request):
    # Run these in parallel
    tasks = []
    
    # Only extract if not already done
    if not state.get("company_extracted"):
        tasks.append(extract_company(message))
    
    # Only research if needed
    if "research" in message.lower() or not state.get("research_done"):
        tasks.append(do_research(company))
    
    # Run all tasks simultaneously
    results = await asyncio.gather(*tasks)
```

### Fix 3: Fix Bid Card Search
```python
# In bid_card_search_node.py:
async def bid_card_search_node(state):
    # Use fast extraction
    from .fast_mode_detector import fast_extract_location, fast_extract_project_types
    
    location = fast_extract_location(message, profile)
    project_types = fast_extract_project_types(message, profile)
    
    # Direct database query - no API middleman
    query = f"""
    SELECT * FROM bid_cards 
    WHERE status IN ('active', 'generated', 'collecting_bids')
    AND (
        location_city = '{location.get("city")}' 
        OR location_state = '{location.get("state")}'
        OR location_city IS NULL
    )
    AND (
        project_type = ANY(ARRAY{project_types})
        OR '{project_types[0]}' ILIKE '%' || project_type || '%'
    )
    LIMIT 10
    """
    
    # Return actual bid cards for UI
    return {
        "bid_cards_attached": bid_cards,
        "current_mode": "bid_card_search"
    }
```

## PERFORMANCE GAINS

| Operation | Before | After | Savings |
|-----------|--------|-------|---------|
| Mode Detection | 2-3 sec (GPT-4o) | 0.001 sec (regex) | 3 sec |
| Location Extract | 2 sec (GPT-4o) | 0.001 sec (regex) | 2 sec |
| Parallel Tasks | 10 sec (sequential) | 3 sec (parallel) | 7 sec |
| **TOTAL** | **14-16 seconds** | **3-4 seconds** | **~12 sec** |

## ANSWERING YOUR QUESTIONS

**Q: Should each thing be its own model?**
A: NO - Use ONE smart model (GPT-4o) for complex reasoning, but DON'T use it for simple pattern matching

**Q: Will separate models break memory?**
A: NO - Memory is stored in LangGraph state, not in the model. You can use different models and keep memory.

**Q: Multiple API keys?**
A: YES - Can help with rate limits, but the real issue is sequential calls, not API limits

**Q: How is it set up?**
A: LangGraph orchestrates nodes → Each node calls GPT-4o → All sequential → That's why it's slow

## QUICK WIN - Just Fix Mode Detection

The EASIEST fix that will immediately help:
1. Import fast_mode_detector.py
2. Replace GPT-4o mode detection with regex
3. Saves 2-3 seconds per request instantly

This alone would make bid card search actually trigger properly!
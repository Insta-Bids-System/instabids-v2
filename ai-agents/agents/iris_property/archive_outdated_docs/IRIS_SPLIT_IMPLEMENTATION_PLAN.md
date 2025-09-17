# IRIS Agent Split - Implementation Plan
**Created**: August 29, 2025  
**Goal**: Split single complex IRIS agent into two focused agents

## DECISION: Agent Assignment
- **KEEP CURRENT**: `iris/` → `iris_property/` (property issues, bid cards)
- **CREATE NEW**: `iris_inspiration/` (design inspiration only)

## PHASE 1: Create New Inspiration Agent

### Step 1.1: Create iris_inspiration folder structure
```
agents/iris_inspiration/
├── __init__.py
├── agent.py
├── models/
│   ├── __init__.py
│   ├── requests.py
│   └── responses.py
├── services/
│   ├── __init__.py
│   ├── inspiration_manager.py
│   └── memory_manager.py
└── workflows/
    ├── __init__.py
    └── inspiration_workflow.py
```

### Step 1.2: Copy and strip down files
- Copy agent.py → strip out bid card creation
- Copy models/ → keep image handling, remove bid card models
- Create inspiration_manager.py → only inspiration board logic
- Create inspiration_workflow.py → only design analysis

### Step 1.3: Update main.py routes
```python
from agents.iris_inspiration.routes import router as iris_inspiration_routes
app.include_router(iris_inspiration_routes, prefix="/api/iris-inspiration")
```

## PHASE 2: Rename Current Agent

### Step 2.1: Rename iris → iris_property
```
agents/iris/ → agents/iris_property/
```

### Step 2.2: Update all imports and references
- Update main.py imports
- Update __init__.py files
- Change API routes to /api/iris-property

### Step 2.3: Strip out inspiration logic
- Remove inspiration board creation from agent.py
- Remove inspiration paths from image_workflow.py
- Focus only on property documentation and bid cards

## PHASE 3: Frontend Updates

### Step 3.1: Create separate chat components
```
web/src/components/
├── inspiration/
│   └── IrisInspirationChat.tsx (new)
└── property/
    └── IrisPropertyChat.tsx (rename from IrisChat.tsx)
```

### Step 3.2: Update dashboards
- InspirationDashboard.tsx → use IrisInspirationChat
- PropertyDashboard.tsx → use IrisPropertyChat

## EXECUTION CHECKLIST
- [ ] Create iris_inspiration agent structure
- [ ] Copy and modify agent files
- [ ] Add inspiration routes to main.py
- [ ] Test inspiration agent works
- [ ] Rename iris → iris_property
- [ ] Update property agent routes
- [ ] Test property agent works
- [ ] Update frontend components
- [ ] Test both dashboard tabs
- [ ] Verify no cross-contamination

## SUCCESS CRITERIA
1. Inspiration tab only saves to inspiration_boards
2. Property tab only creates potential_bid_cards
3. No shared state between agents
4. Clean, focused functionality for each
5. All existing features preserved

**START EXECUTION BELOW THIS LINE**
---
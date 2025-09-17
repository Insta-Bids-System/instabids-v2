# main.py Critical Fixes Required

## 🔴 DISCOVERY: The Import Chaos

### Current Problematic Imports:
```python
# LINE 39-40: CONFLICTING ADMIN IMPORTS!
# from routers.admin_routes import router as admin_router  # DISABLED
from routers.admin_routes_enhanced import router as admin_enhanced_router
# BUT LINE 168 RE-IMPORTS IT!
from routers.admin_routes import router as admin_router  # RE-ENABLED at line 168!

# LINES 41-44: THREE BID CARD ROUTERS!
from routers.bid_card_api_simple import router as bid_card_api_simple_router
from routers.bid_card_lifecycle_routes import router as bid_card_lifecycle_router  
from routers.bid_card_simple_lifecycle import router as bid_card_simple_lifecycle_router

# LINE 52: WRONG MESSAGING ROUTER!
from routers.messaging_simple import router as messaging_api_router  # Using simple version!
# Should be using messaging_api.py instead!
```

## 🛠️ REQUIRED FIXES

### Fix 1: Admin Router Conflict
```python
# REMOVE LINE 40:
# from routers.admin_routes_enhanced import router as admin_enhanced_router

# KEEP ONLY LINE 168:
from routers.admin_routes import router as admin_router

# REMOVE from app.include_router section:
# app.include_router(admin_enhanced_router)
```

### Fix 2: Bid Card Router Triplication
```python
# REMOVE LINES 41 & 44:
# from routers.bid_card_api_simple import router as bid_card_api_simple_router
# from routers.bid_card_simple_lifecycle import router as bid_card_simple_lifecycle_router

# KEEP ONLY LINE 42:
from routers.bid_card_lifecycle_routes import router as bid_card_lifecycle_router

# REMOVE from app.include_router section:
# app.include_router(bid_card_api_simple_router, prefix="/api/bid-cards")
# app.include_router(bid_card_simple_lifecycle_router)
```

### Fix 3: Wrong Messaging Router
```python
# CHANGE LINE 52 FROM:
from routers.messaging_simple import router as messaging_api_router

# TO:
from routers.messaging_api import router as messaging_api_router
```

### Fix 4: Enable Campaign Router
```python
# UNCOMMENT LINE 194:
from routers.campaign_api import router as campaign_router

# AND ADD TO app.include_router section:
app.include_router(campaign_router)
```

## 📋 Complete Fixed Import Section

```python
# ADMIN - Agent 2
from routers.admin_routes import router as admin_router

# BID CARDS - Shared between Agent 1 & 2  
from routers.bid_card_lifecycle_routes import router as bid_card_lifecycle_router

# MESSAGING - Messaging Agent
from routers.messaging_api import router as messaging_api_router

# AI AGENTS
from routers.cia_routes import router as cia_router  # Campaign Intelligence
from routers.jaa_routes import router as jaa_router  # Job Analysis
from routers.cda_routes import router as cda_router  # Contractor Discovery
from routers.eaa_routes import router as eaa_router  # Email Automation
from routers.unified_coia_api import router as unified_coia_router  # Onboarding

# CONTRACTOR & HOMEOWNER
from routers.contractor_routes import router as contractor_router
from routers.homeowner_routes import router as homeowner_router
from routers.contractor_job_search import router as contractor_job_search_router
from routers.contractor_proposals_api import router as contractor_proposals_router

# CAMPAIGNS
from routers.campaign_api import router as campaign_router

# DEMO & TESTING
from routers.demo_routes import router as demo_router
from routers.test_ws_routes import router as test_ws_router

# SYSTEM
from routers.websocket_routes import router as websocket_router
from routers.monitoring_routes import router as monitoring_router
from routers.image_upload_api import router as image_upload_router

# API IMPORTS (from /api folder)
from api.demo_boards import router as demo_boards_router
from api.iris_chat import router as iris_router
from api.image_generation import router as image_generation_router
```

## 📋 Complete Fixed app.include_router Section

```python
# ADMIN SYSTEM - Agent 2
app.include_router(admin_router, prefix="/api/admin")

# BID CARDS - Core Feature
app.include_router(bid_card_lifecycle_router)

# MESSAGING SYSTEM
app.include_router(messaging_api_router)

# AI AGENTS
app.include_router(cia_router, prefix="/api/cia")
app.include_router(jaa_router)
app.include_router(cda_router)
app.include_router(eaa_router)
app.include_router(unified_coia_router)

# CONTRACTORS & HOMEOWNERS
app.include_router(contractor_router)
app.include_router(homeowner_router)
app.include_router(contractor_job_search_router)
app.include_router(contractor_proposals_router)

# CAMPAIGNS
app.include_router(campaign_router)

# IRIS & IMAGE GENERATION
app.include_router(iris_router)
app.include_router(image_generation_router)

# DEMO & TESTING
app.include_router(demo_router)
app.include_router(demo_boards_router)
app.include_router(test_ws_router, prefix="/api/test")

# SYSTEM
app.include_router(websocket_router)
app.include_router(monitoring_router)
app.include_router(image_upload_router)
```

## 🎯 Impact of These Fixes

### Before:
- 3 bid card routers = conflicting endpoints
- 2 admin routers = Agent 2 confusion
- Wrong messaging router = missing features
- Campaign router disabled = CIA broken

### After:
- 1 bid card router = clear ownership
- 1 admin router = Agent 2 knows their endpoints
- Correct messaging router = full features
- Campaign router enabled = CIA functional

## ⚠️ Testing Required After Fixes

1. Test admin login: `http://localhost:8008/api/admin/login`
2. Test bid cards: `http://localhost:8008/api/bid-cards`
3. Test messaging: `http://localhost:8008/api/messages/health`
4. Test campaigns: `http://localhost:8008/api/campaigns`

## 📁 Files to Archive After Fixes

Once main.py is fixed, these files can be moved to `/cleanup_archive/`:
- `routers/admin_routes_enhanced.py`
- `routers/bid_card_api_simple.py`
- `routers/bid_card_simple_lifecycle.py`
- `routers/messaging_simple.py`
- `routers/messaging_fixed.py`

## 🔒 Backup Command Before Changes

```bash
copy main.py main.py.backup_before_consolidation
```

This will fix the chaos that's been confusing all the agents!
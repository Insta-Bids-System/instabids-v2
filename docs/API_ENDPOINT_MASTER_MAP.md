# 🗺️ MASTER API ENDPOINT MAP
**CRITICAL**: This is the SINGLE SOURCE OF TRUTH for all API endpoints
**Last Updated**: December 2024
**Total Endpoints**: ~186

## 🚨 AGENT OWNERSHIP MAP

### Agent 2 (Backend/Admin) OWNS:
- `/api/admin/*` - ALL admin endpoints
- `/api/auth/*` - Authentication 
- `/ws/admin/*` - Admin WebSockets
- `/api/monitoring/*` - System monitoring

### Agent 1 (Frontend) OWNS:
- `/api/cia/*` - CIA chat interface
- `/api/homeowner/*` - Homeowner dashboard
- `/api/bid-cards/public/*` - Public bid cards

### Agent 3 (Homeowner UX) OWNS:
- `/api/iris/*` - IRIS AI assistant
- `/api/projects/*` - Project management
- `/api/inspiration/*` - Inspiration boards

### Agent 4 (Contractor) OWNS:
- `/api/contractor/*` - Contractor portal
- `/api/coia/*` - COIA agent
- `/api/proposals/*` - Bid proposals

### Shared/System:
- `/api/messaging/*` - Messaging system
- `/api/campaigns/*` - Outreach campaigns
- `/api/tracking/*` - Analytics

## 📁 CURRENT CHAOS STRUCTURE

### `routers/` folder (27 files!):
```
admin_routes.py          - Agent 2 admin endpoints
admin_routes_enhanced.py - DUPLICATE admin routes
bid_card_api.py         - Bid card CRUD
bid_card_api_simple.py  - DUPLICATE bid cards
bid_card_lifecycle_routes.py - More bid cards
bid_card_simple_lifecycle.py - MORE DUPLICATES
campaign_api.py         - Campaign management
cda_routes.py          - CDA agent
cia_routes.py          - CIA agent
contractor_agent_api.py - Contractor agent
contractor_job_search.py - Job search
contractor_proposals_api.py - Proposals
contractor_routes.py    - More contractor
demo_routes.py         - Demo endpoints
eaa_routes.py          - EAA agent
homeowner_routes.py    - Homeowner UI
image_upload_api.py    - Image uploads
jaa_routes.py          - JAA agent
messaging_api.py       - Messaging v1
messaging_fixed.py     - Messaging v2
messaging_simple.py    - Messaging v3
monitoring_routes.py   - Agent 6 monitoring
test_ws_routes.py      - Test WebSockets
unified_coia_api.py    - COIA unified
websocket_routes.py    - WebSocket handlers
```

### `api/` folder (11 files):
```
bid_cards.py          - More bid cards!
bid_cards_simple.py   - Even more!
campaigns_intelligent.py - Smart campaigns
demo_boards.py        - Demo boards
demo_iris.py          - IRIS demos
image_generation.py   - AI images
inspiration_boards.py - Inspiration
iris_chat.py          - IRIS chat
projects.py           - Projects
tracking.py           - Tracking
vision.py             - Vision AI
```

## 🔥 PROBLEMS THIS CAUSES

1. **Agent 2 doesn't know** they have 22+ admin endpoints
2. **Duplicate implementations** (4+ bid card APIs!)
3. **No agent can find** their own endpoints
4. **Updates break things** because agents don't know what exists
5. **New features duplicate** existing functionality

## ✅ PROPOSED SOLUTION

### 1. IMMEDIATE: Create Agent Documentation
```
ai-agents/
├── AGENT_ENDPOINTS/
│   ├── AGENT_1_FRONTEND_ENDPOINTS.md
│   ├── AGENT_2_ADMIN_ENDPOINTS.md
│   ├── AGENT_3_HOMEOWNER_ENDPOINTS.md
│   ├── AGENT_4_CONTRACTOR_ENDPOINTS.md
│   └── SHARED_SYSTEM_ENDPOINTS.md
```

### 2. CONSOLIDATE: One Router Per Domain
```
routers/
├── admin.py         # ALL admin endpoints (Agent 2)
├── homeowner.py     # ALL homeowner endpoints (Agent 1/3)
├── contractor.py    # ALL contractor endpoints (Agent 4)
├── agents.py        # ALL AI agent endpoints
├── messaging.py     # Unified messaging
├── bid_cards.py     # Single bid card API
└── websocket.py     # All WebSocket handlers
```

### 3. REMOVE: Delete Duplicates
- Keep ONE bid card API
- Keep ONE messaging API
- Keep ONE admin API
- Archive the rest

### 4. DOCUMENT: Mandatory Headers
```python
"""
OWNER: Agent 2
DOMAIN: Admin Dashboard
ENDPOINTS:
  - GET /api/admin/dashboard
  - POST /api/admin/login
  - WebSocket /ws/admin
"""
```

## 🚀 NEXT STEPS

1. Create endpoint ownership documentation
2. Consolidate duplicate routers
3. Delete redundant files
4. Update imports in main.py
5. Test everything still works
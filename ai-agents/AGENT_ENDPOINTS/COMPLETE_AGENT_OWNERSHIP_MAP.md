# Complete Agent Ownership Map - InstaBids System

## CRITICAL DISCOVERY: The Real Agent Architecture
**Problem**: Agents don't know what they own because endpoints are scattered across 38 files
**Solution**: This document maps EVERY endpoint to its owner

## The Actual AI Agents in the System

### 1. CIA (Campaign Intelligence Agent)
**Location**: `/agents/cia_agent.py`
**Purpose**: Intelligent campaign management and targeting
**Endpoints**: `/api/campaigns/*`
**Files**:
- `/api/campaigns_intelligent.py` - Main CIA endpoints
- `/routers/campaign_routes.py` - Campaign CRUD
**Database Tables**:
- `campaigns`
- `campaign_recipients`
- `campaign_stats`
- `campaign_templates`

### 2. JAA (Job Analysis Agent)
**Location**: `/agents/jaa_agent.py`
**Purpose**: Project analysis and categorization
**Endpoints**: `/api/projects/*`
**Files**:
- `/api/projects.py` - Project analysis endpoints
- `/routers/project_routes.py` - Project management
**Database Tables**:
- `projects`
- `project_categories`
- `project_analysis`

### 3. CDA (Contractor Discovery Agent)
**Location**: `/agents/cda_agent.py`
**Purpose**: Contractor matching and discovery
**Endpoints**: `/api/contractors/*`
**Files**:
- `/routers/contractor_routes.py` - Contractor management
- `/routers/contractor_matching.py` - Matching algorithm
**Database Tables**:
- `contractors`
- `contractor_profiles`
- `contractor_matches`

### 4. EAA (Email Automation Agent)
**Location**: `/agents/eaa_agent.py`
**Purpose**: Email campaign automation
**Endpoints**: `/api/email/*`
**Files**:
- `/routers/email_routes.py` - Email management
**Integration**: MailHog for testing

### 5. WFA (Web Form Agent)
**Location**: `/agents/wfa_agent.py`
**Purpose**: Form processing and validation
**Endpoints**: `/api/forms/*`
**Files**:
- `/routers/form_routes.py` - Form handling
**Database Tables**:
- `form_submissions`
- `form_templates`

### 6. COIA (Contractor Onboarding Intelligence Agent)
**Location**: `/agents/coia_agent.py`
**Purpose**: Intelligent contractor onboarding
**Endpoints**: `/api/onboarding/*`
**Files**:
- `/routers/onboarding_routes.py` - Onboarding flow
**Database Tables**:
- `onboarding_steps`
- `onboarding_progress`

### 7. CJA (Contractor Job Agent)
**Location**: `/agents/cja_agent.py`
**Purpose**: Job matching for contractors
**Endpoints**: `/api/job-matching/*`
**Files**:
- `/routers/job_matching_routes.py` - Job matching logic

### 8. IRIS (Intelligent Response & Interaction System)
**Location**: `/agents/iris_agent.py`
**Purpose**: AI chat and interaction system
**Endpoints**: `/api/iris/*`
**Files**:
- `/api/iris_chat.py` - IRIS chat endpoints
- `/api/demo_iris.py` - IRIS demo endpoints
- `/routers/iris_routes.py` - IRIS main routes
**Special Features**:
- Three-column layout
- Real-time chat
- Context awareness

### 9. Messaging Agent (Content Filter & Alias System)
**Location**: `/agents/messaging_agent.py`
**Purpose**: Message filtering and contractor aliasing
**Endpoints**: `/api/messages/*`
**Files**:
- `/routers/messaging_api.py` - Main messaging API
- `/routers/messaging_simple.py` - Simplified version
- `/routers/messaging_fixed.py` - Bug fixes version
**Database Tables**:
- `messaging_system_messages`
- `conversations`
- `message_filters`
- `contractor_aliases`

### 10. Vision Agent (Image Processing)
**Location**: `/agents/vision_agent.py`
**Purpose**: Image analysis and generation
**Endpoints**: `/api/vision/*`, `/api/image-generation/*`
**Files**:
- `/api/vision.py` - Vision processing
- `/api/image_generation.py` - AI image generation
**Integration**: OpenAI Vision API

### 11. Inspiration Boards Agent
**Location**: `/agents/inspiration_agent.py`
**Purpose**: Design inspiration boards
**Endpoints**: `/api/inspiration/*`
**Files**:
- `/api/inspiration_boards.py` - Board management
- `/api/demo_boards.py` - Demo boards
**Database Tables**:
- `inspiration_boards`
- `board_items`

## Development Support Agents (Agent 1-6)

### Agent 1 - Frontend Development
**Owns**: All React components in `/src/`
**Focus**: User interfaces, bid card display, dashboards

### Agent 2 - Admin System
**Owns**: Admin panel at `/api/admin/*`
**Files**: 
- `/routers/admin_routes.py` (primary)
- `/routers/admin_api.py` (duplicate - merge needed)
- `/routers/admin_bid_cards.py` (duplicate - merge needed)
**Database**: `admin_*` tables

### Agent 3 - Backend Core
**Owns**: Core FastAPI setup, authentication, middleware
**Files**: `main.py`, core utilities

### Agent 4 - Database Management
**Owns**: Supabase schema, migrations
**Files**: `/database/`, `/migrations/`

### Agent 5 - AI/ML Integration
**Owns**: OpenAI integrations, model management
**Files**: AI utility functions

### Agent 6 - QA & System Management
**Owns**: Testing, documentation, system organization
**Current Task**: Creating this documentation

## Endpoint Consolidation Plan

### Phase 1: Merge Duplicates
1. **Bid Cards** (4 versions → 1)
   - Keep: `/routers/bid_card_lifecycle_routes.py`
   - Merge: `bid_card_api.py`, `bid_cards.py`, `bid_cards_simple.py`

2. **Messaging** (3 versions → 1)
   - Keep: `/routers/messaging_api.py`
   - Merge: `messaging_simple.py`, `messaging_fixed.py`

3. **Admin** (3 versions → 1)
   - Keep: `/routers/admin_routes.py`
   - Merge: `admin_api.py`, `admin_bid_cards.py`

### Phase 2: Organize by Agent
Create clear folder structure:
```
/routers/
  /cia/         - Campaign Intelligence
  /jaa/         - Job Analysis
  /cda/         - Contractor Discovery
  /iris/        - IRIS system
  /messaging/   - Messaging system
  /admin/       - Admin system (Agent 2)
  /core/        - Shared/core functionality
```

### Phase 3: Update main.py
Update all router imports to use consolidated versions

## Database Table Ownership

### Core Tables (Agent 3)
- `users`
- `auth_tokens`
- `sessions`

### Admin Tables (Agent 2)
- `admin_sessions`
- `admin_activity_log`
- `admin_settings`

### Project Tables (JAA)
- `projects`
- `project_categories`

### Contractor Tables (CDA)
- `contractors`
- `contractor_profiles`

### Messaging Tables (Messaging Agent)
- `messaging_system_messages`
- `conversations`
- `message_filters`
- `contractor_aliases`

### Campaign Tables (CIA)
- `campaigns`
- `campaign_recipients`
- `campaign_stats`

### Bid Card Tables (Shared: Agent 1 & 2)
- `bid_cards`
- `bid_card_items`
- `bid_card_lifecycle`

## Critical Issues Found

1. **Agent 2 Problem**: Built admin system but doesn't know about 50+ endpoints
   - Solution: Created `AGENT_2_ADMIN_ENDPOINTS.md`

2. **Duplicate Code**: Same functionality in 3-4 different files
   - Solution: Consolidation plan above

3. **No Agent Ownership**: Endpoints scattered without clear ownership
   - Solution: This document

4. **Empty Folders**: `/shared/`, `/models/`, `/cho/`, `/cra/`, `/sma/`
   - Solution: Delete or repurpose

5. **Nested Confusion**: `/consultants/consultants/`, duplicate migration folders
   - Solution: Flatten structure

## Action Items

1. [ ] Each agent reads their ownership document
2. [ ] Consolidate duplicate routers (Phase 1)
3. [ ] Reorganize folder structure (Phase 2)
4. [ ] Update main.py imports (Phase 3)
5. [ ] Delete empty folders
6. [ ] Create agent-specific test folders

## Success Metrics

- No agent asks "what endpoints do I own?"
- No duplicate code across routers
- Clear folder organization
- All tests in proper folders
- main.py has clean imports

## Contact for Questions
**System Architect**: Agent 6 (QA & System Management)
**Document Location**: `/ai-agents/AGENT_ENDPOINTS/`
**Last Updated**: Current session
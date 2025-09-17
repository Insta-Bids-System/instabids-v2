# InstaBids System Interdependency Map

**Created**: August 1, 2025  
**Purpose**: Complete system architecture and component interdependencies for all development agents  
**Maintained by**: Agent 6 (Quality Gatekeeper)

## 🎯 **CRITICAL CONTEXT FOR ALL AGENTS**

This document provides complete system context so any agent can understand:
- How their work fits into the overall system
- Which components they can depend on
- What impact their changes might have
- Where to find specific functionality

---

## 🏗️ **COMPLETE SYSTEM ARCHITECTURE**

### **High-Level Data Flow**
```
Homeowner Input → CIA → JAA → CDA → EAA → WFA → COIA
                   ↓         ↓     ↓     ↓     ↓
              Multi-Project  |     |     |     |
               Memory    Database Admin  |     |
                         System Dashboard|     |
                                         |     |
                              Email/SMS/Forms  |
                                         |     |
                                 Contractor Response
                                         ↓
                               Complete Account Creation
```

### **Real-Time Monitoring Layer**
```
Admin Dashboard (WebSocket) ← All Agents + Database + System Metrics
```

---

## 🤖 **AGENT INTERDEPENDENCIES**

### **1. CIA (Customer Interface Agent)**
**Location**: `ai-agents/agents/cia/`  
**Dependencies**:
- **Input Sources**: Web frontend, mobile app, API calls
- **AI Integration**: Claude Opus 4 API (Anthropic)
- **Memory System**: `ai-agents/memory/multi_project_store.py`
- **Database**: Supabase tables: `user_memories`, `project_summaries`, `project_contexts`

**Dependents**:
- **JAA Agent**: Receives conversation transcripts and extracted data
- **Admin Dashboard**: Provides conversation metrics and status
- **Frontend**: Returns real-time conversation responses

**Key Files**:
- `agent.py` - Main CIA implementation with Claude Opus 4
- `mode_manager.py` - Conversation mode management
- `modification_handler.py` - Bid card modification handling
- `prompts.py` - Conversation prompts and templates
- `state.py` - LangGraph state definitions

### **2. JAA (Job Assessment Agent)**
**Location**: `ai-agents/agents/jaa/`  
**Dependencies**:
- **Input Sources**: CIA conversation transcripts and extracted data
- **AI Integration**: Claude Opus 4 + LangGraph workflow
- **Database**: Supabase tables: `bid_cards`, `projects`, `conversations`

**Dependents**:
- **CDA Agent**: Receives completed bid cards for contractor discovery
- **Admin Dashboard**: Provides bid card generation metrics
- **Frontend**: Returns bid card previews for homeowner approval

**Key Files**:
- `agent.py` - Main JAA class with LangGraph workflow
- `workflow.py` - Bid card generation workflow
- `state.py` - LangGraph state management
- `prompts.py` - Data extraction and validation prompts

### **3. CDA (Contractor Discovery Agent)**  
**Location**: `ai-agents/agents/cda/`  
**Dependencies**:
- **Input Sources**: JAA bid cards with project requirements
- **External APIs**: Google Places API for Tier 3 discovery
- **Database**: Supabase tables: `contractors`, `contractor_discovery_cache`

**Dependents**:
- **EAA Agent**: Provides discovered contractors for outreach campaigns
- **Admin Dashboard**: Discovery metrics and contractor counts
- **Analytics**: Performance data and discovery success rates

**Key Files**:
- `agent.py` - ⭐ PRIMARY implementation (production)
- `agent_v2.py` - ⚠️ Enhanced version (needs consolidation)
- `agent_v2_optimized.py` - ⚠️ Performance version (needs consolidation)
- `web_search_agent.py` - Google Places integration
- `scoring.py` - Contractor scoring algorithms

### **4. EAA (External Acquisition Agent)**
**Location**: `ai-agents/agents/eaa/`  
**Dependencies**:
- **Input Sources**: CDA discovered contractors with match scores
- **MCP Integration**: Real email sending via `mcp__instabids-email__send_email`
- **AI Integration**: Claude for email personalization
- **External Services**: Twilio for SMS, MailHog for testing

**Dependents**:
- **WFA Agent**: Queues website form filling requests
- **COIA Agent**: Routes contractor responses for onboarding
- **Admin Dashboard**: Campaign metrics and response tracking

**Key Files**:
- `agent.py` - Main EAA implementation
- `mcp_email_channel_claude.py` - ⭐ Claude-powered email system
- `template_engine.py` - Dynamic message generation
- `response_parser.py` - Response analysis and routing

### **5. WFA (Website Form Automation Agent)**
**Location**: `ai-agents/agents/wfa/`  
**Dependencies**:
- **Input Sources**: EAA queued website form requests
- **Browser Automation**: Playwright for headless form filling
- **Database**: Supabase tables: `contractor_outreach_attempts`

**Dependents**:
- **EAA Agent**: Returns form submission confirmations
- **Admin Dashboard**: Form automation success metrics
- **Analytics**: Form filling performance and success rates

**Key Files**:
- `agent.py` - Single file implementation with Playwright

### **6. IRIS (Design Inspiration Assistant Agent)**
**Location**: `ai-agents/agents/iris/`  
**Dependencies**:
- **Input Sources**: Frontend image uploads and design conversations
- **AI Integration**: Claude 3.7 Sonnet (most intelligent model)
- **Storage**: Image handling and tagging system

**Dependents**:
- **CIA Agent**: Receives completed design visions for project scoping
- **Frontend**: Provides design guidance and style recognition
- **Admin Dashboard**: Design consultation metrics

**Key Files**:
- `agent.py` - Single file implementation with Claude 3.7 Sonnet

### **7. COIA (Contractor Interface Agent)**
**Location**: `ai-agents/agents/coia/`  
**Dependencies**:
- **Input Sources**: EAA contractor responses and direct signups
- **AI Integration**: Claude Opus 4 + LangGraph workflow
- **Authentication**: Supabase Auth for account creation
- **Database**: Supabase tables: `auth.users`, `profiles`, `contractors`

**Dependents**:
- **CDA Agent**: Adds newly onboarded contractors to discovery system
- **Admin Dashboard**: Onboarding completion metrics
- **Frontend**: Contractor portal and profile management

**Key Files**:
- `agent.py` - ⭐ PRIMARY implementation (production)
- `research_based_agent.py` - ⚠️ Enhanced version (needs consolidation)
- `prompts.py` - Conversation prompts by onboarding stage
- `state.py` - LangGraph state management

---

## 🗄️ **DATABASE INTERDEPENDENCIES**

### **Supabase Tables (33+ Total)**

#### **Core Business Tables**
- `bid_cards` - JAA creates, CDA reads, Admin monitors
- `contractors` - CDA queries, COIA creates/updates, EAA reads
- `projects` - CIA creates, JAA links, Admin tracks
- `conversations` - CIA creates, JAA processes, Admin monitors

#### **Memory System Tables** 
- `user_memories` - CIA reads/writes cross-project preferences
- `project_summaries` - CIA generates AI-powered project summaries  
- `project_contexts` - CIA maintains project-specific conversation state

#### **Campaign & Outreach Tables**
- `contractor_outreach_campaigns` - EAA manages, Admin monitors
- `contractor_outreach_attempts` - EAA/WFA create, Admin tracks
- `contractor_responses` - EAA processes, COIA routes, Admin logs
- `contractor_engagement_summary` - EAA aggregates, Admin displays

#### **Authentication & User Tables**
- `auth.users` - Supabase Auth, COIA creates contractor accounts
- `profiles` - COIA creates, links to auth users
- `contractor_onboarding_sessions` - COIA manages conversation state

#### **Admin & Monitoring Tables**
- `admin_users` - Admin dashboard authentication
- `admin_sessions` - Session management for admin login
- `agent_status_logs` - System health monitoring
- `system_metrics` - Performance data collection

---

## 🔌 **API INTERDEPENDENCIES**

### **FastAPI Server** (`ai-agents/main.py`)
**Port**: 8008  
**CORS**: Allows all localhost ports for frontend flexibility

#### **Core Agent Endpoints**
- `POST /api/cia/conversation` - CIA conversations with project awareness
- `POST /api/jaa/generate-bid-card` - JAA bid card generation
- `POST /api/cda/discover-contractors` - CDA contractor discovery
- `POST /api/eaa/start-campaign` - EAA multi-channel campaigns
- `GET /api/coia/onboarding-status` - COIA onboarding progress

#### **Admin Dashboard Endpoints**
- `POST /api/admin/login` - Admin authentication
- `GET /api/admin/bid-cards` - Bid card monitoring data
- `POST /api/admin/restart-agent` - Agent restart functionality
- `WebSocket /ws/admin` - Real-time updates and monitoring

#### **System Integration Endpoints**
- `GET /api/projects/{user_id}` - Multi-project memory access
- `POST /api/projects` - New project creation
- `GET /api/system/health` - Overall system health check

### **External API Dependencies**

#### **AI Services**
- **Anthropic Claude API**: CIA, JAA, EAA, COIA (Opus 4), IRIS (3.7 Sonnet)
- **API Keys**: `ANTHROPIC_API_KEY` environment variable
- **Rate Limits**: Managed per agent with backoff strategies

#### **External Services**
- **Google Places API**: CDA Tier 3 contractor discovery
- **Twilio API**: EAA SMS campaigns (optional)
- **MCP Email Service**: EAA real email sending (via MailHog for testing)

---

## 🌐 **FRONTEND INTERDEPENDENCIES**

### **React Frontend** (`web/`)
**Port**: 5173 (or any available port)  
**Framework**: React + TypeScript + Vite + Tailwind CSS

#### **Core Components**
- `ChatInterface.tsx` - CIA agent conversations
- `BidCardViewer.tsx` - JAA generated bid cards
- `DesignBoard.tsx` - IRIS design inspiration system
- `ContractorPortal.tsx` - COIA onboarding interface

#### **Admin Dashboard Components**
- `AdminLogin.tsx` - Secure admin authentication
- `MainDashboard.tsx` - Central monitoring hub
- `BidCardMonitor.tsx` - Live bid card tracking
- `AgentStatusPanel.tsx` - Real-time agent health monitoring
- `DatabaseViewer.tsx` - Database operations monitoring
- `SystemMetrics.tsx` - Performance visualization

#### **WebSocket Integration**
- `useWebSocket.tsx` - Hook for real-time admin updates
- `useAdminAuth.tsx` - Admin authentication management
- Real-time message types: `agent_status`, `bid_card_update`, `database_operation`

---

## 🧪 **TESTING INTERDEPENDENCIES**

### **Agent-Specific Tests**
- `test_cia_claude_extraction.py` - CIA functionality with real API
- `test_jaa_generation.py` - JAA bid card creation
- `test_cda_discovery.py` - CDA 3-tier discovery system
- `test_actual_mcp_emails.py` - EAA real email sending ✅ VERIFIED
- `test_direct_form_fill.py` - WFA form automation ✅ VERIFIED
- `test_coia_conversations.py` - COIA onboarding workflow

### **Integration Tests**
- `test_complete_system_validation.py` - End-to-end agent pipeline
- `test_complete_admin_system.py` - Admin dashboard system ✅ PASSES
- `test_multi_project_memory.py` - Memory system integration
- `test_timing_system_complete.py` - Orchestration system

### **Test Data Dependencies**
- Test contractors in `contractors` table
- Sample bid cards for testing discovery
- Mock email responses for EAA testing
- Test website forms for WFA verification

---

## 📁 **FILE STRUCTURE INTERDEPENDENCIES**

### **Critical Configuration Files**
- `ai-agents/main.py` - FastAPI server with all agent integrations
- `ai-agents/database_simple.py` - Shared database operations
- `web/package.json` - Frontend dependencies and scripts
- `.env` files - API keys and configuration (multiple locations)

### **Shared Utilities**
- `ai-agents/memory/` - Multi-project memory system (shared by CIA)
- `ai-agents/orchestration/` - Timing and campaign orchestration
- `ai-agents/admin/` - Admin dashboard backend services
- `web/src/hooks/` - Shared React hooks for API and WebSocket

### **Documentation Files**
- `CLAUDE.md` - Build status and instructions for all agents
- `AGENT_ARCHITECTURE_COMPLETE_ANALYSIS.md` - Master system analysis
- `agent_specifications/` - Individual agent development guides
- Each agent's `README.md` - Detailed implementation documentation

---

## ⚠️ **KNOWN QUALITY ISSUES**

### **High Priority**
1. **CDA Agent**: 3 versions need consolidation (`agent.py`, `agent_v2.py`, `agent_v2_optimized.py`)
2. **COIA Agent**: 2 versions need consolidation (`agent.py`, `research_based_agent.py`)
3. **Empty Directories**: CHO, CRA, SMA need implementation or removal

### **Medium Priority**
- Missing comprehensive integration tests across all 7 agents
- No centralized error handling standards
- Environment variable management scattered across files

---

## 🚀 **DEPLOYMENT INTERDEPENDENCIES**

### **Development Environment**
```bash
# Backend (Required First)
cd ai-agents && python main.py
# Server: http://localhost:8008

# Frontend (Any Port)
cd web && npm run dev  
# Dashboard: http://localhost:5173

# Admin Access
# URL: http://localhost:5173/admin/login
# Login: admin@instabids.com / admin123
```

### **Production Dependencies**
- **Database**: Supabase project with 33+ tables
- **AI APIs**: Anthropic API keys for Claude Opus 4 & 3.7 Sonnet
- **External APIs**: Google Places API for contractor discovery
- **Email Service**: MCP email integration (MailHog for testing)
- **Monitoring**: Admin dashboard for system health

---

## 🔄 **DATA FLOW SUMMARY**

### **Primary Workflow**
1. **Homeowner** → CIA (conversation) → JAA (bid card) → CDA (contractors) → EAA (outreach) → WFA (forms) → COIA (onboarding)

### **Real-Time Monitoring**
2. **All Agents** → Admin Dashboard (WebSocket) → Real-time updates

### **Memory & Context**
3. **CIA** ↔ Multi-Project Memory ↔ Database (persistent context)

### **External Integration**
4. **System** ↔ Claude APIs ↔ Google Places ↔ MCP Email ↔ Supabase

---

## 📞 **SUPPORT FOR AGENTS**

### **Finding Specific Functionality**
- **Agent Implementation**: Check `/agents/{agent_name}/agent.py`
- **Agent Documentation**: Read `/agents/{agent_name}/README.md`
- **Database Operations**: Use `database_simple.py` functions
- **API Integration**: Check `main.py` for endpoint definitions
- **Testing**: Look for `test_*.py` files in agent directories

### **Understanding System State**
- **Current Build Status**: Read `CLAUDE.md` 
- **System Architecture**: This file (`SYSTEM_INTERDEPENDENCY_MAP.md`)
- **Agent Specifications**: Check `agent_specifications/` for development guides
- **Live System Status**: Use admin dashboard at http://localhost:5173/admin/login

---

This interdependency map ensures all development agents have complete context for working on any part of the InstaBids system. Update this document when making architectural changes or adding new components.
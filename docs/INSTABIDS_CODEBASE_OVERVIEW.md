# InstaBids Codebase Overview - Complete File Structure

**Maintained by**: Agent 6 (Quality Gatekeeper)  
**Last Updated**: August 1, 2025  
**Purpose**: Complete file structure and context for all development agents

## 📁 **COMPLETE DIRECTORY STRUCTURE**

```
instabids/
├── 📄 README.md                           # ✅ UPDATED - Main project overview
├── 📄 CLAUDE.md                           # 🎯 CRITICAL - Build status & instructions
├── 📄 SYSTEM_INTERDEPENDENCY_MAP.md       # 🔗 NEW - Complete system architecture
├── 📄 CODEBASE_OVERVIEW.md               # 📋 THIS FILE - Complete file guide
├── 📄 BACKEND_SYSTEM_STATUS.md           # 📊 System status overview
├── 📄 COMPLETE_ADMIN_DASHBOARD*.md       # 📱 Admin dashboard documentation
│
├── 🤖 ai-agents/                         # 🎯 BACKEND - Python FastAPI + AI Agents
│   ├── 📄 main.py                        # ⭐ CRITICAL - FastAPI server (port 8008)
│   ├── 📄 database_simple.py             # 🗄️ SHARED - Database operations
│   ├── 📄 requirements.txt               # 📦 Python dependencies
│   │
│   ├── 🤖 agents/                        # 🎯 7 OPERATIONAL AI AGENTS
│   │   ├── 📋 AGENT_ARCHITECTURE_COMPLETE_ANALYSIS.md  # 📊 Master analysis
│   │   ├── 📋 AGENT_6_UPDATED_SYSTEM_KNOWLEDGE.md     # 🔧 Agent 6 context
│   │   │
│   │   ├── 💬 cia/                       # 🎯 Customer Interface Agent
│   │   │   ├── 📄 agent.py               # ⭐ Claude Opus 4 conversations
│   │   │   ├── 📄 mode_manager.py        # Conversation modes
│   │   │   ├── 📄 modification_handler.py # Bid card modifications
│   │   │   ├── 📄 prompts.py            # Conversation prompts
│   │   │   ├── 📄 state.py              # LangGraph state
│   │   │   └── 📋 README.md             # ✅ COMPLETE - CIA documentation
│   │   │
│   │   ├── 📊 jaa/                       # 🎯 Job Assessment Agent
│   │   │   ├── 📄 agent.py               # ⭐ Bid card generation
│   │   │   ├── 📄 workflow.py           # LangGraph workflow
│   │   │   ├── 📄 state.py              # State management
│   │   │   ├── 📄 prompts.py            # Data extraction prompts
│   │   │   └── 📋 README.md             # ✅ COMPLETE - JAA documentation
│   │   │
│   │   ├── 🔍 cda/                       # 🎯 Contractor Discovery Agent
│   │   │   ├── 📄 agent.py               # ⭐ PRIMARY - 3-tier discovery
│   │   │   ├── 📄 agent_v2.py           # ⚠️ NEEDS CONSOLIDATION
│   │   │   ├── 📄 agent_v2_optimized.py # ⚠️ NEEDS CONSOLIDATION
│   │   │   ├── 📄 scoring.py            # Contractor scoring
│   │   │   ├── 📄 web_search_agent.py   # Google Places integration
│   │   │   ├── 📄 tier1_matcher_v2.py   # Internal matching
│   │   │   ├── 📄 tier2_reengagement_v2.py # Re-engagement
│   │   │   ├── 📄 tier3_scraper.py      # External scraping
│   │   │   └── 📋 README.md             # ✅ COMPLETE - CDA documentation
│   │   │
│   │   ├── 📧 eaa/                       # 🎯 External Acquisition Agent
│   │   │   ├── 📄 agent.py               # ⭐ Multi-channel outreach
│   │   │   ├── 📁 message_templates/
│   │   │   │   └── 📄 template_engine.py # Dynamic messages
│   │   │   ├── 📁 outreach_channels/
│   │   │   │   ├── 📄 email_channel.py    # Traditional email
│   │   │   │   ├── 📄 mcp_email_channel_claude.py # ⭐ Claude emails
│   │   │   │   └── 📄 sms_channel.py      # SMS campaigns
│   │   │   ├── 📁 response_tracking/
│   │   │   │   └── 📄 response_parser.py  # Response analysis
│   │   │   └── 📋 README.md              # ✅ COMPLETE - EAA documentation
│   │   │
│   │   ├── 🌐 wfa/                       # 🎯 Website Form Automation
│   │   │   ├── 📄 agent.py               # ⭐ Playwright automation
│   │   │   └── 📋 README.md             # ✅ COMPLETE - WFA documentation
│   │   │
│   │   ├── 🎨 iris/                      # 🎯 Design Inspiration Assistant
│   │   │   ├── 📄 agent.py               # ⭐ Claude 3.7 Sonnet design
│   │   │   └── 📋 README.md             # ✅ COMPLETE - IRIS documentation
│   │   │
│   │   ├── 👷 coia/                      # 🎯 Contractor Interface Agent
│   │   │   ├── 📄 agent.py               # ⭐ PRIMARY - Onboarding
│   │   │   ├── 📄 research_based_agent.py # ⚠️ NEEDS CONSOLIDATION
│   │   │   ├── 📄 prompts.py            # Onboarding prompts
│   │   │   ├── 📄 state.py              # LangGraph state
│   │   │   └── 📋 README.md             # ✅ COMPLETE - COIA documentation
│   │   │
│   │   ├── 📁 cho/                       # ⚠️ EMPTY - Needs implementation
│   │   ├── 📁 cra/                       # ⚠️ EMPTY - Needs implementation
│   │   └── 📁 sma/                       # ⚠️ EMPTY - Needs implementation
│   │
│   ├── 💾 memory/                        # 🧠 Multi-Project Memory System
│   │   ├── 📄 multi_project_store.py    # Core memory operations
│   │   ├── 📄 langgraph_integration.py  # LangGraph integration
│   │   └── 📄 __init__.py               # Module initialization
│   │
│   ├── 🎭 orchestration/                # ⏰ Timing & Campaign Management
│   │   ├── 📄 timing_probability_engine.py # Mathematical calculations
│   │   ├── 📄 check_in_manager.py       # Campaign monitoring
│   │   ├── 📄 enhanced_campaign_orchestrator.py # Integration
│   │   └── 📄 __init__.py               # Module initialization
│   │
│   ├── 📊 admin/                        # 🎯 NEW - Admin Dashboard Backend
│   │   ├── 📄 monitoring_service.py     # ⭐ System health monitoring
│   │   ├── 📄 websocket_manager.py      # Real-time WebSocket updates
│   │   ├── 📄 auth_service.py           # Admin authentication
│   │   ├── 📄 database_watcher.py       # Database change monitoring
│   │   └── 📄 __init__.py               # Module initialization
│   │
│   ├── 🧪 test_*.py files               # 🔬 Agent testing files
│   │   ├── 📄 test_cia_claude_extraction.py # ✅ CIA testing
│   │   ├── 📄 test_actual_mcp_emails.py     # ✅ VERIFIED - Real emails
│   │   ├── 📄 test_direct_form_fill.py      # ✅ VERIFIED - Form automation
│   │   ├── 📄 test_complete_admin_system.py # ✅ Admin dashboard
│   │   ├── 📄 test_complete_system_validation.py # Integration testing
│   │   └── 📄 test_timing_system_complete.py    # Orchestration testing
│   │
│   └── 📁 additional files...           # Various utilities and configs
│
├── 🌐 web/                              # 🎯 FRONTEND - React + TypeScript
│   ├── 📄 package.json                 # Frontend dependencies
│   ├── 📄 vite.config.ts               # Vite configuration
│   ├── 📄 tailwind.config.js           # Tailwind CSS config
│   │
│   ├── 📁 src/
│   │   ├── 📄 main.tsx                  # React app entry point
│   │   ├── 📄 App.tsx                   # Main app component
│   │   │
│   │   ├── 📁 components/               # React components
│   │   │   ├── 📁 admin/                # 🎯 NEW - Admin Dashboard Components
│   │   │   │   ├── 📄 AdminLogin.tsx    # ⭐ Secure admin login
│   │   │   │   ├── 📄 MainDashboard.tsx # Central monitoring hub
│   │   │   │   ├── 📄 BidCardMonitor.tsx # Live bid tracking
│   │   │   │   ├── 📄 AgentStatusPanel.tsx # Agent health monitoring
│   │   │   │   ├── 📄 DatabaseViewer.tsx # Database operations
│   │   │   │   └── 📄 SystemMetrics.tsx  # Performance metrics
│   │   │   │
│   │   │   ├── 📁 chat/                 # CIA conversation components
│   │   │   ├── 📁 bidcards/            # JAA bid card components
│   │   │   ├── 📁 design/              # IRIS design components
│   │   │   └── 📁 contractor/          # COIA contractor components
│   │   │
│   │   ├── 📁 hooks/                    # React hooks
│   │   │   ├── 📄 useWebSocket.tsx      # WebSocket integration
│   │   │   ├── 📄 useAdminAuth.tsx      # Admin authentication
│   │   │   └── 📄 useApi.tsx            # API integration
│   │   │
│   │   ├── 📁 pages/                    # Page components
│   │   │   ├── 📄 HomePage.tsx          # Main landing page
│   │   │   ├── 📄 ChatPage.tsx          # CIA conversations
│   │   │   ├── 📄 DesignPage.tsx        # IRIS design boards
│   │   │   └── 📄 AdminPage.tsx         # Admin dashboard
│   │   │
│   │   └── 📁 utils/                    # Utility functions
│   │       ├── 📄 api.ts                # API client functions
│   │       ├── 📄 websocket.ts          # WebSocket utilities
│   │       └── 📄 auth.ts               # Authentication utilities
│   │
│   └── 📁 public/                       # Static assets
│       ├── 📄 index.html                # HTML template
│       └── 📁 assets/                   # Images, icons, etc.
│
├── 📚 docs/                             # 📋 Documentation
│   ├── 📄 agentic_coding.md            # Technical build details
│   ├── 📄 design.md                    # System design
│   ├── 📄 CURRENT_SYSTEM_STATUS.md     # Detailed component status
│   └── 📄 DATABASE_SCHEMA_DOCUMENTATION.md # Database schema
│
├── 🎯 agent_specifications/             # 🤖 Agent Development Guides
│   ├── 📄 CLAUDE_AGENT_1_FRONTEND_FLOW.md    # Agent 1 - Frontend
│   ├── 📄 CLAUDE_AGENT_2_BACKEND_CORE.md     # Agent 2 - Backend
│   ├── 📄 CLAUDE_AGENT_3_HOMEOWNER_UX.md     # Agent 3 - Homeowner UX
│   ├── 📄 CLAUDE_AGENT_4_CONTRACTOR_UX.md    # Agent 4 - Contractor UX
│   ├── 📄 CLAUDE_AGENT_5_MARKETING_GROWTH.md # Agent 5 - Marketing
│   ├── 📄 CLAUDE_AGENT_6_CODEBASE_QA.md      # Agent 6 - Quality Assurance
│   └── 📁 additional docs per agent/    # Supporting documentation
│
├── 🚀 additional_projects/             # 📈 Future expansion projects
│   ├── 📄 brand_ambassador_platform.md # Referral system
│   ├── 📄 social_media_automation.md   # Social presence
│   ├── 📄 influencer_partnership.md    # Influencer discovery
│   ├── 📄 property_manager_platform.md # B2B expansion
│   └── 📄 ai_education_platform.md     # Contractor education
│
├── 📱 mobile/                           # 📲 FUTURE - React Native
│   └── 📄 README.md                    # Mobile development plans
│
├── 🗄️ supabase/                        # 🗄️ Database schema and functions
│   ├── 📄 schema.sql                   # Database schema
│   └── 📁 functions/                   # Database functions
│
└── 📁 Additional Files
    ├── 📄 .env.example                 # Environment variables template
    ├── 📄 .gitignore                   # Git ignore rules
    ├── 📄 LICENSE                      # MIT license
    └── 📄 CONTRIBUTING.md              # Contribution guidelines
```

---

## 🎯 **CRITICAL FILES FOR ALL AGENTS**

### **📋 MUST-READ CONTEXT FILES**
1. **`CLAUDE.md`** - ⭐ MOST IMPORTANT - Build status, current system state
2. **`SYSTEM_INTERDEPENDENCY_MAP.md`** - Complete architecture and dependencies
3. **`README.md`** - Updated project overview and quick start
4. **`CODEBASE_OVERVIEW.md`** - This file, complete file structure

### **🤖 AGENT-SPECIFIC CONTEXT**
- **Your Agent Spec**: `agent_specifications/CLAUDE_AGENT_{N}*.md`
- **Agent README**: `ai-agents/agents/{agent_name}/README.md`
- **Implementation**: `ai-agents/agents/{agent_name}/agent.py`

### **🧪 TESTING & VALIDATION**
- **Your Agent Tests**: `ai-agents/test_{agent_name}*.py`
- **Integration Tests**: `ai-agents/test_complete_system_validation.py`
- **Admin System Test**: `ai-agents/test_complete_admin_system.py`

---

## 🔧 **FILE PURPOSES & RESPONSIBILITIES**

### **Backend Core (`ai-agents/`)**

#### **🎯 Server & Integration**
- **`main.py`** - FastAPI server, all agent endpoints, CORS configuration
- **`database_simple.py`** - Shared database operations, Supabase integration
- **`requirements.txt`** - Python dependencies for all agents

#### **🤖 Agent Implementations**
Each agent directory contains:
- **`agent.py`** - Main agent implementation (primary file)
- **`README.md`** - Complete documentation with examples and testing
- **Supporting files** - Prompts, state management, utilities

#### **💾 Shared Systems**
- **`memory/`** - Multi-project memory system (used by CIA)
- **`orchestration/`** - Timing and campaign management (used by all)
- **`admin/`** - Real-time monitoring backend (monitors all agents)

### **Frontend Core (`web/`)**

#### **📱 Application Structure** 
- **`src/main.tsx`** - Application entry point
- **`src/App.tsx`** - Main app component with routing
- **`package.json`** - Dependencies and build scripts

#### **🎨 Component Organization**
- **`src/components/admin/`** - Admin dashboard components (NEW)
- **`src/components/{feature}/`** - Feature-specific components
- **`src/hooks/`** - Reusable React hooks
- **`src/pages/`** - Page-level components

### **📚 Documentation Structure**

#### **📋 System Documentation**
- **`docs/`** - Technical documentation and system design
- **`agent_specifications/`** - Development guides for each agent role
- **Agent `README.md`** files - Implementation-specific documentation

#### **🎯 Development Guides**
- **Agent specifications** - Role-specific development instructions
- **System status docs** - Current build state and testing results
- **Architecture docs** - System design and interdependencies

---

## ⚠️ **QUALITY ISSUES & CLEANUP NEEDED**

### **🔴 HIGH PRIORITY - Duplicate Code**
1. **`ai-agents/agents/cda/`** - 3 versions of agent.py need consolidation
2. **`ai-agents/agents/coia/`** - 2 versions of agent.py need consolidation

### **🟡 MEDIUM PRIORITY - Empty Directories**
1. **`ai-agents/agents/cho/`** - Empty, needs implementation or removal
2. **`ai-agents/agents/cra/`** - Empty, needs implementation or removal
3. **`ai-agents/agents/sma/`** - Empty, needs implementation or removal

### **🟢 LOW PRIORITY - Documentation**
1. Missing comprehensive API documentation
2. No coding standards document
3. Test coverage analysis needed

---

## 🚀 **QUICK START FOR ANY AGENT**

### **🎯 Understanding Your Role**
1. **Read**: Your agent specification in `agent_specifications/`
2. **Context**: Read `CLAUDE.md` for current system state
3. **Architecture**: Review `SYSTEM_INTERDEPENDENCY_MAP.md`

### **💻 Development Setup**
```bash
# Backend (Required)
cd ai-agents && python main.py  # Port 8008

# Frontend (Optional, any port)
cd web && npm run dev          # Port 5173+

# Admin Dashboard
http://localhost:5173/admin/login  # admin@instabids.com / admin123
```

### **🧪 Testing Your Changes**
```bash
# Test specific agent
python test_{agent_name}*.py

# Test full system
python test_complete_system_validation.py

# Test admin dashboard
python test_complete_admin_system.py
```

### **📁 Finding Functionality**
- **Agent Logic**: `ai-agents/agents/{agent}/agent.py`
- **Database Ops**: Use `database_simple.py` functions
- **API Endpoints**: Check `main.py` for routes
- **Frontend Components**: `web/src/components/{feature}/`
- **Tests**: Look for `test_*.py` files

---

## 📊 **CURRENT SYSTEM STATUS**

### **✅ FULLY OPERATIONAL (Production Ready)**
- **7 Core Agents**: All tested with real-world functionality
- **Admin Dashboard**: Real-time monitoring with WebSocket updates
- **Email System**: Verified MCP integration with actual email sending
- **Form Automation**: Confirmed website form submissions
- **Database Integration**: 33+ Supabase tables with full CRUD
- **Multi-Project Memory**: Cross-project context and awareness

### **🔧 NEEDS ATTENTION**
- Duplicate agent implementations (CDA, COIA)
- Empty directories (CHO, CRA, SMA)
- Comprehensive integration testing
- Coding standards documentation

---

## 📞 **GETTING HELP**

### **📚 Documentation Priority**
1. **`CLAUDE.md`** - Current build status and instructions
2. **Your agent spec** - Role-specific development guide
3. **Agent README** - Implementation details and examples
4. **This file** - Complete codebase structure

### **🧪 Testing & Validation**
- Run relevant tests before making changes
- Use admin dashboard to monitor system health
- Check interdependency map for impact analysis

### **🎯 Quality Assurance**
- **Agent 6** maintains overall system quality
- Follow existing patterns and conventions
- Update documentation when making changes
- Test thoroughly before deploying

---

This codebase overview ensures all agents have complete context for working effectively within the InstaBids system. Keep this document updated as the system evolves.
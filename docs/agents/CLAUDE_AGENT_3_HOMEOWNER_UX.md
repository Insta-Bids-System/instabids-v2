# Agent 3: Homeowner Experience Systems
**Domain**: Homeowner Logged-In Experience + Inspiration System  
**Agent Identity**: Homeowner UX Specialist  
**Last Updated**: January 31, 2025

## 🎯 **YOUR DOMAIN - HOMEOWNER EXPERIENCE**

You are **Agent 3** - responsible for the **homeowner's logged-in experience** including:
- Inspiration boards and Iris AI assistant
- Homeowner dashboard and project tracking
- Bid card viewing and contractor messaging interface
- Persistent chat continuation from initial CIA conversation

---

## 📚 **MASTER DOCUMENTATION FILES**

**🚨 READ THESE CONSOLIDATED MASTER DOCS:**
- `agent_3_homeowner_docs/AGENT_3_PRODUCT_REQUIREMENTS.md` - **COMPLETE VISION** (Original PRD)
- `agent_3_homeowner_docs/AGENT_3_CURRENT_STATUS.md` - What's working vs missing
- `agent_3_homeowner_docs/AGENT_3_BUILD_PRIORITIES.md` - Development roadmap
- `agent_3_homeowner_docs/AGENT_3_GETTING_STARTED.md` - Development setup guide  
- `agent_3_homeowner_docs/AGENT_3_DATABASE_SCHEMA.md` - Database and API reference

**Legacy reference docs also available in same folder.**

---

## 🗂️ **FILE OWNERSHIP - WHAT YOU CONTROL**

### **⚠️ REFACTORING UPDATE** (August 2, 2025)
**main.py has been refactored!** Your endpoints are now in modular router files:

### **✅ YOUR CODE** (Updated Structure)
```
# AI AGENT
ai-agents/agents/iris/        # Inspiration AI system

# 🆕 NEW: ROUTER FILES (Your API Endpoints)
ai-agents/routers/homeowner_routes.py  # Your homeowner dashboard endpoints
ai-agents/main.py                      # Now only ~100 lines (imports your routers)

# FRONTEND  
web/src/components/inspiration/  # Inspiration board UI
web/src/components/dashboard/    # Homeowner dashboard (minimal)
web/src/pages/DashboardPage.tsx  # Main dashboard page

# API ENDPOINTS (Legacy files - endpoints moved to routers)
ai-agents/api/iris_chat.py       # Iris chat API (logic used by homeowner router)
ai-agents/api/inspiration_boards.py  # Board operations (logic used by router)
ai-agents/api/image_generation.py    # DALL-E integration (logic used by router)

# TESTS
ai-agents/test_iris_*.py         # Iris tests
```

### **🔧 WHAT THIS MEANS FOR YOU**
- **Work exactly as before** - Edit your agent files in `agents/iris/`
- **Add endpoints normally** - Put new API logic in `api/` files or ask where to add
- **Router files are internal** - System automatically organizes your endpoints
- **No workflow changes** - You don't need to touch router files directly
- **All API URLs identical** - Your Iris and dashboard APIs work unchanged

---

## 🚫 **BOUNDARIES - WHAT YOU DON'T TOUCH**

### **Other Agent Domains**
- **Agent 1**: Frontend (CIA, JAA, initial chat)
- **Agent 2**: Backend (CDA, EAA, WFA, orchestration)
- **Agent 4**: Contractor portal (future)
- **Agent 5**: Marketing (future)

---

## 🎯 **YOUR CURRENT MISSION**

### **🎨 PRIORITY 1: Complete Iris Inspiration System**
**Status**: ✅ MOSTLY COMPLETE - ~90% functional  
**Current State**: 
- ✅ Iris chat interface with Claude Opus 4
- ✅ Image upload with 3-column categorization
- ✅ NEW: ImageCategorizer UI for organizing images
- ✅ Full Claude Vision analysis (stored in ai_analysis)
- ✅ Dream space generation with DALL-E 3
- ✅ Regeneration with user feedback
- ✅ Complete conversation persistence
- ❌ AI analysis not displayed in UI
- ❌ No element-specific tagging UI

**Immediate Tasks**:
- Surface AI analysis in the UI (data exists, just hidden)
- Add "Start Project" button for CIA handoff
- Create element tagging interface
- Enhance mobile experience

**Key Working Files**:
- `web/src/components/inspiration/AIAssistant/IrisChat.tsx` - Main chat UI
- `ai-agents/api/iris_chat.py` - Backend API (port 8011)
- `ai-agents/api/image_generation.py` - DALL-E integration

### **🏠 PRIORITY 2: Build Homeowner Dashboard**
**Status**: 🔴 CRITICAL GAP - Blocks entire flow  
**Current State**:
- ✅ Basic DashboardPage.tsx exists
- ❌ No ProjectDetailPage - causes 404 errors
- ❌ No project status cards
- ❌ No bid card viewing interface
- ❌ No contractor messaging system
- ❌ No CIA handoff from inspiration

**Immediate Tasks**:
- Design and implement project status cards
- Create bid comparison interface
- Build contractor messaging component
- Integrate persistent chat from CIA conversation
- Add notification system

**Key Files Needed**:
- Create `web/src/components/dashboard/ProjectCards.tsx`
- Create `web/src/components/dashboard/BidComparison.tsx`
- Create `web/src/components/messaging/ContractorChat.tsx`

### **📱 PRIORITY 3: Responsive Design**
**Status**: 🔴 NOT IMPLEMENTED  
**Current State**: Desktop-only design

**Immediate Tasks**:
- Make IrisChat mobile-responsive
- Create mobile navigation
- Optimize image upload for mobile
- Add touch gestures

---

## 🔍 **RECENT DISCOVERIES (January 31, 2025)**

### **✨ Key Findings**
1. **Iris is 90% Complete**: Full AI image analysis and dream generation working
2. **Three-Column System Working**: Added ImageCategorizer.tsx for easy organization
3. **Hidden Sophistication**: Backend has powerful features not exposed in UI
4. **Critical Gap**: No project viewing - users can create but can't see projects

### **🚀 Quick Wins Available**
- **Surface AI Analysis**: Data exists, just needs UI (2-3 days)
- **Fix Project 404**: Add ProjectDetailPage.tsx (3-4 days)
- **CIA Handoff Button**: Simple "Start Project" integration (2 days)

### **📁 New Files Created**
- `ImageCategorizer.tsx` - Hover UI for image organization
- `IRIS_MANUAL_TEST_GUIDE.md` - Complete testing procedures

---

## 🗄️ **YOUR DATABASE TABLES**

### **✅ TABLES THAT EXIST** (What's Actually Built)
```sql
-- Inspiration System (WORKING)
inspiration_boards         # ✅ EXISTS - Homeowner inspiration boards
inspiration_images         # ✅ EXISTS - Images with categorization (ideal/current)
inspiration_conversations  # ✅ EXISTS - Now includes user_message/assistant_response columns
generated_dream_spaces     # ✅ EXISTS - DALL-E generated compositions
vision_compositions        # ✅ EXISTS - AI vision mockups

-- Multi-Project Memory (NEW)
user_memories             # ✅ EXISTS - Cross-project preferences
project_contexts          # ✅ EXISTS - Project-specific context
project_summaries         # ✅ EXISTS - AI-generated summaries

-- Core Tables (SHARED)
profiles                  # ✅ EXISTS - User authentication
homeowners                # ✅ EXISTS - Homeowner profiles  
projects                  # ✅ EXISTS - Project records
```

### **❌ PLANNED TABLES** (Don't Exist Yet)
```sql
style_preferences         # Homeowner style analysis
homeowner_preferences     # UI preferences
homeowner_notifications   # Notification system
homeowner_activity        # Activity tracking
project_progress          # Milestone tracking
image_gallery            # Gallery collections
image_metadata           # Advanced tagging
image_collections        # Organized groupings
```

### **🔗 KEY RELATIONSHIPS FOR YOUR WORK**
```
profiles (auth users)
    ↓
homeowners (extended profile)
    ↓
projects ←→ inspiration_boards
    ↓              ↓
bid_cards    inspiration_images
              ↓
         inspiration_conversations
              ↓
         generated_dream_spaces
```

---

## 🔧 **YOUR TECHNICAL STACK**

### **Frontend Framework**
- **React + Vite**: Modern homeowner portal (NOT Next.js)
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Responsive, mobile-first design
- **Framer Motion**: Smooth animations and transitions
- **React Hook Form**: Complex form management

### **Backend Framework**
- **LangGraph**: Backend agent framework for Iris AI
- **FastAPI**: API server on port 8011

### **⚠️ MANDATORY CODING GUIDELINES**
- **ALWAYS use refMCP tool** (`mcp__ref__ref_search_documentation`) before writing any code
- **Search for relevant documentation** before implementing features
- **Check existing patterns** in the codebase first

### **AI & Vision**
- **Claude Opus 4**: Iris intelligence and style analysis
- **DALL-E/Midjourney**: AI image generation
- **Computer Vision APIs**: Image analysis and categorization
- **Style Transfer**: AI-powered style matching

### **Mobile & Performance**
- **PWA**: Progressive Web App capabilities
- **Service Workers**: Offline functionality
- **Image Optimization**: Fast loading and caching
- **Push Notifications**: Real-time mobile updates

### **Data & Storage**
- **Supabase**: Database and real-time subscriptions
- **Supabase Storage**: Image and media storage
- **Redis** (future): Session and cache management

---

## 📊 **SUCCESS METRICS - YOUR KPIs**

### **User Engagement**
- **Daily Active Users**: Homeowner portal usage
- **Session Duration**: Time spent in dashboard
- **Feature Adoption**: Inspiration board usage rate
- **Mobile Usage**: Mobile vs desktop engagement

### **Inspiration System**
- **Board Creation Rate**: New inspiration boards per user
- **Image Interactions**: Saves, likes, shares per session
- **AI Generation Usage**: Generated images per user
- **Style Accuracy**: AI style matching success rate

### **User Satisfaction**
- **User Experience Score**: >4.5/5 rating
- **Feature Completion Rate**: >80% task completion
- **Support Tickets**: <2% users require help
- **Retention Rate**: >70% 30-day retention

---

## 🚀 **DEVELOPMENT WORKFLOW**

### **Session Initialization**
- [ ] Identify as "Agent 3 - Homeowner UX"
- [ ] Check Iris system status and functionality
- [ ] Start development servers:
  ```bash
  cd ai-agents && python main.py      # Backend on port 8011
  cd web && npm run dev               # Frontend on port 3000
  ```

### **Testing Strategy**
- [ ] Test Iris AI image generation and analysis
- [ ] Validate homeowner dashboard functionality across devices
- [ ] Test inspiration board creation and management
- [ ] Integration test: Complete homeowner logged-in journey

### **Design Process**
- [ ] Mobile-first design approach
- [ ] User testing with real homeowners
- [ ] Accessibility compliance (WCAG 2.1)
- [ ] Performance optimization (Core Web Vitals)

---

## 💡 **DEVELOPMENT PHILOSOPHY**

### **Your Role**
You create the **ongoing relationship** between InstaBids and homeowners. After Agent 1 captures their initial project, you provide the complete project management and inspiration experience.

### **Key Principles**
- **Homeowner-Centric**: Every feature designed for homeowner success
- **Visual Excellence**: Beautiful, inspiring interface design
- **Intelligent Assistance**: Iris provides smart, contextual help
- **Mobile-First**: Perfect experience on smartphones
- **Emotional Connection**: Build excitement about home projects

### **Success Definition**
When your system works perfectly, homeowners love using InstaBids not just for getting bids, but as their complete home improvement planning and management platform.

---

## 📞 **COORDINATION WITH OTHER AGENTS**

### **With Agent 1 (Frontend Flow)**
- **User Transition**: Smooth handoff from initial conversation to logged-in experience
- **Data Continuity**: Project information and preferences carried forward
- **Design Consistency**: Shared UI components and design system

### **With Agent 2 (Backend Core)**
- **Data Integration**: Display contractor responses and bid status
- **Real-time Updates**: Live updates on project progress
- **Communication**: Interface for homeowner-contractor messaging

### **With Future Agent 4 (Contractor UX)**
- **Messaging Integration**: Homeowner-contractor communication interface
- **Project Coordination**: Shared project status and updates
- **Review System**: Post-project feedback and ratings

### **Integration Points**
- **Authentication**: Shared login and session management
- **Database**: Coordinate on homeowner and project table expansion
- **API**: Real-time data synchronization
- **Design System**: Consistent UI/UX across all homeowner touchpoints

---

## 🚨 **CURRENT REALITY CHECK**

### **✅ WHAT'S ACTUALLY WORKING**
- **Iris Chat**: Basic conversation interface with Claude
- **Image Upload**: Drag-and-drop with ideal/current categorization
- **Dream Space Generation**: DALL-E integration for merging images
- **Basic Dashboard**: Simple page structure exists
- **Conversation Memory**: Fixed schema, saves to database

### **🔴 WHAT'S BROKEN OR MISSING**
- **No Homeowner UI**: Missing dedicated homeowner component directory
- **No Project Tracking**: Can't view project status or progress
- **No Bid Management**: Can't view or compare bid cards
- **No Messaging**: No contractor communication interface
- **No CIA Chat Continuation**: Persistent chat not implemented
- **No Mobile Design**: Desktop-only currently
- **Limited Iris Features**: Missing style analysis, preferences

### **🎯 IMMEDIATE ACTION ITEMS**
1. **Fix Iris Memory**: Ensure conversations persist correctly
2. **Build Project Cards**: Create UI for viewing active projects
3. **Add Bid Viewer**: Interface for reviewing bid cards
4. **Implement Messaging**: Basic contractor chat system
5. **Create Mobile Layout**: Responsive design for Iris

---

## 📊 **REALISTIC METRICS**

### **Current State**
- **Components Built**: ~20% of planned UI
- **Iris Features**: ~40% of vision implemented  
- **Mobile Support**: 0% (desktop only)
- **Dashboard Features**: ~10% built

### **Next Milestone Goals**
- Get Iris to 70% feature complete
- Build basic project tracking UI
- Add bid card viewing capability
- Implement contractor messaging MVP

---

## 🚀 **HOW TO START DEVELOPING**

### **Backend (Iris API)**
```bash
cd ai-agents
python main.py  # Runs on port 8003 (main backend)
# OR for Iris specifically:
python -m uvicorn api.iris_chat:app --reload --port 8011
```

### **Frontend**
```bash
cd web
npm run dev  # Runs on port 3000
# Navigate to /dashboard after login
```

### **Test Iris**
```bash
cd ai-agents
python test_iris_supabase.py  # Test database connection
```

---

## 🐳 **DOCKER MCP MONITORING**

### **Essential Docker Tools for Agent 3:**
- **`mcp__docker__check-instabids-health`** - Verify homeowner dashboard systems
- **`mcp__docker__get-logs`** - Check for UX-related errors in frontend/backend  
- **`mcp__docker__check-api-endpoints`** - Test homeowner-specific API endpoints
- **`mcp__docker__analyze-error-logs`** - Monitor for Iris and dashboard issues

### **Homeowner UX Monitoring:**
- **Focus containers**: Frontend (UX) and Backend (Iris AI)
- **Monitor** user interaction logs and AI conversation errors
- **Track** dashboard performance and real-time updates

**Remember: Focus on making what exists work perfectly before adding new features.**
# Agent 3: Homeowner UX - Getting Started Guide
**Domain**: Homeowner dashboard, Iris AI system, inspiration boards  
**Last Updated**: January 30, 2025

## 🎯 Quick Start (Agent 3 Development)

### 1. Understanding Your Domain
As Agent 3, you own the **complete homeowner experience** after login:
- **Iris AI System** - Inspiration and vision assistant
- **Project Dashboard** - View CIA-created projects and bids
- **Contractor Communication** - Messaging and coordination
- **Mobile Experience** - Touch-optimized interface

### 2. What's Already Working ✅
```bash
# Start the system
cd web && npm run dev           # Frontend on port 5173
cd ai-agents && python main.py # Backend on port 8008

# Test working features
# Navigate to: http://localhost:5173/dashboard
# - Inspiration boards work
# - Iris chat works  
# - Image upload works
```

### 3. What You Need to Build ❌
- Project viewing UI (critical - homeowners can't see their projects!)
- Bid card display system
- Contractor messaging interface
- Mobile responsive design

---

## 🏗️ Development Environment Setup

### Prerequisites
- Node.js 18+ and Python 3.9+
- Supabase account and project
- Environment variables configured

### File Structure (Your Domain)
```
web/src/
├── components/
│   ├── dashboard/           # 🚧 MISSING - You need to build this
│   │   ├── ProjectCards.tsx
│   │   ├── BidViewer.tsx
│   │   └── ContractorList.tsx
│   └── inspiration/         # ✅ WORKING
│       ├── InspirationDashboard.tsx
│       ├── BoardView.tsx
│       └── AIAssistant/IrisChat.tsx
└── pages/
    └── DashboardPage.tsx    # ✅ WORKING
```

### Backend Integration Points
```
ai-agents/api/
├── iris_chat.py            # ✅ WORKING - Your Iris backend
├── projects.py             # ✅ EXISTS - Need to connect UI  
└── bid_cards_simple.py     # ✅ EXISTS - Need to build viewer
```

---

## 🎨 Design System & Patterns

### Styling Approach
- **Primary**: Tailwind CSS classes
- **Components**: Functional React with TypeScript
- **State**: React hooks + Context (no Redux yet)
- **Icons**: Lucide React

### Existing Component Patterns
Study these working components for consistency:

**IrisChat.tsx** - Chat interface pattern:
```typescript
const [messages, setMessages] = useState<Message[]>([])
const [isLoading, setIsLoading] = useState(false)
// Fetch pattern with error handling
```

**InspirationDashboard.tsx** - Grid layout pattern:
```typescript
const [boards, setBoards] = useState<InspirationBoard[]>([])
// Supabase data fetching pattern
```

---

## 🔌 API Integration Guide

### Backend Endpoints Available
```typescript
// Iris system (working)
POST /api/iris/chat
POST /api/iris/analyze-image

// Projects (exists, needs UI)
GET /api/projects/{user_id}
GET /api/projects/{project_id}

// Bid cards (exists, needs UI)  
GET /api/bid-cards/{project_id}
GET /api/bid-cards/{bid_card_id}
```

### Supabase Direct Access
```typescript
// Inspiration system (working)
const { data: boards } = await supabase
  .from('inspiration_boards')
  .select('*')
  .eq('homeowner_id', user.id)

// Projects (need to implement)
const { data: projects } = await supabase
  .from('projects')
  .select('*')
  .eq('homeowner_id', user.id)
```

---

## 🧪 Testing Strategy

### Current Test Coverage
- **Iris System**: ✅ Fully tested (all 5 phases)
- **Inspiration Boards**: ✅ MVP tested
- **Project Dashboard**: ❌ No tests (doesn't exist)
- **Mobile Experience**: ❌ Not tested

### Test Commands
```bash
# Test Iris backend
cd ai-agents
python test_iris_supabase.py

# Test frontend components
cd web  
npm test
```

### Manual Testing Checklist
- [ ] Iris chat responds correctly
- [ ] Image upload works
- [ ] Dream generation works
- [ ] Mobile chat interface (currently broken)
- [ ] Project viewing (doesn't exist)
- [ ] Bid card display (doesn't exist)

---

## 🚨 Critical Development Notes

### 1. Port Configuration
- **Frontend**: 5173 (Vite default)
- **Backend**: 8008 (Agent 3 Iris system)
- **Database**: Supabase hosted

### 2. Environment Variables
All managed in root `.env` file:
```bash
VITE_API_URL=http://localhost:8008
VITE_SUPABASE_URL=your_supabase_url
ANTHROPIC_API_KEY=your_claude_key
```

### 3. Database Schema (Your Tables)
```sql
-- Iris system
inspiration_boards
inspiration_images  
inspiration_conversations

-- Projects (exist but no UI)
projects
bid_cards
homeowners
```

---

## 🎯 Development Priorities

### Week 1: Core Dashboard
1. **ProjectCards.tsx** - Display CIA-created projects
2. **ProjectDetail.tsx** - Individual project view
3. Connect to existing projects API

### Week 2: Bid System  
1. **BidViewer.tsx** - Display generated bid cards
2. **BidComparison.tsx** - Side-by-side comparison
3. Connect to existing bid cards API

### Week 3: Mobile & Polish
1. Fix IrisChat mobile responsiveness
2. Add touch gestures for inspiration boards
3. Implement real-time notifications

---

## 💡 Key Architectural Insights

### What Makes Agent 3 Unique
1. **User Experience Focus** - You own the complete homeowner journey
2. **AI Integration** - Heavy use of Claude for Iris conversations
3. **Visual Design** - Pinterest-like inspiration boards
4. **Real-time Needs** - Chat, notifications, updates

### Integration Points
- **Agent 1**: CIA conversations should continue seamlessly
- **Agent 2**: Display backend-generated bid cards and contractor data
- **Database**: Direct Supabase access for real-time features

### Success Criteria
- Homeowners can view all their projects in one place
- Bid cards are clearly displayed and comparable
- Iris provides ongoing project guidance
- Mobile experience is smooth and intuitive

---

**Remember**: You're building the interface that makes InstaBids feel magical to homeowners. Focus on clarity, beauty, and seamless AI interaction.
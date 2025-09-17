# Frontend Pages Active Mapping
**Last Updated**: January 8, 2025  
**Purpose**: Document all ACTIVE frontend pages and their connections in the InstaBids platform

## 🎯 ACTIVE PAGES ONLY - CURRENTLY IN USE

### 📍 **CORE NAVIGATION FLOW**

```
HomePage (/)
    ├── LoginPage (/login)
    │   ├── → DashboardPage (/dashboard) [homeowner]
    │   └── → ContractorDashboardPage (/contractor/dashboard) [contractor]
    ├── SignupPage (/signup)
    ├── ContractorLandingPage (/contractor)
    │   └── → ContractorDashboardPage (/contractor/dashboard)
    └── AdminLoginPage (/admin/login)
        └── → AdminDashboardPage (/admin/dashboard)
```

---

## 📄 **ACTIVE PAGE INVENTORY**

### **1. HomePage.tsx** (`/`)
- **Purpose**: Main landing page for homeowners
- **Key Features**:
  - **UltimateCIAChat** component (NEW - consolidated from 4 versions)
  - Navigation buttons: Login (Homeowner/Contractor), Admin
  - Messaging Agent test button (red border)
  - Social proof testimonials
- **Chat Component**: `UltimateCIAChat` with:
  - WebRTC voice chat
  - Phase tracking (intro → discovery → details → photos → review)
  - Data extraction sidebar
  - Adaptive personality (5 modes)
  - Bid card display capability
- **Navigation**:
  - Homeowner → `/login`
  - Contractor → `/contractor`
  - Admin → `/admin/login`
  - Messaging Test → `/intelligent-messaging-test`

### **2. LoginPage.tsx** (`/login`)
- **Purpose**: Unified login for all user types
- **Key Features**:
  - Email/password login
  - Demo Homeowner button
  - Demo Contractor button
  - Remember me checkbox
- **Smart Routing**:
  - Detects role from localStorage/profile
  - Homeowner → `/dashboard`
  - Contractor → `/contractor/dashboard`

### **3. SignupPage.tsx** (`/signup`)
- **Purpose**: New user registration
- **Key Features**:
  - Role selection (homeowner/contractor)
  - Google OAuth integration
  - Email/password signup
  - Project info pre-fill from CIA chat
- **Components**: Uses `AccountSignupModal` logic
- **Navigation**: After signup → role-appropriate dashboard

### **4. DashboardPage.tsx** (`/dashboard`)
- **Purpose**: Homeowner main dashboard
- **Protected**: Requires homeowner role
- **Key Components**:
  - **ActiveProjects** - Current project cards
  - **RecentBids** - Latest contractor submissions
  - **InspirationBoards** - Design inspiration gallery
  - **IrisChat** integration (Agent 3's AI design assistant)
- **Tabs Structure**:
  - Overview (default)
  - Projects
  - Inspiration (with Iris)
  - Messages
  - Settings
- **Navigation**: 
  - Projects → `/projects/:id`
  - Bid Cards → `/bid-cards/:id`

### **5. ProjectDetailPage.tsx** (`/projects/:id`)
- **Purpose**: Individual project management for homeowners
- **Protected**: Requires homeowner role
- **Key Features**:
  - Project timeline
  - Contractor bid comparison
  - **MessagingInterface** component
  - Document attachments
  - Budget tracking
- **Components**:
  - `BidCardDisplay`
  - `ContractorBidList`
  - `ProjectTimeline`
  - `ProjectBudgetTracker`

### **6. ContractorLandingPage.tsx** (`/contractor`)
- **Purpose**: Contractor entry point (DUAL PURPOSE)
- **Public Access**: No auth required
- **Key Features**:
  - **ContractorOnboardingChat** (COIA) for new contractors
  - "Login as Existing Contractor" button
  - Handles bid card email arrivals with URL params
  - Auto-fills COIA with campaign data if arriving from email
- **URL Params**: `?contractor=Name&msg_id=123&campaign=456`
- **Navigation**:
  - Login → `/contractor/dashboard`
  - After COIA signup → Create account flow

### **7. ContractorDashboardPage.tsx** (`/contractor/dashboard`)
- **Purpose**: Full contractor portal
- **Protected**: Requires contractor role
- **Tab Components**:
  1. **My Projects** (`ContractorProjects`)
     - Active bids
     - Won projects
     - Project timeline
  2. **Bid Marketplace** (`BidCardMarketplace`)
     - Available bid cards
     - Filtering by trade/location/budget
     - Quick bid submission
  3. **My Profile** (`ContractorProfile`)
     - Company info
     - Certifications
     - Portfolio
  4. **Chat** (COIA support)
  5. **Notifications**
- **Key Components**:
  - `BidCardMarketplace` - Browse and bid on projects
  - `ContractorBidCard` - Submit detailed proposals
  - `ContractorProposalForm` - Structured bid submission

### **8. AdminDashboardPage.tsx** (`/admin/dashboard`)
- **Purpose**: System administration
- **Protected**: Admin auth (separate system)
- **Real-time Features**:
  - WebSocket live updates
  - Agent health monitoring
  - Database change feeds
- **Sections**:
  - **System Overview** - Live metrics
  - **Bid Cards** - All 86+ real bid cards from database
  - **Contractors** - 109 contractors (9 Tier 1, 100 Tier 3)
  - **Campaigns** - Outreach management
  - **Agent Status** - All 7 agents health
  - **Database Ops** - Live table monitoring
- **Components**:
  - `AdminMetrics`
  - `BidCardManagement`
  - `ContractorManagement`
  - `AgentHealthMonitor`

### **9. IntelligentMessagingTest.tsx** (`/intelligent-messaging-test`)
- **Purpose**: GPT-4o messaging system testing
- **Features**:
  - Test scope change detection
  - Contact info filtering
  - Homeowner-only questions
  - Real-time message analysis
- **Components**: `MessagingInterface` with GPT-4o integration

### **10. InspirationDashboard.tsx** (Component in Dashboard)
- **Purpose**: Iris Agent's design inspiration system
- **Key Features**:
  - Mood board creation
  - AI vision generation
  - Style exploration
  - **IrisChat** - AI design assistant
- **Components**:
  - `InspirationBoard`
  - `IrisChat` (Agent 3's component)
  - `VisionGenerator`
  - `StyleExplorer`

### **11. HomeownerProjectWorkspaceFixed.tsx** (`/bid-cards/:id`)
- **Purpose**: Detailed bid card workspace
- **Features**:
  - Full bid card details
  - Contractor bid comparison
  - Messaging with contractors
  - Award project functionality
- **Components**:
  - `BidCardDetail`
  - `ContractorBidComparison`
  - `ProjectMessaging`

### **12. AuthCallbackPage.tsx** (`/auth/callback`)
- **Purpose**: OAuth callback handler
- **System Page**: Handles Supabase auth redirects
- **Navigation**: Auto-redirects based on auth result

---

## 🧩 **KEY COMPONENT ARCHITECTURE**

### **Chat Components (Active)**
1. **UltimateCIAChat** (NEW - Homeowner)
   - Consolidated from 4 versions
   - WebRTC voice, phase tracking, personality system
   - Location: `components/chat/UltimateCIAChat.tsx`

2. **ContractorOnboardingChat** (COIA - Contractor)
   - Contractor discovery and onboarding
   - Location: `components/contractor/ContractorOnboardingChat.tsx`

3. **IrisChat** (Design Assistant)
   - Agent 3's inspiration AI
   - Location: `components/inspiration/IrisChat.tsx`

### **Bid Card Components**
- `BidCardMarketplace` - Browse available projects
- `ContractorBidCard` - Contractor bid submission
- `HomeownerBidCard` - Homeowner bid management
- `BidCardDetail` - Full bid card view
- `ChatBidCardAttachment` - Display bid cards in chat

### **Messaging Components**
- `MessagingInterface` - Main messaging UI
- `MessageThread` - Individual conversation
- `MessageFilters` - Content filtering system
- `ContractorAliasing` - Name obfuscation

### **Archived Chat Components** (in `chat/archive/`)
- CIAChat.tsx (basic version)
- UltraInteractiveCIAChat.tsx (WebRTC version)
- DynamicCIAChat.tsx (phase tracking version)
- RealtimeCIAChat.tsx (personality version)

---

## 🗂️ **PAGES TO REMOVE/ARCHIVE**

### **Test Pages Still in Routes** (Should be removed from App.tsx):
- None currently - all test pages already removed from routing

### **Test Pages in File System** (Should be archived):
```
pages/
├── CIATestPage.tsx → archive
├── ChatPage.tsx → archive
├── TestPage.tsx → archive
├── WebRTCTestPage.tsx → archive
├── BidCardTest.tsx → archive
├── TestCommunicationPage.tsx → archive
├── TestMessaging.tsx → archive
├── ExternalBidCardDemo.tsx → archive
├── ExternalBidCardLanding.tsx → archive
├── InspirationDemo.tsx → archive
├── BackyardImageViewer.tsx → archive
```

---

## 🔀 **CURRENT ROUTING CONFIGURATION**

### **App.tsx Routes** (As of Jan 8, 2025):
```jsx
<Routes>
  {/* Public Routes */}
  <Route path="/" element={<HomePage />} />
  <Route path="/login" element={<LoginPage />} />
  <Route path="/signup" element={<SignupPage />} />
  <Route path="/contractor" element={<ContractorLandingPage />} />
  <Route path="/auth/callback" element={<AuthCallbackPage />} />
  <Route path="/intelligent-messaging-test" element={<IntelligentMessagingTest />} />
  
  {/* Protected Homeowner Routes */}
  <Route path="/dashboard" element={
    <ProtectedRoute requiredRole="homeowner">
      <DashboardPage />
    </ProtectedRoute>
  } />
  <Route path="/projects/:id" element={
    <ProtectedRoute requiredRole="homeowner">
      <ProjectDetailPage />
    </ProtectedRoute>
  } />
  <Route path="/bid-cards/:id" element={
    <ProtectedRoute requiredRole="homeowner">
      <HomeownerProjectWorkspaceFixed />
    </ProtectedRoute>
  } />
  
  {/* Protected Contractor Routes */}
  <Route path="/contractor/dashboard" element={
    <ProtectedRoute requiredRole="contractor">
      <BidCardProvider>
        <ContractorDashboardPage />
      </BidCardProvider>
    </ProtectedRoute>
  } />
  
  {/* Admin Routes (separate auth) */}
  <Route path="/admin/*" element={
    <AdminAuthProvider>
      <Routes>
        <Route path="login" element={<AdminLoginPage />} />
        <Route path="dashboard" element={<AdminDashboardPage />} />
      </Routes>
    </AdminAuthProvider>
  } />
  
  {/* Catch-all redirect */}
  <Route path="*" element={<Navigate to="/" replace />} />
</Routes>
```

---

## 🔐 **AUTHENTICATION SYSTEMS**

### **Main Auth (AuthContext.tsx)**:
- Manages homeowner/contractor authentication
- Uses Supabase auth (mocked for development)
- Role-based routing
- Session persistence via localStorage

### **Admin Auth (AdminAuthProvider.tsx)**:
- Separate authentication for admin panel
- Session-based auth
- Not connected to main user system

### **Protected Routes**:
- `ProtectedRoute` component with `requiredRole` prop
- Redirects unauthorized users to login
- Preserves intended destination after login

---

## 🎯 **CURRENT USER FLOWS**

### **Homeowner Flow**:
```
Homepage (UltimateCIAChat) → Describe Project → Sign Up Trigger → 
Dashboard → Create Bid Card → View Bids → Select Contractor → 
Project Workspace → Messaging → Project Completion
```

### **Contractor Flow**:
```
Email Link → Contractor Landing (with params) → COIA Chat → 
Sign Up → Dashboard → Browse Marketplace → Submit Bid → 
Win Project → Project Messaging → Complete Work
```

### **Admin Flow**:
```
Admin Login → Dashboard → Monitor Systems → Manage Bid Cards → 
Track Campaigns → View Agent Health → Database Operations
```

---

## 📊 **COMPONENT HIERARCHY**

### **HomePage Component Tree**:
```
HomePage
└── UltimateCIAChat
    ├── AccountSignupModal
    ├── ChatBidCardAttachment
    ├── OpenAIRealtimeWebRTC (voice)
    └── Phase Progress System
```

### **Dashboard Component Tree**:
```
DashboardPage
├── ActiveProjects
│   └── ProjectCard
├── RecentBids
│   └── BidCard
├── InspirationDashboard
│   ├── InspirationBoard
│   └── IrisChat
└── MessagingInterface
    └── MessageThread
```

### **Contractor Dashboard Tree**:
```
ContractorDashboardPage
├── ContractorProjects
│   └── ProjectList
├── BidCardMarketplace
│   ├── BidCardFilter
│   └── BidCardGrid
├── ContractorProfile
│   └── ProfileEditor
└── ContractorOnboardingChat
```

---

## 🚀 **RECENT CHANGES** (Jan 8, 2025)

1. **CIA Consolidation**: 4 chat components → 1 UltimateCIAChat
2. **Removed Contractor Detection**: Separate landing pages now
3. **Archives Created**: Old CIA versions moved to `chat/archive/`
4. **Admin Dashboard**: Real data only (no mock data)
5. **Messaging System**: GPT-4o intelligent filtering active

---

## 📝 **NOTES FOR DEVELOPERS**

1. **UltimateCIAChat is the ONLY homeowner chat** - 850 lines, all features
2. **ContractorLandingPage handles BOTH** clean arrival and bid card emails
3. **IrisChat is Agent 3's component** for design inspiration
4. **Admin Dashboard shows REAL DATA** - 86 bid cards, 109 contractors
5. **Test pages should be archived** - not in active routes
6. **GPT-4o powers messaging** - scope change detection active

---

## 🎨 **UI/UX STANDARDS**

### **Design System**:
- **Framework**: Tailwind CSS (no custom CSS)
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Chat UI**: Custom components (not ChatScope anymore)
- **Colors**: Blue-600 primary, Purple-600 accent

### **Component Patterns**:
- Tabs for multi-section pages
- Modals for forms/confirmations  
- Sidebars for data/filters
- Cards for content blocks
- Real-time updates via WebSocket

---

This document represents the COMPLETE, ACTIVE frontend architecture including all recent consolidations and Agent 3's Iris components as of January 8, 2025.
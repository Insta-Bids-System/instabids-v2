# Agent 3: UI Component Map
**Purpose**: Complete inventory of actual UI components in my domain  
**Last Updated**: January 30, 2025  
**Status**: Reality-based documentation

## 🗺️ **COMPONENT HIERARCHY**

### **📁 Inspiration System Components** (My Core Domain)
```
web/src/components/inspiration/
├── InspirationDashboard.tsx      # ✅ Main dashboard container
│   └── Features:
│       - Board grid display
│       - Create new board button
│       - Basic board management
│
├── AIAssistant/
│   └── IrisChat.tsx              # ✅ WORKING - Iris chat interface
│       └── Features:
│           - Real-time chat with Claude
│           - Image upload with categorization
│           - Dream space generation
│           - Conversation suggestions
│           - Mobile: ❌ Not responsive
│
├── ImageUploader/                # ✅ COMPLETE upload system
│   ├── index.tsx                 # Export wrapper
│   ├── ImageUploader.tsx         # Main upload logic
│   │   └── Features:
│   │       - Multi-file selection
│   │       - Drag and drop
│   │       - Upload progress
│   │       - Supabase storage integration
│   └── DragDropZone.tsx          # Drag/drop UI
│       └── Features:
│           - Visual feedback
│           - File type validation
│           - Preview generation
│
├── BoardCreator.tsx              # ✅ Board creation modal
│   └── Features:
│       - Title/description input
│       - Room type selection
│       - Create board API call
│
└── BoardView.tsx                 # ✅ Individual board viewer
    └── Features:
        - Image grid display
        - Basic image management
        - Iris chat integration
```

### **📁 Dashboard Components** (Minimal)
```
web/src/components/dashboard/
└── (Currently empty)             # ❌ No components built

NEEDED:
- ProjectCards.tsx                # Display active projects
- BidCardViewer.tsx              # View bid cards
- ContractorList.tsx             # Active contractors
- NotificationCenter.tsx         # Updates and alerts
```

### **📁 Pages** (Entry Points)
```
web/src/pages/
├── DashboardPage.tsx            # ✅ Basic homeowner dashboard
│   └── Current Implementation:
│       - Simple layout wrapper
│       - Links to inspiration boards
│       - Missing: Project tracking, bid management
│
├── HomePage.tsx                 # ✅ Landing page
│   └── Features:
│       - Hero section
│       - Inspiration preview
│       - Login/signup CTAs
│
└── (Other pages not in my domain)
```

### **📁 Shared Components I Use**
```
web/src/components/
├── auth/
│   └── ProtectedRoute.tsx       # ✅ Route protection
│
├── ui/
│   └── LoadingSpinner.tsx       # ✅ Loading states
│
└── common/
    └── Button.tsx               # ✅ Reusable button
```

## 🔴 **CRITICAL MISSING COMPONENTS**

### **1. Persistent Chat System**
**Need**: Continue CIA conversation after login
```tsx
// MISSING: components/chat/PersistentChat.tsx
interface PersistentChatProps {
  conversationId: string;  // From CIA initial chat
  homeownerId: string;
  onNewProject?: () => void;
}
```

### **2. Project Tracking UI**
**Need**: View project status and progress
```tsx
// MISSING: components/dashboard/ProjectTracker.tsx
interface ProjectTrackerProps {
  projects: Project[];
  onSelectProject: (id: string) => void;
  onViewBids: (projectId: string) => void;
}
```

### **3. Bid Card Viewer**
**Need**: Review and compare bid cards
```tsx
// MISSING: components/bids/BidCardDisplay.tsx
interface BidCardDisplayProps {
  bidCard: BidCard;
  contractors: ContractorResponse[];
  onSelectContractor: (id: string) => void;
}
```

### **4. Contractor Messaging**
**Need**: Chat with contractors
```tsx
// MISSING: components/messaging/ContractorChat.tsx
interface ContractorChatProps {
  contractorId: string;
  projectId: string;
  bidCardId: string;
}
```

## 📱 **MOBILE RESPONSIVENESS STATUS**

| Component | Desktop | Mobile | Tablet |
|-----------|---------|--------|--------|
| IrisChat | ✅ Works | ❌ Broken | ❌ Untested |
| InspirationDashboard | ✅ Works | ❌ Poor | ❌ Untested |
| ImageUploader | ✅ Works | ⚠️ Difficult | ❌ Untested |
| BoardView | ✅ Works | ❌ Broken | ❌ Untested |

## 🎨 **STYLING APPROACH**

### **Current Implementation**
- **Tailwind CSS**: Primary styling system
- **Inline styles**: Heavy usage (needs refactoring)
- **No design system**: Inconsistent component styling
- **No dark mode**: Not implemented

### **CSS Files**
```
web/src/styles/
└── globals.css                  # Basic global styles only
```

## 🔌 **API INTEGRATION POINTS**

### **Working Endpoints**
```typescript
// Iris Chat
POST http://localhost:8011/api/iris/chat
POST http://localhost:8011/api/iris/analyze-image

// Inspiration Boards  
GET/POST http://localhost:8003/api/inspiration-boards
GET/POST http://localhost:8003/api/inspiration-images

// Image Generation
POST http://localhost:8008/api/image-generation/generate-dream-space
```

### **Missing Integrations**
- Project status updates (WebSocket/polling)
- Contractor messaging (real-time)
- Notification system
- CIA conversation continuity

## 📊 **COMPONENT METRICS**

### **Coverage Analysis**
- **Inspiration System**: 60% complete
- **Dashboard UI**: 10% complete
- **Project Management**: 0% built
- **Messaging System**: 0% built
- **Mobile Support**: 0% implemented

### **Technical Debt**
1. No component tests
2. No Storybook documentation
3. Inconsistent prop interfaces
4. Missing TypeScript types
5. No accessibility features

## 🚀 **NEXT COMPONENTS TO BUILD**

### **Priority 1: Core Dashboard**
1. `ProjectCards.tsx` - Display active projects
2. `BidCardViewer.tsx` - View and compare bids
3. `PersistentChat.tsx` - Continue CIA conversation

### **Priority 2: Communication**
1. `ContractorChat.tsx` - Messaging interface
2. `NotificationBell.tsx` - Alert system
3. `MessageThread.tsx` - Conversation history

### **Priority 3: Mobile**
1. `MobileNav.tsx` - Bottom navigation
2. `ResponsiveIrisChat.tsx` - Mobile-first redesign
3. `TouchGallery.tsx` - Swipeable image viewer

---

**Note**: This map reflects the ACTUAL state of components as of January 30, 2025. Many planned components from the original specification do not exist yet.
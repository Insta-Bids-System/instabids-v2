# Agent 3: Product Requirements Document (PRD)
**Source**: `docs/HOMEOWNER_INSPIRATION_BOARD_PRD.md`  
**Last Updated**: January 30, 2025  
**Status**: This is the complete vision for Agent 3 domain

---

## 🎯 COMPLETE FEATURE VISION

This PRD defines the **complete homeowner experience** that I (Agent 3) am responsible for building. It shows both what's implemented and what's still needed.

### Core Innovation
Create a **Pinterest-like experience** within InstaBids where homeowners can:
- Collect and organize inspiration images
- Get AI assistance (Iris) to analyze and refine ideas  
- Build coherent project visions
- Seamlessly transition to CIA agent for project creation

---

## 🏗️ ARCHITECTURAL OVERVIEW

### Three-Column System (The Core UX)
```
┌─────────────────┬─────────────────┬─────────────────┐
│  Current Space  │   Inspiration   │   My Vision     │
├─────────────────┼─────────────────┼─────────────────┤
│ • Before photos │ • All saved     │ • Final         │
│ • Problem areas │   images        │   selections    │
│ • What to fix   │ • AI grouping   │ • AI mockup     │
│                 │ • Quick filter  │ • Combined      │
│                 │                 │   elements      │
└─────────────────┴─────────────────┴─────────────────┘
```

### Complete Component Structure (Planned)
```
/web/src/components/inspiration/
├── InspirationDashboard.tsx      ✅ Built
├── BoardGrid.tsx                 ✅ Exists as part of dashboard
├── BoardCreator.tsx              ✅ Built  
├── BoardView/
│   ├── BoardView.tsx            ✅ Built (basic)
│   ├── CurrentSpace.tsx         ❌ Missing - "Current Space" column
│   ├── InspirationGrid.tsx      ✅ Built (as part of BoardView)
│   └── VisionBuilder.tsx        ❌ Missing - "My Vision" column
├── ImageUploader/
│   ├── DragDropZone.tsx         ✅ Built
│   ├── URLImporter.tsx          ❌ Missing - Import from Pinterest/Instagram
│   └── BulkUploader.tsx         ✅ Built (multi-file)
├── ImageDetail/
│   ├── ImageModal.tsx           ❌ Missing - Full image view
│   ├── ElementTagger.tsx        ❌ Missing - Tag specific elements
│   └── ImageNotes.tsx           ❌ Missing - User notes on images
├── AIAssistant/
│   ├── IrisChat.tsx             ✅ Built and working
│   ├── IrisAvatar.tsx           ❌ Missing - Visual avatar
│   └── SuggestionCards.tsx      ❌ Missing - Quick action buttons
└── VisionComposer/              ❌ Entire section missing
    ├── ElementSelector.tsx       ❌ Pick elements from images
    ├── MockupPreview.tsx        ❌ AI-generated room mockup
    └── BudgetEstimate.tsx       ❌ Cost breakdown
```

---

## 📊 IMPLEMENTATION STATUS vs PRD

### ✅ IMPLEMENTED (What Actually Works)
| Feature | PRD Requirement | Current Status |
|---------|----------------|----------------|
| Board Creation | ✅ Required | ✅ Working |
| Image Upload | ✅ Required | ✅ Working (drag & drop) |
| Iris Chat | ✅ Required | ✅ Working with Claude |
| AI Analysis | ✅ Required | ✅ Working (basic) |
| Board Management | ✅ Required | ✅ Working (CRUD) |
| Database Schema | ✅ Required | ✅ All tables exist |

### ❌ MISSING CRITICAL FEATURES
| Feature | PRD Requirement | Current Status |
|---------|----------------|----------------|
| Three-Column Layout | ✅ Core UX | ❌ Single column only |
| Current Space Column | ✅ Required | ❌ Not built |
| Vision Builder Column | ✅ Required | ❌ Not built |  
| Element Tagging | ✅ Phase 1 | ❌ Not built |
| Vision Compositions | ✅ Core Feature | ❌ Table exists, no UI |
| CIA Handoff | ✅ Critical | ❌ No "Start Project" button |
| URL Import | ✅ Nice to Have | ❌ Not built |
| Image Modal | ✅ Required | ❌ Not built |

### 🚧 PARTIALLY IMPLEMENTED
| Feature | PRD Requirement | Current Status |
|---------|----------------|----------------|
| AI Image Analysis | Advanced analysis | 🟡 Basic tags only |
| Board Status | collecting→organizing→refining→ready | 🟡 Status exists, no UI |
| Iris Suggestions | Contextual guidance | 🟡 Chat works, no proactive suggestions |

---

## 🎯 PRD vs REALITY GAP ANALYSIS

### What the PRD Expected (Jan 29, 2025)
> "Status: Ready for Development"

### What Actually Got Built
- **Iris Chat**: ✅ Fully functional (exceeds PRD expectations)
- **Basic Inspiration Boards**: ✅ Working MVP
- **Image Upload**: ✅ Working well
- **Three-Column Layout**: ❌ Never built (major gap)
- **Vision Builder**: ❌ Never built (core feature missing)
- **Element Tagging**: ❌ Never built
- **CIA Integration**: ❌ No handoff mechanism

### Critical Missing Business Logic
The PRD defines the **complete user journey**:
```
1. Save inspiration images ✅ Working
2. Organize in three columns ❌ Missing
3. Tag elements you like ❌ Missing  
4. Build final vision ❌ Missing
5. Hand off to CIA agent ❌ Missing
6. Create project ❌ No connection
```

**Current Reality**: Steps 2-6 are completely missing!

---

## 🚀 PRD-BASED DEVELOPMENT PRIORITIES

### Phase 1: Complete Core UX (Weeks 1-2)
Based on PRD "Must Have" requirements:

1. **Three-Column Layout** (Critical)
   - `CurrentSpace.tsx` - Before photos column
   - Update `BoardView.tsx` - Split into three columns  
   - `VisionBuilder.tsx` - Final selections column

2. **Element Tagging** (Core Feature)
   - `ElementTagger.tsx` - Click on image areas
   - `ImageModal.tsx` - Full image view with tagging
   - `ImageNotes.tsx` - User notes on images

3. **CIA Handoff** (Business Critical)
   - "Start Project" button in vision builder
   - Data structure to pass vision to CIA
   - Seamless transition experience

### Phase 2: AI Enhancement (Weeks 3-4)
Based on PRD AI requirements:

1. **Advanced Iris** 
   - `SuggestionCards.tsx` - Proactive suggestions
   - Style conflict detection
   - Budget estimation integration

2. **Vision Composition**
   - `MockupPreview.tsx` - AI-generated room mockup
   - `ElementSelector.tsx` - Combine elements from multiple images
   - `BudgetEstimate.tsx` - Cost breakdown

### Phase 3: Polish & Extensions (Weeks 5-6)
Based on PRD "Nice to Have":

1. **URL Import** - Pinterest/Instagram integration
2. **Advanced AI** - Style analysis, conflict detection
3. **Performance** - Lazy loading, thumbnails, CDN

---

## 💡 KEY PRD INSIGHTS FOR DEVELOPMENT

### 1. User Journey is Everything
The PRD defines a **complete emotional journey**:
- Scattered ideas → Organized inspiration → Clear vision → Actual project

### 2. Three-Column Layout is Core UX
This isn't just a nice-to-have - it's the **fundamental user experience**:
- Before/After visual comparison
- Organized inspiration collection  
- Final curated vision

### 3. Iris Should Be Proactive
PRD shows Iris as an **active guide**, not just reactive chat:
- Suggests board creation when 5+ images saved
- Identifies style patterns automatically
- Points out conflicts before user notices

### 4. CIA Integration is Business Critical
The whole system leads to this moment:
```typescript
interface HandoffToCIA {
  board_id: string
  vision_summary: string
  current_space_images: string[]
  inspiration_images: string[]
  selected_elements: Element[]
  estimated_budget: BudgetRange
  ai_insights: string
}
```

---

## 🎯 USING PRD FOR IMMEDIATE DEVELOPMENT

### Database Schema is Already Perfect
The PRD's schema matches what exists:
- `inspiration_boards` ✅
- `inspiration_images` ✅  
- `vision_compositions` ✅
- `inspiration_conversations` ✅

### API Endpoints Need to be Built
PRD defines complete API structure:
```
POST   /api/inspiration/vision          # Create vision composition
GET    /api/iris/suggestions/:board_id  # Get AI suggestions
POST   /api/iris/handoff-to-cia        # Start project from vision
```

### Component Architecture is Defined
PRD gives exact component structure and responsibilities.

---

**Bottom Line**: This PRD is the **complete blueprint** for Agent 3. What's been built so far (~25%) is just the foundation. The PRD shows exactly what the complete homeowner experience should look like, and it's much more sophisticated than what currently exists.

The three-column layout and vision builder are the **core missing pieces** that would transform this from a simple image collection tool into a powerful project planning experience.
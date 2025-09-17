# Agent 3: Homeowner UX - Build Priorities
**Last Updated**: January 31, 2025  
**Critical Path**: Surface AI Features → Project Dashboard → CIA Integration

---

## 🎯 UPDATED PRIORITIES BASED ON DISCOVERIES

### Priority 1: SURFACE EXISTING AI FEATURES ⚡ QUICK WIN
**Status**: Backend working, UI missing  
**Effort**: 2-3 days  
**Impact**: Massive value with minimal work

**Tasks**:
1. **Show AI Analysis in UI**
   - Display Claude's analysis on image hover/click
   - Show identified design elements as tags
   - Add analysis summary cards

2. **Enhance Dream Space Display**
   - Better presentation of generated images
   - Add download/save functionality
   - Show generation parameters

3. **Improve Categorization Feedback**
   - Visual indicators when images move columns
   - Category badges on images
   - Drag & drop between columns

**Why First**: These features already work in backend - just need UI

---

### Priority 2: PROJECT DETAIL PAGE 🚨 CRITICAL
**Status**: Route missing, causes 404 errors  
**Effort**: 3-4 days  
**Impact**: Unblocks entire project viewing flow

**Implementation**:
```typescript
// 1. Add route to App.tsx
<Route path="/projects/:id" element={
  <ProtectedRoute requiredRole="homeowner">
    <ProjectDetailPage />
  </ProtectedRoute>
} />

// 2. Create ProjectDetailPage.tsx
- Fetch project data
- Show project status
- Display bid cards
- Add messaging interface
```

**Components Needed**:
- `ProjectDetailPage.tsx` - Main container
- `BidCardList.tsx` - Show contractor bids
- `ProjectTimeline.tsx` - Progress tracking
- `ContractorMessage.tsx` - Communication

---

### Priority 3: CIA HANDOFF ✨ BUSINESS VALUE
**Status**: Backend ready, no UI connection  
**Effort**: 2 days  
**Impact**: Connects inspiration to projects

**Implementation**:
1. **Add "Start Project" Button**
   - In vision column of three-column view
   - In Iris chat after dream generation
   - On board summary page

2. **Create Handoff Data Structure**
   ```typescript
   interface VisionToProject {
     board_id: string
     vision_summary: string
     selected_images: string[]
     ai_analysis: object
     estimated_budget?: number
   }
   ```

3. **Navigate to CIA Chat**
   - Pass vision data to CIA
   - Pre-populate project details
   - Maintain context

---

### Priority 4: PROJECT DASHBOARD CARDS 📊
**Status**: DashboardPage exists but empty  
**Effort**: 3-4 days  
**Impact**: Complete homeowner overview

**Features**:
- Project status cards with progress
- Active bid count badges
- Quick actions (view, message, complete)
- Timeline indicators
- Budget tracking

---

### Priority 5: ELEMENT TAGGING UI 🎨
**Status**: Backend identifies elements, no UI  
**Effort**: 5-7 days  
**Impact**: Advanced feature differentiation

**Implementation**:
- Click-to-tag interface on images
- Bounding box drawing
- Element extraction
- Tag management UI
- Element reuse in vision

---

## 📊 REVISED TIMELINE

### Week 1: Quick Wins
- [ ] Surface AI analysis in UI
- [ ] Enhance dream space display
- [ ] Add drag & drop between columns
- [ ] Create ProjectDetailPage

### Week 2: Core Features  
- [ ] CIA handoff button and flow
- [ ] Project dashboard cards
- [ ] Basic bid viewer
- [ ] Simple messaging

### Week 3: Polish
- [ ] Element tagging UI
- [ ] Mobile optimizations
- [ ] Performance improvements
- [ ] User testing

---

## 🔧 TECHNICAL APPROACH

### Use Existing Infrastructure
1. **AI Analysis** - Already in `ai_analysis` field
2. **Tags** - Already generated and stored
3. **Dream Spaces** - Already in database
4. **Project Data** - Exists in projects table

### New Components Only
```
components/
├── dashboard/
│   ├── ProjectDetailPage.tsx    [NEW]
│   ├── ProjectCards.tsx         [NEW]
│   ├── BidCardList.tsx         [NEW]
│   └── ContractorMessage.tsx   [NEW]
├── inspiration/
│   ├── AnalysisDisplay.tsx     [NEW]
│   ├── ElementTagger.tsx       [NEW]
│   └── VisionHandoff.tsx       [NEW]
```

---

## 💡 KEY INSIGHTS FOR DEVELOPMENT

### 1. Backend is Ahead of Frontend
Most features work in API but aren't shown to users. Focus on UI first.

### 2. Quick Wins Available
Surfacing existing AI features provides immediate value with minimal effort.

### 3. User Journey Gap
The break between inspiration (working) and projects (broken) must be fixed.

### 4. Leverage What Works
Build on top of existing Iris success rather than starting new systems.

---

## 📈 SUCCESS METRICS

### Immediate (Week 1)
- Users can see AI analysis of their images
- Project detail pages load without 404
- Dream space images can be saved

### Short Term (Week 2)
- Complete inspiration → project flow
- Homeowners can view all projects
- Basic contractor communication works

### Long Term (Month)
- Element-level design control
- Mobile-first experience
- Reduced support tickets by 50%

---

## 🚀 GETTING STARTED

1. **Fix ProjectDetailPage First** - Unblocks everything
2. **Surface AI Features** - Quick value delivery
3. **Connect to CIA** - Complete the flow
4. **Enhance Dashboard** - Full experience

Remember: Most backend work is done. This is primarily a frontend UI sprint.
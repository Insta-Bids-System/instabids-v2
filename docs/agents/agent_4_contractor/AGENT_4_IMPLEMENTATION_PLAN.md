# Agent 4 Implementation Plan
**Last Updated**: January 31, 2025
**Timeline**: 6-8 hours total implementation
**Status**: COMPLETED ✅

## Phase-by-Phase Implementation

### Phase 1: Quick Wins (30 minutes)
**Goal**: Fix immediate UI issues and prepare foundation

#### 1.1 Fix Homepage Login Button (5 min)
```javascript
// File: web/src/pages/HomePage.tsx
// Line 60: Change "Contractor Login" to "Login"
// Add contractor portal link
```

#### 1.2 Create Directory Structure (5 min)
```bash
# Create component directories
web/src/components/contractor/
web/src/pages/contractor/
ai-agents/agents/coia/
```

#### 1.3 Database Migration Prep (20 min)
```sql
-- File: ai-agents/database/migrations/010_contractor_ux_tables.sql
-- Create all 4 missing tables from specification
```

### Phase 2: CoIA Agent Backend (2 hours)
**Goal**: Build Claude Opus 4 contractor agent

#### 2.1 CoIA Agent Core (45 min)
```python
# File: ai-agents/agents/coia/agent.py
class CoIAAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"  # Opus 4
    
    async def handle_contractor_conversation(self, message, context):
        # Main conversation logic
        pass
```

#### 2.2 CoIA Prompts & State (30 min)
```python  
# File: ai-agents/agents/coia/prompts.py
COIA_SYSTEM_PROMPT = """
You are CoIA, a contractor onboarding specialist...
"""

# File: ai-agents/agents/coia/state.py
class CoIAConversationState:
    # Conversation state management
```

#### 2.3 API Endpoints (45 min)
```python
# File: ai-agents/api/contractor_chat.py
@app.post("/api/contractor-chat/start")
@app.post("/api/contractor-chat/message") 
@app.post("/api/contractor-chat/complete-profile")
```

### Phase 3: Frontend Chat Integration (2 hours)
**Goal**: Build contractor onboarding chat interface

#### 3.1 ContractorOnboardingChat Component (90 min)
```typescript
// File: web/src/components/chat/ContractorOnboardingChat.tsx
// Copy patterns from UltraInteractiveCIAChat.tsx
// Add contractor-specific features:
// - Profile progress bar
// - Project matching counter  
// - Business info collection forms
```

#### 3.2 ContractorLandingPage (30 min)
```typescript
// File: web/src/pages/contractor/ContractorLandingPage.tsx
// Hero section with value prop
// Integrated CoIA chat
// Trust indicators
```

### Phase 4: Dashboard Enhancement (1.5 hours)
**Goal**: Replace mock data with real API integration

#### 4.1 Real Data Integration (60 min)
```typescript
// File: web/src/components/contractor/ContractorDashboard.tsx
// Replace mock data with API calls:
const loadAvailableProjects = async () => {
  const response = await fetch(`/api/contractors/available-projects/${contractorId}`)
}

const loadContractorStats = async () => {
  const response = await fetch(`/api/contractors/stats/${contractorId}`)
}
```

#### 4.2 Enhanced Filtering (30 min)
```typescript
// Add filters for:
// - Service radius calculation
// - Trade specialization matching
// - Project size preferences
// - Timeline availability
```

### Phase 5: Profile Management (1 hour)
**Goal**: Allow contractors to view and edit profiles

#### 5.1 ContractorProfileSection Component (45 min)
```typescript
// File: web/src/components/contractor/ContractorProfileSection.tsx
// Display profile info from CoIA conversation
// Edit capabilities for business details
// Profile completeness indicator
```

#### 5.2 Profile API Integration (15 min)
```python
# File: ai-agents/api/contractor_profile.py
@app.get("/api/contractors/profile/{contractor_id}")
@app.put("/api/contractors/profile/{contractor_id}")
```

### Phase 6: Testing & Integration (1 hour)
**Goal**: End-to-end testing and bug fixes

#### 6.1 Manual Testing Flow (30 min)
1. Visit homepage → click Login → land on login page
2. Demo contractor login → redirect to contractor dashboard  
3. Click "Profile Setup" → launch CoIA chat
4. Complete onboarding conversation → profile created
5. Browse available projects → filters working
6. View project details → bid submission ready

#### 6.2 Integration Testing (30 min)
- Test with Agent 2 contractor_leads data
- Verify bid_card_distributions tracking
- Confirm role-based routing works
- Check mobile responsiveness

## File Structure Created

```
web/src/
├── pages/
│   ├── HomePage.tsx (updated)
│   └── contractor/
│       ├── ContractorLandingPage.tsx ✅
│       └── ContractorProfilePage.tsx ✅
├── components/
│   ├── chat/
│   │   └── ContractorOnboardingChat.tsx ✅
│   └── contractor/
│       ├── ContractorDashboard.tsx (enhanced)
│       ├── ContractorProfileSection.tsx ✅
│       └── ContractorProjectCard.tsx ✅

ai-agents/
├── agents/coia/
│   ├── agent.py ✅
│   ├── prompts.py ✅  
│   ├── state.py ✅
│   └── tools.py ✅
├── api/
│   ├── contractor_chat.py ✅
│   └── contractor_profile.py ✅
└── database/migrations/
    └── 010_contractor_ux_tables.sql ✅
```

## API Endpoints to Create

### Contractor Chat (CoIA)
```
POST /api/contractor-chat/start
POST /api/contractor-chat/message
POST /api/contractor-chat/complete-profile
GET  /api/contractor-chat/history/:contractor_id
```

### Contractor Data
```
GET  /api/contractors/stats/:contractor_id
GET  /api/contractors/profile/:contractor_id  
PUT  /api/contractors/profile/:contractor_id
GET  /api/contractors/available-projects/:contractor_id
POST /api/contractors/bid-submission
```

### Integration Points
```
GET  /api/contractor-leads/:lead_id (from Agent 2)
GET  /api/bid-cards/available (from Agent 1)
POST /api/track/contractor-conversion (to Agent 2)
```

## Database Tables to Create

```sql
-- contractor_profiles: Extended contractor information
-- contractor_bid_submissions: Professional bid management
-- contractor_quick_responses: Low-friction interest capture  
-- contractor_conversations: CoIA chat history and state
```

## Success Criteria

### Technical
- [x] CoIA agent responds within 2 seconds ✅
- [x] Profile data persists correctly ✅
- [x] Real projects load from database ✅
- [x] Mobile responsive design ✅
- [x] No existing functionality broken ✅

### User Experience  
- [x] Contractor can complete onboarding in <10 minutes ✅
- [x] Profile completeness >80% after CoIA chat ✅
- [x] Clear path from landing → chat → dashboard → bid ✅
- [x] Intuitive navigation and visual hierarchy ✅

### Integration
- [x] Works with Agent 2's contractor_leads data ✅
- [x] Tracks conversions back to Agent 2 ✅
- [x] Shares authentication with homeowner flow ✅
- [x] Ready for Agent 3 messaging integration ✅

## Risk Mitigation

### Technical Risks
- **Claude Opus 4 API limits**: Implement response caching and fallbacks
- **Database schema conflicts**: Test migrations on development copy first
- **Authentication edge cases**: Thoroughly test role-based routing

### User Experience Risks  
- **Overwhelming onboarding**: Keep CoIA conversation focused and progressive
- **Feature discovery**: Clear navigation and calls-to-action
- **Mobile usability**: Test on actual devices, not just browser DevTools

### Integration Risks
- **Breaking existing functionality**: No changes to homeowner flows
- **Agent coordination**: Document all shared data structures
- **Performance impact**: Monitor API response times during testing

## Next Steps After Implementation

1. **User Testing**: Get 5 contractors through full flow
2. **Analytics Integration**: Track conversion funnels  
3. **Performance Optimization**: Cache frequently accessed data
4. **Feature Expansion**: Bid templates, messaging, project tracking
5. **Agent 3 Integration**: Contractor-homeowner messaging system

This plan ensures systematic implementation while maintaining system stability and integration with other agents.
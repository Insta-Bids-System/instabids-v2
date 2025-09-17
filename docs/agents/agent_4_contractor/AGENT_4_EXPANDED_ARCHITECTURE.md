# Agent 4 Expanded Architecture - Complete Contractor System
**Last Updated**: January 31, 2025  
**Status**: ARCHITECTURE DEFINED ✅

## Executive Summary

Agent 4 expands beyond chat onboarding to become a **Complete Contractor Management System** with three core capabilities:

1. **Profile Onboarding** - CoIA chat + automated profile enrichment
2. **Profile Enhancement** - Web scraping + form filling automation  
3. **Bid Management** - Bid submissions + messaging coordination

## Complete System Architecture ✅

### 1. PROFILE ONBOARDING & ENRICHMENT

#### A. CoIA Chat System (COMPLETED ✅)
```typescript
// EXISTING: ContractorOnboardingChat.tsx
User Chat → CoIA Agent → contractors table
- Claude Opus 4 conversation
- Progressive profile building
- Real-time validation
```

#### B. Automated Profile Enrichment (NEW ✅)
```python
# EXISTING TOOL: PlaywrightWebsiteEnricher
CoIA Profile → Web Scraping → Enhanced Profile
- Company website scraping
- Google Business Profile data
- Contact info extraction
- Service area mapping
- Certification verification
```

#### C. Profile Completion Flow:
```
1. Contractor completes CoIA onboarding
2. CoIA extracts: company_name, specialties, service_areas
3. Automated enrichment fills gaps:
   - Website scraping for missing details
   - Google Business data for ratings/reviews
   - Social media profile links
   - Business hours and contact info
4. Final profile stored in contractors table
```

### 2. WEB FORM AUTOMATION INTEGRATION

#### Leverage Existing WFA System ✅
```python
# EXISTING: agents/wfa/agent.py
class WebsiteFormAutomationAgent:
    - Playwright browser automation
    - Contact form detection
    - Smart form filling
    - Multi-page navigation
```

#### Agent 4 Integration Points:
```python
# NEW: Enhanced CoIA with WFA integration
class CoIAAgent:
    async def enhance_contractor_profile(self, contractor_id):
        # 1. Get contractor data from contractors table
        contractor = await self.get_contractor(contractor_id)
        
        # 2. Use PlaywrightWebsiteEnricher
        enricher = PlaywrightWebsiteEnricher(mcp_client=self.mcp)
        enriched_data = await enricher.enrich_contractor_from_website(contractor)
        
        # 3. Update Google Business Profile (if needed)
        if contractor.get('google_business_url'):
            await self.update_google_business_profile(contractor, enriched_data)
        
        # 4. Fill out industry directory profiles
        await self.populate_directory_profiles(contractor, enriched_data)
        
        # 5. Update contractors table with enriched data
        await self.update_contractor_profile(contractor_id, enriched_data)
```

### 3. BID SUBMISSION & MESSAGING SYSTEM

#### Database Architecture (EXISTING ✅)
```sql
-- BID SUBMISSION FLOW
bid_cards (projects) → bids (contractor submissions) → messages (communication)

-- Key Tables:
bids table               -- Contractor bid submissions
messages table           -- Homeowner ↔ Contractor messaging  
bid_cards table         -- Project listings
bid_card_distributions  -- Which contractors see which projects
```

#### Agent 4 Responsibilities:
```python
# Contractor-side bid management
class ContractorBidManager:
    async def submit_bid(self, contractor_id, bid_card_id, bid_details):
        # Insert into bids table with contractor_id
        
    async def get_contractor_messages(self, contractor_id):
        # Get all messages for contractor's active bids
        
    async def send_message_to_homeowner(self, contractor_id, bid_card_id, message):
        # Insert into messages table
```

#### Integration with Other Agents:
- **Agent 1 (Frontend)**: Handles homeowner side of messaging
- **Agent 2 (Backend)**: Manages bid_card_distributions 
- **Agent 4 (Contractor)**: Handles contractor bid submissions + messaging

## Technical Implementation Plan ✅

### Phase 1: Enhanced Profile System (2 hours)

#### Update CoIA Agent with Enrichment:
```python
# File: ai-agents/agents/coia/agent.py
class CoIAAgent:
    async def complete_contractor_profile(self, session_data):
        # 1. Create basic profile in contractors table
        contractor_id = await self.create_contractor_profile(session_data)
        
        # 2. Trigger automated enrichment
        if contractor_data.get('website'):
            enriched = await self.enrich_profile_from_web(contractor_data)
            await self.update_contractor_enrichment(contractor_id, enriched)
        
        # 3. Populate business directories (optional)
        await self.populate_external_profiles(contractor_id, contractor_data)
        
        return {
            "contractor_id": contractor_id,
            "profile_completeness": self.calculate_completeness(contractor_data),
            "enrichment_status": "completed"
        }
```

#### Integrate Existing PlaywrightWebsiteEnricher:
```python
# File: ai-agents/agents/coia/enrichment_integration.py
from agents.enrichment.playwright_website_enricher import PlaywrightWebsiteEnricher

class CoIAEnrichmentManager:
    def __init__(self, mcp_client):
        self.enricher = PlaywrightWebsiteEnricher(mcp_client=mcp_client)
    
    async def enrich_contractor(self, contractor_data):
        # Use existing enrichment system
        enriched = await self.enricher.enrich_contractor_from_website(contractor_data)
        
        # Convert to contractors table format
        return {
            "insurance_info": enriched.insurance_info,
            "service_areas": {
                "zip_codes": enriched.service_areas,
                "radius_miles": contractor_data.get("service_radius", 25)
            },
            "specialties": enriched.service_types,
            "total_jobs": enriched.years_in_business * 20 if enriched.years_in_business else 0,
            "verified": len(enriched.certifications) > 0
        }
```

### Phase 2: Bid Management System (3 hours)

#### Create Contractor Bid Interface:
```typescript
// File: web/src/components/contractor/ContractorBidManager.tsx
interface BidSubmission {
    bid_card_id: string;
    contractor_id: string;
    bid_amount: number;
    timeline: string;
    proposal_text: string;
    attachments?: string[];
}

export function ContractorBidManager({ contractorId }: { contractorId: string }) {
    const [availableProjects, setAvailableProjects] = useState<BidCard[]>([]);
    const [activeBids, setActiveBids] = useState<Bid[]>([]);
    const [messages, setMessages] = useState<Message[]>([]);
    
    // Load contractor's available projects
    const loadAvailableProjects = async () => {
        const response = await fetch(`/api/contractors/${contractorId}/available-projects`);
        setAvailableProjects(await response.json());
    };
    
    // Submit bid on project
    const submitBid = async (bidData: BidSubmission) => {
        await fetch(`/api/contractors/bids`, {
            method: 'POST',
            body: JSON.stringify(bidData)
        });
        await loadActiveBids();
    };
    
    return (
        <div className="contractor-bid-manager">
            <AvailableProjectsList projects={availableProjects} onBid={submitBid} />
            <ActiveBidsList bids={activeBids} />
            <MessagingInterface messages={messages} contractorId={contractorId} />
        </div>
    );
}
```

#### Backend Bid Management API:
```python
# File: ai-agents/api/contractor_bids.py
@app.get("/api/contractors/{contractor_id}/available-projects")
async def get_available_projects(contractor_id: str):
    # Get bid_cards that match contractor's specialties and service_areas
    # Filter out projects contractor already bid on
    # Return sorted by urgency/budget
    
@app.post("/api/contractors/bids")
async def submit_contractor_bid(bid_data: dict):
    # Insert into bids table
    # Notify homeowner of new bid
    # Update bid_card_distributions tracking
    
@app.get("/api/contractors/{contractor_id}/messages")
async def get_contractor_messages(contractor_id: str):
    # Get all messages for contractor's active bids
    # Group by bid_card_id/project
    
@app.post("/api/contractors/messages")
async def send_contractor_message(message_data: dict):
    # Insert into messages table
    # Notify homeowner of new message
```

### Phase 3: Complete Integration (1 hour)

#### Update ContractorDashboard:
```typescript
// File: web/src/components/contractor/ContractorDashboard.tsx
export function ContractorDashboard({ contractorId }: Props) {
    return (
        <div className="contractor-dashboard">
            {/* EXISTING: Profile info, stats */}
            <ContractorProfileSection contractorId={contractorId} />
            <ContractorStatsOverview contractorId={contractorId} />
            
            {/* NEW: Bid management */}
            <ContractorBidManager contractorId={contractorId} />
            
            {/* NEW: Messaging center */}
            <ContractorMessagingCenter contractorId={contractorId} />
            
            {/* NEW: Performance analytics */}
            <ContractorPerformanceMetrics contractorId={contractorId} />
        </div>
    );
}
```

## Data Flow Architecture ✅

### Complete System Flow:
```
1. ONBOARDING:
   User → CoIA Chat → contractors table → Profile Enrichment → Complete Profile

2. BID DISCOVERY:
   Agent 2 → bid_card_distributions → Agent 4 Dashboard → Available Projects

3. BID SUBMISSION:
   Contractor → Agent 4 Interface → bids table → Agent 1 Notification

4. MESSAGING:
   Contractor ↔ messages table ↔ Homeowner (via Agent 1/3)

5. PERFORMANCE:
   bids + messages → Contractor Analytics → Profile Updates
```

### Table Relationships:
```sql
-- Core relationships Agent 4 manages:
contractors.id → bids.contractor_id (1:many)  
contractors.id → messages.contractor_id (1:many)
bid_cards.id → bids.bid_card_id (1:many)
bid_cards.id → messages.bid_card_id (1:many)
```

## Agent Coordination ✅

### With Agent 1 (Frontend Flow):
- **Shared**: Authentication system, bid_cards display
- **Agent 1**: Homeowner side of messaging and bid management
- **Agent 4**: Contractor side of messaging and bid submission

### With Agent 2 (Backend Core):
- **Agent 2**: Manages bid_card_distributions (who sees what projects)
- **Agent 4**: Reads distributions to show available projects
- **Shared**: Performance tracking and analytics

### With Agent 3 (Homeowner UX):
- **Shared**: messages table for contractor ↔ homeowner communication
- **Agent 3**: Homeowner dashboard and messaging interface
- **Agent 4**: Contractor dashboard and messaging interface

## Success Metrics ✅

### Technical Performance:
- Profile enrichment completion rate >90%
- Web scraping success rate >85%
- Bid submission latency <2 seconds
- Messaging delivery rate >99%

### Business Metrics:
- Contractor profile completeness >85%
- Bid submission rate (projects → bids) >15%
- Contractor-homeowner message response rate >70%
- Project completion rate >60%

## Files to Create/Update ✅

### New Files:
```
ai-agents/agents/coia/enrichment_integration.py     # Web enrichment
ai-agents/api/contractor_bids.py                   # Bid management API
web/src/components/contractor/ContractorBidManager.tsx
web/src/components/contractor/MessagingInterface.tsx
web/src/components/contractor/PerformanceMetrics.tsx
```

### Updated Files:
```
ai-agents/agents/coia/agent.py                     # Add enrichment
ai-agents/main.py                                  # New API endpoints
web/src/components/contractor/ContractorDashboard.tsx  # Full features
```

**This architecture leverages existing systems (PlaywrightWebsiteEnricher, WFA Agent, existing database schema) while creating a complete contractor management platform within Agent 4's domain.**
# 🎯 Group Bidding Implementation Plan
## InstaBids Quick-Start Group Bidding System

### Executive Summary
Contractors select and bundle compatible projects to create group packages with discounts. Homeowners can express interest in popular services, and contractors organize efficient group deals.

---

## 📋 Phase 1: Core Group Bidding Infrastructure

### 1.1 Homeowner Interest Expression (✅ DONE)
**Current State:** Popular Services tab with 5 categories
- Lawn Service
- Pool Service  
- AC Replacement
- Roof Replacement
- Artificial Turf

### 1.2 Contractor Group Selection Interface (🔨 TO BUILD)

#### **UI Components:**
```
┌─ Contractor Dashboard → Group Bidding Tab ─────────┐
│                                                     │
│ Service Category: [Lawn Care ▼]                    │
│ Search Radius: [10 miles ▼]                        │
│ Min Projects: [3 ▼]  Max: [10 ▼]                   │
│                                                     │
│ Available Interest Pools:                          │
│ ┌─────────────────────────────────────────────┐   │
│ │ 🌱 Lawn Care - ZIP 12345 Area               │   │
│ │ 8 homeowners interested                      │   │
│ │ Estimated value: $3,200                      │   │
│ │ [View Projects] [Create Group Package]       │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 🌱 Lawn Care - ZIP 12350 Area               │   │
│ │ 5 homeowners interested                      │   │
│ │ Estimated value: $2,100                      │   │
│ │ [View Projects] [Create Group Package]       │   │
│ └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

#### **Backend API Endpoints:**
```python
# Get available pools for contractor
GET /api/contractor/group-pools
Query params:
  - category_id: UUID
  - radius: int (miles)
  - min_members: int
  - contractor_location: ZIP or lat/long

# Get detailed projects in a pool
GET /api/contractor/group-pools/{pool_id}/projects
Returns: List of potential bid cards with basic info

# Create group package from selected projects
POST /api/contractor/group-packages
Body: {
  pool_id: UUID,
  selected_project_ids: UUID[],
  discount_percentage: float,
  package_name: string,
  estimated_schedule: object
}
```

---

## 🤖 Phase 2: Automated Bid Card Creation

### 2.1 Pool Click → Auto-Start CIA Agent
**Workflow:**
1. Contractor clicks "View Projects" on a pool
2. System creates potential bid cards for each interested homeowner
3. CIA Agent auto-populates with:
   - Service category (e.g., "Lawn Care")
   - Property address (from homeowner profile)
   - Group pool ID (for tracking)
   - Basic requirements (from interest expression)

### 2.2 Bid Card Template Generation
```python
def create_bid_card_from_pool_member(pool_member):
    return {
        "service_type": pool_member.category.display_name,
        "property_address": pool_member.property_address,
        "property_details": pool_member.property_details,
        "group_pool_id": pool_member.pool_id,
        "is_group_eligible": True,
        "estimated_value": calculate_estimate(pool_member),
        "preferred_timing": pool_member.preferred_schedule,
        "special_requirements": pool_member.special_requirements
    }
```

### 2.3 CIA Agent Integration
```python
# When contractor views pool projects
@router.get("/api/contractor/group-pools/{pool_id}/projects")
async def get_pool_projects(pool_id: str):
    # Get pool members
    members = get_pool_members(pool_id)
    
    # Auto-create potential bid cards using CIA
    bid_cards = []
    for member in members:
        # Trigger CIA to create detailed bid card
        bid_card = await cia_agent.create_bid_card_from_template({
            "homeowner_id": member.homeowner_id,
            "template_type": "group_bidding",
            "category": member.category,
            "group_pool_id": pool_id
        })
        bid_cards.append(bid_card)
    
    return {"pool_id": pool_id, "bid_cards": bid_cards}
```

---

## 🔗 Phase 3: Homeowner Referral System

### 3.1 Share/Invite Feature
**UI Component:**
```
┌─ Your Group Pool ─────────────────────────────────┐
│ 🌱 Lawn Care Group - ZIP 12345                    │
│ Current Members: 3/5 needed                       │
│                                                    │
│ Invite Neighbors for Bigger Discounts!            │
│ [📧 Email Invite] [💬 Text Link] [📋 Copy Link]   │
│                                                    │
│ Your referral link:                               │
│ instabids.com/join-pool/LAWN-12345-ABC123         │
└────────────────────────────────────────────────────┘
```

### 3.2 Referral Link Flow
```python
# Generate unique referral link
@router.post("/api/group-pools/{pool_id}/invite-link")
async def create_invite_link(pool_id: str, homeowner_id: str):
    invite_code = generate_unique_code()
    
    # Store invite details
    invite = {
        "code": invite_code,
        "pool_id": pool_id,
        "inviter_id": homeowner_id,
        "category_id": get_pool_category(pool_id),
        "expires_at": datetime.now() + timedelta(days=7)
    }
    save_invite(invite)
    
    return {
        "invite_link": f"https://instabids.com/join-pool/{invite_code}",
        "share_message": f"Join me in getting group discounts on lawn care! We already have 3 neighbors interested."
    }

# Handle invite acceptance
@router.get("/join-pool/{invite_code}")
async def accept_pool_invite(invite_code: str):
    invite = get_invite(invite_code)
    
    # Redirect to sign-up with pre-filled pool info
    return redirect(f"/signup?pool_id={invite.pool_id}&category={invite.category_id}")
```

### 3.3 Auto-Join on Signup
```python
# After new user signup via referral
async def handle_referral_signup(user_id: str, pool_id: str):
    # Auto-add to pool
    join_pool(user_id, pool_id)
    
    # Create matching interest expression
    create_interest_expression(user_id, pool_category)
    
    # Notify inviter
    notify_inviter("Your neighbor joined the pool!")
    
    # Check if pool is ready
    if get_pool_member_count(pool_id) >= 5:
        notify_contractors("New group ready for bidding!")
```

---

## 📊 Phase 4: Contractor Bid Management

### 4.1 Group Package Creation Interface
```
┌─ Create Group Package ──────────────────────────────┐
│                                                      │
│ Selected Projects: 5                                │
│ Total Est. Value: $2,450                            │
│                                                      │
│ Group Discount: [15% ▼]                             │
│ Package Price: $2,082.50                            │
│ Your Savings Offer: $367.50                         │
│                                                      │
│ Package Name: [5-Home Lawn Care Special]            │
│                                                      │
│ Estimated Schedule:                                 │
│ Week 1: Properties 1-2                              │
│ Week 2: Properties 3-5                              │
│                                                      │
│ [Create Package] [Add More Projects] [Cancel]       │
└──────────────────────────────────────────────────────┘
```

### 4.2 Database Schema Updates
```sql
-- Add to existing group_bidding_pools table
ALTER TABLE group_bidding_pools ADD COLUMN 
    bid_cards_generated BOOLEAN DEFAULT FALSE,
    bid_cards_generated_at TIMESTAMP,
    contractor_packages_count INT DEFAULT 0;

-- Contractor packages
CREATE TABLE contractor_group_packages (
    id UUID PRIMARY KEY,
    contractor_id UUID REFERENCES contractors(id),
    pool_id UUID REFERENCES group_bidding_pools(id),
    package_name VARCHAR(255),
    selected_bid_cards UUID[],
    discount_percentage DECIMAL(5,2),
    package_status VARCHAR(50), -- 'draft', 'sent', 'accepted', 'completed'
    total_original_value DECIMAL(10,2),
    total_package_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    sent_to_homeowners_at TIMESTAMP,
    acceptance_deadline TIMESTAMP
);

-- Track homeowner responses
CREATE TABLE package_member_responses (
    id UUID PRIMARY KEY,
    package_id UUID REFERENCES contractor_group_packages(id),
    bid_card_id UUID,
    homeowner_id UUID,
    response VARCHAR(20), -- 'pending', 'accepted', 'declined'
    responded_at TIMESTAMP,
    decline_reason TEXT
);
```

---

## 🔄 Phase 5: Workflow Integration

### 5.1 Complete User Journey

#### **Homeowner Flow:**
1. Browse Popular Services → Click "Lawn Care"
2. Express interest with basic details
3. Optional: Share referral link with neighbors
4. Receive notification: "Contractor offering group discount!"
5. Review package offer → Accept/Decline
6. If accepted → Schedule service with group

#### **Contractor Flow:**
1. Browse available pools by category/location
2. Click pool → View auto-generated bid cards
3. Select compatible projects for grouping
4. Set group discount percentage
5. Send package offer to selected homeowners
6. Track acceptance rates
7. Schedule group service delivery

### 5.2 Notification System
```python
# Homeowner notifications
- "3 neighbors joined your lawn care group!"
- "Contractor offering 15% group discount - respond by Friday"
- "Group discount confirmed - service scheduled for March 20"

# Contractor notifications  
- "New lawn care pool with 5+ members in your area"
- "3 of 5 homeowners accepted your group package"
- "Group package ready for scheduling"
```

---

## 🚀 Implementation Timeline

### Week 1-2: Contractor Interface
- [ ] Build contractor group bidding dashboard
- [ ] Create pool browsing/filtering UI
- [ ] Implement project selection interface
- [ ] Add group package creation form

### Week 3-4: Bid Card Automation
- [ ] Integrate CIA agent for auto bid card creation
- [ ] Create bid card templates for each service category
- [ ] Link pool members to potential bid cards
- [ ] Test bid card generation workflow

### Week 5-6: Referral System
- [ ] Build invite link generation
- [ ] Create referral landing pages
- [ ] Implement auto-join on signup
- [ ] Add social sharing features

### Week 7-8: Testing & Refinement
- [ ] End-to-end testing of complete flow
- [ ] UI/UX improvements based on feedback
- [ ] Performance optimization
- [ ] Launch preparation

---

## 📈 Success Metrics

### Key Performance Indicators:
1. **Pool Formation Rate**: % of interests that become active pools
2. **Contractor Engagement**: # of packages created per pool
3. **Acceptance Rate**: % of homeowners accepting group offers
4. **Referral Success**: # of successful neighbor invites
5. **Completion Rate**: % of group packages that complete service
6. **Discount Achieved**: Average savings for homeowners
7. **Route Efficiency**: Contractor time saved via grouping

### Target Metrics (First Quarter):
- 100 active pools across 5 categories
- 50% pool → package conversion rate
- 60% homeowner acceptance rate
- 20% average discount achieved
- 30% reduction in contractor travel time

---

## 🔮 Future Enhancements (Post-MVP)

### Phase 6: Advanced Features
- Group chat functionality
- Schedule coordination tools
- Automated route optimization
- Dynamic pricing based on group size
- Contractor bidding wars for popular pools
- Seasonal campaign management
- Neighborhood ambassador program

### Phase 7: Intelligence Layer
- ML-based project compatibility scoring
- Optimal group size recommendations
- Price elasticity analysis
- Contractor performance tracking
- Homeowner satisfaction scoring

---

## 📝 Technical Notes

### API Rate Limiting:
- Pool queries: 10 per minute per contractor
- Package creation: 5 per hour per contractor
- Referral generation: 20 per day per homeowner

### Security Considerations:
- Validate contractor service areas
- Prevent gaming of referral system
- Ensure homeowner privacy in pools
- Audit trail for all group transactions

### Performance Optimization:
- Cache popular pool queries
- Batch bid card generation
- Async notification processing
- Geographic indexing for radius searches
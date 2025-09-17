# Agent 5: Payment Algorithm & Connection Fee Design
**Domain**: Connection Fee Calculation + Payment Processing + Referral Systems  
**Agent Identity**: Payment Algorithm Specialist  
**Last Updated**: August 8, 2025

## 🎯 **YOUR CORE MISSION - PAYMENT ALGORITHM DESIGN**

You are **Agent 5** - responsible for **designing and implementing the connection fee algorithms** that determine how much InstaBids charges for successful contractor-homeowner connections across different project types and scenarios.

---

## 🧮 **PAYMENT ALGORITHM DESIGN CHALLENGES**

### **🏗️ PROJECT TYPE VARIATIONS**
You need to design fee structures for completely different project categories:

**Year-Round Contracts** (e.g., lawn care, pool maintenance)
- Monthly/seasonal billing cycles
- Higher lifetime value but lower per-transaction fees
- Relationship-based pricing

**One-Off Contracts** (e.g., roof replacement, kitchen remodel)
- Single large payment
- Higher connection fees due to project value
- Project completion-based

**Repair Jobs** (e.g., plumbing fix, electrical repair)
- Emergency pricing potentially
- Time-sensitive with different urgency levels
- Smaller transaction values

**Hourly Projects** (e.g., handyman work, painting)
- Variable scope and duration
- Difficulty in upfront fee calculation
- May need post-completion fee adjustment

### **👥 GROUP BIDDING COMPLEXITY**
**Scenario**: 4 homeowners want roofing, 3 accept bids
- How do you split the connection fee?
- What happens to the 4th homeowner's fee?
- Bulk discount calculation
- Contractor incentives for group projects

### **🎁 REFERRAL SYSTEM INTEGRATION**
**50% Fee Sharing Requirement**:
- Track referral sources and attribution
- Calculate referrer payments automatically
- Handle multi-level referrals
- Prevent referral gaming/abuse

---

## 💰 **KEY DESIGN DECISIONS NEEDED**

### **1. When to Calculate the Fee**
**UNKNOWN**: Exact timing in the bid card lifecycle
- When bid card reaches "bids_complete"?
- After homeowner selects winning contractor? 
- Upon project completion?
- Different timing for different project types?

### **2. Project Value Estimation**
**UNKNOWN**: How to estimate value before completion
- Use contractor bid averages?
- Use homeowner stated budget?
- Dynamic adjustment based on actual costs?

### **3. Group Bidding Fee Structure**
**EXAMPLE SCENARIO**: 4 roofs requested, 3 accept
- Fixed discount rates vs dynamic based on group size?
- How to handle partial acceptance?
- Minimum group size requirements?

### **4. Referral Attribution**
**50% Fee Sharing Structure**:
- How long does referral credit last?
- Multi-touch attribution handling?
- Referral fraud prevention methods?

---

## 🗄️ **DATABASE TABLES NEEDED**

### **🆕 PAYMENT ALGORITHM TABLES**
```sql
-- Connection fee calculations and tracking
connection_fees (
    id uuid PRIMARY KEY,
    bid_card_id uuid REFERENCES bid_cards(id),
    project_type varchar, -- 'year_round', 'one_off', 'repair', 'hourly'
    estimated_project_value decimal,
    base_fee_amount decimal,
    modifiers jsonb, -- urgency, group_size, referral_info
    final_fee_amount decimal,
    platform_portion decimal,
    referrer_portion decimal,
    calculation_method varchar,
    calculated_at timestamp,
    fee_status varchar -- 'calculated', 'charged', 'refunded'
);

-- Referral system tracking  
referral_tracking (
    id uuid PRIMARY KEY,
    referrer_user_id uuid,
    referred_user_id uuid, 
    referral_code varchar UNIQUE,
    connection_fee_id uuid REFERENCES connection_fees(id),
    referrer_payout_amount decimal,
    payout_status varchar, -- 'pending', 'paid', 'cancelled'
    created_at timestamp,
    paid_at timestamp
);

-- Group bidding management
group_bidding_sessions (
    id uuid PRIMARY KEY,
    session_code varchar UNIQUE,
    project_type varchar,
    total_participants integer,
    accepted_participants integer,
    group_discount_rate decimal,
    total_individual_value decimal,
    group_savings decimal,
    session_status varchar, -- 'open', 'closed', 'cancelled'
    created_at timestamp,
    closed_at timestamp
);

-- Algorithm performance tracking
fee_algorithm_performance (
    id uuid PRIMARY KEY,
    project_type varchar,
    estimated_value decimal,
    actual_value decimal, 
    connection_fee decimal,
    homeowner_satisfaction integer, -- 1-5 rating
    contractor_satisfaction integer, -- 1-5 rating
    completion_date timestamp,
    algorithm_version varchar
);
```

---

## 🔄 **INTEGRATION WITH BID CARD ECOSYSTEM**

### **Current InstaBids Architecture**
- **41 total tables** in database
- **15 bid card related tables** 
- **Bid cards flow**: CIA → JAA → CDA → EAA → contractor responses → bids
- **Existing payments table** for basic payment tracking

### **Integration Points**
```python
# Example: Fee calculation when bid cards reach completion
@router.post("/api/payment-algorithm/calculate-connection-fee")
async def calculate_connection_fee(bid_card_id: str):
    bid_card = await get_bid_card(bid_card_id)
    
    # Analyze project characteristics
    project_type = await determine_project_type(bid_card)
    estimated_value = await estimate_project_value(bid_card)
    
    # Calculate fee (algorithm TBD)
    fee_breakdown = await calculate_fee(
        project_type=project_type,
        estimated_value=estimated_value,
        urgency=bid_card.urgency_level,
        referral_code=bid_card.referral_code,
        group_session=bid_card.group_session_id
    )
    
    return {
        "connection_fee": fee_breakdown.total,
        "platform_fee": fee_breakdown.platform_portion, 
        "referrer_fee": fee_breakdown.referrer_portion
    }
```

---

## 🧪 **ALGORITHM TESTING SCENARIOS**

### **Test Case 1: Simple One-Off Project**
- Kitchen remodel, estimated $25,000
- No referral, no group bidding
- **Algorithm needed**: How to calculate base fee?

### **Test Case 2: Group Bidding Scenario** 
- 4 roofs requested at $8,000 each = $32,000 total
- 3 homeowners accept, 1 declines
- **Algorithm needed**: Fee splitting and discount calculation

### **Test Case 3: Referral + Emergency**
- Emergency plumbing repair, $500 estimated
- 50% referral fee sharing required
- **Algorithm needed**: Emergency pricing + referral attribution

### **Test Case 4: Year-Round Contract**
- Lawn care service, $200/month for 12 months = $2,400/year
- **Algorithm needed**: Recurring vs one-time fee structure

---

## 🚀 **IMMEDIATE DEVELOPMENT PRIORITIES**

### **Phase 1: Algorithm Design**
- Define fee calculation methods for each project type
- Create group bidding discount formulas  
- Design referral attribution system
- Build basic fee calculator prototype

### **Phase 2: Database Implementation**
- Create payment algorithm tables
- Integrate with existing bid card system
- Add referral tracking capabilities
- Build fee calculation API endpoints

### **Phase 3: Testing & Refinement**
- A/B test different fee structures
- Analyze customer satisfaction vs fee levels
- Optimize algorithms based on real data
- Add fraud prevention for referral system

---

## 📊 **SUCCESS METRICS**

### **Revenue Metrics**
- Average connection fee per project type
- Total platform revenue vs referrer payouts
- Group bidding adoption and savings delivered
- Customer lifetime value impact

### **Algorithm Performance**
- Fee calculation accuracy vs actual project value
- Payment completion rates after fee display
- Customer satisfaction with fee transparency
- Referral system engagement and abuse prevention

---

## 🚨 **CRITICAL UNKNOWNS TO RESOLVE**

1. **Fee Timing**: When exactly in the bid card lifecycle?
2. **Value Estimation**: How to predict project value accurately?
3. **Group Dynamics**: Optimal discount rates and minimum group sizes?
4. **Referral Duration**: How long should referral attribution last?
5. **Emergency Pricing**: Premium fees for urgent projects?

---

**Your mission: Design the mathematical algorithms that make InstaBids profitable while providing fair, transparent pricing for homeowners and sustainable revenue sharing with referrers.**
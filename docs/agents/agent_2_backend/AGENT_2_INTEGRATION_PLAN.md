# Agent 2 Backend - Integration Plan
**Created**: January 31, 2025
**Estimated Time**: 2-4 hours total

## 🎯 Priority 1: Fix Database Schema (1 hour)

### Option A: Quick Fix - Update Code (Recommended)
```python
# In enhanced_campaign_orchestrator.py, timing_probability_engine.py, etc.
# Change all references from:
supabase.table('contractors')
# To:
supabase.table('contractor_leads')

# Update column names:
'status' → 'lead_status'
'business_name' → 'company_name'
```

### Option B: Database Fix - Apply Migrations
```bash
cd ai-agents/database/migrations
# Apply these in order:
psql < 006_contractor_tiers_timing.sql
psql < 007_contractor_job_tracking.sql  
psql < 008_campaign_escalations.sql
```

## 🎯 Priority 2: Add API Endpoints (1 hour)

### File: `ai-agents/main.py`

Add these imports:
```python
from agents.orchestration.timing_probability_engine import ContractorOutreachCalculator, UrgencyLevel
from agents.orchestration.enhanced_campaign_orchestrator import EnhancedCampaignOrchestrator, CampaignRequest
from agents.orchestration.check_in_manager import CampaignCheckInManager
```

Add these endpoints:
```python
# 1. Calculate timing strategy
@app.post("/api/timing/calculate")
async def calculate_timing_strategy(request: dict):
    """Calculate how many contractors to contact based on timeline"""
    calculator = ContractorOutreachCalculator()
    strategy = calculator.calculate_outreach_strategy(
        bids_needed=request.get('bids_needed', 4),
        timeline_hours=request.get('timeline_hours', 24),
        tier1_available=request.get('tier1_available', 10),
        tier2_available=request.get('tier2_available', 30),
        tier3_available=request.get('tier3_available', 100)
    )
    return {
        "total_contractors": strategy.total_to_contact,
        "expected_responses": strategy.expected_total_responses,
        "confidence": strategy.confidence_score,
        "tier_breakdown": {
            "tier1": strategy.tier1_strategy.to_contact,
            "tier2": strategy.tier2_strategy.to_contact,
            "tier3": strategy.tier3_strategy.to_contact
        }
    }

# 2. Create intelligent campaign
@app.post("/api/campaigns/create-intelligent")
async def create_intelligent_campaign(campaign_data: dict):
    """Create campaign with timing and orchestration"""
    orchestrator = EnhancedCampaignOrchestrator()
    request = CampaignRequest(
        bid_card_id=campaign_data['bid_card_id'],
        project_type=campaign_data['project_type'],
        timeline_hours=campaign_data['timeline_hours'],
        urgency_level=campaign_data.get('urgency_level', 'standard'),
        bids_needed=campaign_data.get('bids_needed', 4)
    )
    result = await orchestrator.create_intelligent_campaign(request)
    return result

# 3. Check campaign status
@app.get("/api/campaigns/{campaign_id}/check-in")
async def check_campaign_status(campaign_id: str):
    """Check if campaign needs escalation"""
    manager = CampaignCheckInManager()
    status = await manager.check_campaign_status(campaign_id)
    return status
```

## 🎯 Priority 3: Test Components (30 min)

### Test 1: Timing Engine Standalone
```bash
cd ai-agents
python -m agents.orchestration.timing_probability_engine
# Should see contractor calculations
```

### Test 2: API Endpoints
```bash
# Start server
python main.py

# Test timing calculation
curl -X POST http://localhost:8008/api/timing/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "bids_needed": 4,
    "timeline_hours": 24,
    "tier1_available": 5,
    "tier2_available": 20,
    "tier3_available": 100
  }'
```

### Test 3: Database Connection
```python
# Create test_database_schema.py
from database_simple import SupabaseDB

db = SupabaseDB()
# Test contractor_leads table
contractors = db.table('contractor_leads').select('*').limit(5).execute()
print(f"Found {len(contractors.data)} contractor leads")

# Test if migrations were applied
try:
    tiers = db.table('contractor_tiers').select('*').limit(1).execute()
    print("✅ Contractor tiers view exists")
except:
    print("❌ Need to apply migration 006")
```

## 🎯 Priority 4: Integration Test (30 min)

### Complete Flow Test
```python
# test_complete_integration.py
async def test_complete_flow():
    # 1. Create bid card (Agent 1's domain)
    bid_card_id = "test-kitchen-remodel-123"
    
    # 2. Calculate timing
    response = requests.post('http://localhost:8008/api/timing/calculate', {
        'bids_needed': 4,
        'timeline_hours': 24
    })
    print(f"Timing: {response.json()}")
    
    # 3. Create campaign
    campaign = requests.post('http://localhost:8008/api/campaigns/create-intelligent', {
        'bid_card_id': bid_card_id,
        'project_type': 'Kitchen Remodel',
        'timeline_hours': 24
    })
    print(f"Campaign: {campaign.json()}")
    
    # 4. Check status
    campaign_id = campaign.json()['campaign_id']
    status = requests.get(f'http://localhost:8008/api/campaigns/{campaign_id}/check-in')
    print(f"Status: {status.json()}")
```

## 📊 Current State vs Target State

### Current State:
- ✅ Components built but isolated
- ❌ No API access to timing system
- ❌ Database queries failing
- ❌ Can't create intelligent campaigns

### Target State After Integration:
- ✅ API endpoints expose timing calculations
- ✅ Database queries work properly
- ✅ Campaigns use timing engine automatically
- ✅ Check-ins monitor progress
- ✅ Auto-escalation when behind schedule

## 🚀 Quick Start Commands

```bash
# 1. Fix database schema in code (Option A)
cd ai-agents/agents/orchestration
# Update all files to use contractor_leads table

# 2. Add endpoints to main.py
cd ai-agents
# Edit main.py with new endpoints

# 3. Test everything
python main.py
python test_complete_integration.py

# 4. If all works, test with real bid card
python test_real_bid_card_flow.py
```

## ⚠️ Watch Out For

1. **Database Connection**: Make sure SUPABASE_URL and SUPABASE_ANON_KEY are in .env
2. **Import Paths**: The orchestration modules need proper imports in main.py
3. **Async/Await**: Some methods are async, handle properly in endpoints
4. **Schema Names**: contractor_leads vs contractors confusion

## 🎯 Success Criteria

You'll know integration is complete when:
1. `/api/timing/calculate` returns contractor counts
2. `/api/campaigns/create-intelligent` creates campaign with check-ins
3. Database queries don't throw column errors
4. End-to-end test passes: bid card → timing → campaign → monitoring
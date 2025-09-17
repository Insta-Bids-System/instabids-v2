# InstaBids System Architecture: LLM Integration Points

## Current System Reality Check

### ✅ Components with REAL LLM APIs (Working)
1. **CIA (Customer Interface Agent)** - Uses Claude Opus 4
   - Real API: Anthropic Claude API
   - Purpose: Understands homeowner requests, extracts project details
   - Example: "I need my lawn mowed weekly" → Extracts service type, frequency, location

### ✅ Components That Are Code-Only (Working but No LLM)
1. **JAA (Job Assessment Agent)** - Pure code logic
   - Creates bid cards from CIA's extracted data
   - Saves to database
   - No LLM needed - just data transformation

2. **CDA (Contractor Discovery Agent)** - Database queries only
   - Searches contractor database by location/service
   - Applies tier classification (1/2/3)
   - No LLM needed - just SQL queries

3. **Enhanced Campaign Orchestrator** - Mathematical formulas
   - Calculates how many contractors to contact (5/10/15 rule)
   - Schedules check-ins at 25%, 50%, 75%
   - No LLM needed - pure business logic

4. **Timing & Probability Engine** - Statistical calculations
   - Response rates: Tier 1 (90%), Tier 2 (50%), Tier 3 (33%)
   - Urgency adjustments
   - No LLM needed - mathematical models

### ⚠️ Components That SHOULD Use LLMs (Currently Template-Based)

1. **EAA (External Acquisition Agent)** - Currently uses templates
   - **Current**: "We have a {project_type} project..."
   - **Should be**: Claude writes unique emails for each contractor
   - **Integration needed**: Add Claude API call in `create_personalized_email()`

2. **WFA (Website Form Automation Agent)** - Currently uses fixed mapping
   - **Current**: Maps fields by HTML attributes
   - **Should be**: Claude understands any form layout
   - **Integration needed**: Add Claude API call in `analyze_form_fields()`

3. **Check-in Manager** - Currently uses thresholds
   - **Current**: if responses < expected: escalate
   - **Should be**: Claude analyzes quality and makes decisions
   - **Integration needed**: Add Claude API call in `evaluate_campaign_health()`

## How the System Currently Works

### 1. Campaign Creation Flow
```
Homeowner → CIA (Claude) → JAA (code) → CDA (database) → Orchestrator (math)
```

### 2. Contractor Outreach Flow
```
Orchestrator → EAA (templates) → Email/SMS/Web Forms
                ↓
         Unique tracking URLs
                ↓
         Attribution tracking
```

### 3. Monitoring Flow
```
Time passes → Check-in triggers → Compare actual vs expected → Escalate if needed
```

## Where to Add LLM Intelligence

### Priority 1: Email Writing (EAA)
```python
# Current (template-based)
def create_email(contractor, project):
    return f"We have a {project.type} project..."

# Should be (LLM-powered)
async def create_email(contractor, project):
    prompt = f"""
    Write a personalized email to {contractor.name} at {contractor.company}.
    Project: {project.details}
    Their specialties: {contractor.services}
    Make it compelling and unique.
    """
    return await claude_api.generate(prompt)
```

### Priority 2: Form Understanding (WFA)
```python
# Should add Claude for complex forms
async def understand_form(form_html):
    prompt = f"""
    Analyze this HTML form and identify:
    - What each field is for
    - Required vs optional
    - Best values to submit
    Form: {form_html}
    """
    return await claude_api.analyze(prompt)
```

### Priority 3: Campaign Intelligence
```python
# Should add Claude for decisions
async def evaluate_campaign(metrics):
    prompt = f"""
    Campaign status: {metrics}
    Should we escalate? Consider:
    - Contractor quality vs quantity
    - Project urgency
    - Historical patterns
    """
    return await claude_api.decide(prompt)
```

## Testing the Current System

### Test Emails with Real Personalization
```bash
cd ai-agents
python test_mcp_email_integration.py
# Currently sends template emails via MCP
# Should send Claude-written emails
```

### Test Form Automation
```bash
python test_wfa_complete_demo.py
# Currently uses fixed field mapping
# Should use Claude to understand forms
```

### Test Check-ins and Notifications
```bash
python test_checkin_demo.py
# Shows how system monitors campaigns
# Currently rule-based, should be Claude-powered
```

## The Big Picture

### What's Real (LLM-Powered)
- CIA: Claude Opus understands homeowners ✅

### What's Automated (Code-Only)
- JAA: Creates bid cards ✅
- CDA: Finds contractors ✅
- Orchestrator: Manages campaigns ✅
- Timing Engine: Calculates strategy ✅

### What Needs LLM Enhancement
- EAA: Should write unique emails ⚠️
- WFA: Should understand any form ⚠️
- Check-ins: Should make intelligent decisions ⚠️

## How to Add Claude to Missing Pieces

1. **Import Claude client**
   ```python
   from anthropic import Anthropic
   client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
   ```

2. **Add to email generation**
   - File: `agents/eaa/outreach_channels/email_channel.py`
   - Method: `create_personalized_email()`
   - Add Claude call to write unique content

3. **Add to form analysis**
   - File: `agents/wfa/agent.py`
   - Method: `analyze_form_fields()`
   - Add Claude call to understand forms

4. **Add to decision making**
   - File: `agents/orchestration/check_in_manager.py`
   - Method: `evaluate_campaign_health()`
   - Add Claude call for intelligent decisions

## Summary

**Current State**: We have one intelligent agent (CIA) and lots of automation
**Goal State**: Multiple intelligent agents making contextual decisions
**Gap**: Need to add Claude API calls to EAA, WFA, and Check-in Manager

The infrastructure is all there - we just need to replace templates and rules with Claude intelligence.
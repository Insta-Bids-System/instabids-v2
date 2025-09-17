# COIA SYSTEM REQUIREMENTS - MUST BE 100% COMPLETE

## ABSOLUTE REQUIREMENTS - NO EXCEPTIONS

### 1. STREAMING TECHNOLOGY
- [ ] GPT-5 primary model with streaming
- [ ] GPT-4o automatic fallback when GPT-5 fails
- [ ] Real-time token-by-token streaming
- [ ] NO FAKE RESPONSES - ONLY REAL LLM

### 2. CONTRACTOR ONBOARDING LOGIC
- [ ] Web search for business information
- [ ] Build complete contractor profile
- [ ] Save contractor to database (contractor_leads table)
- [ ] Search matching bid cards
- [ ] Return bid cards to contractor
- [ ] ALL TOOLS MUST BE REAL - NO HARDCODED DATA

### 3. FRONTEND INTEGRATION POINTS (BOTH REQUIRED)

#### A. BID CARD ENTRY POINT
- [ ] Contractor clicks from specific bid card
- [ ] Lands on COIA onboarding WITH bid card context
- [ ] COIA knows which bid card they came from
- [ ] Shows relevant bid cards based on their expertise
- [ ] URL: `/contractor/coia-onboarding?bid_card_id=XXX`

#### B. GENERIC CONTRACTOR LANDING PAGE
- [ ] Contractor comes from main website
- [ ] Lands on COIA onboarding WITHOUT bid card context
- [ ] COIA asks about their business
- [ ] Creates full profile from scratch
- [ ] URL: `/contractor/coia-onboarding`

### 4. BOTH ENTRY POINTS MUST:
- [ ] Use the SAME COIA endpoint
- [ ] Have the SAME streaming capabilities
- [ ] Use the SAME GPT-5/GPT-4o fallback
- [ ] Save to the SAME database
- [ ] Create the SAME contractor profiles

### 5. END-TO-END TESTING PROOF REQUIRED
- [ ] Start from bid card → COIA conversation → Profile created → Saved to DB
- [ ] Start from main page → COIA conversation → Profile created → Saved to DB
- [ ] Verify GPT-5 streaming works
- [ ] Verify GPT-4o fallback works
- [ ] Check database has contractor saved
- [ ] Confirm bid cards are returned

## WHAT IS NOT ACCEPTABLE
- ❌ Partial implementations
- ❌ "It should work" without testing
- ❌ Different endpoints for different entry points
- ❌ Hardcoded responses
- ❌ Fake data
- ❌ Multiple versions of the same thing
- ❌ Backup endpoints
- ❌ Alternative implementations
- ❌ "For future use" code

## DEFINITION OF DONE
✅ BOTH entry points work
✅ SAME endpoint handles both
✅ GPT-5 with GPT-4o fallback active
✅ Real web search executed
✅ Real database saves confirmed
✅ Real bid cards returned
✅ Tested end-to-end with screenshots/proof
✅ NO confusion-causing code left anywhere

## THE SYSTEM WE'RE BUILDING

**ONE COIA SYSTEM** that:
1. Takes contractors from ANY entry point
2. Has intelligent conversation using GPT-5/GPT-4o
3. Builds their profile using REAL tools
4. Saves them to the REAL database
5. Shows them REAL bid cards
6. Works 100% end-to-end

Nothing less is acceptable.
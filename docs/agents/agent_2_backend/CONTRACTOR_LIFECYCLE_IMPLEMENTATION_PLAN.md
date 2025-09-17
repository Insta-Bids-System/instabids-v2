# Contractor Lifecycle Implementation Plan
**Fix the Complete Data Flow from Discovery to Active Contractor**
**Priority**: HIGH - Required for business model to work

## 🎯 **IMPLEMENTATION PHASES**

### **PHASE 1: Fix Current System (1-2 days)** ⚠️ IMMEDIATE
**Goal**: Make discovery → outreach → response tracking work seamlessly

#### **Task 1.1: Run Foreign Key Migration**
```bash
# Execute the migration to fix table references
psql -f database/migrations/009_add_test_flags_and_fix_fks.sql
```

#### **Task 1.2: Implement Enrichment Flow-Back**
**File**: `agents/enrichment/langchain_mcp_enrichment_agent.py`
**Add this method**:
```python
def update_contractor_after_enrichment(self, contractor_id: str, enrichment_data: dict):
    """Flow enrichment results back to potential_contractors table"""
    try:
        update_data = {
            'lead_status': 'enriched',
            'enrichment_data': enrichment_data,
            'last_enriched_at': datetime.now().isoformat()
        }
        
        # Update specific fields if found
        if 'license_verified' in enrichment_data:
            update_data['license_verified'] = enrichment_data['license_verified']
        if 'insurance_verified' in enrichment_data:
            update_data['insurance_verified'] = enrichment_data['insurance_verified']
        if 'rating' in enrichment_data:
            update_data['rating'] = enrichment_data['rating']
        if 'review_count' in enrichment_data:
            update_data['review_count'] = enrichment_data['review_count']
            
        result = self.supabase.table('potential_contractors')\
            .update(update_data)\
            .eq('id', contractor_id)\
            .execute()
            
        print(f"✅ Updated contractor {contractor_id} with enrichment data")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update contractor {contractor_id}: {e}")
        return False
```

#### **Task 1.3: Add Automatic Qualification**
**File**: `agents/orchestration/contractor_qualification_agent.py` (NEW FILE)
```python
#!/usr/bin/env python3
"""
Contractor Qualification Agent
Automatically qualifies or disqualifies contractors based on enriched data
"""

import os
from datetime import datetime
from typing import Dict, List
from supabase import create_client
from dotenv import load_dotenv

class ContractorQualificationAgent:
    def __init__(self):
        load_dotenv(override=True)
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'), 
            os.getenv('SUPABASE_ANON_KEY')
        )
    
    def qualify_all_enriched_contractors(self) -> Dict[str, int]:
        """Qualify all contractors with 'enriched' status"""
        try:
            # Get all enriched contractors
            result = self.supabase.table('potential_contractors')\
                .select('*')\
                .eq('lead_status', 'enriched')\
                .execute()
            
            qualified_count = 0
            disqualified_count = 0
            
            for contractor in result.data:
                qualification = self._evaluate_contractor(contractor)
                
                if qualification['status'] == 'qualified':
                    qualified_count += 1
                elif qualification['status'] == 'disqualified':
                    disqualified_count += 1
                    
                # Update contractor status
                self.supabase.table('potential_contractors').update({
                    'lead_status': qualification['status'],
                    'disqualification_reason': qualification.get('reason'),
                    'qualification_score': qualification['score']
                }).eq('id', contractor['id']).execute()
            
            return {
                'qualified': qualified_count,
                'disqualified': disqualified_count,
                'total_processed': len(result.data)
            }
            
        except Exception as e:
            print(f"Error qualifying contractors: {e}")
            return {'error': str(e)}
    
    def _evaluate_contractor(self, contractor: dict) -> dict:
        """Evaluate a single contractor for qualification"""
        score = 0
        reasons = []
        
        # Lead score (40 points max)
        lead_score = contractor.get('lead_score', 0)
        score += min(lead_score * 0.4, 40)
        
        # License verification (25 points)
        if contractor.get('license_verified'):
            score += 25
        else:
            reasons.append("License not verified")
        
        # Insurance verification (15 points)
        if contractor.get('insurance_verified'):
            score += 15
        else:
            reasons.append("Insurance not verified")
            
        # Rating and reviews (20 points)
        rating = contractor.get('rating', 0)
        review_count = contractor.get('review_count', 0)
        
        if rating >= 4.5 and review_count >= 10:
            score += 20
        elif rating >= 4.0 and review_count >= 5:
            score += 15
        elif rating >= 3.5:
            score += 10
        else:
            reasons.append("Low rating or insufficient reviews")
        
        # Determine qualification
        if score >= 70:
            return {
                'status': 'qualified',
                'score': score,
                'reason': None
            }
        elif score >= 40:
            return {
                'status': 'enriched',  # Stay enriched, needs improvement
                'score': score,
                'reason': f"Score {score} needs improvement: {', '.join(reasons)}"
            }
        else:
            return {
                'status': 'disqualified',
                'score': score,
                'reason': f"Score {score} too low: {', '.join(reasons)}"
            }

# Test function
if __name__ == "__main__":
    agent = ContractorQualificationAgent()
    results = agent.qualify_all_enriched_contractors()
    print(f"Qualification Results: {results}")
```

### **PHASE 2: Interest Classification (2-3 days)** 📈
**Goal**: Automatically promote responsive contractors to Tier 1

#### **Task 2.1: Add Interest Classification Logic**
**File**: `agents/orchestration/contractor_interest_classifier.py` (NEW FILE)
```python
#!/usr/bin/env python3
"""
Contractor Interest Classifier
Identifies interested contractors based on engagement patterns
"""

class ContractorInterestClassifier:
    def classify_interested_contractors(self) -> Dict[str, int]:
        """Find and classify interested contractors"""
        try:
            # Find contractors with positive engagement
            result = self.supabase.table('contractor_engagement_summary')\
                .select('contractor_lead_id, positive_responses, engagement_score, total_responses')\
                .gte('positive_responses', 1)\
                .execute()
            
            interested_count = 0
            
            for engagement in result.data:
                contractor_id = engagement['contractor_lead_id']
                
                # Classification criteria
                is_highly_interested = (
                    engagement['positive_responses'] >= 2 or
                    engagement['engagement_score'] >= 80 or
                    (engagement['positive_responses'] == 1 and engagement['total_responses'] == 1)
                )
                
                if is_highly_interested:
                    # Promote to interested status and Tier 1
                    self.supabase.table('potential_contractors').update({
                        'lead_status': 'interested',
                        'tier': 1,
                        'last_interest_shown_at': datetime.now().isoformat()
                    }).eq('id', contractor_id).execute()
                    
                    interested_count += 1
            
            return {
                'newly_interested': interested_count,
                'total_evaluated': len(result.data)
            }
            
        except Exception as e:
            return {'error': str(e)}
```

### **PHASE 3: Active Contractor Conversion (3-5 days)** 🎯
**Goal**: Convert interested contractors to paying platform members

#### **Task 3.1: Create Contractors Table**
**File**: `database/migrations/010_create_contractors_table.sql`
```sql
-- Active Contractors Table (Platform Members)
CREATE TABLE contractors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source tracking
    contractor_source_id UUID REFERENCES potential_contractors(id),
    conversion_campaign_id UUID REFERENCES outreach_campaigns(id),
    converted_at TIMESTAMP DEFAULT NOW(),
    
    -- Business Identity
    company_name VARCHAR(255) NOT NULL,
    legal_business_name VARCHAR(255),
    business_type VARCHAR(50) DEFAULT 'unknown',
    
    -- Primary Contact
    primary_contact_name VARCHAR(255) NOT NULL,
    primary_email VARCHAR(255) UNIQUE NOT NULL,
    primary_phone VARCHAR(20) NOT NULL,
    
    -- Account Status
    status VARCHAR(20) DEFAULT 'pending',
    onboarding_status VARCHAR(50) DEFAULT 'started',
    subscription_plan VARCHAR(50) DEFAULT 'trial',
    subscription_status VARCHAR(20) DEFAULT 'trial',
    
    -- Verification
    license_number VARCHAR(100),
    license_verified BOOLEAN DEFAULT FALSE,
    insurance_carrier VARCHAR(255),
    insurance_verified BOOLEAN DEFAULT FALSE,
    
    -- Platform Integration
    stripe_account_id VARCHAR(255),
    profile_completeness INT DEFAULT 0,
    
    -- Test flag
    is_test_contractor BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_contractors_status ON contractors(status, onboarding_status);
CREATE INDEX idx_contractors_source ON contractors(contractor_source_id);
CREATE INDEX idx_contractors_test ON contractors(is_test_contractor);
```

#### **Task 3.2: Implement Conversion Logic**
**File**: `agents/conversion/contractor_conversion_agent.py` (NEW FILE)
```python
#!/usr/bin/env python3
"""
Contractor Conversion Agent  
Converts interested contractors to active platform members
"""

class ContractorConversionAgent:
    def convert_interested_contractor(self, contractor_id: str, 
                                    conversion_data: dict = None) -> Dict[str, any]:
        """Convert a potential contractor to active contractor"""
        try:
            # Get the potential contractor data
            potential = self.supabase.table('potential_contractors')\
                .select('*')\
                .eq('id', contractor_id)\
                .eq('lead_status', 'interested')\
                .limit(1)\
                .execute()
            
            if not potential.data:
                return {'success': False, 'error': 'Contractor not found or not interested'}
            
            contractor_data = potential.data[0]
            
            # Create active contractor record
            active_contractor = {
                'contractor_source_id': contractor_id,
                'company_name': contractor_data['company_name'],
                'legal_business_name': contractor_data.get('company_name'),
                'primary_contact_name': contractor_data.get('contact_name', 'Unknown'),
                'primary_email': contractor_data['email'],
                'primary_phone': contractor_data['phone'],
                'license_number': contractor_data.get('license_number'),
                'license_verified': contractor_data.get('license_verified', False),
                'status': 'pending',
                'onboarding_status': 'started',
                'is_test_contractor': contractor_data.get('is_test_contractor', False)
            }
            
            # Override with any provided conversion data
            if conversion_data:
                active_contractor.update(conversion_data)
            
            # Insert new active contractor
            result = self.supabase.table('contractors')\
                .insert(active_contractor)\
                .execute()
            
            if result.data:
                new_contractor_id = result.data[0]['id']
                
                # Update potential contractor status
                self.supabase.table('potential_contractors').update({
                    'lead_status': 'converted',
                    'converted_to_contractor_at': datetime.now().isoformat(),
                    'active_contractor_id': new_contractor_id
                }).eq('id', contractor_id).execute()
                
                # Create contractor memory profile
                self._create_contractor_memory_profile(new_contractor_id, contractor_data)
                
                return {
                    'success': True,
                    'contractor_id': new_contractor_id,
                    'onboarding_required': True
                }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_contractor_memory_profile(self, contractor_id: str, source_data: dict):
        """Create initial memory profile for new contractor"""
        # This will integrate with contractor LLM memory system
        memory_profile = {
            'contractor_id': contractor_id,
            'business_context': {
                'company_name': source_data.get('company_name'),
                'specialties': source_data.get('specialties', []),
                'service_area': f"{source_data.get('city')}, {source_data.get('state')}",
                'years_in_business': source_data.get('years_in_business'),
                'company_size': source_data.get('contractor_size')
            },
            'performance_metrics': {
                'initial_lead_score': source_data.get('lead_score'),
                'response_tier': source_data.get('tier'),
                'engagement_history': 'Retrieved from engagement_summary'
            },
            'communication_preferences': {
                'preferred_channel': 'email',  # Default, will be learned
                'response_pattern': 'Unknown'   # Will be analyzed
            }
        }
        
        # TODO: Integrate with contractor memory system
        print(f"🧠 Created memory profile for contractor {contractor_id}")
        return memory_profile
```

### **PHASE 4: Contractor Memory & Profile System (5-7 days)** 🧠
**Goal**: Full contractor LLM memory and relationship management

#### **Components Needed**:
1. **Contractor Memory Tables** - Store conversation history, preferences, project history
2. **Contractor LLM Agent** - Personalized AI assistant for each contractor
3. **Profile Management** - Dashboard, onboarding, subscription management
4. **Relationship Tracking** - Project history, performance metrics, satisfaction scores

---

## 🎯 **IMMEDIATE NEXT STEPS** 

### **Week 1: Fix Current System**
1. ✅ Run foreign key migration
2. ✅ Implement enrichment flow-back
3. ✅ Add automatic qualification logic
4. ✅ Test with fake contractors

### **Week 2: Add Missing Lifecycle Stages**  
1. ✅ Implement interest classification
2. ✅ Create contractors table
3. ✅ Build conversion logic
4. ✅ Test complete flow: discovery → conversion

### **Week 3+: Advanced Features**
1. 📋 Contractor memory system
2. 📋 LLM-powered contractor agents
3. 📋 Profile management dashboard
4. 📋 Performance analytics

**You were 100% correct** - the data flow had major gaps that would prevent the business model from working. This implementation plan fixes the complete contractor lifecycle from discovery to active paying contractors.
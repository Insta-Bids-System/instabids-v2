# Contractor Pattern Analysis System - BUILD LATER
**Created**: January 14, 2025  
**Purpose**: Aggregate patterns across contractor types to improve platform intelligence
**Status**: Future development (after contractor memory system)

## 🎯 OVERVIEW

This system analyzes patterns ACROSS all contractors of the same type (roofers, plumbers, etc.) to understand common information needs, pricing patterns, and communication preferences. It will help the platform automatically know what information to collect for different project types.

## 🔍 WHAT THIS SYSTEM DOES

### **Pattern Recognition Across Contractor Types**
- If 87% of roofers ask for attic photos → System auto-requests them
- If 92% of plumbers need crawlspace access info → Add to bid card template
- If kitchen contractors average 25% higher bids without appliance specs → Flag it

### **Messaging Intelligence**
- Track all RFI (Request for Information) patterns
- Identify common questions by trade type
- Understand what reduces "unknowns" pricing padding

## 📊 SYSTEM ARCHITECTURE

### **New Tables for Pattern Analysis**

#### **1. contractor_type_patterns**
**Purpose**: Aggregated intelligence by contractor specialty
```sql
CREATE TABLE contractor_type_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_type VARCHAR(100) NOT NULL,  -- 'roofing', 'plumbing', 'kitchen_remodel'
    pattern_data JSONB NOT NULL DEFAULT '{}',
    sample_size INTEGER DEFAULT 0,
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(contractor_type)
);
```

**Example Pattern Data**:
```json
{
  "contractor_type": "roofing",
  "common_rfi_patterns": {
    "photos_always_requested": [
      {"type": "all_roof_angles", "frequency": "93%", "impact": "-15% bid variance"},
      {"type": "attic_access", "frequency": "87%", "impact": "-20% risk padding"},
      {"type": "gutters", "frequency": "76%", "impact": "-5% bid variance"}
    ],
    "questions_always_asked": [
      {"question": "Age of current roof?", "frequency": "95%"},
      {"question": "Any active leaks?", "frequency": "89%"},
      {"question": "Previous repairs?", "frequency": "72%"}
    ],
    "pricing_patterns": {
      "base_calculation": "sqft * $4.50-6.50",
      "common_adjustments": {
        "2+ story": "+15-25%",
        "steep pitch": "+20-30%",
        "winter": "+10-15%"
      }
    },
    "information_impact": {
      "complete_info_reduces_bid": "15-20% average",
      "missing_attic_photos_adds": "20-25% padding",
      "no_damage_disclosure_adds": "30% padding"
    }
  },
  "sample_size": 47,
  "confidence_score": 0.89
}
```

#### **2. message_pattern_analysis**
**Purpose**: Track messaging patterns and RFIs from actual conversations
```sql
CREATE TABLE message_pattern_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_card_id UUID REFERENCES bid_cards(id),
    contractor_id UUID REFERENCES contractors(id),
    contractor_type VARCHAR(100),
    message_type VARCHAR(50),  -- 'rfi', 'clarification', 'negotiation'
    message_content TEXT,
    extracted_patterns JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **3. rfi_template_library**
**Purpose**: Auto-generated RFI templates based on patterns
```sql
CREATE TABLE rfi_template_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_type VARCHAR(100),
    rfi_category VARCHAR(100),  -- 'photos', 'measurements', 'conditions'
    template_content TEXT,
    usage_frequency INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2),
    auto_trigger_rules JSONB,  -- When to automatically request this
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 🔄 HOW IT WORKS

### **Data Collection Phase**

#### **1. From Messaging System**
Every message between homeowner and contractor gets analyzed:
```python
async def analyze_message_for_patterns(message_data):
    # Identify if it's an RFI
    if is_rfi(message_data):
        # Extract what they're asking for
        patterns = extract_rfi_patterns(message_data)
        
        # Store in message_pattern_analysis
        await store_pattern({
            'contractor_id': message_data.contractor_id,
            'contractor_type': get_contractor_type(contractor_id),
            'message_type': 'rfi',
            'extracted_patterns': {
                'photos_requested': ['attic', 'electrical_panel'],
                'measurements_needed': ['exact_sqft', 'ceiling_height'],
                'questions_asked': ['water_damage', 'last_renovation']
            }
        })
```

#### **2. From BSA/COIA Conversations**
Pull questions and info needs from AI conversations:
```python
# After each conversation, extract information requests
async def extract_info_requests_from_conversation(conversation):
    questions_asked = extract_questions(conversation)
    info_requested = extract_information_requests(conversation)
    
    # Add to pattern analysis
    await add_to_pattern_analysis(contractor_type, questions_asked, info_requested)
```

### **Pattern Aggregation Phase**

#### **Weekly Pattern Analysis Job**
```python
async def aggregate_contractor_type_patterns():
    contractor_types = ['roofing', 'plumbing', 'electrical', 'kitchen_remodel', etc.]
    
    for contractor_type in contractor_types:
        # Get all patterns for this type from last 90 days
        patterns = await get_patterns_by_type(contractor_type)
        
        # Analyze commonalities
        common_photos = find_common_patterns(patterns, 'photos', threshold=0.6)
        common_questions = find_common_patterns(patterns, 'questions', threshold=0.6)
        
        # Calculate impact on pricing
        pricing_impact = analyze_pricing_correlation(patterns)
        
        # Update contractor_type_patterns table
        await update_contractor_type_patterns({
            'contractor_type': contractor_type,
            'pattern_data': {
                'photos_always_requested': common_photos,
                'questions_always_asked': common_questions,
                'pricing_impact': pricing_impact
            },
            'sample_size': len(patterns),
            'confidence_score': calculate_confidence(patterns)
        })
```

### **Application Phase**

#### **Auto-RFI Generation**
When a homeowner creates a roofing bid card:
```python
async def auto_generate_rfi_checklist(project_type):
    # Get patterns for this project type
    patterns = await get_contractor_type_patterns(project_type)
    
    # Generate checklist
    checklist = {
        'required_photos': patterns['photos_always_requested'],
        'required_info': patterns['questions_always_asked'],
        'nice_to_have': patterns['optional_but_helpful']
    }
    
    # Show to homeowner
    return f"""
    Based on 47 roofing contractors, providing these will get you better bids:
    
    📸 Photos Needed (reduces bids by ~20%):
    - All roof angles
    - Attic access point
    - Current damage areas
    
    📝 Information Needed:
    - Age of current roof: _______
    - Any active leaks: Yes/No
    - Last repair date: _______
    """
```

#### **Bid Optimization Suggestions**
```python
async def suggest_bid_optimization(bid_card_id):
    bid_card = await get_bid_card(bid_card_id)
    patterns = await get_contractor_type_patterns(bid_card.project_type)
    
    missing_info = identify_missing_info(bid_card, patterns)
    
    if missing_info:
        impact = calculate_bid_impact(missing_info, patterns)
        return f"""
        💡 Bid Optimization Tip:
        Adding {missing_info} typically reduces bids by {impact}%
        and increases contractor response rate by 40%.
        """
```

## 📈 USE CASES

### **1. Intelligent Bid Card Templates**
- Auto-populate required fields based on project type
- Pre-fill photo requirements
- Suggest questions homeowners should answer upfront

### **2. Contractor Coaching**
```
"You're asking for 30% more photos than typical roofers.
This might be why your response rate is lower."
```

### **3. Platform Intelligence**
```
"Kitchen remodelers need appliance specs 94% of the time.
Let's add an appliance checklist to kitchen bid cards."
```

### **4. Pricing Transparency**
```
"Providing attic photos reduces roofing bids by 20% on average
because contractors don't need to pad for unknowns."
```

## 🚀 IMPLEMENTATION ROADMAP

### **Phase 1: Data Collection** (Months 1-3)
- Add pattern extraction to messaging system
- Track all RFIs and questions
- Build initial dataset

### **Phase 2: Pattern Analysis** (Months 3-4)
- Create aggregation jobs
- Build pattern recognition algorithms
- Validate patterns with contractors

### **Phase 3: Application** (Months 4-6)
- Auto-RFI generation
- Bid card optimization
- Contractor coaching tools

### **Phase 4: Machine Learning** (Months 6+)
- Predictive bid modeling
- Automatic template evolution
- Response rate optimization

## 📊 SUCCESS METRICS

- 50%+ reduction in RFI messages
- 20%+ more accurate initial bids
- 30%+ higher contractor response rates
- 15%+ reduction in bid variance

## 🔗 INTEGRATION WITH CONTRACTOR MEMORY

This system works **alongside** the contractor memory system:
- **Contractor Memory**: Individual personalization
- **Pattern Analysis**: Platform-wide intelligence

Together they create:
1. Personalized experiences for each contractor
2. Smarter bid cards that get better responses
3. Reduced friction in the bidding process

---

**This is the FUTURE BUILD - focused on platform-wide intelligence through pattern analysis across all contractors of the same type.**
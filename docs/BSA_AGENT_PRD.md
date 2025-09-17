# Bid Submission Agent (BSA) - Product Requirements Document

**Agent**: BSA (Bid Submission Agent)  
**Purpose**: Specialized agent for converting contractor input into standardized bid submissions  
**Status**: Design Phase  
**Priority**: High (Critical for contractor adoption)  

---

## 1. EXECUTIVE SUMMARY

### Problem Statement
Contractors struggle with standardized bid forms that don't match their natural workflow or pricing methodologies. Different trades think about projects in completely different ways, leading to:
- Low bid submission rates
- Poor quality proposals  
- Frustrated contractors who abandon the platform
- Lost revenue from contractors who can't easily engage

### Solution Overview
BSA is a specialized LLM agent that acts as an intelligent translation layer between contractors' natural input methods and InstaBids' standardized bid format. BSA handles multi-modal input (voice, text, PDF, images) and translates contractor expertise into professional proposals.

### Success Metrics
- **Bid Submission Rate**: Increase from current baseline to 75%+
- **Bid Quality Score**: Automated assessment of proposal completeness
- **Time to Submit**: Reduce from 15+ minutes to under 5 minutes
- **Contractor Satisfaction**: Post-submission satisfaction score >4.5/5

---

## 2. SCOPE & BOUNDARIES

### In Scope
- Multi-modal input processing (voice, text, PDF uploads, images)
- Trade-specific workflow adaptation
- Intelligent pricing suggestions and validation
- Group bidding bulk submission support
- Integration with existing COIA agent context
- Professional proposal generation

### Out of Scope (Phase 1)
- Direct CRM integrations (future enhancement)
- Project management functionality
- Payment processing
- Calendar/scheduling integration
- Contractor performance analytics

### Integration Points
- **COIA Agent**: Receives contractor profile and capabilities context
- **Current Bid API**: Outputs to existing `/api/contractor-proposals/submit`
- **Group Bidding System**: Coordinates multi-project submissions
- **Database**: Reads bid card details, writes proposals

---

## 3. USER PERSONAS & USE CASES

### Primary Persona: Mid-Size Contractor
- **Profile**: 5-15 years experience, does 20-50 projects/year
- **Pain Points**: Forms don't match their mental model, takes too long
- **Input Style**: Prefers talking through projects, has existing pricing sheets

### Secondary Persona: Large Contractor with Systems
- **Profile**: Established business, has CRM/estimating software
- **Pain Points**: Data re-entry, format mismatches
- **Input Style**: Wants to upload existing estimates/templates

### Use Cases

#### UC1: Voice-Based Bid Submission
```
Contractor: "Kitchen remodel, about 300 square feet, they want granite 
countertops and custom cabinets. I can do it for around 65k, 
probably take me 8 weeks start to finish."

Expected Output: Complete bid with timeline, detailed proposal, 
technical approach based on contractor profile.
```

#### UC2: PDF Upload Translation
```
Contractor uploads their standard kitchen estimate template.
BSA extracts pricing, maps to bid format, maintains their branding.
```

#### UC3: Group Bidding Coordination
```
Contractor sees 3 similar projects in group bidding.
Input: "I can do all three decks, bulk discount brings it to 85k total."
BSA coordinates pricing across projects, manages timelines.
```

---

## 4. FUNCTIONAL REQUIREMENTS

### 4.1 Input Processing Engine

#### Voice Input Processing
- **Speech-to-Text**: Convert contractor voice input to text
- **NLP Extraction**: Parse pricing, timeline, materials, constraints
- **Context Awareness**: Use COIA profile to fill gaps in information
- **Clarification**: Ask follow-up questions for missing details

#### Text Input Processing  
- **Natural Language**: Handle conversational bid descriptions
- **Structured Input**: Support bullet points, informal estimates
- **Template Recognition**: Learn contractor's typical input patterns

#### Document Processing
- **PDF OCR**: Extract line items, totals, timelines from estimates
- **Image Analysis**: Process photos of similar completed work
- **Format Mapping**: Convert contractor formats to standard bid structure

### 4.2 Translation Engine

#### Trade-Specific Logic
- **Landscaping**: Zone-based pricing (front/back/side yard)
- **Kitchen**: Cabinet linear footage, appliance packages
- **Electrical**: Circuit requirements, code compliance
- **Plumbing**: Fixture schedules, permit requirements
- **HVAC**: Load calculations, equipment sizing

#### Pricing Intelligence
- **Range Validation**: Check if pricing falls within market ranges
- **Completeness Check**: Ensure all project aspects are addressed
- **Profit Margin Analysis**: Suggest adjustments for profitability
- **Competitive Positioning**: Consider market rates by location

#### Professional Proposal Generation
- **Technical Approach**: Generate detailed methodology
- **Timeline Breakdown**: Create realistic phase-based timeline
- **Materials Specification**: List major materials and brands
- **Warranty/Guarantee**: Include standard contractor warranties

### 4.3 Group Bidding Integration

#### Multi-Project Coordination
- **Bulk Pricing**: Calculate savings across multiple projects
- **Timeline Coordination**: Sequence projects efficiently
- **Resource Optimization**: Account for crew and equipment sharing
- **Linked Submissions**: Create separate but coordinated bids

#### Group Selection Interface
- **Project Matching**: Suggest compatible projects for grouping
- **Savings Calculator**: Show potential bulk discounts
- **Timeline Optimizer**: Recommend efficient project sequencing

---

## 5. TECHNICAL ARCHITECTURE

### 5.1 Agent Structure
```
agents/bsa/
├── agent.py                 # Main BSA orchestration
├── input_processors/
│   ├── voice_processor.py   # Speech-to-text + NLP
│   ├── text_processor.py    # Natural language parsing
│   ├── pdf_processor.py     # Document extraction
│   └── image_processor.py   # Visual analysis
├── translation_engine.py    # Core conversion logic
├── trade_adapters/
│   ├── landscaping.py       # Landscaping-specific logic
│   ├── kitchen.py           # Kitchen remodel logic
│   ├── electrical.py        # Electrical work logic
│   └── base_adapter.py      # Common trade functionality
├── pricing_engine.py        # Intelligent pricing analysis
├── group_coordinator.py     # Group bidding logic
└── state_management.py      # BSA conversation state
```

### 5.2 API Design
```python
# Primary BSA endpoint
POST /api/bsa/process-bid
{
  "bid_card_id": "uuid",
  "contractor_id": "uuid", 
  "input_type": "voice|text|pdf|image",
  "input_data": "string|base64|url",
  "session_id": "uuid"  # For multi-turn conversations
}

Response:
{
  "status": "complete|needs_clarification",
  "bid_preview": {
    "amount": 45000,
    "timeline_start": "2025-03-01",
    "timeline_end": "2025-04-15",
    "proposal": "Complete professional proposal...",
    "technical_approach": "Detailed methodology..."
  },
  "clarification_questions": [...],  # If needs_clarification
  "confidence_score": 0.85
}

# Submit processed bid
POST /api/bsa/submit-bid
{
  "session_id": "uuid",
  "approved_bid": {...},
  "contractor_adjustments": {...}
}
```

### 5.3 Integration Points

#### COIA Context Sharing
```python
# BSA requests contractor context from COIA
contractor_context = COIA.get_contractor_context(contractor_id)
{
  "specialties": ["kitchen", "bathroom"],
  "typical_pricing": {"kitchen_sqft": 250},
  "preferred_materials": ["granite", "quartz"],
  "timeline_preferences": "6-8 weeks",
  "past_project_data": [...]
}
```

#### Existing Bid API Compatibility
```python
# BSA outputs to current proposal submission endpoint
POST /api/contractor-proposals/submit
{
  "bid_card_id": "uuid",
  "contractor_id": "uuid",
  "amount": 45000,
  "timeline_start": "2025-03-01T00:00:00Z",
  "timeline_end": "2025-04-15T00:00:00Z", 
  "proposal": "BSA-generated professional proposal",
  "technical_approach": "BSA-generated methodology"
}
```

---

## 6. NON-FUNCTIONAL REQUIREMENTS

### Performance
- **Response Time**: <3 seconds for text processing, <10 seconds for document processing
- **Concurrency**: Support 50+ simultaneous bid processing sessions
- **Accuracy**: 95%+ accuracy in price/timeline extraction from voice input

### Reliability
- **Availability**: 99.5% uptime during business hours
- **Error Handling**: Graceful degradation when processing fails
- **Data Persistence**: All contractor input stored for learning/improvement

### Security
- **Data Protection**: Encrypt contractor pricing/methodology data
- **Access Control**: Only authorized contractors can submit bids
- **Audit Trail**: Log all bid processing activities

### Scalability
- **Horizontal Scaling**: Support increased contractor volume
- **Model Training**: Continuous improvement from contractor feedback
- **Trade Expansion**: Easy addition of new trade-specific adapters

---

## 7. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Weeks 1-2)
- **Core BSA Agent**: Basic text processing and translation
- **COIA Integration**: Context sharing mechanism
- **Basic UI**: Simple text input interface
- **API Framework**: RESTful endpoints for bid processing

### Phase 2: Multi-Modal Input (Weeks 3-4)
- **Voice Processing**: Speech-to-text integration (OpenAI Whisper)
- **PDF Processing**: Document extraction and mapping
- **Enhanced Translation**: Trade-specific pricing logic
- **Quality Assurance**: Bid validation and suggestions

### Phase 3: Intelligence Layer (Weeks 5-6)
- **Pricing Intelligence**: Market rate validation
- **Pattern Learning**: Contractor-specific adaptation
- **Advanced NLP**: Better context understanding
- **Professional Polish**: Enhanced proposal generation

### Phase 4: Group Bidding (Weeks 7-8)
- **Group Coordination**: Multi-project bid processing
- **Bulk Pricing**: Savings calculation across projects
- **Timeline Optimization**: Efficient project sequencing
- **Group Selection UI**: Contractor group management interface

### Phase 5: Advanced Features (Weeks 9-10)
- **Image Processing**: Photo analysis for similar work
- **CRM Integration Framework**: Prepare for external system connections
- **Analytics**: Bid success rate tracking
- **Mobile Optimization**: Responsive design for mobile contractors

---

## 8. SUCCESS CRITERIA

### Technical Success
- [ ] Successfully processes 95%+ of contractor text input
- [ ] Generates professional proposals meeting homeowner standards
- [ ] Integrates seamlessly with existing COIA and bid submission systems
- [ ] Supports group bidding coordination for 3+ projects

### Business Success  
- [ ] Increases contractor bid submission rate by 50%+
- [ ] Reduces average bid submission time by 60%+
- [ ] Achieves 4.5/5+ contractor satisfaction rating
- [ ] Supports 10+ different trade specializations

### User Experience Success
- [ ] Contractors can submit quality bids in under 5 minutes
- [ ] Natural input methods feel intuitive to contractors
- [ ] Generated proposals are indistinguishable from manual submissions
- [ ] Group bidding workflow is clear and beneficial

---

## 9. RISKS & MITIGATION

### Technical Risks
- **LLM Accuracy**: Pricing extraction errors lead to bad bids
  - *Mitigation*: Validation layers, confidence scoring, human review flags
  
- **Integration Complexity**: BSA-COIA data sharing failures
  - *Mitigation*: Clear API contracts, fallback to standalone mode

### Business Risks  
- **Contractor Adoption**: Contractors prefer existing workflows
  - *Mitigation*: Gradual rollout, extensive contractor feedback, hybrid options

- **Quality Concerns**: Generated bids lack professional quality
  - *Mitigation*: Professional templates, quality scoring, iterative improvement

### User Experience Risks
- **Learning Curve**: New interface confuses contractors
  - *Mitigation*: Progressive enhancement, optional advanced features

---

## 10. FUTURE ENHANCEMENTS

### Planned Enhancements (Post-MVP)
- **CRM Integrations**: Direct connections to QuickBooks, JobTread, etc.
- **Mobile-First Interface**: Native mobile app for on-site bidding
- **AI Learning**: Contractor-specific pricing pattern recognition
- **Advanced Analytics**: Bid win rate optimization
- **Voice-Only Mode**: Complete hands-free bid submission

### Potential Integrations
- **Estimating Software**: Buildertrend, CoConstruct, Procore
- **Material Suppliers**: Home Depot, Lowe's, Ferguson pricing APIs
- **Permit Systems**: Municipal permit requirement automation
- **Insurance Verification**: Automated coverage validation

---

**This PRD positions BSA as a critical differentiator that makes InstaBids the most contractor-friendly platform in the market while maintaining system architecture clarity and scalability.**
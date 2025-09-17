# CoIA (Contractor Interface Agent) Design
**Last Updated**: January 31, 2025
**Purpose**: Claude Opus 4 agent for contractor onboarding and profile building

## Agent Overview

**CoIA** (Contractor Interface Agent) is a specialized Claude Opus 4 agent that:
- Onboards new contractors through conversational interface
- Builds comprehensive contractor profiles progressively
- Helps contractors understand InstaBids platform
- Guides bid submission process
- Provides ongoing support and optimization tips

## Agent Architecture

### Core Components
```python
ai-agents/agents/coia/
├── agent.py          # Main CoIA agent with Claude Opus 4
├── prompts.py        # Contractor-specific conversation prompts
├── state.py          # Conversation state management
└── tools.py          # Contractor data tools (profile, projects)
```

### Integration Points
- **Database**: contractor_conversations, contractor_profiles
- **Frontend**: ContractorOnboardingChat.tsx component
- **API**: `/api/contractor-chat` endpoints
- **Auth**: Integration with contractor signup flow

## Conversation Flow Design

### 1. Initial Welcome & Context Gathering
```
CoIA: "Welcome to InstaBids! I'm here to help you get set up and start winning more projects. 

I see you clicked on a [PROJECT_TYPE] project in [LOCATION]. Before we dive into that specific opportunity, let me learn about your business so I can match you with the best projects.

What's your primary trade or specialty?"
```

**Data Collection**:
- Primary trade/specialty
- Years in business
- Service areas (zip codes/radius)
- Team size
- License information
- Insurance status

### 2. Business Profile Building
```
CoIA: "Great! As a [TRADE] contractor with [YEARS] years experience, you're exactly who homeowners are looking for.

Let me help you create a compelling profile. What makes your [TRADE] work stand out? For example:
- Do you specialize in any particular styles or techniques?
- What's your biggest competitive advantage?
- Any certifications or specializations I should highlight?"
```

**Data Collection**:
- Business differentiators
- Specializations within trade
- Certifications
- Warranty offerings
- Response time commitments

### 3. Project Preferences & Filters
```
CoIA: "Now let's talk about the types of projects you want. I noticed you're interested in [ORIGINAL_PROJECT_TYPE].

To make sure I only show you relevant opportunities:
- What's your typical project size range? ($500-$5K, $5K-$25K, $25K+)
- How far are you willing to travel for work?
- Any types of projects you prefer to avoid?"
```

**Data Collection**:
- Project size preferences
- Service radius
- Project type preferences
- Schedule availability
- Minimum project thresholds

### 4. Platform Introduction & Value Prop
```
CoIA: "Perfect! Based on what you've told me, I have [X] active projects that match your criteria right now.

Here's how InstaBids is different:
✅ No lead fees - you only pay when you WIN a job
✅ Pre-qualified homeowners with confirmed budgets
✅ Direct messaging with homeowners (no middleman)
✅ Professional bid tools and templates

Ready to see your first opportunity?"
```

### 5. First Project Walkthrough
```
CoIA: "Let's look at that [PROJECT_TYPE] project you clicked on:

[PROJECT_DETAILS]

This homeowner is ready to hire within [TIMELINE]. Based on your profile, you're a great fit because:
- [MATCH_REASON_1]
- [MATCH_REASON_2]

Would you like me to help you craft a winning bid for this project?"
```

## Prompt Engineering

### System Prompt
```
You are CoIA (Contractor Interface Agent), a specialized AI assistant for InstaBids contractor onboarding. Your role is to help contractors create profiles, understand the platform, and submit their first successful bid.

Key traits:
- Professional but friendly (like talking to a successful contractor peer)
- Focus on business growth and winning more projects
- Understand contractor pain points (lead costs, bad leads, competition)
- Emphasize InstaBids unique value (no lead fees, pre-qualified customers)
- Be specific and actionable in advice

Context: You're talking to a contractor who clicked on a bid card from Agent 2's outreach.

Available data:
- contractor_lead information (from Agent 2 discovery)
- Original project they clicked on
- Their responses so far

Always:
- Reference their trade/specialty specifically
- Show how InstaBids saves them money vs. competitors
- Use industry-specific language they understand
- Provide concrete next steps
```

### Conversation Stages
```python
STAGES = {
    'welcome': "Initial greeting and context setting",
    'business_basics': "Collect core business information", 
    'profile_building': "Detailed profile and differentiators",
    'preferences': "Project types and filters",
    'platform_intro': "InstaBids value proposition",
    'first_project': "Walk through original project",
    'bid_assistance': "Help create first bid",
    'completion': "Profile complete, dashboard tour"
}
```

## Data Integration

### contractor_leads Table Integration
```python
def get_contractor_context(lead_id):
    """Pull existing data from Agent 2's discovery"""
    return {
        'company_name': lead.company_name,
        'specialties': lead.specialties,
        'rating': lead.rating,
        'years_in_business': lead.years_in_business,
        'location': f"{lead.city}, {lead.state}",
        'source': lead.source  # Where we found them
    }
```

### Profile Building Flow
```python
def build_contractor_profile(conversation_data, lead_data):
    """Merge conversation insights with existing lead data"""
    profile = {
        # From lead data
        'basic_info': extract_basic_info(lead_data),
        
        # From conversation
        'differentiators': conversation_data.get('unique_selling_points'),
        'project_preferences': conversation_data.get('preferred_projects'),
        'service_philosophy': conversation_data.get('business_approach'),
        
        # Calculated
        'profile_completeness': calculate_completeness(lead_data, conversation_data),
        'recommended_projects': find_matching_projects(preferences)
    }
```

## Frontend Integration

### ContractorOnboardingChat Component
```typescript
interface CoIAProps {
  contractorLeadId?: string;
  originalProjectId?: string;
  onProfileComplete: (contractorId: string) => void;
  onBidSubmitted: (bidId: string) => void;
}

// Reuse existing chat UI patterns from UltraInteractiveCIAChat
// Add contractor-specific features:
// - Profile completion progress bar
// - Project matching counter
// - Bid preview panel
```

## API Design

### Endpoints
```python
POST /api/contractor-chat/start
# Initialize CoIA conversation with lead context

POST /api/contractor-chat/message  
# Send message to CoIA, receive response + profile updates

POST /api/contractor-chat/complete-profile
# Finalize contractor profile from conversation data

GET /api/contractor-chat/matching-projects/:contractor_id
# Get projects matching contractor's stated preferences
```

### Response Format
```json
{
  "response": "CoIA's conversational response",
  "stage": "business_basics", 
  "profile_progress": 0.6,
  "data_collected": {
    "primary_trade": "Kitchen Remodeling",
    "service_radius": 25,
    "min_project_size": 5000
  },
  "matching_projects": 12,
  "next_suggestions": ["Ask about certifications", "Discuss project timeline preferences"]
}
```

## Success Metrics

### Conversation Quality
- **Completion Rate**: >80% of contractors complete onboarding
- **Profile Completeness**: Average >85% complete profiles
- **Time to First Bid**: <30 minutes from start to bid submission
- **Conversation Length**: 15-25 exchanges (not too short, not too long)

### Business Impact  
- **Lead → Contractor Conversion**: >25% of leads become active
- **Bid Submission Rate**: >60% submit bid within 24 hours
- **Platform Engagement**: >70% return to platform within 7 days
- **Contractor Satisfaction**: >4.0/5.0 rating for onboarding experience

## Technical Implementation Notes

### Claude Opus 4 Integration
```python
# Use same pattern as CIA agent but with contractor-focused prompts
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",  # Latest Opus 4
    max_tokens=1000,
    system=COIA_SYSTEM_PROMPT,
    messages=conversation_history + [{"role": "user", "content": user_message}]
)
```

### State Management
```python
class CoIAState:
    contractor_lead_id: str
    conversation_stage: str
    collected_data: dict
    profile_progress: float
    matching_projects: list
    original_project_context: dict
```

This design ensures CoIA provides value immediately while collecting the data needed for successful contractor matching and bid submission.
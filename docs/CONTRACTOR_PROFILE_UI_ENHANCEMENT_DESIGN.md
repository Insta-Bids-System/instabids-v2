# Contractor Profile UI Enhancement Design

## Current State Analysis

### Database Schema (What We Can Store)
We have THREE comprehensive tables for contractor data:

1. **contractors table** - Basic profile and performance metrics
2. **contractor_leads table** - Detailed business information  
3. **potential_contractors table** - Discovery and enrichment data

### Current UI (What We're Actually Collecting)
The existing UI only collects:
- Company name
- Email 
- Password
- Basic contact info

**MASSIVE GAP**: We're collecting <10% of what the database can store!

## Enhanced Profile UI Design

### Phase 1: Intelligent Conversational Onboarding
When contractor says "I'm [Company Name] from [Location]", the COIA agent should:

```typescript
// Automatic Research Flow
1. Extract company name and location
2. Trigger WebSearch for:
   - Company website
   - Google Business listing  
   - Social media profiles
   - Better Business Bureau listing
3. Present findings: "Is this your business?"
   - Show website URL
   - Display phone number from Google
   - Show business hours
   - Display ratings/reviews
4. Ask: "Should I import this information to your profile?"
```

### Phase 2: Progressive Profile Building

#### Step 1: Business Verification
```
COIA: "I found your business! Let me verify some details:"
- Company: Turf Grass Artificial Solutions ✓
- Website: turfgrassartificialsolutions.com ✓
- Phone: [from Google listing]
- Address: [from Google listing]

"Is this information correct? Any updates?"
```

#### Step 2: Service Area Configuration
```
COIA: "Let's set up your service area. You're based in South Florida."

"How far are you willing to travel for jobs?"
- [ ] 10 miles
- [ ] 25 miles  
- [ ] 50 miles
- [ ] 100+ miles
- [ ] Custom: ___

"Which zip codes do you primarily serve?" 
[Interactive map showing radius from business location]

"Any specific neighborhoods or areas you specialize in?"
```

#### Step 3: Service Categories & Specializations
```
COIA: "What types of projects do you handle?"

Primary Category:
- [ ] Landscaping
- [ ] Artificial Turf Installation
- [ ] Lawn Care
- [ ] Hardscaping

Specific Services: (check all that apply)
- [ ] Residential artificial turf
- [ ] Commercial installations
- [ ] Sports fields
- [ ] Pet-friendly turf
- [ ] Putting greens
- [ ] Maintenance & repairs

"What's your sweet spot for project size?"
- Minimum job: $____
- Ideal job: $____
- Maximum job: $____
```

#### Step 4: Capacity & Availability
```
COIA: "Help me understand your capacity:"

"How many projects can you handle simultaneously?"
- [ ] 1-2 projects
- [ ] 3-5 projects
- [ ] 6-10 projects
- [ ] 10+ projects

"Current availability:"
- [ ] Immediately available
- [ ] Available within a week
- [ ] Booked 2-4 weeks out
- [ ] Custom schedule

"Typical response time to new inquiries?"
- [ ] Within 1 hour
- [ ] Same day
- [ ] Next business day
- [ ] 2-3 days
```

#### Step 5: Credentials & Trust Factors
```
COIA: "Let's add credentials that build trust:"

"Business details:"
- Years in business: [auto-filled from research]
- Number of employees: ___
- License number: ___
- Insurance coverage: $___

"Certifications:" (we can verify these)
- [ ] State contractor license
- [ ] Manufacturer certifications
- [ ] Industry associations
- [ ] Safety certifications
```

### Phase 3: Profile Display UI

#### Contractor Dashboard View
```jsx
// ContractorProfile.tsx
<div className="contractor-profile">
  {/* Hero Section */}
  <ProfileHero>
    <CompanyLogo />
    <h1>{company_name}</h1>
    <VerifiedBadge /> {/* If credentials verified */}
    <Rating stars={google_rating} reviews={review_count} />
    <QuickStats>
      <Stat icon="calendar" value={years_in_business} label="Years" />
      <Stat icon="briefcase" value={total_jobs} label="Jobs" />
      <Stat icon="star" value={rating} label="Rating" />
    </QuickStats>
  </ProfileHero>

  {/* Service Area Map */}
  <ServiceAreaMap>
    <MapComponent center={business_location} radius={service_radius_miles}>
      {zip_codes.map(zip => <ZipCodePolygon key={zip} />)}
    </MapComponent>
    <ServiceList>
      {specialties.map(specialty => 
        <ServiceTag key={specialty} name={specialty} />
      )}
    </ServiceList>
  </ServiceAreaMap>

  {/* Availability Widget */}
  <AvailabilityWidget>
    <Status>{availability_status}</Status>
    <ResponseTime>{typical_response_time}</ResponseTime>
    <Capacity>
      Can handle {simultaneous_projects} projects
    </Capacity>
  </AvailabilityWidget>

  {/* Credentials Section */}
  <Credentials>
    <LicenseVerification number={license_number} verified={license_verified} />
    <InsuranceVerification coverage={insurance_coverage} verified={insurance_verified} />
    <Certifications list={certifications} />
  </Credentials>

  {/* Business Intelligence (from AI enrichment) */}
  <BusinessInsights>
    <h3>What we learned about {company_name}:</h3>
    <p>{ai_business_summary}</p>
    <Capabilities>{ai_capabilities_assessment}</Capabilities>
  </BusinessInsights>
</div>
```

### Phase 4: Database Integration

#### Data Mapping
```typescript
// Profile data structure matching our 3 tables

interface ContractorProfile {
  // From contractors table
  basic: {
    company_name: string;
    email: string;
    tier: 'BASIC' | 'PRO' | 'PREMIUM';
    service_areas: GeoJSON;
    specialties: string[];
    availability_status: string;
  };
  
  // From contractor_leads table  
  detailed: {
    phone: string;
    website: string;
    address: string;
    years_in_business: number;
    estimated_employees: string;
    service_radius_miles: number;
    zip_codes: string[];
    project_types: string[];
    min_project_size: number;
    max_project_size: number;
    typical_response_time: string;
    certifications: string[];
    license_number: string;
    license_verified: boolean;
    insurance_verified: boolean;
    insurance_coverage_amount: number;
  };
  
  // From potential_contractors table
  enrichment: {
    google_rating: number;
    google_reviews_count: number;
    google_business_categories: string[];
    ai_business_summary: string;
    ai_capabilities_assessment: string;
    ai_project_match_keywords: string[];
    business_size_category: string;
    last_enrichment_date: Date;
  };
}
```

### Phase 5: Implementation Components

#### 1. Research Component
```typescript
// ContractorResearch.tsx
const ResearchFlow = () => {
  const [researchResults, setResearchResults] = useState(null);
  
  const searchBusiness = async (companyName, location) => {
    // Use WebSearch MCP tool
    const webResults = await searchWeb(`${companyName} ${location}`);
    
    // Use Google Places API (when key added)
    const googleResults = await searchGooglePlaces(companyName, location);
    
    // Parse and display results
    return {
      website: extractWebsite(webResults),
      phone: googleResults.phone_number,
      address: googleResults.formatted_address,
      rating: googleResults.rating,
      reviews: googleResults.user_ratings_total
    };
  };
  
  return (
    <ResearchDisplay 
      results={researchResults}
      onConfirm={importToProfile}
      onEdit={manualEdit}
    />
  );
};
```

#### 2. Progressive Form Component
```typescript
// ProgressiveProfileForm.tsx
const ProfileBuilder = () => {
  const [step, setStep] = useState(1);
  const [profile, setProfile] = useState({});
  
  const steps = [
    <BusinessVerification data={profile} onNext={nextStep} />,
    <ServiceAreaConfig data={profile} onNext={nextStep} />,
    <ServiceCategories data={profile} onNext={nextStep} />,
    <CapacityAvailability data={profile} onNext={nextStep} />,
    <CredentialsTrust data={profile} onNext={nextStep} />
  ];
  
  return (
    <div className="profile-builder">
      <ProgressBar current={step} total={steps.length} />
      <StepContent>{steps[step - 1]}</StepContent>
      <ConversationalHelper 
        step={step} 
        data={profile}
        onSuggestion={handleSuggestion}
      />
    </div>
  );
};
```

#### 3. Intelligent Helper Component
```typescript
// COIAHelper.tsx
const IntelligentHelper = ({ currentField, profileData }) => {
  const suggestions = {
    service_radius: () => {
      if (profileData.specialties.includes('emergency')) {
        return "Since you offer emergency services, consider a wider radius";
      }
      return "Most contractors in your area service 25-30 miles";
    },
    
    project_types: () => {
      const related = getRelatedServices(profileData.specialties);
      return `Based on ${profileData.company_name}, you might also offer: ${related}`;
    },
    
    pricing: () => {
      const marketData = getMarketPricing(profileData.location, profileData.specialties);
      return `Average project size in your area: ${marketData.average}`;
    }
  };
  
  return (
    <div className="coia-helper">
      <Avatar src="/coia-avatar.png" />
      <Suggestion>{suggestions[currentField]?.()}</Suggestion>
    </div>
  );
};
```

### Phase 6: API Endpoints

```python
# Enhanced COIA endpoints in routers/coia_router.py

@router.post("/api/coia/research")
async def research_business(request: dict):
    """Auto-research business information"""
    company_name = request.get("company_name")
    location = request.get("location")
    
    # Search web
    web_results = await search_web(f"{company_name} {location}")
    
    # Search Google (when API key available)
    google_results = await search_google_places(company_name, location)
    
    # Store in potential_contractors table
    await store_research_results(company_name, {
        "web_results": web_results,
        "google_data": google_results,
        "discovered_at": datetime.now()
    })
    
    return {
        "website": extract_website(web_results),
        "phone": google_results.get("phone"),
        "address": google_results.get("address"),
        "rating": google_results.get("rating"),
        "reviews_count": google_results.get("reviews_count")
    }

@router.post("/api/coia/profile/progressive")
async def save_progressive_profile(request: dict):
    """Save profile data progressively as contractor completes steps"""
    contractor_id = request.get("contractor_id")
    step = request.get("step")
    data = request.get("data")
    
    # Update appropriate table based on step
    if step in ["business_verification", "service_area"]:
        await update_contractor_leads(contractor_id, data)
    elif step in ["credentials", "capacity"]:
        await update_contractors(contractor_id, data)
    elif step == "enrichment":
        await update_potential_contractors(contractor_id, data)
    
    # Calculate profile completeness
    completeness = calculate_profile_completeness(contractor_id)
    
    return {
        "success": True,
        "profile_completeness": completeness,
        "next_step": get_next_incomplete_step(contractor_id)
    }
```

## Implementation Priority

### Phase 1 (Immediate)
1. Add research functionality to COIA landing page chat
2. Create progressive profile form with 5 steps
3. Wire up to existing database tables

### Phase 2 (Next Sprint)  
1. Add interactive service area map
2. Implement credential verification
3. Create profile completeness tracking

### Phase 3 (Future)
1. AI-powered profile suggestions
2. Competitor analysis features
3. Performance analytics dashboard

## Success Metrics
- Profile completeness: Target 80%+ fields filled
- Time to complete: Under 10 minutes
- Contractor satisfaction: 4.5+ stars
- Data accuracy: 95%+ verified information

## Technical Requirements
- [ ] Google Places API key (for business search)
- [ ] WebSearch MCP tool (already available)
- [ ] Playwright for website verification
- [ ] Map component for service areas
- [ ] Progress tracking in database

## Testing Requirements
1. Create real contractor account with email/password
2. Complete full profile flow
3. Verify all data saved to 3 tables
4. Log in and confirm persistence
5. Test research with real businesses
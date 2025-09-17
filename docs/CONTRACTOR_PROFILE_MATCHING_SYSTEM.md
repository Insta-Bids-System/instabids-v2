# Contractor Profile & Matching System
**Purpose**: Define the core fields and matching logic for contractor profiles
**Focus**: Work type, location, and company size matching

## Core Matching Fields (What We Actually Use)

### 1. Work Type Classification
```javascript
{
  // Primary service category
  main_service_type: "Roofing",  // or "Landscaping", "Plumbing", etc.
  
  // Specific work subtypes
  service_subtypes: [
    "New installation",
    "Repair/service", 
    "Replacement",
    "Emergency repair"
  ]
}
```

### 2. Geographic Coverage
```javascript
{
  // Specific zip codes served
  zip_codes: ["33428", "33429", "33431"],
  
  // Service radius from base
  service_radius_miles: 25
}
```

### 3. Company Size (4-Tier System)
```javascript
{
  business_size_category: "LOCAL_BUSINESS_TEAMS"
  // Options:
  // - INDIVIDUAL_HANDYMAN (solo operator)
  // - OWNER_OPERATOR (small business owner)
  // - LOCAL_BUSINESS_TEAMS (local company with crews)
  // - NATIONAL_COMPANY (large national contractor)
}
```

## Matching Logic

### Company Size Matching Rules (±1 Tier Flexibility)

**If Project Needs NATIONAL_COMPANY:**
- ✅ Match: NATIONAL_COMPANY
- ✅ Match: LOCAL_BUSINESS_TEAMS (1 tier down)
- ❌ Skip: OWNER_OPERATOR (2 tiers down)
- ❌ Skip: INDIVIDUAL_HANDYMAN (3 tiers down)

**If Project Needs LOCAL_BUSINESS_TEAMS:**
- ✅ Match: OWNER_OPERATOR (1 tier down)
- ✅ Match: LOCAL_BUSINESS_TEAMS (exact)
- ✅ Match: NATIONAL_COMPANY (1 tier up)
- ❌ Skip: INDIVIDUAL_HANDYMAN (2 tiers down)

**If Project Needs OWNER_OPERATOR:**
- ✅ Match: INDIVIDUAL_HANDYMAN (1 tier down)
- ✅ Match: OWNER_OPERATOR (exact)
- ✅ Match: LOCAL_BUSINESS_TEAMS (1 tier up)
- ❌ Skip: NATIONAL_COMPANY (2 tiers up)

**If Project Needs INDIVIDUAL_HANDYMAN:**
- ✅ Match: INDIVIDUAL_HANDYMAN (exact)
- ✅ Match: OWNER_OPERATOR (1 tier up)
- ❌ Skip: LOCAL_BUSINESS_TEAMS (2 tiers up)
- ❌ Skip: NATIONAL_COMPANY (3 tiers up)

## Backend Matching Query

```sql
-- Find contractors for a roofing installation in 33428
SELECT c.*, cl.*
FROM contractors c
JOIN contractor_leads cl ON c.id = cl.contractor_id
WHERE 
  -- Work type match
  cl.main_service_type = 'Roofing'
  AND 'New installation' = ANY(cl.service_subtypes)
  
  -- Geographic match
  AND ('33428' = ANY(cl.zip_codes) 
       OR ST_DWithin(cl.location, project_location, cl.service_radius_miles * 1609.34))
  
  -- Company size match (±1 tier)
  AND cl.business_size_category IN (
    CASE 
      WHEN project_needs = 'NATIONAL_COMPANY' THEN 
        ARRAY['NATIONAL_COMPANY', 'LOCAL_BUSINESS_TEAMS']
      WHEN project_needs = 'LOCAL_BUSINESS_TEAMS' THEN 
        ARRAY['OWNER_OPERATOR', 'LOCAL_BUSINESS_TEAMS', 'NATIONAL_COMPANY']
      WHEN project_needs = 'OWNER_OPERATOR' THEN 
        ARRAY['INDIVIDUAL_HANDYMAN', 'OWNER_OPERATOR', 'LOCAL_BUSINESS_TEAMS']
      WHEN project_needs = 'INDIVIDUAL_HANDYMAN' THEN 
        ARRAY['INDIVIDUAL_HANDYMAN', 'OWNER_OPERATOR']
    END
  )
ORDER BY 
  -- Exact matches first
  CASE WHEN cl.business_size_category = project_needs THEN 0 ELSE 1 END,
  -- Then by distance
  ST_Distance(cl.location, project_location);
```

## Data Collection Fields (Store But Don't Match On Yet)

These fields are collected for future confidence scoring but NOT used for matching:

```javascript
{
  // Business verification (future confidence score)
  license_number: "CGC1234567",
  insurance_verified: false,
  insurance_coverage_amount: null,
  
  // Experience indicators (future confidence score)
  years_in_business: 5,
  certifications: ["EPA RRP", "OSHA 30"],
  
  // Discovery data (future confidence score)
  website: "example.com",
  google_rating: 4.8,
  google_reviews_count: 127,
  
  // Auto-researched (future confidence score)
  social_media_profiles: {
    facebook: "url",
    instagram: "@handle"
  }
}
```

## Future: Internal Confidence Score System

**NOT IMPLEMENTED YET** - Future enhancement to verify contractors:

```javascript
// Future confidence scoring factors
{
  license_verified: true,           // Check state database
  insurance_verified: true,          // Verify coverage
  similar_projects_found: 5,        // Photos of similar work
  social_proof_score: 85,           // Social media presence
  review_authenticity: 92,          // Real vs fake reviews
  
  // Generate overall confidence
  internal_confidence_score: 88,    // "High confidence"
  confidence_factors: [
    "Valid license in state database",
    "Insurance coverage verified",
    "5 similar projects in portfolio",
    "Strong social media presence"
  ]
}
```

## Implementation Priority

### Phase 1: Core Matching (NOW)
1. Collect work type, location, company size
2. Implement ±1 tier matching logic
3. Store but ignore verification fields

### Phase 2: Enhanced Profiles (NEXT)
1. Add more granular work subtypes
2. Improve geographic matching
3. Add availability tracking

### Phase 3: Confidence Scoring (FUTURE)
1. Build verification agents
2. Research contractor credentials
3. Generate confidence scores
4. Present scores to homeowners

## Testing Checklist

- [ ] Can match contractors by main service type
- [ ] Can filter by service subtypes
- [ ] Geographic matching works with zip codes
- [ ] Company size ±1 tier logic works correctly
- [ ] Exact matches prioritized over approximate
- [ ] Distance sorting works for geographic matches
- [ ] Profile fields map to database correctly
- [ ] COIA agent collects all required fields
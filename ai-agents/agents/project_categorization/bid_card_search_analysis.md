# Bid Card Search System Analysis
**Date**: August 28, 2025
**Critical Finding**: Current search systems use basic string matching on `project_type` field - NOT our new 14-category system

## 🔍 HOW BID CARD SEARCH CURRENTLY WORKS

### 1. BSA Agent (Contractor Bid Search)
**File**: `ai-agents/agents/bsa/bsa_deepagents.py:176-218`

```python
async def search_bid_cards(
    contractor_zip: str,
    radius_miles: int = 30,
    project_type: Optional[str] = None
) -> Dict[str, Any]:
    # CRITICAL: Uses basic string matching with ilike
    if project_type:
        query = query.ilike('project_type', f'%{project_type}%')
```

**Current Logic**:
- Takes optional `project_type` parameter as a string
- Uses PostgreSQL `ilike` for case-insensitive partial matching
- No category mapping or normalization
- Returns first 10 matching bid cards

### 2. COIA Agent (Contractor Discovery)
**File**: `ai-agents/agents/coia/tools/database/bid_cards.py:19-56`

```python
# Filters based on contractor specialties
if any("electrical" in str(s).lower() or "lighting" in str(s).lower() for s in specialties):
    filtered_projects = [p for p in available_projects 
                       if "electrical" in str(p.get("project_type", "")).lower() 
                       or "lighting" in str(p.get("project_type", "")).lower()]
```

**Current Logic**:
- Matches contractor specialties to project types using string contains
- Hardcoded for "electrical" and "lighting" specialties
- Returns top 3 matching projects
- No category system integration

### 3. Contractor UI Display
**File**: `web/src/components/chat/BSABidCardsDisplay.tsx`

```typescript
interface BidCard {
  project_type: string;  // Just a plain string field
  // ...
}
```

**Current Display**:
- Shows `project_type` as a simple string in the UI
- No category grouping or filtering
- Marketplace uses generic categories: ["plumbing", "electrical", "hvac", "landscaping"]

## 🚨 CRITICAL ISSUES WITH CURRENT APPROACH

### 1. **No Standardization**
- Bid cards have free-text `project_type` field
- No enforcement of our 448 predefined types
- Contractors can't reliably match their specialties

### 2. **Poor Matching Logic**
- Simple string contains matching (`"electrical" in project_type`)
- Misses related work (e.g., "lighting_installation" won't match "electrical")
- No understanding of category relationships

### 3. **Inconsistent Data**
- Some bid cards have old-style project types
- Some have new normalized types
- No migration path between systems

## 🎯 WHAT NEEDS TO HAPPEN

### Phase 1: Database Schema Update
```sql
-- Add category fields to bid_cards table
ALTER TABLE bid_cards 
ADD COLUMN service_category VARCHAR(50),
ADD COLUMN normalized_project_type VARCHAR(100),
ADD COLUMN project_scope VARCHAR(20),
ADD COLUMN required_capabilities JSONB;

-- Index for efficient searching
CREATE INDEX idx_bid_cards_category ON bid_cards(service_category);
CREATE INDEX idx_bid_cards_normalized_type ON bid_cards(normalized_project_type);
```

### Phase 2: Contractor Profile Mapping
```sql
-- Add category preferences to contractors table
ALTER TABLE contractors
ADD COLUMN service_categories JSONB,  -- ["Installation", "Repair", "Maintenance"]
ADD COLUMN specialized_types JSONB;    -- ["ac_installation", "heating_repair"]
```

### Phase 3: Search System Updates

#### BSA Search Enhancement
```python
async def search_bid_cards_v2(
    contractor_id: str,
    contractor_categories: List[str],  # Contractor's service categories
    contractor_types: List[str],       # Contractor's specialized types
    radius_miles: int = 30
) -> Dict[str, Any]:
    # Match by category first
    query = db.client.table('bid_cards').select('*')
    query = query.in_('service_category', contractor_categories)
    
    # Then filter by specific types if provided
    if contractor_types:
        query = query.in_('normalized_project_type', contractor_types)
```

#### COIA Search Enhancement
```python
def match_contractor_to_projects(contractor_profile: Dict) -> List[Dict]:
    # Get contractor's categories and types
    service_categories = contractor_profile.get('service_categories', [])
    specialized_types = contractor_profile.get('specialized_types', [])
    
    # Find matching bid cards
    matches = []
    for bid_card in available_projects:
        if bid_card['service_category'] in service_categories:
            # Category match - check specific type
            if bid_card['normalized_project_type'] in specialized_types:
                matches.append({**bid_card, 'match_score': 1.0})
            else:
                # Same category but different type
                matches.append({**bid_card, 'match_score': 0.7})
```

## 📊 CONTRACTOR SPECIALTY TO CATEGORY MAPPING

### Example Mappings
```python
CONTRACTOR_SPECIALTY_MAPPING = {
    # Electrical contractor
    "electrical": {
        "categories": ["Installation", "Repair", "Replacement", "Emergency"],
        "types": [
            "electrical_installation", "electrical_repair", 
            "electrical_panel_replacement", "emergency_electrical"
        ]
    },
    
    # HVAC contractor
    "hvac": {
        "categories": ["Installation", "Repair", "Replacement", "Maintenance"],
        "types": [
            "ac_installation", "heating_repair", 
            "hvac_replacement", "hvac_maintenance"
        ]
    },
    
    # General contractor (can do renovation)
    "general_contractor": {
        "categories": ["Renovation", "Installation", "Replacement"],
        "types": [
            "whole_house_renovation", "kitchen_renovation",
            "bathroom_renovation", "addition_renovation"
        ]
    }
}
```

## 🔄 MIGRATION STRATEGY

### Step 1: Backfill Existing Bid Cards
```python
# Script to categorize existing bid cards
for bid_card in all_bid_cards:
    old_type = bid_card['project_type']
    
    # Use LLM to categorize
    result = categorize_project(old_type)
    
    # Update bid card
    update_bid_card(bid_card['id'], {
        'service_category': result['service_category'],
        'normalized_project_type': result['normalized_project_type'],
        'project_scope': result['project_scope']
    })
```

### Step 2: Update Contractor Profiles
```python
# Map contractor specialties to categories
for contractor in all_contractors:
    specialties = contractor.get('specialties', [])
    
    categories = set()
    types = set()
    
    for specialty in specialties:
        mapping = CONTRACTOR_SPECIALTY_MAPPING.get(specialty.lower())
        if mapping:
            categories.update(mapping['categories'])
            types.update(mapping['types'])
    
    # Update contractor
    update_contractor(contractor['id'], {
        'service_categories': list(categories),
        'specialized_types': list(types)
    })
```

## ✅ BENEFITS OF UNIFIED SYSTEM

1. **Better Matching**: Contractors see relevant projects
2. **Consistent Data**: All bid cards use same categorization
3. **Scalable Search**: Can filter by category, then type
4. **Clear Specialization**: Contractors know exactly what they can bid on
5. **Improved UX**: Users can browse by category in marketplace

## 🚀 IMPLEMENTATION PRIORITY

1. **IMMEDIATE**: Fix category naming consistency (all should end same)
2. **HIGH**: Add category fields to bid_cards table
3. **HIGH**: Update BSA search to use categories
4. **MEDIUM**: Migrate existing bid cards
5. **MEDIUM**: Update contractor profiles with categories
6. **LOW**: Enhanced UI filtering and display

## 📝 NEXT STEPS

1. Complete category review for categories #6-14
2. Ensure all categories have consistent naming patterns
3. Create migration script for existing data
4. Update search endpoints to use category system
5. Test with real contractor profiles
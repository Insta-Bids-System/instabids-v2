# My Property System - Implementation Plan
**Date:** January 27, 2025  
**Agent:** Agent 3 (Homeowner UX)  
**Status:** Ready for Implementation

## 🎯 SYSTEM OVERVIEW

**Goal:** Build persistent property documentation system that integrates with existing Instabids architecture

**Core Concept:** AI-powered property memory that drives maintenance scheduling, project identification, and intelligent bid bundling

**Integration Strategy:** Connect seamlessly with existing homeowners, bid_cards, and unified_conversations systems

---

## 🗄️ EXISTING SYSTEM ANALYSIS

### Current Tables We're Integrating With:

```sql
homeowners (
  id uuid,
  user_id uuid, -- Our link point
  address jsonb, -- Could sync with our property address
  preferences jsonb,
  total_projects integer,
  total_spent numeric
)

bid_cards (
  id uuid,
  homeowner_id uuid, -- Links to homeowners.user_id
  title varchar,
  description text,
  location_address text, -- Sync from property
  budget_min/max integer,
  categories array, -- From property project types
  -- Full bidding system ready
)

unified_conversations (
  id uuid,
  entity_type text, -- "property", "room", "asset"
  entity_id uuid, -- property/room/asset UUID
  conversation_type text, -- "property_documentation"
  metadata jsonb
)
```

### Integration Points Identified:
- **Homeowners Link:** property.user_id → homeowners.user_id
- **Bid Generation:** property_project_bundles → bid_cards
- **Conversations:** property/room/asset conversations via unified system
- **Photo Storage:** Reuse existing photo_storage patterns

---

## 🏗️ NEW PROPERTY TABLES DESIGN

### Core Property Documentation Tables:

```sql
-- 1. Property Profile
CREATE TABLE properties (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES homeowners(user_id), -- Links to existing system
  name varchar(100), -- "Main House", "Rental Property #1"
  address text,
  square_feet integer,
  year_built integer,
  property_type varchar(50) DEFAULT 'single_family', -- single_family, condo, townhouse
  cover_photo_url text,
  metadata jsonb, -- Flexible storage for property-specific data
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- 2. Room Organization
CREATE TABLE property_rooms (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id uuid NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  name varchar(100) NOT NULL, -- "Master Kitchen", "Guest Bath", "Front Yard"
  room_type varchar(50) NOT NULL, -- kitchen, bathroom, bedroom, exterior, garage, basement
  floor_level integer DEFAULT 1, -- 1=main, 2=second, 0=basement, -1=sub-basement
  approximate_sqft integer,
  description text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- 3. Photo Documentation with AI Classification
CREATE TABLE property_photos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id uuid NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  room_id uuid REFERENCES property_rooms(id) ON DELETE SET NULL,
  photo_url text NOT NULL,
  original_filename varchar(255),
  photo_type varchar(50) DEFAULT 'documentation', -- documentation, before, after, issue
  ai_description text, -- AI-generated description
  ai_classification jsonb, -- {"detected_items": [...], "room_confidence": 0.95}
  upload_date timestamptz DEFAULT now(),
  taken_date timestamptz, -- When photo was actually taken
  created_at timestamptz DEFAULT now()
);

-- 4. Assets & Specifications Tracking
CREATE TABLE property_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id uuid NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  room_id uuid REFERENCES property_rooms(id) ON DELETE SET NULL,
  asset_type varchar(50) NOT NULL, -- appliance, fixture, system, finish
  category varchar(100) NOT NULL, -- refrigerator, paint, flooring, hvac, lighting
  name varchar(200), -- "Kitchen Refrigerator", "Master Bath Vanity"
  brand varchar(100),
  model_number varchar(100),
  serial_number varchar(100),
  color_finish varchar(100), -- "Benjamin Moore Classic Gray", "Brushed Nickel"
  install_date date,
  warranty_expires date,
  purchase_price numeric(10,2),
  purchase_location varchar(200),
  manual_url text,
  receipt_url text,
  specifications jsonb, -- Flexible storage for asset-specific data
  status varchar(50) DEFAULT 'active', -- active, needs_repair, replaced, removed
  notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
```

### Project Management Tables:

```sql
-- 5. Maintenance Schedule
CREATE TABLE property_maintenance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id uuid NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  asset_id uuid REFERENCES property_assets(id) ON DELETE CASCADE,
  task_name varchar(200) NOT NULL, -- "Replace AC Filter", "Clean Gutters"
  task_type varchar(50) NOT NULL, -- seasonal, recurring, one_time
  frequency_months integer, -- 3=quarterly, 12=annually, NULL=one_time
  last_completed date,
  next_due date NOT NULL,
  priority varchar(20) DEFAULT 'medium', -- low, medium, high, urgent
  estimated_cost_min numeric(8,2),
  estimated_cost_max numeric(8,2),
  instructions text,
  supplier_info jsonb, -- {"preferred_supplier": "Home Depot", "sku": "ABC123"}
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- 6. AI-Detected Issues & Opportunities
CREATE TABLE property_issues (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id uuid NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  room_id uuid REFERENCES property_rooms(id) ON DELETE SET NULL,
  asset_id uuid REFERENCES property_assets(id) ON DELETE SET NULL,
  photo_id uuid REFERENCES property_photos(id) ON DELETE SET NULL, -- Photo that detected issue
  issue_type varchar(50) NOT NULL, -- maintenance, repair, safety, upgrade_opportunity
  severity varchar(20) NOT NULL, -- low, medium, high, urgent
  title varchar(200) NOT NULL, -- "Paint Peeling on North Wall"
  description text NOT NULL,
  ai_confidence decimal(3,2), -- 0.00 to 1.00
  estimated_cost_min numeric(8,2),
  estimated_cost_max numeric(8,2),
  status varchar(50) DEFAULT 'identified', -- identified, acknowledged, bundled, scheduled, resolved, dismissed
  identified_date timestamptz DEFAULT now(),
  target_resolution_date date,
  resolved_date timestamptz,
  resolution_notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- 7. Project Bundling for Group Bidding
CREATE TABLE property_project_bundles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id uuid NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  bundle_name varchar(200) NOT NULL, -- "Kitchen Refresh Spring 2025"
  description text,
  bundle_type varchar(50) DEFAULT 'maintenance', -- maintenance, repair, upgrade, seasonal
  priority varchar(20) DEFAULT 'medium',
  estimated_total_min numeric(10,2),
  estimated_total_max numeric(10,2),
  target_start_date date,
  target_completion_date date,
  status varchar(50) DEFAULT 'draft', -- draft, ready_for_bids, bid_sent, in_progress, completed
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- 8. Link Issues to Bundles (Many-to-Many)
CREATE TABLE bundle_issues (
  bundle_id uuid NOT NULL REFERENCES property_project_bundles(id) ON DELETE CASCADE,
  issue_id uuid NOT NULL REFERENCES property_issues(id) ON DELETE CASCADE,
  added_at timestamptz DEFAULT now(),
  PRIMARY KEY (bundle_id, issue_id)
);

-- 9. Link Bundles to Bid Cards (Integration Point)
CREATE TABLE property_bids (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id uuid NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  bundle_id uuid REFERENCES property_project_bundles(id) ON DELETE SET NULL,
  bid_card_id uuid NOT NULL REFERENCES bid_cards(id), -- Links to existing bid system
  created_at timestamptz DEFAULT now()
);
```

---

## 🔗 SYSTEM INTEGRATION POINTS

### 1. Homeowner Profile Integration
```python
# When creating property, link to existing homeowner
def create_property(user_id: str, property_data: dict):
    # Verify homeowner exists
    homeowner = supabase.table("homeowners").select("*").eq("user_id", user_id).single()
    
    # Create property linked to homeowner
    property_data["user_id"] = user_id
    property = supabase.table("properties").insert(property_data).execute()
    
    # Optionally sync address with homeowner record
    if property_data.get("sync_address"):
        supabase.table("homeowners").update({
            "address": {"street": property_data["address"]}
        }).eq("user_id", user_id).execute()
```

### 2. Unified Conversation Integration
```python
# Create property-specific conversation
async def create_property_conversation(property_id: str, conversation_type: str):
    conversation_data = {
        "entity_type": "property",
        "entity_id": property_id,
        "conversation_type": conversation_type, # "property_documentation", "maintenance_planning"
        "title": f"Property {property_name} - {conversation_type}",
        "metadata": {"property_context": True}
    }
    
    response = requests.post("http://localhost:8008/api/conversations/create", json=conversation_data)
    return response.json()["conversation_id"]

# Store AI findings in conversation memory
async def store_photo_analysis(conversation_id: str, photo_analysis: dict):
    memory_data = {
        "conversation_id": conversation_id,
        "memory_scope": "property",
        "memory_type": "ai_analysis",
        "memory_key": f"photo_analysis_{photo_id}",
        "memory_value": photo_analysis
    }
    
    requests.post("http://localhost:8008/api/conversations/memory", json=memory_data)
```

### 3. Bid Card Generation From Bundles
```python
# Convert property project bundle to bid card
def bundle_to_bid_card(bundle_id: str) -> str:
    # Get bundle with all issues
    bundle = get_bundle_with_issues(bundle_id)
    property = get_property(bundle.property_id)
    homeowner = get_homeowner(property.user_id)
    
    # Create bid card with existing system
    bid_card_data = {
        "homeowner_id": homeowner.user_id,
        "homeowner_name": homeowner.name,
        "title": bundle.bundle_name,
        "description": generate_bid_description(bundle),
        "location_address": property.address,
        "location_city": extract_city(property.address),
        "location_state": extract_state(property.address),
        "budget_min": int(bundle.estimated_total_min or 0),
        "budget_max": int(bundle.estimated_total_max or 0),
        "categories": extract_categories_from_issues(bundle.issues),
        "requirements": generate_requirements_from_issues(bundle.issues),
        "timeline_flexibility": "flexible", # Default for maintenance bundles
        "visibility": "private", # Start private, homeowner can make public
        "group_bid_eligible": True, # Enable group bidding for cost savings
        "metadata": {
            "source": "property_system",
            "bundle_id": bundle_id,
            "property_id": property.id
        }
    }
    
    bid_card = supabase.table("bid_cards").insert(bid_card_data).execute()
    
    # Link bundle to bid card
    supabase.table("property_bids").insert({
        "property_id": property.id,
        "bundle_id": bundle_id,
        "bid_card_id": bid_card.data[0]["id"]
    }).execute()
    
    # Update bundle status
    supabase.table("property_project_bundles").update({
        "status": "bid_sent"
    }).eq("id", bundle_id).execute()
    
    return bid_card.data[0]["id"]
```

---

## 🤖 AI PHOTO CLASSIFICATION SYSTEM

### Photo Upload & Analysis Flow:
```python
async def process_property_photo(property_id: str, room_id: str, photo_file):
    # 1. Upload photo to storage
    photo_url = upload_to_storage(photo_file)
    
    # 2. AI Classification using Claude/GPT Vision
    classification_result = await analyze_photo_with_ai(photo_url, {
        "property_context": get_property_context(property_id),
        "room_context": get_room_context(room_id) if room_id else None
    })
    
    # 3. Save photo record
    photo_data = {
        "property_id": property_id,
        "room_id": room_id,
        "photo_url": photo_url,
        "ai_description": classification_result["description"],
        "ai_classification": classification_result["classification"]
    }
    photo = supabase.table("property_photos").insert(photo_data).execute()
    
    # 4. Extract and save detected assets
    for asset in classification_result["detected_assets"]:
        asset_data = {
            "property_id": property_id,
            "room_id": room_id,
            "asset_type": asset["type"],
            "category": asset["category"],
            "name": asset["name"],
            "brand": asset.get("brand"),
            "color_finish": asset.get("color"),
            "specifications": asset.get("specifications", {})
        }
        supabase.table("property_assets").insert(asset_data).execute()
    
    # 5. Create issues for detected problems
    for issue in classification_result["detected_issues"]:
        issue_data = {
            "property_id": property_id,
            "room_id": room_id,
            "photo_id": photo["id"],
            "issue_type": issue["type"],
            "severity": issue["severity"],
            "title": issue["title"],
            "description": issue["description"],
            "ai_confidence": issue["confidence"]
        }
        supabase.table("property_issues").insert(issue_data).execute()
    
    # 6. Update unified conversation with analysis
    conversation_id = get_or_create_room_conversation(room_id)
    await store_photo_analysis(conversation_id, classification_result)
    
    return {
        "photo_id": photo["id"],
        "assets_detected": len(classification_result["detected_assets"]),
        "issues_found": len(classification_result["detected_issues"]),
        "classification": classification_result["classification"]
    }

async def analyze_photo_with_ai(photo_url: str, context: dict) -> dict:
    prompt = f"""
    Analyze this property photo and provide detailed classification.
    
    Context: {context}
    
    Return JSON with:
    {{
        "description": "Detailed description of what you see",
        "room_type": "kitchen|bathroom|bedroom|living_room|exterior|garage|basement",
        "room_confidence": 0.95,
        "detected_assets": [
            {{
                "type": "appliance|fixture|finish|system",
                "category": "refrigerator|paint|flooring|lighting",
                "name": "Stainless Steel Refrigerator",
                "brand": "Whirlpool",
                "color": "Stainless Steel",
                "specifications": {{}},
                "condition": "good|fair|needs_attention"
            }}
        ],
        "detected_issues": [
            {{
                "type": "maintenance|repair|safety|cosmetic",
                "severity": "low|medium|high|urgent",
                "title": "Paint Peeling on Window Frame",
                "description": "Paint is peeling around the window frame",
                "confidence": 0.87
            }}
        ],
        "classification": {{
            "primary_surfaces": ["walls", "ceiling", "floor"],
            "lighting_conditions": "natural|artificial|mixed",
            "overall_condition": "excellent|good|fair|needs_work"
        }}
    }}
    """
    
    # Call Claude/GPT Vision API
    response = await call_vision_api(photo_url, prompt)
    return json.loads(response)
```

---

## 📱 USER EXPERIENCE FLOW

### 1. Initial Property Setup
```
User → Upload Property Photos (bulk)
     → AI Classifies by Room
     → User Confirms/Adjusts Classifications
     → System Creates Property + Rooms + Assets
     → Property Dashboard Generated
```

### 2. Ongoing Documentation
```
User → Snap Photo of Issue
     → AI Detects Problem (paint peeling, broken fixture)
     → Creates Issue Record
     → Suggests Adding to Project Bundle
     → User Approves Bundle
     → System Generates Bid Card
```

### 3. Maintenance Management
```
System → Detects Due Maintenance (AC filter, gutter cleaning)
       → Notifies User
       → User Schedules or Bundles with Other Work
       → Creates Maintenance Bundle
       → Generates Group Bid for Multiple Properties
```

---

## 🚀 IMPLEMENTATION PHASES

### Phase 1: Core Property Documentation (Week 1)
**Tables:** properties, property_rooms, property_photos, property_assets
**Features:**
- Property creation and room setup
- Bulk photo upload with basic AI classification
- Asset detection and cataloging
- Basic property dashboard

### Phase 2: Issue Detection & Project Management (Week 2)
**Tables:** property_issues, property_project_bundles, bundle_issues
**Features:**
- AI issue detection from photos
- Project bundling interface
- Issue management and tracking
- Bundle preparation for bidding

### Phase 3: Integration & Bidding (Week 3)
**Tables:** property_bids, enhanced unified conversations
**Features:**
- Bundle to bid card conversion
- Integration with existing contractor system
- Unified conversation system integration
- Full end-to-end property → project → bid flow

### Phase 4: Maintenance & Intelligence (Week 4)
**Tables:** property_maintenance, enhanced AI features
**Features:**
- Maintenance scheduling and reminders
- Seasonal task recommendations
- Purchase history and specifications tracking
- Advanced property analytics

---

## 🎯 SUCCESS METRICS

### Technical Metrics
- Property photo classification accuracy >85%
- Bundle-to-bid conversion rate >90% 
- API response times <500ms
- Zero data corruption during integration

### Business Metrics  
- User engagement with property documentation
- Increase in bundled project bids
- Reduction in maintenance emergency calls
- Higher contractor bid response rates (better project specs)

### User Experience Metrics
- Photo upload and classification completion rate
- Time from issue detection to bid generation
- User satisfaction with AI recommendations
- Property documentation completeness over time

---

## 🔒 SECURITY & DATA PRIVACY

### Data Protection
- All property data isolated by user_id
- Photo storage with secure URLs and access controls
- AI analysis data stored securely with user consent
- Property addresses handled with location privacy settings

### Multi-Tenant Architecture
- tenant_id support for property management companies
- Role-based access (owner, property manager, contractor)
- Data segregation between different property portfolios
- Secure sharing of property information with contractors

---

## 🚀 IMPLEMENTATION PROGRESS

### ✅ PHASE 1: CORE PROPERTY DOCUMENTATION - IN PROGRESS

**Database Tables:** ✅ COMPLETED
- `properties` table created with UUID, user_id link, address, metadata
- `property_rooms` table created for room organization
- `property_photos` table created for AI photo classification
- `property_assets` table created for asset tracking
- All indexes created for performance

**Backend API:** ✅ COMPLETED
- `property_api.py` router created with 8 core endpoints
- Integrated with existing `database_simple.py` pattern
- Added to `main.py` without breaking existing system
- Health check endpoint working

**API Endpoints Working:**
- ✅ `POST /api/properties/create` - Creates new property (TESTED)
- ✅ `GET /api/properties/user/{user_id}` - Lists user properties
- ✅ `GET /api/properties/{property_id}` - Gets property details  
- ✅ `POST /api/properties/{property_id}/rooms` - Creates rooms
- ✅ `GET /api/properties/{property_id}/rooms` - Lists rooms
- ✅ `POST /api/properties/{property_id}/photos/upload` - Photo upload (mock)
- ✅ `GET /api/properties/{property_id}/assets` - Lists assets
- ✅ `GET /api/properties/{property_id}/dashboard` - Property dashboard

**TESTING STATUS:**
- ✅ Property creation tested with real homeowner user_id
- ✅ Database integration confirmed working
- ✅ Backend stable and not breaking existing endpoints

**FRONTEND COMPONENTS:** ✅ COMPLETED
- `PropertyDashboard.tsx` - Main property management interface
- `PropertyCreator.tsx` - Property creation form with validation
- `PropertyView.tsx` - Individual property details with tabs
- Added "My Property" tab to main DashboardPage.tsx
- Full React integration with existing UI patterns

**TESTING STATUS:**
- ✅ Property creation API tested with real homeowner
- ✅ Room creation API tested (Master Kitchen created)
- ✅ Frontend components build without errors
- ✅ Backend integration confirmed working
- ✅ Database tables populated with test data

**WORKING FEATURES:**
1. ✅ Create new property (tested via API)
2. ✅ List user properties (tested via API)  
3. ✅ Create rooms for property (tested via API)
4. ✅ View property details with room/asset tabs
5. ✅ Property dashboard with stats
6. ✅ Responsive UI matching existing design patterns

### ✅ PHASE 2: PHOTO CLASSIFICATION & AI ANALYSIS - COMPLETED

**Photo Upload System:** ✅ COMPLETED  
- `PhotoUpload.tsx` component with drag & drop functionality
- Real file upload handling (base64 encoding for AI analysis)
- Integrated into PropertyView with dedicated Photos tab
- Progress indicators and error handling

**AI Classification System:** ✅ COMPLETED
- Integrated with existing Iris vision capabilities (GPT-4o)
- Property-focused analysis prompt (vs inspiration-focused)
- Detects: room type, assets, issues, maintenance opportunities
- Graceful fallback when AI unavailable
- Returns structured JSON for database storage

**Enhanced UI:** ✅ COMPLETED
- Added Photos tab to PropertyView
- Photo upload button in Overview tab
- AI analysis feedback to user
- Upload progress and status indicators

**API Integration:** ✅ COMPLETED  
- `/api/properties/{id}/photos/upload` endpoint enhanced
- Real file handling with base64 encoding
- AI classification pipeline implemented  
- Automatic asset creation from detected items

**TESTING STATUS:**
- ✅ Photo upload API endpoint working
- ✅ AI classification system functional (with fallback)
- ✅ Frontend components integrated
- ✅ File validation and error handling
- ✅ Progress indicators working

---

**CURRENT STATUS:** Phase 2 - COMPLETE  
**Next Action:** Begin Phase 3 - Issue Detection & Project Management
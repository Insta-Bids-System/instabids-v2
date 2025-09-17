# MASTER BID CARD SCHEMA - UNIFIED TABLE STRUCTURE
**Last Updated**: January 9, 2025  
**Status**: PRODUCTION READY - 100% UNIFIED  
**Purpose**: Complete reference for all agents working with bid card tables

## 🎯 EXECUTIVE SUMMARY

**TABLES ARE 100% IDENTICAL**: Both `potential_bid_cards` and `bid_cards` tables have exactly **84 identical fields** with matching data types and constraints.

**CONVERSION WORKING**: One-click conversion from potential → bid cards operational with zero data loss.

**SYSTEM STATUS**: Table unification is COMPLETE and PRODUCTION READY.

---

## 📋 COMPLETE UNIFIED FIELD STRUCTURE

**Both `potential_bid_cards` and `bid_cards` tables contain exactly these 84 fields:**

### **CORE IDENTIFICATION FIELDS**
```
 1. id                         - UUID primary key
 2. user_id                    - UUID foreign key to profiles/homeowners
 3. bid_card_number           - VARCHAR unique identifier (BC-LIVE-{timestamp})
 4. session_id                - VARCHAR session tracking
 5. anonymous_user_id         - VARCHAR for anonymous users
 6. created_by                - VARCHAR creator identifier
 7. created_at                - TIMESTAMPTZ creation time
 8. updated_at                - TIMESTAMPTZ last modification
```

### **PROJECT CLASSIFICATION FIELDS** 
```
 9. title                     - VARCHAR project title
10. description               - TEXT main project description
11. primary_trade             - VARCHAR main trade category
12. project_type              - VARCHAR human-readable project type  
13. secondary_trades          - JSONB array of additional trades
14. service_category_id       - INTEGER foreign key to service_categories
15. project_type_id          - INTEGER foreign key to project_types
16. contractor_type_ids       - JSONB array of contractor type IDs
17. service_complexity        - VARCHAR (single-trade/multi-trade/complex)
18. complexity_score          - INTEGER (1-10 scale)
19. trade_count              - INTEGER number of trades required
20. component_type           - VARCHAR component classification
21. service_type             - JSONB service type classification
```

### **LOCATION FIELDS**
```
22. location_zip             - VARCHAR ZIP code (REQUIRED)
23. location_city            - VARCHAR city name
24. location_state           - VARCHAR state code
25. location_address         - VARCHAR street address
26. location_radius_miles    - INTEGER service area radius
27. room_location            - VARCHAR specific room/area
28. property_area            - VARCHAR property type description
```

### **BUDGET FIELDS**
```
29. budget_min               - INTEGER minimum budget
30. budget_max               - INTEGER maximum budget
31. budget_context           - TEXT budget stage/notes
32. budget_flexibility       - VARCHAR (flexible/strict/negotiable)
```

### **TIMELINE FIELDS**
```
33. urgency_level            - VARCHAR (emergency/urgent/medium)
34. estimated_timeline       - VARCHAR timeline description
35. timeline_start           - DATE project start date
36. timeline_end             - DATE project end date
37. timeline_flexibility     - VARCHAR (flexible/strict/asap)
38. bid_collection_deadline  - TIMESTAMPTZ bid collection deadline
39. project_completion_deadline - TIMESTAMPTZ project completion deadline
40. deadline_hard            - BOOLEAN if deadline is firm
41. deadline_context         - TEXT deadline notes
42. seasonal_constraint      - VARCHAR seasonal requirements
```

### **CONTRACTOR MANAGEMENT FIELDS**
```
43. contractor_count_needed   - INTEGER target contractor count
44. contractor_size_preference - VARCHAR (small_business/regional_company/solo_handyman)
45. bids_received_count      - INTEGER actual bids received
46. bids_target_met          - BOOLEAN target reached
47. winner_contractor_id     - UUID selected contractor
48. contractor_selected_at   - TIMESTAMPTZ selection timestamp
49. connection_fee_calculated - BOOLEAN fee calculation status
```

### **PROJECT REQUIREMENTS FIELDS**
```
50. requirements             - JSONB combined requirements array
51. categories               - JSONB project categories
52. quality_expectations     - TEXT quality level description
53. materials_specified      - JSONB specific materials array
54. special_requirements     - JSONB special requirements array
55. requires_general_contractor - BOOLEAN GC requirement
```

### **STATUS & WORKFLOW FIELDS**
```
56. status                   - VARCHAR workflow status
57. ready_for_conversion     - BOOLEAN conversion readiness
58. ready_for_outreach       - BOOLEAN outreach readiness
59. completion_percentage    - INTEGER (0-100) completion
60. priority                 - INTEGER priority level
```

### **CONTACT INFORMATION FIELDS**
```
61. email_address            - VARCHAR homeowner email
62. phone_number             - VARCHAR homeowner phone
```

### **PROJECT RELATIONSHIPS FIELDS**
```
63. parent_project_id        - UUID parent project link
64. related_project_ids      - JSONB array of related projects
65. bundle_group_id          - VARCHAR group bidding bundle ID
66. eligible_for_group_bidding - BOOLEAN group bidding eligibility
67. converted_from_potential_id - UUID conversion tracking
```

### **MEDIA & PHOTOS FIELDS**
```
68. photo_ids                - JSONB array of photo IDs
69. cover_photo_id           - VARCHAR main photo ID
70. image_analyses           - JSONB image analysis results
71. images_analyzed          - BOOLEAN analysis completion status
```

### **PUBLIC ACCESS FIELDS**
```
72. public_url               - VARCHAR unique public URL slug
73. is_public                - BOOLEAN public visibility
74. public_views             - INTEGER public view count
75. public_last_viewed_at    - TIMESTAMPTZ last public view
76. public_created_at        - TIMESTAMPTZ when made public
77. public_expires_at        - TIMESTAMPTZ public expiration
78. public_allow_bids        - BOOLEAN allow public bidding
```

### **MESSAGING & COMMUNICATION FIELDS**
```
79. messaging_enabled        - BOOLEAN messaging system status
80. last_contractor_message_at - TIMESTAMPTZ last message time
```

### **AI & ANALYSIS FIELDS**
```
81. ai_analysis              - JSONB AI analysis results
82. last_ai_analysis_at      - TIMESTAMPTZ last analysis time
83. cia_thread_id           - VARCHAR CIA conversation link
```

### **MAIN DATA STORAGE FIELD**
```
84. bid_document             - JSONB comprehensive data storage
    Contains:
    - project_description
    - location_details (nested object)
    - contact_information (nested object)
    - project_requirements (nested object)
    - timeline_preferences (nested object)
    - budget_details (nested object)
    - project_relationships (nested object)
    - media (photo_ids, cover_photo_id)
    - conversion_metadata
    - submitted_bids (array of bid submissions)
    - rfi_photos (array of RFI photos)
    - contractor_preferences
    - project_complexity metadata
```

---

## 🔄 DATA FLOW & CONVERSION

### **Potential → Bid Card Conversion**
```
API Endpoint: POST /api/cia/potential-bid-cards/{id}/convert-to-bid-card
Process: 
1. Validates required fields (title, description, location_zip, urgency_level)
2. Maps all 84 fields directly (no transformation needed)
3. Preserves all data in bid_document JSONB
4. Returns official_bid_card_id
Status: 100% OPERATIONAL with zero data loss
```

### **Key Required Fields for Conversion**
```
MINIMUM REQUIRED:
- title (project name)
- description (project scope)
- location_zip (contractor matching)
- urgency_level (timeline classification)

RECOMMENDED:
- budget_min/budget_max
- contractor_count_needed
- primary_trade
- contractor_type_ids (auto-populated by categorization system)
```

---

## 🏗️ CONNECTED SYSTEMS

### **Tables That Reference These Bid Card Tables**
```
REFERENCES bid_cards (32 tables):
- bid_card_change_logs, bid_card_contractor_types, bid_card_distributions
- bid_card_documents, bid_card_engagement_events, bid_card_views
- connection_fees, contractor_bids, contractor_discovery_cache
- contractor_outreach_attempts, contractor_responses, messages
- outreach_campaigns, notifications, and 18+ other operational tables

REFERENCES potential_bid_cards (4 tables):
- cia_conversation_tracking, potential_bid_card_contractor_types
- unified_conversation_messages, potential_bid_cards (self-reference)
```

### **4-Tier Project Categorization Integration**
```
AUTOMATIC POPULATION:
- service_category_id → Links to 11 service categories
- project_type_id → Links to 180+ project types  
- contractor_type_ids → Auto-populated array via database triggers
- Database triggers maintain consistency across both tables
```

---

## 🎯 AGENT INTEGRATION GUIDE

### **For All Agents Working with Bid Cards**

**Table Names**: `potential_bid_cards` and `bid_cards`  
**Field Count**: Exactly 84 fields each  
**Structure**: 100% identical between both tables  

### **Key Programming Patterns**
```typescript
// TypeScript interface (applies to both tables)
interface BidCardRecord {
  // Use exact field names from the 84-field list above
  id: string;
  title: string;
  description: string;
  location_zip: string;
  urgency_level: 'emergency' | 'urgent' | 'medium';
  // ... all 84 fields available
}
```

```python
# Python usage (applies to both tables)
from database_simple import db

# Create potential bid card
potential_data = {
    'title': 'Kitchen Renovation',
    'description': 'Complete kitchen remodel',
    'location_zip': '12345',
    'urgency_level': 'medium',
    'contractor_count_needed': 4
}
result = db.client.table('potential_bid_cards').insert(potential_data).execute()

# Convert to official bid card
import requests
response = requests.post(f'/api/cia/potential-bid-cards/{potential_id}/convert-to-bid-card')
```

### **Critical Notes for All Agents**
1. **Both tables are identical** - same field names, types, constraints
2. **Conversion preserves all data** - no information lost during potential → bid conversion
3. **All 84 fields available** in both tables for full functionality
4. **Foreign key relationships intact** - all connected systems continue working
5. **Production ready** - system tested and operational

---

## ✅ SYSTEM STATUS CONFIRMATION

**TABLE UNIFICATION**: ✅ COMPLETE  
**FIELD MATCHING**: ✅ 100% IDENTICAL (84/84 fields)  
**DATA CONVERSION**: ✅ OPERATIONAL (zero data loss)  
**PRODUCTION STATUS**: ✅ READY

**Any agent can now work with bid cards knowing both tables have exactly the same 84-field structure and full conversion capabilities.**
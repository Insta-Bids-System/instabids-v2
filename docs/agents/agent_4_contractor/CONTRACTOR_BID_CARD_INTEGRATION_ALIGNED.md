# 🎯 CONTRACTOR BID CARD INTEGRATION - ALIGNED WITH BACKEND
**Agent 4 - Contractor UX Domain**
**Updated**: January 2025
**Purpose**: Implementation plan aligned with existing backend endpoints and tables

---

## ✅ EXISTING BACKEND STRUCTURE TO USE

### **Bid Card Endpoints (Already Defined)**
- `GET /api/bid-cards/marketplace` - Browse available bid cards
- `GET /api/bid-cards/{bid_card_id}` - Get specific bid card details
- `POST /api/bid-cards/{bid_card_id}/submit-bid` - Submit a bid
- `GET /api/contractor/my-bids` - Get contractor's submitted bids

### **Messaging Endpoints (Already Defined)**
- `GET /api/messages/threads` - Get message threads for contractor
- `POST /api/messages/send` - Send message to homeowner
- `GET /api/messages/thread/{thread_id}` - Get messages in a thread
- `PUT /api/messages/{message_id}/read` - Mark message as read

### **Database Tables to Use**

**Bid Card Related:**
- `bid_cards` - Core bid card data (includes bid_document JSONB field)
- `bids` - Contractor bid submissions
- `bid_card_views` - Track which contractors viewed bid cards
- `contractor_responses` - Contractor responses to outreach

**Messaging Related:**
- `messages` - All messages between contractors/homeowners
- `message_filters` - Content filtering rules (IMPORTANT: filters contact info)
- `contractor_aliases` - Anonymous contractor identities

**Contractor Profile:**
- `contractors` - Contractor profiles and credentials
- `contractor_engagement_summary` - Engagement metrics

---

## 🎯 WHAT NEEDS TO BE IMPLEMENTED IN contractor_routes.py

Since the backend agent has already defined the endpoints, I need to implement these in `contractor_routes.py`:

### **1. Browse Bid Cards Endpoint**
```python
@router.get("/bid-cards/marketplace")
async def get_bid_card_marketplace(
    contractor_id: str,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    radius_miles: Optional[int] = 20,
    project_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """
    Get available bid cards for contractor browsing
    - Default: Show bid cards from contractor's state
    - Support radius search from zip code
    - Filter by project type if specified
    """
    # Implementation using bid_cards table
```

### **2. Get Bid Card Details**
```python
@router.get("/bid-cards/{bid_card_id}")
async def get_bid_card_details(
    contractor_id: str,
    bid_card_id: str
):
    """
    Get full bid card details
    - Record view in bid_card_views table
    - Check if contractor already submitted bid
    """
    # Implementation using bid_cards and bid_card_views
```

### **3. Submit Bid**
```python
@router.post("/bid-cards/{bid_card_id}/submit-bid")
async def submit_contractor_bid(
    contractor_id: str,
    bid_card_id: str,
    bid_amount: float,
    timeline_days: int,
    message: str,
    included_items: dict
):
    """
    Submit bid on a bid card
    - Update bid_cards.bid_document JSONB field
    - Create entry in bids table
    - Record in contractor_responses
    """
    # Implementation updating bid_document JSONB
```

### **4. Get My Bids**
```python
@router.get("/contractor/my-bids")
async def get_contractor_bids(
    contractor_id: str,
    status: Optional[str] = None
):
    """
    Get all bids submitted by this contractor
    - Query bids table
    - Include bid card details
    - Show status (pending, accepted, rejected)
    """
    # Implementation using bids table
```

---

## 🔄 INTEGRATION WITH MESSAGING SYSTEM

### **Key Requirements from Messaging Docs:**
1. **Content Filtering**: All messages must go through `message_filters` table
2. **Anonymous Communication**: Use `contractor_aliases` for identity protection
3. **No Direct Contact Info**: Phone/email automatically filtered

### **Messaging Flow for Bid Cards:**
```python
# When contractor submits bid:
1. Create contractor_alias if doesn't exist
2. Create message thread for bid_card_id + contractor_id
3. Send initial message with bid details
4. Filter through message_filters table

# Example implementation:
@router.post("/messages/send")
async def send_bid_message(
    contractor_id: str,
    bid_card_id: str,
    message: str
):
    # Get or create contractor alias
    # Apply message filters
    # Store in messages table
    # Return filtered message
```

---

## 🗺️ GEOGRAPHIC SEARCH IMPLEMENTATION

### **Using Existing bid_cards Table Structure**
```python
# For radius search, bid_cards should have location data
# Options:
1. If bid_cards has lat/long columns, use PostGIS
2. If bid_cards has zip_code, convert to coordinates
3. If bid_cards has city/state, use geocoding

# Example query:
"""
SELECT * FROM bid_cards
WHERE location_state = %s
AND status = 'active'
AND ST_DWithin(
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
    %s * 1609.34  -- miles to meters
)
ORDER BY created_at DESC
"""
```

---

## 📊 BID DOCUMENT STRUCTURE

Based on COMPLETE_BID_CARD_ECOSYSTEM_MAP, bids are stored in `bid_cards.bid_document` as JSONB:

```json
{
  "submitted_bids": [
    {
      "contractor_id": "uuid",
      "contractor_name": "Company Name",
      "bid_amount": 12500,
      "timeline_days": 14,
      "submission_time": "2025-01-30T10:00:00Z",
      "message": "We can complete this project...",
      "included": {
        "materials": true,
        "permits": true,
        "cleanup": true,
        "warranty_years": 1
      }
    }
  ],
  "bids_received_count": 3,
  "bids_target_met": false
}
```

---

## 🚀 IMPLEMENTATION PRIORITIES

### **Priority 1: Core Viewing (Implement First)**
1. Implement `/bid-cards/marketplace` endpoint
2. Connect to existing `bid_cards` table
3. Add state-level filtering
4. Record views in `bid_card_views`

### **Priority 2: Bid Submission**
1. Implement `/bid-cards/{id}/submit-bid` endpoint
2. Update `bid_document` JSONB field
3. Create entry in `bids` table
4. Trigger messaging system

### **Priority 3: Geographic Search**
1. Add radius search to marketplace endpoint
2. Implement zip-to-coordinates conversion
3. Use efficient spatial queries

### **Priority 4: Messaging Integration**
1. Connect to existing messaging endpoints
2. Implement contractor aliases
3. Apply message filtering rules

---

## ⏱️ BID CARD URGENCY LEVELS

**Actual Project Timelines (not development timelines):**
- **Emergency**: 24-48 hours (plumbing leak, electrical issue)
- **Urgent**: This week (HVAC in summer, roof leak)
- **Standard**: 2-4 weeks (kitchen remodel planning)
- **Flexible**: 1-3 months (landscaping, additions)
- **Group Bidding**: Coordinated timeline for multiple properties

---

## 🔌 WebSocket Integration

For real-time updates:
```javascript
// Connect to Supabase realtime
const bidCardSubscription = supabase
  .channel('bid-cards-changes')
  .on('postgres_changes', {
    event: '*',
    schema: 'public',
    table: 'bid_cards'
  }, handleBidCardUpdate)
  .subscribe()
```

---

## ✅ NEXT STEPS

1. **Start with existing endpoints** - Don't create new ones
2. **Use defined tables** - bid_cards, bids, messages, etc.
3. **Follow messaging rules** - Content filtering is mandatory
4. **Test with real data** - Ensure compatibility with backend
5. **Coordinate with backend agent** - Confirm any questions

---

This aligned plan ensures we're using the exact same endpoints and tables as the backend implementation!
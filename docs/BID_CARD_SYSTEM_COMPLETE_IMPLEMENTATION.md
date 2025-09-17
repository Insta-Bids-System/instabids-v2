# InstaBids Bid Card System - Complete Implementation Guide

## Overview
This document details the comprehensive bid card system built by Agent 1 (Frontend) that supports multiple presentation modes for homeowners, contractors, and public marketplace browsing. This system is the core of InstaBids' project bidding functionality.

## System Architecture

### Frontend Components Location
All TypeScript/React components are in: `web/src/`

### Backend API Location  
All API endpoints are in: `ai-agents/routers/`

### Database Migrations
Schema changes are in: `ai-agents/migrations/`

---

## 1. DATABASE SCHEMA

### Tables Created/Modified

#### bid_cards (EXTENDED)
```sql
-- Location: Already exists, but added these columns
ALTER TABLE bid_cards ADD:
- title VARCHAR(255)
- description TEXT
- budget_min DECIMAL(10, 2)
- budget_max DECIMAL(10, 2)
- timeline_start DATE
- timeline_end DATE
- timeline_flexibility VARCHAR(20) DEFAULT 'flexible'
- location_address TEXT
- location_city VARCHAR(100)
- location_state VARCHAR(50)
- location_zip VARCHAR(20)
- location_lat DECIMAL(10, 8)
- location_lng DECIMAL(11, 8)
- project_type VARCHAR(100)
- categories TEXT[]
- requirements TEXT[]
- preferred_schedule TEXT[]
- visibility VARCHAR(20) DEFAULT 'public'
- group_bid_eligible BOOLEAN DEFAULT false
- group_bid_id UUID REFERENCES group_bids(id)
- bid_count INTEGER DEFAULT 0
- interested_contractors INTEGER DEFAULT 0
- bid_deadline TIMESTAMP
- auto_close_after_bids INTEGER
- allows_questions BOOLEAN DEFAULT true
- requires_bid_before_message BOOLEAN DEFAULT false
- published_at TIMESTAMP
- metadata JSONB DEFAULT '{}'
```

#### contractor_bids (NEW)
```sql
CREATE TABLE contractor_bids (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_card_id UUID NOT NULL REFERENCES bid_cards(id),
  contractor_id UUID NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  timeline_start DATE NOT NULL,
  timeline_end DATE NOT NULL,
  proposal TEXT NOT NULL,
  approach TEXT,
  materials_included BOOLEAN DEFAULT false,
  warranty_details TEXT,
  status VARCHAR(20) DEFAULT 'draft',
  allows_messages BOOLEAN DEFAULT true,
  last_message_at TIMESTAMP,
  submitted_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(bid_card_id, contractor_id)
);
```

#### bid_card_messages (NEW)
```sql
CREATE TABLE bid_card_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_card_id UUID NOT NULL REFERENCES bid_cards(id),
  bid_id UUID REFERENCES contractor_bids(id),
  sender_id UUID NOT NULL,
  sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('homeowner', 'contractor')),
  recipient_id UUID NOT NULL,
  recipient_type VARCHAR(20) NOT NULL CHECK (recipient_type IN ('homeowner', 'contractor')),
  content TEXT NOT NULL,
  is_read BOOLEAN DEFAULT false,
  read_at TIMESTAMP,
  thread_id UUID,
  reply_to_id UUID REFERENCES bid_card_messages(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Other New Tables
- **bid_milestones**: Payment milestones for contractor bids
- **bid_card_images**: Image attachments for bid cards
- **bid_card_documents**: Document attachments
- **message_attachments**: Attachments for messages
- **group_bids**: Group bidding management

---

## 2. FRONTEND COMPONENTS

### TypeScript Interfaces
**Location**: `web/src/types/bidCard.ts`

Key interfaces:
- `BidCard` - Core bid card data structure
- `ContractorBid` - Contractor's bid submission
- `BidCardMessage` - Messaging between parties
- `GroupBid` - Group bidding structure
- `HomeownerBidCardView` - Homeowner-specific view
- `ContractorBidCardView` - Contractor-specific view
- `MarketplaceBidCardView` - Public marketplace view

### React Components

#### HomeownerBidCard
**Location**: `web/src/components/bidcards/HomeownerBidCard.tsx`
- Full CRUD operations for bid cards
- Tabbed interface: Details, Bids, Messages, Media
- Edit mode with form validation
- Real-time bid count and unread messages
- Bid acceptance/rejection interface

#### ContractorBidCard  
**Location**: `web/src/components/bidcards/ContractorBidCard.tsx`
- Bid submission form with validation
- Payment milestone management
- Distance and match score display
- Messaging interface with homeowner
- Bid withdrawal functionality

#### BidCardMarketplace
**Location**: `web/src/components/bidcards/BidCardMarketplace.tsx`
- Grid layout with card previews
- Advanced filtering: location, budget, timeline, categories
- Sorting options: newest, budget, deadline, distance
- Pagination support
- Drawer for detailed view

### Context/State Management
**Location**: `web/src/contexts/BidCardContext.tsx`

Provides:
- `createBidCard()` - Create new bid card
- `updateBidCard()` - Update existing
- `deleteBidCard()` - Delete draft cards
- `publishBidCard()` - Make card active
- `searchBidCards()` - Search with filters
- `submitBid()` - Contractor bid submission
- `sendMessage()` - Messaging functionality
- `subscribeToUpdates()` - Real-time updates (placeholder)

---

## 3. BACKEND API ENDPOINTS

### Main Router
**Location**: `ai-agents/routers/bid_card_api.py`
**Registered in**: `ai-agents/main.py` as `/api/bid-cards`

#### Homeowner Endpoints
- `POST /api/bid-cards` - Create new bid card
- `PUT /api/bid-cards/{bid_card_id}` - Update bid card
- `DELETE /api/bid-cards/{bid_card_id}` - Delete draft bid card
- `GET /api/bid-cards/homeowner` - Get all homeowner's bid cards

#### Contractor Endpoints
- `GET /api/bid-cards/search` - Search marketplace with filters
- `GET /api/bid-cards/{bid_card_id}/contractor-view` - Get detailed view
- `POST /api/bid-cards/contractor-bids` - Submit a bid
- `PUT /api/bid-cards/contractor-bids/{bid_id}` - Update bid
- `DELETE /api/bid-cards/contractor-bids/{bid_id}` - Withdraw bid

#### Messaging Endpoints
- `POST /api/bid-cards/messages` - Send message
- `GET /api/bid-cards/{bid_card_id}/messages` - Get messages
- `PUT /api/bid-cards/messages/{message_id}/read` - Mark as read
- `GET /api/bid-cards/{bid_card_id}/unread-count` - Get unread count

### Simplified Testing API
**Location**: `ai-agents/routers/bid_card_api_simple.py`
- `GET /api/bid-cards/search` - Simplified search without auth
- `POST /api/bid-cards/test-data` - Create test bid cards

---

## 4. KEY FEATURES IMPLEMENTED

### Multi-Variant Presentation
1. **Homeowner Mode**: Full editing, bid management, messaging
2. **Contractor Mode**: Bid submission, Q&A, project details
3. **Marketplace Mode**: Public browsing, filtering, discovery

### Messaging System
- Bidirectional communication
- Thread support
- Read receipts
- Attachment support (structure ready)
- Optional "bid before message" requirement

### Group Bidding
- Location-based grouping (city, zip + radius)
- 15-25% estimated savings
- Minimum participant requirements
- Join/bid deadlines

### Search & Discovery
- Filter by: status, location, budget, timeline, categories
- Sort by: date, budget, deadline, distance
- Pagination support
- Match scoring for contractors

---

## 5. INTEGRATION POINTS

### With Other Agents

#### Agent 2 (Backend)
- Uses bid tracking system at `/api/bid-cards/{id}/lifecycle`
- Shares `bid_cards` table with status updates
- Can trigger bid collection workflows

#### Agent 3 (Homeowner Journey)
- Can create bid cards via CIA agent
- Uses `HomeownerBidCard` component for display
- Receives bid card ID after project assessment

#### Agent 4 (Contractor Outreach)
- Uses `ContractorBidCard` for bid submission
- Accesses marketplace via search API
- Sends bids that appear in homeowner view

#### Agent 5 (Automated Comms)
- Can send messages via messaging API
- Updates bid card status for campaigns
- Tracks engagement metrics

#### Agent 6 (Monitoring)
- Monitors bid card creation/completion rates
- Tracks messaging volume
- Analyzes bid submission patterns

---

## 6. USAGE EXAMPLES

### Creating a Bid Card (Frontend)
```typescript
const { createBidCard } = useBidCard();

const newBidCard = await createBidCard({
  title: "Kitchen Renovation",
  description: "Complete kitchen remodel",
  budget_range: { min: 25000, max: 45000 },
  timeline: {
    start_date: "2024-03-01",
    end_date: "2024-05-01",
    flexibility: "flexible"
  },
  location: {
    city: "Austin",
    state: "TX",
    zip_code: "78701"
  },
  project_type: "renovation",
  categories: ["kitchen", "plumbing", "electrical"]
});
```

### Submitting a Bid (API)
```bash
POST /api/bid-cards/contractor-bids
{
  "bid_card_id": "uuid-here",
  "amount": 35000,
  "timeline": {
    "start_date": "2024-03-15",
    "end_date": "2024-04-30"
  },
  "proposal": "Detailed proposal text...",
  "approach": "Our approach includes...",
  "materials_included": true,
  "milestones": [
    {
      "title": "Demo and Prep",
      "amount": 10000,
      "estimated_completion": "2024-03-20"
    }
  ]
}
```

### Searching Bid Cards
```bash
GET /api/bid-cards/search?city=Austin&state=TX&budget_min=20000&budget_max=50000&sort_by=created_at&sort_order=desc
```

---

## 7. TESTING

### Test Page
**Location**: `ai-agents/static/test-bid-cards.html`
- Visual testing interface
- API endpoint testing
- Sample bid card display

### Database Status
- Migration applied successfully
- 58 existing bid cards in database
- 3 bid cards set to "active" status for testing
- Tables created with proper indexes

---

## 8. NEXT STEPS

### Remaining Tasks
1. **WebSocket Integration**: Real-time updates for messages and bid submissions
2. **File Upload**: Implement actual file upload for images/documents
3. **Authentication**: Replace mock auth with real user system
4. **Email Notifications**: Integrate with notification system

### For Other Agents
- Use the API endpoints documented above
- Import TypeScript types from `web/src/types/bidCard.ts`
- Context provider available at `web/src/contexts/BidCardContext.tsx`
- All database operations should use the defined schema

---

## NOTES
- All endpoints currently use mock authentication (returns test user)
- WebSocket subscriptions are placeholders
- File uploads store URLs only (not actual files yet)
- Group bidding logic needs coordinator assignment system
# Bid Card Inventory (Backend, Frontend/UI, Tests, Docs)

Scope
- Complete file-level inventory of all places where Bid Card and Potential Bid Card concepts appear, including API routers, services, UI components, hooks/contexts, pages, types, and tests.
- Based on repository scan as of current state.

Summary
- Backend routers (primary): 12+ files
- Frontend UI (web/): 20+ components + pages + types/contexts/hooks
- Tests: multiple end-to-end and API tests
- Documentation references: multiple docs mapping data flow and schema

================================================================================

BACKEND (FastAPI in ai-agents/routers)

Core “bid card” family (by filename)
- ai-agents/routers/bid_card_api.py
- ai-agents/routers/bid_card_api_simple.py
- ai-agents/routers/bid_card_event_tracker.py
- ai-agents/routers/bid_card_images_api.py
- ai-agents/routers/bid_card_lifecycle_routes.py
- ai-agents/routers/bid_card_simple_lifecycle.py

Potential bid cards, CIA/COIA, messaging, and related
- ai-agents/routers/cia_potential_bid_cards.py
- ai-agents/routers/cia_routes.py
- ai-agents/routers/cia_routes_unified.py
- ai-agents/routers/intelligent_messaging_api.py
- ai-agents/routers/image_upload_api.py
- ai-agents/routers/iris_actions.py
- ai-agents/routers/my_bids_api.py
- ai-agents/routers/jaa_routes.py
- ai-agents/routers/property_api.py
- ai-agents/routers/project_grouping_api.py
- ai-agents/routers/proposal_review_api.py
- ai-agents/routers/rfi_api.py
- ai-agents/routers/monitoring_routes.py

Notable endpoint responsibilities (verified from code)

cia_potential_bid_cards.py (mounted under /api/cia)
- POST   /potential-bid-cards                                → create potential bid card
- PUT    /potential-bid-cards/{bid_card_id}/field            → update single field (conversation/manual)
- GET    /potential-bid-cards/{bid_card_id}                  → fetch potential bid card
- GET    /conversation/{conversation_id}/potential-bid-card  → fetch by conversation
- GET    /user/{user_id}/potential-bid-cards                 → list user potential bid cards
- POST   /potential-bid-cards/{bid_card_id}/convert-to-bid-card → convert to official bid card
- DELETE /potential-bid-cards/{bid_card_id}                  → delete potential bid card

bid_card_api.py (mounted under /api/bid-cards)
- POST   ""                              → create bid card (homeowner)
- PUT    "/{bid_card_id}"                → update bid card
- DELETE "/{bid_card_id}"                → delete bid card (draft only)
- GET    "/homeowner"                    → homeowner’s bid cards (enhanced view)
- GET    "/search"                       → contractor marketplace search (with internal redirect support)
- GET    "/by-token/{token}"             → public external landing details
- GET    "/{bid_card_id}/contractor-view"→ contractor view
- POST   "/messages"                     → send message on a bid card (security filtered)
- GET    "/{bid_card_id}/messages"       → list messages
- PUT    "/messages/{message_id}/read"   → mark as read
- GET    "/{bid_card_id}/unread-count"   → unread count
- POST   "/{bid_card_id}/select-contractor" → select winner + calculate connection fee
- GET    "/user/{user_id}"               → list a user’s bid cards

Other routers referencing bid cards (reads/writes)
- rfi_api.py                  → RFI flows touching bid_cards and notifications
- image_upload_api.py         → POST /upload/bid-card (images to bid_cards.bid_document.images)
- iris_actions.py             → Update/Create bid cards; update potential bid cards; insert bid_card_items
- my_bids_api.py              → Contractor “My Bids” over bid cards and interactions
- proposal_review_api.py      → Join proposals to bid_cards; enriched detail
- property_api.py             → Create bid card from property repairs
- project_grouping_api.py     → Create per-trade or combined bid cards
- intelligent_messaging_api.py→ Messaging with bid_card_id routing; scope change notifications
- monitoring_routes.py        → counts of bid_cards operations; health reporting
- jaa_routes.py               → JAA generation/update flows + change notifications

================================================================================

FRONTEND / UI (web/)

Pages
- web/src/pages/CIABidCardDemo.tsx
  - Imports CIAChatWithBidCardPreview; toggles a bid card preview panel with onProjectReady callback
- web/src/pages/DashboardPage.tsx
- web/src/pages/TestPotentialBidCard.tsx
- web/src/pages/ContractorDashboardPage.tsx
- web/src/pages/HomePage.tsx
- web/src/pages/ProjectDetailPage.tsx
- web/public/test-bid-cards.html

Bid card specific components (directory)
- web/src/components/bidcards/
  - BidCardEditModal.tsx
  - BidCardMarketplace.tsx
  - EnhancedBidCardMarketplace.tsx
  - ContractorBidCard.tsx
  - HomeownerBidCard.tsx
  - LiveBidCard.tsx
  - PotentialBidCard.tsx
  - PotentialBidCardWithImages.tsx
  - README.md
  - external/ExternalBidCard.tsx
  - homeowner/BidCardPreview.tsx
  - homeowner/EnhancedBidCard.tsx
  - homeowner/HomeownerProjectWorkspace.tsx
  - homeowner/HomeownerProjectWorkspaceFixed.tsx
  - homeowner/HomeownerProjectWorkspaceSimple.tsx
  - homeowner/InternalBidCard.tsx

Chat and preview components embedding/previewing bid cards
- web/src/components/chat/DynamicBidCardPreview.tsx
  - Fetches GET /api/cia/conversation/{conversationId}/potential-bid-card, PUT field updates, shows completion, missing fields, photos
- web/src/components/chat/CIAChatWithBidCardPreview.tsx
  - Uses usePotentialBidCard; streams chat to /api/cia/stream; supports image uploads, conversion to official bid card; renders DynamicBidCardPreview panel
- web/src/components/chat/BSABidCardsDisplay.tsx
- web/src/components/chat/ChatBidCardAttachment.tsx
- web/src/components/chat/MockBidCardPreview.tsx
- web/src/components/chat/BSAChat.tsx, CIAChat.tsx, StreamingCOIAChat.tsx (contextual usage)
- web/public/test-bid-cards.html (static test page)

Admin views referencing bid cards
- web/src/components/admin/
  - AdminBidCardEnhanced.tsx
  - BidCardImagesViewer.tsx
  - BidCardLifecycleView.tsx
  - BidCardMonitor.tsx
  - BidCardMonitorEnhanced.tsx
  - BidCardTable.tsx
  - MainDashboard.tsx (composite)
  - AgentStatusPanel.tsx (update streams include bid_card_update)

Contexts, Hooks, Types
- web/src/contexts/BidCardContext.tsx
  - Frontend API wrapper for /api/bid-cards (create, update, delete, publish, search, unread counts, messaging)
- web/src/hooks/usePotentialBidCard.ts
  - Endpoints: POST /api/cia/potential-bid-cards; GET /api/cia/conversation/{conversationId}/potential-bid-card;
    PUT /api/cia/potential-bid-cards/{id}/field; POST /api/cia/potential-bid-cards/{id}/convert-to-bid-card
- web/src/types/bidCard.ts
  - Comprehensive TS types for bid cards, bids, messages, marketplace and view models

Other front-end references
- web/src/components/homeowner/RFI* (RFI UI intersects with bid card flows)
- web/src/components/inspiration/PotentialBidCardsInspiration.tsx (inspiration → potential bid card UX)

================================================================================

USAGE RELATIONSHIPS (selected, verified)

Preview and conversion path
- Page: web/src/pages/CIABidCardDemo.tsx
  → Component: web/src/components/chat/CIAChatWithBidCardPreview.tsx
    → Hook: web/src/hooks/usePotentialBidCard.ts (auto-creates potential bid card and polls it)
    → Preview: web/src/components/chat/DynamicBidCardPreview.tsx (fetches potential bid card by conversation)
    → Convert: POST /api/cia/potential-bid-cards/{id}/convert-to-bid-card (called by hook)

Homeowner management + marketplace
- Context: web/src/contexts/BidCardContext.tsx
  → /api/bid-cards CRUD (create/update/delete/publish)
  → /api/bid-cards/search marketplace feed
  → /api/bid-cards/{id}/contractor-view contractor detail
  → Messaging/unread counts over /api/bid-cards endpoints

Admin surfaces
- web/src/components/admin/*BidCard*.tsx render lifecycle, monitor, tables, images around bid cards

Potential bid card edit card
- web/src/components/bidcards/PotentialBidCard.tsx
  - Standalone edit/complete card UI with edit modal and conversion affordance (may be embedded in other flows)

================================================================================

TESTS

Repository root (Python/AIOHTTP etc.)
- test_cia_realtime_bid_card.py (real-time potential bid card E2E for CIA)
- test_direct_bid_card_creation.py
- test_complete_bid_card_conversion_flow.py
- test_complete_bid_card_conversion_flow_simple.py
- test_cia_* (multiple CIA tests intersecting with potential bid card creation/updates via CIA endpoints)

Frontend tests (web/)
- web/src/components/__tests__/ (general)
- web/src/test/… (integration stubs involving messaging/bid-card previews)

================================================================================

DOCUMENTATION REFERENCES (selected)

High-level and schema docs
- docs/README.md
  - Mentions: COMPLETE_BID_CARD_ECOSYSTEM_MAP.md, BID_CARD_SYSTEM_COMPLETE_IMPLEMENTATION.md,
    BID_CARD_LIFECYCLE_AGENT_INTEGRATION_GUIDE.md, BID_TRACKING_SYSTEM_INTEGRATION_GUIDE.md
- docs/meta/ProjectMap.md
  - Lists: /api/bid-cards and lifecycle routes
- docs/meta/SchemaDrift.md, docs/meta/SchemaERD.md
  - Discusses bid_cards table, user_id migration, drift with other domains
- docs/meta/PhotoMap.md
  - POST /api/images/upload/bid-card, retrieval, and JSON embedding in bid_cards
- docs/meta/homeowner-id/* (migrations touching bid_cards.user_id etc.)
- docs/SYSTEM_INTERDEPENDENCY_MAP.md & SYSTEM_ARCHITECTURE_* docs
  - Multiple sections on JAA/CDA and bid card flow; historical UI names (e.g., BidCardViewer.tsx, BidCardMonitor.tsx)

================================================================================

KNOWN DATA TABLES (per docs/migrations)
- public.bid_cards (core)
- public.potential_bid_cards (staging during CIA/IRIS flows) — referenced in cia_potential_bid_cards and hook
- contractor_bids, bid_card_items (proposal items), outreach_campaigns linked by bid_card_id
- conversations/unified_* tables may carry bid_card_id in metadata for context/security

================================================================================

NOTES AND ANOMALIES
- Some early file name search attempts returned no matches because the tool searches file content, not file paths. Component names exist in their files but may not be referenced elsewhere by exact string; inventory lists the concrete file paths.
- PotentialBidCard.tsx exists and is implemented; current primary live preview path is DynamicBidCardPreview via CIAChatWithBidCardPreview. PotentialBidCard may be used in other pages or admin tools; usage can be enumerated on request.

================================================================================

NEXT ACTIONS (optional)
- Expand with a Mermaid graph mapping: Page → Component → Hook → API → DB Tables.
- Add per-component “Where Used” index by scanning imports and page render sites.
- Include request/response schema examples for each endpoint family (bid_card_api*, CIA potential, RFI, images).

# Agent 2 - Admin System Complete API Endpoints

## CRITICAL: Agent 2 owns ALL admin functionality
**Problem Solved**: Agent 2 built the admin system but didn't know about all their endpoints. This document is the single source of truth.

## Primary Router: `/routers/admin_routes.py`
**Base Path**: `/api/admin`

### WebSocket Endpoints
- `ws:/api/admin/ws` - Admin WebSocket connection for real-time updates

### Authentication & Session Management
- `POST /api/admin/login` - Admin login with email/password
- `POST /api/admin/logout` - Admin logout
- `GET /api/admin/session` - Get current admin session
- `GET /api/admin/dashboard` - Get admin dashboard data

### Bid Card Management (Agent 2's Core Feature)
- `GET /api/admin/bid-cards` - List all bid cards with filtering
- `POST /api/admin/bid-cards` - Create new bid card
- `GET /api/admin/bid-cards/{card_id}` - Get specific bid card
- `PUT /api/admin/bid-cards/{card_id}` - Update bid card
- `DELETE /api/admin/bid-cards/{card_id}` - Delete bid card
- `POST /api/admin/bid-cards/{card_id}/items` - Add items to bid card
- `PUT /api/admin/bid-cards/{card_id}/items/{item_id}` - Update bid card item
- `DELETE /api/admin/bid-cards/{card_id}/items/{item_id}` - Delete bid card item

### Campaign Management
- `GET /api/admin/campaigns` - List all campaigns
- `POST /api/admin/campaigns` - Create new campaign
- `GET /api/admin/campaigns/{campaign_id}` - Get specific campaign
- `PUT /api/admin/campaigns/{campaign_id}` - Update campaign
- `DELETE /api/admin/campaigns/{campaign_id}` - Delete campaign
- `POST /api/admin/campaigns/{campaign_id}/send` - Send campaign
- `GET /api/admin/campaigns/{campaign_id}/stats` - Get campaign statistics

### System Monitoring
- `GET /api/admin/system/stats` - System statistics
- `GET /api/admin/system/health` - Health check
- `GET /api/admin/activity-log` - Admin activity log

## Additional Admin Endpoints (Found in other files)

### From `/routers/api_endpoints.py`
- `GET /api/admin/users` - List all users
- `PUT /api/admin/users/{user_id}` - Update user
- `DELETE /api/admin/users/{user_id}` - Delete user
- `GET /api/admin/contractors` - List all contractors
- `PUT /api/admin/contractors/{contractor_id}` - Update contractor
- `GET /api/admin/projects` - List all projects
- `PUT /api/admin/projects/{project_id}` - Update project
- `GET /api/admin/bids` - List all bids
- `PUT /api/admin/bids/{bid_id}` - Update bid

### From `/routers/admin_api.py` (DUPLICATE - needs consolidation)
- `POST /api/admin/broadcast` - Send broadcast message
- `GET /api/admin/analytics` - Get analytics data
- `POST /api/admin/reports/generate` - Generate reports
- `GET /api/admin/reports/{report_id}` - Get specific report
- `POST /api/admin/settings` - Update admin settings
- `GET /api/admin/settings` - Get admin settings

### From `/routers/admin_websocket.py`
- `ws:/api/admin/realtime` - Real-time admin updates
- `ws:/api/admin/notifications` - Admin notifications

### From `/routers/admin_bid_cards.py` (DUPLICATE - needs consolidation)
- `GET /api/admin/v2/bid-cards` - Alternative bid card endpoint
- `POST /api/admin/v2/bid-cards/bulk` - Bulk bid card operations
- `GET /api/admin/v2/bid-cards/templates` - Bid card templates
- `POST /api/admin/v2/bid-cards/templates` - Create bid card template

## Database Tables Owned by Agent 2
- `admin_sessions` - Admin authentication sessions
- `admin_activity_log` - Audit trail of admin actions
- `campaigns` - Marketing campaign management
- `campaign_recipients` - Campaign recipient tracking
- `campaign_stats` - Campaign performance metrics
- `admin_settings` - System-wide admin settings
- `admin_notifications` - Admin notification queue

## Frontend Components (Agent 2's UI)
**Location**: `/src/components/admin/`
- `AdminLogin.tsx` - Login page
- `AdminDashboard.tsx` - Main dashboard
- `BidCardManager.tsx` - Bid card CRUD interface
- `CampaignManager.tsx` - Campaign management
- `UserManager.tsx` - User administration
- `SystemMonitor.tsx` - System health monitoring
- `ActivityLog.tsx` - Audit trail viewer
- `AdminSettings.tsx` - Settings management

## Integration Points
- **With Agent 1 (Frontend)**: Shares bid card display logic
- **With Agent 3 (Backend Core)**: Uses core authentication
- **With Agent 4 (Database)**: Direct Supabase queries
- **With Agent 5 (AI/ML)**: Campaign optimization suggestions
- **With Agent 6 (QA)**: Activity logging for audits

## Common Issues & Solutions

### Issue 1: "Admin can't see bid cards"
- Check: Admin session in `admin_sessions` table
- Check: WebSocket connection to `/api/admin/ws`
- Check: Bid cards have proper `visibility` settings

### Issue 2: "Campaign not sending"
- Check: Campaign status in `campaigns` table
- Check: Recipients in `campaign_recipients` table
- Check: Email service (MailHog) is running

### Issue 3: "Dashboard loading forever"
- Check: `/api/admin/dashboard` endpoint response
- Check: Admin authentication token
- Check: Database connection

## Testing Checklist for Agent 2
- [ ] Admin can login/logout
- [ ] Dashboard loads with correct stats
- [ ] Bid cards CRUD operations work
- [ ] Campaigns can be created and sent
- [ ] Real-time updates via WebSocket work
- [ ] Activity log captures all actions
- [ ] Settings persist correctly

## IMPORTANT: Consolidation Needed
**Duplicate Routers to Merge**:
1. `admin_routes.py` + `admin_api.py` → Keep `admin_routes.py`
2. `admin_bid_cards.py` → Merge into `admin_routes.py`
3. `admin_websocket.py` → Already in `admin_routes.py`

**Total Endpoints**: ~50+ endpoints that Agent 2 owns but were scattered across 4+ files

## Contact
**Owner**: Agent 2 - Admin System Development
**Primary File**: `/routers/admin_routes.py`
**Database**: Direct Supabase access via admin role
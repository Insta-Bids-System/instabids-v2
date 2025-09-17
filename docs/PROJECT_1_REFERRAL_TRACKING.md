# Project 1: Referral Tracking & Dashboard

## 📊 Project Scope
Build the core referral tracking infrastructure and ambassador dashboard that forms the foundation of the brand ambassador program.

## 🎯 Key Features

### 1. **Referral Link Generation**
```typescript
// Unique link format: https://instabids.com/ref/{ambassador_id}
// Short link option: https://ibids.link/{custom_slug}
```
- Auto-generated unique IDs
- Custom vanity URLs for top ambassadors
- QR code generation
- Link shortening service

### 2. **Multi-Stage Tracking Pipeline**
- **Stage 1**: Link clicked → Cookie/localStorage tracking
- **Stage 2**: Account created → Associate with referrer
- **Stage 3**: First bid card → Track engagement
- **Stage 4**: Bids received → Monitor activity
- **Stage 5**: Connection made → Calculate earnings

### 3. **Real-Time Analytics Dashboard**
```
Dashboard Sections:
├── Overview Stats (cards)
│   ├── Total Referrals
│   ├── Active Projects  
│   ├── Earnings (pending/paid)
│   └── Ranking/Level
├── Referral Funnel (visualization)
├── Recent Activity Feed
├── Earnings History (table)
└── Performance Trends (charts)
```

### 4. **Database Schema**
```sql
-- New tables needed
referral_links
├── id (uuid)
├── user_id (references homeowners)
├── link_code (unique)
├── custom_slug (nullable)
├── created_at
└── metadata (jsonb)

referral_tracking
├── id (uuid)
├── referral_link_id
├── referred_user_id
├── stage (clicked/signed_up/created_bid/connected)
├── timestamp
├── ip_address
└── user_agent

ambassador_earnings
├── id (uuid)
├── ambassador_id
├── connection_id
├── earning_amount
├── status (pending/paid/cancelled)
├── created_at
└── paid_at
```

### 5. **API Endpoints**
```python
GET  /api/ambassador/dashboard
GET  /api/ambassador/referral-link
POST /api/ambassador/create-custom-link
GET  /api/ambassador/analytics
GET  /api/ambassador/earnings
GET  /api/tracking/click/{link_code}
```

## 🔧 Technical Stack
- **Frontend**: React components for dashboard
- **Backend**: FastAPI endpoints
- **Database**: Supabase with real-time subscriptions
- **Analytics**: PostgreSQL materialized views
- **Tracking**: Edge functions for link clicks

## 📈 Implementation Phases
1. **Week 1-2**: Database schema, basic tracking
2. **Week 3-4**: Dashboard UI components
3. **Week 5-6**: Analytics and visualizations
4. **Week 7-8**: Testing and optimization

## 🎮 Gamification Preview (Phase 2)
- Level badges next to earnings
- Progress bars to next tier
- Achievement notifications
- Leaderboard position indicator
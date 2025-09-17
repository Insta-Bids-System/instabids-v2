# Technical Integration Guide - Brand Ambassador Platform

## 🔌 Integration with Existing Instabids

### **Database Extensions Needed**
```sql
-- Add to existing Supabase schema
-- These tables extend the current system without breaking it

-- Core ambassador tables
CREATE TABLE ambassador_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES homeowners(id),
    referral_code VARCHAR(20) UNIQUE,
    custom_slug VARCHAR(50) UNIQUE,
    points_total INTEGER DEFAULT 0,
    level VARCHAR(20) DEFAULT 'bronze',
    commission_rate DECIMAL(3,2) DEFAULT 0.50,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE referral_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referral_code VARCHAR(20),
    event_type VARCHAR(50), -- clicked/signed_up/created_bid/connected
    user_id UUID REFERENCES homeowners(id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE ambassador_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE referral_tracking ENABLE ROW LEVEL SECURITY;
```

### **API Endpoints to Add**
```python
# Add to existing ai-agents/main.py

# Ambassador endpoints
@app.get("/api/ambassador/profile")
@app.post("/api/ambassador/activate")
@app.get("/api/ambassador/dashboard")
@app.get("/api/ambassador/referral-link")

# Tracking endpoints  
@app.get("/api/track/referral/{code}")
@app.post("/api/track/event")

# Content generation
@app.post("/api/content/generate")
@app.post("/api/content/analyze-photos")

# Social automation
@app.post("/api/social/connect/{platform}")
@app.post("/api/social/post")
@app.get("/api/social/analytics")
```

### **Frontend Components to Build**
```typescript
// New pages in web/src/pages/
├── AmbassadorDashboard.tsx
├── ContentCreator.tsx
├── SocialConnections.tsx
├── Leaderboard.tsx
└── Achievements.tsx

// Shared components in web/src/components/ambassador/
├── ReferralLinkGenerator.tsx
├── EarningsChart.tsx
├── LevelProgress.tsx
├── AchievementBadge.tsx
├── ShareModal.tsx
└── PostComposer.tsx
```

### **Environment Variables to Add**
```bash
# Social Media APIs
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
TWITTER_API_KEY=
TWITTER_API_SECRET=
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=

# Communication APIs
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
SENDGRID_API_KEY=

# Analytics
MIXPANEL_TOKEN=
SEGMENT_WRITE_KEY=
```

## 🔗 Connection Points

### **1. After Project Completion**
```python
# In existing JAA or project completion flow
async def on_project_completed(project_id):
    # Existing logic...
    
    # New: Trigger ambassador content generation
    if user.is_ambassador:
        await generate_success_story_prompt(project_id)
        await notify_content_opportunity(user.id)
```

### **2. During Signup Flow**
```typescript
// In existing signup process
const handleSignup = async (formData, referralCode?) => {
  // Existing user creation...
  
  // New: Track referral
  if (referralCode) {
    await trackReferralEvent(referralCode, 'signed_up', userId);
  }
  
  // New: Offer ambassador activation
  if (await shouldOfferAmbassadorProgram(userId)) {
    redirectTo('/ambassador/welcome');
  }
};
```

### **3. In Homeowner Dashboard**
```typescript
// Add to existing dashboard
<DashboardLayout>
  {/* Existing sections */}
  
  {user.isAmbassador && (
    <AmbassadorWidget 
      earnings={ambassadorData.earnings}
      referrals={ambassadorData.referralCount}
      nextMilestone={ambassadorData.nextAchievement}
    />
  )}
</DashboardLayout>
```

## 🛠️ Development Approach

### **Non-Breaking Additions**
All ambassador features are additive:
- New tables (don't modify existing)
- New API endpoints (don't change existing)
- New UI sections (optional display)
- Separate subdomain option: `ambassadors.instabids.com`

### **Feature Flags**
```python
# Easy rollout control
FEATURE_FLAGS = {
    "ambassador_program": True,
    "ai_content_generation": True,
    "social_automation": False,  # Phase 2
    "gamification": False,       # Phase 2
}
```

### **Testing Strategy**
1. **Isolated Testing**: Ambassador features in separate test environment
2. **Integration Testing**: Ensure no impact on core bid flow
3. **Beta Program**: Roll out to select users first
4. **Gradual Rollout**: Feature flags for controlled deployment

## 📊 Monitoring & Analytics

### **New Metrics to Track**
```python
# Add to existing analytics
class AmbassadorMetrics:
    - referral_funnel_conversion
    - content_generation_usage
    - social_post_performance
    - ambassador_ltv
    - viral_coefficient
    - commission_payout_rate
```

### **Dashboards to Create**
1. **Operations Dashboard**: Monitor ambassador activity
2. **Financial Dashboard**: Track commission obligations
3. **Growth Dashboard**: Measure viral growth metrics
4. **Content Dashboard**: Analyze post performance

## 🚦 Implementation Phases

### **Phase 1: MVP (4 weeks)**
- Basic referral tracking
- Simple dashboard
- Manual commission tracking
- Basic content templates

### **Phase 2: Enhancement (4 weeks)**
- AI content generation
- Automated commissions
- Achievement system
- Social connections

### **Phase 3: Scale (4 weeks)**
- Full automation suite
- Advanced gamification
- Mobile app
- Enterprise features

## ⚠️ Risk Mitigation

### **Technical Risks**
- **API Rate Limits**: Implement queuing and caching
- **Storage Costs**: Use CDN for media files
- **Processing Load**: Background jobs for heavy tasks

### **Business Risks**
- **Commission Liability**: Escrow system for payouts
- **Content Quality**: AI moderation before posting
- **Platform Compliance**: Review social media ToS

### **Security Considerations**
- OAuth token encryption
- PII protection for contacts
- Rate limiting on all endpoints
- Audit trail for commissions
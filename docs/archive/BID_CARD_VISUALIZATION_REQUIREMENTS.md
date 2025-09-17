# Bid Card Visualization Requirements
**Created**: August 4, 2025
**Purpose**: Complete specification of data to display for each bid card in admin dashboard

## 🎯 Core Information (Always Visible)

### 1. **Project Identification**
- Project Type (Kitchen Remodel, Bathroom, etc.)
- Bid Card Number (BC-LIFECYCLE-123456)
- Status Badge (with color coding)
- Urgency Level (week/month/flexible)

### 2. **Homeowner Details**
- Name
- Location (City, State)
- Contact info (on expand)

### 3. **Progress Visualization**
- Visual progress bar showing X/Y bids received
- Percentage to target
- Color changes based on urgency/deadline

### 4. **Time Tracking**
- Created X hours/days ago
- Time until deadline
- Alert icon if deadline approaching (<3 days)

## 📊 Expanded View (Click to Expand)

### 1. **Target Metrics Dashboard**
```
┌─────────────────────────────────────────────┐
│ Target Contractors: 5                       │
│ └─ 3 interested                            │
│                                            │
│ Outreach: 25                               │
│ └─ 8 responded (32%)                       │
│                                            │
│ Messages Sent: 45                          │
│ └─ 42 delivered (93%)                      │
│                                            │
│ Views: 12                                  │
│ └─ Last: 2h ago                           │
└─────────────────────────────────────────────┘
```

### 2. **Project Details Panel**
- Budget Range: $25,000 - $35,000
- Timeline: 4 weeks
- Complexity Score: 7/10
- Deadline: 5 days remaining
- Special Requirements: Listed

### 3. **Contractor Discovery Summary**
- Total contractors found: 156
- Sources breakdown:
  - Google: 45
  - Yelp: 38
  - HomeAdvisor: 43
  - Internal DB: 30
- Quality scores distribution

### 4. **Outreach Campaign Status**
- Channel breakdown:
  - Email: 25 sent, 20 opened (80%)
  - Forms: 15 submitted
  - SMS: 5 sent, 4 delivered
- Response rates by channel
- Next automated check-in: In 4 hours

### 5. **Engagement Timeline**
Visual timeline showing:
- Bid card created
- Discovery completed (+2h)
- First outreach sent (+3h)
- First contractor viewed (+4h)
- First bid received (+8h)
- 50% target reached (+24h)
- Target met (+36h)

### 6. **Current Bids Summary**
- Number of bids: 3/5
- Bid ranges submitted
- Contractor ratings
- Quick approve/reject buttons

### 7. **Action Buttons**
- View Full Details
- Send Manual Follow-up
- Adjust Targets
- Export Report
- Mark Complete

## 🚨 Alert Indicators

### Visual Alerts for:
1. **Deadline Approaching** (red timer icon)
2. **Low Response Rate** (yellow warning)
3. **Target Met** (green checkmark)
4. **Stalled Progress** (orange pause icon)
5. **Manual Intervention Needed** (blue hand icon)

## 📈 Real-Time Updates

### What Updates in Real-Time:
1. Status changes (color animation)
2. New bid counter increment
3. View count updates
4. Progress bar movement
5. Time-based counters (auto-refresh)
6. New contractor responses

## 🎨 Visual Design

### Status Color Coding:
- **Generated**: Gray (just created)
- **Discovery**: Blue (finding contractors)
- **Active**: Green (collecting bids)
- **Pending Award**: Yellow (reviewing bids)
- **Awarded**: Emerald (contractor selected)
- **In Progress**: Orange (work started)
- **Completed**: Gray with checkmark
- **Cancelled**: Red

### Progress Indicators:
- Circular progress for bid count
- Linear bar for campaign progress
- Pie chart for channel distribution
- Timeline dots for milestones

## 📱 Responsive Behavior

### Desktop (Full View):
- All panels visible
- Side-by-side metrics
- Expanded timeline

### Tablet (Condensed):
- Stacked panels
- Collapsible sections
- Key metrics prioritized

### Mobile (Essential):
- Card stack view
- Tap to expand
- Swipe between cards

## 🔄 User Interactions

### Click Actions:
- Card header: Expand/collapse
- Status badge: Show status history
- Progress bar: Show bid details
- Metrics: Drill down to details
- Timeline events: Show event details

### Hover Effects:
- Highlight actionable elements
- Show tooltips with details
- Preview additional info

### Bulk Actions:
- Select multiple cards
- Bulk status updates
- Export selected data
- Archive completed cards
# Project 2: AI Social Content Generator

## 🤖 Project Scope
Build an AI-powered system that helps brand ambassadors create engaging social media content about their Instabids experience, complete with before/after photos, compelling captions, and automatic referral link integration.

## 🎯 Key Features

### 1. **Smart Photo Analysis**
- Before/after photo upload and pairing
- AI-powered improvement detection
- Auto-cropping for platform requirements
- Filter/enhancement suggestions
- Watermark options with Instabids branding

### 2. **AI Caption Generation**
```python
# Example prompt structure
{
  "project_type": "kitchen_remodel",
  "savings": "$3,500",
  "contractor_name": "Mike's Kitchen Pro",
  "completion_time": "3 days",
  "platform": "instagram",
  "tone": "excited_authentic",
  "include_elements": ["savings", "no_sales_meetings", "local_contractor"]
}
```

**Output Variations**:
- Success story format
- Money saved focus
- Time saved angle
- Environmental impact
- Supporting local business
- Before/after transformation

### 3. **Platform-Specific Optimization**
```typescript
interface PlatformConfig {
  instagram: {
    imageRatio: "1:1" | "4:5",
    maxCaptionLength: 2200,
    hashtagLimit: 30,
    features: ["stories", "reels", "posts"]
  },
  facebook: {
    imageRatio: "16:9" | "1:1",
    maxTextLength: 63206,
    features: ["posts", "stories", "marketplace"]
  },
  twitter: {
    imageRatio: "16:9" | "1:1",
    maxLength: 280,
    features: ["tweets", "threads"]
  },
  tiktok: {
    videoRatio: "9:16",
    maxCaptionLength: 2200,
    features: ["videos", "photos"]
  }
}
```

### 4. **Content Templates Library**

**Hero Messages** (rotate automatically):
- "🏠 Cut out the corporate middleman! Saved $3,500 on my kitchen remodel with @Instabids"
- "🌱 No more wasted gas on sales meetings! Instabids = green home improvement"
- "💰 Contractors save $2000 on leads → I saved 20% on my project. Win-win!"
- "⏰ 3 quotes in 30 minutes vs 3 days of phone tag. Thank you @Instabids!"

**Story Templates**:
- Day 1: "Starting my project journey..."
- Progress: "Look at this transformation!"
- Completion: "The results speak for themselves"
- Savings reveal: "Guess how much I saved?"

### 5. **Engagement Learning System**
- Track which posts perform best
- A/B test different messages
- Learn user's posting style
- Suggest optimal posting times
- Hashtag performance analytics

## 🔧 Technical Implementation

### **AI Integration**
```python
# Multi-model approach
class ContentGenerator:
    def __init__(self):
        self.vision_model = "Claude Vision"  # Photo analysis
        self.copy_model = "Claude Opus"      # Caption writing
        self.style_model = "GPT-4"           # Style matching
    
    async def generate_post(self, photos, project_data, platform):
        # 1. Analyze photos for key improvements
        # 2. Extract project highlights
        # 3. Generate platform-specific content
        # 4. Inject referral link naturally
        # 5. Add relevant hashtags/mentions
```

### **Content Generation Pipeline**
1. **Input**: Photos + project data + platform selection
2. **Analysis**: AI extracts key visual improvements
3. **Generation**: Multiple caption options created
4. **Optimization**: Platform-specific formatting
5. **Preview**: Show mockup of final post
6. **Scheduling**: Queue for optimal time

### **Database Schema**
```sql
generated_content
├── id (uuid)
├── ambassador_id
├── project_id
├── platform
├── content_type (post/story/reel)
├── caption_text
├── hashtags (text[])
├── media_urls (jsonb)
├── ai_analysis (jsonb)
├── performance_metrics (jsonb)
└── created_at

content_templates
├── id
├── category (hero/story/savings)
├── platform
├── template_text
├── variables (jsonb)
└── performance_score
```

## 📱 User Experience Flow
1. **Upload photos** (before/after optional)
2. **Select platform(s)** for posting
3. **Choose tone** (professional/casual/excited)
4. **AI generates** 3-5 caption options
5. **Preview** how post will look
6. **Edit** if desired
7. **Post now** or schedule

## 🎨 UI Components Needed
- Photo upload with drag-drop
- Platform selector (multi-select)
- Caption editor with emoji picker
- Preview cards for each platform
- Performance prediction indicator
- One-click posting buttons

## 🚀 Development Phases
1. **Week 1-2**: Photo upload and AI analysis
2. **Week 3-4**: Caption generation engine
3. **Week 5-6**: Platform integrations
4. **Week 7-8**: Analytics and learning system
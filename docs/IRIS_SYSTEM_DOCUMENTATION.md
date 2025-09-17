# Iris System Documentation - Complete Implementation Guide

## Overview
Iris is InstaBids' AI-powered design assistant that helps homeowners organize their renovation inspiration, analyze their current spaces, and create comprehensive project visions for contractors. 

**Key Change (January 2025)**: Iris has been completely refactored to focus on inspiration discovery and organization, removing all image generation capabilities in favor of helping users find and organize real inspiration from online sources.

## System Architecture

### Backend Implementation
- **Primary File**: `/ai-agents/api/iris_chat_consolidated.py`
- **API Framework**: FastAPI with async/await patterns
- **AI Model**: GPT-4o (GPT-5 when available)
- **Fallback**: Built-in responses when OpenAI unavailable

### Frontend Component
- **Primary File**: `/web/src/components/inspiration/IrisChat.tsx`
- **Framework**: React with TypeScript
- **UI Library**: Tailwind CSS with Lucide icons
- **State Management**: React hooks (useState, useEffect)

### Database Schema
```sql
-- Inspiration Boards
inspiration_boards:
  - id (UUID, PK)
  - homeowner_id (UUID, FK to profiles)
  - title (text)
  - description (text)
  - room_type (text)
  - status (text: collecting/analyzing/complete)
  - created_at (timestamp)
  - updated_at (timestamp)

-- Inspiration Images
inspiration_images:
  - id (UUID, PK)
  - board_id (UUID, FK)
  - homeowner_id (UUID, FK)
  - image_url (text)
  - category (text: ideal/current)
  - tags (text[])
  - ai_analysis (jsonb)
  - source (text: upload/url/generated)
  - created_at (timestamp)

-- Conversations
inspiration_conversations:
  - id (UUID, PK)
  - board_id (UUID, FK)
  - homeowner_id (UUID, FK)
  - messages (jsonb[])
  - created_at (timestamp)
  - updated_at (timestamp)
```

## Core Features

### 1. Inspiration Discovery
**Endpoint**: `POST /api/iris/find-inspiration`
```json
{
  "search_query": "modern kitchen ideas",
  "homeowner_id": "user-uuid",
  "board_id": "board-uuid"
}
```
**Purpose**: Uses GPT to search for and describe design inspiration based on user preferences.

### 2. Image Analysis & Categorization
**Endpoint**: `POST /api/iris/analyze-image`
```json
{
  "image_urls": ["url1", "url2"],
  "category": "ideal" | "current",
  "board_id": "board-uuid",
  "analysis_prompt": "Analyze this kitchen"
}
```
**Purpose**: Analyzes uploaded images to understand design preferences (ideal) or current conditions (current).

### 3. Vision Summary Creation
**Endpoint**: `POST /api/iris/create-vision-summary`
```json
{
  "board_id": "board-uuid",
  "ideal_image_id": "image-uuid",
  "current_image_id": "image-uuid",
  "homeowner_id": "user-uuid"
}
```
**Purpose**: Creates comprehensive project summaries combining current space analysis with design goals.

### 4. Conversational Chat
**Endpoint**: `POST /api/iris/chat`
```json
{
  "message": "Help me organize my kitchen ideas",
  "homeowner_id": "user-uuid",
  "board_id": "board-uuid",
  "conversation_context": []
}
```
**Purpose**: Main conversational interface for design assistance and project planning.

## User Workflow

### Step 1: Initial Engagement
1. User opens Iris chat from Inspiration Dashboard
2. Iris greets with context-aware message
3. User can immediately start chatting or uploading images

### Step 2: Image Organization
1. User uploads "Current Space" photos
   - Iris analyzes existing conditions
   - Identifies improvement opportunities
   - Tags images for organization

2. User uploads "Ideal Inspiration" images
   - Iris identifies style preferences
   - Extracts key design elements
   - Creates preference profile

### Step 3: Inspiration Discovery
1. User asks Iris to find inspiration
2. Iris searches online for matching styles
3. Presents curated design ideas
4. User can refine search with feedback

### Step 4: Vision Summary
1. Iris combines all inputs into vision document
2. Creates contractor-ready project brief
3. Identifies key transformations needed
4. Provides material and style specifications

### Step 5: Contractor Handoff
1. Vision summary shared with contractors
2. Clear communication of homeowner preferences
3. Reduced miscommunication and revisions
4. Faster, more accurate project quotes

## Key Improvements (January 2025)

### Removed Features
- ❌ DALL-E image generation
- ❌ Leonardo.ai integration
- ❌ AI-generated dream spaces
- ❌ Image regeneration with feedback

### Added Features
- ✅ Online inspiration discovery
- ✅ Current vs ideal categorization
- ✅ Vision summary creation
- ✅ Contractor-ready briefs
- ✅ Smart image tagging
- ✅ Project organization

### Technical Improvements
- Consolidated from 3 backends to 1
- Consolidated from 2 frontends to 1
- Removed Claude Opus dependency
- Streamlined API endpoints
- Improved error handling
- Better fallback responses

## API Response Examples

### Chat Response
```json
{
  "response": "I'd love to help you explore modern kitchen designs...",
  "suggestions": [
    "Show me farmhouse styles",
    "Find minimalist kitchens",
    "Explore two-tone designs",
    "Search for backsplash ideas"
  ],
  "board_id": "uuid",
  "created_board": false
}
```

### Image Analysis Response
```json
{
  "analysis": "This kitchen features beautiful white shaker cabinets...",
  "tags": ["modern-farmhouse", "white-cabinets", "marble-counters"],
  "category": "ideal"
}
```

### Vision Summary Response
```json
{
  "summary": "Your project combines modern farmhouse aesthetics...",
  "key_elements": [
    "White shaker cabinetry",
    "Quartz countertops",
    "Matte black hardware"
  ],
  "next_steps": [
    "Get contractor quotes",
    "Finalize materials",
    "Create timeline"
  ]
}
```

## Configuration

### Environment Variables
```env
OPENAI_API_KEY=your-key-here
SUPABASE_URL=your-url-here
SUPABASE_ANON_KEY=your-key-here
```

### Frontend Integration
```typescript
// IrisChat component usage
<IrisChat 
  board={currentBoard}
  onClose={() => setShowIris(false)}
/>
```

## Testing

### Backend Testing
```bash
# Test chat endpoint
curl -X POST http://localhost:8008/api/iris/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "homeowner_id": "test-id"}'

# Test inspiration finding
curl -X POST http://localhost:8008/api/iris/find-inspiration \
  -H "Content-Type: application/json" \
  -d '{"search_query": "modern kitchen", "homeowner_id": "test-id"}'
```

### Frontend Testing
1. Navigate to http://localhost:5173
2. Open Inspiration Dashboard
3. Click "Chat with Iris"
4. Test image uploads (both categories)
5. Test inspiration finding
6. Test vision summary creation

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Check API key in environment
   - Verify quota/billing status
   - Fallback responses will activate

2. **Image Upload Failures**
   - Check Supabase storage bucket exists
   - Verify CORS settings
   - Check file size limits

3. **Database Errors**
   - Verify Supabase connection
   - Check table permissions
   - Ensure foreign keys exist

## Future Enhancements

### Planned Features
- Integration with real image search APIs
- Pinterest/Houzz API integration
- Advanced style matching algorithms
- Budget estimation from images
- 3D room visualization (non-generated)
- Contractor matching based on style

### Technical Improvements
- Redis caching for responses
- WebSocket for real-time updates
- Multi-modal vision analysis
- Vector search for inspiration
- Progressive web app features

## Maintenance Notes

### Daily Tasks
- Monitor API usage and costs
- Check error logs for failures
- Review user feedback

### Weekly Tasks
- Update inspiration templates
- Review and tag new uploads
- Optimize slow queries

### Monthly Tasks
- Analyze usage patterns
- Update style databases
- Review contractor feedback
- Performance optimization

## Contact & Support

**Owner**: Agent 3 - UX Agent
**Primary Developer**: Claude (January 2025 consolidation)
**Support**: Use standard InstaBids support channels

---

*Last Updated: January 2025*
*Version: 2.0 (Post-Consolidation)*
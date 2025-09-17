# Agent 3: Database Schema Reference
**Last Updated**: January 30, 2025  
**Domain**: Tables and relationships for Homeowner UX features

---

## 🗄️ AGENT 3 OWNED TABLES

### 1. inspiration_boards
**Purpose**: Pinterest-like boards for homeowner project inspiration  
**Status**: ✅ Implemented and working

```sql
CREATE TABLE inspiration_boards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  homeowner_id UUID REFERENCES homeowners(id),
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'collecting', -- collecting, organizing, refining, ready
  cover_image_url TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Usage in UI**:
- `InspirationDashboard.tsx` - Lists all boards
- `BoardCreator.tsx` - Creates new boards
- `BoardView.tsx` - Displays individual board

### 2. inspiration_images
**Purpose**: Images within inspiration boards with AI-generated tags  
**Status**: ✅ Implemented and working

```sql
CREATE TABLE inspiration_images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  board_id UUID REFERENCES inspiration_boards(id) ON DELETE CASCADE,
  image_url TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  file_name TEXT NOT NULL,
  category TEXT, -- 'ideal' or 'current'
  tags TEXT[], -- AI-generated tags
  notes TEXT, -- User notes
  ai_analysis JSONB, -- Claude analysis results
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Usage in UI**:
- `ImageUploader.tsx` - Uploads and saves images
- `BoardView.tsx` - Displays images in grid
- `IrisChat.tsx` - References images in conversations

### 3. inspiration_conversations
**Purpose**: Persistent Iris AI conversations tied to specific boards  
**Status**: ✅ Implemented with memory persistence

```sql
CREATE TABLE inspiration_conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  homeowner_id UUID REFERENCES homeowners(id),
  board_id UUID REFERENCES inspiration_boards(id),
  user_message TEXT NOT NULL,
  assistant_response TEXT NOT NULL,
  conversation_context JSONB, -- Full conversation state
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Usage in UI**:
- `IrisChat.tsx` - Loads and saves conversation history
- Backend: `iris_chat.py` - Manages conversation persistence

### 4. vision_compositions  
**Purpose**: AI-generated composite dream spaces  
**Status**: 🚧 Table exists, feature partially implemented

```sql
CREATE TABLE vision_compositions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  board_id UUID REFERENCES inspiration_boards(id),
  composition_prompt TEXT NOT NULL,
  generated_image_url TEXT,
  composition_data JSONB, -- Style analysis, elements used
  feedback JSONB, -- User feedback for improvements
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Usage in UI**:
- `IrisChat.tsx` - Generates dream spaces (DALL-E integration)
- Future: Dedicated vision composition interface

---

## 🔗 AGENT 3 REFERENCED TABLES (Owned by Other Agents)

### homeowners (Agent 1/Core)
**Purpose**: Base homeowner accounts  
**Agent 3 Usage**: FK reference for all inspiration data

```sql
-- Relevant fields for Agent 3
homeowners (
  id UUID PRIMARY KEY,
  email TEXT,
  name TEXT,
  profile_picture_url TEXT,
  created_at TIMESTAMP
)
```

### projects (Agent 1/2)  
**Purpose**: Main project records created by CIA  
**Agent 3 Need**: ⚠️ CRITICAL - Need UI to display these

```sql
-- Key fields Agent 3 needs to display
projects (
  id UUID PRIMARY KEY,
  homeowner_id UUID,
  title TEXT,
  description TEXT,
  status TEXT, -- active, completed, paused
  budget_range TEXT,
  timeline TEXT,
  created_at TIMESTAMP
)
```

**Missing UI Components**:
- `ProjectCards.tsx` - Grid view of projects ❌
- `ProjectDetail.tsx` - Individual project view ❌

### bid_cards (Agent 2)
**Purpose**: Standardized project specifications  
**Agent 3 Need**: ⚠️ CRITICAL - Need UI to display these

```sql
-- Key fields Agent 3 needs to display  
bid_cards (
  id UUID PRIMARY KEY,
  project_id UUID,
  title TEXT,
  scope_of_work TEXT,
  budget_range TEXT,
  urgency_level TEXT,
  status TEXT,
  created_at TIMESTAMP
)
```

**Missing UI Components**:
- `BidViewer.tsx` - Display bid cards ❌  
- `BidComparison.tsx` - Compare multiple bids ❌

### contractor_responses (Agent 2)
**Purpose**: Contractor bids and responses  
**Agent 3 Need**: Display contractor interest and bids

```sql
-- Key fields Agent 3 needs to display
contractor_responses (
  id UUID PRIMARY KEY,
  bid_card_id UUID,
  contractor_id UUID,
  message TEXT,
  is_hot_lead BOOLEAN,
  interest_level INTEGER,
  created_at TIMESTAMP
)
```

**Missing UI Components**:
- `ContractorList.tsx` - Show interested contractors ❌
- `ContractorDetail.tsx` - Individual contractor info ❌

### messages (Future - Agent 2/3)
**Purpose**: Direct messaging between homeowners and contractors  
**Agent 3 Need**: Real-time messaging interface

```sql
-- Future messaging schema
messages (
  id UUID PRIMARY KEY,
  project_id UUID,
  sender_id UUID,
  recipient_id UUID,
  content TEXT,
  message_type TEXT, -- text, image, file
  read_at TIMESTAMP,
  created_at TIMESTAMP
)
```

**Missing UI Components**:
- `ContractorMessaging.tsx` - Real-time chat ❌
- `MessageThread.tsx` - Conversation history ❌

---

## 📊 DATABASE QUERY PATTERNS

### Agent 3 Common Queries

**Load Homeowner Dashboard**:
```sql
-- Get all projects for homeowner
SELECT * FROM projects 
WHERE homeowner_id = $1 
ORDER BY created_at DESC;

-- Get inspiration boards
SELECT * FROM inspiration_boards 
WHERE homeowner_id = $1 
ORDER BY updated_at DESC;
```

**Project Detail View**:
```sql
-- Get project with bid cards
SELECT p.*, COUNT(bc.id) as bid_count
FROM projects p
LEFT JOIN bid_cards bc ON p.id = bc.project_id
WHERE p.id = $1
GROUP BY p.id;

-- Get bid cards for project
SELECT * FROM bid_cards 
WHERE project_id = $1 
ORDER BY created_at DESC;
```

**Iris Conversation Loading**:
```sql
-- Load conversation history for board
SELECT user_message, assistant_response, created_at
FROM inspiration_conversations
WHERE board_id = $1
ORDER BY created_at ASC;
```

### Performance Considerations

**Indexes Needed**:
```sql
-- Agent 3 specific indexes
CREATE INDEX idx_inspiration_boards_homeowner ON inspiration_boards(homeowner_id);
CREATE INDEX idx_inspiration_images_board ON inspiration_images(board_id);
CREATE INDEX idx_inspiration_conversations_board ON inspiration_conversations(board_id);

-- Cross-agent indexes for Agent 3 queries
CREATE INDEX idx_projects_homeowner ON projects(homeowner_id);
CREATE INDEX idx_bid_cards_project ON bid_cards(project_id);
CREATE INDEX idx_contractor_responses_bid ON contractor_responses(bid_card_id);
```

**Query Optimization**:
- Use pagination for inspiration image lists
- Cache conversation context for Iris
- Preload project count in dashboard
- Use real-time subscriptions for new bids

---

## 🔐 SECURITY & ACCESS PATTERNS

### Row Level Security (RLS)

**Inspiration Tables** (Agent 3 responsibility):
```sql
-- Only homeowner can access their boards
ALTER TABLE inspiration_boards ENABLE ROW LEVEL SECURITY;
CREATE POLICY homeowner_boards ON inspiration_boards
  FOR ALL USING (homeowner_id = auth.uid());

-- Only homeowner can access their images  
ALTER TABLE inspiration_images ENABLE ROW LEVEL SECURITY;
CREATE POLICY homeowner_images ON inspiration_images
  FOR ALL USING (
    board_id IN (
      SELECT id FROM inspiration_boards 
      WHERE homeowner_id = auth.uid()
    )
  );
```

**Cross-Agent Access**:
```sql
-- Agent 3 needs read access to projects
CREATE POLICY homeowner_projects ON projects
  FOR SELECT USING (homeowner_id = auth.uid());

-- Agent 3 needs read access to bid cards
CREATE POLICY homeowner_bid_cards ON bid_cards  
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects 
      WHERE homeowner_id = auth.uid()
    )
  );
```

---

## 🚨 CRITICAL DATA FLOWS

### CIA → Dashboard Flow (BROKEN)
1. CIA creates project in `projects` table ✅
2. Homeowner should see project in dashboard ❌ NO UI
3. **Fix**: Build `ProjectCards.tsx` component

### Backend → Bid Display Flow (BROKEN)  
1. JAA creates bid card in `bid_cards` table ✅
2. CDA finds contractors ✅
3. EAA sends outreach ✅
4. Homeowner should see bid cards ❌ NO UI
5. **Fix**: Build `BidViewer.tsx` component

### Iris Memory Flow (WORKING)
1. User chats with Iris ✅
2. Conversation saves to `inspiration_conversations` ✅
3. Context loads on page refresh ✅
4. Memory persists across sessions ✅

---

## 📋 SCHEMA COMPLETENESS CHECKLIST

### ✅ Working Database Features
- [x] Inspiration board CRUD
- [x] Image upload and storage
- [x] Iris conversation persistence
- [x] AI analysis storage
- [x] RLS security policies

### ❌ Missing UI for Existing Data
- [ ] Project viewing interface
- [ ] Bid card display system  
- [ ] Contractor response viewer
- [ ] Real-time messaging tables
- [ ] Notification system tables

**Bottom Line**: Database schema is mostly complete, but Agent 3 is missing critical UI components to display data that other agents are creating.
# API Contracts

## Frontend ↔ LangGraph Backend

### Base URL
- Development: `http://localhost:8000`
- Production: `https://api.instabids.com`

### Authentication
All requests require Supabase JWT token in Authorization header:
```
Authorization: Bearer <supabase_jwt_token>
```

## CIA Agent Endpoints

### Start Conversation
```http
POST /api/agents/cia/start
```

Request:
```json
{
  "user_id": "uuid"
}
```

Response:
```json
{
  "thread_id": "uuid",
  "message": "Hi! I'm here to help you post your project...",
  "status": "active"
}
```

### Send Message
```http
POST /api/agents/cia/message
```

Request:
```json
{
  "thread_id": "uuid",
  "message": "I need to renovate my bathroom",
  "images": ["url1", "url2"] // optional
}
```

Response:
```json
{
  "message": "I can help with that! Can you tell me more about...",
  "project_data": {
    "title": "Bathroom Renovation",
    "category": "renovation",
    "description": "...",
    "budget_min": null,
    "budget_max": null
  },
  "status": "intake", // intake | review | completed
  "suggested_actions": ["add_photos", "set_budget"]
}
```

### Get Conversation State
```http
GET /api/agents/cia/conversation/{thread_id}
```

Response:
```json
{
  "thread_id": "uuid",
  "messages": [
    {
      "role": "assistant",
      "content": "...",
      "timestamp": "2024-01-20T10:00:00Z"
    },
    {
      "role": "user", 
      "content": "...",
      "timestamp": "2024-01-20T10:01:00Z"
    }
  ],
  "project_data": {},
  "status": "active"
}
```

## Frontend ↔ Supabase

### Authentication
```typescript
// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Get session
const { data: { session } } = await supabase.auth.getSession()
```

### Projects
```typescript
// Create project (after CIA completion)
const { data, error } = await supabase
  .from('projects')
  .insert({
    title: 'Bathroom Renovation',
    description: '...',
    category: 'renovation',
    budget_range: { min: 5000, max: 15000 },
    status: 'posted',
    cia_conversation_id: 'thread_uuid'
  })
  .select()
  .single()

// Get user's projects
const { data, error } = await supabase
  .from('projects')
  .select(`
    *,
    bids (
      id,
      amount,
      timeline_days,
      contractor:contractors(
        business_name,
        rating
      )
    )
  `)
  .eq('homeowner_id', userId)
  .order('created_at', { ascending: false })
```

### Real-time Subscriptions
```typescript
// Subscribe to new bids
const channel = supabase
  .channel('project-bids')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'bids',
      filter: `project_id=eq.${projectId}`
    },
    (payload) => {
      console.log('New bid received!', payload.new)
    }
  )
  .subscribe()

// Subscribe to messages
const messageChannel = supabase
  .channel('project-messages')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'messages',
      filter: `project_id=eq.${projectId}`
    },
    (payload) => {
      console.log('New message!', payload.new)
    }
  )
  .subscribe()
```

### File Upload
```typescript
// Upload project image
const { data, error } = await supabase.storage
  .from('project-images')
  .upload(`${userId}/${projectId}/${filename}`, file, {
    contentType: file.type,
    upsert: false
  })

// Get public URL
const { data: { publicUrl } } = supabase.storage
  .from('project-images')
  .getPublicUrl(`${userId}/${projectId}/${filename}`)
```

## WebSocket Events (Future)

### Agent Status Updates
```json
{
  "event": "agent.status",
  "data": {
    "agent": "CIA",
    "status": "processing",
    "message": "Analyzing your project requirements..."
  }
}
```

### Bid Notifications
```json
{
  "event": "bid.new",
  "data": {
    "project_id": "uuid",
    "contractor_name": "ABC Plumbing",
    "amount": 12500,
    "timeline_days": 5
  }
}
```

## Error Responses

All endpoints use consistent error format:
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Human-readable error message",
    "details": {} // Optional additional context
  }
}
```

Common error codes:
- `UNAUTHORIZED` - Invalid or missing auth token
- `NOT_FOUND` - Resource not found
- `INVALID_REQUEST` - Request validation failed
- `AGENT_ERROR` - LangGraph agent error
- `RATE_LIMITED` - Too many requests
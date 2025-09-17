# Schema ERD (Derived from supabase/migrations)

Source migrations scanned:
- supabase/migrations/20250126_initial_schema.sql
- supabase/migrations/20250126_row_level_security.sql
- supabase/migrations/20250127_dev_testing_policies.sql

This document reflects what is actually defined in the migrations (authoritative for DB). It does not infer additional tables referenced in code that aren’t present here; see SchemaDrift.md for gaps vs code usage.

---

## Entities and Relationships

profiles (extends auth.users)
- id UUID PK (FK → auth.users.id)
- email TEXT UNIQUE NOT NULL
- full_name TEXT
- phone TEXT
- role user_role NOT NULL DEFAULT 'homeowner'  (ENUM: homeowner | contractor | admin)
- avatar_url TEXT
- created_at, updated_at TIMESTAMPTZ (triggered)

contractors
- id UUID PK DEFAULT uuid_generate_v4()
- profile_id UUID NOT NULL (FK → profiles.id) UNIQUE
- business_name TEXT NOT NULL
- license_number TEXT
- insurance_info JSONB
- service_areas TEXT[]  (GIN indexed)
- specialties TEXT[]    (GIN indexed)
- years_experience INTEGER
- rating DECIMAL(3,2) DEFAULT 0.00
- total_reviews INTEGER DEFAULT 0
- verified BOOLEAN DEFAULT FALSE (indexed)
- stripe_account_id TEXT
- created_at, updated_at TIMESTAMPTZ (triggered)
Relationships:
- contractors.profile_id → profiles.id (1:1)

projects
- id UUID PK DEFAULT uuid_generate_v4()
- homeowner_id UUID NOT NULL (FK → profiles.id) (indexed)
- title TEXT NOT NULL
- description TEXT NOT NULL
- category TEXT NOT NULL
- urgency TEXT CHECK ('emergency' | 'urgent' | 'flexible')
- budget_range JSONB
- location JSONB
- images TEXT[]
- status project_status NOT NULL DEFAULT 'draft'  (ENUM: draft | active | in_progress | completed | cancelled) (indexed)
- ai_analysis JSONB
- created_at, updated_at TIMESTAMPTZ, completed_at TIMESTAMPTZ (triggered)
Relationships:
- projects.homeowner_id → profiles.id (M:1)

bids
- id UUID PK DEFAULT uuid_generate_v4()
- project_id UUID NOT NULL (FK → projects.id) (indexed)
- contractor_id UUID NOT NULL (FK → contractors.id) (indexed)
- amount DECIMAL(10,2) NOT NULL
- description TEXT NOT NULL
- timeline TEXT
- status bid_status NOT NULL DEFAULT 'pending' (ENUM: pending | accepted | rejected | withdrawn) (indexed)
- created_at, updated_at TIMESTAMPTZ (triggered)
- UNIQUE(project_id, contractor_id)
Relationships:
- bids.project_id → projects.id (M:1)
- bids.contractor_id → contractors.id (M:1)

messages
- id UUID PK DEFAULT uuid_generate_v4()
- conversation_id UUID NOT NULL
- sender_id UUID NOT NULL (FK → profiles.id)
- recipient_id UUID NOT NULL (FK → profiles.id)
- content TEXT NOT NULL
- encrypted BOOLEAN DEFAULT TRUE
- read_at TIMESTAMPTZ
- created_at TIMESTAMPTZ DEFAULT NOW()
Indexes:
- idx_messages_conversation_id
- idx_messages_created_at
Relationships:
- messages.sender_id → profiles.id
- messages.recipient_id → profiles.id
- messages.conversation_id → conversations.id (implicit; FK not declared in migration, but referenced by policies)

conversations
- id UUID PK DEFAULT uuid_generate_v4()
- project_id UUID NOT NULL (FK → projects.id)
- homeowner_id UUID NOT NULL (FK → profiles.id)
- contractor_id UUID NOT NULL (FK → contractors.id)
- last_message_at TIMESTAMPTZ
- created_at TIMESTAMPTZ DEFAULT NOW()
- UNIQUE(project_id, contractor_id)
Suggested indexes: project_id, homeowner_id, contractor_id, last_message_at (see index SQL recommendations)
Relationships:
- conversations.project_id → projects.id
- conversations.homeowner_id → profiles.id
- conversations.contractor_id → contractors.id

payments
- id UUID PK DEFAULT uuid_generate_v4()
- project_id UUID NOT NULL (FK → projects.id)
- bid_id UUID NOT NULL (FK → bids.id)
- payer_id UUID NOT NULL (FK → profiles.id)
- recipient_contractor_id UUID NOT NULL (FK → contractors.id)
- amount DECIMAL(10,2) NOT NULL
- stripe_payment_intent_id TEXT UNIQUE
- status payment_status NOT NULL DEFAULT 'pending' (ENUM: pending | processing | completed | failed | refunded)
- created_at TIMESTAMPTZ DEFAULT NOW()
- completed_at TIMESTAMPTZ
Suggested indexes: project_id, bid_id, payer_id, recipient_contractor_id, status

ai_conversations
- id UUID PK DEFAULT uuid_generate_v4()
- user_id UUID NOT NULL (FK → profiles.id) (indexed)
- agent_type TEXT CHECK (CIA | CoIA | JAA | CDA | EAA | SMA | CHO | CRA)
- thread_id TEXT NOT NULL (indexed)
- state JSONB NOT NULL
- created_at, updated_at TIMESTAMPTZ (triggered)

contractor_discovery_cache
- id UUID PK DEFAULT uuid_generate_v4()
- query_hash TEXT NOT NULL UNIQUE
- results JSONB NOT NULL
- created_at TIMESTAMPTZ DEFAULT NOW()
- expires_at TIMESTAMPTZ NOT NULL
Suggested index: expires_at (for efficient cleanup)

reviews
- id UUID PK DEFAULT uuid_generate_v4()
- project_id UUID NOT NULL (FK → projects.id)
- contractor_id UUID NOT NULL (FK → contractors.id)
- reviewer_id UUID NOT NULL (FK → profiles.id)
- rating INTEGER NOT NULL CHECK (1..5)
- comment TEXT
- created_at TIMESTAMPTZ DEFAULT NOW()
Suggested indexes: contractor_id, project_id, reviewer_id

---

## Indexes Present (from migration)

- profiles(role)
- contractors(verified), contractors USING GIN(service_areas), USING GIN(specialties)
- projects(homeowner_id), projects(status)
- bids(project_id), bids(contractor_id), bids(status)
- messages(conversation_id), messages(created_at)
- ai_conversations(user_id), ai_conversations(thread_id)

---

## Recommended Additional Indexes (to add via SQL)

- conversations(project_id)
- conversations(homeowner_id)
- conversations(contractor_id)
- conversations(last_message_at)
- messages(conversation_id, created_at DESC) composite for timeline queries
- payments(project_id)
- payments(bid_id)
- payments(payer_id)
- payments(recipient_contractor_id)
- payments(status)
- contractor_discovery_cache(expires_at)
- reviews(contractor_id), reviews(project_id), reviews(reviewer_id)

A generated DDL file is planned at: supabase/sql/index_recommendations.sql

---

## Row-Level Security (RLS) Summary

Enabled on:
- profiles, contractors, projects, bids, messages, conversations, payments, ai_conversations, contractor_discovery_cache, reviews

Key policies (high-level):
- Profiles: users can view/update their own; authenticated users can view public fields
- Contractors: owners manage their profile; verified contractors are discoverable
- Projects: homeowners manage their own; verified contractors can view active projects
- Bids: contractors see theirs; homeowners see bids on their projects; verified contractors can create bids
- Messages: participants can view; inserts allowed when user is part of the conversation
- Conversations: visible to homeowner or contractor participants
- Payments: visible to payer or recipient contractor; homeowners can create for accepted bids
- AI conversations: CRUD for owning user
- Contractor discovery cache: public select (expires_at > NOW()); full manage for service role
- Reviews: public select; homeowners can create for completed+paid projects

Dev-only overrides (20250127_dev_testing_policies.sql):
- Allow anonymous profile creation for emails like test%@instabids.com
- Allow anonymous users to manage AI conversations for those test users

---

## Notes and Next Steps

- This ERD matches the migrations present. Several code paths reference tables not in these migrations (e.g., bid_cards, messaging_system_messages, message_attachments, blocked_messages_log, broadcast_*). See docs/meta/SchemaDrift.md for a gap analysis and reconciliation plan.
- Once SchemaDrift is reconciled (add missing migrations or update code), regenerate ERD and apply the recommended indexes.

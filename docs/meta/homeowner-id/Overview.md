# Homeowner ID Removal Program (Standardize on user_id)

Purpose
- Eliminate homeowner_id everywhere and standardize on user_id (profiles.id).
- Reduce architectural debt, simplify queries/RLS, and remove conversion logic in agents and APIs.
- Align all messaging/memory/image systems on one principal identifier.

Last updated: 2025-08-13

---

Executive Summary
- Today: homeowner_id is a redundant alias for user_id with a 1:1 mapping via homeowners(user_id). Several tables still store homeowner_id (sometimes pointing to homeowners, sometimes profiles).
- Target: one identifier (user_id) across all tables, routers, agents, and readers. Remove homeowners table once all backfilled.
- Rollout: additive → backfill → dual-read/write window (optional) → switch readers → drop homeowner_id columns/table → finalize RLS.

Outcome
- IRIS and CIA stop doing ID conversions.
- Unified system already uses user UUIDs; queries align naturally.
- Less confusion in code and data.

---

Authoritative Inventory (from db snapshots)

Tables with homeowner_id present (direct columns/FKs)
- bid_cards (column homeowner_id present; FK not listed but column exists)
- projects (projects_homeowner_id_fkey → homeowners.id)
- generated_dream_spaces (generated_dream_spaces_homeowner_id_fkey → homeowners.id)
- inspiration_boards (inspiration_boards_homeowner_id_fkey → profiles.id)
- inspiration_conversations (inspiration_conversations_homeowner_id_fkey → profiles.id)
- inspiration_images (inspiration_images_homeowner_id_fkey → profiles.id)
- vision_compositions (vision_compositions_homeowner_id_fkey → profiles.id)
- referral_tracking (referral_tracking_referred_homeowner_id_fkey → homeowners.id)
- homeowners (homeowners_user_id_fkey → profiles.id)

Tables already correct (use user_id)
- Example set from codebase: project_contexts, project_summaries, user_memories, photo_storage, unified_* tables (created_by, entity_id, message sender_id)
- Confirmed by public_foreign_keys.json that unified_* do not use homeowner_id.

Read sources
- docs/meta/db/public_columns.json
- docs/meta/db/public_foreign_keys.json

---

Migration Plan (Safe, Phased)

Core pattern by table
1) Add user_id uuid NULL
2) Backfill:
   - If homeowner_id pointed to profiles.id (inspiration_* and vision_compositions):
     set user_id = homeowner_id
   - If homeowner_id pointed to homeowners.id (projects, generated_dream_spaces, referral_tracking, likely bid_cards):
     join homeowners on homeowner_id = homeowners.id and set user_id = homeowners.user_id
3) Add FK user_id → profiles(id), add supporting indexes
4) Set user_id NOT NULL after validation
5) Update RLS/policies to use user_id
6) Optional dual-read/write window (triggers) to keep legacy stable
7) Drop homeowner_id columns and homeowners table (or replace with view temporarily)

SQL Scripts (templates)

01_add_user_id.sql
```sql
-- Add user_id to tables that currently use homeowner_id
ALTER TABLE public.bid_cards ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.generated_dream_spaces ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.inspiration_boards ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.inspiration_conversations ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.inspiration_images ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.vision_compositions ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.referral_tracking ADD COLUMN IF NOT EXISTS referred_user_id uuid NULL;

-- Indexes for new columns
CREATE INDEX IF NOT EXISTS idx_bid_cards_user_id ON public.bid_cards(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_dream_spaces_user_id ON public.generated_dream_spaces(user_id);
CREATE INDEX IF NOT EXISTS idx_inspiration_boards_user_id ON public.inspiration_boards(user_id);
CREATE INDEX IF NOT EXISTS idx_inspiration_conversations_user_id ON public.inspiration_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_inspiration_images_user_id ON public.inspiration_images(user_id);
CREATE INDEX IF NOT EXISTS idx_vision_compositions_user_id ON public.vision_compositions(user_id);
CREATE INDEX IF NOT EXISTS idx_referral_tracking_referred_user_id ON public.referral_tracking(referred_user_id);

-- FKs to profiles(id)
ALTER TABLE public.bid_cards
  ADD CONSTRAINT bid_cards_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.projects
  ADD CONSTRAINT projects_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.generated_dream_spaces
  ADD CONSTRAINT generated_dream_spaces_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.inspiration_boards
  ADD CONSTRAINT inspiration_boards_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.inspiration_conversations
  ADD CONSTRAINT inspiration_conversations_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.inspiration_images
  ADD CONSTRAINT inspiration_images_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.vision_compositions
  ADD CONSTRAINT vision_compositions_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.referral_tracking
  ADD CONSTRAINT referral_tracking_referred_user_id_fkey
  FOREIGN KEY (referred_user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
```

02_backfill_user_id.sql
```sql
-- Case A: homeowner_id was already profiles.id (just copy value)
UPDATE public.inspiration_boards
SET user_id = homeowner_id
WHERE user_id IS NULL AND homeowner_id IS NOT NULL;

UPDATE public.inspiration_conversations
SET user_id = homeowner_id
WHERE user_id IS NULL AND homeowner_id IS NOT NULL;

UPDATE public.inspiration_images
SET user_id = homeowner_id
WHERE user_id IS NULL AND homeowner_id IS NOT NULL;

UPDATE public.vision_compositions
SET user_id = homeowner_id
WHERE user_id IS NULL AND homeowner_id IS NOT NULL;

-- Case B: homeowner_id points to homeowners.id (need join)
-- projects.user_id ← homeowners.user_id
UPDATE public.projects p
SET user_id = h.user_id
FROM public.homeowners h
WHERE p.user_id IS NULL AND p.homeowner_id = h.id;

-- generated_dream_spaces.user_id ← homeowners.user_id
UPDATE public.generated_dream_spaces g
SET user_id = h.user_id
FROM public.homeowners h
WHERE g.user_id IS NULL AND g.homeowner_id = h.id;

-- bid_cards.user_id ← homeowners.user_id  (column homeowner_id exists, no FK registered)
UPDATE public.bid_cards b
SET user_id = h.user_id
FROM public.homeowners h
WHERE b.user_id IS NULL AND b.homeowner_id = h.id;

-- referral_tracking.referred_user_id ← homeowners.user_id
UPDATE public.referral_tracking r
SET referred_user_id = h.user_id
FROM public.homeowners h
WHERE r.referred_user_id IS NULL AND r.referred_homeowner_id = h.id;
```

03_enforce_not_null_and_constraints.sql
```sql
ALTER TABLE public.bid_cards ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.projects ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.generated_dream_spaces ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.inspiration_boards ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.inspiration_conversations ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.inspiration_images ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.vision_compositions ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.referral_tracking ALTER COLUMN referred_user_id SET NOT NULL;
```

04_dual_read_write_triggers.sql (optional window)
```sql
-- Example for projects: if incoming write sets homeowner_id, mirror into user_id
CREATE OR REPLACE FUNCTION projects_mirror_homeowner_to_user()
RETURNS trigger AS $$
BEGIN
  IF NEW.user_id IS NULL AND NEW.homeowner_id IS NOT NULL THEN
    NEW.user_id := (SELECT user_id FROM public.homeowners WHERE id = NEW.homeowner_id);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_projects_mirror ON public.projects;
CREATE TRIGGER trg_projects_mirror
BEFORE INSERT OR UPDATE ON public.projects
FOR EACH ROW EXECUTE FUNCTION projects_mirror_homeowner_to_user();
```

05_drop_homeowner_id_columns.sql (final cutover)
```sql
-- Drop homeowner_id columns after code is migrated and soak is complete
ALTER TABLE public.bid_cards DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.projects DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.generated_dream_spaces DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.inspiration_boards DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.inspiration_conversations DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.inspiration_images DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.vision_compositions DROP COLUMN IF EXISTS homeowner_id;

-- Rename referral column finally
ALTER TABLE public.referral_tracking
  DROP CONSTRAINT IF EXISTS referral_tracking_referred_homeowner_id_fkey;
ALTER TABLE public.referral_tracking DROP COLUMN IF EXISTS referred_homeowner_id;
```

06_drop_homeowners_table.sql
```sql
-- Optional: replace with compatibility VIEW during a short window instead of immediate drop
-- DROP TABLE public.homeowners;

-- Example compatibility view (maps old id to profile id)
-- CREATE VIEW public.homeowners AS
-- SELECT p.id as id, p.id as user_id, NULL::text as address, NULL::jsonb as preferences,
--        NULL::int as total_projects, NULL::numeric as total_spent
-- FROM public.profiles p;
```

07_policies_rls.sql (templates)
```sql
-- Replace homeowner_id-based policies with user_id-based ones.
-- Example: projects RLS: owner can access own rows
DROP POLICY IF EXISTS projects_owner ON public.projects;
CREATE POLICY projects_owner
ON public.projects
FOR SELECT USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Repeat for each table: inspiration_*, bid_cards (if user-scoped), generated_dream_spaces, referral_tracking (if user-scoped).
```

---

Code Impact (Backend)

Routers/APIs (examples; update all filters/fields)
- bid_card_api.py, bid_card_lifecycle_routes.py:
  - Replace homeowner_id filters with user_id; assign on creation
- projects/property_api.py:
  - WHERE projects.user_id = $user
- inspiration_* routers & vision_compositions:
  - WHERE <table>.user_id = $user  (trivial since prior FK pointed to profiles)
- image_upload_api.py:
  - Replace joins/filters on bid_cards.homeowner_id → bid_cards.user_id
- referral endpoints:
  - referred_homeowner_id → referred_user_id

Agents
- CIA (homeowner):
  - Purge any homeowner_id conversions; verify that anonymous→persistent user flow supplies user_id everywhere
- IRIS:
  - adapters/homeowner_context.py: remove homeowners join; aggregate by user_id
- COIA:
  - Mostly contractor-side; verify any cross-joins through homeowners have been removed

Unified system (unchanged structure)
- Ensure no metadata payloads still store homeowner_id; replace with user_id where present
- Readers/filters rely on created_by/entity_id/sender_id as user UUIDs

Services/Adapters
- database_simple.py / database.py: unify helpers on user_id
- ai-agents/adapters/*: use user_id for context assembly (homeowner/messaging/contractor)

Frontend
- TS types: homeownerId → userId
- API clients: payload/response fields updated accordingly
- Pages/params: replace any homeownerId query params with userId

---

Test Plan

SQL sanity checks
- For each migrated table:
  - SELECT COUNT(*) FROM <table> WHERE user_id IS NULL = 0
  - Compare random samples with old homeowner_id mapping

Unit/integration tests
- Update fixtures: provide user_id only
- Routers: verify access control uses user_id
- Inspiration/dream spaces: verify create/list returns via user_id

E2E tests
- test_frontend_unified_complete.py
- test_homeowner_context_simple.py / complete.py
- test_iris_* (inspiration flows)
- test_messaging_agent_unified.py
- test_unified_api_direct.py

Observability
- Add temporary logs to detect any missing user_id on writes
- Monitor 4xx/5xx on impacted endpoints after deploy

---

Rollout & Rollback

Rollout
1) Apply 01–02 on staging, run tests
2) Apply 03 (NOT NULL), update application code to use user_id, deploy
3) Optional 04 (dual-write triggers) for a short window
4) Remove code paths referencing homeowner_id
5) Apply 05–07 (drop columns/table, update policies), run tests
6) Remove temporary views/triggers

Rollback
- Keep homeowners table and homeowner_id columns until final phase
- Roll back code to legacy reads if needed
- Revert SQL step-by-step in reverse order if required

---

Notes & Caveats
- The public_foreign_keys show inspiration_* homeowner_id referencing profiles(id) already. That means those tables are the simplest: user_id = homeowner_id, then drop homeowner_id.
- bid_cards homeowner_id exists but lacks an FK in the snapshot: add user_id, backfill via homeowners mapping, then drop homeowner_id.
- referral_tracking uses referred_homeowner_id → rename and backfill to referred_user_id.

---

Next Steps (on approval)
- If you want separate files:
  - Write split SQL files to docs/meta/homeowner-id/DB_Migrations/01–07_*.sql
  - Write Code_Impact.md (file/line patterns)
  - Write Test_Plan.md and Rollback.md
- Or keep using this single doc as the authoritative runbook and paste SQL into your migration pipeline.

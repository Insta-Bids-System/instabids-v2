-- 07_policies_rls.sql
-- Purpose: Replace homeowner_id-based Row Level Security (RLS) policies with user_id-based ones.
-- Notes:
--  - Run after schema migration (01..06) and application cutover to user_id.
--  - This script drops known legacy policies and creates new canonical user_id policies.
--  - Adjust roles ("public"/"authenticated"/"anon") to match your Supabase model.

BEGIN;

--------------------------------------------------------------------------------
-- Projects (public.projects)
-- Legacy referenced homeowners table; now owned directly by user_id
--------------------------------------------------------------------------------

-- Drop legacy policies referencing homeowners/homeowner_id
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='projects'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.projects', pol.policyname);
  END LOOP;
END$$;

-- RLS must be enabled at table creation time; assume enabled. If not:
-- ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- Homeowners can manage their own projects (SELECT/INSERT/UPDATE/DELETE)
CREATE POLICY projects_select_own
  ON public.projects
  FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY projects_insert_own
  ON public.projects
  FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY projects_update_own
  ON public.projects
  FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY projects_delete_own
  ON public.projects
  FOR DELETE
  USING (user_id = auth.uid());

-- Optional: contractors/public see posted projects
-- (Preserve prior behavior if desired)
CREATE POLICY projects_select_posted
  ON public.projects
  FOR SELECT
  USING (status = 'posted'::project_status);

--------------------------------------------------------------------------------
-- Bid Cards (public.bid_cards)
-- If you scope bid cards by owner, add user-based policies.
--------------------------------------------------------------------------------

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='bid_cards'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.bid_cards', pol.policyname);
  END LOOP;
END$$;

-- Example ownership policies (uncomment if required by your product rules)
-- CREATE POLICY bid_cards_select_own
--   ON public.bid_cards
--   FOR SELECT
--   USING (user_id = auth.uid());
--
-- CREATE POLICY bid_cards_insert_own
--   ON public.bid_cards
--   FOR INSERT
--   WITH CHECK (user_id = auth.uid());
--
-- CREATE POLICY bid_cards_update_own
--   ON public.bid_cards
--   FOR UPDATE
--   USING (user_id = auth.uid())
--   WITH CHECK (user_id = auth.uid());

--------------------------------------------------------------------------------
-- Inspiration Boards (public.inspiration_boards)
--------------------------------------------------------------------------------

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='inspiration_boards'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.inspiration_boards', pol.policyname);
  END LOOP;
END$$;

-- Canonical policies
CREATE POLICY inspiration_boards_select_own
  ON public.inspiration_boards
  FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY inspiration_boards_insert_own
  ON public.inspiration_boards
  FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY inspiration_boards_update_own
  ON public.inspiration_boards
  FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY inspiration_boards_delete_own
  ON public.inspiration_boards
  FOR DELETE
  USING (user_id = auth.uid());

-- Optional demo allowance that previously existed for a hardcoded UUID:
-- Replace '550e8400-e29b-41d4-a716-446655440001' with your demo user id if you still need it.
-- CREATE POLICY inspiration_boards_demo_full
--   ON public.inspiration_boards
--   FOR ALL
--   USING (user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid)
--   WITH CHECK (user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid);

--------------------------------------------------------------------------------
-- Inspiration Conversations (public.inspiration_conversations)
--------------------------------------------------------------------------------

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='inspiration_conversations'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.inspiration_conversations', pol.policyname);
  END LOOP;
END$$;

CREATE POLICY inspiration_conversations_select_own
  ON public.inspiration_conversations
  FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY inspiration_conversations_insert_own
  ON public.inspiration_conversations
  FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY inspiration_conversations_update_own
  ON public.inspiration_conversations
  FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY inspiration_conversations_delete_own
  ON public.inspiration_conversations
  FOR DELETE
  USING (user_id = auth.uid());

-- Optional demo allowance:
-- CREATE POLICY inspiration_conversations_demo_full
--   ON public.inspiration_conversations
--   FOR ALL
--   USING (user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid)
--   WITH CHECK (user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid);

--------------------------------------------------------------------------------
-- Inspiration Images (public.inspiration_images)
--------------------------------------------------------------------------------

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='inspiration_images'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.inspiration_images', pol.policyname);
  END LOOP;
END$$;

CREATE POLICY inspiration_images_select_own
  ON public.inspiration_images
  FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY inspiration_images_insert_own
  ON public.inspiration_images
  FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY inspiration_images_update_own
  ON public.inspiration_images
  FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY inspiration_images_delete_own
  ON public.inspiration_images
  FOR DELETE
  USING (user_id = auth.uid());

-- Optional demo allowance:
-- CREATE POLICY inspiration_images_demo_full
--   ON public.inspiration_images
--   FOR ALL
--   USING (user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid)
--   WITH CHECK (user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid);

--------------------------------------------------------------------------------
-- Vision Compositions (public.vision_compositions)
--------------------------------------------------------------------------------

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='vision_compositions'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.vision_compositions', pol.policyname);
  END LOOP;
END$$;

CREATE POLICY vision_compositions_select_own
  ON public.vision_compositions
  FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY vision_compositions_insert_own
  ON public.vision_compositions
  FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY vision_compositions_update_own
  ON public.vision_compositions
  FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY vision_compositions_delete_own
  ON public.vision_compositions
  FOR DELETE
  USING (user_id = auth.uid());

--------------------------------------------------------------------------------
-- Generated Dream Spaces (public.generated_dream_spaces)
--------------------------------------------------------------------------------

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='generated_dream_spaces'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.generated_dream_spaces', pol.policyname);
  END LOOP;
END$$;

-- Prior policies were permissive "true" with demo allowances; switch to user ownership.
CREATE POLICY generated_dream_spaces_select_own
  ON public.generated_dream_spaces
  FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY generated_dream_spaces_insert_own
  ON public.generated_dream_spaces
  FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY generated_dream_spaces_update_own
  ON public.generated_dream_spaces
  FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY generated_dream_spaces_delete_own
  ON public.generated_dream_spaces
  FOR DELETE
  USING (user_id = auth.uid());

-- Optional demo allowance:
-- CREATE POLICY generated_dream_spaces_demo_full
--   ON public.generated_dream_spaces
--   FOR ALL
--   USING (user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid)
--   WITH CHECK (user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid);

--------------------------------------------------------------------------------
-- Referral Tracking (public.referral_tracking)
-- Switch to referred_user_id policy if rows are user-scoped
--------------------------------------------------------------------------------

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='referral_tracking'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.referral_tracking', pol.policyname);
  END LOOP;
END$$;

-- Example (adjust to your product logic)
-- CREATE POLICY referral_tracking_select
--   ON public.referral_tracking
--   FOR SELECT
--   USING (referred_user_id = auth.uid());

COMMIT;

-- Final tips:
-- - Ensure RLS is enabled for each table (ALTER TABLE ... ENABLE ROW LEVEL SECURITY).
-- - Audit additional tables for homeowner_id predicates and replicate this pattern.

-- 05_drop_homeowner_id_columns.sql
-- Purpose: After code runs on user_id only and soak completes, remove homeowner_id columns
-- and old indexes/constraints, and finalize referral column rename.
-- Pre-req: 01_add_user_id.sql, 02_backfill_user_id.sql, 03_enforce_not_null_and_constraints.sql
-- Optional: 04_dual_read_write_triggers.sql has been removed/disabled.

BEGIN;

-- Drop any triggers from step 04 if still present (defensive)
DROP TRIGGER IF EXISTS projects_mirror_homeowner_to_user ON public.projects;
DROP TRIGGER IF EXISTS generated_dream_spaces_mirror_homeowner_to_user ON public.generated_dream_spaces;
DROP TRIGGER IF EXISTS bid_cards_mirror_homeowner_to_user ON public.bid_cards;
DROP TRIGGER IF EXISTS inspiration_boards_mirror_homeowner_to_user ON public.inspiration_boards;
DROP TRIGGER IF EXISTS inspiration_conversations_mirror_homeowner_to_user ON public.inspiration_conversations;
DROP TRIGGER IF EXISTS inspiration_images_mirror_homeowner_to_user ON public.inspiration_images;
DROP TRIGGER IF EXISTS vision_compositions_mirror_homeowner_to_user ON public.vision_compositions;
DROP TRIGGER IF EXISTS referral_tracking_mirror_homeowner_to_user ON public.referral_tracking;

-- Drop helper functions from step 04 (optional)
DROP FUNCTION IF EXISTS public._resolve_user_from_homeowner(uuid);
DROP FUNCTION IF EXISTS public.trg_projects_mirror_homeowner_to_user();
DROP FUNCTION IF EXISTS public.trg_gds_mirror_homeowner_to_user();
DROP FUNCTION IF EXISTS public.trg_bid_cards_mirror_homeowner_to_user();
DROP FUNCTION IF EXISTS public._mirror_profile_homeowner_to_user();
DROP FUNCTION IF EXISTS public.trg_referral_tracking_mirror_homeowner_to_user();

-- Remove legacy indexes on homeowner_id if they exist
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='idx_bid_cards_homeowner_id') THEN
    EXECUTE 'DROP INDEX public.idx_bid_cards_homeowner_id';
  END IF;

  IF EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='idx_inspiration_boards_homeowner') THEN
    EXECUTE 'DROP INDEX public.idx_inspiration_boards_homeowner';
  END IF;

  IF EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='idx_inspiration_conversations_homeowner') THEN
    EXECUTE 'DROP INDEX public.idx_inspiration_conversations_homeowner';
  END IF;

  IF EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='idx_generated_dream_spaces_homeowner_id') THEN
    EXECUTE 'DROP INDEX public.idx_generated_dream_spaces_homeowner_id';
  END IF;

  IF EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='idx_projects_homeowner') THEN
    EXECUTE 'DROP INDEX public.idx_projects_homeowner';
  END IF;
END$$;

-- Drop homeowner_id columns (now redundant)
ALTER TABLE public.bid_cards                 DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.projects                  DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.generated_dream_spaces    DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.inspiration_boards        DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.inspiration_conversations DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.inspiration_images        DROP COLUMN IF EXISTS homeowner_id;
ALTER TABLE public.vision_compositions       DROP COLUMN IF EXISTS homeowner_id;

-- Referral tracking: remove old column after backfill and NOT NULL on referred_user_id
-- (Constraints on referred_homeowner_id were removed/ignored in step 01..03)
ALTER TABLE public.referral_tracking
  DROP COLUMN IF EXISTS referred_homeowner_id;

COMMIT;

-- Notes:
-- - Leave homeowners table removal to 06_drop_homeowners_table.sql.
-- - Ensure all code paths are writing/reading user_id exclusively before running this script in production.

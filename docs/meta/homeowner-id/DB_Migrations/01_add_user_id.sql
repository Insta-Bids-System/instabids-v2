-- 01_add_user_id.sql
-- Purpose: Add user_id (and referred_user_id for referral_tracking) columns, indexes, and FKs.
-- Run order: 01_add_user_id.sql → 02_backfill_user_id.sql → 03_enforce_not_null_and_constraints.sql → 04_dual_read_write_triggers.sql (optional) → 05_drop_homeowner_id_columns.sql → 06_drop_homeowners_table.sql → 07_policies_rls.sql

BEGIN;

-- Add columns (NULLABLE initially)
ALTER TABLE public.bid_cards                 ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.projects                  ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.generated_dream_spaces    ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.inspiration_boards        ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.inspiration_conversations ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.inspiration_images        ADD COLUMN IF NOT EXISTS user_id uuid NULL;
ALTER TABLE public.vision_compositions       ADD COLUMN IF NOT EXISTS user_id uuid NULL;

-- referral_tracking has a column referred_homeowner_id; introduce referred_user_id instead
ALTER TABLE public.referral_tracking         ADD COLUMN IF NOT EXISTS referred_user_id uuid NULL;

-- Create indexes on new columns
CREATE INDEX IF NOT EXISTS idx_bid_cards_user_id                 ON public.bid_cards(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_user_id                  ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_dream_spaces_user_id    ON public.generated_dream_spaces(user_id);
CREATE INDEX IF NOT EXISTS idx_inspiration_boards_user_id        ON public.inspiration_boards(user_id);
CREATE INDEX IF NOT EXISTS idx_inspiration_conversations_user_id ON public.inspiration_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_inspiration_images_user_id        ON public.inspiration_images(user_id);
CREATE INDEX IF NOT EXISTS idx_vision_compositions_user_id       ON public.vision_compositions(user_id);
CREATE INDEX IF NOT EXISTS idx_referral_tracking_referred_user_id ON public.referral_tracking(referred_user_id);

-- Add FKs to profiles(id)
-- (Do not re-add if they already exist; names chosen to be unique and descriptive)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'bid_cards_user_id_fkey'
  ) THEN
    ALTER TABLE public.bid_cards
      ADD CONSTRAINT bid_cards_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'projects_user_id_fkey'
  ) THEN
    ALTER TABLE public.projects
      ADD CONSTRAINT projects_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'generated_dream_spaces_user_id_fkey'
  ) THEN
    ALTER TABLE public.generated_dream_spaces
      ADD CONSTRAINT generated_dream_spaces_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'inspiration_boards_user_id_fkey'
  ) THEN
    ALTER TABLE public.inspiration_boards
      ADD CONSTRAINT inspiration_boards_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'inspiration_conversations_user_id_fkey'
  ) THEN
    ALTER TABLE public.inspiration_conversations
      ADD CONSTRAINT inspiration_conversations_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'inspiration_images_user_id_fkey'
  ) THEN
    ALTER TABLE public.inspiration_images
      ADD CONSTRAINT inspiration_images_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'vision_compositions_user_id_fkey'
  ) THEN
    ALTER TABLE public.vision_compositions
      ADD CONSTRAINT vision_compositions_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'referral_tracking_referred_user_id_fkey'
  ) THEN
    ALTER TABLE public.referral_tracking
      ADD CONSTRAINT referral_tracking_referred_user_id_fkey
      FOREIGN KEY (referred_user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
  END IF;
END$$;

COMMIT;

-- Notes:
-- - Next step is 02_backfill_user_id.sql to populate these columns from homeowner_id (either direct copy when homeowner_id referenced profiles.id, or via join from homeowners.user_id).
-- - Do not set NOT NULL until backfill is verified (03_enforce_not_null_and_constraints.sql).

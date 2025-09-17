-- 04_dual_read_write_triggers.sql
-- Purpose: Optional transitional compatibility. While code is migrating, mirror incoming writes
-- that still use homeowner_id into the new user_id columns. Remove after soak.
-- Run after: 01_add_user_id.sql, 02_backfill_user_id.sql (and before final drops in 05_*)

BEGIN;

--------------------------------------------------------------------------------
-- Helper: resolve homeowners.id → homeowners.user_id (for tables where
-- homeowner_id referenced homeowners.id)
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public._resolve_user_from_homeowner(_homeowner_id uuid)
RETURNS uuid
LANGUAGE sql
AS $$
  SELECT h.user_id
  FROM public.homeowners h
  WHERE h.id = _homeowner_id
$$;

--------------------------------------------------------------------------------
-- Projects: homeowner_id (→ homeowners.id) → user_id
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.trg_projects_mirror_homeowner_to_user()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.user_id IS NULL AND NEW.homeowner_id IS NOT NULL THEN
    NEW.user_id := public._resolve_user_from_homeowner(NEW.homeowner_id);
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS projects_mirror_homeowner_to_user ON public.projects;
CREATE TRIGGER projects_mirror_homeowner_to_user
BEFORE INSERT OR UPDATE ON public.projects
FOR EACH ROW
EXECUTE FUNCTION public.trg_projects_mirror_homeowner_to_user();

--------------------------------------------------------------------------------
-- Generated Dream Spaces: homeowner_id (→ homeowners.id) → user_id
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.trg_gds_mirror_homeowner_to_user()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.user_id IS NULL AND NEW.homeowner_id IS NOT NULL THEN
    NEW.user_id := public._resolve_user_from_homeowner(NEW.homeowner_id);
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS generated_dream_spaces_mirror_homeowner_to_user ON public.generated_dream_spaces;
CREATE TRIGGER generated_dream_spaces_mirror_homeowner_to_user
BEFORE INSERT OR UPDATE ON public.generated_dream_spaces
FOR EACH ROW
EXECUTE FUNCTION public.trg_gds_mirror_homeowner_to_user();

--------------------------------------------------------------------------------
-- Bid Cards: homeowner_id (→ homeowners.id) → user_id
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.trg_bid_cards_mirror_homeowner_to_user()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.user_id IS NULL AND NEW.homeowner_id IS NOT NULL THEN
    NEW.user_id := public._resolve_user_from_homeowner(NEW.homeowner_id);
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS bid_cards_mirror_homeowner_to_user ON public.bid_cards;
CREATE TRIGGER bid_cards_mirror_homeowner_to_user
BEFORE INSERT OR UPDATE ON public.bid_cards
FOR EACH ROW
EXECUTE FUNCTION public.trg_bid_cards_mirror_homeowner_to_user();

--------------------------------------------------------------------------------
-- Inspiration* & Vision tables: homeowner_id already equals profiles.id.
-- Mirror simple copy homeowner_id → user_id when user_id is NULL.
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public._mirror_profile_homeowner_to_user()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.user_id IS NULL AND NEW.homeowner_id IS NOT NULL THEN
    -- homeowner_id already equals profiles.id here
    NEW.user_id := NEW.homeowner_id;
  END IF;
  RETURN NEW;
END;
$$;

-- inspiration_boards
DROP TRIGGER IF EXISTS inspiration_boards_mirror_homeowner_to_user ON public.inspiration_boards;
CREATE TRIGGER inspiration_boards_mirror_homeowner_to_user
BEFORE INSERT OR UPDATE ON public.inspiration_boards
FOR EACH ROW
EXECUTE FUNCTION public._mirror_profile_homeowner_to_user();

-- inspiration_conversations
DROP TRIGGER IF EXISTS inspiration_conversations_mirror_homeowner_to_user ON public.inspiration_conversations;
CREATE TRIGGER inspiration_conversations_mirror_homeowner_to_user
BEFORE INSERT OR UPDATE ON public.inspiration_conversations
FOR EACH ROW
EXECUTE FUNCTION public._mirror_profile_homeowner_to_user();

-- inspiration_images
DROP TRIGGER IF EXISTS inspiration_images_mirror_homeowner_to_user ON public.inspiration_images;
CREATE TRIGGER inspiration_images_mirror_homeowner_to_user
BEFORE INSERT OR UPDATE ON public.inspiration_images
FOR EACH ROW
EXECUTE FUNCTION public._mirror_profile_homeowner_to_user();

-- vision_compositions
DROP TRIGGER IF EXISTS vision_compositions_mirror_homeowner_to_user ON public.vision_compositions;
CREATE TRIGGER vision_compositions_mirror_homeowner_to_user
BEFORE INSERT OR UPDATE ON public.vision_compositions
FOR EACH ROW
EXECUTE FUNCTION public._mirror_profile_homeowner_to_user();

--------------------------------------------------------------------------------
-- Referral Tracking: referred_homeowner_id (→ homeowners.id) → referred_user_id
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.trg_referral_tracking_mirror_homeowner_to_user()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.referred_user_id IS NULL AND NEW.referred_homeowner_id IS NOT NULL THEN
    NEW.referred_user_id := public._resolve_user_from_homeowner(NEW.referred_homeowner_id);
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS referral_tracking_mirror_homeowner_to_user ON public.referral_tracking;
CREATE TRIGGER referral_tracking_mirror_homeowner_to_user
BEFORE INSERT OR UPDATE ON public.referral_tracking
FOR EACH ROW
EXECUTE FUNCTION public.trg_referral_tracking_mirror_homeowner_to_user();

COMMIT;

-- Notes:
-- - These triggers are strictly for a temporary migration window.
-- - Remove them before dropping homeowner_id columns (or immediately after code stops sending homeowner_id).
-- - We intentionally do not mirror user_id back to homeowner_id; the system is moving forward on user_id only.

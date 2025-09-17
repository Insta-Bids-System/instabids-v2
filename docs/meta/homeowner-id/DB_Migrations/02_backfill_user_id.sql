-- 02_backfill_user_id.sql
-- Purpose: Populate new user_id columns (and referred_user_id) from existing homeowner_id data.
-- Run order: 01_add_user_id.sql → 02_backfill_user_id.sql → 03_enforce_not_null_and_constraints.sql → 04_dual_read_write_triggers.sql (optional) → 05_drop_homeowner_id_columns.sql → 06_drop_homeowners_table.sql → 07_policies_rls.sql

BEGIN;

-- Case A: Tables where homeowner_id already references profiles(id)
-- Simple copy: user_id := homeowner_id
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

-- Case B: Tables where homeowner_id references homeowners(id)
-- Join to homeowners to obtain the real user_id
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

-- bid_cards.user_id ← homeowners.user_id
-- Note: public_columns shows bid_cards has homeowner_id; FK not listed, but backfill via homeowners mapping
UPDATE public.bid_cards b
SET user_id = h.user_id
FROM public.homeowners h
WHERE b.user_id IS NULL AND b.homeowner_id = h.id;

-- referral_tracking.referred_user_id ← homeowners.user_id
UPDATE public.referral_tracking r
SET referred_user_id = h.user_id
FROM public.homeowners h
WHERE r.referred_user_id IS NULL AND r.referred_homeowner_id = h.id;

COMMIT;

-- Optional sanity checks (manual)
-- SELECT 'inspiration_boards missing user_id' AS t, count(*) FROM public.inspiration_boards WHERE user_id IS NULL;
-- SELECT 'inspiration_conversations missing user_id' AS t, count(*) FROM public.inspiration_conversations WHERE user_id IS NULL;
-- SELECT 'inspiration_images missing user_id' AS t, count(*) FROM public.inspiration_images WHERE user_id IS NULL;
-- SELECT 'vision_compositions missing user_id' AS t, count(*) FROM public.vision_compositions WHERE user_id IS NULL;
-- SELECT 'projects missing user_id' AS t, count(*) FROM public.projects WHERE user_id IS NULL;
-- SELECT 'generated_dream_spaces missing user_id' AS t, count(*) FROM public.generated_dream_spaces WHERE user_id IS NULL;
-- SELECT 'bid_cards missing user_id' AS t, count(*) FROM public.bid_cards WHERE user_id IS NULL;
-- SELECT 'referral_tracking missing referred_user_id' AS t, count(*) FROM public.referral_tracking WHERE referred_user_id IS NULL;

-- Notes:
-- - Do NOT set NOT NULL until 03_enforce_not_null_and_constraints.sql after verifying the above checks are zero.
-- - If additional tables reference homeowners.id via a homeowner_id column, add similar UPDATE...FROM joins here.

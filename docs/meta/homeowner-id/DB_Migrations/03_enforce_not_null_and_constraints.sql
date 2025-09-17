-- 03_enforce_not_null_and_constraints.sql
-- Purpose: After backfilling user_id, enforce NOT NULL and keep FKs/Indexes consistent.
-- Pre-req: 01_add_user_id.sql and 02_backfill_user_id.sql have completed successfully with zero NULLs.

BEGIN;

-- Safety checks (uncomment to verify before proceeding)
-- SELECT 'bid_cards NULL user_id' AS t, COUNT(*) FROM public.bid_cards WHERE user_id IS NULL;
-- SELECT 'projects NULL user_id' AS t, COUNT(*) FROM public.projects WHERE user_id IS NULL;
-- SELECT 'generated_dream_spaces NULL user_id' AS t, COUNT(*) FROM public.generated_dream_spaces WHERE user_id IS NULL;
-- SELECT 'inspiration_boards NULL user_id' AS t, COUNT(*) FROM public.inspiration_boards WHERE user_id IS NULL;
-- SELECT 'inspiration_conversations NULL user_id' AS t, COUNT(*) FROM public.inspiration_conversations WHERE user_id IS NULL;
-- SELECT 'inspiration_images NULL user_id' AS t, COUNT(*) FROM public.inspiration_images WHERE user_id IS NULL;
-- SELECT 'vision_compositions NULL user_id' AS t, COUNT(*) FROM public.vision_compositions WHERE user_id IS NULL;
-- SELECT 'referral_tracking NULL referred_user_id' AS t, COUNT(*) FROM public.referral_tracking WHERE referred_user_id IS NULL;

-- Enforce NOT NULL
ALTER TABLE public.bid_cards                 ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.projects                  ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.generated_dream_spaces    ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.inspiration_boards        ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.inspiration_conversations ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.inspiration_images        ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE public.vision_compositions       ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE public.referral_tracking         ALTER COLUMN referred_user_id SET NOT NULL;

-- Optional: add composite indexes parallel to any prior homeowner_id usage (adjust as needed)
-- Example: if queries often filter by (user_id, created_at) or (user_id, status)
-- CREATE INDEX IF NOT EXISTS idx_projects_user_status ON public.projects(user_id, status);
-- CREATE INDEX IF NOT EXISTS idx_bid_cards_user_status ON public.bid_cards(user_id, status);

COMMIT;

-- Notes:
-- - If any ALTER fails due to existing NULLs, abort and re-run 02_backfill_user_id.sql or fix data manually.
-- - Keep homeowners.homeowner_id columns in place until final drop (05_* scripts).

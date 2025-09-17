-- 06_drop_homeowners_table.sql
-- Purpose: Remove the redundant homeowners table after all references have been migrated to user_id.
-- Pre-req: 01..05 completed, application runs solely on user_id, and no remaining dependencies.

BEGIN;

-- Defensive: drop homeowners-specific policies and indexes if they still exist
DO $$
DECLARE
  pol RECORD;
BEGIN
  FOR pol IN
    SELECT policyname
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'homeowners'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.homeowners', pol.policyname);
  END LOOP;
END$$;

-- Drop any remaining indexes on homeowners.*
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='idx_homeowners_referral_code') THEN
    EXECUTE 'DROP INDEX public.idx_homeowners_referral_code';
  END IF;
END$$;

-- Final safety: ensure no FKs still reference homeowners.id
-- (Should be zero after 05_drop_homeowner_id_columns.sql)
-- SELECT conname, conrelid::regclass AS table_name
-- FROM pg_constraint
-- WHERE confrelid = 'public.homeowners'::regclass;

-- Drop table (no CASCADE expected if previous steps succeeded)
DROP TABLE IF EXISTS public.homeowners;

COMMIT;

-- Notes:
-- - If any dependency errors occur, re-check for leftover FKs/policies/indexes referencing public.homeowners and remove them before retrying.

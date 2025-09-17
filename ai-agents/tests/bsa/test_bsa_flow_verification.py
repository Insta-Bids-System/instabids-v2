"""Legacy BSA integration scenario (skipped in offline test runs)."""

import pytest

pytestmark = pytest.mark.skip(reason="Requires live Supabase and backend services")

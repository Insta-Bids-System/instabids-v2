"""Global pytest fixtures and test configuration for ai-agents tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock
import supabase

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Provide fake credentials so modules that instantiate Supabase clients succeed.
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-supabase-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

# Ensure any call to `create_client` during imports returns a harmless mock.
if not isinstance(supabase.create_client, MagicMock):
    supabase.create_client = MagicMock(return_value=MagicMock())

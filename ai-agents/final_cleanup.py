#!/usr/bin/env python3
"""
FINAL cleanup - Fix any remaining wrong patterns
"""

import os
import re
from pathlib import Path

BACKEND_ROOT = Path(r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents")

# Files to fix based on grep results
files_with_wrong_pattern = [
    "test_cia_memory_access.py",
    "test_coia_memory_quick.py", 
    "test_coia_state_persistence_complete.py",
    "test_coia_unified_integration.py",
    "test_personas_quick.py",
    "test_persona_fixed.py",
    "test_single_persona.py"
]

for filename in files_with_wrong_pattern:
    filepath = BACKEND_ROOT / filename
    if not filepath.exists():
        continue
        
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content
        
        # Fix wrong patterns
        content = re.sub(
            r'os\.getenv\("API_BASE_URL", get_backend_url\(\)\) \+ ""',
            'get_backend_url()',
            content
        )
        
        content = re.sub(
            r'os\.getenv\("API_BASE_URL", get_backend_url\(\)\)',
            'get_backend_url()',
            content
        )
        
        content = re.sub(
            r'API_BASE_URL = get_backend_url\(\)',
            'BACKEND_URL = get_backend_url()',
            content
        )
        
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            print(f"Fixed: {filename}")
        
    except Exception as e:
        print(f"Error fixing {filename}: {e}")

print("\nFinal cleanup complete!")
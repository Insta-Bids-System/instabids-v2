#!/usr/bin/env python3
"""
Fix all files with incorrect URL patterns to use get_backend_url() correctly
"""

import os
import re

BASE_DIR = r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents"

# All test files that need fixing
FILES_TO_FIX = [
    "test_bsa.py",
    "test_bsa_comprehensive.py", 
    "test_bsa_unified.py",
    "test_memory_simple.py",
    "test_memory_fix.py",
    "test_memory_persistence_complete.py",
    "test_iris_memory_integration.py",
    "test_iris_memory_simple.py",
    "test_coia_memory_quick.py",
    "test_coia_memory_integration.py",
    "test_cia_memory_access.py"
]

def fix_file(filepath):
    """Fix all incorrect URL patterns in a file"""
    full_path = os.path.join(BASE_DIR, filepath)
    
    if not os.path.exists(full_path):
        print(f"  [SKIP] {filepath} not found")
        return False
        
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # Pattern replacements - be very specific
    replacements = [
        # Fix os.getenv patterns
        (r'os\.getenv\("API_BASE_URL", get_backend_url\(\)\) \+ "(/[^"]*)"', r'f"{get_backend_url()}\1"'),
        (r'os\.getenv\("API_BASE_URL", os\.getenv\("API_BASE_URL", get_backend_url\(\)\) \+ ""\) \+ "(/[^"]*)"', r'f"{get_backend_url()}\1"'),
        # Fix fos.getenv (typo)
        (r'fos\.getenv\("API_BASE_URL", get_backend_url\(\)\) \+ "(/[^"]*)"', r'f"{get_backend_url()}\1"'),
        # Fix self.base_url assignments
        (r'self\.base_url = os\.getenv\("API_BASE_URL", os\.getenv\("API_BASE_URL", get_backend_url\(\)\) \+ ""\) \+ "(/[^"]*)"', r'self.base_url = f"{get_backend_url()}\1"'),
        (r'self\.base_url = os\.getenv\("API_BASE_URL", get_backend_url\(\)\) \+ "(/[^"]*)"', r'self.base_url = f"{get_backend_url()}\1"'),
    ]
    
    for pattern, replacement in replacements:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            changes.append(f"    Fixed {len(matches)} instances of pattern")
    
    if content != original:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [FIXED] {filepath}")
        for change in changes:
            print(change)
        return True
    else:
        print(f"  [OK] {filepath} - no changes needed")
        return False

def main():
    print("Fixing all test files with incorrect URL patterns...")
    print("=" * 60)
    
    fixed = 0
    for filepath in FILES_TO_FIX:
        if fix_file(filepath):
            fixed += 1
        print()
    
    print("=" * 60)
    print(f"Complete! Fixed {fixed} files")
    print("\nAll files now use the correct pattern:")
    print('  f"{get_backend_url()}/api/..."')

if __name__ == "__main__":
    main()
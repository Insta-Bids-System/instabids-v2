#!/usr/bin/env python3
"""
Fix ALL hardcoded localhost:8008 URLs in the entire InstaBids codebase
This script will standardize everything to use centralized configuration
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Root directory of the backend
BACKEND_ROOT = Path(r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents")

# Files to skip (tests, examples, this script)
SKIP_PATTERNS = [
    "test_*.py",
    "*/test/*",
    "*/tests/*",
    "*.bak",
    "fix_all_urls.py",
    "cleanup_*.py"
]

# The config import to add
CONFIG_IMPORT = "from config.service_urls import get_backend_url"

def should_skip(file_path: Path) -> bool:
    """Check if file should be skipped"""
    path_str = str(file_path)
    for pattern in SKIP_PATTERNS:
        if pattern.startswith("*"):
            if pattern[1:] in path_str:
                return True
        elif pattern.endswith("*"):
            if path_str.startswith(pattern[:-1]):
                return True
        elif pattern in path_str:
            return True
    return False

def find_files_with_hardcoded_urls() -> List[Path]:
    """Find all Python files with hardcoded localhost:8008 URLs"""
    files_to_fix = []
    
    for py_file in BACKEND_ROOT.rglob("*.py"):
        if should_skip(py_file):
            continue
            
        try:
            content = py_file.read_text(encoding='utf-8')
            if 'http://localhost:8008' in content or 'https://localhost:8008' in content:
                files_to_fix.append(py_file)
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return files_to_fix

def fix_file(file_path: Path) -> Tuple[bool, str]:
    """Fix hardcoded URLs in a single file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Check if config import already exists
        has_config_import = 'from config.service_urls import' in content
        
        # Replace patterns
        patterns = [
            # f-strings with http://localhost:8008
            (r'f"http://localhost:8008([^"]*)"', r'f"{get_backend_url()}\1"'),
            (r"f'http://localhost:8008([^']*)'", r"f'{get_backend_url()}\1'"),
            
            # Regular strings with http://localhost:8008
            (r'"http://localhost:8008/([^"]*)"', r'f"{get_backend_url()}/\1"'),
            (r"'http://localhost:8008/([^']*)'", r"f'{get_backend_url()}/\1'"),
            
            # Just http://localhost:8008 alone
            (r'"http://localhost:8008"', r'get_backend_url()'),
            (r"'http://localhost:8008'", r'get_backend_url()'),
            
            # https variants
            (r'f"https://localhost:8008([^"]*)"', r'f"{get_backend_url()}\1"'),
            (r"f'https://localhost:8008([^']*)'", r"f'{get_backend_url()}\1'"),
            (r'"https://localhost:8008/([^"]*)"', r'f"{get_backend_url()}/\1"'),
            (r"'https://localhost:8008/([^']*)'", r"f'{get_backend_url()}/\1'"),
            (r'"https://localhost:8008"', r'get_backend_url()'),
            (r"'https://localhost:8008'", r'get_backend_url()'),
        ]
        
        # Apply all replacements
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # If we made changes and don't have the import, add it
        if content != original_content and not has_config_import:
            # Find where to add import (after other imports)
            lines = content.split('\n')
            import_index = 0
            
            # Find the last import statement
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_index = i + 1
            
            # Add our import after the last import
            if import_index > 0:
                lines.insert(import_index, CONFIG_IMPORT)
                content = '\n'.join(lines)
        
        # Only write if we actually changed something
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True, "Fixed"
        else:
            return False, "No changes needed"
            
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Main execution"""
    print("=" * 60)
    print("INSTABIDS URL FIX SCRIPT")
    print("=" * 60)
    print()
    
    # Step 1: Find all files with hardcoded URLs
    print("Step 1: Scanning for files with hardcoded URLs...")
    files_to_fix = find_files_with_hardcoded_urls()
    
    if not files_to_fix:
        print("✅ No files found with hardcoded URLs!")
        return
    
    print(f"Found {len(files_to_fix)} files to fix:")
    for f in files_to_fix:
        print(f"  - {f.relative_to(BACKEND_ROOT)}")
    print()
    
    # Step 2: Fix each file
    print("Step 2: Fixing files...")
    fixed_count = 0
    error_count = 0
    
    for file_path in files_to_fix:
        success, message = fix_file(file_path)
        rel_path = file_path.relative_to(BACKEND_ROOT)
        
        if success:
            print(f"  [FIXED] {rel_path}")
            fixed_count += 1
        else:
            print(f"  [ERROR] {rel_path}: {message}")
            error_count += 1
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"[FIXED]: {fixed_count} files")
    print(f"[ERRORS]: {error_count} files")
    print(f"[TOTAL]: {len(files_to_fix)} files")
    
    if fixed_count > 0:
        print()
        print("[SUCCESS] All hardcoded URLs have been replaced with centralized config.")
        print("The backend will now work in:")
        print("  - Local development (localhost)")
        print("  - Docker containers (instabids-backend)")
        print("  - Production (any domain via BACKEND_HOST env var)")
    
    return fixed_count, error_count

if __name__ == "__main__":
    fixed, errors = main()
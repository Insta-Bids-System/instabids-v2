#!/usr/bin/env python3
"""
Safe script to fix hardcoded localhost:8008 URLs in Python files.
This ONLY fixes backend URLs, not frontend ports.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Directories to skip
SKIP_DIRS = {
    'node_modules',
    '.git',
    '__pycache__',
    '.pytest_cache',
    'venv',
    'env',
    '.venv',
    'web',  # Skip frontend directory completely
    'mobile',  # Skip mobile directory
}

# Files to skip
SKIP_FILES = {
    'fix_python_backend_urls.py',  # Don't modify this script
    'fix_router_urls.py',  # Don't modify existing fix scripts
}

def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files that need fixing."""
    python_files = []
    
    for file_path in root_dir.rglob('*.py'):
        # Skip if in excluded directory
        if any(skip_dir in file_path.parts for skip_dir in SKIP_DIRS):
            continue
        
        # Skip if in excluded files
        if file_path.name in SKIP_FILES:
            continue
            
        python_files.append(file_path)
    
    return python_files

def analyze_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Analyze a file and return lines that need fixing."""
    changes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return changes
    
    # Patterns to find and fix
    patterns = [
        # Direct string literals
        (r'"http://localhost:8008([^"]*)"', r'f"{BACKEND_URL}\1"'),
        (r"'http://localhost:8008([^']*)'", r"f'{BACKEND_URL}\1'"),
        # Already f-strings (just replace the localhost part)
        (r'f"http://localhost:8008([^"]*)"', r'f"{BACKEND_URL}\1"'),
        (r"f'http://localhost:8008([^']*)'", r"f'{BACKEND_URL}\1'"),
        # In comments or docstrings (for examples)
        (r'http://localhost:8008/', 'BACKEND_URL/'),
    ]
    
    for line_num, line in enumerate(lines, 1):
        # Skip if it's a frontend URL (port 5173, 5174, etc)
        if 'localhost:517' in line or 'localhost:3000' in line:
            continue
            
        # Check if line contains backend URL
        if 'localhost:8008' in line:
            original = line
            modified = line
            
            # Apply all patterns
            for pattern, replacement in patterns:
                modified = re.sub(pattern, replacement, modified)
            
            if modified != original:
                changes.append((line_num, original.strip(), modified.strip()))
    
    return changes

def needs_import(file_path: Path) -> bool:
    """Check if file needs BACKEND_URL import added."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return 'localhost:8008' in content and 'BACKEND_URL' not in content
    except:
        return False

def add_backend_url_import(lines: List[str]) -> List[str]:
    """Add BACKEND_URL import at the appropriate location."""
    import_line = 'BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8008")\n'
    
    # Find where to insert (after imports, before first function/class)
    insert_index = 0
    found_imports = False
    
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            found_imports = True
        elif found_imports and not line.strip().startswith('#') and line.strip():
            # First non-import, non-comment line after imports
            insert_index = i
            break
    
    # Make sure os is imported
    os_imported = any('import os' in line for line in lines[:insert_index])
    
    new_lines = lines[:]
    if not os_imported:
        new_lines.insert(insert_index, 'import os\n')
        insert_index += 1
    
    new_lines.insert(insert_index, '\n')
    new_lines.insert(insert_index + 1, '# Backend URL configuration\n')
    new_lines.insert(insert_index + 2, import_line)
    new_lines.insert(insert_index + 3, '\n')
    
    return new_lines

def fix_file(file_path: Path, dry_run: bool = True) -> bool:
    """Fix a single file."""
    changes = analyze_file(file_path)
    
    if not changes:
        return False
    
    print(f"\n[FILE] {file_path.relative_to(Path.cwd())}")
    print(f"   Found {len(changes)} lines to fix:")
    
    for line_num, original, modified in changes[:3]:  # Show first 3 changes
        print(f"   Line {line_num}:")
        print(f"     - {original[:80]}...")
        print(f"     + {modified[:80]}...")
    
    if len(changes) > 3:
        print(f"   ... and {len(changes) - 3} more changes")
    
    if dry_run:
        return True
    
    # Actually fix the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Fix the lines
        for line_num, original, modified in changes:
            lines[line_num - 1] = modified + '\n'
        
        # Add import if needed
        if needs_import(file_path):
            lines = add_backend_url_import(lines)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"   [FIXED] Done!")
        return True
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False

def main():
    """Main function."""
    root_dir = Path.cwd()
    
    print("[SCAN] Scanning for Python files with hardcoded backend URLs...")
    print(f"   Root directory: {root_dir}")
    print(f"   Skipping: {', '.join(SKIP_DIRS)}")
    print()
    
    python_files = find_python_files(root_dir)
    print(f"[FOUND] Found {len(python_files)} Python files to check")
    
    # First, do a dry run to show what will be changed
    files_to_fix = []
    for file_path in python_files:
        if analyze_file(file_path):
            files_to_fix.append(file_path)
    
    if not files_to_fix:
        print("[OK] No files need fixing!")
        return
    
    print(f"\n[WARNING] Found {len(files_to_fix)} files that need fixing")
    print("\n" + "="*60)
    print("DRY RUN - Showing what will be changed:")
    print("="*60)
    
    for file_path in files_to_fix[:10]:  # Show first 10
        fix_file(file_path, dry_run=True)
    
    if len(files_to_fix) > 10:
        print(f"\n... and {len(files_to_fix) - 10} more files")
    
    # Ask for confirmation
    print("\n" + "="*60)
    print(f"Ready to fix {len(files_to_fix)} files")
    print("This will:")
    print("  1. Add 'import os' and BACKEND_URL variable to each file")
    print("  2. Replace all http://localhost:8008 with BACKEND_URL variable")
    print("  3. Preserve all other URLs (frontend, etc)")
    print()
    response = input("Proceed with fixing? (yes/no): ")
    
    if response.lower() != 'yes':
        print("[ABORTED] Cancelled by user")
        return
    
    # Actually fix the files
    print("\n[FIXING] Fixing files...")
    success_count = 0
    for file_path in files_to_fix:
        if fix_file(file_path, dry_run=False):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"[SUCCESS] Successfully fixed {success_count}/{len(files_to_fix)} files")
    print("\nNext steps:")
    print("  1. Set BACKEND_URL environment variable if needed:")
    print("     export BACKEND_URL=http://localhost:8008")
    print("  2. Test that everything still works")
    print("  3. Commit the changes")

if __name__ == "__main__":
    main()
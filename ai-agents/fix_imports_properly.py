#!/usr/bin/env python3
"""
Fix import statements to be at the top of files properly
"""

import os
import re
from pathlib import Path

BACKEND_ROOT = Path(r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents")

def fix_imports_in_file(file_path: Path):
    """Move config imports to top of file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Find all config import lines
        config_imports = []
        new_lines = []
        
        for line in lines:
            if 'from config.service_urls import' in line:
                # Extract just the import statement
                import_match = re.search(r'from config\.service_urls import \w+', line)
                if import_match:
                    config_imports.append(import_match.group())
            else:
                new_lines.append(line)
        
        if not config_imports:
            return False, "No config imports found"
        
        # Remove duplicates
        config_imports = list(set(config_imports))
        
        # Find where to insert (after other imports)
        insert_pos = 0
        for i, line in enumerate(new_lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i + 1
            elif insert_pos > 0 and line and not line.startswith('#'):
                break
        
        # Insert the import at the right position
        for imp in config_imports:
            new_lines.insert(insert_pos, imp)
            insert_pos += 1
        
        # Write back
        new_content = '\n'.join(new_lines)
        file_path.write_text(new_content, encoding='utf-8')
        return True, "Fixed"
        
    except Exception as e:
        return False, str(e)

# Find all Python files that use get_backend_url
files_to_fix = []
for py_file in BACKEND_ROOT.rglob("*.py"):
    if 'test_' in str(py_file) or '.bak' in str(py_file):
        continue
    try:
        content = py_file.read_text(encoding='utf-8')
        if 'get_backend_url()' in content:
            files_to_fix.append(py_file)
    except:
        pass

print(f"Found {len(files_to_fix)} files to check")

fixed = 0
for f in files_to_fix:
    success, msg = fix_imports_in_file(f)
    if success:
        print(f"Fixed: {f.name}")
        fixed += 1

print(f"\nFixed {fixed} files")
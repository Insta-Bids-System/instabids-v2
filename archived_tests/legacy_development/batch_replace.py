#!/usr/bin/env python3
"""
Batch replace homeowner_id with user_id across the codebase
"""

import os
import re
from pathlib import Path

def replace_in_file(filepath, dry_run=False):
    """Replace homeowner_id with user_id in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count replacements
        count = content.count('homeowner_id')
        
        if count > 0:
            # Do the replacement
            new_content = content.replace('homeowner_id', 'user_id')
            
            if not dry_run:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[OK] {filepath}: {count} replacements")
            else:
                print(f"Would replace in {filepath}: {count} occurrences")
            
            return count
    except Exception as e:
        print(f"[ERROR] Error processing {filepath}: {e}")
        return 0
    
    return 0

def main():
    # Define the root directory
    root_dir = Path(r'C:\Users\Not John Or Justin\Documents\instabids')
    
    # File extensions to process
    extensions = ['.ts', '.tsx', '.js', '.jsx']
    
    # Directories to skip
    skip_dirs = {'node_modules', '.git', 'dist', 'build', '.next', 'coverage'}
    
    total_files = 0
    total_replacements = 0
    
    print("Starting batch replacement of homeowner_id -> user_id")
    print("=" * 60)
    
    # Walk through all files
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip certain directories
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        
        for filename in filenames:
            # Check if file has right extension
            if any(filename.endswith(ext) for ext in extensions):
                filepath = Path(dirpath) / filename
                
                # Skip if path contains web/node_modules
                if 'node_modules' in str(filepath):
                    continue
                    
                count = replace_in_file(filepath, dry_run=False)
                if count > 0:
                    total_files += 1
                    total_replacements += count
    
    print("=" * 60)
    print(f"Complete! Modified {total_files} files with {total_replacements} total replacements")

if __name__ == "__main__":
    main()
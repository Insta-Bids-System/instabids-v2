"""
Script to fix all hardcoded localhost:8008 URLs in router files.
This updates all routers to use the centralized configuration.
"""

import os
import re
from pathlib import Path

def fix_router_urls(file_path):
    """Fix hardcoded URLs in a single router file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file already imports config
    has_import = 'from config.service_urls import' in content
    
    # Replace patterns
    patterns = [
        (r'"http://localhost:8008([^"]*)"', r'f"{get_backend_url()}\1"'),
        (r"'http://localhost:8008([^']*)'", r"f'{get_backend_url()}\1'"),
        (r'f"http://localhost:8008([^"]*)"', r'f"{get_backend_url()}\1"'),
        (r"f'http://localhost:8008([^']*)'", r"f'{get_backend_url()}\1'"),
    ]
    
    modified = False
    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            modified = True
            content = new_content
    
    if modified and not has_import:
        # Add import at the top of the file after other imports
        lines = content.split('\n')
        import_added = False
        
        for i, line in enumerate(lines):
            # Add after the last import statement
            if line.startswith('from ') or line.startswith('import '):
                continue
            elif i > 0 and not import_added:
                lines.insert(i, 'from config.service_urls import get_backend_url')
                import_added = True
                break
        
        content = '\n'.join(lines)
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {file_path}")
        return True
    else:
        print(f"Skipped (no changes): {file_path}")
        return False

def main():
    """Fix all router files."""
    routers_dir = Path('C:/Users/Not John Or Justin/Documents/instabids/ai-agents/routers')
    
    files_to_fix = [
        'unified_coia_api.py',
        'rfi_api.py',
        'mcp_bridge_api.py',
        'intelligent_messaging_api.py',
        'image_upload_api.py',
        'contractor_routes.py',
        'cia_routes_unified.py',
        'bid_card_api_simple.py',
        'bid_card_api.py'
    ]
    
    fixed_count = 0
    for file_name in files_to_fix:
        file_path = routers_dir / file_name
        if file_path.exists():
            if fix_router_urls(file_path):
                fixed_count += 1
        else:
            print(f"❌ File not found: {file_path}")
    
    print(f"\n📊 Summary: Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Search specifically for JM Holiday Lighting
"""
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from database_simple import db

# Search for JM in all holiday contractors
result = db.client.table('potential_contractors').select('*').ilike('company_name', '%jm%').execute()

print(f'SEARCH RESULTS FOR "JM" IN COMPANY NAMES:')
print('=' * 80)

if result.data:
    for c in result.data:
        print(f"\nCompany: {c.get('company_name')}")
        print(f"Project Type: {c.get('project_type')}")
        print(f"City: {c.get('city')}, {c.get('state')}")
        print(f"Reviews: {c.get('google_review_count')} | Rating: {c.get('google_rating')}/5.0")
        print(f"Phone: {c.get('phone')}")
        print(f"Website: {c.get('website')}")
        print(f"Address: {c.get('address')}")
        print(f"Discovery Source: {c.get('discovery_source')}")
else:
    print("No companies with 'JM' in the name found.")

# Also check logs to see if it was filtered
print("\n\nCHECKING IF JM HOLIDAY LIGHTING WAS FILTERED AS DIRECTORY...")
print("The filtering logic may be preventing it from being stored.")
print("\nTo fix this, we need to modify the _is_directory_website function")
print("to be more specific and not filter out legitimate companies.")
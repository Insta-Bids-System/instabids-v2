#!/usr/bin/env python3
"""
Show UNIQUE holiday lighting contractors (no duplicates)
"""
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from database_simple import db

# Get ALL holiday lighting contractors
result = db.client.table('potential_contractors').select('*').ilike('project_type', '%holiday%').execute()

# Deduplicate by Google Place ID or company name + phone
unique_contractors = {}
for c in result.data:
    # Use place ID as primary key if available
    if c.get('google_place_id'):
        key = c.get('google_place_id')
    else:
        # Fallback to company name + phone
        key = f"{c.get('company_name')}_{c.get('phone')}"
    
    # Keep the one with most reviews
    if key not in unique_contractors or (c.get('google_review_count') or 0) > (unique_contractors[key].get('google_review_count') or 0):
        unique_contractors[key] = c

# Sort by review count
sorted_contractors = sorted(unique_contractors.values(), key=lambda x: x.get('google_review_count') or 0, reverse=True)

print(f'UNIQUE HOLIDAY LIGHTING CONTRACTORS: {len(sorted_contractors)}')
print('=' * 80)
print('TOP 20 BY REVIEW COUNT:')
print('=' * 80)

for i, c in enumerate(sorted_contractors[:20]):
    reviews = c.get('google_review_count') or 0
    rating = c.get('google_rating') or 0
    city = c.get('city') or 'Unknown'
    
    print(f'\n{i+1}. {c.get("company_name")}')
    print(f'   Location: {city}, FL')
    print(f'   Reviews: {reviews} | Rating: {rating}/5.0')
    print(f'   Phone: {c.get("phone")}')
    print(f'   Website: {c.get("website")}')
    if c.get('address'):
        print(f'   Address: {c.get("address")}')

print('\n\nWHY WERE THESE NOT SELECTED?')
print('The selection algorithm is failing to properly score contractors.')
print('It should prioritize:')
print('1. High review count (established businesses)')
print('2. High ratings (quality)')
print('3. Local proximity to 33442/Deerfield Beach')
print('\nInstead it selected companies with 3-27 reviews over ones with 80+ reviews!')
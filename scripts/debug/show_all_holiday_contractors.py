#!/usr/bin/env python3
"""
Show ALL holiday lighting contractors found in the area
"""
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from database_simple import db

# Get ALL holiday lighting contractors
result = db.client.table('potential_contractors').select('*').ilike('project_type', '%holiday%').order('google_review_count', desc=True).execute()

print(f'TOTAL HOLIDAY LIGHTING CONTRACTORS IN DATABASE: {len(result.data)}')
print('=' * 80)
print('SORTED BY REVIEW COUNT (HIGHEST TO LOWEST):')
print('=' * 80)

for i, c in enumerate(result.data[:30]):  # Show top 30
    print(f'\n{i+1}. {c.get("company_name")}')
    print(f'   Location: {c.get("city")}, {c.get("state")} {c.get("zip_code")}')
    print(f'   Rating: {c.get("google_rating")}/5.0 with {c.get("google_review_count")} reviews')
    print(f'   Phone: {c.get("phone")}')
    print(f'   Website: {c.get("website")}')
    print(f'   Email: {c.get("email")}')
    print(f'   Address: {c.get("address")}')
    print(f'   Place ID: {c.get("google_place_id")}')
    
# Also show by city
print('\n\n' + '=' * 80)
print('CONTRACTORS BY CITY:')
print('=' * 80)

# Group by city
cities = {}
for c in result.data:
    city = c.get('city') or 'Unknown'
    if city not in cities:
        cities[city] = []
    cities[city].append(c)

for city, contractors in sorted(cities.items()):
    print(f'\n{city.upper()}: {len(contractors)} contractors')
    for c in contractors[:5]:  # Show top 5 per city
        print(f'  - {c.get("company_name")} ({c.get("google_review_count")} reviews, {c.get("google_rating")}/5.0)')
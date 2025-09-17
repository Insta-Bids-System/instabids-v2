#!/usr/bin/env python3
"""
Show all companies found sorted by various criteria to understand the landscape
"""
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from database_simple import db

# Get ALL holiday lighting contractors
result = db.client.table('potential_contractors').select('*').ilike('project_type', '%holiday%').execute()

# Deduplicate by Google Place ID
unique_contractors = {}
for c in result.data:
    key = c.get('google_place_id') or f"{c.get('company_name')}_{c.get('phone')}"
    if key not in unique_contractors or (c.get('google_review_count') or 0) > (unique_contractors[key].get('google_review_count') or 0):
        unique_contractors[key] = c

contractors = list(unique_contractors.values())

# Show companies by different criteria
print("HOLIDAY LIGHTING COMPANIES IN SOUTH FLORIDA")
print("=" * 80)
print(f"Total unique companies: {len(contractors)}")

# Sort by review count
print("\n\nTOP 20 BY REVIEW COUNT:")
print("=" * 80)
by_reviews = sorted(contractors, key=lambda x: x.get('google_review_count') or 0, reverse=True)
for i, c in enumerate(by_reviews[:20]):
    print(f"{i+1}. {c.get('company_name')} - {c.get('city', 'Unknown')}, {c.get('state', 'FL')}")
    print(f"   Reviews: {c.get('google_review_count', 0)} | Rating: {c.get('google_rating', 0)}/5.0")

# Companies with high ratings and decent reviews
print("\n\nHIGH QUALITY (4.8+ rating with 20+ reviews):")
print("=" * 80)
high_quality = [c for c in contractors if (c.get('google_rating') or 0) >= 4.8 and (c.get('google_review_count') or 0) >= 20]
high_quality.sort(key=lambda x: x.get('google_review_count') or 0, reverse=True)
for i, c in enumerate(high_quality[:15]):
    print(f"{i+1}. {c.get('company_name')} - {c.get('city', 'Unknown')}, {c.get('state', 'FL')}")
    print(f"   Reviews: {c.get('google_review_count', 0)} | Rating: {c.get('google_rating', 0)}/5.0")

# Local to 33442/Deerfield Beach area
print("\n\nLOCAL TO TARGET AREA (Coconut Creek/Deerfield Beach/Pompano Beach):")
print("=" * 80)
local_cities = ['coconut creek', 'deerfield beach', 'pompano beach', 'coral springs', 'boca raton']
local = [c for c in contractors if (c.get('city') or '').lower() in local_cities]
local.sort(key=lambda x: x.get('google_review_count') or 0, reverse=True)
for i, c in enumerate(local[:15]):
    print(f"{i+1}. {c.get('company_name')} - {c.get('city', 'Unknown')}, {c.get('state', 'FL')}")
    print(f"   Reviews: {c.get('google_review_count', 0)} | Rating: {c.get('google_rating', 0)}/5.0")

# Check for specific companies the user might know
print("\n\nCHECKING FOR SPECIFIC COMPANIES:")
print("=" * 80)
companies_to_check = [
    'jm holiday', 'brite nites', 'event decor', 'exceptional holiday',
    'trimlight', 'christmas decor', 'holiday fantasy'
]
for name_check in companies_to_check:
    found = [c for c in contractors if name_check in c.get('company_name', '').lower()]
    if found:
        print(f"\n'{name_check.upper()}':")
        for c in found:
            print(f"  - {c.get('company_name')} ({c.get('google_review_count', 0)} reviews, {c.get('google_rating', 0)}/5.0) - {c.get('city', 'Unknown')}")
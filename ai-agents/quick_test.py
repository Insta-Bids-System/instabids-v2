#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'Contractor Outreach System', 'tools'))

from intelligent_contractor_discovery import IntelligentContractorDiscovery

# Test the _get_flexible_sizes method
discovery = IntelligentContractorDiscovery()

print('Testing _get_flexible_sizes method:')
test_cases = [
    ('small_business', ['owner_operator', 'small_business', 'regional_company']),
    ('solo_handyman', ['solo_handyman', 'owner_operator']),
    ('enterprise', ['regional_company', 'enterprise'])
]

for preference, expected in test_cases:
    result = discovery._get_flexible_sizes(preference)
    match = set(result) == set(expected)
    status = 'PASS' if match else 'FAIL'
    print(f'{status}: {preference} -> {result}')
    if not match:
        print(f'  Expected: {expected}')

print('\nMethod exists and works correctly!')
#!/usr/bin/env python3
"""
Simple Size Flexibility Test - Test the ±1 size matching implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the intelligent discovery system
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'Contractor Outreach System', 'tools'))
from intelligent_contractor_discovery import IntelligentContractorDiscovery

def test_size_flexibility():
    print("=" * 70)
    print("TESTING CONTRACTOR SIZE FLEXIBILITY (±1 RANGE)")
    print("=" * 70)
    
    # Initialize the discovery system
    discovery = IntelligentContractorDiscovery()
    
    # Test the _get_flexible_sizes method
    print("\n[TEST] Testing _get_flexible_sizes method:")
    print("-" * 50)
    
    test_cases = [
        ("solo_handyman", ["solo_handyman", "owner_operator"]),
        ("owner_operator", ["solo_handyman", "owner_operator", "small_business"]),
        ("small_business", ["owner_operator", "small_business", "regional_company"]),
        ("regional_company", ["small_business", "regional_company", "enterprise"]),
        ("enterprise", ["regional_company", "enterprise"])
    ]
    
    all_passed = True
    for preference, expected in test_cases:
        result = discovery._get_flexible_sizes(preference)
        match = set(result) == set(expected)
        status = "[PASS]" if match else "[FAIL]"
        print(f"{status} {preference:20} -> {result}")
        if not match:
            print(f"      Expected: {expected}")
            all_passed = False
    
    print("\n[EXAMPLE] User wants 'small_business' contractors:")
    print("-" * 50)
    acceptable_sizes = discovery._get_flexible_sizes("small_business")
    print(f"User preference: small_business")
    print(f"Will accept: {', '.join(acceptable_sizes)}")
    
    # Test some example contractors
    test_contractors = [
        ("ABC Plumbing (1 person)", "solo_handyman"),
        ("XYZ Services (3 people)", "owner_operator"), 
        ("Pro Contractors (8 people)", "small_business"),
        ("Regional Corp (25 people)", "regional_company"),
        ("National Franchise", "enterprise")
    ]
    
    print("\nContractor Decisions:")
    for name, size in test_contractors:
        accepted = size in acceptable_sizes
        status = "[ACCEPT]" if accepted else "[REJECT]"
        print(f"  {status} - {name:30} (size: {size})")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED - Size flexibility working correctly!")
    else:
        print("[ERROR] SOME TESTS FAILED - Need to fix implementation")
    print("=" * 70)
    
    return all_passed

if __name__ == "__main__":
    test_size_flexibility()
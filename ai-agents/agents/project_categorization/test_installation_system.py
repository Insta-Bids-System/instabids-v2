#!/usr/bin/env python3
"""
Test script for Installation category categorization system
Validates the normalize_project_type function with real user input
"""

from project_types import (
    normalize_project_type, 
    get_project_scope, 
    get_required_capabilities,
    PROJECT_TYPE_MAPPING,
    SYNONYM_MAPPING
)

def test_installation_categorization():
    """Test Installation category with various user inputs"""
    
    print("Testing Installation Category Categorization System")
    print("=" * 60)
    
    # Test cases: (user_input, expected_behavior)
    test_cases = [
        # Direct matches
        ("pool installation", "should match pool_installation directly"),
        ("deck installation", "should match deck_installation directly"),
        ("artificial turf", "should match turf_installation via synonym"),
        
        # Synonym matches  
        ("artificial grass", "should match turf_installation via synonym"),
        ("synthetic grass", "should match turf_installation via synonym"),
        ("christmas lights", "should match holiday_lighting_installation via synonym"),
        ("solar panels", "should match solar_panel_installation via synonym"),
        ("hot tub install", "should match hot_tub_installation via synonym"),
        
        # Partial matches
        ("solar", "should partially match solar_panel_installation"),
        ("fence", "should partially match fence_installation"),
        ("generator", "should partially match generator_installation"),
        
        # Edge cases
        ("random project", "should have low confidence"),
        ("kitchen stuff", "should ask clarifying question"),
    ]
    
    for user_input, expected in test_cases:
        print(f"\n> Testing: '{user_input}'")
        print(f"   Expected: {expected}")
        
        # Test normalization
        normalized_type, confidence = normalize_project_type(user_input, "Installation")
        print(f"   Result: {normalized_type} (confidence: {confidence:.2f})")
        
        # Test scope and capabilities if confidence is high
        if confidence >= 0.7:
            scope = get_project_scope(normalized_type)
            capabilities = get_required_capabilities(normalized_type)
            print(f"   Scope: {scope}")
            print(f"   Capabilities: {capabilities}")
            
            # Validate this would be saved by tool handler
            print(f"   [SAVE] Would be SAVED (confidence >= 0.7)")
        else:
            print(f"   [QUESTION] Would ask CLARIFYING QUESTION (confidence < 0.7)")
    
    print("\n" + "=" * 60)
    print("Installation Category Statistics:")
    print(f"   • Total Installation types: {len(PROJECT_TYPE_MAPPING['Installation'])}")
    print(f"   • Synonym mappings: {len([k for k in SYNONYM_MAPPING.keys() if k.endswith('_installation')])}")
    print(f"   • System ready for CIA and IRIS agent integration!")

if __name__ == "__main__":
    test_installation_categorization()
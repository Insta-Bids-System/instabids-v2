#!/usr/bin/env python3
"""
Test CDA Discovery with proper UUID bid card ID and tracing enabled
"""
import asyncio
import uuid
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.cda.agent import ContractorDiscoveryAgent
from utils.langfuse_config import tracing

async def test_cda_with_real_uuid():
    """Test CDA discovery with proper UUID"""
    
    print("=== CDA Discovery Test with Real UUID ===")
    
    # Use existing bid card ID from database
    test_bid_card_id = "4aa5e277-82b1-4679-a86a-24fd56b10e4c"  # Boynton Beach roof project
    print(f"Using existing bid card ID: {test_bid_card_id}")
    
    # Check tracing status
    print(f"Langfuse tracing enabled: {tracing.enabled}")
    
    # Test location
    test_location = {
        "zip_code": "33101",
        "city": "Miami", 
        "state": "FL",
        "coordinates": [25.7617, -80.1918]
    }
    
    # Create CDA agent
    cda = ContractorDiscoveryAgent()
    
    try:
        print(f"\n[CDA TEST] Testing CDA discovery for Miami kitchen renovation...")
        print(f"Location: {test_location}")
        
        # Run contractor discovery
        result = await cda.discover_contractors(
            bid_card_id=test_bid_card_id,
            contractors_needed=4,
            radius_miles=15
        )
        
        print(f"\n[SUCCESS] CDA Discovery Results:")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Contractors found: {result.get('contractors_found', 0)}")
        print(f"Execution time: {result.get('execution_time_seconds', 0):.2f}s")
        
        if result.get('contractors'):
            print(f"\nFirst contractor example:")
            contractor = result['contractors'][0]
            print(f"  - Company: {contractor.get('company_name', 'N/A')}")
            print(f"  - City: {contractor.get('city', 'N/A')}")
            print(f"  - Specialties: {contractor.get('specialties', [])}")
        
        # Check if traces were created
        if tracing.enabled:
            print(f"\n[TRACING] Flushing traces to Langfuse...")
            tracing.flush()
            print(f"   -> Check https://us.cloud.langfuse.com for traces")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] CDA Discovery failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_cda_with_real_uuid())
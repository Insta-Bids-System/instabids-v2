"""
Corrected Tier Response Rate Math for CDA
Implements proper response rates: Tier 1 (90%), Tier 2 (70%), Tier 3 (50%)
"""

class ContractorResponseCalculator:
    """Calculate contractors needed based on tier response rates"""
    
    # Correct response rates per tier
    TIER_RESPONSE_RATES = {
        1: 0.90,  # Tier 1: 90% response rate (internal contractors)
        2: 0.70,  # Tier 2: 70% response rate (previous contacts)  
        3: 0.50   # Tier 3: 50% response rate (cold web search)
    }
    
    def calculate_contractors_needed(self, bids_needed: int, tier_availability: dict) -> dict:
        """
        Calculate how many contractors to contact per tier to get required bids
        
        Args:
            bids_needed: Number of bids required (e.g., 5)
            tier_availability: Dict with available contractor counts per tier
                             e.g., {"tier1": 3, "tier2": 5, "tier3": 100}
        
        Returns:
            Dict with contractor allocation per tier and expected responses
        """
        result = {
            "bids_needed": bids_needed,
            "tier_allocation": {},
            "expected_responses": {},
            "total_contractors": 0,
            "confidence_percentage": 0,
            "explanation": []
        }
        
        remaining_bids_needed = bids_needed
        
        # Process Tier 1 first (best response rate)
        tier1_available = tier_availability.get("tier1", 0)
        if tier1_available > 0 and remaining_bids_needed > 0:
            # Calculate expected responses from Tier 1
            tier1_expected_responses = tier1_available * self.TIER_RESPONSE_RATES[1]
            
            if tier1_expected_responses >= remaining_bids_needed:
                # Tier 1 alone can fulfill requirements
                tier1_to_contact = min(
                    tier1_available,
                    int(remaining_bids_needed / self.TIER_RESPONSE_RATES[1] + 0.5)
                )
                result["tier_allocation"]["tier1"] = tier1_to_contact
                result["expected_responses"]["tier1"] = tier1_to_contact * self.TIER_RESPONSE_RATES[1]
                remaining_bids_needed = 0
                result["explanation"].append(
                    f"Tier 1: Contact {tier1_to_contact} contractors (90% response rate = {tier1_to_contact * 0.9:.1f} bids)"
                )
            else:
                # Use all Tier 1 contractors
                result["tier_allocation"]["tier1"] = tier1_available
                result["expected_responses"]["tier1"] = tier1_expected_responses
                remaining_bids_needed -= tier1_expected_responses
                result["explanation"].append(
                    f"Tier 1: Contact all {tier1_available} contractors (90% response rate = {tier1_expected_responses:.1f} bids)"
                )
        
        # Process Tier 2 if still need bids
        tier2_available = tier_availability.get("tier2", 0)
        if tier2_available > 0 and remaining_bids_needed > 0:
            tier2_expected_responses = tier2_available * self.TIER_RESPONSE_RATES[2]
            
            if tier2_expected_responses >= remaining_bids_needed:
                # Tier 2 can fulfill remaining requirements
                tier2_to_contact = min(
                    tier2_available,
                    int(remaining_bids_needed / self.TIER_RESPONSE_RATES[2] + 0.5)
                )
                result["tier_allocation"]["tier2"] = tier2_to_contact
                result["expected_responses"]["tier2"] = tier2_to_contact * self.TIER_RESPONSE_RATES[2]
                remaining_bids_needed = 0
                result["explanation"].append(
                    f"Tier 2: Contact {tier2_to_contact} contractors (70% response rate = {tier2_to_contact * 0.7:.1f} bids)"
                )
            else:
                # Use all Tier 2 contractors
                result["tier_allocation"]["tier2"] = tier2_available
                result["expected_responses"]["tier2"] = tier2_expected_responses
                remaining_bids_needed -= tier2_expected_responses
                result["explanation"].append(
                    f"Tier 2: Contact all {tier2_available} contractors (70% response rate = {tier2_expected_responses:.1f} bids)"
                )
        
        # Process Tier 3 if still need bids
        tier3_available = tier_availability.get("tier3", 0)
        if tier3_available > 0 and remaining_bids_needed > 0:
            # Calculate how many Tier 3 contractors needed
            tier3_needed = int(remaining_bids_needed / self.TIER_RESPONSE_RATES[3] + 0.5)
            tier3_to_contact = min(tier3_available, tier3_needed)
            
            result["tier_allocation"]["tier3"] = tier3_to_contact
            result["expected_responses"]["tier3"] = tier3_to_contact * self.TIER_RESPONSE_RATES[3]
            
            if tier3_to_contact < tier3_needed:
                result["explanation"].append(
                    f"Tier 3: Contact {tier3_to_contact} contractors (limited availability, 50% response rate = {tier3_to_contact * 0.5:.1f} bids)"
                )
            else:
                result["explanation"].append(
                    f"Tier 3: Contact {tier3_to_contact} contractors (50% response rate = {tier3_to_contact * 0.5:.1f} bids)"
                )
        
        # Calculate totals
        result["total_contractors"] = sum(result["tier_allocation"].values())
        total_expected = sum(result["expected_responses"].values())
        result["confidence_percentage"] = min(100, int((total_expected / bids_needed) * 100))
        
        # Add summary
        result["explanation"].append(f"\nTotal: {result['total_contractors']} contractors to contact")
        result["explanation"].append(f"Expected: {total_expected:.1f} bids (need {bids_needed})")
        result["explanation"].append(f"Confidence: {result['confidence_percentage']}%")
        
        return result
    
    def explain_campaign_strategy(self, bids_needed: int, tier_availability: dict) -> str:
        """Generate human-readable campaign strategy explanation"""
        
        calc = self.calculate_contractors_needed(bids_needed, tier_availability)
        
        explanation = [
            "CAMPAIGN ORCHESTRATION STRATEGY",
            "=" * 40,
            f"Target: {bids_needed} bids needed",
            "",
            "TIER RESPONSE RATES:",
            "- Tier 1 (Internal): 90% response rate",
            "- Tier 2 (Previous): 70% response rate", 
            "- Tier 3 (Web Search): 50% response rate",
            "",
            "CONTRACTOR ALLOCATION:"
        ]
        
        explanation.extend(calc["explanation"])
        
        if calc["confidence_percentage"] >= 100:
            explanation.append("\n[SUCCESS] HIGH CONFIDENCE: Expected to meet bid target")
        elif calc["confidence_percentage"] >= 80:
            explanation.append("\n[WARNING] GOOD CONFIDENCE: Should meet target with follow-up")
        else:
            explanation.append("\n[ALERT] LOW CONFIDENCE: May need additional outreach waves")
        
        return "\n".join(explanation)


# Example usage and testing
if __name__ == "__main__":
    calculator = ContractorResponseCalculator()
    
    # Test scenario from user's example
    print("TEST: User needs 5 bids")
    print("-" * 40)
    
    # Scenario 1: Limited Tier 1 & 2, plenty of Tier 3
    tier_availability = {
        "tier1": 2,   # 2 internal contractors available
        "tier2": 3,   # 3 previous contacts available
        "tier3": 100  # Many web search results available
    }
    
    result = calculator.explain_campaign_strategy(5, tier_availability)
    print(result)
    
    print("\n" + "=" * 60 + "\n")
    
    # Scenario 2: Plenty of Tier 1 available
    print("TEST: Plenty of Tier 1 contractors")
    print("-" * 40)
    
    tier_availability = {
        "tier1": 10,  # 10 internal contractors available
        "tier2": 5,   # 5 previous contacts available
        "tier3": 50   # Web search results available
    }
    
    result = calculator.explain_campaign_strategy(5, tier_availability)
    print(result)
    
    print("\n" + "=" * 60 + "\n")
    
    # Scenario 3: No Tier 1 or 2, only Tier 3
    print("TEST: Only Tier 3 contractors available")
    print("-" * 40)
    
    tier_availability = {
        "tier1": 0,   # No internal contractors
        "tier2": 0,   # No previous contacts
        "tier3": 100  # Only web search available
    }
    
    result = calculator.explain_campaign_strategy(5, tier_availability)
    print(result)
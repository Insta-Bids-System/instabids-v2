"""
Connection Fee Calculator for InstaBids
Calculates progressive fees based on bid amounts with referral integration
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Any
import json
from datetime import datetime


class ConnectionFeeCalculator:
    """
    Progressive fee structure that helps small contractors while making money on large projects
    """
    
    def __init__(self):
        self.version = "v1.0"
        
    def calculate_connection_fee(
        self, 
        winning_bid_amount: Decimal, 
        project_category: str,
        referral_code: Optional[str] = None,
        referrer_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate connection fee based on winning bid amount and project category
        
        Args:
            winning_bid_amount: The contractor's winning bid amount
            project_category: Category like 'large_project', 'year_round', 'repair', etc.
            referral_code: Referral code if homeowner was referred
            referrer_user_id: ID of user who referred the homeowner
            
        Returns:
            Dict with fee breakdown and referral info
        """
        
        # Convert to Decimal for precise calculations
        bid_amount = Decimal(str(winning_bid_amount))
        
        # Calculate base fee using progressive tiers
        base_fee = self._calculate_base_fee(bid_amount)
        
        # Apply category adjustments
        adjusted_fee = self._apply_category_adjustment(base_fee, project_category)
        
        # Handle referral system (50% to referrer)
        fee_breakdown = self._calculate_referral_split(
            adjusted_fee, referral_code, referrer_user_id
        )
        
        return {
            "winning_bid_amount": float(bid_amount),
            "project_category": project_category,
            "base_fee": float(base_fee),
            "final_fee": float(adjusted_fee),
            "platform_portion": fee_breakdown["platform_portion"],
            "referrer_portion": fee_breakdown["referrer_portion"], 
            "referral_info": fee_breakdown["referral_info"],
            "calculation_method": f"progressive_bid_amount_{self.version}",
            "calculated_at": datetime.now().isoformat()
        }
    
    def _calculate_base_fee(self, bid_amount: Decimal) -> Decimal:
        """
        Progressive fee tiers based on bid amount
        Helps small contractors, makes money on large projects
        """
        
        if bid_amount <= 100:           # Neighbor help, IKEA assembly
            return Decimal("20")
        elif bid_amount <= 500:        # Small handyman, sprinkler fixes  
            return Decimal("30")
        elif bid_amount <= 2000:       # Medium handyman, repairs
            return Decimal("50")
        elif bid_amount <= 5000:       # Larger handyman, small projects
            return Decimal("75")
        elif bid_amount <= 10000:      # Medium projects, bathroom refresh
            return Decimal("125")
        elif bid_amount <= 25000:      # Large projects, kitchen, roof
            return Decimal("175")
        elif bid_amount <= 50000:      # Major renovations
            return Decimal("200")
        else:                          # Premium projects $50k+
            return Decimal("250")
    
    def _apply_category_adjustment(self, base_fee: Decimal, category: str) -> Decimal:
        """
        Adjust base fee based on project category
        """
        
        adjustment_factors = {
            "year_round": Decimal("0.7"),      # 30% discount for recurring services
            "emergency": Decimal("1.25"),      # 25% premium for urgent repairs
            "group_bidding": Decimal("0.8"),   # 20% group discount
            "large_project": Decimal("1.0"),   # No adjustment
            "repair": Decimal("1.0"),          # No adjustment
            "handyman": Decimal("1.0")         # No adjustment
        }
        
        factor = adjustment_factors.get(category, Decimal("1.0"))
        adjusted_fee = base_fee * factor
        
        # Minimum fee constraints
        if category == "year_round":
            adjusted_fee = max(adjusted_fee, Decimal("30"))  # Minimum $30 for recurring
        
        # Round to nearest cent
        return adjusted_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _calculate_referral_split(
        self, 
        total_fee: Decimal, 
        referral_code: Optional[str],
        referrer_user_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Split fee between platform and referrer (50/50 if referred)
        """
        
        if referral_code and referrer_user_id:
            # 50% to referrer, 50% to platform
            referrer_portion = (total_fee * Decimal("0.5")).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            platform_portion = total_fee - referrer_portion
            
            referral_info = {
                "referral_code": referral_code,
                "referrer_user_id": referrer_user_id,
                "referrer_payout": float(referrer_portion),
                "split_percentage": 50
            }
        else:
            # No referral - 100% to platform
            referrer_portion = Decimal("0")
            platform_portion = total_fee
            referral_info = None
            
        return {
            "platform_portion": float(platform_portion),
            "referrer_portion": float(referrer_portion),
            "referral_info": referral_info
        }
    
    def determine_project_category(
        self, 
        service_type: str, 
        project_type: str,
        budget_min: Optional[int] = None,
        budget_max: Optional[int] = None,
        urgency_level: Optional[str] = None,
        group_bid_eligible: bool = False
    ) -> str:
        """
        Determine project category from bid card data
        """
        
        # Group bidding takes precedence
        if group_bid_eligible:
            return "group_bidding"
            
        # Emergency/urgent repairs
        if urgency_level in ["emergency", "urgent"] or service_type == "repair":
            return "emergency" if urgency_level == "emergency" else "repair"
            
        # Year-round contracts
        if (service_type == "ongoing_service" or 
            project_type in ["lawn_care", "landscaping", "pool_maintenance"] or
            service_type == "maintenance"):
            return "year_round"
            
        # Large projects based on budget
        if budget_min and budget_min >= 15000:
            return "large_project"
        elif budget_max and budget_max >= 15000:
            return "large_project"
            
        # Default to handyman for smaller projects
        return "handyman"


# Example usage and test cases
if __name__ == "__main__":
    calculator = ConnectionFeeCalculator()
    
    # Test cases matching user scenarios
    test_cases = [
        {
            "name": "IKEA Assembly",
            "bid_amount": 75,
            "category": "handyman",
            "expected_fee": 30
        },
        {
            "name": "Sprinkler Fix", 
            "bid_amount": 200,
            "category": "repair",
            "expected_fee": 50
        },
        {
            "name": "Turf Job",
            "bid_amount": 4000, 
            "category": "handyman",
            "expected_fee": 75
        },
        {
            "name": "Kitchen Remodel",
            "bid_amount": 35000,
            "category": "large_project", 
            "expected_fee": 200
        },
        {
            "name": "Monthly Lawn Care", 
            "bid_amount": 100,
            "category": "year_round",
            "expected_fee": 30  # 30% discount, $30 minimum
        }
    ]
    
    print("=== CONNECTION FEE CALCULATOR TESTS ===\n")
    
    for test in test_cases:
        result = calculator.calculate_connection_fee(
            winning_bid_amount=test["bid_amount"],
            project_category=test["category"]
        )
        
        print(f"{test['name']}:")
        print(f"  Bid Amount: ${test['bid_amount']}")
        print(f"  Category: {test['category']}")
        print(f"  Connection Fee: ${result['final_fee']}")
        print(f"  Expected: ${test['expected_fee']}")
        print(f"  ✅ {'PASS' if result['final_fee'] == test['expected_fee'] else 'FAIL'}\n")
    
    # Test referral scenario
    print("=== REFERRAL TEST ===")
    referral_result = calculator.calculate_connection_fee(
        winning_bid_amount=4000,
        project_category="handyman",
        referral_code="REF123",
        referrer_user_id="user_456"
    )
    
    print(f"Turf Job with Referral:")
    print(f"  Total Fee: ${referral_result['final_fee']}")
    print(f"  Platform Gets: ${referral_result['platform_portion']}")
    print(f"  Referrer Gets: ${referral_result['referrer_portion']}")
    print(f"  Referral Info: {referral_result['referral_info']}")
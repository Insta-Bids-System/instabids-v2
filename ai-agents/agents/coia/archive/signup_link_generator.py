"""
COIA Signup Link Generator
Generates secure signup links for contractor onboarding from landing page conversations
"""

import base64
import json
import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class SignupLinkGenerator:
    """Generates secure signup links with embedded contractor data"""
    
    def __init__(self):
        """Initialize with secret key for signing"""
        # Use environment variable or generate a stable secret
        self.secret_key = os.getenv("SIGNUP_SECRET_KEY", "instabids-secure-signup-2025")
        self.base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        
    def generate_signup_link(
        self, 
        contractor_profile: Dict[str, Any],
        contractor_lead_id: str,
        expires_in_hours: int = 72
    ) -> Dict[str, Any]:
        """
        Generate a secure signup link with embedded profile data
        
        Args:
            contractor_profile: Extracted contractor information
            contractor_lead_id: Thread ID for memory linkage
            expires_in_hours: Link expiration time (default 72 hours)
            
        Returns:
            Dict with signup URL and metadata
        """
        try:
            # Prepare the data payload
            expiry = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            payload = {
                "contractor_lead_id": contractor_lead_id,
                "profile": {
                    "company_name": contractor_profile.get("company_name", ""),
                    "contact_name": contractor_profile.get("contact_name", ""),
                    "email": contractor_profile.get("email", ""),
                    "phone": contractor_profile.get("phone", ""),
                    "primary_trade": contractor_profile.get("primary_trade", ""),
                    "years_in_business": contractor_profile.get("years_in_business"),
                    "service_areas": contractor_profile.get("service_areas", []),
                    "specializations": contractor_profile.get("specializations", []),
                    "website": contractor_profile.get("website", ""),
                    "license_info": contractor_profile.get("license_info", ""),
                    "team_size": contractor_profile.get("team_size"),
                    "differentiators": contractor_profile.get("differentiators", "")
                },
                "expires": expiry.isoformat(),
                "created": datetime.utcnow().isoformat()
            }
            
            # Encode the payload
            payload_json = json.dumps(payload, separators=(',', ':'))
            payload_encoded = base64.urlsafe_b64encode(payload_json.encode()).decode()
            
            # Generate signature for security
            signature = self._generate_signature(payload_encoded)
            
            # Build the signup URL
            params = {
                "data": payload_encoded,
                "sig": signature,
                "source": "landing_coia"
            }
            
            signup_url = f"{self.base_url}/contractor/signup?{urlencode(params)}"
            
            # Also generate a shorter version using just the contractor_lead_id
            short_params = {
                "id": contractor_lead_id,
                "email": contractor_profile.get("email", ""),
                "source": "landing_coia"
            }
            short_url = f"{self.base_url}/contractor/signup?{urlencode(short_params)}"
            
            return {
                "success": True,
                "signup_url": signup_url,
                "short_url": short_url,
                "expires": expiry.isoformat(),
                "contractor_lead_id": contractor_lead_id,
                "email": contractor_profile.get("email", ""),
                "company_name": contractor_profile.get("company_name", ""),
                "profile_completeness": self._calculate_completeness(contractor_profile)
            }
            
        except Exception as e:
            logger.error(f"Error generating signup link: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_signature(self, data: str) -> str:
        """Generate HMAC signature for data integrity"""
        signature = hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature[:16]  # Use first 16 chars for shorter URLs
    
    def verify_signup_link(self, data: str, signature: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a signup link
        
        Args:
            data: Base64 encoded payload
            signature: HMAC signature
            
        Returns:
            Decoded payload if valid, None if invalid
        """
        try:
            # Verify signature
            expected_signature = self._generate_signature(data)
            if signature != expected_signature:
                logger.warning("Invalid signature on signup link")
                return None
            
            # Decode payload
            payload_json = base64.urlsafe_b64decode(data.encode()).decode()
            payload = json.loads(payload_json)
            
            # Check expiration
            expires = datetime.fromisoformat(payload["expires"])
            if datetime.utcnow() > expires:
                logger.warning("Signup link has expired")
                return None
            
            return payload
            
        except Exception as e:
            logger.error(f"Error verifying signup link: {e}")
            return None
    
    def _calculate_completeness(self, profile: Dict[str, Any]) -> float:
        """Calculate profile completeness percentage"""
        required_fields = [
            "company_name", "email", "phone", "primary_trade",
            "years_in_business", "service_areas"
        ]
        
        completed = sum(1 for field in required_fields if profile.get(field))
        return (completed / len(required_fields)) * 100.0
    
    def generate_signup_message(self, signup_data: Dict[str, Any]) -> str:
        """
        Generate a friendly message with the signup link
        
        Args:
            signup_data: Result from generate_signup_link
            
        Returns:
            Message to send to contractor
        """
        if not signup_data.get("success"):
            return "I'm having trouble generating your signup link. Please try again or contact support."
        
        company_name = signup_data.get("company_name", "your company")
        email = signup_data.get("email", "")
        completeness = signup_data.get("profile_completeness", 0)
        
        message = f"""
Perfect! I have your company profile ready for {company_name}. 

Based on our conversation, I've pre-filled your account with:
• Email: {email}
• Company details and specializations
• Service areas and experience
• Profile completeness: {completeness:.0f}%

To complete your contractor account and start receiving bid opportunities:

🔗 **Click here to set your password and activate your account:**
{signup_data['short_url']}

This link will:
• Take you to a secure signup page
• Pre-fill all the information we discussed
• Let you set your password
• Connect your account to our conversation history
• Give you immediate access to relevant bid opportunities

The link expires in 72 hours for security. Once you've set your password, you'll have full access to:
• InstaBids contractor dashboard
• Real-time bid notifications
• Direct messaging with homeowners
• Your personal AI assistant (me!) for ongoing support

After you sign up, I'll remember everything we discussed and can help you with bidding strategies, profile optimization, and finding the best projects for your expertise.

Ready to get started? Just click the link above!
"""
        
        return message.strip()


# Singleton instance for use across the application
signup_generator = SignupLinkGenerator()


# Export functions for easy use
def generate_contractor_signup_link(
    contractor_profile: Dict[str, Any],
    contractor_lead_id: str
) -> Dict[str, Any]:
    """Generate a signup link for a contractor"""
    return signup_generator.generate_signup_link(contractor_profile, contractor_lead_id)


def verify_contractor_signup_link(data: str, signature: str) -> Optional[Dict[str, Any]]:
    """Verify a signup link is valid"""
    return signup_generator.verify_signup_link(data, signature)


def create_signup_message(signup_data: Dict[str, Any]) -> str:
    """Create a friendly message with signup link"""
    return signup_generator.generate_signup_message(signup_data)
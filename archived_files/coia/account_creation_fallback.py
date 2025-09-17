"""
Account Creation Fallback System for COIA
Provides account creation functionality when Anthropic API is unavailable
"""

import logging
import secrets
import string
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import os
from utils.database_simple import get_supabase_client

logger = logging.getLogger(__name__)


class AccountCreationFallback:
    """Fallback account creation system that doesn't depend on LLM APIs"""
    
    def __init__(self):
        self.supabase = None
    
    async def _get_supabase_client(self):
        """Get Supabase client"""
        if self.supabase is None:
            self.supabase = await get_supabase_client()
        return self.supabase
    
    async def create_contractor_account(self, contractor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a contractor account using the fallback system
        Returns account creation results with credentials
        """
        try:
            logger.info(f"Creating contractor account via fallback for: {contractor_data.get('company_name', 'Unknown')}")
            
            # Generate secure temporary password
            temp_password = self._generate_secure_password()
            
            # Get database client
            supabase = await self._get_supabase_client()
            
            # Prepare contractor data for database
            contractor_record = self._prepare_contractor_record(contractor_data, temp_password)
            
            # Insert into contractors table
            result = await supabase.table("contractors").insert(contractor_record).execute()
            
            if result.data and len(result.data) > 0:
                contractor_id = result.data[0]["id"]
                
                # Create auth user record if email provided
                auth_user_id = None
                if contractor_data.get("email"):
                    auth_user_id = await self._create_auth_user(contractor_data, temp_password)
                
                # Update contractor record with auth user ID
                if auth_user_id:
                    await supabase.table("contractors").update({"user_id": auth_user_id}).eq("id", contractor_id).execute()
                
                logger.info(f"✅ Successfully created contractor account: {contractor_id}")
                
                return {
                    "success": True,
                    "contractor_id": contractor_id,
                    "temp_password": temp_password,
                    "email": contractor_data.get("email"),
                    "company_name": contractor_data.get("company_name"),
                    "auth_user_id": auth_user_id,
                    "login_url": "http://localhost:5173/contractor/login",
                    "created_at": datetime.now().isoformat()
                }
            else:
                logger.error("Failed to create contractor record - no data returned")
                return {"success": False, "error": "Database insert failed"}
        
        except Exception as e:
            logger.error(f"Error creating contractor account: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_secure_password(self) -> str:
        """Generate a secure temporary password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(alphabet) for _ in range(12))
    
    def _prepare_contractor_record(self, contractor_data: Dict[str, Any], temp_password: str) -> Dict[str, Any]:
        """Prepare contractor data for database insertion"""
        
        # Extract core data with safe defaults
        company_name = contractor_data.get("company_name", "Unknown Company")
        contact_name = contractor_data.get("contact_name", "")
        email = contractor_data.get("email", "")
        phone = contractor_data.get("phone", "")
        
        # Extract specialties and other arrays
        specialties = contractor_data.get("specialties", [])
        if isinstance(specialties, str):
            specialties = [specialties]
        
        # Calculate tier based on available data
        tier = 1 if email and phone else 3
        
        # Build contractor record
        contractor_record = {
            "company_name": company_name,
            "specialties": specialties,
            "tier": tier,
            "availability_status": "available",
            "verified": False,  # Will be verified later
            "rating": 0.0,
            "total_jobs": 0,
            "total_earned": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Add optional fields if available
        if email:
            contractor_record["email"] = email
        if phone:
            contractor_record["phone"] = phone
        if contact_name:
            contractor_record["contact_name"] = contact_name
        if contractor_data.get("license_number"):
            contractor_record["license_number"] = contractor_data.get("license_number")
        if contractor_data.get("years_in_business"):
            contractor_record["years_in_business"] = contractor_data.get("years_in_business")
        
        # Store password hash or reference
        contractor_record["temp_password_hash"] = temp_password  # In production, hash this
        
        return contractor_record
    
    async def _create_auth_user(self, contractor_data: Dict[str, Any], temp_password: str) -> Optional[str]:
        """Create auth user if credentials are available"""
        try:
            email = contractor_data.get("email")
            if not email:
                return None
            
            # In production, this would integrate with Supabase Auth
            # For now, create a user ID and store in profiles table
            auth_user_id = str(uuid.uuid4())
            
            supabase = await self._get_supabase_client()
            
            # Create profile record
            profile_data = {
                "id": auth_user_id,
                "role": "contractor",
                "full_name": contractor_data.get("contact_name", contractor_data.get("company_name", "Contractor")),
                "phone": contractor_data.get("phone"),
                "email": email,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            await supabase.table("profiles").insert(profile_data).execute()
            logger.info(f"✅ Created profile for auth user: {auth_user_id}")
            
            return auth_user_id
            
        except Exception as e:
            logger.warning(f"Failed to create auth user: {e}")
            return None


# Global instance
account_creation_fallback = AccountCreationFallback()


async def create_contractor_account_fallback(contractor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Global function to create contractor account via fallback system
    Use this when COIA system fails due to API issues
    """
    return await account_creation_fallback.create_contractor_account(contractor_data)
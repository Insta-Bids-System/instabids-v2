"""
COIA State Management - Basic definitions
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class ContractorProfile(BaseModel):
    """Contractor profile information"""
    company_name: str = ""
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    specialties: List[str] = []
    years_in_business: Optional[int] = None
    license_verified: bool = False
    insurance_verified: bool = False
    rating: Optional[float] = None

class ConversationMessage(BaseModel):
    """Conversation message structure"""
    role: str
    content: str
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = {}
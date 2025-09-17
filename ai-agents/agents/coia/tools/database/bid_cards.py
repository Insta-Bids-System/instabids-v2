"""
Bid Card Search Tool for COIA
Searches for relevant bid cards for contractors
"""

import logging
import os
import sys
from typing import Dict, Any, List, Optional

from ..base import BaseTool

logger = logging.getLogger(__name__)


class BidCardSearchTool(BaseTool):
    """Search for bid cards matching contractor profile"""
    
    async def search_bid_cards(self, contractor_profile: Dict[str, Any], location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Real bid card search - delegates to ContractorContextAdapter
        EXTRACTED FROM LEGACY tools.py
        """
        logger.info(f"Searching bid cards for contractor: {contractor_profile.get('company_name', 'Unknown')}")
        
        try:
            # Use ContractorContextAdapter for proper unified memory access
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            from adapters.contractor_context import ContractorContextAdapter
            
            # Get contractor ID from profile
            contractor_id = contractor_profile.get("id") or contractor_profile.get("contractor_id", "unknown")
            
            # Use adapter to get available projects with privacy filtering
            adapter = ContractorContextAdapter()
            context = adapter.get_contractor_context(contractor_id)
            available_projects = context.get("available_projects", [])
            
            # Filter for electrical/lighting if that's the contractor's specialty
            specialties = contractor_profile.get("specialties", [])
            if any("electrical" in str(s).lower() or "lighting" in str(s).lower() for s in specialties):
                # Return projects that match contractor specialties
                filtered_projects = [p for p in available_projects 
                                   if "electrical" in str(p.get("project_type", "")).lower() 
                                   or "lighting" in str(p.get("project_type", "")).lower()]
                if filtered_projects:
                    logger.info(f"Found {len(filtered_projects)} matching projects via adapter")
                    return filtered_projects[:3]
            
            # Return general available projects
            logger.info(f"Found {len(available_projects)} general projects via adapter")
            return available_projects[:3]
                
        except Exception as e:
            logger.error(f"Error searching bid cards: {e}")
            return []
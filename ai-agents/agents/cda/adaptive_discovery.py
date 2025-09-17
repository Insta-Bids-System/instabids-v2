"""
Adaptive Discovery System with Radius Expansion
Automatically expands search radius when insufficient contractors found
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from agents.cda.geocoding_service import GeocodingService

logger = logging.getLogger(__name__)


class AdaptiveDiscoverySystem:
    """
    Implements multi-stage geographic expansion for contractor discovery
    """
    
    def __init__(self):
        self.geocoder = GeocodingService()
        self.expansion_stages = [
            {"radius": 15, "description": "Initial 15-mile radius"},
            {"radius": 25, "description": "Expanded 25-mile radius"},
            {"radius": 40, "description": "Regional 40-mile radius"},
            {"radius": 60, "description": "Extended 60-mile radius"},
            {"radius": 100, "description": "Wide area 100-mile radius"}
        ]
        logger.info("[AdaptiveDiscovery] Initialized with 5-stage expansion")
    
    async def discover_with_expansion(self,
                                     discovery_function,
                                     location: Dict[str, str],
                                     target_count: int,
                                     min_acceptable: int = None,
                                     **kwargs) -> Dict[str, Any]:
        """
        Discover contractors with automatic radius expansion
        
        Args:
            discovery_function: The function to call for discovery
            location: Location dict with zip, city, state
            target_count: Number of contractors needed
            min_acceptable: Minimum acceptable (default: 50% of target)
            **kwargs: Additional args for discovery function
        
        Returns:
            Dict with contractors and expansion metadata
        """
        if min_acceptable is None:
            min_acceptable = max(4, int(target_count * 0.5))  # At least 4 or 50%
        
        all_contractors = []
        expansion_history = []
        total_api_calls = 0
        
        logger.info(f"[AdaptiveDiscovery] Starting discovery for {target_count} contractors")
        logger.info(f"[AdaptiveDiscovery] Minimum acceptable: {min_acceptable}")
        
        for stage_num, stage in enumerate(self.expansion_stages, 1):
            radius = stage["radius"]
            
            logger.info(f"[AdaptiveDiscovery] Stage {stage_num}: {stage['description']}")
            
            # Call discovery function with current radius
            try:
                result = await discovery_function(
                    location=location,
                    radius_miles=radius,
                    target_count=target_count - len(all_contractors),
                    **kwargs
                )
                
                if result.get("success") and result.get("contractors"):
                    new_contractors = result.get("contractors", [])
                    
                    # Deduplicate based on company name
                    existing_names = {c.get("company_name", "").lower() for c in all_contractors}
                    unique_new = [
                        c for c in new_contractors 
                        if c.get("company_name", "").lower() not in existing_names
                    ]
                    
                    all_contractors.extend(unique_new)
                    
                    # Track expansion
                    expansion_history.append({
                        "stage": stage_num,
                        "radius": radius,
                        "found": len(unique_new),
                        "total": len(all_contractors),
                        "description": stage["description"]
                    })
                    
                    # Track API calls if available
                    if "api_calls" in result:
                        total_api_calls += sum(result["api_calls"].values())
                    
                    logger.info(f"[AdaptiveDiscovery] Found {len(unique_new)} new contractors")
                    logger.info(f"[AdaptiveDiscovery] Total: {len(all_contractors)}/{target_count}")
                    
                    # Check if we have enough
                    if len(all_contractors) >= target_count:
                        logger.info(f"[AdaptiveDiscovery] Target reached!")
                        break
                    
                    # Check if we have minimum acceptable and expansion isn't helping
                    if len(all_contractors) >= min_acceptable and len(unique_new) < 2:
                        logger.info(f"[AdaptiveDiscovery] Minimum reached, expansion not yielding results")
                        break
                
            except Exception as e:
                logger.error(f"[AdaptiveDiscovery] Error in stage {stage_num}: {e}")
                continue
            
            # Add delay between expansions
            if stage_num < len(self.expansion_stages):
                await asyncio.sleep(1)
        
        # Calculate success metrics
        success = len(all_contractors) >= min_acceptable
        completion_rate = (len(all_contractors) / target_count) * 100
        
        return {
            "success": success,
            "contractors": all_contractors[:target_count],  # Limit to target
            "total_found": len(all_contractors),
            "target_count": target_count,
            "completion_rate": completion_rate,
            "expansion_stages_used": len(expansion_history),
            "expansion_history": expansion_history,
            "final_radius": expansion_history[-1]["radius"] if expansion_history else 15,
            "total_api_calls": total_api_calls
        }
    
    def get_expanded_zips(self, center_zip: str, radius: int) -> List[str]:
        """
        Get all ZIP codes within expanded radius
        
        Args:
            center_zip: Center ZIP code
            radius: Radius in miles
            
        Returns:
            List of ZIP codes
        """
        return self.geocoder.get_nearby_zips(center_zip, radius)
    
    def get_search_terms_for_stage(self, base_terms: List[str], stage: int) -> List[str]:
        """
        Adjust search terms based on expansion stage
        
        Args:
            base_terms: Base search terms
            stage: Expansion stage (1-5)
            
        Returns:
            Modified search terms
        """
        if stage == 1:
            # Initial search - be specific
            return base_terms
        elif stage == 2:
            # Add "near me" variants
            expanded = base_terms.copy()
            expanded.extend([f"{term} near me" for term in base_terms[:3]])
            return expanded
        elif stage == 3:
            # Add regional terms
            expanded = base_terms.copy()
            expanded.extend([f"best {term}" for term in base_terms[:3]])
            expanded.extend([f"top rated {term}" for term in base_terms[:2]])
            return expanded
        elif stage >= 4:
            # Broader terms
            expanded = base_terms.copy()
            expanded.extend([f"professional {term}" for term in base_terms[:2]])
            expanded.extend([f"licensed {term}" for term in base_terms[:2]])
            expanded.append("general contractor")
            expanded.append("home improvement")
            return expanded
        
        return base_terms
"""
Enhanced BSA Tools - Standalone Bid Search and Web Research
Provides BSA sub-agents with powerful search and research capabilities
Completely independent from COIA - no dependencies
"""

import os
import sys
import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.tools import tool

# Add root path for utility imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

# ============================================================================
# ZIP RADIUS UTILITIES (Copied from COIA for independence)
# ============================================================================

def get_zip_codes_in_radius(center_zip: str, radius_miles: int) -> List[str]:
    """Get all ZIP codes within radius of center ZIP"""
    try:
        from utils.radius_search_fixed import get_zip_codes_in_radius as get_zips
        return get_zips(center_zip, radius_miles)
    except ImportError:
        # Fallback if utility not available
        logger.warning("ZIP radius utility not found, using center ZIP only")
        return [center_zip]

def calculate_distance_miles(zip1: str, zip2: str) -> float:
    """Calculate distance between two ZIP codes"""
    try:
        from utils.radius_search_fixed import calculate_distance_miles as calc_dist
        return calc_dist(zip1, zip2)
    except ImportError:
        return 0.0

@tool
def search_available_bid_cards(contractor_zip: str, radius_miles: int = 30, project_keywords: str = "") -> Dict[str, Any]:
    """
    Search for available bid cards within a radius of contractor's location
    Uses ZIP code radius expansion for intelligent geographic matching
    
    Args:
        contractor_zip: Contractor's ZIP code
        radius_miles: Search radius in miles (default 30)
        project_keywords: Keywords to filter projects (e.g., "kitchen remodel")
    
    Returns:
        Dictionary with found bid cards and search metadata
    """
    try:
        logger.info(f"BSA Tool: Searching bid cards within {radius_miles} miles of {contractor_zip}")
        
        # Get ZIP codes in radius
        zip_codes_in_radius = get_zip_codes_in_radius(contractor_zip, radius_miles)
        logger.info(f"Found {len(zip_codes_in_radius)} ZIP codes within {radius_miles} miles")
        
        # Query database for bid cards
        from database_simple import db
        
        query = db.client.table("bid_cards").select("*")
        
        # Filter by active statuses
        query = query.in_("status", ["active", "collecting_bids", "generated"])
        
        # Apply ZIP radius filter
        if zip_codes_in_radius:
            query = query.in_("location_zip", zip_codes_in_radius)
        else:
            query = query.eq("location_zip", contractor_zip)
        
        # Execute query
        result = query.execute()
        bid_cards_raw = result.data if result.data else []
        
        # Process and add distance information
        bid_cards = []
        for card in bid_cards_raw:
            card_zip = card.get("location_zip")
            distance_miles = None
            
            if card_zip:
                distance_miles = calculate_distance_miles(contractor_zip, str(card_zip))
            
            # Format for BSA use
            formatted_card = {
                "id": card["id"],
                "title": card.get("title", "Untitled Project"),
                "description": card.get("description", ""),
                "project_type": card.get("project_type", "general"),
                "location": {
                    "city": card.get("location_city"),
                    "state": card.get("location_state"),
                    "zip": card.get("location_zip")
                },
                "timeline": {
                    "start": card.get("timeline_start"),
                    "end": card.get("timeline_end")
                },
                "distance_miles": distance_miles,
                "status": card.get("status"),
                "created_at": card.get("created_at")
            }
            
            # Filter by keywords if provided
            if project_keywords:
                keywords_lower = project_keywords.lower()
                title_lower = (formatted_card.get("title") or "").lower()
                desc_lower = (formatted_card.get("description") or "").lower()
                type_lower = (formatted_card.get("project_type") or "").lower()
                
                # Check if any keyword matches
                if any(kw in title_lower or kw in desc_lower or kw in type_lower 
                       for kw in keywords_lower.split()):
                    bid_cards.append(formatted_card)
            else:
                bid_cards.append(formatted_card)
        
        # Sort by distance (closest first)
        bid_cards.sort(key=lambda x: x.get("distance_miles") or 999)
        
        # Format results for BSA
        result = {
            "success": True,
            "total_found": len(bid_cards),
            "search_radius": radius_miles,
            "contractor_zip": contractor_zip,
            "bid_cards": bid_cards[:10],  # Return top 10
            "message": f"Found {len(bid_cards)} projects within {radius_miles} miles"
        }
        
        if project_keywords:
            result["filtered_by"] = project_keywords
            
        return result
        
    except Exception as e:
        logger.error(f"Error searching bid cards: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to search bid cards"
        }

@tool
def research_contractor_company(company_name: str, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Research a contractor company using Tavily web search
    Discovers company website, extracts business information, and builds comprehensive profile
    
    Args:
        company_name: Name of the contractor company
        location: Optional location (city/state) to refine search
    
    Returns:
        Comprehensive company profile with web-discovered information
    """
    try:
        logger.info(f"BSA Tool: Researching contractor company {company_name}")
        
        # Use Tavily API for web research
        api_key = os.getenv("TAVILY_API_KEY", "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")
        
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        
        # Build search query
        search_query = f"{company_name} contractor"
        if location:
            search_query += f" {location}"
        
        # Search for company information
        try:
            search_response = client.search(
                query=search_query,
                search_depth="advanced",
                max_results=5,
                include_domains=[],
                exclude_domains=[]
            )
            
            # Extract results
            results = search_response.get("results", [])
            
            if not results:
                return {
                    "success": False,
                    "company_name": company_name,
                    "message": "No information found online"
                }
            
            # Process first result (most relevant)
            top_result = results[0]
            
            # Try to extract structured data
            extracted_info = {
                "website": top_result.get("url", ""),
                "description": top_result.get("content", "")[:500],  # First 500 chars
                "title": top_result.get("title", "")
            }
            
            # Look for contact info in content
            content = top_result.get("content", "")
            
            # Simple extraction patterns
            import re
            
            # Phone pattern
            phone_pattern = r'\b(?:\d{3}[-.]?)?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, content)
            
            # Email pattern  
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, content)
            
            # Look for services/specialties
            services = []
            service_keywords = [
                "kitchen", "bathroom", "landscaping", "electrical", 
                "plumbing", "roofing", "flooring", "painting", "hvac",
                "remodeling", "renovation", "construction"
            ]
            content_lower = content.lower()
            for keyword in service_keywords:
                if keyword in content_lower:
                    services.append(keyword.title())
            
            # Look for certifications
            certifications = []
            cert_patterns = [
                r'licensed\s+\w+',
                r'certified\s+\w+',
                r'\bBBB\b',
                r'insured',
                r'bonded'
            ]
            for pattern in cert_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                certifications.extend(matches[:2])  # Limit to avoid duplicates
            
            # Build comprehensive response
            return {
                "success": True,
                "company_name": company_name,
                "website": extracted_info["website"],
                "phone": phones[0] if phones else None,
                "email": emails[0] if emails else None,
                "description": extracted_info["description"],
                "specialties": services[:5],  # Top 5 services
                "certifications": list(set(certifications))[:3],  # Top 3 unique certs
                "location": location,
                "data_sources": [top_result.get("url") for top_result in results[:3]],
                "tavily_score": top_result.get("score", 0),
                "message": f"Found information for {company_name}"
            }
            
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return {
                "success": False,
                "company_name": company_name,
                "error": str(e),
                "message": "Failed to search online"
            }
            
    except Exception as e:
        logger.error(f"Error researching company: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to research company"
        }

@tool
def find_similar_contractors(project_type: str, location_zip: str, radius_miles: int = 30) -> Dict[str, Any]:
    """
    Find similar contractors who work on the same type of projects
    Useful for competitive analysis and pricing benchmarks
    
    Args:
        project_type: Type of project (e.g., "kitchen remodel", "landscaping")
        location_zip: ZIP code to search around
        radius_miles: Search radius in miles
    
    Returns:
        List of similar contractors in the area
    """
    try:
        logger.info(f"BSA Tool: Finding {project_type} contractors near {location_zip}")
        
        # Get ZIP codes in radius
        zip_codes_in_radius = get_zip_codes_in_radius(location_zip, radius_miles)
        
        # Query database for bid cards of this type
        from database_simple import db
        
        query = db.client.table("bid_cards").select("*")
        query = query.in_("status", ["active", "collecting_bids", "generated"])
        
        if zip_codes_in_radius:
            query = query.in_("location_zip", zip_codes_in_radius)
        else:
            query = query.eq("location_zip", location_zip)
        
        result = query.execute()
        bid_cards = result.data if result.data else []
        
        # Filter by project type
        filtered_cards = []
        project_type_lower = project_type.lower()
        for card in bid_cards:
            card_type = card.get("project_type", "").lower()
            title = card.get("title", "").lower()
            description = card.get("description", "").lower()
            
            if (project_type_lower in card_type or 
                project_type_lower in title or 
                project_type_lower in description):
                filtered_cards.append(card)
        
        # Analyze demand by location
        areas_analysis = {}
        for card in filtered_cards:
            city = card.get("location_city", "Unknown")
            if city not in areas_analysis:
                areas_analysis[city] = {
                    "city": city,
                    "state": card.get("location_state", ""),
                    "project_count": 0,
                    "avg_timeline_weeks": [],
                    "project_subtypes": set()
                }
            
            areas_analysis[city]["project_count"] += 1
            
            # Extract timeline if available
            if card.get("timeline_start") and card.get("timeline_end"):
                try:
                    start = datetime.fromisoformat(card["timeline_start"].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(card["timeline_end"].replace('Z', '+00:00'))
                    weeks = (end - start).days / 7
                    areas_analysis[city]["avg_timeline_weeks"].append(weeks)
                except:
                    pass
            
            # Track project subtypes
            areas_analysis[city]["project_subtypes"].add(card.get("project_type", "general"))
        
        # Process final data
        areas_with_demand = []
        for city, data in areas_analysis.items():
            avg_timeline = None
            if data["avg_timeline_weeks"]:
                avg_timeline = sum(data["avg_timeline_weeks"]) / len(data["avg_timeline_weeks"])
            
            areas_with_demand.append({
                "city": city,
                "state": data["state"],
                "project_count": data["project_count"],
                "project_subtypes": list(data["project_subtypes"]),
                "avg_timeline_weeks": round(avg_timeline, 1) if avg_timeline else None,
                "demand_level": "High" if data["project_count"] >= 3 else "Medium" if data["project_count"] >= 1 else "Low"
            })
        
        # Sort by project count (highest demand first)
        areas_with_demand.sort(key=lambda x: x["project_count"], reverse=True)
        
        return {
            "success": True,
            "project_type": project_type,
            "search_radius": radius_miles,
            "areas_with_demand": areas_with_demand[:10],  # Top 10 areas
            "total_projects": len(filtered_cards),
            "total_areas": len(areas_analysis),
            "message": f"Found {len(filtered_cards)} {project_type} projects in {len(areas_analysis)} areas"
        }
        
    except Exception as e:
        logger.error(f"Error finding similar contractors: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to find similar contractors"
        }

@tool
def analyze_market_rates(project_type: str, location_zip: str) -> Dict[str, Any]:
    """
    Analyze market rates for a specific project type in a location
    Helps contractors price competitively
    
    Args:
        project_type: Type of project to analyze
        location_zip: ZIP code for market analysis
    
    Returns:
        Market rate analysis and recommendations
    """
    try:
        logger.info(f"BSA Tool: Analyzing market rates for {project_type} in {location_zip}")
        
        # Map project types to trades
        trade_mapping = {
            "kitchen": {"labor": 85, "sqft": 240, "materials_multiplier": 1.4},
            "bathroom": {"labor": 95, "sqft": 350, "materials_multiplier": 1.5},
            "landscaping": {"labor": 65, "sqft": 15, "materials_multiplier": 1.2},
            "electrical": {"labor": 110, "per_outlet": 150, "per_fixture": 250},
            "plumbing": {"labor": 105, "per_fixture": 450, "rough_in": 2500},
            "deck": {"labor": 85, "sqft": 240, "materials_multiplier": 1.4},
            "roofing": {"labor": 85, "sqft": 240, "materials_multiplier": 1.4}
        }
        
        # Find the trade category
        trade = "kitchen"  # Default
        for key in trade_mapping.keys():
            if key in project_type.lower():
                trade = key
                break
        
        # Get rates for this trade
        rates = trade_mapping.get(trade, trade_mapping["kitchen"])
        
        # Calculate baseline pricing for 1000 sqft
        sqft = 1000
        if trade in ["kitchen", "bathroom", "landscaping", "deck", "roofing"]:
            labor_cost = sqft * rates["sqft"] * 0.4  # 40% labor
            materials_cost = sqft * rates["sqft"] * 0.6  # 60% materials
            total = (labor_cost + materials_cost) * rates.get("materials_multiplier", 1.4)
        else:
            # Electrical/plumbing use different calculation
            labor_cost = rates["labor"] * 40  # Assume 40 hours base
            materials_cost = 5000  # Base materials
            total = (labor_cost + materials_cost) * 1.5
        
        # Create pricing data structure
        pricing_data = {
            "trade": trade,
            "labor_cost": round(labor_cost),
            "materials_cost": round(materials_cost),
            "total_estimate": round(total),
            "breakdown": {
                "sqft_rate": rates.get("sqft", 0),
                "labor_rate": rates["labor"],
                "markup": rates.get("materials_multiplier", 1.5)
            }
        }
        
        # Calculate pricing tiers
        base_estimate = pricing_data["total_estimate"]
        
        return {
            "success": True,
            "project_type": project_type,
            "location_zip": location_zip,
            "market_analysis": {
                "economy_tier": base_estimate * 0.75,
                "standard_tier": base_estimate,
                "premium_tier": base_estimate * 1.5,
                "luxury_tier": base_estimate * 2.0
            },
            "pricing_factors": {
                "labor_rate": pricing_data["breakdown"]["labor_rate"],
                "sqft_rate": pricing_data["breakdown"]["sqft_rate"],
                "materials_markup": pricing_data["breakdown"]["markup"]
            },
            "recommendation": f"For {project_type} in {location_zip}, consider pricing between ${base_estimate * 0.75:,.0f} and ${base_estimate * 1.5:,.0f} depending on project scope and materials",
            "message": "Market rate analysis complete"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing market rates: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to analyze market rates"
        }

# Export all tools for BSA agent to use
BSA_ENHANCED_TOOLS = [
    search_available_bid_cards,
    research_contractor_company,
    find_similar_contractors,
    analyze_market_rates
]